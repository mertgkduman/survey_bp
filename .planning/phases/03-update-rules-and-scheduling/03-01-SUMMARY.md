---
phase: 03-update-rules-and-scheduling
plan: "01"
subsystem: canonical-execution
tags: [min-sum, flooding, local-step, pydantic, CLI, verification]
requires:
  - phase: 02-canonical-css-execution-and-policy-contracts
    provides: strict V2 canonical manifests, structural ledgers, scoped work budgets, and flooding SPA
provides:
  - strict V3 min-sum/flooding manifest dispatch through the public canonical CLI
  - closed min-sum update rule with explicit numerical evidence
  - schedule-neutral local-step admission used by flooding execution
affects: [03-update-rules-and-scheduling, update-rules, scheduling, verification]
plan_head_before: 2169218bd675b39eb2c2c3667960164e0242dc8a
actuals:
  tokens: 10434
  tasks: 1
  commits: 2
tech-stack:
  added: []
  patterns:
    - complete local-step work is reserved before mutation and convergence evaluation
    - versioned canonical manifests preserve V2 SPA while V3 binds min-sum semantics
key-files:
  created:
    - src/bp_registry/canonical/updates.py
    - tests/canonical/test_update_rules.py
  modified:
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/manifests.py
    - src/bp_registry/runner.py
    - src/bp_registry/canonical/verification.py
    - tests/test_canonical_cli.py
key-decisions:
  - "V3 is the explicit min-sum public-contract boundary; V2 retains binary SPA semantics unchanged."
  - "Flooding delegates admitted sweeps to CanonicalLocalStepExecutor, whose reservation includes candidate/convergence work."
requirements-completed: [UPD-01]
coverage:
  - id: D1
    description: "Public V3 min-sum/flooding preflight, run, and verify-run reconstruction."
    requirement: UPD-01
    verification:
      - kind: integration
        ref: tests/test_canonical_cli.py#test_min_sum_public_manifest_preflights_runs_and_verifies
        status: pass
    human_judgment: false
  - id: D2
    description: "Signed-minimum, degree-one, saturation-boundary, nonfinite, and denied-reservation semantics."
    requirement: UPD-01
    verification:
      - kind: unit
        ref: tests/canonical/test_update_rules.py
        status: pass
    human_judgment: false
duration: 13m
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 01: Update Rules and Scheduling Summary

**A strict V3 min-sum/flooding manifest now runs through the public canonical CLI with independently reconstructed terminal evidence and atomic local-step admission.**

## Performance

- **Duration:** 13m
- **Started:** 2026-09-24T09:13:30Z
- **Completed:** 2026-09-24T09:26:01Z
- **Tasks:** 1/1
- **Files modified:** 13

## Accomplishments

- Added `CheckUpdateRule`, `MinSumUpdate`, and numerical evidence with float64 signed-minimum, degree-one, zero-sign, finite-input, and saturation semantics.
- Added V3 public manifest dispatch while preserving V2 binary-SPA/flooding parsing, execution, and verification semantics.
- Promoted a schedule-neutral local-step executor and routed flooding admission through it before any state mutation.
- Added public CLI and independent-oracle regressions for V3 min-sum execution and denied-reservation immutability.

## Task Commits

1. **Task 1 RED: min-sum boundary tests** — `92f2433` (`test`)
2. **Task 1 GREEN: min-sum local-step execution** — `3794edf` (`feat`)

## Files Created/Modified

- `src/bp_registry/canonical/updates.py` — closed min-sum update contract and evidence.
- `src/bp_registry/canonical/execution.py` — reusable local-step proposal/progress/executor and flooding integration.
- `src/bp_registry/manifests.py` and `src/bp_registry/runner.py` — strict V3 dispatch without altering V2 meaning.
- `src/bp_registry/canonical/verification.py` — independent min-sum reconstruction.
- `tests/canonical/test_update_rules.py` and `tests/test_canonical_cli.py` — numerical oracle, rollback, and public CLI coverage.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_update_rules.py tests/test_canonical_cli.py -k 'min_sum or historical_flooding'` — 9 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_numerics.py tests/canonical/test_flooding.py tests/canonical/test_contracts.py tests/test_canonical_cli.py tests/test_ledger.py` — passed before the final CLI-environment-only test refinement; the changed V3 test subsequently passed in the targeted command above.
- `gsd-tools check tdd-red-evidence .planning/phases/03-update-rules-and-scheduling/03-01-red-evidence.json --raw` — `RED_EVIDENCE_OK`.

## TDD Gate Compliance

- **RED:** `92f2433` intentionally failed `test_min_sum_public_update_contract_exists`; persisted evidence validated as `RED_EVIDENCE_OK`.
- **GREEN:** `3794edf` makes the selected min-sum and historical-flooding suite pass.
- **REFACTOR:** not needed as a separate commit; the GREEN implementation contains the focused integration cleanup.

## Decisions Made

- V3 owns min-sum’s distinct profile and closed policy kind so V2 evidence is never relabeled or reinterpreted.
- The local-step reservation includes the check budget before computation; denial therefore leaves the supplied message, progress, and schedule-owned inputs unchanged.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Test contract] Corrected the rollback test to use the existing `candidate_checks` work dimension.**
   - **Found during:** Task 1 GREEN verification.
   - **Issue:** The first test named a nonexistent `syndrome_checks` field, so it could not construct a valid `WorkVector`.
   - **Fix:** Bound the mandatory convergence check to the established `candidate_checks` dimension.
   - **Files modified:** `tests/canonical/test_update_rules.py`
   - **Verification:** targeted update-rule suite passed.
   - **Committed in:** `3794edf`

2. **[Rule 3 - Test environment] Forced subprocess CLI coverage to import the active worktree source.**
   - **Found during:** Task 1 GREEN verification.
   - **Issue:** the installed package did not yet include the uncommitted V3 module, so a subprocess CLI test loaded stale code.
   - **Fix:** scoped `PYTHONPATH` to the worktree `src/` directory in that test.
   - **Files modified:** `tests/test_canonical_cli.py`
   - **Verification:** public CLI subprocess preflight, canonical run, and verify-run passed.
   - **Committed in:** `3794edf`

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 3).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The V3 update-rule and local-step tracer is ready for additional update policies and schedule implementations. Historical V2 SPA/flooding evidence remains replayable.

## Self-Check: PASSED

---

*Phase: 03-update-rules-and-scheduling*
*Completed: 2026-09-24*
