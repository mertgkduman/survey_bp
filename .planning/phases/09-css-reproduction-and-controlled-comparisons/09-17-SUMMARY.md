---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "17"
subsystem: campaigns
tags: [failure-count, canonical, bounded-batch, blocked]
status: blocked
plan_head_before: 7fec771
commits: 4
dependency_graph:
  requires: [09-08, 09-16]
  provides: [single-arm canonical bounded execution seam]
  affects: [09-06, 09-18]
key_files:
  modified:
    - src/bp_registry/campaigns/contracts.py
    - src/bp_registry/campaigns/planning.py
    - src/bp_registry/campaigns/execution.py
    - tests/test_campaign_execution.py
actuals:
  tokens: 9500
  tasks: 1
  commits: 4
---

# Phase 09 Plan 17: Bounded Canonical Execution Summary

Implemented and verified the single-arm canonical bounded-unit seam, then stopped before claiming the required engine-level hard guards.

## Completed Work

### Task 1: Execute one real canonical failure-count unit end to end

- Added `FailureCountWorkSpecV1`, which binds an exactly-one-arm canonical work specification to an outcome-independent `FailureCountPolicyV1`.
- Added `freeze_failure_count_work_spec()`. Its preimage includes the prospective work specification and ordered unit keys, so unit ordinals are frozen before execution and remain independent of completion order.
- Added `run_canonical_bounded_batch()` for an exact contiguous ordinal range. It does not call `run_canonical_work_plan()` and runs each selected unit through the existing materialized-sample, canonical-ledger, `_campaign_attempt()`, and `verify_canonical_attempt()` path.
- The adapter rechecks manifest iteration bounds and batch/campaign work, event, evidence, storage, worker, and ordinal projections before dispatch. It seals measured work, evidence, storage, receipt, and wall-boundary observations after a completed batch.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py tests/test_campaign_failure_count.py -k 'single_arm_work_spec or executable_limit or understated_bound or canonical_bounded_unit or tracer_ordered_stop or paired_canonical_replays' -x` — 5 passed, 46 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py tests/test_campaign_failure_count.py -k 'canonical_bounded_batch or failure_count_resource_cap or understated_bound or receipt_reserve or predispatch_cap or batch_projection or mid_unit_cap or wall_boundary_overshoot or no_work_after_timeout or evidence_cap or storage_cap or bounded_interruption or tracer_ordered_stop' -x` — 4 passed, 48 deselected.

## Blocking Plan Gap

Task 2 requires byte guards before every canonical ledger append and artifact write, plus an iteration-boundary timeout that emits a resumable partial attempt. The owned wrapper cannot implement those facts truthfully: `run_canonical_materialized_one()` calls `canonical.execution.run_canonical_structural_shot()`, which constructs `CanonicalEventWriter` internally and exposes no resource-guard or interruption-receipt injection point. The runner only supplies static execution controls.

Implementing the remaining guarantees requires changing the canonical engine API and its event-writer lifecycle in `src/bp_registry/canonical/execution.py`, then threading a typed guard through `runner.py` and `ledger.py`. That is a public execution-engine contract change outside this plan's listed ownership and affects every canonical decoder path, so this is a Rule 4 architectural blocker. The current adapter must not be presented as enforcing mid-unit evidence/storage stops, boundary-observed timeout interruption receipts, or resume lineage.

## Task Commits

- `dcd1944` test(09-17): add failing bounded canonical unit test
- `941ee70` feat(09-17): run one bounded canonical failure-count unit
- `6a12431` test(09-17): add bounded batch receipt regression
- `7c8fd38` feat(09-17): seal bounded canonical batch resources

## Self-Check: PASSED

The bounded adapter, strict work-spec freezer, focused regression tests, and all four task commits exist. The summary intentionally remains blocked because Task 2's mandatory dynamic guard and immutable partial-receipt behavior is absent.
