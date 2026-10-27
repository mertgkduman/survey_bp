---
spike: 007
idea: pfister-slide-bp-reproduction
name: full-v2-curve-sweep
type: comparison
validates: "Given the promoted v2 canonical BP4 and binary SPA kernels, when every B1 and double-Gross presentation probability is run on paired depolarizing errors, then local rates, uncertainty, and policy mismatches can be assessed point by point"
verdict: IN_PROGRESS
related: [001-slide-evidence, 003-paired-reproduction, 006-canonical-promotion]
tags: [canonical, reproduction, simulation]
---

# Spike 007: Full v2 curve sweep

## Scope

Run every distinct physical depolarizing probability in the supplied B1 and
double-Gross plots. Use the promoted compiled BP4 v2 and binary SPA v2 kernels,
and retain source-policy Q8 min-sum/OMS controls where appropriate. Samples at
each code/probability are shared across arms. Store per-shot ledgers, exact
denominators, uncertainty intervals, and comparative plots under
`from_dr_pfister_presentetations/results/full_v2_curves/`.

## Status

Experiment design and execution in progress. The source Q8 and min-sum curves
must be identified separately from float64 v2 adaptations.
