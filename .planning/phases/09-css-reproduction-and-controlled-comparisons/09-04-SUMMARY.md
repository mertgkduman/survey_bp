---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "04"
subsystem: campaign-assessment
tags: [python, pydantic, negative-binomial, censoring, CSS]
requires:
  - phase: 08-reproducible-campaigns-and-statistical-assessment
    provides: strict fixed-shot and finite-look assessment contracts
provides:
  - ordered failure-count stopping with exact target-th-failure prefixes
  - separately retained terminal-batch tail and cap-censored states
  - inverse-binomial interval and multiplicative target-rule compatibility gates
affects: [campaigns, statistics, reporting, CSS reproduction]
tech-stack:
  added: []
  patterns: [strict Pydantic discriminated records, frozen inferential prefixes, separate cost and inference evidence]
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/contracts.py
    - tests/test_campaign_contracts.py
key-decisions:
  - "The target-th verified decoder failure, not the completed terminal batch, fixes the inverse-binomial trial count."
  - "Later terminal-batch shots are authorized provenance and cost evidence only; a cap before target remains censored without an interval."
patterns-established:
  - "Sampling-design validators reject interval and decision-rule substitutions before any campaign record is accepted."
requirements-completed: [EVAL-02]
actuals:
  tokens: 3266
  tasks: 2
  commits: 4
plan_head_before: 28c34831a7a1772d16641b7299aac7c44d42cc41
coverage:
  - id: D1
    description: Ordered failure-count stopping binds the target-th-failure prefix, terminal-batch tail, and cap censoring.
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: tests/test_campaign_contracts.py#test_failure_count_stopping_binds_ordered_prefix_tail_and_censoring
        status: pass
    human_judgment: false
  - id: D2
    description: Inverse-binomial and multiplicative assessments remain disjoint from historical fixed-shot and finite-look designs.
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: tests/test_campaign_contracts.py#test_failure_count_assessment_requires_inverse_binomial_and_multiplicative_rule
        status: pass
    human_judgment: false
duration: 3m
completed: 2026-10-11
status: complete
---

# Phase 09 Plan 04: Failure-Count Assessment Summary

**Ordered failure-count contracts retain exact negative-binomial prefixes, terminal-batch cost tails, cap censoring, and a factor-1.5 target rule without changing fixed-shot or finite-look semantics.**

## Performance

- **Duration:** 3m
- **Started:** 2026-10-11T19:21:28Z
- **Completed:** 2026-10-11T19:24:11Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- Added `FailureCountStoppingV1` with a deterministic campaign/cohort/point/sample ordinal order, exact target-th-failure prefix validation, authorized terminal-batch tail ordinals, and an explicit cap-censored state.
- Added `ExactInverseBinomialIntervalV1` and `MultiplicativeTargetRuleV1`; their cross-field checks bind `T_r`, prefix digest, tail count/digest, and the frozen target factor.
- Kept the existing fixed-shot and finite-look bytes and combinations intact while rejecting their use with inverse-binomial intervals or multiplicative rules.

## Task Commits

1. **Task 1: Freeze bounded failure-count stopping and censoring**
   - `818bb35` `test(09-04): add failing failure-count stopping test`
   - `2032c6c` `feat(09-04): add ordered failure-count stopping contract`
2. **Task 2: Bind inverse-binomial inference and multiplicative tolerance to the new design**
   - `713f8f3` `test(09-04): add failing inverse-binomial assessment test`
   - `ccf55a4` `feat(09-04): bind inverse-binomial failure-count assessment`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'stopping or ordered_stop or terminal_tail or denominator or outcome or partial' -x` — 3 passed, 5 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'failure_count or inverse_binomial or censor or multiplicative or historical' -x` — 2 passed, 7 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -x` — 9 passed.
- Both TDD RED evidence records passed `gsd-tools check tdd-red-evidence` before implementation.

## Decisions Made

- The inferential terminal is `T_r`, with cumulative failure counts exactly `r - 1` before and `r` at that ordinal. Later completed shots in the same authorized batch stay out of the denominator.
- Infrastructure interruption remains an incomplete outcome in the existing matrix. A hard cap before target is a distinct censored state and cannot carry an inferential interval.
- The multiplicative acceptance factor is stored in a strict decision-rule record, leaving source target bounds and precision in `TargetReferenceV1`.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Next Phase Readiness

Statistics and reporting work can now consume a distinct failure-count discriminator without treating a random stopping time or terminal tail as fixed-shot evidence.

## TDD Gate Compliance

| Task | RED | GREEN | Status |
| ---- | --- | ----- | ------ |
| 1 | `818bb35` | `2032c6c` | Pass |
| 2 | `713f8f3` | `ccf55a4` | Pass |

## Self-Check: PASSED

- Found `src/bp_registry/campaigns/contracts.py` and `tests/test_campaign_contracts.py`.
- Found all four task commits in the repository history.
