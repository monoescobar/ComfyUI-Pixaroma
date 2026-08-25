# Contributing

Preserve saved-workflow compatibility: internal node type names, input order,
output order, and frontend serialization are public contracts.

Before opening a pull request, run:

```bash
python scripts/release_preflight.py
python scripts/node_contract_audit.py --expected 79
python -m unittest discover -s tests -v
```

Update the expected count intentionally when adding or removing production
nodes. Do not commit model weights, generated media, credentials, private
prompts, cached downloads, or workstation-specific paths.
