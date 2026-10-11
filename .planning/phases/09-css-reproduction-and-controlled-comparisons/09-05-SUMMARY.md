---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "05"
subsystem: campaign-statistics
tags: [python, scipy, negative-binomial, inverse-binomial, CSS]
requires:
  - phase: 09-css-reproduction-and-controlled-comparisons
    provides: strict ordered failure-count stopping and inverse-binomial contracts
provides:
  - exact two-sided inverse-binomial intervals bound to the ordered target-th failure
  - factor-based source-target decisions that retain source uncertainty separately
  - explicit inconclusive states for cap-censored and incomplete failure-count evidence
affects: [campaigns, reporting, CSS reproduction, controlled comparisons]
tech-stack:
  added: []
  patterns: [negative-binomial tail inversion, immutable inferential-prefix receipts, explicit censored evidence states]
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/statistics.py
    - tests/test_campaign_statistics.py
key-decisions:
  - "Decoder failures are SciPy negative-binomial successes, so the observed variate is T_r minus r nonfailures."
  - "The authorized terminal-batch tail is retained for provenance and cost, then excluded from inverse-binomial trials and target assessment."
  - "The factor-1.5 equivalence band uses only source bounds; source extraction uncertainty remains a separate receipt field."
patterns-established:
  - "Failure-count inference validates the complete ordered prefix and all receipt bindings before numerical inversion."
requirements-completed: [EVAL-02]
actuals:
  tokens: 6505
  tasks: 2
  commits: 4
plan_head_before: 5ad75fd2fd22b236bbd7dc02462486311a30cee0
coverage:
  - id: D1
    description: Completed ordered failure-count evidence receives an exact two-sided inverse-binomial interval using T_r alone.
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_inverse_binomial_small_tail_bounds_match_enumerated_stopping_mass
        status: pass
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_inverse_binomial_uses_exact_ordered_target_failure_not_terminal_batch
        status: pass
    human_judgment: false
  - id: D2
    description: Censored evidence remains inconclusive, and source-target agreement retains the source band separately from the multiplicative factor.
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_multiplicative_target_decision_clips_and_preserves_censored_inconclusive
        status: pass
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_multiplicative_target_decision_keeps_source_band_and_factor_separate
        status: pass
    human_judgment: false
duration: 6m
completed: 2026-10-11
status: complete
---

# Phase 09 Plan 05: Exact Failure-Count Statistics Summary

**Exact inverse-binomial intervals now use the ordered target-th decoder failure, while multiplicative source-target decisions preserve uncertainty and censoring states.**

## Performance

- **Duration:** 6m
- **Started:** 2026-10-11T20:09:34Z
- **Completed:** 2026-10-11T20:15:10Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- Added a validated `ExactInverseBinomialRateV1` whose two-sided bounds invert `scipy.stats.nbinom` for `r` decoder failures and `T_r-r` nonfailures.
- Bound every interval to the ordered inferential prefix, target-th failure ordinal, explicit completed-shot count, terminal-tail digest, and count receipt; later authorized terminal shots cannot alter inference.
- Added `MultiplicativeTargetDecisionV1` with pass, discrepant, and inconclusive outcomes, keeping source target bounds and extraction uncertainty distinct from the frozen factor.
- Routed cap-censored, incomplete-count, and invalid-order evidence through typed inconclusive states without a computed interval or fixed-shot substitution.

## Task Commits

1. **Task 1: Invert one completed failure-count stopping distribution exactly**
   - `41027c5` `test(09-05): add failing inverse-binomial interval tests`
   - `07a5409` `feat(09-05): invert ordered failure-count intervals`
2. **Task 2: Decide multiplicative target agreement without merging uncertainty sources**
   - `8b7538d` `test(09-05): add failing multiplicative target tests`
   - `b1b63f4` `feat(09-05): assess multiplicative failure-count targets`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'inverse_binomial or ordered_stop or authorized_tail or coverage or boundary' -x` — 7 passed, 44 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'multiplicative or containment or discrepant or inconclusive or target' -x` — 12 passed, 39 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'binomial or finite_look or target_interval' -x` — 23 passed, 28 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -x` — 51 passed.
- Both TDD RED evidence records passed `gsd-tools check tdd-red-evidence` before the corresponding implementation commit.

## Decisions Made

- The SciPy negative-binomial success probability is the decoder logical-failure probability. Its failure count is therefore the number of nonfailure shots before the r-th decoder failure.
- The lower endpoint solves `P(K <= T_r-r) = alpha/2`; the upper endpoint solves `P(K >= T_r-r) = alpha/2`, with the all-success boundary fixed at one.
- The acceptable target band is `[source_lower / factor, source_upper * factor]`, clipped to `[0, 1]`; `absolute_tolerance` stays in the retained source-target record and is not folded into this band.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Next Phase Readiness

Reporting and reproduction plans can consume a separately typed failure-count interval and target verdict without converting cap-censored evidence into a point estimate or fixed-shot assessment.

## TDD Gate Compliance

| Task | RED | GREEN | Status |
| ---- | --- | ----- | ------ |
| 1 | `41027c5` | `07a5409` | Pass |
| 2 | `8b7538d` | `b1b63f4` | Pass |

## Self-Check: PASSED

- Found `src/bp_registry/campaigns/statistics.py` and `tests/test_campaign_statistics.py`.
- Found all four task commits in repository history.
