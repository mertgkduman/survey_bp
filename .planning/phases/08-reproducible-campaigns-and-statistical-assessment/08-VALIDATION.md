---
phase: "08"
slug: "reproducible-campaigns-and-statistical-assessment"
status: validated
nyquist_compliant: true
wave_0_complete: true
gap_closure_status: pending
gap_closure_plans: ["08-15", "08-16", "08-17", "08-18", "08-19", "08-20"]
created: "2026-10-11"
---

# Phase 8 — Validation Strategy

This is the pre-execution test contract. The planner assigns task IDs and waves; each plan must name a focused automated verification command and update the task map below.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config | `pyproject.toml` |
| Quick run | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py tests/test_campaign_statistics.py` |
| Phase run | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_*.py tests/test_ledger.py tests/test_sampling.py tests/test_canonical_cli.py tests/canonical/test_profiling.py` |
| Full suite | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Feedback target | Focused tests within 60 seconds; phase run after each wave; full suite at the phase gate |

## Per-Requirement Verification Map

| Requirement | Planned verification | Test file | Current status |
|-------------|----------------------|-----------|----------------|
| LED-05 | 08-01 T1; 08-05 T1-T2; 08-06 T1-T2; 08-11 T1; 08-14 T2 — durable validation, exact merge, replay, resume, and reconstruction | `tests/test_campaign_shards.py` | Pass |
| SIM-01 | 08-04 T1-T2; 08-09 T1-T2; 08-14 T2 — arm/worker invariance and persisted-sample fallback | `tests/test_campaign_execution.py` | Pass |
| SIM-02 | 08-09 T1; 08-10 T1-T2; 08-12 T2; 08-14 T2 — one plan across local/Slurm with resource, timing, and work facts | `tests/test_campaign_execution.py` | Pass |
| SIM-03 | 08-02 T1-T2; 08-06 T1-T2; 08-10 T2; 08-12 T1 — exact resume and identity/rule/dependency drift rejection | `tests/test_campaign_shards.py` | Pass |
| STAT-01 | 08-02 T1-T2; 08-03 T1-T2; 08-07 T1; 08-11 T1 — prespecified targets, effects, methods, families, stopping, and decisions | `tests/test_campaign_contracts.py` | Pass |
| STAT-02 | 08-01 T1; 08-07 T1; 08-11 T2 — integer counts and exact rare-event boundary intervals | `tests/test_campaign_statistics.py` | Pass |
| STAT-03 | 08-02 T2; 08-06 T2; 08-07 T2; 08-09 T2 — fixed/finite looks, alpha, overshoot, and partial evidence | `tests/test_campaign_statistics.py` | Pass |
| STAT-04 | 08-03 T1-T2; 08-07 T1; 08-11 T1 — source and digitization bytes, calibration, precision, and missing sample n | `tests/test_campaign_targets.py` | Pass |
| STAT-05 | 08-02 T2; 08-08 T1-T2; 08-11 T2 — paired cells, intervals, multiplicity, denominators, and acceptance | `tests/test_campaign_statistics.py` | Pass |
| Operational gate | 08-13 T1-T2; 08-14 T1-T2 — representative decoder/replay throughput, storage, scheduler cost, and authorization | `tests/test_campaign_profile_gate.py` | Pass; production gate denies without site ceilings |

## Gap-Closure Nyquist Map

The historical statuses and pass counts above describe Plans 08-01 through 08-14. Plans 08-15 through 08-20 add the following focused checks; each remains pending until its executor records the actual result in the plan summary.

| Plan task | Requirements | Focused automated verification | Status |
|-----------|--------------|---------------------------------|--------|
| 08-15 T1 | LED-05, SIM-01, SIM-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'public_paired_canonical_local_lifecycle or paired_canonical_replays_identical_error_bytes or paired_canonical_rejects_equal_labels_with_different_material or paired_canonical_rejects_attempt_or_ledger_tamper' -x` | Pending |
| 08-15 T2 | LED-05, SIM-01, SIM-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'installed_paired_canonical_local_lifecycle or public_campaign_facade_exports_work_plan' -x` | Pending |
| 08-16 T1 | LED-05, SIM-01, SIM-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'paired_canonical_local_and_slurm_routes_match or paired_canonical_slurm_array_is_bounded' -x` | Pending |
| 08-16 T2 | LED-05, SIM-02, SIM-03 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'paired_canonical_resume or mixed_route_merge or stop_before_resubmit' -x` | Pending |
| 08-17 T1 | LED-05, STAT-02, STAT-05 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'report_serializes_denominator_uncertainty_per_arm or zero_acceptance or outcome_treatment or named_work' -x` | Pending |
| 08-17 T2 | LED-05, STAT-02, STAT-05 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'report and (merge_hash or context_tamper or byte_stable or boundary)' -x` | Pending |
| 08-18 T1 | LED-05, STAT-01, STAT-02, STAT-03, STAT-05 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'installed_assess_emits_complete_campaign_report or installed_assess_preserves_partial_and_postselection_treatment' -x` | Pending |
| 08-18 T2 | LED-05, SIM-02, SIM-03, STAT-01, STAT-02, STAT-03, STAT-05 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'installed_report_verify or installed_report_tamper or installed_route_equivalence_verify_reconstructs_both_routes or route_equivalence_rejects_sample_or_science_drift or report_reassessment_is_byte_stable' -x` | Pending |
| 08-19 T1 | SIM-01, SIM-02, STAT-01 | `OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign plan --campaign data/studies/phase8-paired-canonical-gate-v1.json --campaign-root . --output-root data/results/phase8-paired-canonical-gate-v1` | Pending |
| 08-19 T2 | SIM-01, SIM-02, STAT-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'paired_canonical_gate_definition_and_documented_lifecycle' -x` | Pending |
| 08-20 T1 | LED-05, SIM-01, SIM-03, STAT-01, STAT-02, STAT-03, STAT-05 | `OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign verify --report data/results/phase8-paired-canonical-gate-v1/assessment.json --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json --merge data/results/phase8-paired-canonical-gate-v1/local/campaign-merge.json --campaign-root .` | Pending |
| 08-20 T2 | LED-05, SIM-01, SIM-02, SIM-03, STAT-01, STAT-02, STAT-03, STAT-05 | `OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign verify-routes --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json --local-merge data/results/phase8-paired-canonical-gate-v1/local/campaign-merge.json --local-report data/results/phase8-paired-canonical-gate-v1/assessment.json --slurm-merge data/results/phase8-paired-canonical-gate-v1/slurm-route/campaign-merge.json --slurm-report data/results/phase8-paired-canonical-gate-v1/slurm-route/assessment.json --campaign-root . --output data/results/phase8-paired-canonical-gate-v1/route-equivalence.json` | Pending |
| 08-20 T3 | LED-05, SIM-01, SIM-02, SIM-03, STAT-05 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'retained_paired_canonical_gate_verifies or paired_canonical_rejects_attempt_or_ledger_tamper or operational_gate_verify_requires_retained_bounded_evidence' -x` | Pending |

Gap closure retains the existing Wave 0 infrastructure. The new tests must first prove one materialized physical error is byte-identical across arms, reject equal labels with different code/channel/sample material, reject attempt-receipt or canonical-ledger tampering while leaving canonical event fields and sampler identity unchanged, reconstruct both local and selected Slurm evidence chains, and verify report denominators and merge binding.

## Wave 0 Requirements

- [x] Create the six test files above, using tiny deterministic terminal fixtures for shard corruption and reconstruction cases.
- [x] Include adversarial fixed and adaptive stopping fixtures before implementing assessment decisions.
- [x] Preserve existing canonical ledger, sampler, CLI, and profiling tests in the phase run.

## Sampling Rate

- After each task: run its focused test module and its relevant existing regression module.
- After each wave: run the phase command above.
- Before phase verification: run the full suite and a bounded local/HPC-equivalent campaign with retained replay and profiling receipts.
- No three consecutive tasks may lack an automated verification command.

## Manual-Only Verifications

Site allocation ceilings and production campaign budgets require later user/site input. The Phase 8 implementation is verified with bounded synthetic and representative local runs; it does not authorize a large publication campaign without the measured operational gate.

## Validation Sign-Off

- [x] Every planned task has an automated command or a named Wave 0 prerequisite.
- [x] Phase tests cover all nine mapped requirements.
- [x] Phase suite: 95 passed at the initial sign-off; final full suite: 1141 passed, 1 skipped.
- [x] The bounded campaign and operational gate receipts replay from retained evidence.
- [x] Set `nyquist_compliant: true` after the execution audit.

**Approval:** automated evidence complete; production campaign authorization remains denied until measured site ceilings are supplied.

## Validation Audit 2026-10-11

| Metric | Count |
|--------|-------|
| Requirements with automated coverage | 9 |
| Coverage gaps found | 0 |
| Gaps resolved | 0 |
| Escalated | 0 |

The original requirement map was checked against the Phase 8 test modules and all fourteen completed plan summaries. The targeted campaign suite passed 95 tests at the initial sign-off. After review fixes and fixture regeneration, the full suite passed 1,141 tests with one skip. The retained operational gate verified its receipts, including stop recovery and zero next-look submissions. Those counts are historical evidence and are unchanged by the pending 08-15 through 08-20 checks. Site ceilings remain a separate production authorization condition.
