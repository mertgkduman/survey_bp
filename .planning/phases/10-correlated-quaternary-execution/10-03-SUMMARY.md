---
phase: 10-correlated-quaternary-execution
plan: "03"
subsystem: quaternary-outcome-evaluation
tags: [python, pauli, symplectic, gf2, independent-evaluation, css]
requires:
  - phase: 10-02
    provides: immutable Pauli code, original-problem, and frozen-candidate contracts
provides:
  - Independent general-Pauli outcome classifier with fixed four-outcome order
  - Evaluator-local symplectic syndrome, residual, and GF(2) span checks
  - Typed observed or unavailable logical action evidence
affects: [phase-10-kernel, quaternary-public-execution, quaternary-ledger, qbp-analysis]
tech-stack:
  added: []
  patterns: [evaluator-owned-algebra, sealed-hidden-truth, typed-logical-missingness]
key-files:
  created:
    - src/bp_registry/quaternary/evaluator.py
    - tests/canonical/quaternary/test_evaluator.py
  modified: []
key-decisions:
  - "Keep the quaternary evaluator's symplectic, multiplication, and GF(2) span routines local so kernel algebra cannot validate itself."
  - "Represent each declared logical residual action as immutable (x, z) commutation coordinates; omit it with an explicit reason when the original code has no basis."
patterns-established:
  - "Outcome authority consumes a frozen candidate and separately supplied sealed truth only after decoding."
requirements-completed: [QBP-03]
plan_head_before: 5beb545565c097b07121e902edc6dd5fab8704c6
commits: 2
actuals:
  tokens: 3808
  tasks: 1
  commits: 2
coverage:
  - id: D1
    description: General-Pauli candidates classify in the fixed invalid-syndrome, exact, stabilizer-equivalent, logical-failure order.
    requirement: QBP-03
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_evaluator.py
        status: pass
    human_judgment: false
  - id: D2
    description: Declared logical actions are explicit, missing bases are typed unavailable, and compiled CSS results agree with the established evaluator.
    requirement: QBP-03
    verification:
      - kind: integration
        ref: OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_evaluator.py tests/canonical/quaternary/test_algebra.py tests/canonical/quaternary/test_public_execution.py tests/test_css_small.py -x
        status: pass
    human_judgment: false
metrics:
  duration: 4m
  completed: 2026-10-07
status: complete
---

# Phase 10 Plan 03: Independent Quaternary Evaluator Summary

Independent four-outcome Pauli evaluation using evaluator-owned symplectic algebra, GF(2) stabilizer-span membership, and typed logical-action evidence.

## Accomplishments

- Added a post-freeze evaluator that validates candidate syndrome, computes phase-free residuals, classifies exact and stabilizer-equivalent outcomes, and assigns all remaining valid residuals to logical failure.
- Kept evaluator commutation, multiplication, and elimination code independent from the quaternary kernel implementation.
- Added exhaustive tiny general-code enumeration, all tiny CSS Pauli-pair agreement checks, missing-basis coverage, and malformed-candidate rejection.

## Task Commits

1. **Task 1: Classify general Pauli candidates independently**
   - `2a08a91` `test(10-03): add failing quaternary evaluator contract`
   - `394e6dc` `feat(10-03): classify general Pauli candidates independently`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_evaluator.py -k 'invalid_syndrome or exact or stabilizer_equivalent or logical_failure or unavailable or exhaustive or css or independent or malformed' -x` — 8 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_evaluator.py tests/canonical/quaternary/test_algebra.py tests/canonical/quaternary/test_public_execution.py tests/test_css_small.py -x` — 60 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py -k 'truth_boundary or replay' -x` — 2 passed.

## TDD Gate Compliance

- RED commit `2a08a91` records `RED_EVIDENCE_OK` for the missing evaluator boundary assertion.
- GREEN commit `394e6dc` implements the evaluator and passes the focused and integration suites.
- No refactor commit was required.

## Decisions Made

- Evaluator-local symplectic and GF(2) routines are the authority for outcome classification.
- The evaluator accepts hidden truth only as a separate post-freeze argument, retaining decoder and policy truth separation.
- A logical basis is optional: outcome classification always completes, while unavailable logical detail carries an explicit reason.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Bug] Replaced a relative test-fixture import with a local independent oracle.**
   - **Found during:** Task 1 RED phase.
   - **Issue:** The non-package test directory rejected the relative import during collection, which prevented an intentional behavior assertion.
   - **Fix:** Kept the test oracle independent by defining its compact hand Pauli table locally.
   - **Files modified:** `tests/canonical/quaternary/test_evaluator.py`
   - **Verification:** RED evidence passed, then the full evaluator suite passed.

**Total deviations:** 1 auto-fixed Rule 1 test-boundary correction.

## Known Stubs

None.

## Next Phase Readiness

Later quaternary execution and ledger paths can submit frozen candidates with sealed truth to an independent evaluator, preserving full outcome and logical-detail provenance.

## Self-Check: PASSED

- Confirmed evaluator module, exhaustive test suite, and both TDD commits exist.
