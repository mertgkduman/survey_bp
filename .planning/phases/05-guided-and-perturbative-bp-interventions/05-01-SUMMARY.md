---
phase: 05-guided-and-perturbative-bp-interventions
plan: "01"
subsystem: canonical-decoder
tags: [bpgd, css, intervention, provenance]
requires:
  - phase: "02"
    provides: canonical CSS kernel, scoped budgets, structural ledger, truth boundary
  - phase: "04"
    provides: owned state transition and Relay regression patterns
provides:
  - strict compact version 6 guided-decimation contract
  - owned BP session with atomic finite-prior mutation and sweep reservations
  - source-qualified BPGD tracer through original validation and structural events
affects: [phase-05, phase-06]
actuals:
  tokens: 8278
  tasks: 1
  commits: 2
tech-stack:
  added: []
  patterns: [reserve-compute-commit, truth-sealed-controller, versioned-compact-manifest]
key-files:
  created:
    - src/bp_registry/canonical/intervention_session.py
    - src/bp_registry/canonical/guided_decimation.py
    - tests/canonical/test_guided_decimation.py
  modified:
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/execution.py
key-decisions:
  - "Keep the version 6 guided policy in a separate composition class so V2–V5 continue rejecting that new kind."
  - "Use Algorithm 1 v2's disclosed zero and final-round interpretations, with finite prior magnitude 25 and stable original-index ties."
requirements-completed: [MOD-02]
requirements-partial: [MOD-03, INT-01, INT-02, INT-03, INT-04]
coverage:
  - id: guided-tracer
    description: Versioned BPGD session transition with independent original validation
    requirement: MOD-02
    verification:
      - kind: integration
        ref: "tests/canonical/test_guided_decimation.py#test_tracer_original_validation_and_hidden_truth_sealing"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_guided_decimation.py#test_denial_rollback_keeps_parent_session_exactly_intact"
        status: pass
    human_judgment: false
duration: 15min
completed: 2026-09-30
status: complete
---

# Phase 5 Plan 01: Guided BP tracer

The canonical structural path now executes a source-qualified guided prior fixation in an owned BP session. It checks a candidate against the immutable original syndrome before independent truth-aware evaluation.

## Accomplishments

- Added a strict version 6 compact contract without widening the historical policy registries.
- Added a session that reserves each complete flooding sweep and fixation before computing and committing the next state; a denied reservation leaves its parent state unchanged.
- Recorded source revision, interpreted zero/final-round rules, stable target selection, state digests, eligibility, reservation leaves, original validity, and atomic work in the structural ledger.
- Kept hidden truth out of the controller; a metamorphic test changes truth while keeping decoder-visible events fixed.

## Task Commits

1. **Task 1: Run one finite-bias BPGD transition** — `50409b5` (`feat`)
2. **Plan metadata** — this summary commit (`docs`)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_guided_decimation.py -k 'tracer or original_validation or denial_rollback or historical_manifest' -x` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_relay.py -k 'tracer or posterior_transfer or historical_manifest'` — 1 passed, 15 deselected.
- `git diff --check` — passed before the production commit.

## Deviations from Plan

The production tracer can run a second bounded BP block when the declared round limit allows it. This exercises a successful post-fixation candidate and proves that truth changes affect only independent evaluation. The original Algorithm 1 final-fixation rule still returns without another BP block.

## Issues Encountered

The first test fixture's most reliable bit was an already satisfied check variable. A second algebraic fixture makes the fixation target and successful continuation inspectable.

## Next Phase Readiness

Plan 05-02 can add source decisions and exact transformed-problem algebra. Plan 05-03 can extend the session and budget contracts. The version 6 public saved-manifest and ledger verifier are owned by Plan 05-08; this plan proves only the compact structural path.

## Self-Check: PASSED

- All three created files exist; production commit `50409b5` contains all declared implementation paths.
- Both plan verification commands passed, including the inherited Relay regression.
