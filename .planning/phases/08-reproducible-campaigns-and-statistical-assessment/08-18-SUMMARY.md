---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "18"
subsystem: paired campaign reporting
tags: [campaigns, reporting, provenance, slurm, verification]
requires:
  - phase: 08-16
    provides: verified paired merge envelopes and typed materialized samples
  - phase: 08-17
    provides: evidence-bound campaign report reconstruction
provides:
  - immutable installed paired assessment reports
  - independent report replay verification
  - local-to-Slurm scientific-equivalence receipts
affects: [phase-08, phase-11, campaign-reporting]
tech-stack:
  added: []
  patterns:
    - installed report verification rebuilds every paired evidence input before comparing retained bytes
    - route comparison separates canonical scientific facts from typed executor observations
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/cli.py
    - src/bp_registry/campaigns/reporting.py
    - src/bp_registry/campaigns/__init__.py
    - tests/test_campaign_execution.py
key-decisions:
  - "Publish paired assessment reports as canonical immutable assessment.json bytes."
  - "Treat absent canonical executor measurements as explicit unavailable observations."
  - "Sort normalized event semantics after removing existing profiler-only fields because event IDs depend on profiler measurements."
actuals:
  tokens: 6914
  tasks: 2
  commits: 3
commits: 3
plan_head_before: 3232c5274f3df914320730e132bb4c0779983b0f
duration: 16min
completed: 2026-10-11
status: complete
---

# Phase 08 Plan 18: Installed Report Lifecycle Summary

**Installed paired campaigns now publish complete immutable reports, independently replay those reports, and prove local and selected-Slurm scientific equivalence.**

## Accomplishments

- Replaced the paired installed assessor's in-memory-only response with canonical atomic `assessment.json` publication, including complete report content, report hash, merge hash, and artifact hash.
- Rebuilds each report from the frozen work plan, verified attempt indexes, canonical merge, typed materialized samples, target evidence, denominator declarations, and named terminal work vectors before publishing or verifying it.
- Added `verify --report`, which rejects changed report bytes, merge evidence, report semantics, samples, work vectors, target data, and denominator treatment before returning a verified response.
- Added `verify-routes`, which independently reconstructs local and selected-Slurm merge/report chains, compares a route-neutral scientific projection, and atomically writes a receipt bound to both merge and report artifacts.
- Exported report reconstruction and report/route verification from `bp_registry.campaigns`.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k installed_assess_emits_complete_campaign_report -x` — passed (1 selected).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k installed_report_verify -x` — passed (1 selected); includes retained-report tamper rejection.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k installed_route_equivalence_verify_reconstructs_both_routes -x` — passed (1 selected, 28.03 seconds).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k public_campaign_facade_exports_work_plan -x` — passed (1 selected).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -x` — passed (42 tests).
- The broader `tests/test_campaign_execution.py -x` command was started, but this executor lost its exit status after the command stream detached. It is intentionally left for the Phase 08 final full-suite gate; the focused installed acceptance checks above are green.

## Task Commits

1. Task 1: `27eb6a5` — `feat(08-18): publish complete paired assessment reports`
2. Task 2: `3cf0931` — `feat(08-18): verify paired reports and routes`
3. Verification coverage: `9c53e4b` — `test(08-18): cover public report verification facade`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Normalize route event order after removing profiler-only values**

- **Found during:** Task 2 installed local/Slurm route-equivalence test.
- **Issue:** Canonical merge ordering used event IDs derived from profiler values. Equivalent local and Slurm events therefore had a different order after the permitted profiler fields were removed.
- **Fix:** Sort the retained complete event semantics canonically after removing only `event_id`, `profile`, `decode_runtime`, and `setup_runtime`.
- **Files modified:** `src/bp_registry/campaigns/reporting.py`
- **Commit:** `3cf0931`

## Known Stubs

None.

## Self-Check: PASSED

- Assigned implementation and test files exist; commits `27eb6a5`, `3cf0931`, and `9c53e4b` are present in Git history.
