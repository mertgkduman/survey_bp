---
phase: 10-correlated-quaternary-execution
plan: "06"
subsystem: quaternary-bp-schedules
tags: [python, qbp, bp4, flooding, variable-serial, normalization, offset]
requires:
  - phase: 10-05
    provides: scalar LLR-BP4 kernel, immutable session state, and numerical profile
provides:
  - Pauli-labelled quaternary edge identity with deterministic check-major ordering
  - Source-defined flooding and variable-node serial BP4 schedules with explicit freshness evidence
  - Scoped scalar C2V normalization and signed-offset transforms
affects: [10-correlated-quaternary-execution, q-bpgd, mbp4, public-manifests]
tech-stack:
  added: []
  patterns: [closed quaternary schedule policy classes, transform application at the scalar C2V boundary]
key-files:
  created:
    - src/bp_registry/quaternary/schedules.py
    - tests/canonical/quaternary/test_schedules.py
  modified: []
key-decisions:
  - "Flooding delegates its untransformed path to the qualified kernel session; serial owns an atomic original-qubit ordered pass."
  - "Normalization and offset are closed scalar C2V transforms with finite positive parameters and persisted equation identities."
patterns-established:
  - "Quaternary graph identity includes the Pauli edge label and rejects binary schedule/update names at the compatibility boundary."
  - "A schedule trace records node/edge order, snapshot/commit boundaries, work, and applied transform equation order."
requirements-completed: [QBP-01, QBP-04]
actuals:
  tokens: 5775
  tasks: 2
  commits: 4
plan_head_before: a427616f494e0e58ff573b56f5432dc7c920ae23
coverage:
  - id: D1
    description: Source flooding and variable-serial BP4 schedules preserve deterministic labelled edge order, freshness, work accounting, and the five-qubit IIIYI regression.
    requirement: QBP-01
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_schedules.py -x"
        status: pass
    human_judgment: false
  - id: D2
    description: Source-defined scalar C2V normalization and signed offset validate parameters, compose in declared order, and reject binary policy names.
    requirement: QBP-04
    verification:
      - kind: unit
        ref: "tests/canonical/quaternary/test_schedules.py#test_normalization_and_offset_have_source_equations_and_scalar_scope"
        status: pass
    human_judgment: false
duration: 10m 14s
completed: 2026-10-07
status: complete
---

# Phase 10 Plan 06: Quaternary Schedules and C2V Transforms Summary

**Source-defined flooding and variable-serial BP4 schedules with labelled graph identity, IIIYI regression evidence, and scoped scalar C2V normalization and offset.**

## Performance

- **Duration:** 10m 14s
- **Started:** 2026-10-07T04:17:06Z
- **Completed:** 2026-10-07T04:27:20Z
- **Tasks:** 2/2
- **Files created:** 2
- **Verification:** 9 schedule-policy tests plus 12 scalar-kernel/vector-oracle regressions passed.

## Accomplishments

- Added a deterministic Pauli-labelled edge table and first-class flooding/variable-serial schedule traces that make update freshness, order, commit boundaries, and work visible.
- Kept flooding on one complete old V2C snapshot while variable serial immediately exposes an updated variable's incident V2C messages to later qubits in the declared original order.
- Qualified the Kuo–Lai five-qubit `IIIYI` fixture: flooding oscillates while serial reaches the `IIIYI` candidate on its third ordered pass.
- Added closed check-message transforms that divide scalar C2V output by `alpha_c` or apply signed `beta` shrinkage, with strict scope and parameter checks.

## Task Commits

1. **Task 1: Execute flooding and source variable-serial BP4**
   - `380f73d` — RED schedule-module contract
   - `6c4731d` — flooding/serial implementation and source fixture tests
2. **Task 2: Apply source quaternary normalization and offset**
   - `3093d5a` — RED C2V-transform contract
   - `e9110f5` — scoped transforms and validation tests

## Files Created

- `src/bp_registry/quaternary/schedules.py` — closed schedule and C2V-transform policy surface over the qualified scalar kernel session.
- `tests/canonical/quaternary/test_schedules.py` — edge identity, freshness, IIIYI, work, equation, composition, and rejection contracts.

## Decisions Made

- Used the kernel session's qualified flooding implementation where no transform is active; the serial schedule owns its distinct source-defined fresh-state pass.
- Restrict transforms to finite scalar C2V values after check reduction and before variable assembly, preserving priors, V2C state, beliefs, and candidate scoring as separate operations.
- Persisted transform equation identities in schedule traces and retained no unqualified binary schedule or min-sum port.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced a noncommuting Pauli test graph.**
- **Found during:** Task 1
- **Issue:** The initial edge-identity fixture violated the stabilizer commutation invariant before schedule behavior could run.
- **Fix:** Used two commuting Pauli rows while retaining distinct labelled graph identities.
- **Files modified:** `tests/canonical/quaternary/test_schedules.py`
- **Verification:** The complete schedule suite passed.
- **Committed in:** `6c4731d`

**2. [Rule 1 - Bug] Made each IIIYI assertion execute exactly one flooding pass.**
- **Found during:** Task 1
- **Issue:** The first candidate assertion accidentally advanced the schedule once per qubit while building a string.
- **Fix:** Stored one sweep result before converting its candidate to an I/X/Y/Z string.
- **Files modified:** `tests/canonical/quaternary/test_schedules.py`
- **Verification:** The regression now proves the intended flooding oscillation and serial convergence sequence.
- **Committed in:** `6c4731d`

**Total deviations:** 2 Rule 1 test-fixture corrections required for valid source-regression coverage.

## TDD Gate Compliance

- **Task 1 RED:** `380f73d`; `RED_EVIDENCE_OK` for `test_quaternary_source_schedule_module_is_available`.
- **Task 1 GREEN:** `6c4731d`; flooding/serial freshness, IIIYI, ordering, and work tests passed.
- **Task 2 RED:** `3093d5a`; `RED_EVIDENCE_OK` for `test_quaternary_check_transform_contract_is_available`.
- **Task 2 GREEN:** `e9110f5`; normalization, offset, scope, parameter, and unsupported-policy tests passed.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_schedules.py -x` — 9 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_kernel.py tests/canonical/quaternary/test_vector_oracle.py -x` — 12 passed.

## Issues Encountered

None beyond the corrected task-local test fixtures documented above.

## Next Phase Readiness

Q-BPGD and MBP4 controllers can select only the explicit quaternary schedules and C2V transforms, carrying their stable policy evidence into public manifests.

## Self-Check: PASSED

Both created files and all four RED/GREEN task commits are present in git history.
