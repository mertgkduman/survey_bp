---
spike: 016
idea: canonical-kernel-audit
name: scalar-admission-fix
type: standard
validates: "Given a min-sum profile without an update rule, when constructed, then both backends reject ambiguous execution"
verdict: VALIDATED
related: [014-v3-policy-audit, 017-profile-evidence-fix]
tags: [fix, admission, scalar, compiled]
---

# Spike 016: Scalar admission fix

## Research and choice

Pure constructor logic; reused the V3-A01 executable counterexample and compiled API contract. No external dependency or mathematical change.

| Approach | Consequence | Decision |
|---|---|---|
| Infer min-sum from a supplied profile | Silently switches a class advertised as SPA | Rejected |
| Require an explicit min-sum update | Matches explicit compiled rule selection | Chosen |

## Investigation and results

The regression initially failed twice: both the default min-sum profile and a changed saturation were accepted as scalar SPA. Scalar admission now rejects both. Compiled admission uses the semantic min-sum marker rather than equality with one default object, closing the saturation variant too. Explicit min-sum still produces 1 for incoming `[1,2]`, while default SPA retains its original equation. Validation happens at graph/kernel construction, outside hot loops.

Red: 2 failed, 1 passed. Green: **76 passed**, including existing stabilization/CPU tests. Arithmetic, profile identities and historical result data were not modified.

## Run and observability

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 .venv/bin/python -m pytest -q tests/canonical/test_kernel_contract_admission.py tests/canonical/test_kernel_stabilization.py
```

`red.log`, `green.log` and `green.xml` retain the before/after evidence. Later fixes add cases to the same regression file, so rerun counts may increase.
