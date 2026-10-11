---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "20"
subsystem: canonical-resource-guard
tags: [canonical, resource-caps, interruption, blocked]
status: blocked
plan_head_before: 4dbe834
commits: 1
dependency_graph:
  requires: [09-08, 09-16]
  provides: [runtime guard groundwork]
  affects: [09-17, 09-18]
key_files:
  modified:
    - src/bp_registry/ledger.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/mbbp.py
    - src/bp_registry/runner.py
    - tests/canonical/test_resource_guard.py
actuals:
  tokens: 20000
  tasks: 0
  commits: 1
---

# Phase 09 Plan 20: Canonical Resource Guard Summary

Implemented a guarded canonical mutation seam and boundary-observed interruption snapshot, but did not complete the exact route-profile and all-engine boundary requirements.

## Completed Groundwork

- Added immutable strict and interruptible runtime authorizations, a mutable single-unit guard, exact ledger/artifact reservations, control-receipt reserve, deterministic cap latching, and wall-boundary snapshots.
- Made canonical ledger writes serialize once, reserve the exact framed bytes before append, commit only after durable append, and release failed reservations.
- Added guarded atomic artifact replacement, typed materialized terminal-or-interrupted wrappers, flooding boundaries, and optional MBBP member/local-step observers. Unguarded execution keeps the historical path.
- Added a public derived-profile record and exact mapping verifier that rejects stale fields for the supported baseline route.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_resource_guard.py tests/test_ledger.py -k 'guard or empty_journal' -x` — 5 passed, 12 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py tests/canonical/test_voting.py -x` — 25 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py -k 'layered_spa_public_manifest_preflights_runs_and_verifies_through_local_executor or public_canonical_work_counts_one_bp_call_per_attempt' -x` — 2 passed, 70 deselected.

## Blocking Plan Gaps

The current executable-maxima implementation does not yet derive a complete, exact reachable-event inventory and exact largest serialized event template for every registered route. It therefore cannot honestly authorize Phase 9 failure-count execution as an independently exact profile.

Guided-decimation and Phase-5 controller loops also need their own truthful pre/post sweep or branch callbacks, and V7 needs a partial open-ledger lifecycle before member execution, so all interruption modes produce the required retained prefix evidence and caller-owned control-receipt seam.

## Commit

- `10b2ada` feat(09-20): add canonical runtime resource guard

## Self-Check: PASSED

The listed source files and focused regressions exist. This summary remains blocked because the missing exact inventory and route-complete interruption propagation are required for the plan objective.
