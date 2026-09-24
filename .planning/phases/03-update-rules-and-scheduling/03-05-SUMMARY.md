---
phase: 03-update-rules-and-scheduling
plan: "05"
subsystem: canonical-work-accounting
tags: [work-vector, budgets, local-schedules, terminal-evidence, ledger, verification]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: layered, serial, randomized, and residual local schedule kernels
provides:
  - atomic local-update-plus-convergence admission across implemented schedules
  - full Phase-3 work vectors and independent dual-budget terminal evidence
  - V3 schedule-terminal ledger support while retaining V2 flooding grammar
affects: [public-schedule-admission, pilot-comparisons, ledger-verification]
plan_head_before: bcd41a5b4c28b323cfbfd45d58ce5207aea565ae
commits: 5
actuals:
  tokens: 68786
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - a local mutation and exactly one convergence check share one pre-mutation reservation
    - V2 work evidence is explicitly serialized separately from full V3 schedule work
key-files:
  created:
    - .planning/phases/03-update-rules-and-scheduling/03-05-task-1-red-evidence.json
    - .planning/phases/03-update-rules-and-scheduling/03-05-task-2-red-evidence.json
  modified:
    - src/bp_registry/canonical/budgets.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/verification.py
    - src/bp_registry/ledger.py
    - src/bp_registry/canonical/schedules.py
    - src/bp_registry/canonical/residual.py
key-decisions:
  - "Convergence checks are a distinct WorkVector resource and every local schedule reserves exactly one before mutating state."
  - "V3 schedule terminals duplicate the same complete work and runtime facts in both cap views; neither view converts the other into total cost."
  - "Historical V2 public flooding work dictionaries remain byte-grammar compatible through versioned serialization."
requirements-completed: [SCH-02, SCH-03, SCH-04, SCH-05]
coverage:
  - id: D1
    description: "Layered, serial, residual, and randomized local schedule work reserves convergence before state mutation and rolls back on denial or failure."
    requirement: SCH-02
    verification:
      - kind: unit
        ref: "tests/canonical/test_budgets.py tests/canonical/test_schedule_semantics.py -k 'local_step or convergence or partial or rollback'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Full work vectors, partial progress, dual budget views, V3 schedule terminals, and V2 flooding grammar reconstruct deterministically."
    requirement: SCH-04
    verification:
      - kind: integration
        ref: "tests/canonical/test_budgets.py tests/canonical/test_work_accounting.py tests/canonical/test_schedule_semantics.py tests/canonical/test_residual_schedule.py tests/test_ledger.py tests/test_canonical_cli.py"
        status: pass
    human_judgment: false
duration: 12m
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 05: Atomic Work and Dual Budget Evidence Summary

**All implemented local schedules now reserve an explicit convergence check with their mutation, while V3 terminals retain exact partial work under separate C2V-cap and schedule-iteration views.**

## Performance

- **Duration:** 12m
- **Started:** 2026-09-24T10:08:57Z
- **Completed:** 2026-09-24T10:21:01Z
- **Tasks:** 2/2
- **Files modified:** 13

## Accomplishments

- Added distinct candidate, convergence, order, residual precomputation/difference, and priority-maintenance counters to the full Phase-3 `WorkVector`.
- Made layered, check-node serial, variable-node serial, residual, randomized-order, and flooding local work reserve the required convergence operation before state changes.
- Added typed V3 schedule-terminal evidence with exact cursor/partial-traversal facts, source-qualified iterations, separate setup/decode runtime facts, and two non-interchangeable budget views.
- Preserved V2 public flooding manifests, work dictionaries, structural records, and verification by serializing their original field grammar explicitly.

## Task Commits

1. **Task 1 RED: local convergence admission** — `1251a97`, `f6cb426` (`test`)
2. **Task 1 GREEN: atomic local convergence reservation** — `6197062` (`feat`)
3. **Task 2 RED: schedule terminal evidence** — `240cd26` (`test`)
4. **Task 2 GREEN: dual budget and versioned terminal evidence** — `2c5c9c4` (`feat`)

## Verification

- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py tests/canonical/test_schedule_semantics.py -k 'local_step or convergence or partial or rollback'` — 2 passed.
- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py tests/canonical/test_work_accounting.py tests/canonical/test_schedule_semantics.py tests/canonical/test_residual_schedule.py tests/test_ledger.py` — 48 passed.
- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py tests/canonical/test_work_accounting.py tests/canonical/test_schedule_semantics.py tests/canonical/test_residual_schedule.py tests/test_ledger.py tests/test_canonical_cli.py` — 100 passed.
- `git diff --check` — passed.

## TDD Gate Compliance

- **Task 1 RED:** `03-05-task-1-red-evidence.json` validates the named layered admission assertion as `RED_EVIDENCE_OK`; `6197062` is the GREEN implementation.
- **Task 2 RED:** `03-05-task-2-red-evidence.json` validates the named schedule-terminal assertion as `RED_EVIDENCE_OK`; `2c5c9c4` is the GREEN implementation.

## Decisions Made

- Convergence checks are not a candidate-check alias: every local proposal carries exactly one separately budgeted `convergence_checks` operation.
- Both D-16 views retain an identical complete work vector and the same setup/decode measurements, so neither cap type implies equal effort or runtime.
- New partial schedule facts use structural event version 3; V2 flooding evidence remains independently replayable with its original keys and meanings.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Compatibility] Preserved public V2 work-limit and terminal grammar after expanding the full work vector.**
- **Found during:** Task 2 verification.
- **Issue:** Directly serializing the expanded vector caused historical V2 manifests to fail strict work-limit validation and would have changed persisted flooding dictionaries.
- **Fix:** Added explicit V2/V3 work serialization and parsing, kept V2 public caps/versioned terminal data on their original field set, and added compatibility coverage.
- **Files modified:** `src/bp_registry/canonical/budgets.py`, `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/verification.py`, `src/bp_registry/manifests.py`, `tests/test_canonical_cli.py`.
- **Verification:** 100-test plan suite passed.
- **Committed in:** `2c5c9c4`.

**2. [Rule 3 - TDD evidence] Corrected Task 1's RED record to the required validator schema before GREEN work.**
- **Found during:** Task 1 RED validation.
- **Issue:** The first evidence record used descriptive rather than validator-recognized field names.
- **Fix:** Recorded the named assertion failure in the standard evidence grammar and revalidated it as `RED_EVIDENCE_OK`.
- **Files modified:** `.planning/phases/03-update-rules-and-scheduling/03-05-task-1-red-evidence.json`.
- **Verification:** `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK`.
- **Committed in:** `f6cb426`.

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 3). **Impact:** The corrections preserve existing public evidence and enforce the required TDD gate without expanding policy scope.

## Issues Encountered

The full CLI-inclusive suite exceeded the terminal's first 30-second output window but completed successfully when its active session was collected: 100 passed in 33.62s.

## Known Stubs

None. Empty policy/cache mappings found in schedule calls are the existing decoder-visible empty-state inputs, not rendering or evidence placeholders.

## Next Phase Readiness

Public schedule-admission plans can now emit V3 schedule-terminal evidence without altering V2 flooding comparisons. Pilot-comparison work can consume both D-16 views while retaining full raw cost and runtime facts.

## Self-Check: PASSED

- Confirmed all Task 1/2 source, test, and RED-evidence artifacts exist.
- Confirmed commits `1251a97`, `f6cb426`, `6197062`, `240cd26`, and `2c5c9c4` are reachable in repository history.
- No skipped tests, unrun verification commands, or unplanned trust-boundary surface remain.

---
*Phase: 03-update-rules-and-scheduling*
*Completed: 2026-09-24*
