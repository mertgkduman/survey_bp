---
spike: 015
idea: canonical-kernel-audit
name: v3-execution-audit
type: comparison
verdict: PARTIAL
---

# Spike 015: Backend and evidence consistency

## Question and Approach

Does the same contract survive scalar, compiled, CPU-batch and public execution? This follows the mathematical and source checks in 012–013; implementation agreement alone is not mathematical proof.

| Method | Role | Limit |
|---|---|---|
| Seeded full-buffer differential | Current v3 and frozen v1, both mathematical families | Small graphs, moderate priors |
| Existing CPU/resolution/work/public regressions | Batch thread counts, numerical scopes, caps and replay | Shares production primitives |
| Public receipt mutation | Independently test replay trust boundary | Selected summary fields only |
| Revalidate prior benchmark artifacts | Tie CPU evidence to unchanged source and original algebra | No new timing measurement |

## Run

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/015-v3-execution-audit/probe.py
PYTHONPATH=src .venv/bin/python .planning/debug/verify_kernel_stabilization.py
```

Regression invocation is in `regression-command.txt`. Probe failures are recorded in `results.json`; inspect its `failed` field.

## Results

**PARTIAL.** The full-buffer differential passes 192 sweeps (96 current v3, 96 frozen v1), seed 110611, maximum absolute error 4.44e-16 against a 2e-11 tolerance. Existing execution regressions pass **114 tests**, including plain/explicit SPA and min-sum CPU batches, six formats, three rounding scopes, thread-mask restoration, caps, candidate decisions and public round trips.

**V3-A03 — incomplete public receipt verification.** Mutating any one of `termination`, `outcome`, `numerical_profile` or `run_fidelity` in a v4 `result.json` still returns `verified: true`. The original ledger bytes and manifest identity are unchanged and replay correctly. Altered work counts are rejected. Verification therefore establishes ledger integrity but fails to validate all authoritative-looking summary claims. Compare deterministic summary fields to replay/preflight, excluding legitimate location-dependent fields; preserve explicitly versioned historical replay.

The prior CPU evidence verifier passes source hashes and independently checks 2,048 benchmark ledger rows against the original graphs, syndrome validity and work equations. Existing benchmark results remain applicable to the identical production source; this spike makes no additional speedup claim. Quantized modes use rounded float64 storage/arithmetic boundaries, not native low-precision SIMD.

Temporary receipt fixtures are removed after probing. Counterexamples retain original/replacement fields and verification outcomes. Production source, historical spike evidence and native source checkouts were not changed.
