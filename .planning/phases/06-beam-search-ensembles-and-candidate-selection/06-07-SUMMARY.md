---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "07"
subsystem: canonical-public-execution
tags: [mbbp-ld, manifests, replay, ledger]
status: implementation_complete_pending_parent_commits
plan_head_before: pending-parent-commit
commits: 0
dependency_graph:
  requires: [06-05, 06-06]
  provides: [public-mbbp-contract, phase6-ledger-replay]
  affects: [canonical-cli, public-runner]
tech_stack:
  added: []
  patterns: [strict-pydantic-contract, deterministic-replay, truth-boundary]
key_files:
  created: [src/bp_registry/canonical/phase6.py, tests/test_phase6_public_execution.py]
  modified: [src/bp_registry/manifests.py, src/bp_registry/canonical/execution.py, src/bp_registry/canonical/verification.py, src/bp_registry/ledger.py, src/bp_registry/runner.py, src/bp_registry/cli.py]
decisions:
  - V7 MBBP-LD requires source-qualified one-hot duplicate-check transforms, independent member state, NMS alpha 0.875, serial checks, and finite aggregate C2V work.
  - Coordinate-majority vote descriptors are structurally specified but rejected until an end-to-end public vote execution path exists.
  - Explicit Phase 6 evidence uses a sealed V6 ledger envelope with basis, member, candidate-origin, duplicate-group, and work-leaf events.
metrics:
  tasks: 2
  status: pending_parent_commit
---

# Phase 06 Plan 07: Public MBBP-LD Execution Summary

Added a strict V7 MBBP-LD experiment boundary, complete structural evidence, and deterministic replay before evaluator access to hidden truth.

## Completed Work

- Added V7 ensemble descriptors, finite caps, source-qualified one-hot transforms, and separate list-selection controls.
- Added truth-free Phase 6 projection plus V7 execution, original-syndrome validation, zero-return sentinel handling, and replay tamper checks.
- Added ledger V6 event grammar and runner/CLI dispatch so public V7 manifests preflight and execute through the installed workflow.
- Extended scope under parent approval to `ledger.py`, `cli.py`, and `runner.py`; the existing envelope could not represent the required explicit Phase 6 event types.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py tests/test_manifest.py -k 'phase6 and (schema or preflight or mbbp or ensemble or vote or historical or unsupported)' -x` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py -k 'public_execution or no_member_converged or zero_return or replay or original or truth_boundary or tamper or duplicate or missing or work or runtime' -x` — 4 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py -k 'canonical_v3_schema_is_generated or canonical_v4_schema_is_generated' -x` — 2 passed.
- Direct V7 `preflight_canonical` smoke check returned `ledger_version: 6`.
- `git diff --check` passed.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 3 - Blocking compatibility] Added the V6 ledger grammar and CLI/runner routing.
   - The existing ledger accepted only versions 2–5 and did not admit the required explicit Phase 6 event kinds.
   - Parent approved the additional owned files before implementation.

## Known Limits

- The V7 vote object is retained as a typed future contract but is rejected before artifact loading until coordinate-majority voting has complete execution and replay coverage. No unsupported vote can silently affect a result.

## Self-Check: PASSED

- All listed code and test files exist in the shared checkout.
- Changes are intentionally uncommitted because the protected-main coordinator will review and commit them.
