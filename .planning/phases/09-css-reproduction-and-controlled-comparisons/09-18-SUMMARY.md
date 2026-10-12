---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "18"
subsystem: campaigns
tags: [ordered-work, matched-arms, local-lifecycle, replay]
status: complete
dependency_graph:
  requires: [09-06, 09-17]
  provides: [public ordered multi-arm fixed/finite plan and lifecycle]
  affects: [09-11, 09-19]
key_files:
  modified: [src/bp_registry/campaigns/contracts.py, src/bp_registry/campaigns/planning.py, src/bp_registry/campaigns/execution.py, src/bp_registry/campaigns/cli.py, src/bp_registry/campaigns/reporting.py, tests/test_campaign_execution.py, docs/campaigns.md]
actuals:
  tasks: 2
  commits: 2
---

# Phase 09 Plan 18: Ordered Matched Campaigns

## Delivered

- Added an additive `OrderedCampaignWorkSpecV1` wrapper with a complete unique declared arm sequence and fixed-shot or finite-look stopping. Historical `CampaignWorkSpecV1` fields and sorted-arm planning remain unchanged.
- `freeze_ordered_campaign_work_spec` freezes coordinate and numeric sample order, then expands each sample into a complete declared-arm group. Its new preimage and digest bind the order rule, group ordinals, unit ordinals and keys, and shards. Input arm and coordinate container permutations do not change ordered identity; changing declared arm order does.
- The installed public `preflight`, `plan`, `run-local`, `merge`, `resume`, `assess`, and `verify` routes preserve that sequence. Local `--max-units` permits a run to stop after one arm inside a group; the next run executes only missing units. Merge retains verified partial-group units, reports exact missing units and groups, and independently replays indexed artifacts. Assessment and terminal report verification require every frozen group. Reordered receipt members, duplicate units, changed order and plan bytes, and scheduler dispatch fail closed.
- Documented the ordered local lifecycle in `docs/campaigns.md`. Production commits: `e337495`, `5860d07`. The latter requires canonical merge envelope bytes on replay.

## Verification

- Task 1 declared-order selector: 8 passed. Combined ordered contract/lifecycle selector: 11 passed.
- Full campaign execution and profile tracer modules: 70 passed in 301.73 seconds.
- The end-to-end test covers an inside-group partial run, partial verify, exact missing-set resume, no rerun of its first unit, terminal assessment and report replay, receipt reordering, duplicate delivery, and denied Slurm dispatch.
- After the canonical merge-byte check, the end-to-end regression passed again (1 passed in 55.39 seconds), including a reformatted-envelope rejection.

## Deviation

Added `selected_unit_keys` to the canonical executor so an ordered run can stop inside a frozen shard without repartitioning the shard or changing historical default execution.

## Self-Check: PASSED

Both plan tasks and their targeted gates passed. Publication Slurm remains denied.
