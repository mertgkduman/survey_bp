---
phase: 11-quaternary-reproduction-and-comparisons
plan: "08"
subsystem: controlled-comparisons
tags: [qldpc, pauli, fixed-marginal, correlation, paired-inference, sizing]
requires:
  - phase: 11-07
    provides: complete replay-bound joint/separate Pauli matched-pair records
provides:
  - Immutable three-point D-09/D-10 fixed-marginal channel design
  - Simultaneous exact D_y and cross-point contrast assessment
  - Digest-bound paired precision preflight receipt
affects: [11-09, 11-10, 11-11, phase-11-controlled-comparisons]
tech-stack:
  added: []
  patterns: [exact rational channel rows, six-arm Bonferroni interval family, pre-outcome paired sizing receipts]
key-files:
  created:
    - data/studies/phase11-fixed-marginal-design.json
    - tests/test_phase11_correlation_statistics.py
  modified:
    - src/bp_registry/campaigns/statistics.py
    - src/bp_registry/campaigns/sizing.py
decisions:
  - "D-12 reports D_y=P(fail_joint)-P(fail_separate) first for each of the three frozen channel rows."
  - "Six exact arm-rate intervals share familywise alpha by Bonferroni allocation; row and cross-point bounds are derived from that one family."
  - "Paired precision is frozen from a pilot identity and a two-contrast family before comparison outcomes can alter admission."
metrics:
  duration: 8m 38s
  completed: 2026-10-14
status: complete
actuals:
  tokens: 8122
  tasks: 2
  commits: 4
commits: 4
plan_head_before: daadeaa4d897275ecb9a5b1662926d0b647a395c
requirements-completed: [QEV-02]
---

# Phase 11 Plan 08: Fixed-Marginal Correlation Statistics Summary

**The controlled comparison now freezes three exact I/X/Y/Z rows with constant binary marginals, reports paired logical-failure differences and simultaneous cross-point bounds, and refuses precision admission without a deterministic paired-design receipt.**

## Accomplishments

- Added the three canonical lower-Y, independence, and higher-Y rows in `I,X,Y,Z` order. Exact rational validation enforces `q_X=q_Z=1/30`, while retaining the intentionally varying nonidentity rate and covariance.
- Added `CorrelationSweepResultV1` and `assess_correlation_sweep`. It accepts only complete, replay-valid `PauliMatchedPairV1` records, rejects duplicate or overlapping physical samples, reports `D_y` first, and derives both frozen changes against independence from one simultaneous six-arm exact interval family.
- Added `calibrate_paired_sweep_design`, a pre-outcome receipt binding the design digest, pilot evidence identity, alpha allocation, stopping rule, two contrast family, and 5,000-pair cap. It preserves the existing `powered` and `blocked_precision` vocabulary.
- Added exact hand-counted, rational-channel, duplicate/partial-pair, zero-discordance, precision-ceiling, tied-effect, and deterministic-receipt regressions.

## Decisions Made

- The design is a fixed-marginal sweep, not a fixed-total-error-rate sweep; the artifact rejects the latter label and checks that total nonidentity varies.
- Cross-point inference uses point-disjoint samples. Existing pointwise paired McNemar/Holm behavior remains unchanged and is not reused as the cross-point test.
- Runtime remains explicitly unavailable in `PauliMatchedPairV1`; the sweep report retains this status rather than fabricating timing evidence.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_correlation_statistics.py -k 'tracer or rational or fixed_marginal or hand_count or contrast or simultaneous' -x` — passed (3 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_correlation_statistics.py -k 'sizing or precision or ceiling or zero or extreme or duplicate or partial or deterministic' -x` — passed (3 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_correlation_statistics.py -x` — passed (6 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py -x` — passed (7 tests).

## TDD Evidence

- Task 1 RED: `test_tracer_rational_fixed_marginal_design_is_exact_and_digest_bound` failed intentionally before the loader existed; `bc653fe` records the regression before `6ee8fff` made it pass.
- Task 2 RED: `test_sizing_receipt_is_deterministic_and_binds_frozen_inputs` failed intentionally before calibration existed; `b70c4b3` records the regression before `0ae05e3` made it pass.

## Task Commits

1. `bc653fe` — `test(11-08): add fixed-marginal sweep regressions`
2. `6ee8fff` — `feat(11-08): assess fixed-marginal correlation sweeps`
3. `b70c4b3` — `test(11-08): add paired-sweep sizing regressions`
4. `0ae05e3` — `feat(11-08): calibrate paired correlation precision`

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed all four implementation and regression files exist.
- Confirmed task commits `bc653fe`, `6ee8fff`, `b70c4b3`, and `0ae05e3` exist in Git history.
