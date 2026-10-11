---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "17"
subsystem: campaign reporting
tags: [campaigns, exact-statistics, provenance, immutable-receipts, paired-sampling]
requires:
  - phase: 08-15
    provides: paired canonical terminal receipts and shared materialized physical samples
provides:
  - exact per-arm all-shot, acceptance, and conditional denominator reports
  - named per-terminal work totals and complete frozen treatment tables
  - byte-replayable reports bound to merge and materialized-sample evidence
affects: [phase-08, campaign-assessment, installed-campaign-lifecycle]
tech-stack:
  added: []
  patterns:
    - report reconstruction validates all evidence before forming denominators
    - work dimensions are retained and summed only by their declared name
    - materialized samples are keyed by frozen physical sample identity
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/statistics.py
    - src/bp_registry/campaigns/reporting.py
    - tests/test_campaign_statistics.py
key-decisions:
  - "Require one named nonnegative work vector for every verified terminal rather than inventing zero work."
  - "Require materialized sample evidence keyed by UnitKey.physical_sample_identity and revalidate its sample and physical-error digests during report reconstruction."
  - "Expose merge_receipt_sha256 explicitly while retaining it and materialized receipt hashes in input_receipt_hashes."
requirements-completed: [LED-05, STAT-02, STAT-05]
actuals:
  tokens: 6748
  tasks: 2
  commits: 5
commits: 5
plan_head_before: 59300b20489b5ce0e8e5e7463c6d579831e47a8e
coverage:
  - id: D1
    description: "Each assessed point reports exact all-shot, acceptance, conditional, treatment, incomplete, and named-work evidence for every arm."
    requirement: STAT-05
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_report_serializes_denominator_uncertainty_per_arm
        status: pass
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_zero_acceptance_keeps_treatment_visible_with_explicit_conditional_reason
        status: pass
    human_judgment: false
  - id: D2
    description: "Campaign reports recompute immutable merge and materialized-sample provenance and reject changed operational context."
    requirement: LED-05
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_report_merge_hash_and_context_tamper_are_bound_to_semantic_bytes
        status: pass
      - kind: unit
        ref: tests/test_campaign_statistics.py#test_report_named_work_rejects_missing_or_extra_terminal_vectors
        status: pass
    human_judgment: false
duration: 3min
completed: 2026-10-11
status: complete
---

# Phase 08 Plan 17: Evidence-Only Denominator Reporting Summary

**Exact per-arm campaign reports now retain outcome treatment, uncertainty, named work, operational context, and independently revalidated merge and sample provenance.**

## Accomplishments

- Connected every point and arm to `outcome_denominator_summary`, including exact all-shot, acceptance, and conditional performance evidence.
- Retained the complete frozen outcome-treatment table and an explicit `zero accepted samples` conditional-unavailability reason.
- Required one named work vector for each verified terminal and totalled work only within matching dimensions.
- Bound `CampaignReportV1` to its verified canonical merge hash and mandatory `MaterializedPhysicalSampleV1` records keyed by `UnitKey.physical_sample_identity`.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'report_serializes_denominator_uncertainty_per_arm or zero_acceptance or outcome_treatment or named_work' -x` — passed (3 selected).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'report and (merge_hash or context_tamper or byte_stable or boundary)' -x` — passed (1 selected).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -x` — passed (42 tests).

## Task Commits

1. Task 1 RED: `e4c80f2` — `test(08-17): define per-arm report denominators`
2. Task 1: `35a5437` — `feat(08-17): report exact per-arm denominators`
3. Task 2 RED: `222f623` — `test(08-17): define immutable report provenance`
4. Task 2: `19c798c` — `feat(08-17): bind reports to merge evidence`

The measured ledger count is five because concurrent Plan 08-16 committed `35b9a3e` between this plan's atomic commits on the shared branch; it is intentionally excluded from the task list.

## Interface for Campaign Lifecycle Wiring

`reconstruct_campaign_report()` and `verify_campaign_report()` require:

- `work_vectors_by_unit`: a mapping from every verified terminal `UnitKey.key` to a nonempty mapping of named nonnegative integer dimensions.
- `materialized_samples_by_identity`: a mapping from every verified `UnitKey.physical_sample_identity` to its `MaterializedPhysicalSampleV1` artifact.

Reconstruction revalidates each materialized artifact's canonical bytes, `materialized_sample_sha256`, and `physical_error_sha256`; inserts both receipt kinds into `input_receipt_hashes`; and rejects missing, extra, or context-mismatched artifacts. The campaign lifecycle must supply these verified attempt artifacts when it assesses a merged campaign.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Next Phase Readiness

The installed assessment path can now supply verified materialized artifacts, named unit work, and allowlisted observations to produce a complete evidence-only report.

## Self-Check: PASSED

- All three implementation/test files and this summary exist.
- The four 08-17 task commits are present in Git history.
