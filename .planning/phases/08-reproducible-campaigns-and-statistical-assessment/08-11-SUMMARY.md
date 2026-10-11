---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "11"
subsystem: campaign reporting and statistical assessment
tags: [campaigns, reporting, evidence-replay, exact-statistics, resources]
requires:
  - phase: 08-03
    provides: frozen source-target receipts
  - phase: 08-06
    provides: verified merge receipts and resumable terminal evidence
  - phase: 08-08
    provides: pure exact and finite-look statistical procedures
provides:
  - Byte-replayable campaign reports reconstructed only from canonical verified merge evidence
  - Explicit target decisions, stopping records, all-shot and paired denominator context
  - Typed work/resource observations with deliberate missingness and environment allowlisting
affects: [08-12, 08-13, 09-css-reproduction, 11-quaternary-reproduction]
tech-stack:
  added: []
  patterns: [canonical merge-byte verification, deterministic report replay, separate work/resource missingness]
key-files:
  created:
    - src/bp_registry/campaigns/reporting.py
  modified:
    - tests/test_campaign_statistics.py
key-decisions:
  - "Reports verify canonical MergeReceipt bytes and pinned receipt hashes before any terminal becomes a denominator."
  - "A multi-arm target must name its assessed arm explicitly; point-level all-shot and paired summaries remain separately visible."
  - "Only allowlisted thread settings are retained as environment observations; unavailable work and resource dimensions retain reasons instead of zero values."
actuals:
  tokens: 9269
  tasks: 2
  commits: 5
commits: 5
plan_head_before: 0dc96dbcd59216b28d6537e746dc1c86aebeaa29
duration: 34min
completed: 2026-10-11
status: complete
---

# Phase 8 Plan 11: Evidence-only campaign reporting Summary

**Campaign reports now replay exact assessment decisions from verified merge terminal facts while retaining denominators, paired coverage, finite-look stopping, work vectors, operational observations, and typed missing measurements.**

## Accomplishments

- Added a strict report reconstructor that validates the exact merge payload bytes and SHA-256 receipt before mapping immutable terminal facts back to frozen campaign units.
- Recomputes all terminal counts, Clopper-Pearson intervals, target bands, source-denominator qualification, paired tables, and finite-look decisions from the preserved evidence rather than shard summary fields.
- Rejects report, target, receipt, and terminal drift during independent semantic-byte replay.
- Retains full outcome status counts, acceptance and conditional denominators, timeout visibility, separate work-vector dimensions, resource/timing/allocation observations, and reasons for unavailable measurements.
- Restricts persisted environment observations to non-secret numerical-library thread settings.

## Task Commits

1. **Task 1 RED: add failing report reconstruction tests** — `1f1cecc` (`test`)
2. **Task 1 GREEN: reconstruct reports from verified campaign evidence** — `d634082` (`feat`)
3. **Task 2 RED: add failing resource accounting report test** — `3f84f84` (`test`)
4. **Task 2 GREEN: retain campaign work and resource context** — `0879397` (`feat`)
5. **Rule 1: replay every declared finite assessment look** — `ce6745d` (`fix`)

## TDD Gate Compliance

- **Task 1 RED:** [RED evidence](./08-11-TASK-1-RED.json) passed `tdd-red-evidence` with `RED_EVIDENCE_OK`; importing the absent reporting module failed at the named target test.
- **Task 1 GREEN:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'report or reconstruct or receipt or tamper or inconclusive' -x` passed with 7 tests before the later finite-look regression.
- **Task 2 RED:** [RED evidence](./08-11-TASK-2-RED.json) passed `tdd-red-evidence` with `RED_EVIDENCE_OK`; a secret-bearing environment observation was initially accepted.
- **Task 2 GREEN:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'denominator or acceptance or work or resource or timeout or missingness' -x` passed with 3 tests.
- **Regression:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py` passed with 37 tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replayed each declared finite look instead of only the final look.**

- **Found during:** Task 2 regression coverage.
- **Issue:** A multi-look assessment passed only its final observation to the finite-look procedure, which correctly rejected the missing earlier look.
- **Fix:** Reconstruct each declared prefix from the frozen work plan and terminal rows; preserve every look record in the report and test a two-look replay.
- **Files modified:** `src/bp_registry/campaigns/reporting.py`, `tests/test_campaign_statistics.py`
- **Commit:** `ce6745d`

## Security Notes

- Canonical merge bytes, merge SHA-256, plan and assessment digests, and target receipt hashes are all checked before report reconstruction.
- Environment serialization accepts only `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, and `NUMEXPR_NUM_THREADS` with positive decimal values.

## Self-Check: PASSED

- Confirmed reporting module, report tests, and both RED-evidence records exist.
- Confirmed task commits `1f1cecc`, `d634082`, `3f84f84`, `0879397`, and `ce6745d` exist with no tracked-file deletions.
- Confirmed the complete campaign-statistics suite passes: 37 passed.
