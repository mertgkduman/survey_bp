---
spike: 035
idea: canonical-kernel-audit
name: completeness-upstream
type: standard
validates: "Upstream interface and algorithm comparison"
verdict: VALIDATED
related: [027, 028, 029, 030, 031, 032, 033]
tags: [completeness]
---

# Upstream interface and algorithm comparison

## Investigation Trail
Continues the already approved mathematics → upstream → policy → execution order. Production baseline 4cce08e. Historical spikes 008–033 remain unchanged. This is an audit, not a behavior migration.

## Research and approach
See [SOURCES.md](SOURCES.md) for primary references, alignment, competing validation approaches and unexecuted comparisons. Installed native `ldpc` is an executable reference; its binary is hashed, while its build commit is unknown. Sionna 2.2.0 is an interface comparison only. Existing pinned Relay/aSCED receipts remain unchanged.

## Results
216 heterogeneous-prior SPA/min-sum circuit cases match native candidates, convergence flags and actual iteration counts. Twelve seeded channels, two rules, three caps, three nonzero syndromes. The fixture avoids active finite saturation and exact ties; zero-syndrome initialization differences are not hidden under a parity claim. This does not establish the whole Sinter/circuit publication pipeline or unknown native controller behavior.

## Run and observability
`NUMBA_NUM_THREADS=4 .venv/bin/python .planning/spikes/035-completeness-upstream/probe.py`

`results.json` retains inputs/details, source hashes, package versions, grouped verdicts and failing assertions. A zero process exit means the audit completed, not that every invariant passed. See [the consolidated report](../CANONICAL-KERNEL-COMPLETENESS-AUDIT.md) for fixes, limitations and freeze gates.
