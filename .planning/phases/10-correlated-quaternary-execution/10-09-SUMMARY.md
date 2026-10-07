---
phase: 10-correlated-quaternary-execution
plan: "09"
subsystem: quaternary-mbp4-execution
tags: [python, qbp, mbp4, fixed-alpha, provenance, replay, four-state-decoding]
requires:
  - phase: 10-08
    provides: resolved quaternary composition, public event grammar, and deterministic replay boundary
provides:
  - Fixed-alpha source-defined MBP4 posterior scaling and unscaled destination-edge inhibition
  - Flooding and variable-serial MBP4 sessions with typed work, state identity, and reconstruction
  - Closed public MBP4 dispatch with source-fidelity and canonical-adaptation evidence
affects: [phase-10-asced, phase-11-quaternary-evaluation]
actuals:
  tokens: 8458
  tasks: 2
  commits: 4
plan_head_before: 3606b17ccd56ccb8055027b0226cfa92fa353e5c
tech-stack:
  added: []
  patterns: [fixed-alpha kernel-owned recurrence, unscaled edge inhibition, composition-level source-fidelity evidence, deterministic public replay]
key-files:
  created:
    - src/bp_registry/quaternary/mbp4.py
    - tests/canonical/quaternary/test_mbp4.py
  modified:
    - src/bp_registry/quaternary/compatibility.py
    - src/bp_registry/quaternary/execution.py
    - src/bp_registry/runner.py
    - tests/canonical/quaternary/test_public_execution.py
key-decisions:
  - "Fixed-alpha MBP4 is a closed quaternary kernel kind: only posterior anticommuting accumulation is scaled by 1/alpha; destination-edge inhibition remains unscaled."
  - "MBP4 plus an individually sourced C2V transform remains executable but is explicitly labeled canonical_adaptation because the combined procedure is not source-defined."
requirements-completed: [QBP-01, QBP-04]
coverage:
  - id: D1
    description: Fixed-alpha MBP4 implements the source recurrence, flooding or serial freshness, typed work, replay, and strict fixed-alpha boundaries.
    requirement: QBP-01
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_mbp4.py
        status: pass
    human_judgment: false
  - id: D2
    description: Public fixed-alpha MBP4 preflights a closed composition, persists recurrence evidence, labels unsourced combinations, and rejects replay tampering.
    requirement: QBP-04
    verification:
      - kind: integration
        ref: tests/canonical/quaternary/test_public_execution.py#test_mbp4_public_source_run_records_fixed_recurrence_and_replays
        status: pass
    human_judgment: false
duration: 7m
completed: 2026-10-07
status: complete
---

# Phase 10 Plan 09: Fixed-Alpha MBP4 Execution Summary

Fixed-alpha MBP4 with source-defined posterior scaling, unscaled edge inhibition, qualified schedules, and replayable public evidence.

## Accomplishments

- Added the distinct Kuo–Lai MBP4 variable recurrence: all posterior anticommuting C2V contributions are scaled by `1/alpha`, while the outgoing destination-edge delta is subtracted unscaled.
- Added typed fixed-alpha session state for flooding and serial schedules, with input validation, work reservations, terminal evidence, state digests, and deterministic reconstruction.
- Added closed public MBP4 composition resolution and event-ledger execution, including exact recurrence identity, alpha, schedule freshness, state/work evidence, adaptation labels, and replay tamper detection.

## Task Commits

1. Task 1 RED — `d53c07d` `test(10-09): add failing MBP4 recurrence contract`
2. Task 1 GREEN — `4b4251e` `feat(10-09): implement fixed-alpha MBP4 recurrence`
3. Task 2 RED — `8e56054` `test(10-09): add failing public MBP4 evidence contract`
4. Task 2 GREEN — `e5c7cf6` `feat(10-09): expose replayable public fixed-alpha MBP4`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_mbp4.py -k 'fixed_alpha or recurrence or posterior or inhibition or normalized or flooding or serial or invalid or ambp4 or work' -x` — 5 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_mbp4.py tests/canonical/quaternary/test_public_execution.py -k 'mbp4 and (public or installed_cli or source or adaptation or replay or tamper or ambp4 or unsupported)' -x` — 8 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_bpgd.py -x` — 3 passed.

## TDD Gate Compliance

- Task 1 RED evidence: `.gsd/tdd-evidence/10-09-task-1-red.json` verified as `RED_EVIDENCE_OK` before kernel implementation.
- Task 2 RED evidence: `.gsd/tdd-evidence/10-09-task-2-red.json` verified as `RED_EVIDENCE_OK` before public dispatch implementation.

## Decisions Made

- `qbp_mbp4_fixed_alpha` is a source-qualified kernel identity that carries one finite positive manifest alpha; alpha lists and AMBP4 labels are rejected because adaptive search is a separate source algorithm.
- Source-backed policy components do not inflate fidelity for a non-source-defined combination; MBP4 plus a C2V transform is persisted as `canonical_adaptation` with the effective recurrence/order evidence.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Next Phase Readiness

The public composition boundary now admits replayable fixed-alpha MBP4 paths. The aSCED plans can invoke the distinct MBP4 kernel only through its qualified fixed-alpha identity and must preserve their own source and splitter gates.

## Self-Check: PASSED

- Confirmed the MBP4 kernel, direct contracts, public execution integration, and all four task commits exist.
