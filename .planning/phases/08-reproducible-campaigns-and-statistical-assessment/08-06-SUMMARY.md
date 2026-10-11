---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "06"
subsystem: campaign resume evidence
tags: [campaigns, immutable-attempts, resume, early-stop, drift-rejection]
requires: [08-05]
provides: [deterministic-resume-preflight, stop-receipt-recovery, scientific-drift-rejection]
affects: [08-09, 08-10, 08-11, 08-14]
tech-stack:
  added: []
  patterns: [complete-look-reconstruction-before-subtraction, exact-scientific-identity, immutable-child-attempts]
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/shards.py
    - tests/test_campaign_shards.py
decisions:
  - "Resume reconstructs the earliest complete declared look and recovers its deterministic stop receipt before excluding any authorized tail."
  - "Scientific/source/environment/dependency/sample/stopping/assessment digests require exact equality; executor allocation remains observational."
  - "Incomplete attempts remain resumable, while terminal, explicit-final, and authorized-undispatched units are excluded by exact frozen key subtraction."
metrics:
  duration: "14m"
  completed: "2026-10-11"
  tasks: 2
  files: 2
actuals:
  tokens: 3826
  tasks: 2
  commits: 5
commits: 5
plan_head_before: ef9ffab2bb01fd76f557b88bea02e25bc8a4790c
status: complete
---

# Phase 08 Plan 06: Immutable Resume Preflight Summary

Campaign resume now reconstructs completed-look decisions from immutable verified evidence, recovers a deterministic early-stop receipt before any retry planning, and rejects scientific identity drift.

## Accomplishments

- Added `derive_resume_plan`, which validates a complete frozen scientific identity, reconstructs each complete look in order, and returns the exact stop receipt required for atomic publication after a post-decision crash.
- Performs exact resume subtraction only after recovery: verified terminals, explicit final nonterminals, and the verified authorized-undispatched tail are excluded; interrupted and missing units remain resumable.
- Produces deterministic immutable child-attempt plans with unit-scoped parent attempt receipt identifiers and hashes.
- Rejects source, environment, dependency, sample namespace, stopping-rule, assessment, campaign, or plan drift while accepting changed observational executor allocations.
- Deduplicates byte-identical delivered attempt snapshots and rejects a receipt-hash alias that names different evidence.
- Added crash-window, recovery, immutable-evidence, scientific-drift, executor-allocation, and forged-partial-stop coverage.

## Task Commits

1. **Task 1: Derive new immutable attempt shards from missing unit keys**
   - `5d14985` `test(08-06): add failing resume recovery coverage`
   - `6808790` `feat(08-06): recover stop receipts before resume`
2. **Task 2: Reject scientific and dependency drift while retaining partial evidence**
   - `dd76c3f` `test(08-06): reject forged partial stop receipt`
   - `1977a9b` `feat(08-06): reject undeclared resume stops`
   - `ff6b139` `fix(08-06): permit recovered stop receipt`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_shards.py -k 'resume or stop_receipt_recovery or crash_window or early_stop or authorized_tail or interruption or attempt_lineage or retry or immutable or set_difference' -x` — 6 passed, 2 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_shards.py -k 'drift or stop_receipt_recovery or crash_window or early_stop or authorized_tail or partial or overshoot or executor or dependency' -x` — 3 passed, 5 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_shards.py -x` — 8 passed.
- `git diff --check` — passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Distinguished recovered stop receipts from retained stop receipts.**
- **Found during:** Task 2 full shard regression.
- **Issue:** The forged-receipt guard also rejected a newly reconstructed receipt, preventing the intended recovery path.
- **Fix:** Require retained receipt look indices to match the reconstructed stop only when retained receipts exist.
- **Files modified:** `src/bp_registry/campaigns/shards.py`
- **Commit:** `ff6b139`

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed `src/bp_registry/campaigns/shards.py` and `tests/test_campaign_shards.py` exist.
- Confirmed task commits `5d14985`, `6808790`, `dd76c3f`, `1977a9b`, and `ff6b139` exist with no tracked-file deletions.
