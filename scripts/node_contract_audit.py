"""Dependency-free static audit of the production Pixaroma node registry."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


def _assignment_names(class_node: ast.ClassDef) -> set[str]:
    names: set[str] = set()
    for statement in class_node.body:
        if isinstance(statement, ast.Assign):
            names.update(
                target.id for target in statement.targets if isinstance(target, ast.Name)
            )
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            names.add(statement.target.id)
    return names


def _mapping(tree: ast.Module, name: str) -> dict[str, str]:
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in statement.targets):
            continue
        if not isinstance(statement.value, ast.Dict):
            raise RuntimeError(f"{name} must be a literal dictionary")
        result: dict[str, str] = {}
        for key, value in zip(statement.value.keys, statement.value.values):
            type_name = ast.literal_eval(key)
            if not isinstance(type_name, str):
                raise RuntimeError(f"{name} contains a non-string key")
            result[type_name] = value.id if isinstance(value, ast.Name) else ast.unparse(value)
        return result
    raise RuntimeError(f"Missing {name}")


def audit(root: Path, expected: int | None = None) -> dict:
    init_tree = ast.parse((root / "__init__.py").read_text(encoding="utf-8-sig"))
    production_modules = []
    for statement in init_tree.body:
        # Imports inside `if dev_mode` are intentionally not visited here.
        if not isinstance(statement, ast.ImportFrom) or not statement.module:
            continue
        if not statement.module.startswith("nodes.node_"):
            continue
        if any(alias.name == "NODE_CLASS_MAPPINGS" for alias in statement.names):
            production_modules.append(statement.module.rsplit(".", 1)[-1])

    entries = []
    failures = []
    seen: set[str] = set()
    for module_name in production_modules:
        path = root / "nodes" / f"{module_name}.py"
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
        class_map = _mapping(tree, "NODE_CLASS_MAPPINGS")
        display_map = _mapping(tree, "NODE_DISPLAY_NAME_MAPPINGS")

        if set(class_map) != set(display_map):
            failures.append(f"{path.name}: class/display mapping keys differ")

        for type_name, class_name in class_map.items():
            if type_name in seen:
                failures.append(f"duplicate registered type: {type_name}")
            seen.add(type_name)
            class_node = classes.get(class_name)
            if class_node is None:
                failures.append(f"{type_name}: class {class_name} is not defined in {path.name}")
                assignments = set()
            else:
                assignments = _assignment_names(class_node)
            if "DESCRIPTION" not in assignments:
                failures.append(f"{type_name}: missing node-level DESCRIPTION")
            display_name = display_map.get(type_name, "")
            if not display_name.strip():
                failures.append(f"{type_name}: empty display name")
            entries.append(
                {
                    "type": type_name,
                    "display_name": display_name,
                    "class": class_name,
                    "module": module_name,
                    "has_description": "DESCRIPTION" in assignments,
                }
            )

    if expected is not None and len(entries) != expected:
        failures.append(f"expected {expected} production node types, found {len(entries)}")

    report = {
        "production_modules": len(production_modules),
        "registered_types": len(entries),
        "expected_types": expected,
        "failures": failures,
        "nodes": sorted(entries, key=lambda item: item["type"].lower()),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--expected", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit(args.root.resolve(), args.expected)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            f"Pixaroma node audit: {report['registered_types']} registered types "
            f"across {report['production_modules']} modules"
        )
        for failure in report["failures"]:
            print(f"ERROR: {failure}")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
