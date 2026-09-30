---
phase: 05-guided-and-perturbative-bp-interventions
plan: "06"
subsystem: canonical-decoder
tags: [freezing, syndrome-flip, sign-flip, replay]
requires:
  - phase: "05-02"
    provides: source decision record and certified XOR/shortening transformations
  - phase: "05-03"
    provides: owned BP session, typed work, and decoder-only stream identities
provides:
  - bounded frustrated-check freezing with temporary zero fixations and release
  - oscillation-ranked syndrome tests with certified XOR lifts
  - normalized-min-sum posterior sign action staged to the next BP boundary
  - idempotent action gate and deterministic reconstruction for all three controllers
affects: [05-08, 05-10, 05-11]
actuals:
  tokens: 26000
  tasks: 3
  commits: 1
tech-stack:
  added: []
  patterns: [idempotent-one-leaf-action, certified-xor-lift-before-selection, staged-posterior-mutation]
key-files:
  created:
    - src/bp_registry/canonical/interventions.py
  modified:
    - src/bp_registry/canonical/intervention_session.py
    - tests/canonical/test_perturbative_interventions.py
key-decisions:
  - "Binary CSS freezing uses a fresh exact-shortening branch for each temporary zero fixation; release reconstructs from the immutable original. This is a controlled adaptation of a quaternary source."
  - "BP-SF replaces unseeded sampling and parallel first-arrival with a purpose-separated seeded declared order."
  - "Sign-only Global targeting uses normalized min-sum; a staged action changes posterior and decision while preserving messages until the next sweep."
requirements-completed: [INT-01, INT-02, INT-03]
coverage:
  - id: freezing
    description: Bounded frustrated-check selection, temporary zero freeze, and release from the original
    requirement: INT-01
    verification:
      - kind: unit
        ref: "tests/canonical/test_perturbative_interventions.py#test_freezing_eligibility_lifetime_release_retry_and_cap"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_perturbative_interventions.py#test_freezing_syndrome_and_sign_replay_reject_semantic_tampering"
        status: pass
    human_judgment: false
  - id: syndrome-flip
    description: Seeded oscillation ranking, certified XOR lift, original validity, and declared-order selection
    requirement: INT-02
    verification:
      - kind: unit
        ref: "tests/canonical/test_perturbative_interventions.py#test_syndrome_flip_first_declared_valid_is_worker_order_invariant"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_perturbative_interventions.py#test_syndrome_certificate_lift_and_original_invalid_without_it"
        status: pass
    human_judgment: false
  - id: sign-flip
    description: Normalized-min-sum Global target with staged posterior action and continued messages
    requirement: INT-03
    verification:
      - kind: unit
        ref: "tests/canonical/test_perturbative_interventions.py#test_sign_flip_posterior_global_target_and_message_continuation"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_perturbative_interventions.py#test_sign_flip_staged_action_rejects_duplicate_and_preserves_messages"
        status: pass
    human_judgment: false
duration: 18min
completed: 2026-09-30
status: complete
---

# Phase 5 Plan 06: Three perturbative intervention families

Freezing, syndrome flip, and posterior sign flip now have separate bounded controllers with explicit source qualifications, original validation, replay, and leaf work.

## Accomplishments

- Freezing identifies frustrated checks after a failed period, draws neighbors from a decoder-only stream without repeats, temporarily fixes zero in a fresh CSS branch, and releases each failed trial from the immutable original.
- BP-SF counts hard-decision oscillations, declares a seeded order of bounded test vectors, solves each transformed syndrome in a fresh session, and selects only after a certified XOR lift and original check.
- The sign-only Global adaptation runs normalized min-sum, ranks variables by mismatched-check incidence, stages a posterior sign change without changing existing messages, and applies its outgoing effect at the next sweep boundary.
- An owner-local action gate makes duplicate commits idempotent and rejects stale proposals; reconstruction reruns all three state machines from decoder-visible inputs.

## Task Commits

1. **Perturbative controllers and staged session action** — `7db6963` (`feat`)
2. **Plan metadata** — this summary commit (`docs`)

## Verification

- Controller, session, guided, and impulse targeted modules: 35 passed.
- Task selections: freezing 1 passed; syndrome flip 4 passed; sign flip 3 passed.
- Independent algebra oracle: 16,384 shortening cases and four constructed cases passed.
- Full regression suite: running at summary authoring time; final result is recorded in the next execution state.

## Deviations from Plan

The shared BP session gained a staged posterior operation and optional compatible kernel so the sign-only controller can execute normalized min-sum without mutating existing messages at the action boundary. The earlier immediate sign mutation remains available for its previous direct contract.

## Issues Encountered

An exact XOR certificate makes working validity equivalent to lifted original validity. The test now explicitly records that a working-valid raw candidate can be original-invalid before the lift, and proves it becomes eligible only after certified lifting.

## Next Phase Readiness

Plan 05-08 can expose all three families through public manifests and event ledgers while preserving source-family and adaptation labels.

## Self-Check: PASSED

The controllers and tests are committed, all three task selections pass, and the independent algebra oracle passes.
