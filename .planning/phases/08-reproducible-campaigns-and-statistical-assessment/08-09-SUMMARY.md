---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "09"
subsystem: campaign execution
tags: [campaigns, process-pool, matched-samples, finite-look, stop-receipts]
requires: [08-04, 08-05, 08-07]
provides: [bounded-local-execution, finite-look-dispatch, crash-window-stop-recovery]
affects: [08-10, 08-11, 08-14, phase-09-css-reproduction, phase-11-quaternary-reproduction]
tech-stack:
  added: []
  patterns: [frozen-shard-process-pool, observational-resource-receipts, deterministic-stop-reconstruction]
key-files:
  created:
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-09-TASK-1-RED.json
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-09-TASK-2-RED.json
  modified:
    - src/bp_registry/campaigns/execution.py
    - tests/test_campaign_execution.py
decisions:
  - "Local workers receive only immutable sorted ShardPlan unit payloads and publish one private sealed receipt per unit."
  - "Worker timing, process IDs, environment, and unavailable device or scheduler facts are observational and excluded from scientific records."
  - "Finite-look dispatch reconstructs each complete boundary before later dispatch and atomically publishes an exact frozen-tail stop receipt."
metrics:
  duration: "~17 minutes"
  completed: "2026-10-11"
  tasks: 2
  files: 4
actuals:
  tokens: 8265
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 66d8179e44d04d6dca11a13023735bbad944d6fa
status: complete
---

# Phase 08 Plan 09: Bounded Local Execution Summary

Frozen campaign shards now execute through a bounded process pool while retaining topology-invariant scientific evidence and deterministic finite-look stop recovery.

## Accomplishments

- Added a bounded `ProcessPoolExecutor` route that consumes supplied immutable shards without repartitioning. Each child restricts and records only the four allowlisted numerical-thread environment variables.
- Sealed each terminal or interrupted unit receipt from a private staging directory. Completed units remain retained when a later unit fails, and missing units stay visibly resumable.
- Kept scientific sample identity, decoder randomness, terminal facts, work vectors, and persisted-sample digests separate from timing, PID, concurrency, and unavailable resource observations.
- Added whole-look dispatch: it evaluates only a fully terminal declared prefix, reconstructs the same pure decision before later work, and atomically persists the exact ordered authorized-undispatched tail.
- Added a post-decision/pre-publication fault hook. Restart reconstructs and publishes byte-identical stop evidence before it can submit a next-look shard; forged retained tails are rejected.

## Task Commits

1. **Task 1: Execute frozen shards with bounded local workers**
   - `7ffdfc5` — RED worker-topology evidence
   - `a171d6a` — bounded local process execution and interruption receipts
2. **Task 2: Dispatch whole finite-look batches across matched arms**
   - `4fa0f80` — RED crash-window recovery evidence
   - `569ed7f` — finite-look dispatcher and deterministic receipt recovery

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'local and (worker or order or failure or resource or work)' -x` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'matched or finite_look or stop_receipt_recovery or crash_window or early_stop or authorized_tail or batch or overshoot or persisted or interruption' -x` — 4 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -x` — 11 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_sampling.py tests/canonical/test_profiling.py -x` — 21 passed.
- `git diff --check` — passed.

## TDD Gate Compliance

- Task 1 RED record `08-09-TASK-1-RED.json` passed `tdd-red-evidence` before `execute_local_work_plan` existed.
- Task 2 RED record `08-09-TASK-2-RED.json` passed `tdd-red-evidence` before `dispatch_finite_looks` existed.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed the execution module, worker and finite-look tests, both RED receipts, and this summary exist.
- Confirmed task commits `7ffdfc5`, `a171d6a`, `4fa0f80`, and `569ed7f` exist with no tracked-file deletions.
