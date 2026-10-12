---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "06"
subsystem: campaigns
tags: [failure-count, canonical, immutable-receipts, public-lifecycle]
status: complete
plan_head_before: 9c917b8d3ac1944e19dc49ea2fdd467f591bba6f
dependency_graph:
  requires: [09-04, 09-05, 09-16, 09-17]
  provides: [public local failure-count plan, bounded dispatch, ordered merge, resume, assessment, independent replay]
  affects: [09-09, 09-10, 09-18]
key_files:
  created: [src/bp_registry/campaigns/failure_count_public.py, tests/test_campaign_failure_count.py]
  modified: [src/bp_registry/campaigns/execution.py, src/bp_registry/campaigns/planning.py, src/bp_registry/campaigns/cli.py, docs/campaigns.md]
actuals:
  tasks: 2
  commits: 3
---

# Phase 09 Plan 06: Public Failure-Count Lifecycle

## Delivered

- Task 1's earlier local controller seals ordered target and cap receipts, retries only the interrupted ordinal, and separates the exact target-th-failure prefix from completed terminal-batch tail. Its commits are `f0a3dfe` and `1f4f9f8`.
- Task 2 adds an acyclic prospective work-layout binding for `campaign_plan_sha256`, validates independent executable maxima and all initial caps at public plan/preflight time, and freezes exactly one arm, one coordinate, one target, and a complete ordinal set equal to the shot cap. The plan contains no terminal facts.
- The six public verbs now handle `failure_count_public_plan_v1`: `plan` freezes local-only work; `run-local` dispatches one guarded next batch; `merge` independently replays retained sample, ledger, attempt, partial, target/censor, and resource evidence; `resume` returns the exact next batch or recovers a missing terminal control receipt without decoding; `assess` produces a versioned report; `verify` byte-compares it with fresh reconstruction.
- Target-reached inference uses only `T_r`. Authorized terminal-batch tail remains in completed-shot, work, wall, event, evidence, and storage accounting. Cap-censored assessment is inconclusive. A mid-unit interruption has zero shot/failure credit and retains its pending ordinal, spent resources, wall overshoot when observed, and parent-linked retry lineage.
- Report and merge receipts expose exact ordered attempt membership, all partial attempt lineage, prefix and tail hashes, cap state, target decision, and observed resource costs. Byte-interrupted attempts have typed unavailable wall timing because their receipt has no wall clock observation. Publication Slurm remains denied. The public route and regressions were committed in `b0e6f75`.

## Verification

- Plan 09-06 Task 1 selectors passed during its earlier local-controller implementation: 4 selected lifecycle tests and 6 selected inherited Phase 8 regressions.
- Final Task 2 lifecycle selector: 8 passed, nonzero selection. Final report/tamper selector: 4 passed, nonzero selection. The full failure-count module passed 16 tests, and the campaign cross-route command passed 197 tests before the final replay refinements.
- Wave 7 full repository gate on committed `b0e6f75`: **1,257 passed, 1 skipped, 25 warnings in 874.68 seconds**; wrapper elapsed 877.08 seconds; peak pytest child RSS 384,176 KiB; exit status 0. Warnings are multiprocessing fork deprecations.

## Deviation

The additive report reducer lives in `failure_count_public.py` instead of changing the historical `reporting.py` schema. This keeps fixed-shot, finite-look, and Phase 8 paired report bytes stable while providing a separate versioned failure-count report.

## Self-Check: PASSED

Both tasks and the Phase 9 Wave 7 full-suite gate passed. No publication scheduler job was submitted or authorized.
