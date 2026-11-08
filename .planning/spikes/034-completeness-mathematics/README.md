---
spike: 034
idea: canonical-kernel-audit
name: completeness-mathematics
type: standard
validates: "Mathematical contract completeness"
verdict: VALIDATED
related: [027, 028, 029, 030, 031, 032, 033]
tags: [completeness]
---

# Mathematical contract completeness

## Investigation Trail
Continues the already approved mathematics → upstream → policy → execution order. Production baseline 4cce08e. Historical spikes 008–033 remain unchanged. This is an audit, not a behavior migration.

## Research and approach
Use independent probability enumeration as the acceptance criterion for tree marginals, following [factor-graph sum-product](https://web.stanford.edu/~montanar/TEACHING/Stat375/papers/sumprod.pdf). Native agreement alone can share errors; backend parity alone cannot establish the equations. Graph relabeling probes loopy invariance without claiming exact loopy inference.

## Results
Three groups pass: 192 four-check, nonuniform Pauli-prior tree cases (1,024 assignments each; maximum marginal error 4.44e-16); 100 graph relabeling comparisons (2.22e-16); explicit rejection of zero-mass joint priors. Prespecified absolute tolerance is 2e-12. Seeds 3401/3402, four undamped sweeps for trees and five for loopy covariance. This expands prior two-check and one-check fixtures, not the accepted zero-prior domain.

## Run and observability
`NUMBA_NUM_THREADS=4 .venv/bin/python .planning/spikes/034-completeness-mathematics/probe.py`

`results.json` retains inputs/details, source hashes, package versions, grouped verdicts and failing assertions. A zero process exit means the audit completed, not that every invariant passed. See [the consolidated report](../CANONICAL-KERNEL-COMPLETENESS-AUDIT.md) for fixes, limitations and freeze gates.
