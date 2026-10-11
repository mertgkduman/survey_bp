---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "13"
subsystem: campaign-operations
tags: [profiling, hpc, resource-projection, authorization, provenance]
requires:
  - phase: 08-reproducible-campaigns-and-statistical-assessment
    provides: verified campaign plans, shard merge receipts, replay evidence, and typed local profiling facts
provides:
  - representative clean/profile operational measurements with explicit missingness
  - fail-closed digest-bound resource and storage authorization receipts
affects: [08-14, campaign-dispatch, phase-09, phase-11]
actuals:
  tokens: 8110
  tasks: 2
  commits: 6
plan_head_before: 6effd76d052ea8ace96114498acc767b7937c6a1
tech-stack:
  added: []
  patterns:
    - Typed representative evidence is accepted only after verified pre-outcome clean/profile semantic agreement.
    - Site ceilings and unavailable required observations deny authorization rather than creating guessed limits.
key-files:
  created:
    - src/bp_registry/campaigns/profiling_gate.py
    - tests/test_campaign_profile_gate.py
  modified: []
key-decisions:
  - "Use a rational safety factor and bounded integer arithmetic for resource projections."
  - "Treat scheduler allocation as observational while scientific caps remain in the scientific authorization identity."
  - "Leave absent HPC/site ceilings unfilled and deny authorization until measured site facts exist."
patterns-established:
  - "Authorization receipts bind campaign, gate, merge, shard, replay, profile, and site-capability digests."
requirements-completed: [LED-05, SIM-02, STAT-03]
coverage:
  - id: D1
    description: "Representative clean/profile evidence aggregates decoder and replay throughput, storage, scheduler cost, and explicit memory missingness."
    requirement: "SIM-02"
    verification:
      - kind: unit
        ref: "tests/test_campaign_profile_gate.py -k 'representative or semantic or throughput or storage or memory or missingness'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Campaign authorization projects bounded resource use and denies missing or exceeded measured site ceilings."
    requirement: "STAT-03"
    verification:
      - kind: unit
        ref: "tests/test_campaign_profile_gate.py -k 'authorization or projection or ceiling or deny or identity'"
        status: pass
    human_judgment: false
duration: 4 min
completed: 2026-10-11
status: complete
---

# Phase 8 Plan 13: Measured Campaign Profiling Gate Summary

**Representative clean/profile evidence now produces digest-bound resource projections that refuse campaigns without measured capacity.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-10-11T06:49:41Z
- **Completed:** 2026-10-11T06:53:59Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- Added typed, pre-outcome representative operational evidence that requires verified shard, merge, and replay receipts plus clean/profile semantic agreement.
- Aggregated decoder and replay throughput, ledger and sidecar storage, event counts, scheduler fixed costs, and explicit peak-memory availability across fast and slow paths on multiple physical samples.
- Added a fail-closed authorization receipt that binds campaign, gate, merge, shard, replay, profile, site-capability, safety-margin, allocation, and projection facts.
- Exposed per-event decoder and ledger measurements, leaving zero-event evidence explicitly unavailable.
- Denies missing required observations, absent site ceilings, every tested resource-ceiling exceedance, and unbounded arithmetic before a large campaign can be authorized.

## Task Commits

1. **Task 1: Aggregate representative clean/profiled operational evidence** - `c692721`, `23b8240` (test → feat)
2. **Task 2: Choose measured resource and storage ceilings and authorize or deny** - `392b677`, `28e8e0c` (test → feat)
3. **Security correction during Task 2** - `096008f` (fix)
4. **Measurement correction during Task 1** - `9e5dda2` (fix)

## Files Created/Modified

- `src/bp_registry/campaigns/profiling_gate.py` - Evidence validation, bounded projection, and authorization receipt contracts.
- `tests/test_campaign_profile_gate.py` - Representative evidence, semantic drift, missingness, ceiling, identity, safety-factor, and arithmetic-boundary coverage.

## Decisions Made

- No site wall-time, CPU, memory, or storage ceilings were invented. A missing capability fact yields a denial until a bounded measurement supplies it.
- The authorization receipt includes worker allocation as an operational observation, while its scientific identity excludes allocation topology and includes scientific caps.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Bounded resource-projection arithmetic**

- **Found during:** Task 2
- **Issue:** Initial validation accepted integers beyond the project work-accounting bound, allowing unbounded projection inputs.
- **Fix:** Applied the 64-bit count bound to inputs, sums, products, and safety-factor projections.
- **Files modified:** `src/bp_registry/campaigns/profiling_gate.py`, `tests/test_campaign_profile_gate.py`
- **Verification:** `test_resource_gate_rejects_unbounded_campaign_arithmetic` and the 14-test profile-gate suite pass.
- **Committed in:** `096008f`

**2. [Rule 2 - Missing Critical Functionality] Explicit per-event measurements**

- **Found during:** Task 1 verification
- **Issue:** Aggregate evidence retained event counts but did not expose the required per-event decoder and storage measurements.
- **Fix:** Added per-event measurement properties and explicit zero-event missingness.
- **Files modified:** `src/bp_registry/campaigns/profiling_gate.py`, `tests/test_campaign_profile_gate.py`
- **Verification:** `test_representative_clean_profiled_evidence_measures_throughput_storage_and_memory` and the 14-test profile-gate suite pass.
- **Committed in:** `9e5dda2`

**Total deviations:** 2 auto-fixed (Rule 2).

## TDD Gate Compliance

- Task 1 RED evidence: `.gsd/tdd-evidence/08-13-task-1-red.json` verified as `RED_EVIDENCE_OK`; `c692721` precedes `23b8240`.
- Task 2 RED evidence: `.gsd/tdd-evidence/08-13-task-2-red.json` verified as `RED_EVIDENCE_OK`; `392b677` precedes `28e8e0c`.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_profile_gate.py -k 'representative or semantic or throughput or storage or memory or missingness' -x` — 6 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_profile_gate.py -k 'authorization or projection or ceiling or deny or identity' -x` — 11 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_profile_gate.py -x` — 14 passed.

## Next Phase Readiness

Phase 8 can use the profiling gate in its bounded local/HPC-equivalent campaign. The gate will deny a publication-scale dispatch until retained representative evidence and explicit site ceilings are supplied.

## Self-Check: PASSED

- `src/bp_registry/campaigns/profiling_gate.py` and `tests/test_campaign_profile_gate.py` exist.
- Task commits `c692721`, `23b8240`, `392b677`, `28e8e0c`, `096008f`, and `9e5dda2` exist.
