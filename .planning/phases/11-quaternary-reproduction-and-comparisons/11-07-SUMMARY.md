---
phase: 11-quaternary-reproduction-and-comparisons
plan: "07"
subsystem: controlled-comparisons
tags: [qldpc, bp4, css, matched-sampling, provenance, all-shot]
requires:
  - phase: 10-correlated-quaternary-execution
    provides: immutable physical-sample and canonical materialized-runner contracts
provides:
  - Same-sample joint-versus-separate Pauli comparison record
  - Marginal-only binary component boundary and canonical-runner adapter
  - Replay-bound component terminals and all-shot outcome evidence
affects: [phase-11-controlled-comparisons, phase-11-sizing, phase-11-public-campaign]
tech-stack:
  added: []
  patterns: [narrow decoder input models, materialized-sample identity binding, digest-bound paired evidence]
key-files:
  created:
    - tests/test_phase11_joint_separate.py
  modified:
    - src/bp_registry/campaigns/contracts.py
    - src/bp_registry/campaigns/controlled_execution.py
key-decisions:
  - "D-05 binary callbacks receive only their component prior, syndrome, and arm-neutral sample identities."
  - "D-06 records retain one materialized Pauli digest across joint and separate arms."
  - "D-08 retains both component terminals and maps nonconvergence to an all-shot failure without dropping the pair."
patterns-established:
  - "Controlled decoders use typed narrow inputs, while original-problem truth stays evaluator-owned until both arms return."
  - "Paired records validate their canonical digest, arm cardinality, component order, and sample identity on replay."
requirements-completed: [QEV-02]
actuals:
  tokens: 7516
  tasks: 2
  commits: 4
plan_head_before: 7e25afc46992b8bfa3a7491d0822727935c0860f
coverage:
  - id: D-05
    description: "Separate X and Z callbacks receive only q_X or q_Z, their syndrome, and arm-neutral identities."
    requirement: QEV-02
    verification:
      - kind: unit
        ref: tests/test_phase11_joint_separate.py::test_tracer_identical_sample_marginals_and_hidden_truth_boundary
        status: pass
    human_judgment: false
  - id: D-06
    description: "Joint and separate outcomes bind one immutable physical-sample and materialized-sample digest."
    requirement: QEV-02
    verification:
      - kind: unit
        ref: tests/test_phase11_joint_separate.py::test_component_adapter_uses_canonical_materialized_runner
        status: pass
    human_judgment: false
  - id: D-08
    description: "All partial convergence combinations retain terminal candidates, work, pair evidence, and all-shot outcomes."
    requirement: QEV-02
    verification:
      - kind: unit
        ref: tests/test_phase11_joint_separate.py::test_partial_nonconvergence_keeps_components_and_all_shot_pair
        status: pass
    human_judgment: false
duration: 5m 22s
completed: 2026-10-14
status: complete
---

# Phase 11 Plan 07: Matched Joint and Separate Inference Summary

**One immutable Pauli sample now drives joint BP4 and separate binary components with marginal-only inputs, independent evaluation, and replayable all-shot evidence.**

## Performance

- **Duration:** 5m 22s
- **Started:** 2026-10-14T19:38:36Z
- **Completed:** 2026-10-14T19:43:58Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Added `PauliMatchedPairV1` and `BinaryComponentTerminalV1` contracts that bind both decoder arms, their complete terminal evidence, physical sample bytes, and canonical replay digest.
- Added `run_joint_separate_unit`, which derives only `q_X=P(X)+P(Y)` and `q_Z=P(Z)+P(Y)` for the binary callbacks and evaluates returned recoveries against the original CSS problem after decoding.
- Added a canonical materialized-runner adapter that retains selected component candidates from the canonical ledger while using the same materialized sample digest for both components.
- Added all-shot outcome mapping and regressions for partial nonconvergence, candidate and evidence tampering, duplicate arms, swapped components, and missing arms.

## Task Commits

1. **Task 1: Execute one GB46 Pauli sample through joint and separate inference** — `0c6e30b` (feat)
2. **Task 2: Preserve partial nonconvergence, work, replay, and tamper evidence** — `e6b9aac` (feat)
3. **Canonical runner integration fix** — `4bc59fa` (fix)
4. **All-shot outcome mapping fix** — `14e80c3` (fix)

## Files Created/Modified

- `src/bp_registry/campaigns/contracts.py` — matched-pair, component-terminal, arm-result, digest, and all-shot contracts.
- `src/bp_registry/campaigns/controlled_execution.py` — joint/separate unit execution, narrow decoder inputs, canonical binary adapter, and independent evaluation.
- `tests/test_phase11_joint_separate.py` — marginal-isolation, same-sample, partial-terminal, all-shot, replay, tamper, malformed-pair, and canonical-adapter coverage.

## Decisions Made

- Decoder callbacks never receive sampled Pauli bytes, hidden X/Z errors, or the full joint distribution in a separate component call.
- Nonconverged components remain in the record; any nonconvergence maps the separate arm to an all-shot failure while preserving its returned candidate and evaluator result.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical functionality] Added the canonical binary-runner adapter**
- **Found during:** Task 2 verification
- **Issue:** The initial narrow callback seam proved marginal isolation but did not itself provide the required existing canonical materialized-runner route.
- **Fix:** Added `canonical_binary_materialized_decoder`, which supplies the same materialized sample and digest to `run_canonical_materialized_one` and retains its selected ledger candidate.
- **Files modified:** `src/bp_registry/campaigns/controlled_execution.py`, `tests/test_phase11_joint_separate.py`
- **Commit:** `4bc59fa`

**2. [Rule 2 - Critical functionality] Bound paired arm statuses to the existing all-shot outcome matrix contract**
- **Found during:** Task 2 verification
- **Issue:** Component terminal evidence was retained, but paired arm records lacked a first-class all-shot classification.
- **Fix:** Added the complete `OutcomeMatrixV1` mapping to matched records and verified that partial nonconvergence is retained as an all-shot failure.
- **Files modified:** `src/bp_registry/campaigns/contracts.py`, `src/bp_registry/campaigns/controlled_execution.py`, `tests/test_phase11_joint_separate.py`
- **Commit:** `14e80c3`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py -k 'tracer or identical_sample or marginals or hidden_truth' -x` — passed (1 test).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py -k 'nonconver or all_shot or component or replay or tamper or duplicate or partial' -x` — passed (6 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py -x` — passed (7 tests).

## Tracer Feedback Gate

The tracer's automated verification was rerun before Task 2 expansion and passed. Interactive end-of-phase verification mode therefore allowed the expansion to continue.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed all three plan files exist.
- Confirmed task commits `0c6e30b`, `e6b9aac`, `4bc59fa`, and `14e80c3` exist in Git history.
