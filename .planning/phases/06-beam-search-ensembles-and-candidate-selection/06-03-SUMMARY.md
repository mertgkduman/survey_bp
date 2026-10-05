---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "03"
subsystem: impulse-decoding
tags: [impulse, forced-zero, forced-one, v2c, numerical-controls, replay]
requires:
  - phase: "06-01"
    provides: strict literature-policy route and compatible Phase 5 dispatch
provides:
  - Closed semantic force-to-zero and force-to-one impulse attempts
  - Source-qualified V2C-only magnitude-25 numerical control
  - Replayable forced-value, clip-boundary, and public-dispatch evidence
affects: [06-09, css-literature-gate, bhatnagar-2026-impulse-decoding]
actuals:
  tokens: 8014
  tasks: 2
  commits: 1
plan_head_before: c975a77cccf04cf95c923b497df94ec747d374f0
tech-stack:
  added: []
  patterns: [closed binary realization, source-boundary numerical transform, immutable original validation]
key-files:
  created: []
  modified: [src/bp_registry/canonical/contracts.py, src/bp_registry/canonical/intervention_session.py, src/bp_registry/canonical/impulse.py, src/bp_registry/canonical/phase5.py, tests/canonical/test_impulse.py]
key-decisions:
  - "Semantic zero and one use distinct closed realization names, signed finite surrogates, canonical identities, and attempt evidence; contradictory optional forced values are rejected."
  - "The Bhatnagar magnitude-25 control runs only after V2C construction and before V2C state commit. It never transforms C2V, priors, posterior beliefs, or candidate scoring."
  - "The source clip and V2C damping are mutually exclusive, and legacy force-one and exact-shortening payloads retain their existing meanings."
requirements-completed: [INT-05, CAN-01]
duration: 18min
completed: 2026-10-05
status: complete
---

# Phase 06 Plan 03: Semantic Impulse and V2C Clip Summary

**Bhatnagar impulse decoding now executes force-to-zero and force-to-one as distinct, replayable semantic controllers and applies its magnitude-25 numerical control only at the V2C state boundary.**

## Accomplishments

- Added `semantic_forced_zero` alongside the historical `semantic_forced_one` and `exact_shortening` realizations.  Zero uses a positive finite LLR, fixes target outgoing V2C messages and the target candidate bit to zero, and records `impulse_positive_infinite_semantic_v1`; one preserves the negative finite and legacy identity.
- Added closed `forced_value` validation to the internal and public Phase 5 contracts.  Attempt rows, working lineage, controller identity, replay, and Phase 5 evidence expose the selected binary value.
- Added an optional registered `v2c_clip = 25.0` session control.  It runs after V2C construction and before committed session state, is carried by baseline and fresh attempt sessions, enters state and controller evidence, and cannot be combined with damping.
- Retained original-problem validation and stable selection ties.  Historical semantic force-one and exact-shortening regression coverage remains green.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_impulse.py -k 'forced_zero or forced_one or forced_value or first_convergence or minimum_weight or historical or v2c_clip or clip_boundary or finite or fresh or replay or original' -x` — 11 passed, 5 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_impulse.py` — 16 passed.
- A broader Phase 5 fixture run completed 35 tests without a failure before exceeding its normal execution window. It was stopped because it was outside this plan's focused verification scope.

## Task Commit

1. **Tasks 1–2: semantic force values and V2C-only clip** — `3cb0a10` (`feat`)

The tasks share the same typed realization and session boundary. They were committed together so public dispatch cannot expose a forced value or numerical control that the fresh session cannot execute.

## Deviations from Plan

None.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed all five owned source/test files exist and their focused regression suite passes.
- Confirmed commit `3cb0a10` exists in repository history.
