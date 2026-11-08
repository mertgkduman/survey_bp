---
spike: 036
idea: canonical-kernel-audit
name: completeness-policies
type: standard
validates: "Policy composition and capability coverage"
verdict: PARTIAL
related: [027, 028, 029, 030, 031, 032, 033]
tags: [completeness]
---

# Policy composition and capability coverage

## Investigation Trail
Continues the already approved mathematics → upstream → policy → execution order. Production baseline 4cce08e. Historical spikes 008–033 remain unchanged. This is an audit, not a behavior migration.

## Research and approach
Inspect accepting entry points, inject source-iteration-dependent NMS/OMS rules, then compare the context at actual update calls. Compare reported posterior state with the state used to construct the candidate. Add a separately labeled single/batch configuration grid and static source inventory; neither substitutes for an independent numerical oracle.

## Results
Four passing controls and ten failed invariants identify **D01** (eight context failures) and **D02** (two serial posterior discrepancies). Explicit flooding and atomic flooding advance source iteration correctly; standalone and local paths do not. The report scopes posterior impact to actual consumers rather than claiming every public candidate is wrong.

The separate grid passes all **432 configurations**, emitting 2,592 shot events. All six formats, all three scopes, both coefficient modes, two damping values and SPA/NMS/OMS are represented for binary and Pauli flooding. It establishes dispatch/backend agreement on this fixture, not arbitrary controller compatibility. The first grid harness omitted the explicit binary min-sum rule; the factory correctly rejected the conflicting default. `initial-grid-results.json` retains this harness error; after correcting the call, all intended configurations execute.

[CAPABILITIES.md](CAPABILITIES.md) maps the existing policy families and exclusions. `source-inventory.json` inventories 113 production modules; 97 have direct test imports. This is not runtime or branch coverage.

## Run and observability
`NUMBA_NUM_THREADS=4 .venv/bin/python .planning/spikes/036-completeness-policies/probe.py`

`results.json` retains inputs/details, source hashes, package versions, grouped verdicts and failing assertions. A zero process exit means the audit completed, not that every invariant passed. See [the consolidated report](../CANONICAL-KERNEL-COMPLETENESS-AUDIT.md) for fixes, limitations and freeze gates.
