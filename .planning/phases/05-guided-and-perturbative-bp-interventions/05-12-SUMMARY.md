---
phase: 05-guided-and-perturbative-bp-interventions
plan: "12"
status: complete
subsystem: deterministic-code-fixtures
tags: [bb-144, hgp, gf2, intervention-oracle]
requires: [05-04, 05-05, 05-06, 05-07]
provides:
  - exact tracked BB-144 and generated-HGP artifact fixtures
  - independent fixed-syndrome shortening, lift, and original validation checks
  - deterministic compatible-policy assertions and explicit unavailable restart checks
affects: [05-11, 05-13]
requirements-completed: [MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04]
completed: 2026-09-30
---

# Phase 5 Plan 12: Deterministic cross-code fixtures

BB-144 and generated HGP fixtures pin the Phase 3 artifact bytes and ordered CSS code, plus the HGP generator seed, dimensions, and metadata. Fixed nonzero observations have literal packed syndrome values. An independent row-parity oracle verifies fixed-coordinate shortening, residual syndrome, lift, and original validation.

Five compatible interventions are exercised on each fixed observation with deterministic target/order/reset and unique typed leaf-work assertions. Restart Belief is explicitly unavailable on these codes because exact distance is not established and the B1 mechanism preset is code-specific. No Monte Carlo sample or performance claim enters these fixtures.

Verification: 15 focused tests passed; the independent exhaustive design checker passed 16,384 shortening cases and four constructed cases. Production test commit: `250d8dd`.
