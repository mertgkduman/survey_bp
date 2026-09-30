---
phase: 05-guided-and-perturbative-bp-interventions
plan: "07"
subsystem: canonical-decoder
tags: [restart-belief, residual-syndrome, b1-distance, replay]
requires:
  - phase: "05-02"
    provides: source decisions, B1 distance bound, and certified transformations
  - phase: "05-03"
    provides: fresh session reset and unique leaf work
provides:
  - bounded deterministic Restart Belief root, branch, and residual controller
  - exact-distance preset rejection for B1 and t_cap=8 mechanism qualification
  - two-step certified lift, strict lower-weight selection, and deterministic reconstruction
affects: [05-08, 05-10, 05-11]
actuals:
  tokens: 14500
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [fresh-residual-reset, inserted-error-only-branch-memory, two-stage-certified-lift]
key-files:
  created:
    - src/bp_registry/canonical/restarting.py
  modified:
    - tests/canonical/test_restart_execution.py
key-decisions:
  - "B1 exact distance remains unavailable; the B1 preset requires t_cap=8, eta<=8, and <=10 residual sweeps and is pilot_adaptation only on dimension-compatible input."
  - "A small graph with a B1-labeled test spec is marked development_fixture, preventing a false B1 result claim."
  - "Each residual solve starts from a fresh session; inserted-error state alone carries across solves, with two certified lifts and an original check before selection."
requirements-completed: [INT-04]
coverage:
  - id: restart-lifecycle
    description: Root LLR order, bounded branches, fresh residual solves, inserted-error state, and B1 distance qualification
    requirement: INT-04
    verification:
      - kind: unit
        ref: "tests/canonical/test_restart_execution.py#test_restart_distance_preset_rejects_b1_and_adaptation_qualifies"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_restart_execution.py#test_restart_root_branch_residual_reset_inserted_and_t_cap"
        status: pass
    human_judgment: false
  - id: restart-selection-replay
    description: Strict lower original weight, stable ties, certified validation, and unique-leaf work replay
    requirement: INT-04
    verification:
      - kind: unit
        ref: "tests/canonical/test_restart_execution.py#test_restart_strict_lower_weight_keeps_stable_tie_and_valid_lifts"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_restart_execution.py#test_restart_replay_rejects_residual_and_work_tampering"
        status: pass
    human_judgment: false
duration: 12min
completed: 2026-09-30
status: complete
---

# Phase 5 Plan 07: Bounded Restart Belief

The Restart Belief controller now orders root LLRs, opens bounded deterministic branches, rebuilds each residual BP solve from a fresh session, and selects only strictly lighter original-valid lifted candidates.

## Accomplishments

- Residual syndromes are computed as `s XOR He`; inserted coordinates are fixed to zero in a fresh structural view, then the resulting candidate is lifted first to residual coordinates and then to the original problem.
- Every branch and residual records inserted-error lineage, before/after session state, reset and preserved fields, contradiction checks, denials, validation, next target, and unique leaf work.
- B1's bounded distance of 18–24 cannot enter an exact-distance preset. The named `t_cap=8` mechanism remains a pilot adaptation on dimension-compatible B1 input, while small fixtures are explicitly development evidence.
- Source execution records randomness as `not_applicable`; deterministic replay regenerates all decisions and work.

## Task Commits

1. **Restart controller and adversarial fixtures** — `b9a3ffe` (`feat`)
2. **Plan metadata** — this summary commit (`docs`)

## Verification

- Restart test module: 12 passed.
- Task 1 selection: 4 passed, 8 deselected.
- Task 2 selection: 4 passed, 8 deselected.
- Independent algebra oracle: 16,384 shortening cases and four constructed cases passed.

## Deviations from Plan

A code-identity status and development-fixture qualification were added so a tiny test graph cannot inherit the B1 pilot label solely from a spec string. The public manifest preflight in Plan 05-08 must bind actual B1 graph identity.

## Issues Encountered

The inconsistent two-check graph exposed a terminal contradictory empty check only after the second inserted error. The fixture now checks that branch and its contradiction leaf explicitly.

## Next Phase Readiness

Plan 05-08 can persist restart branches, residual certificates, and B1 qualification in public ledgers.

## Self-Check: PASSED

The controller and tests are committed, both targeted selections pass, and the independent oracle passes.
