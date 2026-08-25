# Production node-contract audit

Pixaroma version `1.4.126` registers 79 production node types from 74 modules.
Two reference-node types exist in source for development but are excluded from
normal registration because `dev_mode` is false.

Every production type must have:

- a unique stable internal type name;
- a non-empty display name;
- a node-level `DESCRIPTION` visible to ComfyUI help surfaces;
- compatible return names and output tooltips, enforced by release preflight;
- an intentional import in the top-level production mapping.

Run the dependency-free checks from the repository root:

```bash
python scripts/release_preflight.py
python scripts/node_contract_audit.py --expected 79
python -m unittest discover -s tests -v
```

Use `--json` when a machine-readable inventory is required:

```bash
python scripts/node_contract_audit.py --expected 79 --json
```

The expected count is deliberately explicit. Adding or removing a node must be
reviewed as a workflow-compatibility change and update the count, documentation,
tests, and release notes together.

## Notes and help coverage

Pixaroma has three complementary documentation layers:

1. `DESCRIPTION`, input tooltips, and output tooltips travel with each node and
   appear in ComfyUI-aware help surfaces.
2. The in-app Pixaroma Help panel explains controls and workflows in user terms.
3. `README.md`, example workflows, and the mathematical notes in `docs/` cover
   installation, visual operation, and implementation details.

`PixaromaLoopEngine` is registered because ComfyUI's graph expansion executes
it, but it is an internal implementation node. Its description and tooltips
explicitly direct users to Loop Start and Loop End.

## What this check does not claim

Static contract success does not prove every GPU, browser, codec, or model path.
Release verification must still exercise representative workflows in a running
ComfyUI installation and preserve a rollback copy before deployment.
