---
phase: 05-guided-and-perturbative-bp-interventions
plan: "05"
subsystem: canonical-decoder
tags: [impulse, shortening, lifted-selection, replay]
requires:
  - phase: "05-02"
    provides: exact shortening transform and source decision record
  - phase: "05-03"
    provides: transactional BP session and work accounting
provides:
  - bounded baseline-triggered impulse controller with independent coordinate attempts
  - separate semantic force-one and exact-shortening realization identities
  - stable lifted-candidate selection and deterministic attempt/work reconstruction
affects: [05-08, 05-10, 05-11]
actuals:
  tokens: 13000
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [fresh-branch-attempts, lifted-before-selection, symbolic-infinite-operator]
key-files:
  created:
    - src/bp_registry/canonical/impulse.py
  modified:
    - tests/canonical/test_impulse.py
key-decisions:
  - "The unchanged-graph force-to-one arm records negative infinity symbolically and executes finite SPA saturation with a hard target bit; its qualification is source_operator_semantic_adaptation, not a native trajectory claim."
  - "The exact-shortening arm retains a separate controlled_css_adaptation identity and checks a lineage-bound lift before candidate eligibility."
  - "No-proposal and attempt-cap terminals remain distinct; attempted branches stay in unique-leaf work."
requirements-completed: [MOD-03]
coverage:
  - id: impulse-lifecycle
    description: Baseline trigger, fresh bounded attempts, realization labels, and original checks
    requirement: MOD-03
    verification:
      - kind: unit
        ref: "tests/canonical/test_impulse.py#test_baseline_success_has_no_impulse_attempts"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_impulse.py#test_trigger_fresh_shortening_contradiction_and_cap"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_impulse.py#test_source_semantic_forced_one_keeps_graph_and_json_finite"
        status: pass
    human_judgment: false
  - id: impulse-selection-replay
    description: Stable original-coordinate selection and replay of all branch and leaf work
    requirement: MOD-03
    verification:
      - kind: unit
        ref: "tests/canonical/test_impulse.py#test_minimum_weight_and_first_convergence_are_stable_under_worker_order"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_impulse.py#test_impulse_replay_rejects_changed_branch_and_work"
        status: pass
    human_judgment: false
duration: 10min
completed: 2026-09-30
status: complete
---

# Phase 5 Plan 05: Bounded impulse search

The impulse controller runs a baseline BP attempt, branches only after original-syndrome invalidity, and compares independently lifted candidates in declared coordinate order.

## Accomplishments

- Each coordinate gets a fresh BP session, owner identity, working view, action leaf, and sweep leaves. Budget denial, contradictory checks, numerical failure, invalid lifts, valid candidates, caps, and no proposals have distinct outcomes.
- The unchanged-graph source operator and exact-shortening adaptation have separate identities and qualifications. The former stores negative infinity only as a symbolic instruction, with finite saturation disclosed as an adaptation.
- Minimum-weight selection uses original-coordinate Hamming weight; first-convergence stops after the earliest declared valid attempt. Replay regenerates attempt and work evidence from decoder-visible inputs.

## Task Commits

1. **Impulse controller and deterministic fixtures** — `451fa69` (`feat`)
2. **Plan metadata** — this summary commit (`docs`)

## Verification

- Impulse test module: 10 passed.
- Task 1 selection: 7 passed, 2 deselected.
- Task 2 selection: 3 passed, 6 deselected.
- Independent algebra oracle: 16,384 shortening cases and four constructed cases passed.

## Deviations from Plan

None. The finite numerical realization of semantic force-to-one is explicitly qualified as an adaptation.

## Issues Encountered

A search fixture initially used a lineage label lacking the required `original-` prefix. Correcting the fixture exposed a valid first-convergence case with one attempt and a minimum-weight case that examined all five coordinates.

## Next Phase Readiness

Plan 05-08 can expose both impulse realizations through public manifests and ledgers with their distinct fidelity status.

## Self-Check: PASSED

The declared controller and tests are committed, and both plan test selections passed.
