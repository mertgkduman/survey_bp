---
spike: 006
idea: pfister-slide-bp-reproduction
name: canonical-numerical-promotion
type: standard
validates: "Given held-out evidence and algebraic checks, when a superior numerical policy becomes the versioned canonical default, then old v1 runs remain replayable and new runs use the selected policy"
verdict: VALIDATED
related: [004-bp4-numerics, 005-binary-numerics]
tags: [canonical, compatibility, tests]
---

# Spike 006: Canonical numerical promotion

## What This Validates

Whether a selected high-performing BP4 policy and any supported binary policy
can be promoted without changing frozen v1 evidence identities.

## Research

Phase 10 froze `quaternary-bp4-f64-v1` with global `±25` saturation. The
binary reference profile is likewise versioned. A new profile and explicit
legacy selection are required; rewriting v1 would invalidate prior ledgers.

## How to Run

Run `verify_numeric_sweep.py` for algebra and experimental/production
agreement, `verify_promoted_against_heldout.py` for full ledger replay, and
the targeted canonical tests for both v1 and v2. The numerical scale-up
report gives exact commands and profile selection examples.

## What to Expect

New versioned profile IDs, algebraic tests, old-profile regression, and
matched replay evidence.

## Investigation Trail

1. Promotion criterion: choose a policy on held-out samples, using both
   logical failure and decoding work, and preserve v1 as an explicit option.
2. BP4 v2 uses an uncapped four-state LLR state, reference-style strict tie
   ladder, direct tanh-product checks with an exact-unity safeguard, and
   old-V2C damping 0.1. Direct scalar and compiled BP4 now default to v2.
3. Public existing quaternary manifests and Q-BPGD replay explicitly select
   BP4 v1. Binary SPA v2 is selectable by profile; existing binary policy
   sessions retain v1 because their evidence identity and intervention
   schedule semantics are frozen. Tuned Q8 OMS remains separate.

## Results

The numerical profiles preserve v1 `as_evidence()` bytes and expose distinct
v2 IDs. The compiled BP4 v2 output matched the independent experimental
kernel on additional shots; all 50,000 selected held-out BP4 shots and all
7,000 selected held-out binary SPA shots matched their promoted compiled
profiles in every retained outcome and iteration count.
Focused scalar, compiled, and public-regression tests passed; the complete
verification commands and any environment-dependent exclusions are recorded
in the numerical scale-up report.
