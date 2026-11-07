---
spike: 008
idea: canonical-kernel-audit
name: mathematical-correctness
type: standard
validates: "Given small binary and Pauli graphs, when independently evaluated, then messages and decisions satisfy their mathematical contract"
verdict: PARTIAL
related: [004-bp4-numerics, 005-binary-numerics, 006-canonical-promotion, 009-open-source-cross-check]
tags: [mathematics, numerics, independent-oracle]
---

# Spike 008: Mathematical and numerical correctness

## What This Validates

Audit message recurrences separately from hard decisions and numerical approximations. A correct sum-product marginal does not imply a correct candidate, and agreement between two implementations sharing code is insufficient.

## Research

Primary mathematical references: [Kschischang, Frey, Loeliger (2001)](https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf), and [Lai and Kuo, log-domain quantum BP, v3](https://arxiv.org/html/2104.00304v3). Use local factor enumeration for excluded-neighbor messages and exhaustive whole-graph enumeration for tree marginals. Scalar commutation messages preserve four-state inference; X/Z independence is not assumed.

| Approach | Advantage | Limitation | Use |
|---|---|---|---|
| Exact whole-graph probability enumeration | Independent algebraic oracle | Exponential; loopy BP need not equal exact marginals | Five-variable trees |
| Local probability-vector message enumeration | Checks each recurrence on trees and loops | Must independently specify schedule | Four/small-five-variable graphs |
| Existing scalar/compiled differential tests | Efficient regression coverage | Can share a defect | Reserved for spike 011 |

Moderate positive priors avoid intentional saturation. Tolerance was fixed at absolute 2e-12 before running. Damping is checked independently by geometric mixing of normalized probability vectors, equivalent to linear mixing in log odds. The independent commutation truth table does not call production Pauli algebra.

## How to Run

```sh
OMP_NUM_THREADS=1 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/008-mathematical-correctness/probe.py
```

## What to Expect

16 grouped checks, 11 passing and 5 finding-bearing checks. Process success means the audit executed; inspect `failed` and individual events in `results.json`. These are diagnostic checks, not a green CI claim.

## Observability

`results.json` records fixed seeds, counts, actual values, counterexamples, environment versions, repository HEAD, UTC time, and SHA-256 for every production Python source. All inputs are deterministic fixtures; no Monte Carlo publication campaign is performed.

## Investigation Trail

1. Reused prior spikes' frozen-profile history, but built new probability-domain oracles.
2. Initial fixture lineage IDs violated the constructor's original-prefix requirement; corrected the harness before interpreting any kernel result.
3. All 192 binary and 192 Pauli recurrence sweeps passed, including all eight syndromes on each graph and both frozen v1 and undamped v2. Tree terminal marginals agreed with exact enumeration. Maximum recurrence errors were 3.33e-16 and 2.22e-16 respectively.
4. 48 independent damping sweeps passed for weights 0, 0.1, 0.5, and 0.95.
5. Enumerated 54 hard decisions across a three-value LLR grid and both profiles. Three v2 cases select a nonmaximal posterior state. For X/Y/Z LLRs `[-2,0,-2]`, X and Z are most probable, but v2 selects Y. This is more than a preference among tied maxima. Existing `test_kernel.py` explicitly expects the analogous `[-1,0,-1] -> Y` behavior.
6. Both v2 binary prior helpers reject the smallest positive float64 prior although its log odds is finite (~744.44). The single-ratio intermediate overflows; subtraction of logs is finite. At 1e-300 both pass.
7. Both v2 check primitives exhibit the same nonmonotonic unity safeguard: a one-neighbor input 38 yields 37.42995, whereas 40 yields 23.71900. This is a declared numerical-policy tradeoff, not evidence of an incorrect implementation of that profile. Degree-one output is finite and a zero incoming message correctly erases check information.

## Results

**PARTIAL.** The tested moderate-domain binary and scalar BP4 message recurrences and damping are independently validated. The current v2 hard decision cannot be called a maximum-posterior rule. Tiny positive binary priors expose an avoidable finite-domain failure. The check safeguard should remain explicitly identified as a numerical adaptation, with its discontinuity included in the stabilization contract.

Carry the exact counterexamples into upstream and backend checks. Preserve v1/v2 evidence identities; a corrected candidate rule requires an explicitly versioned migration. This spike does not establish published-curve reproduction or correctness on all graph sizes and all policy combinations.
