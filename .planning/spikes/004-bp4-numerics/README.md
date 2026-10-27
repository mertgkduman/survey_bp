---
spike: 004
idea: pfister-slide-bp-reproduction
name: bp4-numerical-scale-up
type: comparison
validates: "Given held-out B1 and double-Gross errors, when check caps and damping are varied without global clipping, then LER and work can be compared against the supplied curves"
verdict: VALIDATED
related: [002-policy-kernel, 003-paired-reproduction, 005-binary-numerics, 006-canonical-promotion]
tags: [bp4, numerics, simulation]
---

# Spike 004: BP4 numerical scale-up

## What This Validates

Whether the reference-style gain persists on new seeds and multiple physical
error rates, and whether a finite check cap or no artificial check cap wins.

## Research

The supplied reference contract and the completed matched numerical audit
(`from_dr_pfister_presentetations/results/performance_investigation/REFERENCE_GAP_AUDIT.md`)
show that global `±25` clipping causes large local nonconvergence. Stable
log-domain box-plus permits a check update without an arbitrary finite cap on
degree-six graphs. Direct tanh-product SPA requires a product safeguard at
unity. No new external dependency is needed.

## How to Run

Run the saved screen and held-out configurations with
`PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python
from_dr_pfister_presentetations/run_scaled_numeric_sweep.py`, passing
`--code`, `--p`, `--shots`, `--seed`, `--configs`, and `--output`. The exact
arguments are recorded in each `summary.json` under
`from_dr_pfister_presentetations/results/numerical_scaleup/`; the selected
policy is in `decoders/canonical_bp4_f64_v2.json`. Rebuild tables and figure
with `analyze_numeric_scaleup.py` and check the numerical recurrence with
`verify_numeric_sweep.py`.

## What to Expect

Paired per-shot ledgers, exact intervals, work distributions, and a source
curve comparison. Each summary holds the ledger SHA-256 and all decoder knobs.

## Investigation Trail

1. Prespecified screen variants: direct tanh product with exact-unity product
   safeguard, log-domain box-plus with check cap 25 or 50 or no cap, and
   selected V2C damping values. All retain uncapped posterior/V2C and the
   reference tie ladder.
2. Screen seeds were 20261101 (B1, `p=.10`, N=200) and 20261031
   (double-Gross, `p=.08`, N=1000). Holdout seeds 20261102 and 20261103
   were selected before decoding their shots. Additional B1 `p=.12` and
   double-Gross `p=.10` points used independent seeds 20261106 and 20261105.
3. The exact-unity safeguard matters: an initial production implementation
   clamped all products close to one and diverged from the experimental
   recurrence. It was corrected and then checked against matched shots.

## Results

The selected product-check BP4 with old-V2C damping 0.1 had 8/20,000
failures on B1 `p=.10` (mean work 12.08) and 15/20,000 on double-Gross
`p=.08` (mean work 6.86), near the supplied slide points 0.00032 and
0.00077. On double-Gross `p=.10`, it had 75/5,000 (slide 0.01505). B1
`p=.12` had 35/5,000, below the slide point 0.0112, so full curve
reproduction remains unresolved. Truly uncapped box-plus was worse than the
selected product rule on both 20,000-shot holdouts. On B1 `p=.10`, damping
reduced product-check failures 19→8, mean work 31.89→12.08, and p99 work
259→48 on the same 20,000 shots. A separate toric control
at `p=.075`, decoder `p0=.10`, `T=25` had 1,489/10,000 failures versus
1,560/10,000 for frozen BP4 v1. Full counts, Type I/II, intervals, and
paired tests are in
`from_dr_pfister_presentetations/results/numerical_scaleup/NUMERIC_SCALEUP_REPORT.md`.
