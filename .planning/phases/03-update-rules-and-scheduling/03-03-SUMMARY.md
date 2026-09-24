---
phase: 03-update-rules-and-scheduling
plan: "03"
subsystem: canonical-scheduling
tags: [layered, SCNS, SVNS, randomized-traversal, replay, local-step]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: V3 min-sum local-step execution and canonical EdgeTable identity
provides:
  - source-qualified layered local-step proposals with exact partition evidence
  - distinct check-node and variable-node serial schedule policies
  - purpose-separated randomized traversal identities and realized order replay
affects: [03-05-work-accounting, 03-06-layered-public-tracer, schedule-admission, pilot-comparisons]
plan_head_before: c37cf914d384c3f1a37efdf3d6b7a367508d84b6
actuals:
  tokens: 11473
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns:
    - immutable schedule proposals delegate reservation and mutation to CanonicalLocalStepExecutor
    - source-qualified local schedule evidence separates stale/fresh reads and D-09 stopping adaptations
    - schedule-order RNG is purpose-separated from physical-error sampling
key-files:
  created:
    - tests/canonical/test_schedule_semantics.py
    - .planning/phases/03-update-rules-and-scheduling/03-03-task-1-red-evidence.json
    - .planning/phases/03-update-rules-and-scheduling/03-03-task-2-red-evidence.json
    - .planning/phases/03-update-rules-and-scheduling/03-03-task-3-red-evidence.json
  modified:
    - src/bp_registry/canonical/schedules.py
key-decisions:
  - "Layer partitions retain exact integer EdgeTable identities, provenance, realized order, and repeated membership rather than textual graph labels."
  - "SCNS and SVNS are separate local policies with explicit visibility evidence; both retain D-09 per-node stopping as an adaptation."
  - "Random schedule order derives from a schedule_order purpose identity and never consumes physical-sampling RNG state."
requirements-completed: [SCH-02, SCH-03, SCH-05]
coverage:
  - id: D1
    description: "Layered partitions validate coverage/conflicts and execute source-qualified local units with fresh later-layer visibility."
    requirement: SCH-02
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_schedule_semantics.py -k layer"
        status: pass
    human_judgment: false
  - id: D2
    description: "Check-node and variable-node serial schedules retain distinct local units, cursor progress, retry safety, and duplicate-attempt rejection."
    requirement: SCH-03
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_schedule_semantics.py -k 'check_node_serial or variable_node_serial or retry or isolation'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Configuration, attempt, and sweep randomized traversal orders replay exactly without changing matched physical samples."
    requirement: SCH-05
    verification:
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_schedule_semantics.py -k 'random or refresh or physical_sample'"
        status: pass
    human_judgment: false
duration: 9 min
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 03: Update Rules and Scheduling Summary

**Layered, check-node serial, variable-node serial, and replayable randomized traversals now execute as inspectable canonical local-step policies.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-24T09:32:55Z
- **Completed:** 2026-09-24T09:42:01Z
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments

- Added conflict-free `LayeredSchedule` partitions with integer structural identity, provenance labels, repeated t-cover membership evidence, layer-level D-09 checks, and fresh later-layer visibility.
- Added separate source-linked `CheckNodeSerialSchedule` (SCNS) and `VariableNodeSerialSchedule` (SVNS) atomic units with explicit stale/fresh read sets, attempt-local progress, retry safety, and duplicate-shot identity protection.
- Added `RandomizedTraversalPlan` with independent `schedule_order` derivation, PCG64 state/replay evidence, exact configuration/attempt/sweep boundaries, and denial-safe order/RNG state.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_schedule_semantics.py -k layer` — 8 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_schedule_semantics.py -k 'check_node_serial or variable_node_serial or retry or isolation'` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_schedule_semantics.py -k 'random or refresh or physical_sample'` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_flooding.py tests/canonical/test_schedule_semantics.py tests/test_sampling.py` — 23 passed.
- `git diff --check c37cf914d384c3f1a37efdf3d6b7a367508d84b6..HEAD` — passed.

## Task Commits

1. **Task 1 RED: layered schedule contract** — `beebe8d` (`test`)
2. **Task 1 GREEN: explicit layered local steps** — `2e25530` (`feat`)
3. **Task 2 RED: serial schedule contract** — `1639c08` (`test`)
4. **Task 2 GREEN: distinct serial local schedules** — `fcbfa77` (`feat`)
5. **Task 3 RED: randomized traversal contract** — `7afb48a` (`test`)
6. **Task 3 GREEN: replayable randomized traversal plans** — `c13db84` (`feat`)

## Files Created/Modified

- `src/bp_registry/canonical/schedules.py` — layered, serial, retry-isolation, and randomized order policies.
- `tests/canonical/test_schedule_semantics.py` — direct production-executor tests for partition validity, visibility, serial distinction, retry, isolation, replay, and sampling independence.
- `.planning/phases/03-update-rules-and-scheduling/03-03-task-*-red-evidence.json` — validated intentional RED-gate records.

## Decisions Made

- Layered and serial schedule policies retain traversal and visibility evidence as decoder-visible structural facts; they do not infer equality from text or Unicode-normalized labels.
- The current work schema has no order-generation resource. `RandomizedTraversalPlan` establishes the reserve-before-draw transaction with an explicit operation count; Plan 03-05 owns the corresponding WorkVector schema extension and ledger reconstruction.
- Generic layer coloring remains explicitly `graph_coloring`, never a representation of the learned Moradi cluster-sequential policy.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test helper] Corrected the independent layer replay executor construction.**
- **Found during:** Task 1 GREEN verification.
- **Issue:** The new test referenced an unbound executor class when independently replaying the second layer.
- **Fix:** Constructed the independent executor from the first executor's concrete type.
- **Files modified:** `tests/canonical/test_schedule_semantics.py`
- **Verification:** Layered and regression suites passed.
- **Committed in:** `2e25530`

**Total deviations:** 1 auto-fixed (1 Rule 1).
**Impact on plan:** The correction was confined to the new test helper and did not change schedule semantics.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The direct schedule policies are ready for Plan 03-05 to extend schedule work accounting and partial-terminal reconstruction, then Plan 03-06 to expose the layered public manifest/CLI tracer. The randomized-order policy intentionally has no public manifest admission before those follow-on plans.

## Self-Check: PASSED

- Found `src/bp_registry/canonical/schedules.py` and `tests/canonical/test_schedule_semantics.py`.
- Found task commits `beebe8d`, `2e25530`, `1639c08`, `fcbfa77`, `7afb48a`, and `c13db84` in repository history.
