import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "node_contract_audit.py"
SPEC = importlib.util.spec_from_file_location("pixaroma_node_contract_audit", SCRIPT)
AUDIT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT_MODULE)


class NodeContractTests(unittest.TestCase):
    def test_production_registry_is_complete(self):
        report = AUDIT_MODULE.audit(ROOT, expected=79)
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["registered_types"], 79)

    def test_internal_loop_engine_is_documented(self):
        report = AUDIT_MODULE.audit(ROOT, expected=79)
        engine = next(node for node in report["nodes"] if node["type"] == "PixaromaLoopEngine")
        self.assertTrue(engine["has_description"])

    def test_release_preflight_and_contract_docs_exist(self):
        for relative in (
            "scripts/release_preflight.py",
            "scripts/node_contract_audit.py",
            "docs/NODE_CONTRACT_AUDIT.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CHANGELOG.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
