---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "14"
subsystem: campaign-operations
tags: [campaigns, bb144, slurm, profiling, receipts, finite-look]
requires:
  - phase: 08-12
    provides: strict campaign lifecycle CLI and retained shard reconstruction
  - phase: 08-13
    provides: representative evidence and fail-closed authorization contracts
provides:
  - bounded, replayable BB-144 operational gate with fast and slow inputs
  - retained finite-look crash/recovery and synthetic Slurm evidence
  - evidence-backed denial when HPC/site ceilings are unavailable
affects: [phase-09, phase-11, campaign-dispatch]
actuals:
  tokens: 20661
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 2ddc8b38e9c80f5f5bde5c3583c070824df2e9b1
tech-stack:
  added: []
  patterns:
    - Preflight validates bounded development-gate metadata and both manifest bytes before output creation.
    - Operational verification reconstructs retained evidence and accepts unavailable site facts only with a production denial.
key-files:
  created:
    - data/studies/phase8-operational-gate-v1.json
    - data/results/phase8-operational-gate-v1/profiling-authorization.json
    - docs/campaigns.md
  modified:
    - src/bp_registry/campaigns/cli.py
    - tests/test_campaign_execution.py
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-VALIDATION.md
key-decisions:
  - "The retained operational gate remains development_fixture/not_assessed and does not support a publication or decoder-quality claim."
  - "Missing HPC/site ceilings and scheduler accounting are evidence for a deny outcome, not values to infer."
requirements-completed: [LED-05, SIM-01, SIM-02, SIM-03, STAT-01, STAT-02, STAT-03, STAT-04, STAT-05]
coverage:
  - id: D1
    description: Frozen fast/slow BB-144 gate inputs and preflight rejection of path digest drift.
    requirement: SIM-03
    verification:
      - kind: integration
        ref: tests/test_campaign_execution.py#test_operational_gate_preflight_binds_both_paths_without_creating_evidence
        status: pass
    human_judgment: false
  - id: D2
    description: Retained finite-look post-decision crash recovery with zero next-look dispatch and immutable pre-crash evidence.
    requirement: LED-05
    verification:
      - kind: integration
        ref: tests/test_campaign_execution.py#test_operational_fixture_recovers_a_post_decision_crash_without_next_look
        status: pass
    human_judgment: false
  - id: D3
    description: Bounded local, Slurm-route, and synthetic Slurm evidence with a fail-closed production authorization receipt.
    requirement: SIM-02
    verification:
      - kind: integration
        ref: tests/test_campaign_execution.py#test_operational_gate_verify_requires_retained_bounded_evidence
        status: pass
    human_judgment: false
duration: 31m
completed: 2026-10-11
status: complete
---

# Phase 8 Plan 14: Bounded Operational Gate Summary

**A replayable BB-144 development gate now retains measured local and synthetic scheduler evidence, proves finite-look crash recovery, and denies production dispatch until site ceilings are supplied.**

## Accomplishments

- Froze fast and slow canonical BB-144 manifests with a common physical-sample namespace, independent arm seed identities, two preselected samples, and not-assessed development labels.
- Added strict gate metadata preflight and an `operational-fixture` command that creates a retained post-decision/pre-publication crash proof; resume recovers the exact stop receipt without submitting the next look.
- Ran the primary tracer through local and Slurm-route execution, verified both replay to the same terminal fact, merged the local receipt, and retained all campaign, merge, assessment, scheduler, and finite-look receipts.
- Recorded actual local route timing and storage. Site capability provided no usable ceilings or accounting, so the retained authorization denies any production-scale or real-array submission.
- Added the exact retained-gate verification command: `bp-registry-campaign verify --campaign data/studies/phase8-operational-gate-v1.json --campaign-root . --output data/results/phase8-operational-gate-v1`.

## Task Commits

1. **Task 1: Freeze the representative gate and researcher documentation** — `9b6c138` (`feat`)
2. **Task 2: Run the bounded gate, retain receipts, and close validation** — `e1e375d` (`feat`)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py tests/test_campaign_profile_gate.py tests/test_campaign_shards.py tests/test_campaign_contracts.py tests/test_campaign_targets.py tests/test_campaign_statistics.py` — 95 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.campaigns.cli verify --campaign data/studies/phase8-operational-gate-v1.json --campaign-root . --output data/results/phase8-operational-gate-v1` — verified retained receipt hashes, stop-receipt recovery, zero next-look submissions, and production denial.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 1125 passed, 1 skipped (18 multiprocessing/fork warnings).

## Measured Gate Facts

- Local primary tracer: 4.063 s elapsed, 1.920 s user time, 0.137 s system time, and 15,378 bytes retained under its local shard root.
- Slurm-route tracer: 3.895 s elapsed, 1.907 s user time, 0.115 s system time, and the same reconstructed terminal fact.
- Synthetic array: two bounded shards, concurrency one, one CPU/task; four frozen synthetic units terminal with no incomplete unit.
- Real scheduler submission: zero. The site capability receipt records unavailable default memory, array size, and accounting.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added an operational-gate verification interface.**

- **Found during:** Task 2.
- **Issue:** The planned `verify --campaign --output` command was not implemented; the existing CLI could only verify one shard receipt and could not prove the retained bounded gate as a bundle.
- **Fix:** Added strict gate-metadata validation, bounded synthetic fixture execution, and evidence-only operational verification.
- **Files modified:** `src/bp_registry/campaigns/cli.py`, `tests/test_campaign_execution.py`.
- **Verification:** The focused 95-test Phase 8 suite and full suite pass.

**2. [Rule 3 - Blocking issue] Used the shell `time` builtin for measured command duration.**

- **Found during:** Task 2.
- **Issue:** `/usr/bin/time` is absent from the execution environment.
- **Fix:** Retained the shell builtin's elapsed/user/system measurements in the gate result directory.
- **Files modified:** `data/results/phase8-operational-gate-v1/local-runtime.txt`, `data/results/phase8-operational-gate-v1/slurm-route-runtime.txt`.
- **Verification:** The values are retained alongside the matching replayable receipts.

## Known Stubs

None.

## Next Phase Readiness

The campaign lifecycle, statistical fixtures, and operational evidence are ready for later bounded studies. A real Slurm array or publication-scale campaign remains denied until the site provides explicit resource ceilings and accounting observations.

## Self-Check: PASSED

- Confirmed the frozen gate, retained receipt set, documentation, validation report, and this summary exist.
- Confirmed task commits `9b6c138` and `e1e375d` exist.
- Confirmed the gate verifier and full test suite pass.
