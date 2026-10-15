---
phase: 11-quaternary-reproduction-and-comparisons
plan: "14"
subsystem: final evidence assessment
tags: [phase11, controlled-evaluation, provenance, claim-boundaries, verification]
requires:
  - phase: 11-quaternary-reproduction-and-comparisons
    plan: "12"
    provides: source-assessment receipts
  - phase: 11-quaternary-reproduction-and-comparisons
    plan: "13"
    provides: policy-comparison verification
  - phase: 11-quaternary-reproduction-and-comparisons
    plan: "15"
    provides: code-specific controlled-evaluation closures
provides:
  - Receipt-bound Phase 11 evidence index with source, controlled, and policy lanes
  - Independent digest and claim-boundary verification for the final index
affects: [phase-11-assessment, quaternary-reproduction, public-campaign-docs]
tech-stack:
  added: []
  patterns: [allowlisted-reference-index, zero-pair-inconclusive-closure, lane-specific-claim-boundaries]
key-files:
  created:
    - data/results/phase11-assessment/assessment.json
    - data/results/phase11-assessment/verification.json
    - tests/test_phase11_final_assessment.py
  modified:
    - src/bp_registry/campaigns/statistics.py
    - src/bp_registry/campaigns/cli.py
    - docs/campaigns.md
key-decisions:
  - "GB46 and BB72 retain three frozen channel rows, zero complete-pair denominators, and no controlled effect claim under sealed deny-only receipts."
  - "The final index keeps source reproduction, primary controlled inference, and policy comparison evidence in independent namespaces."
  - "BB72 retains source-reported distance, project-derived logical limitations, and method exclusions rather than borrowing GB46 eligibility."
metrics:
  duration: 1h
  completed: 2026-10-14
actuals:
  tokens: 12191
  tasks: 3
  commits: 7
commits: 7
plan_head_before: 147c098544b659ee51000851c9a26284845e7419
status: complete
---

# Phase 11 Plan 14: Final Evidence Assessment Summary

**Published a digest-bound Phase 11 evidence index that keeps source, policy, and receipt-bound controlled evidence separate while preserving both controlled codes as zero-pair inconclusive closures.**

## Accomplishments

- Added `phase11-assess` and `phase11-verify` campaign CLI routes. They rebuild the allowlisted source assessments, controlled receipts, policy verification, fixed-marginal design, and complete-method manifest before accepting the final index.
- Recorded GB46 and BB72 with the frozen `lower_y`, `independence`, and `higher_y` rows. Their leading `D_y` statistic, arm rates, uncertainty, convergence, denominator, typed work, and runtime remain explicitly unavailable because the verified Plan 11-15 receipts contain zero assessment-ready complete pairs.
- Added a completeness matrix covering every source target, controlled code and channel anchor, eligible or excluded method, qualification, status, limitation, and permitted claim.
- Documented commands and interpretation rules, including the complete-pair all-shot denominator and the rule that calibration is resource provenance only.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_final_assessment.py -k 'tracer or gb46 or primary or cross_point or simultaneous or bounded or inconclusive' -x` — passed (1).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_final_assessment.py -k 'bb72 or provenance or distance or identical_estimand or no_pooling or exclusion' -x` — passed (1).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_final_assessment.py tests/canonical/quaternary/test_public_execution.py -k 'phase11 or assessment_index or source_lane or controlled_lane or policy_lane or installed_cli or tamper or claim' -x` — passed (including re-signed source, receipt, calibration, and claim substitutions).
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.campaigns.cli phase11-verify --campaign-root . --assessment data/results/phase11-assessment/assessment.json --output-root <temporary-directory>` — returned `status: verified` and preserved `no_controlled_effect_claim` for both codes.

## Task Commits

1. **Task 1: Produce the terminal GB46 joint-versus-separate assessment** — `be01cfe`, `42b3d64` (RED), `eb6f327` (GREEN).
2. **Task 2: Add BB72 assessment with identical estimands and retained caveats** — `0260546` (RED), `03c11c3` (GREEN).
3. **Task 3: Reconcile source, primary, and policy evidence into a verified public index** — `5116696` (RED), `c7d6f58` (GREEN).

## Decisions Made

- A sealed denial and zero complete-pair count support an explicit inconclusive result, never a decoder effect or superiority claim.
- Source result qualification, primary joint-versus-separate inference, and policy mechanism evidence remain separate question-specific evidence lanes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the complete-method manifest schema literal while adding BB72 exclusions.**

- **Found during:** Task 2 GREEN verification.
- **Issue:** The assessment builder initially expected an obsolete schema literal and rejected the checked manifest.
- **Fix:** Bound the validator to `phase11_complete_methods_v1` and regenerated the digest-bound index.
- **Files modified:** `src/bp_registry/campaigns/statistics.py`, `data/results/phase11-assessment/assessment.json`.
- **Commit:** `03c11c3`.

## TDD Gate Compliance

Each task has a persisted intentional RED record verified with `gsd-tools check tdd-red-evidence` before its GREEN implementation commit. Task 1 required a small follow-up RED assertion commit so the Python assertion failure could be represented by the framework's TAP-based evidence checker.

## Known Stubs

None. Unavailable statistics, zero denominators, denied dispatch, source gaps, and ineligible methods are evidence limits retained by the final assessment, not placeholders.

## Self-Check: PASSED

- Confirmed all six planned production artifacts exist.
- Confirmed all seven task commits exist from plan base `147c098544b659ee51000851c9a26284845e7419`.
