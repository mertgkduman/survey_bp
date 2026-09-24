# Deferred Items

## 2026-09-24 — inherited canonical CLI environment failure

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q -x tests/canonical/test_update_rules.py tests/test_manifest.py tests/test_canonical_cli.py` passed 58 tests, then `tests/test_canonical_cli.py::test_documented_tutorial` failed. Its subprocess invokes `.venv/bin/python -m bp_registry.cli`, but that environment cannot import `bp_registry` (`ModuleNotFoundError`). The Phase 04 Relay changes import and test through the configured pytest path; this is an existing editable-install/environment issue outside Plan 04-01's declared files.
