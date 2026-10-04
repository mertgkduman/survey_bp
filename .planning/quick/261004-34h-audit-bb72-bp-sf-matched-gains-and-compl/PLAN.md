---
status: in_progress
quick_id: 261004-34h
date: 2026-10-04
---

# Audit and independently follow up the BB72 BP-SF signal

## Goal

Produce an independent, source-qualified test of the BB72 v1 BP-SF signal with complete observable cost evidence, while continuing the project's Phase 5 verification and Phase 6 transition. Preserve the published v1 design, ledgers, and claims without alteration.

## Tasks

1. Independently audit the v1 matched terminal ledgers, outcome classes, missing runtime, intervention actions, and work counters. Record a reproducible audit and design implications.
2. Add Phase 5 decode runtime measurements as observational evidence with backward-compatible replay validation. Permit BP-SF to run either canonical SPA or canonical min-sum through an explicit manifest policy. Add tests for kernel compatibility, runtime evidence, and old-ledger behavior.
3. Prespecify an independent BB72 v2 factorial study: SPA/min-sum, BP-SF off/on, γ=1/0.5, short and full BP-only controls; matched new samples, separate selection/evaluation if tuning, sample size/power rationale, total-work and runtime views, fixed statistical contrasts, and source-status limits. Run bounded smoke/preflight, then the approved HPC campaign and publish verified results.
4. Prepare the outstanding Phase 5 human verification evidence for review. After technical gates, move into Phase 6 planning without marking a human checkpoint passed autonomously.
5. Protect the sealed v2 campaign against the original Slurm wall-time limit: schedule a conditional continuation that preserves a raw interrupted-ledger copy, trims only a proven incomplete trailing shot, resumes the original manifest/sample identities, verifies all arms, and publishes only the complete package.

## Must haves

- Runtime is marked observational and never changes decoder control flow or deterministic replay decisions.
- The update rule used by each BP-SF session is explicit, validated, and included in its manifest identity.
- No published v1 file or study denominator is rewritten or mixed into v2.
- Selection and evaluation samples are disjoint; all evaluated arms at a rate see the same physical samples.
- BP messages, non-message typed work, BP calls, and runtime availability appear as distinct cost facts.
- Claims remain limited to the tested BB72 X-only CSS regime and qualified canonical adaptations.
