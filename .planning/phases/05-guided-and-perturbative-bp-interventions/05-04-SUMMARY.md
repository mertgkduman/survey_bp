---
phase: 05-guided-and-perturbative-bp-interventions
plan: "04"
subsystem: canonical-decoder
tags: [bpgd, guided-decimation, replay, budget]
requires:
  - phase: "05-02"
    provides: source-qualified BPGD decisions
  - phase: "05-03"
    provides: owned continuing BP session and typed work leaves
provides:
  - bounded BPGD round controller with explicit zero, tie, infinity, and final-round rules
  - deterministic reconstruction of round transitions, original validity, and unique work
affects: [05-08, 05-10, 05-11]
actuals:
  tokens: 9000
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [truth-free-controller-replay, original-check-leaf]
key-files:
  created: []
  modified:
    - src/bp_registry/canonical/guided_decimation.py
    - tests/canonical/test_guided_decimation.py
key-decisions:
  - "An infinite posterior reliability is a numerical-failure terminal under the declared finite-prior interpretation."
  - "The final fixation ends the last round without an undeclared extra BP sweep."
  - "Original-syndrome validation uses a separate reserved work leaf after every completed sweep."
requirements-completed: [MOD-02]
coverage:
  - id: bpgd-rounds
    description: Bounded BPGD rounds with deterministic original-index tie and final-round behavior
    requirement: MOD-02
    verification:
      - kind: unit
        ref: "tests/canonical/test_guided_decimation.py#test_final_round_returns_after_last_fixation_without_extra_sweep"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_guided_decimation.py#test_reliability_tie_zero_and_eligibility_exhaustion"
        status: pass
    human_judgment: false
  - id: bpgd-replay
    description: Decoder-visible reconstruction rejects altered targets, state digests, and work
    requirement: MOD-02
    verification:
      - kind: unit
        ref: "tests/canonical/test_guided_decimation.py#test_replay_rejects_rehashed_target_and_work_tampering"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_guided_decimation.py#test_denial_replay_preserves_last_committed_state_and_work"
        status: pass
    human_judgment: false
duration: 12min
completed: 2026-09-30
status: complete
---

# Phase 5 Plan 04: Replayable guided decimation

The canonical BPGD controller now runs bounded complete BP rounds, fixes one eligible finite prior after each failed round, and records every state and work boundary for deterministic replay.

## Accomplishments

- Reliability ranks the absolute posterior over undecimated original indices, with smallest-index ties and a positive prior at exact zero.
- The controller retains committed BP messages across rounds, returns after the last fixation, and records distinct validity, denial, exhaustion, cap, and numerical terminals.
- Original-syndrome checks have separate committed work leaves. Replay regenerates decisions and work from the graph, syndrome, source-qualified spec, and budget limits rather than trusting declared hashes.

## Task Commits

1. **Complete BPGD state machine and reconstruction** — `92aa555` (`feat`)
2. **Plan metadata** — this summary commit (`docs`)

## Verification

- Guided tests: 10 passed.
- Task 1 selection: 4 passed, 6 deselected.
- Task 2 selection: 5 passed, 5 deselected.
- Independent intervention algebra oracle: 16,384 shortening cases and four constructed cases passed.

## Deviations from Plan

None. Public ledger integration remains assigned to Plan 05-08.

## Issues Encountered

The first replay fixture converged in round two, so a separate inconsistent-syndrome graph now exercises the final fixation and cap path.

## Next Phase Readiness

Plan 05-08 can serialize the typed controller result and bind it to the public shot identity.

## Self-Check: PASSED

The declared controller and test files are committed, and both plan selections passed.
