---
phase: 03-update-rules-and-scheduling
plan: "16"
subsystem: group-shuffled-traversal-verification
tags: [hsu-ndgsbp, traversal, work-budget, tamper-replay]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: Plan 03-10 public group tracer
provides:
  - complete and interrupted source-iteration replay
  - exact partial cursor, repeated-check, candidate, and work evidence
  - budget-denial reason reconstruction for local schedules
affects: [03-17, SCH-06]
key-files:
  modified:
    - src/bp_registry/canonical/verification.py
    - tests/canonical/test_group_shuffled.py
    - tests/test_canonical_cli.py
    - tests/test_manifest.py
requirements-completed: []
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 16: Full Hsu Traversal and Reconstruction

Direct small-graph tests establish complete overlapping-group traversal, a new purpose-separated order on the following iteration, exact local cursor and work counts, and unchanged RNG/message state on admission denial. Public BB-144 tests execute 72 local units across a 71-group source traversal and the next order, plus a work-capped partial traversal. Both verify from persisted public context. Rehashed edits to order, source ID, work, and progress are rejected.

The full-traversal probe exposed a shared local-schedule verifier omission: on a count-budget stop it omitted the typed budget reason. The verifier now reconstructs the reason from its independent BudgetTree replay for BP-call, setup, order-refresh, and local-step denial paths.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_group_shuffled.py tests/test_canonical_cli.py tests/test_manifest.py -k 'hsu or group_shuffled'` — 20 passed.
- `PYTHONPATH=src OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical tests/test_canonical_cli.py tests/test_manifest.py` — 224 passed.
- The same broad target without `PYTHONPATH=src` had one environment-only subprocess import failure; rerunning with the documented source path passed.

## Commit

- `e7ed4ec` — full and interrupted traversal tests and budget-reason replay fix.

## Deviations

- The budget-reason fix also covers other local schedules because the omission was in their shared verifier path.
- Tests and fix were committed together; no separate TDD red-step evidence is claimed.
