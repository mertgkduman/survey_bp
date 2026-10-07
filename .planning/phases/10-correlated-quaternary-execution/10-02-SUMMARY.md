---
phase: 10-correlated-quaternary-execution
plan: "02"
subsystem: quaternary-canonical-kernel
tags: [python, numpy, pauli, symplectic, css, immutable-problems]
requires:
  - phase: 10-01
    provides: bounded public quaternary tracer and fixed I/X/Y/Z convention
provides:
  - Typed immutable Pauli algebra with explicit symplectic semantics
  - Ordered general-stabilizer problem and candidate contracts
  - Lossless CSS-to-Pauli compiler with fixed X-then-Z syndrome order
affects: [phase-10-kernel, quaternary-sampling, quaternary-evaluator, asced]
tech-stack:
  added: []
  patterns: [owned-readonly-arrays, semantic-identity-bytes, certified-working-lineage]
key-files:
  created:
    - src/bp_registry/quaternary/algebra.py
    - src/bp_registry/quaternary/problems.py
    - tests/canonical/quaternary/conftest.py
    - tests/canonical/quaternary/test_algebra.py
  modified: []
key-decisions:
  - "Persist Pauli labels as I=0, X=1, Y=2, Z=3 with symplectic pairs (0,0), (1,0), (1,1), (0,1)."
  - "Compile CSS H_x rows as X checks followed by H_z rows as Z checks, fixing [s_X,s_Z]=[H_x z,H_z x]."
  - "Require explicit transform and lift witnesses for derived working graphs; identity paths cannot alter the original graph or syndrome."
patterns-established:
  - "General quaternary semantic identity includes ordered labels, roles, original-row indexes, logical-basis availability, source identity, and syndrome."
requirements-completed: [QBP-01, QBP-03]
actuals:
  tokens: 6301
  tasks: 2
  commits: 4
plan_head_before: 4a5a5958d10c011b1b55ee908e90ccc1dd80834d
coverage:
  - id: D1
    description: Immutable Pauli algebra with independent commutation and syndrome oracle tests.
    requirement: QBP-01
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_algebra.py
        status: pass
    human_judgment: false
  - id: D2
    description: Ordered general-stabilizer and lossless CSS problem contracts with certified working lineage.
    requirement: QBP-03
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_algebra.py
        status: pass
      - kind: integration
        ref: tests/canonical/quaternary/test_public_execution.py
        status: pass
    human_judgment: false
duration: 10m
completed: 2026-10-07
status: complete
---

# Phase 10 Plan 02: Pauli Algebra and Immutable Problems Summary

**Reusable four-state Pauli algebra and immutable general-stabilizer contracts, including lossless CSS compilation with explicit X-then-Z syndrome semantics.**

## Performance

- **Duration:** 10m
- **Started:** 2026-10-07T02:52:03Z
- **Completed:** 2026-10-07T03:01:35Z
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments

- Added owned, read-only I/X/Y/Z Pauli arrays with symplectic conversion, commutation, phase-free multiplication, syndrome, and weight operations.
- Added immutable general stabilizer, original/working-problem, and candidate contracts with semantic SHA-256 identities and explicit transform/lift certification.
- Compiled validated CSS artifacts into X rows followed by Z rows, preserving row roles, row indexes, logical bases, source identity, and the combined `[s_X,s_Z]` convention.
- Added independent hand tables and exhaustive Pauli-pair tests without using production commutation or syndrome code as the oracle.

## Task Commits

1. **Task 1: Freeze Pauli algebra and independent oracle fixtures**
   - `f1bfeb1` `test(10-02): add failing Pauli algebra contract`
   - `8672ff9` `feat(10-02): implement immutable Pauli algebra`
2. **Task 2: Compile immutable general and CSS Pauli problems**
   - `86e1394` `test(10-02): add failing quaternary problem contract`
   - `3936fbf` `feat(10-02): compile immutable quaternary problems`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_algebra.py -x` — 35 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py -x` — 9 passed.

## Decisions Made

- Kept the Phase 10 algebra separate from the tracer's private helpers so later samplers, kernels, and evaluators use an explicit shared contract without changing the preserved tracer behavior.
- Stored an absent logical basis as `None`; no logical action is inferred when a code omits it.
- Bound source artifact identity and ordered matrix roles into semantic bytes so a CSS row or syndrome-order change cannot retain the same identity.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Bug] Replaced a relative test import with a pytest fixture boundary.**
   - **Found during:** Task 1
   - **Issue:** The non-package test directory could not resolve `.conftest` as a relative import.
   - **Fix:** Exposed the independent hand tables through `pauli_oracle` in the local pytest conftest.
   - **Files modified:** `tests/canonical/quaternary/conftest.py`, `tests/canonical/quaternary/test_algebra.py`
   - **Verification:** Algebra test suite passed.

2. **[Rule 1 - Bug] Corrected an independently derived commutation expectation.**
   - **Found during:** Task 2
   - **Issue:** A general-code fixture expected a row to anticommute with an identical Y label.
   - **Fix:** Corrected the hand-derived expected syndrome from `[1,1]` to `[0,1]`.
   - **Files modified:** `tests/canonical/quaternary/test_algebra.py`
   - **Verification:** General and CSS problem tests passed.

**Total deviations:** 2 auto-fixed Rule 1 test corrections. Both preserved the planned mathematical contract.

## Known Stubs

None.

## Next Phase Readiness

The quaternary kernel, channel sampler, evaluator, and aSCED paths can consume a fixed ordered Pauli graph, immutable original observation, optional logical-basis status, and certified derived working graphs.

## Self-Check: PASSED

- Confirmed all four created source and test files exist.
- Confirmed task commits `f1bfeb1`, `8672ff9`, `86e1394`, and `3936fbf` exist in git history.
