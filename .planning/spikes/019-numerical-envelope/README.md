---
spike: 019
idea: canonical-kernel-audit
name: numerical-envelope
type: standard
validates: "Given finite check inputs across degree and scale, then numerical adaptations and exact-SPA error are quantified"
verdict: PARTIAL
related: [012-v3-mathematical-audit, 020-upstream-envelope]
tags: [numerics, exact-inference, boundary]
---

# Spike 019: Expanded numerical envelope

## Research and approach

Reused prior source-equation work. [Sionna documents a numerically stable phi-domain check update](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.cn_update_phi.html). This is design corroboration, not an executed Sionna oracle.

| Approach | Choice | Reason |
|---|---|---|
| 600-digit Decimal parity-state partition | Independent oracle | Enumerates even/odd probability masses without production tanh or box-plus |
| Existing stable log-domain primitive | Comparison candidate | Already present but not a qualified compiled default |
| Backend agreement only | Insufficient | Can reproduce the same approximation |

## Run

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/019-numerical-envelope/probe.py
```

## Investigation and results

100 cases span 1/2/4/16/64 incoming neighbors, magnitudes 1e-12 through 1000, and positive/negative parity signs. Prespecified absolute tolerance is 2e-11; Decimal precision is 600 digits. The binary and Pauli stable box-plus primitives pass all cases. Four zero/near-zero cases pass.

The default tanh/exact-unity rule exceeds that exact-SPA tolerance in **60/100** cases. The maximum absolute error is 976.281. These are deliberately extreme inputs, not a sampling distribution or error-rate estimate. This expands the already known limitation; it is not a new arithmetic regression.

A three-variable, one-check tree with syndrome 1 and prior LLR 40 has exact posterior LLR about 0.693 per variable. Current compiled v3 gives about 16.281. Thus the safeguard can materially distort posterior confidence even on a tree. Stable box-plus agreement is component-level evidence; it does not qualify a complete replacement default or its CPU performance.

**PARTIAL:** declared finite behavior is reproducible, but a global exact-SPA claim fails. Decide whether the intended default is exact stable SPA or an explicitly approximate source-compatible rule before freezing. Preserve v3 evidence; any numerical default change needs a new version and full scalar/compiled/policy qualification.

`results.json` retains all inputs, oracle values, errors, tree counterexample, source hashes and environment. The diagnostic process writes evidence even when an invariant fails. No production changes.
