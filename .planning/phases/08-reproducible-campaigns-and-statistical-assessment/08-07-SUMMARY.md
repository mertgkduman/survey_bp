---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "07"
subsystem: campaign statistics
tags: [scipy, clopper-pearson, exact-binomial, alpha-spending, finite-look]
requires:
  - phase: 08-02
    provides: frozen assessment, target, family, and finite-look contracts
provides:
  - Exact two-sided Clopper-Pearson reports retaining integer count evidence
  - Frozen target interval containment decisions with receipt linkage
  - Declared finite-look alpha-spending assessment with overshoot and partial-batch evidence
affects: [08-08, 08-11, 08-14]
tech-stack:
  added: []
  patterns: [SciPy exact interval delegation, frozen interval algebra, finite declared look prefix]
key-files:
  created:
    - src/bp_registry/campaigns/statistics.py
    - tests/test_campaign_statistics.py
  modified: []
key-decisions:
  - "Exact rates delegate to scipy.stats.binomtest(...).proportion_ci(method='exact') rather than reimplementing inversion."
  - "Finite-look decisions consume only an ordered prefix of declared boundaries and each target uses its own allocated local alpha."
  - "A partial dispatched batch retains its counts and receipts but has no target verdict until it becomes a complete declared look."
patterns-established:
  - "Statistical outputs carry immutable scalar evidence, rule identifiers, interval algebra inputs, and SHA-256 receipt links."
  - "Target containment passes, strict disjointness fails, and overlaps or missing required source denominators remain inconclusive."
requirements-completed: [STAT-01, STAT-02, STAT-03, STAT-04]
actuals:
  tokens: 7007
  tasks: 2
  commits: 5
commits: 5
plan_head_before: 4c596fe4fd40c2c62aed692f7bf6076c075c27d9
duration: 3min
completed: 2026-10-11
status: complete
coverage:
  - id: D1
    description: Exact fixed-shot reports preserve rare-event count boundaries and use SciPy Clopper-Pearson limits.
    requirement: STAT-02
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_binomial_matches_scipy_for_every_small_count
        status: pass
    human_judgment: false
  - id: D2
    description: Frozen target intervals produce reconstructable pass, fail, and inconclusive verdicts.
    requirement: STAT-04
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_target_decision_uses_containment_disjointness_and_overlap
        status: pass
    human_judgment: false
  - id: D3
    description: Adaptive assessment spends local alpha only at declared complete looks and retains overshoot or partial state.
    requirement: STAT-03
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_finite_look_uses_declared_alpha_and_stops_only_after_a_completed_look
        status: pass
    human_judgment: false
---

# Phase 08 Plan 07: Exact Rates and Finite Looks Summary

**Campaign statistics now provide source-grounded exact rare-event limits, frozen target decisions, and finite-look alpha-spending evidence.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-10-11T05:55:00Z
- **Completed:** 2026-10-11T05:58:23Z
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments

- Added exact two-sided Clopper-Pearson reports that retain counts, alpha, confidence, method, sidedness, intervals, and count receipt hashes.
- Added target containment algebra over the clipped frozen tolerance band, preserving computed and target intervals, tolerance, rule ID, source-denominator state, and receipt hashes.
- Added finite-horizon alpha-spending assessment that accepts only ordered declared look prefixes, records local alpha, planned versus realized shots, overshoot, decisions, partial state, and the frozen stop reason.

## Task Commits

1. **Task 1 RED: exact rate and target-decision coverage** — `6045742` (`test`)
2. **Task 1 GREEN: exact rate and target decisions** — `1df0e89` (`feat`)
3. **Task 2 RED: finite-look evidence coverage** — `b641f38` (`test`)
4. **Task 2 GREEN: finite alpha-spent looks** — `28013b3` (`feat`)

## TDD Gate Compliance

- **Task 1 RED:** `08-07-TASK-1-RED.json` passed `tdd-red-evidence` with `RED_EVIDENCE_OK` before the statistics module existed.
- **Task 1 GREEN:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'binomial or zero_failure or all_failure or target or decision' -x` passed with 16 tests.
- **Task 2 RED:** `08-07-TASK-2-RED.json` passed `tdd-red-evidence` with `RED_EVIDENCE_OK` before finite-look records existed.
- **Task 2 GREEN:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'stopping or finite_look or alpha or overshoot or partial or peeking' -x` passed with 3 tests.
- **Regression:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -x` passed with 19 tests; `tests/test_campaign_contracts.py -x` passed with 6 tests.

## Files Created/Modified

- `src/bp_registry/campaigns/statistics.py` — exact-binomial reports, target decisions, and finite-look assessment records.
- `tests/test_campaign_statistics.py` — exhaustive small-count, rare-event, interval algebra, alpha-spending, overshoot, partial-batch, and undeclared-look coverage.

## Decisions Made

- SciPy is the sole implementation of exact interval inversion; the campaign layer validates inputs and records the declared method rather than duplicating the calculation.
- Finite-look reports use the allocated local alpha at every inspected boundary. A fixed-shot assessment is rejected from the adaptive procedure.
- Completed dispatches retain every realized sample as overshoot when they cross a declared boundary; partial batches remain explicitly inconclusive.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test boundary] Corrected the containment fixture to use an interval fully inside the acceptable band.**
- **Found during:** Task 1 GREEN
- **Issue:** The original `35/100` exact interval overlapped the upper tolerance boundary, so it correctly produced an inconclusive verdict instead of the test's expected pass.
- **Fix:** Used `350/1000`, whose exact interval is contained by the frozen acceptable band.
- **Files modified:** `tests/test_campaign_statistics.py`
- **Verification:** Focused exact-rate and target-decision tests passed.
- **Committed in:** `1df0e89`

**Total deviations:** 1 auto-fixed (Rule 1).

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

- Plan 08-08 can add paired and family-wise procedures on the exact-rate primitives.
- Plans 08-11 and 08-14 can serialize the complete finite-look evidence trail into reports and stop receipts.

## Self-Check: PASSED

- Confirmed the statistical module, tests, and both RED evidence records exist.
- Confirmed task commits `6045742`, `1df0e89`, `b641f38`, and `28013b3` exist with no tracked-file deletion.
