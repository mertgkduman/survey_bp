---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "10"
subsystem: campaign Slurm transport
tags: [campaigns, slurm, immutable-shards, scheduler-receipts, bounded-execution]
requires: [08-09]
provides: [shell-free-slurm-argv, frozen-array-selection, synthetic-scheduler-equivalence]
affects: [08-11, 08-14, phase-09-css-reproduction, phase-11-quaternary-reproduction]
tech-stack:
  added: []
  patterns: [literal-argv, allowlisted-scheduler-observations, receipt-only-allocation, synthetic-array-harness]
key-files:
  created:
    - src/bp_registry/campaigns/slurm.py
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-10-TASK-1-RED.json
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-10-TASK-2-RED.json
  modified:
    - tests/test_campaign_execution.py
decisions:
  - "Slurm receives a literal bounded argv and selects only a zero-based index into the already frozen shard tuple."
  - "Site partition, QOS, account, resource, job-state, timing, and accounting facts are executor observations outside campaign scientific identity."
  - "No site default authorizes a campaign: missing scheduler capability or accounting data remains explicitly unavailable."
metrics:
  duration: "~30 minutes"
  completed: "2026-10-11"
  tasks: 2
  files: 5
actuals:
  tokens: 7797
  tasks: 2
  commits: 4
commits: 4
plan_head_before: e5bc33898d2277da315b34f6a2744c6287b1a081
status: complete
---

# Phase 08 Plan 10: Bounded Slurm Transport Summary

One frozen campaign work plan now has a shell-free, bounded Slurm transport and a synthetic array harness that produces the same scientific facts as local execution without submitting any scheduler job.

## Accomplishments

- Added a `SlurmAllocation` contract that bounds wall time, memory, CPUs, array concurrency, and scheduler identifier lengths. Supplied partition, QOS, and account values must also appear in a caller-provided site allowlist.
- Added `build_sbatch_argv`, which returns a literal argument tuple for `subprocess.run(..., shell=False)`. It derives only `0..len(frozen_shards)-1` array indexes and cannot alter units, samples, looks, stopping, or assessment inputs.
- Added strict `SLURM_ARRAY_TASK_ID` resolution. Missing, malformed, injected, leading-zero, and out-of-range values fail before the local shard entry point can invoke a decoder.
- Added a pure parser for supplied `scontrol` and `sacct` observations. It records only the small allowlisted capability set and reports absent site/accounting data as unavailable instead of selecting a site policy or treating it as zero.
- Added per-task scheduler receipts for allocation request, job/task IDs, allocated CPUs, elapsed time, task state, exit code, accounting availability, launch overhead, and shard fixed cost. These observations remain outside `scientific_records`.
- Added a synthetic array harness that routes every successful task through the same one-shard local executor. It reproduces local terminal keys, sample/decoder identities, terminal facts, work vectors, and the deterministic scientific-record digest.
- Failed, preempted, and cancelled array tasks never run a decoder or fabricate terminals. Their exact frozen shard keys are retained as incomplete and resumable; duplicate task delivery is rejected.

## Task Commits

1. **Task 1: Translate frozen shards into bounded shell-free Slurm requests**
   - `c27e529` — RED argv, array-selection, injection, bounds, and capability-parser coverage.
   - `5bc7a8f` — bounded allocation contract, literal `sbatch` argv, frozen array selection, and read-only capability parser.
2. **Task 2: Prove local and scheduler receipts reconstruct the same science**
   - `961cf6a` — RED local/scheduler equivalence and nonterminal scheduler-state coverage.
   - `727c7da` — synthetic scheduler harness and observational task receipts.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'slurm and (argv or array or injection or bound or capability)' -x` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'executor_equivalence or scheduler_receipt or preempted or cancelled or accounting' -x` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -x` — 15 passed.
- `git diff --check` — passed.

## TDD Gate Compliance

- Task 1 RED evidence in `08-10-TASK-1-RED.json` passed `tdd-red-evidence` before the Slurm adapter existed.
- Task 2 RED evidence in `08-10-TASK-2-RED.json` passed `tdd-red-evidence` before the synthetic scheduler APIs existed.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed `slurm.py`, the campaign execution tests, both RED evidence records, and this summary exist.
- Confirmed task commits `c27e529`, `5bc7a8f`, `961cf6a`, and `727c7da` exist with no tracked-file deletions.
