---
phase: 11-quaternary-reproduction-and-comparisons
plan: "10"
subsystem: quaternary controlled calibration and production authorization
tags: [BB72, GB46, quaternary, paired-calibration, typed-work, default-deny]
requires:
  - phase: 11-08
    provides: fixed-marginal three-point design and precision receipt
  - phase: 11-09
    provides: bounded GB46 public controlled lifecycle
provides:
  - Digest-bound BB72 three-point controlled calibration design
  - Arm and component native work with common callback-wall timing evidence
  - Two-code default-deny production authorization package
affects: [11-11, quaternary-controlled-comparisons, production-dispatch]
tech-stack:
  added: []
  patterns: [qualified-code loader, typed native-unit timing, deterministic deny-only authorization package]
key-files:
  created:
    - data/studies/phase11-bb72-joint-separate.json
    - data/results/phase11-production-authorization.json
    - tests/test_phase11_resource_gate.py
  modified:
    - src/bp_registry/campaigns/contracts.py
    - src/bp_registry/campaigns/controlled_execution.py
    - src/bp_registry/campaigns/profiling_gate.py
    - tests/test_phase11_joint_separate.py
    - tests/test_phase11_quaternary_campaign.py
decisions:
  - "BB72 retains source-reported distance 6 and project-derived logical qualifications; neither becomes a platform verification claim."
  - "Joint BP4 and separate binary arms report native named work beside callback-wall runtime without cross-unit conversion."
  - "The Phase 11 package is immutable deny-only: missing site capacity, accounting, quota/cost, source eligibility, or persisted profiles prevents a dispatch token."
metrics:
  duration: 20m 32s
  completed: 2026-10-14
status: complete
actuals:
  tokens: 10145
  tasks: 3
  commits: 7
commits: 7
plan_head_before: 153039d5fd4b3699abc07042f44a1fed196b0d23
requirements-assessed: [QEV-01, QEV-02]
---

# Phase 11 Plan 10: BB72 Calibration and Default-Deny Authorization Summary

**Qualified the existing BB72 artifact for the public three-point matched lifecycle, retained native work and wall-time facts per arm, and wrote a two-code production package that cannot authorize dispatch.**

## Accomplishments

- Added the BB72 controlled-calibration manifest with exact artifact and provenance digests. It keeps source-reported distance 6 separate from project-derived logical operators and rejects any drift in those qualifications.
- Generalized the established public controlled lifecycle to load either qualified GB46 or BB72 code evidence. The BB72 regression runs, replays, verifies, and assesses six bounded paired records across the frozen three points.
- Extended matched-pair evidence with arm and X/Z component callback-wall runtimes. Native BP4 and binary SPA work mappings stay named independently, and verifier output reports them side by side without a conversion factor.
- Added `Phase11DispatchProposalV1` and a deterministic package covering both code calibrations, controlled/source campaign requests, paired precision, site evidence, accounting, quota/cost, forecasts, and authorization status.
- Wrote the checked-in package at `data/results/phase11-production-authorization.json`; it has `decision: deny`, no dispatch token, and explicit reasons for every missing external prerequisite.
- Added the read-only `verify-authorization` public command. It validates the exact retained package digest, both calibration manifests, site/accounting/precision facts, and deny-only eligibility before printing the receipt.

## Checks Run

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py tests/test_phase11_quaternary_campaign.py -k 'bb72 and (tracer or independence or provenance or distance or replay)' -x` — passed (2 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_quaternary_campaign.py tests/test_phase11_resource_gate.py -k 'bb72 and (three_point or work or runtime or resource or limit or merge)' -x` — passed (1 test).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_resource_gate.py -k 'proposal or deny or ceiling or accounting or stale or source or precision or digest' -x` — passed (5 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase11_controlled.py verify-authorization --package data/results/phase11-production-authorization.json` — passed; returned the retained deny receipt with no dispatch token.

## TDD Evidence

- Task 1 RED: `test_bb72_tracer_preflight_binds_artifact_provenance_and_qualifications` failed because the BB72 design was absent; `56d2e98` records the regression before `ae0464f` supplied the manifest and qualified loader.
- Task 2 RED: `test_bb72_typed_work_and_wall_runtime_are_retained_without_unit_conversion` failed because typed runtime fields were absent; `8da0dfc` and `8455626` precede `2663aef`, which retains arm/component runtime evidence and completes the three-point lifecycle.
- Task 3 RED: `test_phase11_proposal_is_decision_ready_but_default_deny` failed because no package builder existed; `aa8e751` precedes `aa56ba5`, which implements the deny-only package.

## Task Commits

1. `56d2e98` — `test(11-10): add BB72 qualified preflight regression`
2. `ae0464f` — `feat(11-10): qualify BB72 controlled calibration`
3. `8da0dfc` — `test(11-10): add typed runtime regression`
4. `8455626` — `test(11-10): add BB72 three-point resource regression`
5. `2663aef` — `feat(11-10): retain BB72 typed work and runtime`
6. `aa8e751` — `test(11-10): add default-deny authorization regressions`
7. `aa56ba5` — `feat(11-10): add default-deny production package`

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Bug] Raised the timing evidence bound from event-count scale to a bounded nanosecond scale.
   - **Found during:** Task 2
   - **Issue:** A valid BB72 callback runtime exceeded the existing event-count maximum.
   - **Fix:** Bounded timing values by signed 64-bit nanoseconds while retaining nonnegative validation.
   - **Files modified:** `src/bp_registry/campaigns/contracts.py`
   - **Commit:** `2663aef`

## Known Stubs

The production package intentionally retains unavailable `predicted_memory_bytes`, `predicted_wall_time_ns`, and `predicted_typed_work` because no persistent, scheduler-qualified calibration profile or site ceilings exist. These values block dispatch and are tracked in the package receipt rather than used as estimates.

## Next Phase Readiness

Plan 11-11 remains the blocking human authorization gate. QEV-01 and QEV-02 retain their plan-declared manual review flags; this package supplies evidence and cannot resolve those judgments or enable a production dispatch.

## Self-Check: PASSED

- Confirmed all eight implementation, data, and regression files exist.
- Confirmed all seven task commits exist in Git history.
- The stub scan found no placeholder implementation values; the three unavailable forecast fields are intentional deny gates described above.
