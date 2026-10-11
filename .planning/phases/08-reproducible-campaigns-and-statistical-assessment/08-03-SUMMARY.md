---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "03"
subsystem: campaign-target-provenance
tags: [pydantic, sha256, source-targets, plot-digitization, statistical-assessment]
requires: [08-02]
provides: [immutable-source-target-receipts, calibrated-digitization-receipts]
affects: [phase-09-css-reproduction, phase-11-quaternary-reproduction]
tech_stack:
  added: []
  patterns: [strict-frozen-receipts, confined-byte-snapshots, extrema-frozen-intervals]
key_files:
  created:
    - src/bp_registry/campaigns/targets.py
    - tests/test_campaign_targets.py
  modified: []
decisions:
  - "SHA-256 records content integrity linkage and explicitly does not assert source authorship."
  - "Unavailable published denominators remain unavailable with a reason; no count is inferred."
  - "Publication digitization requires distinct operators on two or more passes and freezes each point at the exact retained extrema."
metrics:
  duration: "~20 minutes"
  completed: "2026-10-11"
  tasks: 2
  files: 2
actuals:
  tokens: 6121
  tasks: 2
  commits: 4
plan_head_before: 98a4066bb0d6a38ddde09cd78f6a5b48ccbc6c15
commits: 4
status: complete
---

# Phase 08 Plan 03: Immutable Campaign Target Receipts Summary

Source table and figure targets now carry strict, content-addressed provenance, direct-source precision, published denominator status, and reproducible digitization calibration evidence.

## Accomplishments

- Added immutable source/table target receipts for URI or DOI, revision, access date, exact table cell, byte snapshot, reported bounds and precision, and explicit denominator availability.
- Added confined evidence snapshot reading that rejects absolute paths, traversal, and symlink hops; receipt hashes are explicitly integrity linkage rather than authorship claims.
- Added WebPlotDigitizer-style four-point X1/X2/Y1/Y2 calibration receipts with figure/page/panel/curve/crop metadata, raw project and export snapshots, clicks, operator timestamps, and tool identity.
- Required at least two independently labeled extraction passes and froze each pre-simulation interval to the exact repeated-pass extrema and spread.

## Task Commits

1. **Task 1: Bind direct source targets and denominator status**
   - `6d3f1c6` `test(08-03): add failing source target receipt coverage`
   - `093d155` `feat(08-03): bind direct source target receipts`
2. **Task 2: Preserve digitization calibration and repeated extraction uncertainty**
   - `efbc009` `test(08-03): add failing digitization receipt coverage`
   - `fdc4773` `feat(08-03): preserve digitization calibration receipts`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_targets.py -k 'source or table or denominator or tamper or path' -x` — 6 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_targets.py -k 'digitization or calibration or click or repeated or precision' -x` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_targets.py -x` — 8 passed.
- `git diff --check` — passed.

## TDD Evidence

- Task 1 RED: target module import failed before the source receipt implementation; test committed in `6d3f1c6`.
- Task 2 RED: digitization receipt API import failed before the calibration implementation; test committed in `efbc009`.

## Decisions Made

- SHA-256 fields bind immutable evidence bytes but are never treated as proof of an author's identity.
- A published denominator can be `observed`, `unavailable`, or `not_applicable`; unavailable and not-applicable states require a reason and cannot carry an inferred count.
- Repeated figure extractions must be independently attributed and retain the exact click-derived extrema, preventing later widening or narrowing of a target interval.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The generic `gsd check tdd-red-evidence` command could not parse this Markdown plan as its expected JSON record. The committed RED test runs provide the retained failing evidence for both tasks.

## Known Stubs

None.

## Next Phase Readiness

Phase 9 and Phase 11 can create paper-specific targets by supplying immutable source or digitization receipts and passing the resulting digest into their already-frozen campaign assessment targets.

## Self-Check: PASSED

- `src/bp_registry/campaigns/targets.py` and `tests/test_campaign_targets.py` exist.
- All four task commits are present in repository history.

---

*Phase: 08-reproducible-campaigns-and-statistical-assessment*
*Completed: 2026-10-11*
