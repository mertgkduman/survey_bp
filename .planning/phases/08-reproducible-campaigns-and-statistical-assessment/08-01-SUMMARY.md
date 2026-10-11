---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "01"
subsystem: campaign execution and evidence
tags: [campaigns, pydantic, sha256, canonical-ledger, scipy]
requires:
  - phase: 02-canonical-execution
    provides: canonical one-shot runner, immutable manifests, and validated JSONL events
provides:
  - A strict campaign_spec_v1 facade with an acyclic specification-to-unit-to-plan digest chain
  - Private, atomically sealed one-unit CSS shard evidence with independent validation
  - Exact fixed-shot reconstruction using SciPy Clopper-Pearson intervals
affects: [08-02, 08-04, 08-05, 08-07, 08-09]
tech-stack:
  added: []
  patterns: [domain-separated canonical SHA-256 identities, private-stage-then-replace shard publication]
key-files:
  created:
    - src/bp_registry/campaigns/contracts.py
    - src/bp_registry/campaigns/execution.py
    - src/bp_registry/campaigns/shards.py
    - tests/test_campaign_execution.py
  modified: []
key-decisions:
  - "Campaign specification identity contains only primitive scientific inputs; executor labels are receipt observations."
  - "Unit keys are derived before a separate unsigned complete-plan digest is attached to the shard seal."
  - "One-look fixed-shot intervals use scipy.stats.binomtest(...).proportion_ci(method='exact')."
patterns-established:
  - "Validate one immutable ledger byte snapshot before deriving any campaign terminal count."
  - "Reject manifest traversal, symlink inputs, digest drift, oversized evidence, and receipt-plan mismatches before reconstruction."
requirements-completed: [LED-05, SIM-01, SIM-02, STAT-01, STAT-02]
actuals:
  tokens: 5184
  tasks: 1
  commits: 2
commits: 2
plan_head_before: 86ef2972c83710b996f44268823e93d4f9f7f944
duration: 2min
completed: 2026-10-11
status: complete
coverage:
  - id: D1
    description: One immutable canonical CSS campaign unit is executed, sealed, independently revalidated, and reconstructed.
    requirement: LED-05
    verification:
      - kind: integration
        ref: tests/test_campaign_execution.py#test_tracer_runs_seals_verifies_and_reconstructs_zero_failure
        status: pass
    human_judgment: false
  - id: D2
    description: Scientific campaign identity is acyclic and independent of executor labels.
    requirement: SIM-01
    verification:
      - kind: unit
        ref: tests/test_campaign_execution.py#test_identity_is_acyclic_and_changes_only_with_scientific_primitives
        status: pass
    human_judgment: false
---

# Phase 8 Plan 01: One-unit campaign tracer Summary

**A strict campaign_spec_v1 executes one frozen canonical CSS shot into a sealed shard and reconstructs its exact fixed-shot evidence without worker-dependent scientific identity.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-10-11T05:34:19Z
- **Completed:** 2026-10-11T05:36:26Z
- **Tasks:** 1/1
- **Files modified:** 6

## Accomplishments

- Added strict primitive campaign records with confined inner-manifest paths, byte hashes, finite bounds, and domain-separated SHA-256 identities.
- Derived the unit key before hashing an unsigned plan payload, so neither unit identity nor the plan digest contains a self-reference.
- Reused `run_canonical_one`, staged evidence privately, fsynced files and directories, atomically published the shard, and revalidated its canonical event snapshot before count reconstruction.
- Persisted the all-shot terminal classification and used SciPy's exact binomial interval; the successful tracer keeps `0/1` failures with a positive upper endpoint.

## Task Commits

1. **Task 1 RED: add failing campaign tracer** — `2fba620` (`test`)
2. **Task 1 GREEN: add sealed one-unit campaign tracer** — `ff218b3` (`feat`)

## TDD Gate Compliance

- **RED:** `tests/test_campaign_execution.py::test_tracer_runs_seals_verifies_and_reconstructs_zero_failure` failed on its campaign-package assertion before implementation; the persisted [RED evidence](./08-01-TDD-RED.json) passed `tdd-red-evidence` with `RED_EVIDENCE_OK`.
- **GREEN:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'tracer or identity or acyclic or zero_failure' -x` passed with 2 tests.
- **REFACTOR:** No separate refactor was needed after the focused test pass.

## Files Created/Modified

- `src/bp_registry/campaigns/contracts.py` — frozen campaign inputs and acyclic plan derivation.
- `src/bp_registry/campaigns/execution.py` — local one-unit adapter over the existing canonical runner.
- `src/bp_registry/campaigns/shards.py` — staged sealing, receipt validation, and exact one-look reduction.
- `src/bp_registry/campaigns/__init__.py` — compact public campaign tracer API.
- `tests/test_campaign_execution.py` — end-to-end tracer and identity-boundary coverage.

## Decisions Made

- Executor labels are stored as receipt observations only, keeping worker topology outside campaign, physical-sample, decoder-randomness, unit, and plan identities.
- The inner manifest remains an immutable referenced input. Its raw bytes are hash-pinned and its preflighted sample namespace and decoder seed must agree with the campaign specification.
- Sealed evidence is reconstructed only after the receipt, manifest reference, bounded ledger bytes, canonical lifecycle, and terminal semantics have been revalidated.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The GSD RED-evidence checker consumes TAP summaries while this repository uses pytest. The persisted RED record retains the actual pytest assertion and its appended one-test TAP normalization, and the checker returned `RED_EVIDENCE_OK` before production code was added.

## User Setup Required

None.

## Next Phase Readiness

- Plans 08-02 through 08-14 can extend the strict facade with the full campaign, planning, merge/resume, target, finite-look, scheduler, profiling, reporting, and CLI surfaces.
- The tracer deliberately handles one fixed-shot unit; it makes no source-curve or performance claim.

## Self-Check: PASSED

- Confirmed all campaign modules, the test, and the persisted RED evidence exist.
- Confirmed task commits `2fba620` and `ff218b3` exist and contain no tracked-file deletion.
