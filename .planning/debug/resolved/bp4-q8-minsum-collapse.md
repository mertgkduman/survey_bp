---
status: resolved
trigger: "inspect why vanilla BP4 min-sum almost never converges"
created: 2026-10-27
updated: 2026-10-27
---

## Symptoms

The experimental Q8 BP4 min-sum arm at scale 16, damping 0 misses the target
syndrome on 43,306/50,000 B1 shots at p=0.10 and 10,637/50,000
double-Gross shots at p=0.08. All of these failures reach T=1,000.

## Current Focus

- hypothesis: Confirmed on bounded matched errors: internal clipping of
  identity-referenced V2C messages and both log-sum-exp operands in the
  commutation projection jointly destroys local BP4 min-sum convergence.
- test: Four-arm matched ablation preserving Q8 scalar check messages.
- expecting: Observed: removing both clipping sites restored convergence;
  removing either alone did not.
- next_action: None for diagnosis. Any replacement Q8 policy needs a new
  policy identity and separate qualification.

## Evidence

- timestamp: 2026-10-27; source inspection found Q8 saturation at each V2C
  update and separate clipping of both projection log-sum-exp operands.
- timestamp: 2026-10-27; ephemeral matched diagnostic found 87/100 B1 and
  51/200 double-Gross failures in the original Q8 arm, versus 0/100 and 0/200
  after removing both clipping sites. These exploratory counts require durable
  ledgers before final reporting.
- timestamp: 2026-10-27; durable ledgers and independent audit confirmed the
  same four-arm outcome counts, complete shared-error hashes, per-arm outcome
  partitions, and ledger SHA-256 checks. See
  from_dr_pfister_presentetations/results/performance_investigation/Q8_MINSUM_CLIPPING_INSPECTION.md.

## Resolution

- root_cause: Joint Q8 V2C saturation and separate clipping of both projection
  log masses. Each alone remains a poor policy on the bounded test.
- fix: Diagnostic only; frozen policy outputs were preserved.
- verification: B1 100 paired shots and double-Gross 200 paired shots, each
  with four arms and audited per-shot ledgers. Both-change arm had 0 failures;
  original had 87 and 51, respectively.
- files_changed: inspect_q8_minsum_clipping.py, two ablation output directories,
  and Q8_MINSUM_CLIPPING_INSPECTION.md.
