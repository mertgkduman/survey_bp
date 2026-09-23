---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "10"
subsystem: canonical-css-public-execution
tags: [canonical-bp, executable-preflight, scoped-budgets, flooding, work-accounting, provenance]
requires:
  - phase: 02-08
    provides: strict public canonical manifest and structural evidence path
  - phase: 02-09
    provides: executable canonical tutorial and phase-review gap register
provides:
  - executable admission for the one implemented Phase 2 seven-role baseline
  - exact scoped WorkVector caps with no scalar work proxy
  - public atomic flooding execution with durable BP-call and budget-denial evidence
affects: [phase-02-plan-11, phase-02-plan-12, canonical-results, policy-expansion]
actuals:
  tokens: 14011
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [strict-executable-admission, resource-specific-budget-vectors, reserve-before-mutation, leaf-derived-terminal-work]
key-files:
  created: []
  modified: [src/bp_registry/manifests.py, src/bp_registry/runner.py, src/bp_registry/canonical/execution.py, data/manifests/canonical-three-qubit-development.json, data/manifests/schema-canonical-v2.json, tests/test_canonical_cli.py, tests/canonical/test_budgets.py]
key-decisions:
  - "Only the implemented binary-SPA/flooding/stateless/identity/syndrome-or-budget/stable-first baseline crosses public preflight; identity-only roles are explicit evidence rather than alternate executable behavior."
  - "Public work caps are complete WorkVector maps at shot, search, and attempt scopes; BP calls and flooding sweeps reserve leaf work before mutation."
patterns-established:
  - "Public structural terminals and work facts reduce from the same BudgetTree attempt summary."
requirements-completed: [ENG-02, ENG-03, ENG-06, SCH-01, LED-03]
coverage:
  - id: D1
    description: "Public preflight rejects every contract-valid non-baseline executable composition and persists only exact resource-specific limits."
    requirement: ENG-02
    verification:
      - kind: integration
        ref: tests/test_canonical_cli.py::test_public_preflight_rejects_nonbaseline_executable_bindings
        status: pass
      - kind: integration
        ref: tests/test_canonical_cli.py::test_public_budget_schema_uses_exact_work_resources
        status: pass
    human_judgment: false
  - id: D2
    description: "Public canonical attempts reserve BP calls and atomic flooding work before mutation, preserving scoped denial, edge-free, and numerical-failure boundaries."
    requirement: ENG-03
    verification:
      - kind: integration
        ref: tests/canonical/test_budgets.py
        status: pass
      - kind: unit
        ref: tests/canonical/test_work_accounting.py
        status: pass
    human_judgment: false
  - id: D3
    description: "Completed public attempts report the same committed one-BP-call WorkVector in work and terminal evidence."
    requirement: LED-03
    verification:
      - kind: integration
        ref: tests/test_canonical_cli.py::test_public_canonical_work_counts_one_bp_call_per_attempt
        status: pass
    human_judgment: false
metrics:
  duration: 9 min
  completed: 2026-09-23
status: complete
plan_head_before: 3cf4de62648ff47989172032b176c695f2839ec0
commits: 4
---

# Phase 02 Plan 10: Executable Baseline Admission and Scoped Work Summary

**The public canonical path now admits only the implemented Phase 2 baseline, carries complete per-resource caps into atomic flooding, and records one committed BP call for each real attempt.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-23T21:56:57Z
- **Completed:** 2026-09-23T22:06:31Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

1. Added executable-baseline admission and explicit active versus identity-only binding effects before public sampling or ledger ownership.
2. Replaced scalar public work caps with complete, nested WorkVector maps and regenerated the checked canonical schema/manifest.
3. Routed public binary-SPA flooding through scoped BudgetTree reservations, preserving call-only work on denied or failed sweeps and matching work/terminal evidence.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py tests/canonical/test_work_accounting.py tests/test_canonical_cli.py::test_public_preflight_rejects_nonbaseline_executable_bindings tests/test_canonical_cli.py::test_public_budget_schema_uses_exact_work_resources tests/test_canonical_cli.py::test_public_canonical_work_counts_one_bp_call_per_attempt tests/test_canonical_cli.py::test_public_cap_below_one_sweep_emits_scoped_denial`

Result: `16 passed`.

The stale checked-result and full canonical CLI suite were intentionally deferred to Plan 02-12, as prescribed by this plan after the manifest migration.

## Task Commits

1. **Task 1: Make public preflight admit one executable baseline with exact resource caps**
   - `9549347` test RED: public baseline-admission regressions
   - `89c40da` feat GREEN: executable admission and resource-specific caps
2. **Task 2: Dispatch the admitted baseline through atomic scoped budgets and honest BP-call evidence**
   - `a21e240` test RED: public atomic-budget accounting regressions
   - `c7537af` feat GREEN: scoped atomic flooding dispatch

## Files Created/Modified

- `src/bp_registry/manifests.py` — validates baseline-only public execution and exact scoped resource limits.
- `src/bp_registry/runner.py` — forwards preflighted limits and binding effects to structural execution.
- `src/bp_registry/canonical/execution.py` — reserves BP calls/sweeps and emits terminal facts from committed budget leaves.
- `data/manifests/canonical-three-qubit-development.json` and `data/manifests/schema-canonical-v2.json` — carry the complete resource-cap contract.
- `tests/test_canonical_cli.py` and `tests/canonical/test_budgets.py` — cover public admission, denial, edge-free, numerical-failure, and BP-call behavior.

## Decisions Made

- Unimplemented contract-valid policy variants are rejected at the executable boundary rather than being recorded as labels for fixed behavior.
- Resource-specific caps remain independent scientific measures; no scalar conversion was introduced.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## Next Phase Readiness

Plan 02-11 can now strengthen structural ownership and candidate lineage on an honest public execution path. Plan 02-12 remains responsible for regenerating and verifying checked result artifacts after this manifest migration.

## TDD Gate Compliance

- Task 1 RED and GREEN commits: `9549347` → `89c40da`; RED evidence verified as `RED_EVIDENCE_OK`.
- Task 2 RED and GREEN commits: `a21e240` → `c7537af`; RED evidence verified as `RED_EVIDENCE_OK`.

## Self-Check: PASSED

All seven modified implementation/test/manifest artifacts and the SUMMARY exist; all four measured task commits are present in Git history.
