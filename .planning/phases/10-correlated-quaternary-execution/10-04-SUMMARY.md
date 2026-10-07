---
phase: 10-correlated-quaternary-execution
plan: "04"
subsystem: quaternary-sampling
tags: [python, numpy, pauli, categorical-sampling, reproducibility]
requires:
  - phase: 10-02
    provides: immutable Pauli labels, algebra, and original-problem contracts
provides:
  - Strict named depolarizing and explicit I/X/Y/Z joint-channel declarations
  - Deterministic one-draw categorical Pauli samples with sealed hidden truth
  - Replay identities and immutable channel/sampling ledger evidence
affects: [quaternary-kernel, q-bpgd, manifests, event-ledgers]
actuals:
  tokens: 6022
  tasks: 2
  commits: 4
plan_head_before: 1c796160c40ad250896ce987b593b2bc1df6969e
tech-stack:
  added: []
  patterns:
    - Immutable float64 joint channel tables with persisted validation semantics
    - One categorical Pauli draw per qubit, then derived symplectic truth and syndrome
key-files:
  created:
    - src/bp_registry/quaternary/sampling.py
    - tests/canonical/quaternary/test_sampling.py
  modified: []
key-decisions:
  - "Keep physical I/X/Y/Z probability rows unchanged and represent decoder zero-prior accommodation as a separately identified smoothing object."
  - "Use Decimal conversion of persisted float text for inverse-CDF boundaries so declared ties resolve stably as I<X<Y<Z."
requirements-completed: [QBP-02]
coverage:
  - id: D1
    description: "Validated named and explicit immutable joint Pauli channel declarations preserve exact zeros, row order, tolerance, and heterogeneous per-qubit rates."
    requirement: QBP-02
    verification:
      - kind: unit
        ref: "tests/canonical/quaternary/test_sampling.py#channel validation and smoothing tests"
        status: pass
    human_judgment: false
  - id: D2
    description: "One categorical Pauli draw produces replayable sealed truth and a decoder-visible full syndrome while preserving Y-induced X/Z correlation."
    requirement: QBP-02
    verification:
      - kind: unit
        ref: "tests/canonical/quaternary/test_sampling.py#categorical, single-Y, tie, correlation, and replay tests"
        status: pass
    human_judgment: false
duration: 8m 14s
completed: 2026-10-07
status: complete
---

# Phase 10 Plan 04: Joint Pauli Channel and Sampling Summary

**Immutable four-state physical channels now produce one deterministic categorical Pauli event per qubit while preserving exact zeros, Y correlation, and replay evidence.**

## Performance

- **Duration:** 8m 14s
- **Started:** 2026-10-07T03:45:56Z
- **Completed:** 2026-10-07T03:54:10Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- Added named depolarizing and explicit shared/per-qubit I/X/Y/Z probability tables with strict finite bounds, a persisted `1e-12` row-sum tolerance, immutable float64 values, and no user-table normalization.
- Added separately identified decoder-prior smoothing that never changes the physical sampling distribution or its exact zero probabilities.
- Added domain-separated categorical sampling, sealed Pauli/symplectic hidden truth, a full immutable syndrome observation, and ledger evidence binding the channel, ordering, rates, seed anchor, shot, and optional smoothing identity.
- Proved deterministic I/X/Y/Z values, a single-Y two-component CSS syndrome, non-product X/Z covariance, exact CDF boundary ownership, and replay/tamper behavior.

## Task Commits

1. **Task 1 RED: Validate and identify named and explicit joint channels** — `27889b8` (`test`)
2. **Task 1 GREEN: Validate and identify named and explicit joint channels** — `201ee96` (`feat`)
3. **Task 2 RED: Sample one categorical Pauli and prove X/Z correlation** — `c903526` (`test`)
4. **Task 2 GREEN: Sample one categorical Pauli and prove X/Z correlation** — `d627404` (`feat`)

## Files Created/Modified

- `src/bp_registry/quaternary/sampling.py` — strict joint channel, decoder smoothing, immutable truth/sample types, and categorical sampling.
- `tests/canonical/quaternary/test_sampling.py` — public QBP-02 validation, precision, deterministic, correlation, tie, and replay contracts.

## Decisions Made

- Persisted physical rows retain supplied float64 values after validation. A declared table is rejected when malformed; it is never normalized.
- Physical nonidentity rates remain per-row `1-P(I)`; scalar physical `p` appears only for named depolarizing channels.
- Exact boundary draws are assigned by stable I<X<Y<Z ordering using decimal representations of persisted float values, avoiding binary CDF accumulation drift at declared boundaries.

## TDD Gate Compliance

- **Task 1 RED:** `test_public_joint_pauli_sampling_module_is_available` intentionally failed before `sampling.py` existed; `.gsd/tdd-evidence/10-04-task-1-red.json` verified `RED_EVIDENCE_OK`.
- **Task 1 GREEN:** focused channel and smoothing verification passed: 14 tests.
- **Task 2 RED:** `test_public_categorical_pauli_sampler_is_available` intentionally failed before `sample_joint_pauli` existed; `.gsd/tdd-evidence/10-04-task-2-red.json` verified `RED_EVIDENCE_OK`.
- **Task 2 GREEN:** focused categorical verification passed: 8 tests; the complete sampling file passed: 25 tests.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_sampling.py -x` — 25 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_algebra.py tests/canonical/quaternary/test_evaluator.py tests/test_sampling.py -x` — 53 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py -x` — 9 passed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Float64 cumulative addition would classify a declared `0.3` boundary below the mathematical `0.1 + 0.2` threshold on this platform. The persisted tie convention requires declared-boundary stability, so the sampler accumulates the decimal rendering of persisted values. This is part of the planned precision interpretation, not a scope change.

## Next Phase Readiness

The quaternary kernel can consume resolved joint priors and sealed full-syndrome observations without factorizing X/Z or accessing hidden physical truth.

## Self-Check: PASSED

- Found `src/bp_registry/quaternary/sampling.py` and `tests/canonical/quaternary/test_sampling.py`.
- Found commits `27889b8`, `201ee96`, `c903526`, and `d627404` in the repository history.
