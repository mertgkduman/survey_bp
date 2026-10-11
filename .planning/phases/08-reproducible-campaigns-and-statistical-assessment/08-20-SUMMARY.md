---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "20"
subsystem: retained paired canonical campaign gate
tags: [campaigns, canonical-bp, paired-sampling, slurm, statistics, provenance]
requires:
  - phase: 08-19
    provides: matched BB-144 manifests and frozen four-unit work plan
provides:
  - verified local and direct selected-shard real canonical execution evidence
  - independently reconstructed denominator reports and route-equivalence receipt
  - final development gate denying production without measured site ceilings
affects: [phase-08, phase-09, phase-11]
key-files:
  created:
    - data/results/phase8-paired-canonical-gate-v1/assessment.json
    - data/results/phase8-paired-canonical-gate-v1/slurm-route/assessment.json
    - data/results/phase8-paired-canonical-gate-v1/route-equivalence.json
    - data/results/phase8-paired-canonical-gate-v1/verification.json
  modified:
    - src/bp_registry/campaigns/cli.py
    - src/bp_registry/campaigns/execution.py
    - src/bp_registry/campaigns/reporting.py
    - tests/test_campaign_execution.py
decisions:
  - "Execute frozen Slurm shard indexes directly; no scheduler job was submitted without site ceilings."
  - "Keep incomplete pre-fix runs as excluded diagnostics with zero denominator contribution."
  - "Translate supported canonical null outcomes only in the outer campaign receipt."
actuals:
  tasks: 3
  commits: 3
completed: 2026-10-11
status: complete
---

# Phase 08 Plan 20: Retained Paired Canonical Gate

**The installed lifecycle now runs a real two-arm BB-144 campaign on two shared physical samples, verifies each evidence chain, reports uncertainty, and denies production dispatch without site ceilings.**

## Results

- The local route executed four canonical units, independently verified their unchanged ledgers and outer attempt receipts, merged all four terminals, and derived an empty exact resume set.
- The direct selected-shard route executed both frozen array indexes and produced its own verified merge, empty resume set, and complete report. `verify-routes` independently reconstructed both routes and returned `scientific_records_match: true`.
- Each physical sample's materialized bytes and physical-error SHA-256 match across arms and routes. The final receipt binds all manifests, study/plan, sample/error evidence, attempt ledger hashes, merges, reports, route comparison, and test results.
- All four tiny development shots ended in nonconvergence. Both arms have zero accepted samples, so conditional performance is explicitly unavailable. The all-domain target is `development_fixture` / `not_assessed`; no source reproduction or decoder ranking is claimed.
- The historical synthetic operational gate still verifies its recovered stop receipt, zero next-look submissions, and `production_authorization: deny`. The new real route is retained separately.
- No `sbatch` submission occurred. Requested shard bounds were one CPU, 512 MB, ten minutes, and one concurrent task. Direct child-process wall measurements were 5.68 and 5.07 seconds, with a cumulative peak child RSS upper bound of 119,200 kB. Scheduler allocation/accounting remains unavailable; the final gate retains `production_authorization: deny`.

## Verification

- Installed `verify --report` passed for both reports; installed `verify-routes` returned verified scientific equality.
- Retained-evidence focused regression: 4 passed, including sample/ledger/receipt tamper rejection and historical gate replay.
- Phase 08 suite: **205 passed** in 335.13 seconds.
- Full workspace suite: **1,158 passed, 1 skipped** in 856.35 seconds; 25 multiprocessing fork deprecation warnings. Both suites exited zero, with logs and status files retained beside this summary.

## Task Commits

1. `5860aed` — verified local campaign, receipt/report integration fixes, and retained-evidence regressions.
2. `ea51040` — direct selected-shard evidence, route equivalence, procedure documentation, and exact merge artifact path.
3. `11ef379` — incomplete pre-fix execution diagnostics, explicitly excluded from scientific denominators.

## Deviations and Repairs

- Real execution exposed canonical `outcome: null` at the fast arm's `max_iterations` stop and Relay's completed leg limit without a candidate. The outer campaign receipt now maps only these supported cases to `nonconvergence`; independent verification repeats the mapping and canonical event bytes are unchanged.
- The development target ID differs from its sole physical point ID. Report reconstruction now resolves that name only for a genuinely one-point frozen plan; multi-point ambiguity remains an error.
- Merge replay now proves indexed run receipts contain exactly the embedded attempt set, and sample/ledger reads are bounded before parsing. The adversarial retained test rejects an unrelated extra indexed delivery.
- The installed paired merge artifact is `campaign-paired-merge.json`; Plan 08-20 and validation commands were corrected accordingly.
- Two incomplete pre-fix local runs remain under `local-failed-*-mapping` with `scientific_denominator_contribution: false`; neither enters the verified report.

## Remaining Condition

Publication-scale or actual Slurm submission needs measured and approved site wall, core, memory, storage, replay, and scheduler-cost ceilings plus accounting. This is a separate production authorization gate, not a missing Phase 08 development result.
