---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "02"
subsystem: campaign assessment contracts
tags: [campaigns, pydantic, prespecification, finite-look, alpha-spending]
requires:
  - phase: 08-01
    provides: frozen one-unit campaign identity and sealed tracer evidence
provides:
  - Strict content-addressed assessment records for targets, uncertainty, families, stopping, outcomes, and scientific caps
  - Fixed-shot and finite-look stopping contracts with bounded, complete alpha allocations
  - A total outcome matrix that keeps infrastructure interruption outside completed denominators
affects: [08-03, 08-04, 08-05, 08-06, 08-07, 08-09, 08-11]
tech-stack:
  added: []
  patterns: [strict frozen Pydantic preflight, digest-bound scientific caps, finite-look alpha-spending]
key-files:
  created:
    - tests/test_campaign_contracts.py
  modified:
    - src/bp_registry/campaigns/contracts.py
key-decisions:
  - "Assessment semantics are content-addressed data, while scheduler allocation remains receipt-only observation."
  - "Phase 8 admits only a declared finite look schedule; fixed-shot campaigns cannot declare interim looks."
  - "Infrastructure interruption is incomplete, and invalid/no-proposal/nonconvergent/timeout decoder terminals remain all-shot failures."
patterns-established:
  - "Every finite-look family-target-look coordinate receives exactly one local alpha allocation whose family total is bounded."
  - "Outcome mappings are exhaustive and reject silent denominator drops."
requirements-completed: [SIM-03, STAT-01, STAT-03, STAT-05]
actuals:
  tokens: 8120
  tasks: 2
  commits: 5
commits: 5
plan_head_before: 0faf56d769904d8f0c508b8af4140973f39608aa
duration: 18min
completed: 2026-10-11
status: complete
coverage:
  - id: D1
    description: Assessment preflight freezes targets, exact interval settings, comparison families, decision rule, resource caps, and their digest.
    requirement: STAT-01
    verification:
      - kind: unit
        ref: tests/test_campaign_contracts.py#test_campaign_assessment_is_strict_and_digest_bound
        status: pass
    human_judgment: false
  - id: D2
    description: Fixed-shot and finite-look stopping records reject interim looks, incomplete alpha grids, and family-alpha overspend.
    requirement: STAT-03
    verification:
      - kind: unit
        ref: tests/test_campaign_contracts.py#test_stopping_rejects_fixed_interim_look_and_unbounded_alpha_spending
        status: pass
    human_judgment: false
  - id: D3
    description: The total outcome matrix retains all-shot failures and marks infrastructure interruption incomplete.
    requirement: STAT-05
    verification:
      - kind: unit
        ref: tests/test_campaign_contracts.py#test_outcome_denominator_matrix_is_total_and_interruption_stays_partial
        status: pass
    human_judgment: false
---

# Phase 8 Plan 02: Prespecified campaign assessment contracts Summary

**Strict campaign assessment records now bind target receipts, uncertainty, resource caps, finite-look inference, and total denominator treatment before execution.**

## Performance

- **Duration:** 18 min
- **Completed:** 2026-10-11
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments

- Added strict, frozen records for target receipt references, exact Clopper-Pearson intervals, comparison families, decision rules, and digest-bound scientific resource caps.
- Added disjoint fixed-shot and finite-look contracts. Finite looks require increasing whole-batch boundaries, a complete family-target-look alpha grid, and total local alpha no greater than the family allocation.
- Added a total terminal-status matrix: nonconvergence, timeout, invalid syndrome, and no proposal count as all-shot failures; infrastructure interruption remains incomplete; postselection must be stated explicitly.
- Added adversarial tests for missing/extra fields, scientific digest drift, nonfinite resource values, invalid stopping, alpha overspending, uncovered outcomes, and interrupted denominator treatment.

## Task Commits

1. **Task 1 RED: add campaign assessment contract tests** — `caa4507`, `0b2baf9` (`test`)
2. **Task 1 GREEN: freeze campaign assessment semantics** — `1c89222` (`feat`)
3. **Task 2 RED: add stopping boundary coverage** — `4b41169` (`test`)
4. **Task 2 GREEN: validate stopping and denominator matrix** — `3e6872c` (`feat`)

## TDD Gate Compliance

- **Task 1 RED:** [RED evidence](./08-02-TASK-1-RED.json) passed `tdd-red-evidence` with `RED_EVIDENCE_OK`; the public strict assessment contract assertion failed before implementation.
- **Task 1 GREEN:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'campaign or identity or resource or drift or strict' -x` passed with 3 tests.
- **Task 2 RED:** [RED evidence](./08-02-TASK-2-RED.json) passed `tdd-red-evidence` with `RED_EVIDENCE_OK`; a fixed-shot campaign wrongly accepted an interim look before validation was added.
- **Task 2 GREEN:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'stopping or alpha or denominator or outcome or partial' -x` passed with 3 tests.
- **Regression:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'tracer or identity or acyclic or zero_failure' -x` passed with 2 tests.

## Files Created/Modified

- `src/bp_registry/campaigns/contracts.py` — strict assessment, resource, stopping, alpha, and outcome contracts linked to campaign identity.
- `tests/test_campaign_contracts.py` — boundary and tamper tests for preflight and denominator rules.

## Decisions Made

- Site HPC limits remain unspecified as directed. The schema records per-campaign scientific caps, while a later profiling gate will derive practical authorization from measured resource evidence.
- Existing Plan 08-01 one-unit tracer records remain supported without an assessment block. Any assessed campaign uses `CampaignAssessmentV1`, whose required fields are strict and digest-bound.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The TDD evidence checker requires a small TAP-normalized assertion record in addition to pytest output. The persisted records passed its `RED_EVIDENCE_OK` gate.

## User Setup Required

None.

## Next Phase Readiness

- Target provenance can now populate `target_receipt_sha256` records in Plan 08-03.
- Planning, merge/resume, and reporting can consume the frozen stopping, outcome, and resource contracts without scheduler allocation entering the scientific digest.

## Self-Check: PASSED

- Confirmed both declared implementation and test files exist.
- Confirmed task commits `caa4507`, `0b2baf9`, `1c89222`, `4b41169`, and `3e6872c` exist with no tracked-file deletions.
