---
phase: 05-guided-and-perturbative-bp-interventions
plan: "10"
status: complete
subsystem: bounded-b1-pilot-calibration
tags: [b1, matched-samples, scheduler-entitlement, cap-freeze]
requires: [05-08]
provides:
  - verified four-shot seven-arm calibration ledger
  - exact ordered B1 matrix and logical identity gate
  - scheduler entitlement and objective cap-freeze seal
  - frozen sixteen-shot evaluation manifest
affects: [05-14, 05-11, 05-13]
requirements-completed: [MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04]
completed: 2026-10-01
---

# Phase 5 Plan 10: B1 calibration and cap freeze

The prespecified `p=0.07` calibration used four matched physical B1 sample identities across one baseline and six separate single-intervention arms. All 28 admitted shots have terminal records, typed unique-leaf work, and public per-arm results. The runner checked the frozen B1 artifact's raw, semantic, ordered matrix, and logical identities before sampling.

The Slurm entitlement records job, account, partition, QOS, node, two allocated CPUs, memory, walltime, and one OpenMP thread per arm. Independent arms ran in at most two worker processes. The objective freeze records attempt statuses, no-proposal slots, cap hits, terminal classes, and typed work; it retains unsuccessful paths. It does not use logical outcomes to change ceilings.

The evaluation manifest seals sixteen disjoint physical samples, exactly seven arm slots, source qualifications, fixed controls, the entitlement digest, calibration result and ledger digests, and the cap-freeze digest. Both the initial self-audit and a fresh audit after the ordered B1 identity gate passed. Three focused design and fail-closed tests passed. Evaluation had no output when the seal was created.

A source review exposed incomplete work receipts and wall-clock boundary handling in the first pilot. Its calibration and evaluation records were superseded. The retained calibration uses the `corrected_work_accounting_v2` revision, fresh physical sample and decoder-seed namespaces, and new run identities. Its 28 shots were executed and replay-checked, and the cap freeze was recomputed from those records without changing the prespecified numerical ceilings. The frozen evaluation identities are disjoint from both the current calibration and the superseded first run. The cap-freeze self-audit passed against the new manifest before evaluation began.

The retained result remains `pilot_adaptation` and `not_assessed`; no ranking or curve agreement is inferred.
