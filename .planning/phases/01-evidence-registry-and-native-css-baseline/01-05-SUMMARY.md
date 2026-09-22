---
phase: 01-evidence-registry-and-native-css-baseline
plan: 05
subsystem: durable-shot-ledger
tags: [jsonl, fsync, posix-locks, provenance, reconciliation]
requires:
  - {phase: 01-03, provides: native CSS tracer and initial JSONL shot events}
  - {phase: 01-04, provides: deterministic samples and independent CSS outcomes}
provides:
  - Versioned and validated begin/terminal JSONL records
  - Cross-process per-shot ownership through terminal persistence
  - Idempotent interruption repair and terminal-row aggregate reconstruction
affects: [01-07, 01-09, native-css-tracer, reproducibility]
actuals:
  tokens: 6449
  tasks: 2
  commits: 4
plan_head_before: 440283dd12699ccf0fd4b2a77f6bafeab2f948ad
tech-stack:
  added: []
  patterns: [versioned JSONL events, fsynced local journal writes, POSIX advisory ownership locks, terminal-only denominators]
key-files:
  created: []
  modified: [src/bp_registry/ledger.py, src/bp_registry/runner.py, tests/test_ledger.py]
key-decisions:
  - "A stable run/shot key is protected by a separate owner lock held from durable begin through terminal fsync."
  - "Interruption is a reconciliation inference after ownership release, never an observed decoder termination."
  - "Aggregates derive only from terminal rows, including outcome-unavailable rows."
patterns-established:
  - "Validate and replay JSONL transitions under a journal lock before every append."
  - "Preserve deterministic sample identity before sampling so an interrupted attempt remains replayable."
requirements-completed: [LED-01, REG-04]
coverage:
  - id: D1
    description: Durable begin/terminal lifecycle preserves normal and catchable-error shot provenance.
    requirement: LED-01
    verification:
      - {kind: integration, ref: "tests/test_ledger.py::test_runner_records_begin_before_sampling_and_an_error_terminal", status: pass}
      - {kind: integration, ref: "tests/test_reference_smoke.py", status: pass}
    human_judgment: false
  - id: D2
    description: A live owner remains pending and an abandoned begin is repaired exactly once after owner release.
    requirement: LED-01
    verification:
      - {kind: integration, ref: "tests/test_ledger.py::test_active_owner_stays_pending_then_dead_owner_is_repaired_once", status: pass}
    human_judgment: false
  - id: D3
    description: Final-row summaries keep nonconvergence, interruption, postselection, and unavailable outcomes distinct.
    requirement: LED-01
    verification:
      - {kind: unit, ref: "tests/test_ledger.py::test_terminal_row_is_durable_and_summary_counts_only_final_rows", status: pass}
    human_judgment: false
duration: 31min
completed: 2026-09-22
status: complete
---

# Phase 01 Plan 05: Durable Shot Ledger Summary

**The CSS tracer now records each attempted shot as a versioned, fsynced lifecycle with cross-process ownership, explicit error evidence, and repairable interruption provenance.**

## Accomplishments

- Replaced the minimal JSONL writer with validated version 1 begin and terminal records, exclusive journal access, flush/fsync durability, stable identity conflict checks, and terminal-only summaries.
- Added a per-shot POSIX advisory lock that the runner acquires before sampling and releases only after terminal persistence; active attempts remain pending when reconciliation runs concurrently.
- Added durable error terminals that distinguish sampling, decoding, and evaluation failures while preserving deterministic sample identity, decoder configuration/version, unavailable native counters, and independent-outcome status.
- Added interruption repair that appends exactly one inferred terminal after ownership releases without a terminal event. It records null native internals and never presents recovery as observed decoder termination.

## Task Commits

1. **Task 1 RED: durable ledger contracts** — `01b8686` (`test`)
2. **Task 1 RED: runner error lifecycle** — `ee7b70e` (`test`)
3. **Task 1 / Task 2 GREEN: durable lifecycle, ownership, reconciliation, and summaries** — `0f83846` (`feat`)
4. **Typed replay identity validation** — `ab3088d` (`fix`)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_ledger.py tests/test_reference_smoke.py` — **9 passed**.
- The concurrency test starts a separate spawned process that holds a shot owner lock. Reconciliation returns no row while that process is live, then appends and retains one interrupted terminal after it exits without completing the shot.

## Decisions Made

- Journal and ownership locks are separate: the journal lock keeps reload, validation, append, and repair atomic; the owner lock represents a live shot across sampling, decoding, and evaluation.
- Terminal retries with identical payloads are idempotent; reused identities with conflicting begin or terminal content are rejected.
- `native_converged`, decoder termination, selected output, postselection, and independent outcome are independent fields. Missing native facts remain null with an explicit reason.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Next Phase Readiness

Later pilot and comparison work can rebuild denominator counts from durable final records and safely reconcile abandoned local journal attempts before analyzing results.

## Self-Check: PASSED

- `src/bp_registry/ledger.py`, `src/bp_registry/runner.py`, and `tests/test_ledger.py` exist.
- All four task commits are present in git history.
- Targeted ledger and tracer verification passed with 9 tests.
