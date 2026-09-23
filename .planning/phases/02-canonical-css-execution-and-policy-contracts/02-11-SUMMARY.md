---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "11"
subsystem: canonical-css-provenance-boundaries
tags: [canonical-bp, ledger-ownership, candidate-lineage, truth-boundary, tdd]
requires:
  - phase: 02-10
    provides: public canonical execution with structural evidence and scoped work accounting
provides:
  - owner-authenticated canonical structural evidence appends
  - strict content identity for binary candidate vectors
  - original-working-attempt-candidate validation before evaluation
affects: [phase-02-plan-12, canonical-results, policy-selection]
actuals:
  tokens: 4015
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [owner-before-idempotency, strict-prehash-validation, attempt-bound-candidate-identity]
key-files:
  created: []
  modified: [src/bp_registry/ledger.py, src/bp_registry/canonical/lineage.py, src/bp_registry/canonical/problems.py, src/bp_registry/canonical/execution.py, tests/test_ledger.py, tests/canonical/test_tracing.py, tests/canonical/test_truth_boundary.py]
key-decisions:
  - "Canonical event ownership is asserted before duplicate-event handling and retained through the durable append."
  - "Canonical candidate identity includes the current working problem, typed attempt identity, and validated binary payload."
patterns-established:
  - "Selection policy output is engine-verified against immutable current-attempt lineage before evaluation or structural selection evidence."
requirements-completed: [ENG-05, LED-02]
coverage:
  - id: D1
    description: Canonical evidence admits intermediate and terminal facts only from the open shot owner, while lifecycle kinds remain typed routes.
    requirement: LED-02
    verification:
      - kind: integration
        ref: tests/test_ledger.py::test_canonical_intermediate_events_require_active_writer_ownership
        status: pass
      - kind: unit
        ref: tests/test_ledger.py::test_canonical_event_rejects_reserved_lifecycle_kinds
        status: pass
    human_judgment: false
  - id: D2
    description: Candidate content and selector output are validated against the current original-working-attempt chain before evaluation.
    requirement: ENG-05
    verification:
      - kind: unit
        ref: tests/canonical/test_tracing.py::test_candidate_payload_rejects_coercion_and_nonvectors
        status: pass
      - kind: unit
        ref: tests/canonical/test_truth_boundary.py::test_working_problem_validates_complete_identity_edge
        status: pass
      - kind: integration
        ref: tests/canonical/test_truth_boundary.py::test_engine_rejects_candidate_from_other_working_problem_or_attempt
        status: pass
    human_judgment: false
metrics:
  duration: 9 min
  completed: 2026-09-23
status: complete
plan_head_before: 8712391da5f27aa3619b475e4d34f3189d823978
commits: 4
---

# Phase 02 Plan 11: Canonical Ownership and Candidate Lineage Summary

**Canonical evidence now has a live writer owner, and every evaluated candidate is a validated binary vector bound to the current original, working problem, and attempt.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-23T22:10:11Z
- **Completed:** 2026-09-23T22:19:02Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

1. Required a live `CanonicalEventWriter` owner for all non-begin structural facts, including duplicate-content attempts, and reserved lifecycle methods for `begin()` and `terminal()`.
2. Rejected coercive, scalar, multidimensional, boolean, and non-binary candidate payloads before content addressing.
3. Bound candidate IDs to the current working object and deterministic attempt ordinal, rejecting detached selector output before independent evaluation.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_ledger.py tests/canonical/test_tracing.py tests/canonical/test_truth_boundary.py tests/test_canonical_cli.py::test_public_canonical_work_counts_one_bp_call_per_attempt tests/test_canonical_cli.py::test_public_cap_below_one_sweep_emits_scoped_denial`

Result: `27 passed`.

The focused public temporary-output regressions ran here. Checked result artifacts remain assigned to Plan 02-12 after the Plan 02-10 manifest migration.

## Task Commits

1. **Task 1: Enforce active shot ownership for every structural append**
   - `a1fe03e` test RED: ownership and reserved-lifecycle assertions
   - `5326ff5` feat GREEN: owner-enforced canonical append boundary
2. **Task 2: Validate canonical candidate payloads and current-attempt ancestry**
   - `292848c` test RED: candidate payload, edge, and selector assertions
   - `9504bc4` feat GREEN: strict content validation and attempt-bound candidate identity

## Files Created/Modified

- `src/bp_registry/ledger.py` — verifies active ownership before canonical journal access and reserves lifecycle kinds.
- `src/bp_registry/canonical/lineage.py` — validates original binary payload form before conversion or hashing.
- `src/bp_registry/canonical/problems.py` — requires a complete current original-to-working identity edge.
- `src/bp_registry/canonical/execution.py` — derives and checks attempt-bound candidate lineage in both canonical shot paths.
- `tests/test_ledger.py`, `tests/canonical/test_tracing.py`, and `tests/canonical/test_truth_boundary.py` — adversarial ownership and lineage coverage.

## Decisions Made

- Ownership is checked before duplicate-event handling so an identical event never grants a second writer an append path.
- Candidate identity now includes the current attempt as well as the working identity and immutable payload.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Regression] Updated the prior trace ordering assertion for owner-first validation**
- **Found during:** Task 2 verification
- **Issue:** The earlier assertion expected an open-shot ordering error when an ownerless writer submitted an event.
- **Fix:** The assertion now expects `ShotOwnershipError`, the stronger public boundary introduced by Task 1.
- **Files modified:** `tests/canonical/test_tracing.py`
- **Verification:** `tests/canonical/test_tracing.py tests/canonical/test_truth_boundary.py` reports `14 passed`.
- **Committed in:** `9504bc4`

**Total deviations:** 1 auto-fixed (1 regression).
**Impact on plan:** The adjustment aligns prior coverage with the new owner-authenticated append contract.

## Known Stubs

None.

## Issues Encountered

None.

## Next Phase Readiness

Plan 02-12 can regenerate and inspect checked canonical result artifacts with owner-authenticated structural evidence and current-attempt candidate lineage.

## TDD Gate Compliance

- Task 1 RED and GREEN commits: `a1fe03e` → `5326ff5`.
- Task 2 RED and GREEN commits: `292848c` → `9504bc4`.

## Self-Check: PASSED
