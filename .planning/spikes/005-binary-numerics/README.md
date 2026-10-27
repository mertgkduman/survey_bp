---
spike: 005
idea: pfister-slide-bp-reproduction
name: binary-numerical-scale-up
type: comparison
validates: "Given the same CSS errors, when binary SPA uses global clipping, check-only clipping, or uncapped stable box-plus, then block LER and work differences are measurable"
verdict: VALIDATED
related: [003-paired-reproduction, 004-bp4-numerics, 006-canonical-promotion]
tags: [binary, numerics, simulation]
---

# Spike 005: Binary numerical scale-up

## What This Validates

Whether the BP4 numerical improvement generalizes to the separate X/Z binary
SPA kernel, and whether changing its canonical default is justified.

## Research

`src/bp_registry/canonical/compiled.py` and `numerics.py` use the same global
`±25` clipping pattern for binary SPA. The existing tuned binary OMS adapter
is a different check rule and remains a separate baseline. Stable box-plus
and tanh-product variants need no new dependency.

## How to Run

Use `run_scaled_numeric_sweep.py` with
`results/numerical_scaleup/binary_screen.json` or `binary_heldout.json`.
The configs, seeds, counts, and SHA-256 checked event ledgers are in each
output directory. `analyze_numeric_scaleup.py` verifies pairing and derives
the exact intervals and paired comparisons.

## What to Expect

Paired block outcomes, exact/stabilizer success counts, Type I/II failures,
iteration distributions, and per-code uncertainty.

## Investigation Trail

1. Freeze physical depolarizing p and binary marginal prior 2p/3; decode
   X and Z separately on the same sampled four-Pauli errors.
2. Screen B1 `p=.10`, N=200 and double-Gross `p=.08`, N=1,000; hold out
   new seeds at N=2,000 and N=5,000 respectively. Compare direct-product
   SPA, capped/uncapped box-plus, frozen SPA v1, and tuned Q8 OMS.

## Results

Float64 SPA v2 product with old-V2C damping 0.1 beat frozen SPA v1:
B1 94/2,000 versus 158/2,000 failures, and double-Gross 221/5,000 versus
262/5,000. The paired rescue/loss counts were 71/7 and 50/9. Truly
uncapped box-plus with damping was similar to product SPA on these binary
holdouts. Tuned Q8 OMS remained stronger on double-Gross (158/5,000) and
was unresolved against SPA v2 on B1 (91/2,000). The v2 SPA profile is
available explicitly; public v1 sessions remain pinned to their frozen
numerical contract. See the numerical scale-up report for complete data.
