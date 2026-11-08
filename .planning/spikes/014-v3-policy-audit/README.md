---
spike: 014
idea: canonical-kernel-audit
name: v3-policy-audit
type: standard
verdict: PARTIAL
---

# Spike 014: Policy composition and admission

## Question and Research

Can a policy author trust both accepted composition behavior and its declared numerical evidence?

[Sionna's documented extension surface](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html) separates check/variable updates, schedules, callbacks, precision and optional returned state. It is an architectural comparison, not an executed numerical reference. Our corresponding extension points are update rules, schedules, ordered transforms, stateful memory/interventions and explicit resolution policies. Public admission is intentionally narrower than low-level extension APIs.

| Approach | Benefit | Choice |
|---|---|---|
| Identity, order and state-isolation metamorphisms | Detect seam errors without imitating implementation | Primary |
| Constructor/evidence counterexamples | Test what downstream policy authors can actually request | Primary |
| Existing policy regressions | Cover established memory, schedules and MBP4 behavior | Complement; not a fresh independent oracle |

## Run and Observability

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/014-v3-policy-audit/probe.py
```

The probe records failed assertions as findings; process success does not imply qualification. `results.json` contains full declared profiles and actual outputs. Regression command and output are retained separately.

## Findings

**PARTIAL: two new low-level contract gaps.**

- **V3-A01 — scalar rule/profile admission.** `BinarySpaKernel(profile=MIN_SUM_CPU_F64)` accepts a min-sum identity but runs SPA. Incoming `[1,2]` yields about 0.735 instead of 1. The compiled constructor rejects the same pairing. Explicit `MinSumUpdate()` is correct. Default v3 and public literal profiles are not implicated by this example.
- **V3-A02 — descriptive metadata can contradict execution.** Accepted custom profiles can claim float32 and exact-zero decision 1 while executing float64 and decision 0. A custom Pauli tie label is likewise ignored. Freeze or validate fixed semantic fields; route supported variations through implemented policy parameters. This is a scientific evidence/API integrity issue, not proof that default arithmetic is wrong.

The composition check passed: neutral normalization preserves 16 paired results across four damping settings; serial damping and transform order are observable; independent sessions do not share state; original checks are read-only; three incompatible compositions fail admission. Some repeated results can be terminal snapshots: these are lifecycle checks, not a claim of 16 newly committed sweeps.

Existing tests cover additional named memory and MBP4 policies. Neither this spike nor those tests certify arbitrary combinations, all quantized schedule/intervention combinations, or circuit-level kernels. CPU batch admission remains limited to qualified flooding configurations.

Regression result: **49 passed**. These tests do not assert the two newly discovered admission counterexamples.
