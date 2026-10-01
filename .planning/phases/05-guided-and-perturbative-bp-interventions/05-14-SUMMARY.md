---
phase: 05-guided-and-perturbative-bp-interventions
plan: "14"
status: complete
subsystem: sealed-b1-mechanism-evaluation
tags: [b1, matched-samples, intervention-ledger, replay-verified]
requires: [05-10]
provides:
  - verified sixteen-sample seven-arm B1 mechanism evaluation
  - complete retained attempt and typed-work ledger
  - explicit replay and aggregate reconciliation
affects: [05-11, 05-13, phase5-verification]
requirements-completed: [MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04]
completed: 2026-10-01
---

# Phase 5 Plan 14: Sealed B1 mechanism evaluation

The evaluation began only after the exact B1 artifact and ordered matrices, two-CPU Slurm entitlement, corrected four-shot calibration, passing objective cap-freeze self-audit, source qualifications, fixed arm controls, and all binding digests passed preflight. Its 16 `p=0.07` physical sample identities are disjoint from the four calibration identities and the superseded first pilot. Each physical sample is shared by one identity baseline and six separate single-intervention arms; no arm combines interventions.

The retained result has 16 matched samples and 112 admitted arm shots. All seven arm ledgers have 16 terminal and typed-work records, and the aggregate ledger contains 4,983 events, including 1,083 attempt rows. Failed, denied, invalid, cap-hit, unavailable, and no-proposal paths remain inspectable; selected candidates are checked on the original problem. Per-arm result reconstruction replayed every shot before publication. A separate public `--verify` pass then replayed all seven arms and passed aggregate ledger, digest, and matched-identity reconciliation. The post-run cap-freeze self-audit passed with the same seal digest.

The output is labeled `pilot_adaptation` and `not_assessed`. It makes no performance ranking, curve-agreement, statistical reproduction, or superiority claim. The earlier pilot at Git commit `5bdc3d9` remains superseded development evidence; its outcomes did not change the prespecified numerical caps or source variants.

The 43 public Phase 5 execution tests passed, the deterministic BB-144/HGP fixtures passed, the intervention-design check passed 16,388 cases, and the regenerated notebook and standalone HTML passed their checks. The complete test suite was covered by the canonical, non-ledger, and ledger runs: 678 passed and one skipped. The ledger module was run alone after an unrelated concurrent timing check exceeded its 10-second wait; all 13 ledger tests passed without B1 contention.
