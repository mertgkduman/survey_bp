---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "16"
subsystem: paired campaign execution
tags: [canonical-bp, slurm, selected-shards, resume, provenance]
requires:
  - phase: 08-15
    provides: frozen paired work plans and canonical materialized-sample replay
provides:
  - bounded real canonical selected-shard Slurm route
  - mixed-route, route-neutral merge envelope with verified sample descriptors
  - exact retry reduction through the shared resume planner
affects: [phase-08, phase-11, campaign-reporting]
tech-stack:
  added: []
  patterns:
    - scheduler facts remain delivery observations outside canonical merge evidence
    - materialized samples are indexed by frozen physical identity and rehydrated from verified paths
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/execution.py
    - src/bp_registry/campaigns/cli.py
    - src/bp_registry/campaigns/__init__.py
    - tests/test_campaign_execution.py
key-decisions:
  - "Require paired run-shard callers to provide bounded Slurm allocation and strict scheduler-observation receipts."
  - "Reduce duplicate route deliveries only after exact deterministic semantic trace, manifest, sample/error, terminal, and work-vector agreement."
  - "Keep profiler-only canonical ledger variance as independently verified delivery evidence rather than treating it as scientific disagreement."
requirements-completed: [LED-05, SIM-01, SIM-02, SIM-03]
actuals:
  tokens: 12052
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 35a5437e4480645bc8876ccecfb6fc2fd479fb0c
duration: 34min
completed: 2026-10-11
status: complete
---

# Phase 08 Plan 16: Canonical Selected-Shard Slurm Summary

**Paired campaigns can now execute every frozen shard through a bounded real canonical Slurm route, merge independently verified local and scheduler deliveries, and return only scientifically authorized retries.**

## Accomplishments

- Added paired `emit-slurm` support that derives its literal shell-free array argv from the persisted complete work plan.
- Added paired `run-shard` execution for exactly one decimal-selected frozen shard, with validated allocation and scheduler observations.
- Replayed and revalidated materialized sample bytes, physical-error hashes, manifests, canonical ledgers, terminal facts, and ledger-derived work vectors before merge.
- Added `campaign_paired_merge_envelope_v1`, containing a route-neutral canonical inner merge, verified input-artifact indexes, and `materialized_samples_by_identity` descriptors keyed by physical identity.
- Routed paired resume through `derive_resume_plan` using a complete frozen scientific identity and exported the general reducer from the campaign facade.
- Passed typed materialized samples and verified named work vectors to the Phase 08 reporting contract.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'paired_canonical_local_and_slurm_routes_match or paired_canonical_slurm_array_is_bounded' -x` — passed (2 selected).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'paired_canonical_resume or mixed_route_merge or stop_before_resubmit' -x` — passed (1 selected).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'installed_paired_canonical_local_lifecycle' -x` — passed (1 selected).
- Broader `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py tests/test_campaign_shards.py -x` — passed (48 tests in 168.99 seconds). The first broad attempt exposed the new Phase 08-17 materialized-sample/work-vector report requirement; the compatibility fix is included in this result.

## Task Commits

1. Task 1: `35b9a3e` — `feat(08-16): execute canonical paired Slurm shards`
2. Task 2: `237d69c` — `feat(08-16): merge route-neutral canonical evidence`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Prevent canonical runtime profiling from creating false mixed-route conflicts**

- **Found during:** Task 2 mixed-route merge regression.
- **Issue:** Independently executed canonical ledgers differed in runtime/RSS profiler fields and event IDs despite identical frozen inputs, materialized error bytes, candidate/outcome/termination facts, and work vectors.
- **Fix:** Preserve and independently verify both complete ledger hashes, while duplicate reduction compares the full deterministic semantic trace after excluding only profiler, setup-runtime, decode-runtime, and derived event-ID observations.
- **Files modified:** `src/bp_registry/campaigns/cli.py`
- **Commit:** `237d69c`

**2. [Rule 2 - Missing critical functionality] Bind merge evidence to typed materialized samples and work vectors**

- **Found during:** Broader installed lifecycle regression after Phase 08-17 reporting integration.
- **Issue:** Report reconstruction requires one revalidated materialized artifact per physical identity and a nonempty named work vector for every verified terminal.
- **Fix:** Added confined, hash-checked sample descriptor rehydration and extracted work vectors exclusively from verified canonical ledger events.
- **Files modified:** `src/bp_registry/campaigns/execution.py`, `src/bp_registry/campaigns/cli.py`
- **Commit:** `237d69c`

## Known Stubs

None.

## Self-Check: PASSED

- All assigned implementation and test files exist; commits `35b9a3e` and `237d69c` are present in Git history.
