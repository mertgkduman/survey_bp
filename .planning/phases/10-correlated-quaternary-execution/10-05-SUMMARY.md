---
phase: 10-correlated-quaternary-execution
plan: "05"
subsystem: quaternary-bp-kernel
tags: [python, numpy, qldpc, bp4, llr, numerical-oracle]
requires:
  - phase: 10-02
    provides: immutable Pauli code/problem boundary and persisted I/X/Y/Z order
provides:
  - Frozen `quaternary-bp4-f64-v1` numerical profile and stable scalar primitives
  - Attempt-owned source-equation scalar LLR-BP4 session with typed work accounting
  - Independent conventional vector BP4 and exact-enumeration tree oracles
affects: [10-correlated-quaternary-execution, quaternary-schedules, q-bpgd, public-manifests]
actuals:
  tokens: 8477
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 5c6e4e9803ed2c23ceb1147c6f8a06f8bee89c9f
tech-stack:
  added: []
  patterns: ["Three identity-referenced node LLRs with scalar commutation edge messages", "Independent probability-vector/exact oracle tests", "Reserve complete four-state sweep work before mutable session state"]
key-files:
  created:
    - src/bp_registry/quaternary/numerics.py
    - src/bp_registry/quaternary/kernel.py
    - tests/canonical/quaternary/test_vector_oracle.py
    - tests/canonical/quaternary/test_kernel.py
  modified: []
key-decisions:
  - "Freeze quaternary-bp4-f64-v1 at float64 natural-log identity-referenced LLRs with symmetric +/-25 saturation and a vector/exact oracle gate before public evidence."
  - "Keep four-state node beliefs throughout production execution; only edge factors are commute/anticommute scalars."
  - "Use deterministic I<X<Y<Z ties, with I selected only when all nonidentity LLRs are strictly positive."
patterns-established:
  - "Quaternary scalar kernels receive only immutable observed problems and decoder priors; hidden truth has no kernel API path."
requirements-completed: [QBP-01]
coverage:
  - id: D1
    description: Frozen stable quaternary numerical profile and scalar LLR primitives.
    requirement: QBP-01
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_vector_oracle.py tests/canonical/quaternary/test_kernel.py -x"
        status: pass
    human_judgment: false
  - id: D2
    description: Source-equation scalar LLR-BP4 session with immutable four-state snapshots and budget caps.
    requirement: QBP-01
    verification:
      - kind: unit
        ref: "tests/canonical/quaternary/test_kernel.py#test_kernel_tree_sweep_matches_independent_vector_and_exact_posteriors"
        status: pass
    human_judgment: false
duration: 8m 10s
completed: 2026-10-07
status: complete
---

# Phase 10 Plan 05: Scalar LLR-BP4 Kernel Summary

**A frozen four-state scalar LLR-BP4 kernel with finite numerical semantics, owned attempt state, and independent vector/exact tree validation.**

## Performance

- **Duration:** 8m 10s
- **Started:** 2026-10-07T03:58:55Z
- **Completed:** 2026-10-07T04:07:05Z
- **Tasks:** 2/2
- **Files created:** 4
- **Verification:** 12 focused oracle/kernel tests and 9 existing tracer-subset tests passed.

## Accomplishments

- Added the persisted `quaternary-bp4-f64-v1` profile with float64 identity-referenced X/Y/Z LLRs, stable ordered reductions, symmetric saturation, nonfinite termination, smoothing, and tie semantics.
- Implemented scalar commute/anticommute C2V updates, three-component excluded V2C/posterior LLRs, normalized I/X/Y/Z marginals, original-syndrome stopping, immutable snapshots, and reserve-before-mutation work accounting.
- Added independent probability-vector BP4 and exact posterior enumeration references, then qualified the production tree sweep against both.

## Task Commits

1. **Task 1: Build stable three-LLR numerical primitives and independent oracles**
   - `6b71ec8` — RED test contract
   - `9bdd0af` — stable numerical primitives and numerical tests
2. **Task 2: Execute source-equation scalar LLR-BP4 sessions**
   - `0cef6e5` — RED kernel contract
   - `f73b294` — scalar kernel, session, and oracle/cap/immutability tests

## Files Created

- `src/bp_registry/quaternary/numerics.py` — frozen profile plus finite log-domain primitives.
- `src/bp_registry/quaternary/kernel.py` — pure scalar BP4 operations and owned session/snapshot lifecycle.
- `tests/canonical/quaternary/test_vector_oracle.py` — independent conventional vector BP4 and exact enumeration references.
- `tests/canonical/quaternary/test_kernel.py` — numerical, source-equation tree, work-cap, and truth-boundary contracts.

## Decisions Made

- Retained complete I/X/Y/Z probability mass at every node and converted to a scalar only for individual commutation factors.
- Declared the +/-25.0 limit as a project convention, with profile evidence that requires vector/exact qualification before public manifests may rely on it.
- Counted a flooding sweep in existing typed work categories: edge C2V/V2C updates, four-state belief assemblies, one Pauli candidate, one convergence check, per-variable candidate checks, and one BP call.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the test oracle import under pytest collection.**
- **Found during:** Task 2
- **Issue:** A relative test-module import failed because the quaternary test directory is not a Python package.
- **Fix:** Used pytest's test-directory import path for the independent oracle helpers.
- **Files modified:** `tests/canonical/quaternary/test_kernel.py`
- **Verification:** Focused kernel/oracle suite passed.
- **Committed in:** `f73b294`

**2. [Rule 1 - Bug] Quantized excluded three-LLR V2C beliefs before scalar check reduction.**
- **Found during:** Task 2
- **Issue:** The first sweep passed a three-component V2C vector directly into scalar box-plus.
- **Fix:** Applied the source-defined commutation LLR per excluded edge before ordered box-plus.
- **Files modified:** `src/bp_registry/quaternary/kernel.py`
- **Verification:** Tree messages and marginals match independent vector BP4 and exact enumeration.
- **Committed in:** `f73b294`

**Total deviations:** 2 auto-fixed Rule 1 corrections. Both were required for source-equation correctness and test execution.

## TDD Gate Compliance

- **Task 1 RED:** `6b71ec8`; evidence `RED_EVIDENCE_OK` for `test_quaternary_numerical_profile_is_available`.
- **Task 1 GREEN:** `9bdd0af`; focused numerical/oracle command passed.
- **Task 2 RED:** `0cef6e5`; evidence `RED_EVIDENCE_OK` for `test_scalar_llr_bp4_kernel_is_available`.
- **Task 2 GREEN:** `f73b294`; kernel/vector/exact/cap/truth-boundary command passed.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_vector_oracle.py tests/canonical/quaternary/test_kernel.py -x` — 12 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py -k 'tracer or installed_cli or non_css or null or empty or one_qubit or encoding or truth_boundary or replay or tamper or assessment' -x` — 9 passed.

## Issues Encountered

The GSD RED-evidence checker requires TAP-formatted target-failure output. The ordinary pytest failure was intentional but not parser-readable, so the evidence record was regenerated in the required TAP form before GREEN work began.

## Next Phase Readiness

The stable scalar BP4 kernel, numerical profile, and independent oracle ladder are ready for source-defined schedules and quaternary interventions. The profile's declared vector/exact gate has passed for the qualified tiny tree fixtures.

## Self-Check: PASSED

All four created files exist and all four Task 1/Task 2 commits are present in git history.
