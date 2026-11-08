---
spike: 012
idea: canonical-kernel-audit
name: v3-mathematical-audit
type: standard
validates: "Given stabilized v3, when independently checked across priors, ties and numerical boundaries, then its declared mathematics holds"
verdict: VALIDATED
related: [008-mathematical-correctness, 013-v3-upstream-audit, 014-v3-policy-audit]
tags: [mathematics, v3, quantization, exact-inference]
---

# Spike 012: V3 mathematical audit

## What This Validates

The corrected numerical contracts on bounded small graphs, including heterogeneous priors and disconnected variables. VALIDATED means the stated tests passed; it does not certify every finite-input behavior as exact SPA or freeze all policy entry points.

## Research

The minimum-LLR decision and commutation reduction are grounded in [Lai–Kuo Algorithm 1](https://arxiv.org/html/2104.00304v3#S3). The independent enumeration from spike 008 is reused unchanged, while this harness selects v3 and expands nonuniform-prior and rounding-boundary coverage.

| Approach | Strength | Limitation | Choice |
|---|---|---|---|
| Local probability enumeration and geometric damping | Independent of production LLR helpers | Exponential in local degree | Primary recurrence oracle |
| Exhaustive full-state tree posterior | Independent global answer | Only small trees; undamped convergence | Exact limiting check |
| Scalar/compiled agreement | Useful implementation differential | Shared errors can pass | Deferred to spike 015 |

Prespecified tolerances: probability/exact-tree errors <2e-12; reconstructed edge LLRs ≤2e-11 absolute; float16 quantization and MAP tie choices exact.

## How to Run

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/012-v3-mathematical-audit/probe.py
```

## What to Expect

Six passing grouped checks, including 768 recurrence sweeps, 16 exact tree cases, 216 decision equality patterns, 1,003 finite probabilities and 253,945 float16 representable/midpoint/adjacent-value cases.

## Observability

`results.json` records inputs for the safeguard characterization, tolerances implicit in the executable assertions, case counts, maximum errors, package versions, production source hashes and Git revision. Probe process success alone is not the verdict: inspect `failed`.

## Investigation Trail

1. Added a disconnected variable and heterogeneous priors to both binary and commuting-Pauli graph families. Exercised all eight syndromes on a tree and a loopy graph with damping 0/.1/.65/.95 for six sweeps.
2. Compared both posterior probabilities and complete V2C messages to a probability-domain recurrence. Damping is independently expressed as normalized geometric mixing.
3. Exhaustively marginalized the small trees after undamped propagation.
4. Compared the corrected MAP decision to `argmin(0,X,Y,Z)` over 216 equality/sign/scale patterns.
5. Included the least positive subnormal and the largest probability below one in stable-prior checks.
6. Exhausted finite float16 values, halfway boundaries and immediately adjacent float64 numbers; all match the declared finite-saturation-plus-IEEE-rounding reference.
7. Reconfirmed the already declared large-LLR approximation: one-neighbor input 38 maps to 37.43, while 40 maps to 23.72. This is not new and must not be described as globally exact or monotone SPA.

## Results

**VALIDATED within the stated domain.** Maximum posterior errors are 4.44e-16 binary and 2.22e-16 Pauli. No new mathematical defect was observed in these tests. The exact-unity numerical adaptation remains an explicit limitation and should stay visible in the interface and evidence.
