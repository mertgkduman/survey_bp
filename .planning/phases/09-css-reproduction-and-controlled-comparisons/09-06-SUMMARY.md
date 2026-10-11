---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "06"
subsystem: campaigns
tags: [failure-count, immutable-receipts, lifecycle, blocked]
status: blocked
plan_head_before: 9c917b8d3ac1944e19dc49ea2fdd467f591bba6f
commits: 2
dependency_graph:
  requires: [09-04, 09-05]
  provides: [local one-arm failure-count stop/censor receipt primitive]
  affects: [09-08, 09-10, public campaign lifecycle]
tech_stack:
  added: []
  patterns: [sealed immutable unit attempts, ordinal replay, terminal-batch tail separation]
key_files:
  created: [tests/test_campaign_failure_count.py]
  modified: [src/bp_registry/campaigns/execution.py]
decisions:
  - "Do not expose the local controller as the existing public campaign lifecycle until failure terminal facts are moved out of the frozen assessment plan."
metrics:
  duration: partial execution
  completed_date: 2026-10-11
actuals:
  tokens: 14500
  tasks: 1
  commits: 2
---

# Phase 09 Plan 06: Failure-Count Lifecycle Summary

Implemented a sealed local one-arm failure-count controller, then stopped before the incompatible public CLI/report integration.

## Completed Work

### Task 1: Dispatch, seal, and resume one target-reached failure-count campaign

- `dispatch_failure_count_batches()` freezes ordinal order from the work plan, dispatches whole local batches, and stops only after the target-th ordered failure or a whole-batch cap.
- Unit attempts, including interruptions, are immutable. Resume retries only the interrupted ordinal in a fresh attempt directory and does not rerun completed shots.
- `verify_failure_count_receipt()` rebuilds stop/censor evidence from sealed receipt bytes. It rejects altered order, counts, tails, and work facts.
- A target receipt separates the exact inferential prefix through `T_r` from already-completed terminal-batch tail. Tail shots remain in actual work counts.
- A cap-first terminal is emitted as `inconclusive_cap_censored` with no verdict.

**Commits:**

- `f0a3dfe` feat(09-06): seal ordered failure-count lifecycle
- `1f4f9f8` fix(09-06): resume only interrupted failure units

## Blocking Plan Gap

Task 2 remains unimplemented. The current public `plan`, `run-local`, `verify`, `merge`, `resume`, and `assess` path cannot honestly consume the new lifecycle without a persistent-contract redesign.

`CampaignAssessmentV1` freezes `FailureCountStoppingV1.terminal_state`, the observed `terminal_failure_ordinal`, prefix/tail hashes, and the inverse-binomial interval before execution. Those fields are only knowable after ordered terminal evidence has been sealed. Separately, `_paired_run()` calls `run_canonical_work_plan()` over all frozen units at once, so it cannot stop at a verified target batch or recover a missing terminal receipt before dispatching more work.

The controller therefore has no safe way to make the existing public commands claim failure-count support. It currently accepts one arm and a test-supplied unit runner; it is not a substitute for canonical paired execution.

## Required Replan Interface

1. Split the prospective failure-count policy (target failures, batch size, declared ordering, cap authorizations, resource caps) from a new post-run terminal receipt containing `target_reached` or `cap_censored`, `T_r`, prefix/tail digests, and observed counts.
2. Add a canonical single-unit/bounded-batch execution adapter that produces verified canonical attempt receipts without scheduling all work-plan units at once.
3. Route `plan`, `run-local`, `merge`, `resume`, `assess`, and `verify` by the prospective policy. Their failure-count form must retain and replay the ordered merge, exact prefix/tail split, terminal receipt, actual work/resources, and cap censoring.
4. Define the public ordinal for multi-arm plans before allowing controlled comparisons through this path; the current controller deliberately rejects `units_per_sample_group != 1`.
5. Enforce all frozen shot, work, evidence, storage, and wall authorizations before each whole batch. The completed primitive currently enforces the whole-shot cap only.
6. Preserve the existing rule that Phase 9 has no publication Slurm submission until site ceilings are measured.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_failure_count.py -k 'tracer or ordered_stop or terminal_batch_tail or censor or resume or interruption' -x` — 4 passed, 2 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'matched or finite_look or stop_receipt_recovery or crash_window or early_stop or authorized_tail or batch or overshoot or persisted or interruption' -x` — 6 passed, 38 deselected.
- Full local lifecycle test module — 6 passed.

## Deviations from Plan

### Architectural blocker

Task 2 requires changing the persisted assessment/plan grammar and the canonical public execution path. This is a Rule 4 architectural change, so it was not made inline. The summary is deliberately `blocked`; Plan 09-06 is not complete.

## Self-Check: PASSED

`src/bp_registry/campaigns/execution.py`, `tests/test_campaign_failure_count.py`, and both task commits exist. The summary accurately records that Task 2 and the plan-level public lifecycle acceptance criteria remain unmet.
