---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "17"
subsystem: campaigns
tags: [failure-count, canonical, bounded-batch, complete]
status: complete
plan_head_before: 2ff908b
dependency_graph:
  requires: [09-08, 09-16, 09-20]
  provides: [derived bounded admission, guarded canonical batches, immutable partial attempts, cap-censored replay]
  affects: [09-06, 09-18]
key_files:
  modified:
    - src/bp_registry/campaigns/contracts.py
    - src/bp_registry/campaigns/planning.py
    - src/bp_registry/campaigns/execution.py
    - tests/test_campaign_execution.py
actuals:
  tasks: 2
---

# Phase 09 Plan 17: Bounded Canonical Execution Summary

## Delivered

- `FailureCountWorkSpecV1` freezes one arm, exact ordinals, policy, and the canonical work plan. The bounded adapter verifies Plan 09-20's independently derived executable maxima before materialization and admits only the next declared strict batch or one explicitly interruptible development unit.
- Admission checks retained, independently replayed terminal and partial actuals plus the next maximum against shots, work, events, evidence, and storage in frozen cap precedence. The nominal per-unit timeout must fit the prospective wall cap. The closed partial receipt schema has a 10,626-byte serialized maximum, below the 32,768-byte control reserve.
- One runtime guard charges the materialized sample, canonical ledger, and terminal attempt. The terminal attempt includes a durable wall/resource observation checked against the retained sample, ledger, profile, and guarded artifact sizes. Historical unguarded fixed-shot, finite-look, and V7 routes retain their existing bytes.
- Wall, evidence, and storage interruptions seal immutable zero-credit `FailureCountPartialAttemptV1` receipts with the denied operation, consumed resources, exact pending ordinal, fresh attempt identity, and digest-linked retry lineage. Replay rejects altered paths, counters, profile, ordinal, parent, sample, or ledger. A retry reuses the materialized sample and charges it once.
- If no new maximum fits after a partial, or a strict batch reaches its wall boundary between units, the adapter seals an immutable cap-censored receipt. It retains completed prefix shots and costs, the prior wall observations, the pending ordinal, and any partial digest; repeated calls replay the same bytes and cannot dispatch a different ordinal.

## Verification

- Plan 09-17 focused task selectors passed with nonzero selections; additional accumulated-cap, retry, wall-boundary, and censor replay regressions passed.
- Canonical guard, ledger, campaign execution, failure-count, and CLI cross-route command: 162 passed in 337.21 seconds. The final committed revision then passed the full repository suite: 1,247 passed, 1 skipped in 883.70 seconds, peak pytest RSS 388,664 KiB. The full suite contains the cross-route tests and the later added cap regressions.

## Commits

`a9653a0`, `2fe79f1`, `507b5a1`, `34a1bcd`, `4381c32`, `e5f8bca`, `34a1f58`, `d4a5eab`, `3046e4e`, `194410a`, and `d15e152` complete the retained earlier bounded adapter. Plan 09-06 owns public lifecycle orchestration, target inference, and report presentation.

## Self-Check: PASSED

Both tasks and the Phase 9 Wave 6 full-suite gate passed. No publication-scale scheduler authorization was introduced.
