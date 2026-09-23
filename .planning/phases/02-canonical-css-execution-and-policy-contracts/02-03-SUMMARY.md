---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "03"
subsystem: canonical-css-numerics-and-scheduling
tags: [css, binary-spa, float64, flooding, numerical-profile, deterministic-order]
requires:
  - phase: 02-01
    provides: project-owned binary SPA kernel and canonical policy boundaries
provides:
  - named binary-spa-flooding-f64-v1 numerical profile with materialized conventions
  - stable finite LLR box-plus primitives and explicit degree-one behavior
  - canonical edge tables and double-buffered flooding sweeps with proposed leaf work
affects: [canonical-policy-expansion, update-rules-and-scheduling, canonical-ledger-work-accounting]
tech-stack:
  added: []
  patterns: [named-numerical-profile, finite-boundary-validation, canonical-edge-order, double-buffered-flooding]
key-files:
  created:
    - src/bp_registry/canonical/schedules.py
    - tests/canonical/conftest.py
    - tests/canonical/test_numerics.py
    - tests/canonical/test_flooding.py
  modified:
    - src/bp_registry/canonical/numerics.py
    - src/bp_registry/canonical/kernel.py
key-decisions:
  - "binary-spa-flooding-f64-v1 uses CPU NumPy float64, natural-log odds, symmetric K=25 clipping, and explicit deterministic ties."
  - "Flooding commits only a complete new v2c buffer after deriving all c2v messages from an immutable old snapshot."
patterns-established:
  - "Numerical boundaries reject nonfinite data with named NumericalFailure evidence rather than coercing it."
  - "Sparse graph enumeration is normalized into a check-major, variable-minor edge table before message updates."
requirements-completed: [ENG-04, SCH-01]
coverage:
  - id: D1
    description: Named finite numerical profile, LLR encoding, degree-one check rule, and deterministic tie handling.
    requirement: ENG-04
    verification:
      - kind: unit
        ref: tests/canonical/test_numerics.py
        status: pass
    human_judgment: false
  - id: D2
    description: Canonical edge ordering and complete old/new-buffer flooding sweep semantics with proposed work counts.
    requirement: SCH-01
    verification:
      - kind: unit
        ref: tests/canonical/test_flooding.py
        status: pass
    human_judgment: false
metrics:
  duration: 7m
  completed: 2026-09-23
  tasks_completed: 2
  files_changed: 6
status: complete
plan_head_before: ce0ea426ad595ca0a12e8732d0c84a0902bd1793
commits: 4
actuals:
  tokens: 7136
  tasks: 2
  commits: 4
---

# Phase 02 Plan 03: Stable SPA Numerics and Flooding Contracts Summary

`binary-spa-flooding-f64-v1` now fixes all binary SPA numerical conventions and drives canonical, double-buffered flooding sweeps independent of sparse input order.

## Performance

- **Duration:** 7m
- **Started:** 2026-09-23T08:15:26Z
- **Completed:** 2026-09-23T08:22:13Z
- **Tasks:** 2
- **Files changed:** 6

## Accomplishments

1. Materialized deterministic CPU float64 natural-log LLR conventions, K=25 clipping, stable pairwise box-plus, degree-one checks, zero hard decisions, and canonical-ID ties.
2. Added a canonical check-major/variable-minor edge table plus complete old-v2c → c2v → new-v2c flooding sweeps with explicit proposed leaf work.
3. Routed the project-owned kernel through the schedule contract and verified numerical, ordering, empty-graph, malformed-input, and full-regression behavior.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_numerics.py tests/canonical/test_flooding.py`

Result: `6 passed`.

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`

Result: `91 passed`.

## Task Commits

1. **Task 1: Lock probability/LLR encoding and stable finite sum-product arithmetic**
   - `df5807b` test RED: numerical-profile contract tests
   - `1a0de3b` feat GREEN: stable numerical profile primitives
2. **Task 2: Make flooding edge order, stale/fresh reads, and sweep work explicit**
   - `9f46257` test RED: flooding schedule contract tests
   - `75e6929` feat GREEN: canonical double-buffered flooding schedule

## Decisions Made

- The reference profile is named `binary-spa-flooding-f64-v1`; paper-specific clipping or tie behavior must use another named profile or explicit adaptation.
- A flooding schedule owns message ordering and returns proposed work only; budget reservation and committed accounting remain with Plan 04.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserved one-message check neighborhoods as one-element buffers**

- **Found during:** Task 2 verification
- **Issue:** NumPy scalar indexing for a single incoming check message violated the vector-only box-plus boundary.
- **Fix:** Used indexed one-element arrays so every check update receives the same typed vector shape as larger neighborhoods.
- **Files modified:** `src/bp_registry/canonical/schedules.py`
- **Verification:** Flooding contract tests and the full suite pass.
- **Committed in:** `75e6929`

**Total deviations:** 1 auto-fixed (Rule 1).

## Known Stubs

None.

## Issues Encountered

The GSD RED-evidence validator consumes TAP summaries while this project uses pytest. The actual targeted pytest failures were preserved as compact TAP evidence records before GREEN, and both target tests were verified as intentional RED failures.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Later update and schedule policies can reuse the canonical edge identity, pure kernel message functions, and typed proposed-work vector without changing the flooding semantics.

## Self-Check: PASSED

All six planned source/test artifacts and all four task commits (`df5807b`, `1a0de3b`, `9f46257`, `75e6929`) exist. Coverage metadata classifies both deliverables as automatically verified.
