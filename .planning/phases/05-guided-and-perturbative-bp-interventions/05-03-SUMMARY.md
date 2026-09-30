---
phase: 05-guided-and-perturbative-bp-interventions
plan: "03"
subsystem: canonical-decoder
tags: [session, intervention, budget, replay]
requires:
  - phase: "05-01"
    provides: owned BPGD tracer session and atomic sweep seam
provides:
  - explicit continuation, fresh reset, and posterior sign mutation operations
  - graph/prior/owner-qualified session state and proposal identity
  - versioned intervention action union and new leaf work categories
  - purpose-separated deterministic decoder stream identities
affects: [05-04, 05-05, 05-06, 05-07, 05-08]
actuals:
  tokens: 9218
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [owned-session-continuation, checked-fresh-reset, typed-proposal-authorization]
key-files:
  created:
    - tests/canonical/test_restart_execution.py
  modified:
    - src/bp_registry/canonical/kernel.py
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/intervention_session.py
    - src/bp_registry/canonical/budgets.py
    - src/bp_registry/canonical/guided_decimation.py
    - src/bp_registry/canonical/execution.py
    - tests/canonical/test_guided_decimation.py
key-decisions:
  - "Version 2/3 work serialization retains its prior field set; new intervention categories use version 4 work evidence."
  - "Fresh reset returns a distinct branch session; retained edge state is admitted only as a complete compatible snapshot."
  - "Source-deterministic BPGD declares its decoder stream not_applicable; stream derivation is reserved for randomized controllers."
requirements-completed: []
requirements-partial: [MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04]
coverage:
  - id: session-lifecycle
    description: Explicit BP continuation and checked reset with preserved diagnostic state on failure
    verification:
      - kind: unit
        ref: "tests/canonical/test_restart_execution.py#test_session_continue_and_fresh_reset_clear_all_undeclared_state"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_restart_execution.py#test_session_numerical_failure_rolls_back_reservation_and_state"
        status: pass
    human_judgment: false
  - id: intervention-transaction
    description: Typed proposal and unique reserved work leaf before mutation
    verification:
      - kind: unit
        ref: "tests/canonical/test_guided_decimation.py#test_proposal_carries_source_mutation_work_and_rejects_untrusted_action"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_restart_execution.py#test_leaf_work_extension_preserves_historical_serialization"
        status: pass
    human_judgment: false
duration: 8min
completed: 2026-09-30
status: complete
---

# Phase 5 Plan 03: Session and atomic work contract

The binary SPA kernel now opens an owned intervention session. Controllers can continue committed flooding state, create a fresh branch, mutate a finite prior, or flip a posterior with explicit preserved and recomputed fields.

## Accomplishments

- Added graph, prior, coordinate, dtype, owner, C2V/V2C, posterior, candidate, cursor, and mutation evidence to committed session state.
- Added a checked fresh branch reset; incompatible retained state is rejected before work reservation or parent mutation.
- Added source-qualified finite-prior proposals carrying exact action, target order, expected state, child lineage, and full anticipated work.
- Added separate work counts for fixation, transforms, lifted coordinates, original checks, and ranking scans while preserving historical version 2/3 wire fields.
- Added a deterministic decoder stream identity that excludes the physical-sampling purpose.

## Task Commits

1. **Session lifecycle and work fields** — `eea4fd3` (`feat`)
2. **Typed proposal authorization** — `156e8d9` (`feat`)
3. **Shot-scoped owner identity integration** — `36f0b9b` (`fix`)
4. **Plan metadata** — this summary commit (`docs`)

## Verification

- Session/continuation/reset targeted command: 6 passed, 4 deselected.
- Proposal/reservation/leaf targeted command: 11 passed, 9 deselected.
- Full `tests/canonical/test_restart_execution.py`: 7 passed.
- Full inherited `tests/canonical/test_budgets.py`: 9 passed.
- Guided tracer after ownership integration: 4 passed.

## Deviations from Plan

The BPGD structural dispatcher was also updated to bind session ownership to its deterministic shot identity; otherwise separate shots with identical syndromes shared the same evidence-level owner label. This did not change the capability-token foreign-owner check.

## Issues Encountered

The first posterior-flip fixture chose a zero-valued posterior, so changing its sign left outgoing messages equal. The fixture now chooses a nonzero posterior target and verifies the actual V2C change.

## Next Phase Readiness

Plans 05-04 through 05-07 can use continuing sessions, fresh branches, and new work categories. The version 6 public manifest and ledger verifier still belong to Plan 05-08.

## Self-Check: PASSED

- Three production commits and all declared files exist.
- Both task verification commands passed, including inherited budget tests.
