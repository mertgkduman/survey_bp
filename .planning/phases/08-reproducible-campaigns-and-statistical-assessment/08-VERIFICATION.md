---
phase: 08-reproducible-campaigns-and-statistical-assessment
verified: 2026-10-11T10:43:56Z
status: passed
score: 7/7 must-haves verified
covered_files:
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-01-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-01-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-02-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-02-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-03-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-03-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-04-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-04-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-05-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-05-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-06-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-06-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-07-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-07-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-08-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-08-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-09-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-09-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-10-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-10-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-11-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-11-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-12-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-12-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-13-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-13-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-14-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-14-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-15-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-15-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-16-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-16-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-17-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-17-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-18-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-18-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-19-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-19-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-20-PLAN.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-20-SUMMARY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-REVIEW.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-SECURITY.md
  - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-VALIDATION.md
  - data/manifests/phase8-paired-bb144-fast.json
  - data/manifests/phase8-paired-bb144-slow.json
  - data/results/phase8-operational-gate-v1/assessment.json
  - data/results/phase8-operational-gate-v1/profiling-authorization.json
  - data/results/phase8-paired-canonical-gate-v1/assessment.json
  - data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json
  - data/results/phase8-paired-canonical-gate-v1/local/campaign-paired-merge.json
  - data/results/phase8-paired-canonical-gate-v1/route-equivalence.json
  - data/results/phase8-paired-canonical-gate-v1/slurm-route/assessment.json
  - data/results/phase8-paired-canonical-gate-v1/slurm-route/campaign-paired-merge.json
  - data/results/phase8-paired-canonical-gate-v1/verification.json
  - data/studies/phase8-paired-canonical-gate-v1.json
  - docs/campaigns.md
  - src/bp_registry/campaigns/__init__.py
  - src/bp_registry/campaigns/cli.py
  - src/bp_registry/campaigns/contracts.py
  - src/bp_registry/campaigns/execution.py
  - src/bp_registry/campaigns/identity.py
  - src/bp_registry/campaigns/planning.py
  - src/bp_registry/campaigns/profiling_gate.py
  - src/bp_registry/campaigns/reporting.py
  - src/bp_registry/campaigns/shards.py
  - src/bp_registry/campaigns/slurm.py
  - src/bp_registry/campaigns/statistics.py
  - src/bp_registry/campaigns/targets.py
  - tests/canonical/test_truth_boundary.py
  - tests/test_campaign_contracts.py
  - tests/test_campaign_execution.py
  - tests/test_campaign_profile_gate.py
  - tests/test_campaign_shards.py
  - tests/test_campaign_statistics.py
  - tests/test_campaign_targets.py
  - tests/test_canonical_cli.py
covered_digest: "v1:sha256:e5b2c9b0bd6aa89eb730ef7196c20bf2510cd58d565276fe6a684ff945ba4e32"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/7
  gaps_closed:
    - "Real paired canonical execution now reaches installed plan, local and selected-shard run, resume, and assess."
    - "Denominator uncertainty, treatment, conditional performance, work, and merge provenance now reach complete reports."
  gaps_remaining: []
gaps: []
---

# Phase 8 — Goal Verification

**Result: 7/7 observable truths verified.** As a researcher, I want to run, resume, and statistically assess paired experiments, so that I can preserve sample identity and stopping semantics while reporting uncertainty.

| # | Observable truth | Verdict | Evidence |
|---|---|---|---|
| 1 | One coherent public paired plan/run/resume/assess lifecycle executes real decoders. | VERIFIED | Installed commands froze four units, ran both canonical arms locally and by direct selected shard, verified attempts, merged, resumed empty, and assessed. The historical synthetic fixture remains separate. |
| 2 | Matched arms share exact physical samples independently of arm randomness and route. | VERIFIED | The final gate recomputes two materialized artifact byte hashes and physical-error hashes across all arm/route uses; decoder randomness identities remain arm scoped. |
| 3 | Frozen work survives local and bounded selected-shard transport, exact merge/resume, and tamper rejection. | VERIFIED | Two immutable shards and four units independently verify. Each route has an empty resume set; route verification returns scientific equality. Receipt, ledger, sample, and indexed-delivery tamper tests reject drift. No Slurm job was submitted. |
| 4 | Assessment inputs freeze target, method, family, stopping, and provenance before execution. | VERIFIED | The strict study and work plan bind source, environment, dependency, manifest, sampler, target, assessment, and plan digests. No-write preflight was checked. |
| 5 | Statistical fixtures cover rare/zero events, stopping, incomplete evidence, and pairing. | VERIFIED | The Phase 8 suite passed 205 tests, including exact intervals and adversarial evidence cases; the full workspace suite passed 1,158 with one skip. |
| 6 | Reports expose denominators, uncertainty, treatment, work/context, and merge provenance. | VERIFIED | Both independently reconstructed campaign reports carry per-arm denominator summaries, exact acceptance/all-shot uncertainty, zero-acceptance conditional missingness, named work, treatment table, input hashes, and exact merge receipt SHA-256. |
| 7 | Representative resource evidence is measured and production work remains gated by site ceilings. | VERIFIED | Direct shard process times and cumulative child RSS bounds are retained. Scheduler allocation/accounting was not observed. The historical gate verifies a recovered stop receipt, zero next-look submissions, and production denial; the new gate also denies production. |

## Requirements and Scope

LED-05; SIM-01, SIM-02, SIM-03; and STAT-01 through STAT-05 are satisfied for Phase 8's bounded development scope. The retained real two-arm fixture is development_fixture / not_assessed. All four shots ended in nonconvergence, so zero accepted samples and unavailable conditional performance are correctly reported. It makes no source-curve or decoder-superiority claim. Phase 9 owns paper-specific CSS publication targets and budgets; actual Slurm submission and publication-scale campaigns require measured site ceilings.

## Behavioral Checks

- Installed report verification passed independently for local and direct selected-shard reports.
- Installed route verification returned verified true and scientific_records_match true.
- The historical operational verifier returned verified true, a recovered stop receipt, zero next-look submissions, and production_authorization deny.
- Focused retained-evidence checks: 4 passed. Phase suite: 205 passed. Full suite: 1,158 passed, 1 skipped. Both exited zero; logs and status files are retained.
- Code review has zero open findings. The security audit closes 71/71 unique registered threats with zero open.

## Human Verification

None is required for the scoped Phase 8 development contract. Missing site ceilings are a later production authorization condition, explicitly denied in the retained gate rather than inferred from this small run.
