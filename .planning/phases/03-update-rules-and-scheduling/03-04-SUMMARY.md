---
phase: 03-update-rules-and-scheduling
plan: "04"
subsystem: canonical-execution
tags: [srbp, residual-scheduling, min-sum, sum-product, work-accounting, tdd]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: min-sum update rule and schedule-neutral canonical local-step executor
provides:
  - a closed Huang--Ueng conventional syndrome-based residual BP policy
  - stateful residual-cache reset and exact dependency invalidation semantics
  - full-pool setup and local-unit budget admission with source-visible work facts
affects: [03-update-rules-and-scheduling, SCH-04, work-accounting, public-policy-admission]
plan_head_before: c37cf914d384c3f1a37efdf3d6b7a367508d84b6
actuals:
  tokens: 8145
  tasks: 2
  commits: 8
tech-stack:
  added: []
  patterns:
    - full residual cache lifecycle is verified against an independent source oracle after every local step
    - setup and local-unit work are reserved before min-sum prediction or SPA/V2C mutation
key-files:
  created:
    - src/bp_registry/canonical/residual.py
    - tests/canonical/test_residual_schedule.py
  modified: []
key-decisions:
  - "The only residual procedure is conventional Huang--Ueng sRBP: min-sum predicts priorities while SPA commits C2V messages."
  - "Exact maxima use first canonical EdgeTable position; this and D-09 per-selection stopping are disclosed canonical adaptations."
requirements-completed: [SCH-04]
coverage:
  - id: D1
    description: "Closed conventional sRBP local unit with full-pool min-sum priority prediction, SPA commit, stable tie, and immediate convergence check."
    requirement: SCH-04
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_residual_schedule.py -k 'tracer or selection or tie'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Stateful reset/invalidation lifecycle, irregular source work, source-iteration progress, and atomic setup/local-step rollback."
    requirement: SCH-04
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_residual_schedule.py"
        status: pass
    human_judgment: false
duration: 9 min
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 04: Residual Schedule Summary

**A closed Huang--Ueng sRBP schedule now executes deterministic residual-selected SPA local units while retaining source-faithful min-sum cache lifecycle and atomic work admission.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-24T09:33:45Z
- **Completed:** 2026-09-24T09:42:07Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added `SyndromeResidualSchedule`, `ResidualCache`, and `ResidualSelection` for the single admitted conventional sRBP baseline.
- Enforced MS prediction versus SPA commit asymmetry, full EdgeTable scanning with first-edge ties, dependency-only cache refresh, and D-09 convergence checks.
- Added independent full-cache lifecycle-oracle tests across irregular graphs, source-iteration/partial-progress checks, and setup/local-step denial and exception rollback coverage.

## Task Commits

1. **Task 1 RED: residual tracer contract** — `10cc04e`, `b573927` (`test`)
2. **Task 1 GREEN: residual-selected local unit** — `d449c08` (`feat`)
3. **Task 2 RED: lifecycle and rollback invariants** — `0a6cffd` (`test`)
4. **Task 2 GREEN: source cache lifecycle** — `84601a7` (`feat`)
5. **Task 2 regression: every-step oracle comparison** — `b6a36d4` (`test`)
6. **Task 2 RED/GREEN: setup reservation boundary** — `93fc020` (`test`), `b8535f1` (`fix`)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_residual_schedule.py -k 'tracer or selection or tie'` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_residual_schedule.py` — 10 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_update_rules.py tests/canonical/test_residual_schedule.py tests/canonical/test_budgets.py` — 28 passed.
- `git diff --check` — passed.

## TDD Gate Compliance

- **Task 1 RED:** `03-04-task-1-red-evidence.json` validates the named assertion failure as `RED_EVIDENCE_OK`; `d449c08` is the GREEN implementation.
- **Task 2 RED:** `03-04-task-2-red-evidence.json` validates the denied-cache rollback failure as `RED_EVIDENCE_OK`; `84601a7` is the GREEN implementation.
- **Setup admission RED:** `03-04-setup-red-evidence.json` validates the missing setup-admission failure as `RED_EVIDENCE_OK`; `b8535f1` is the GREEN fix.

## Decisions Made

- Kept conventional Huang--Ueng sRBP closed: no alternate score, priority structure, tie menu, or stateless global refresh is exposed.
- Recorded `canonical_edge_order` and `D-09 after residual-selected local unit` as canonical adaptations rather than source claims.
- Kept detailed residual source work explicit in `ResidualWork` while Phase 03 Plan 05 owns the shared `WorkVector` schema expansion.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored the denied-path residual cache return.**
- **Found during:** Task 2 rollback verification.
- **Issue:** The initial denied branch discarded its `cache` binding before constructing the immutable no-op result.
- **Fix:** Preserved and returned the original cache on denial.
- **Files modified:** `src/bp_registry/canonical/residual.py`
- **Verification:** Denial, exception, and complete residual suites pass.
- **Committed in:** `84601a7`

**2. [Rule 2 - Missing critical functionality] Reserved initial full-pool setup work before residual calculation.**
- **Found during:** Task 2 close-out audit.
- **Issue:** Setup work was reported but not admitted through `BudgetTree` before min-sum prediction.
- **Fix:** Added optional atomic setup reservation, explicit denied setup result, and rollback on setup calculation failure.
- **Files modified:** `src/bp_registry/canonical/residual.py`, `tests/canonical/test_residual_schedule.py`
- **Verification:** Setup admission/denial regression and complete suite pass.
- **Committed in:** `b8535f1`

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 2).
**Impact on plan:** Both changes enforce the plan's atomic cache/work contract without adding a residual-policy variant or changing the shared work schema owned by Plan 03-05.

## Issues Encountered

The first Task 1 RED evidence record used unsupported field names. It was corrected and revalidated as `RED_EVIDENCE_OK` before the GREEN implementation; no production behavior was affected.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The source-qualified residual kernel boundary is ready for Plan 03-05 to assign the final Phase-3 shared work-vector/evidence grammar and for Plan 03-13 to add public manifest/CLI admission without changing residual semantics.

## Self-Check: PASSED

- `src/bp_registry/canonical/residual.py` and `tests/canonical/test_residual_schedule.py` exist.
- All eight task commits listed above exist in history.
- No Known Stubs, skipped tests, unrun verification, or new trust-boundary surface were found.

---
*Phase: 03-update-rules-and-scheduling*
*Completed: 2026-09-24*
