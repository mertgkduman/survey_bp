---
spike: 027
idea: canonical-kernel-audit
name: stable-spa-stress-audit
type: standard
validates: "Given the corrected kernel, when boundaries are exercised, then independent multi-check inference, mixed-scale messages and finite-state failure boundaries"
verdict: PARTIAL
related: [023, 024, 025, 026]
tags: [freeze-audit, boundaries]
---

# Stable SPA stress audit

## Research
Reuse the independent equations, pinned upstream identities and qualified contracts in spikes 019–026. Numerical and implementation agreement are tested separately.

## Investigation Trail
Baseline 12cf2b1, production be7286e. No production changes.

## Results
Three grouped mathematical checks pass: 32 exact two-check tree cases across binary/Pauli inference, 120 mixed-scale checks with 360 independent parity comparisons and 120 edge permutations, and three Pauli-label permutations. Marginal tolerance is 2e-12; parity tolerance is 2e-11.

C01: finite inputs of magnitude 1e308 produce nonfinite BP4 beliefs, V2C and marginals under float64 `scalar_edges` resolution. `all_messages` and `all_state` reject the same overflow. This is a missing finite-state guard, not a failure of the ordinary-range parity equation. It affects an admitted composition and prevents an unconditional finite-state guarantee. Recommended fix: detect nonfinite state before returning/committing it, shared by sweep, decode and batch paths.

## Run
`OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/027-stable-spa-stress-audit/probe.py`

## Investigation Trail
Expanded from single-check cases to independent full joint inference on a tree with two checks. Mixed magnitudes and edge permutations passed. An overflow sensitivity probe then isolated the missing guard to scalar-only resolution; the other two scopes fail closed.
