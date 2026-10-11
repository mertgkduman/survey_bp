---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "08"
subsystem: campaign-statistics
tags: [scipy, exact-binomial, paired-comparison, holm, denominators]
requires:
  - phase: 08-07
    provides: Exact rate and finite-look assessment primitives
provides:
  - Complete matched paired-outcome tables with conservative paired intervals
  - Frozen-family Holm adjustment that retains unavailable sentinel members
  - Explicit all-shot, acceptance, conditional, and incomplete-pair denominators
affects: [phase-09-css-reproduction, phase-11-quaternary-reproduction, campaign-reporting]
tech-stack:
  added: []
  patterns: ["Exact SciPy binomial procedures with retained count receipts", "Unavailable comparisons remain frozen-family p*=1 sentinels"]
key-files:
  created:
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-08-TASK-1-RED.json
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-08-TASK-2-RED.json
  modified:
    - src/bp_registry/campaigns/statistics.py
    - tests/test_campaign_statistics.py
key-decisions:
  - "Paired inference joins the complete campaign/cohort/point/sample identity and rejects duplicate or partial pairs."
  - "Holm preserves the frozen family size for unavailable comparisons and makes any required unavailable member inconclusive."
  - "All-shot and accepted conditional performance retain separate exact denominators; infrastructure interruption remains incomplete."
patterns-established:
  - "Report terminal-status counts, acceptance uncertainty, and conditional denominator beside all-shot performance."
  - "Do not convert actual decoder work into a universal iteration metric."
requirements-completed: [STAT-01, STAT-03, STAT-05]
plan_head_before: bac7073a147f9babc7fa2dab781171954abb50b4
commits: 4
actuals:
  tokens: 8713
  tasks: 2
  commits: 4
coverage:
  - id: D1
    description: Complete paired 2x2 effects, exact discordance tests, and conservative frozen-family Holm adjustment.
    requirement: STAT-05
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_paired_table_exhaustively_retains_cells_marginals_and_exact_discordance
        status: pass
    human_judgment: false
  - id: D2
    description: All-shot, acceptance, conditional, and incomplete-pair denominator reporting.
    requirement: STAT-05
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_outcome_summary_exposes_all_shot_acceptance_and_conditional_denominators
        status: pass
    human_judgment: false
duration: 3m
completed: 2026-10-11
status: complete
---

# Phase 08 Plan 08: Paired Evidence and Denominator Reporting Summary

**Exact shared-sample paired comparisons, conservative frozen-family Holm results, and explicit terminal-to-conditional outcome denominators.**

## Performance

- **Duration:** 3m
- **Started:** 2026-10-11T06:07:25Z
- **Completed:** 2026-10-11T06:10:40Z
- **Tasks:** 2
- **Files modified:** 4
- **Verification:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -x` — 30 passed

## Accomplishments

- Joined paired arms only by identical frozen campaign, cohort, point, and physical sample identity; duplicate and partial arm evidence cannot yield a paired effect.
- Reported every paired 2x2 cell, marginal failure rate, simultaneous-exact discordant-cell risk-difference interval, and SciPy exact conditional McNemar p-value.
- Applied Holm adjustment against the full frozen family, retaining unavailable comparisons as p*=1, with explicit order, rank, multiplier, adjusted value, and inconclusive conclusions.
- Kept planned, dispatched, terminal, incomplete, accepted, all-shot, conditional, terminal-status, and actual-work values distinct in campaign summaries.

## Task Commits

1. **Task 1: Compute exact paired evidence and frozen-family multiplicity**
   - `8b2150e` — RED tests and verified evidence
   - `8623a99` — paired table and Holm implementation
2. **Task 2: Report acceptance, conditional denominators, and incomplete pairs**
   - `0880627` — RED tests and verified evidence
   - `a995e64` — denominator and incomplete-pair implementation

## Files Created/Modified

- `src/bp_registry/campaigns/statistics.py` — paired evidence, Holm family results, terminal outcome aggregation, and incomplete-pair coverage contracts.
- `tests/test_campaign_statistics.py` — adversarial paired, multiplicity, terminal disposition, acceptance, and partial-pair coverage.
- `08-08-TASK-1-RED.json` and `08-08-TASK-2-RED.json` — verified intentional RED evidence for both TDD tasks.

## Decisions Made

- The paired difference is first-arm failure rate minus second-arm failure rate; its interval subtracts simultaneous exact intervals for the two discordant-cell probabilities at half alpha each.
- Infrastructure interruption contributes to the explicit incomplete count and never enters a completed all-shot or conditional denominator.
- Unavailable Holm comparisons remain after numeric results in the report order and retain their frozen family multiplier, but always receive adjusted p=1 and an inconclusive conclusion.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The GSD RED-evidence checker consumes TAP-formatted evidence rather than native pytest output. Both RED receipts preserve the exact pytest command and actual assertion failure, then encode the checker-compatible test count and failure identity.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 9 and Phase 11 can consume a preserved paired statistical procedure that does not hide partial samples, terminal categories, acceptance, or multiplicity-family availability.

## Self-Check: PASSED

- `src/bp_registry/campaigns/statistics.py` and `tests/test_campaign_statistics.py` exist.
- Commits `8b2150e`, `8623a99`, `0880627`, and `a995e64` exist on the active phase branch.

---

*Phase: 08-reproducible-campaigns-and-statistical-assessment*
*Completed: 2026-10-11*
