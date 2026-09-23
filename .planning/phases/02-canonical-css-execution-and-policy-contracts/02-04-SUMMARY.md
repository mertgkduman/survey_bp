---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "04"
subsystem: canonical-css-budgeting-and-accounting
tags: [css, belief-propagation, hierarchical-budgets, work-accounting, provenance, runtime-metrics]
requires:
  - phase: 02-03
    provides: canonical double-buffered flooding sweeps and proposed work counts
  - phase: 02-05
    provides: typed append-only lineage and structural work/runtime evidence vocabulary
provides:
  - hard hierarchical reserve-before-work count budgets and one-shot reservations
  - leaf-only atomic work vectors with lineage-derived scope totals
  - schedule-qualified iteration and explicit runtime/resource metric missingness
affects: [canonical-policy-expansion, CSS-evaluation, durable-shot-evidence, profiling]
tech-stack:
  added: []
  patterns: [reserve-before-mutation, one-shot-reservation, leaf-only-accounting, monotonic-boundary-control, qualified-measurements]
key-files:
  created:
    - src/bp_registry/canonical/budgets.py
    - tests/canonical/test_budgets.py
    - tests/canonical/test_work_accounting.py
  modified:
    - src/bp_registry/canonical/execution.py
key-decisions:
  - "Count budgets reserve a complete typed flooding vector at every ancestor before any sweep mutation, while wall-clock limits remain boundary-checked operational controls."
  - "Committed work is retained only as a uniquely identified leaf delta; scope totals are derived by ancestry reduction rather than separately emitted counters."
  - "Iteration counts carry schedule and atomic-unit semantics, while runtime/resource facts preserve units, precision, method, scope, and unavailable reasons."
patterns-established:
  - "Atomic flooding treats a full old-v2c to new-v2c sweep as the smallest reservable state-changing work unit."
  - "Inactive intervention, branch, relay, and fallback categories serialize as observed zero in the complete WorkVector."
requirements-completed: [ENG-03, LED-03]
coverage:
  - id: D1
    description: "Hierarchical count caps reserve before complete flooding sweeps, roll back on failure, and expose scoped count or wall-clock termination evidence."
    requirement: ENG-03
    verification:
      - kind: unit
        ref: "tests/canonical/test_budgets.py"
        status: pass
    human_judgment: true
    rationale: "Automated invariants prove cap and boundary semantics; a researcher must still review whether named scopes and termination reasons communicate the intended scientific interpretation."
  - id: D2
    description: "Unique leaf work vectors reduce through branch, leg, member, search, and shot ancestry without double counting; iteration and resource facts remain qualified."
    requirement: LED-03
    verification:
      - kind: unit
        ref: "tests/canonical/test_work_accounting.py"
        status: pass
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q"
        status: pass
    human_judgment: false
metrics:
  duration: 7 min
  completed: 2026-09-23
  tasks_completed: 2
  files_changed: 4
status: complete
plan_head_before: 029c2a660cf1fce71ea638ddce949ba8088d10d8
commits: 5
actuals:
  tokens: 7353
  tasks: 2
  commits: 5
---

# Phase 02 Plan 04: Hierarchical Budgets and Atomic Work Summary

Canonical flooding attempts now reserve one complete typed work vector before state mutation, enforce every ancestor cap, and derive evidence totals solely from committed unique leaf events.

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-23T08:40:13Z
- **Completed:** 2026-09-23T08:48:10Z
- **Tasks:** 2
- **Files changed:** 4

## Accomplishments

1. Added thread-safe count-budget trees, one-shot reservations, explicit count termination evidence, and separately modeled monotonic wall-clock deadlines at declared synchronization boundaries.
2. Added atomic flooding execution that reserves the complete edge/variable sweep vector before calculation, commits it after a finite buffer swap, and rolls it back on failure.
3. Added complete leaf-only work vectors, schedule-qualified iteration counts, and typed runtime/resource facts with explicit unavailable reasons.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py tests/canonical/test_work_accounting.py`

Result: `9 passed`.

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`

Result: `107 passed`.

## Task Commits

1. **Task 1: Reserve hierarchical count budgets before atomic sweeps**
   - `bc5a0df` test RED: hierarchical budget contract tests
   - `dbcc80d` feat GREEN: atomic hierarchical sweep budgets
   - `99b30a0` test: root-limit and sweep-rollback coverage
2. **Task 2: Emit leaf work once and derive qualified effort/runtime summaries**
   - `b8acd43` test RED: leaf work accounting contracts
   - `7f14086` feat GREEN: qualified work and resource measurements

## Files Created/Modified

- `src/bp_registry/canonical/budgets.py` - Hard scoped budgets, leaf vectors, termination facts, qualified iteration, and resource metrics.
- `src/bp_registry/canonical/execution.py` - Atomic flooding sweep reservation/commit boundary.
- `tests/canonical/test_budgets.py` - Hierarchical cap, rollback, concurrency, and wall-clock boundary tests.
- `tests/canonical/test_work_accounting.py` - Leaf reduction, zero vector, iteration, precision, and missingness tests.

## Decisions Made

- Count limits are hard, pre-mutation reservations; wall-clock duration is not converted into a retroactive work count.
- The only durable accounting source is a unique leaf vector, so every ancestor total is a derived reduction.
- Runtime and resource data may be unavailable, but unavailable values retain collection method, scope, unit, precision, and a reason.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## Next Phase Readiness

Later intervention, branching, relay, and fallback policies can add their own unique leaf vectors without changing root-total semantics or pretending their zero baseline work is absent.

## TDD Gate Compliance

- Task 1 RED (`bc5a0df`) and GREEN (`dbcc80d`) committed in order; targeted contract failure was validated as `RED_EVIDENCE_OK`.
- Task 2 RED (`b8acd43`) and GREEN (`7f14086`) committed in order; targeted contract failure was validated as `RED_EVIDENCE_OK`.

## Self-Check: PASSED

All four planned implementation/test artifacts, the SUMMARY artifact, and all five measured task commits exist.

---
*Phase: 02-canonical-css-execution-and-policy-contracts*
*Completed: 2026-09-23*
