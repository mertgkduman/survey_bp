---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "05"
subsystem: campaign shard evidence
tags: [campaigns, immutable-shards, replay, retry-lineage, deterministic-merge]
requires: [08-01, 08-04]
provides: [private-atomic-shards, independently-verified-attempts, exact-coverage-merge]
affects: [08-06, 08-09, 08-10, 08-11, 08-14]
tech-stack:
  added: []
  patterns: [same-filesystem-atomic-publication, content-bound-receipts, frozen-unit-order]
key-files:
  created:
    - tests/test_campaign_shards.py
  modified:
    - src/bp_registry/campaigns/shards.py
decisions:
  - "A sealed attempt records the complete planned-to-running-to-sealed lifecycle and may retry only from an interrupted parent."
  - "Merge accepts only independently validated/replayed attempt snapshots and reduces outcomes using frozen work-plan unit order."
  - "A valid look-stop receipt authorizes only its exact remaining frozen tail after a complete verified look."
metrics:
  duration: "5m19s"
  completed: "2026-10-11"
  tasks: 2
  files: 2
actuals:
  tokens: 7350
  tasks: 2
  commits: 4
commits: 4
plan_head_before: d91fb7ca4ebfb0fa31d5493cf3006aeb166da1e6
status: complete
---

# Phase 08 Plan 05: Immutable Shards and Exact Coverage Summary

Campaign workers now seal private shard directories atomically, retain immutable retry lineage, and merge only independently verified terminal evidence in frozen unit order.

## Accomplishments

- Hardened shard publication with caller-private staging directories, regular-file and symlink checks, file and directory fsync, same-filesystem atomic replacement, and a no-reopen rule.
- Added v2 receipt-envelope validation for environment, source, executor, timing, expected/open/terminal keys, independently verified status, sidecar bytes, and replay status. Legacy v1 validation remains readable for already-retained evidence.
- Added immutable attempt receipt validation. Every receipt is one legal lifecycle, parent links cannot be missing, cyclic, cross-unit, or terminal-parented, and all receipt identities are retained.
- Added deterministic merge of independently verified snapshots. It preserves interrupted attempts, gives one denominator contribution to a terminal recovery, records byte-identical terminal retries as redundant, rejects conflicting terminal evidence, and reconstructs event ordering from frozen units plus event IDs.
- Added exact missing, incomplete, explicit-final-nonterminal, unexpected, authorized-undispatched, terminal, redundancy, and stop-receipt fields to the merge receipt.
- Added adversarial fixtures for atomic seal behavior, invalid lineage, recovery retry, terminal conflict, deterministic permutation, missing coverage, and authenticated early-stop tails.

## Task Commits

1. **Task 1: Seal and independently validate immutable shard products**
   - `d287f67` `test(08-05): add immutable shard and lineage coverage`
   - `c211138` `feat(08-05): seal and validate immutable shard evidence`
2. **Task 2: Merge by exact unit coverage and conflict detection**
   - `6dbde92` `test(08-05): add deterministic shard merge coverage`
   - `15c7694` `feat(08-05): merge verified shards by frozen coverage`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_shards.py -k 'seal or immutable or attempt_lineage or interruption or corruption or replay or sidecar or path' -x` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_shards.py -k 'merge or attempt_lineage or retry or authorized_tail or early_stop or duplicate or conflict or missing or ordering or reconstruct' -x` — 4 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_shards.py -x` — 5 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py tests/test_ledger.py -x` — 19 passed.
- `git diff --check` — passed.

## TDD Evidence

- Task 1 RED: `tests/test_campaign_shards.py` failed because `validate_attempt_lineage` was unavailable before implementation.
- Task 2 RED: `tests/test_campaign_shards.py` failed because `merge_verified_attempts` was unavailable before implementation.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed `src/bp_registry/campaigns/shards.py` and `tests/test_campaign_shards.py` exist.
- Confirmed task commits `d287f67`, `c211138`, `6dbde92`, and `15c7694` exist with no tracked-file deletions.
