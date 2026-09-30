---
phase: 05-guided-and-perturbative-bp-interventions
plan: "02"
subsystem: canonical-decoder
tags: [source-qualification, gf2, transform, lift]
requires:
  - phase: "05-01"
    provides: version 6 guided tracer and original-problem boundary
provides:
  - six-arm source and adaptation decision record
  - exact fixed-coordinate and certified syndrome transforms
  - total original-coordinate lifts with independent syndrome validation
affects: [05-04, 05-05, 05-06, 05-07, 05-08]
actuals:
  tokens: 7875
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns: [source-qualification-matrix, certified-transform-lift, immutable-working-view]
key-files:
  created:
    - docs/evidence/phase5-source-decisions.json
    - src/bp_registry/canonical/transformations.py
    - tests/canonical/test_impulse.py
    - tests/canonical/test_perturbative_interventions.py
    - tests/test_phase5_public_execution.py
  modified:
    - src/bp_registry/canonical/problems.py
key-decisions:
  - "Keep unknown BPGD, impulse, and sign-flip author-code identities unverified rather than claiming absence."
  - "Treat structural impulse shortening as a controlled adaptation distinct from source unchanged-graph infinite-LLR forcing."
  - "Require algebraic Ht evidence for syndrome lifts; a row mask alone cannot certify an original recovery."
requirements-completed: []
requirements-partial: [MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04]
coverage:
  - id: source-qualification
    description: Versioned source and adaptation identities for all six Phase 5 arms
    verification:
      - kind: unit
        ref: "tests/test_phase5_public_execution.py#test_source_decisions_qualification_native_availability_restart_distance"
        status: pass
    human_judgment: false
  - id: transform-lift
    description: Exact shortening and syndrome XOR certificate with independent original checks
    verification:
      - kind: unit
        ref: "tests/canonical/test_impulse.py#test_shortening_lift_exhaustive_matches_independent_gf2_oracle"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_perturbative_interventions.py#test_syndrome_certificate_lift_and_original_invalid_without_it"
        status: pass
    human_judgment: false
duration: 8min
completed: 2026-09-30
status: complete
---

# Phase 5 Plan 02: Source decisions and certified transforms

Every planned intervention now has an explicit source, adaptation, availability, and unresolved-detail record. Pure GF(2) transforms create immutable working views whose lifts are checked against the immutable original syndrome.

## Accomplishments

- Recorded all six source revisions, kernel families, triggers, target/reset/lift rules, verified repository commits where available, B1's bounded distance, and the mechanism-only `t_cap=8` status.
- Added exact coordinate shortening and syndrome XOR transforms with lineage-bound certificates; malformed maps and corrupted certificates fail closed.
- Kept finite prior bias distinct from exact fixing and retained all original check rows, including empty checks after shortening.
- Exhaustively checked 16,384 production lift cases and the independent design oracle; covered all-fixed success/contradiction and source-incompatible row masks.

## Task Commits

1. **Freeze source decision matrix** — `df22239` (`docs`)
2. **Transform, lift, and independently validate** — `200b6cd` (`feat`)
3. **Plan metadata** — this summary commit (`docs`)

## Verification

- Source decision test: 1 passed.
- Transform and syndrome certificate tests: 4 passed.
- `tools/validate_intervention_design.py --check`: 16,384 shortening cases and four constructed cases passed.
- Historical truth-boundary tests: 6 passed after preserving their rejection contract.

## Deviations from Plan

The existing `WorkingProblem` identity-edge error wording was preserved for historical tests while admitting explicit transform edges. No semantic identity behavior was loosened.

## Issues Encountered

The historical truth-boundary test matched the old `identity edge` error text. Transform metadata checks now retain that phrase while still rejecting uncertified transforms.

## Next Phase Readiness

Plans 05-04 through 05-07 can build controllers on the typed transform/lift primitives. Source labels remain qualifications, not reproduction results. The Plotly package gate remains a separate blocking-human plan.

## Self-Check: PASSED

- Both task commits and all declared created files exist.
- Both plan verification commands and the inherited truth-boundary regression passed.
