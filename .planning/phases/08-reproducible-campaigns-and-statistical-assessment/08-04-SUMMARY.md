---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "04"
subsystem: campaign identity and planning
tags: [campaigns, sha256, sample-matching, deterministic-sharding, finite-look]
requires: [08-02]
provides: [arm-neutral-sample-identities, frozen-unit-shard-plans, finite-look-tails]
affects: [08-05, 08-09, 08-10, phase-09-css-reproduction, phase-11-quaternary-reproduction]
tech-stack:
  added: []
  patterns: [domain-separated-sha256, immutable-dataclass-work-plan, executor-allocation-separation]
key-files:
  created:
    - src/bp_registry/campaigns/identity.py
    - src/bp_registry/campaigns/planning.py
  modified:
    - tests/test_campaign_execution.py
decisions:
  - "Physical sample identity is derived from scientific digest, cohort, point, arm-neutral namespace, and sample ID only."
  - "Decoder-local randomness binds arm and declared decoder seed but excludes workers, branches, and plan digest."
  - "Campaign work plans partition complete sample groups before allocation and retain an exact tail for every completed look."
metrics:
  duration: "~17 minutes"
  completed: "2026-10-11"
  tasks: 2
  files: 3
actuals:
  tokens: 5493
  tasks: 2
  commits: 4
commits: 4
plan_head_before: f99a21ca4c4c963ae6702130a4610ffc754acef7
status: complete
---

# Phase 08 Plan 04: Deterministic Campaign Identity and Sharding Summary

Campaign work now has acyclic scientific identities, arm-neutral physical samples, arm-scoped decoder randomness, and complete topology-independent shard plans.

## Accomplishments

- Added domain-separated SHA-256 identities for physical samples, decoder randomness, and atomic unit contributions. Physical sample identities exclude arm and executor topology; decoder randomness includes only the declared arm, seed identity, sample, and primitive campaign digest.
- Added `PersistedSampleReceiptV1` with byte count and SHA-256 verification for backends that must consume a retained physical sample artifact. Tampered bytes fail before a decoder can use them.
- Added immutable `UnitKey`, `ShardPlan`, and `CampaignWorkPlan` records. Plans expand sorted coordinates into complete paired-arm unit sets, partition by declared whole-sample look boundaries, and compute a plan digest only after serializing the unsigned complete plan.
- Added exact completed prefixes and authorized-undispatched tails for each declared look. Executor allocation is a separately validated shard-to-slot mapping and cannot alter unit or shard membership.
- Bounded total units, per-shard units, total shards, and serialized plan bytes before a work plan is materialized or dispatched.

## Task Commits

1. **Task 1: Derive arm-neutral samples and arm-scoped decoder randomness**
   - `5bbae43` `test(08-04): add matched sample identity coverage`
   - `130acad` `feat(08-04): derive topology-independent samples`
2. **Task 2: Freeze exact unit keys and disjoint shard membership**
   - `46b527c` `test(08-04): add frozen shard-plan coverage`
   - `f37e771` `feat(08-04): freeze deterministic unit and shard plans`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'sample and (acyclic or worker or arm or persisted or decoder_randomness)' -x` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'unit_key or shard_plan or acyclic or authorized_tail or coverage or topology or bound' -x` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -x` — 6 passed.
- `git diff --check` — passed.

## TDD Evidence

- Task 1 RED: campaign execution tests failed with `ModuleNotFoundError: bp_registry.campaigns.identity` before implementation; committed in `5bbae43`.
- Task 2 RED: campaign execution tests failed with `ModuleNotFoundError: bp_registry.campaigns.planning` before implementation; committed in `46b527c`.

## Decisions Made

- SHA-256 identities are integrity linkage. A separate persisted sample receipt binds artifact bytes for non-reproducible external backends.
- The plan digest seals the full derived plan but never appears in its own preimage, a unit key, sample identity, or decoder-randomness identity.
- Look boundaries count complete physical sample groups, so all arms for a sample are dispatched together and no look prefix splits a paired comparison.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed `src/bp_registry/campaigns/identity.py`, `src/bp_registry/campaigns/planning.py`, and `tests/test_campaign_execution.py` exist.
- Confirmed task commits `5bbae43`, `130acad`, `46b527c`, and `f37e771` exist with no tracked-file deletions.
