---
spike: 011
idea: canonical-kernel-audit
name: execution-consistency
type: comparison
validates: "Given identical profiles and observations, when public, scalar, and compiled paths run, then behavior and evidence agree"
verdict: PARTIAL
related: [006-canonical-promotion, 008-mathematical-correctness, 010-policy-extensibility]
tags: [backends, replay, accounting, stopping]
---

# Spike 011: Execution consistency

## What This Validates

Behavioral agreement at complete message buffers, initial/final candidate boundaries, budget exhaustion, and durable public evidence. Tests distinguish matching replay from independently correct evidence.

## Research

The independent mathematical and upstream references are recorded in spikes 008 and 009. This spike compares implementations of the project's own contracts; no additional numerical library is required.

| Approach | Strength | Limitation | Use |
|---|---|---|---|
| Randomized matched buffers | Isolates recurrence/backend differences | Identical defects can pass | 192 sweeps, fixed seed |
| Boundary counterexamples | Exercises prior initialization and denied work | Small fixtures, no incidence estimate | Both v1 and v2 |
| Public run plus replay plus independent work expectation | Finds self-consistent wrong evidence | Replay alone cannot establish correctness | Two retained counterexample bundles |
| Frozen regression fixtures | Protect legacy behavior and source identities | Existing expectations may preserve a defect | 160 existing tests |

## How to Run

```sh
OMP_NUM_THREADS=1 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/011-execution-consistency/probe.py
```

`regression.xml` records the exact selected pytest identities. They cover budgets/work, truth boundaries/traces, restart, compiled binary/paper-BPGD/BP4/Q-BPGD, resolution, versioned defaults, guided decimation, impulse, grouped schedules, MBBP, fair Relay/Beam legs, and quaternary kernel checks.

## What to Expect

18 grouped diagnostics: 6 pass and 12 identify differences or defects. These are repeated manifestations of several root causes, not twelve independent bugs. Existing regression selection: **160 passed in 15.62 s**.

## Observability

`results.json` retains exact arrays, priors, graph matrices, profile names, counters, numerical deltas, source hashes, and environment versions. The `quaternary_experiment_v2-budget-counterexample/` and `quaternary_experiment_v3-budget-counterexample/` directories preserve the actual input, normalized manifest, event ledger, and result. Their run IDs are deterministic diagnostic fixture IDs, not publication samples.

Each bundle retains the original temporary-path receipt as `original-result.json`. In `result.json`, only filesystem location metadata is relocated to the retained bundle; manifest and ledger bytes/hashes are unchanged. The probe verifies both the original run and the retained bundle. Rerunning `probe.py` refreshes the paths for the current checkout.

## Investigation Trail

1. Compared 192 complete scalar/compiled sweeps across twelve random small graphs, both numerical versions, and both binary/Pauli families. Matched C2V, V2C, beliefs and Pauli marginals within 2e-11; maximum observed absolute error was 4.44e-16. This checks buffers, not an assertion of all terminal control-flow equivalence.
2. Tested admitted binary `p=.8` with cap zero and with an edgeless graph. Scalar initialization selects `[1,1,1]`; both compiled profiles return `[0,0,0]`. The compiled path initializes candidates to zeros instead of hard-deciding the prior. Both prior range and zero-iteration cap are accepted APIs.
3. Tested BP4 priors `[.1,.6,.2,.1]` on an XX check. Scalar v1 immediately returns `[X,X]`, while compiled v1 immediately returns `[I,I]` for the same zero syndrome, even with a positive iteration cap. At cap zero, v2 also disagrees in both candidate and convergence flag. Candidate validity and termination reason need separate, explicit initial/final boundary semantics.
4. Allowed exactly one BP call, committed a sweep, then requested another. The budget tree retains `bp_calls=1`, but the capped QBP snapshot replaces its cumulative work with an all-zero vector. Both frozen v1 and v2 reproduce this; messages themselves remain unchanged after denial. Similar zero-work terminal construction exists in transformed and serial paths and merits the same fix; only the plain session was directly probed here.
5. Reproduced the lost-work defect through both public quaternary schema v2 (numerical v1) and schema v3 (numerical v2). Both ledgers record zero work after one executed sweep. Both pass `verify_quaternary_run`. Deterministic replay reproduces the bug and therefore cannot be the sole work-accounting oracle.
6. Compared plain compiled v2 SPA to an explicit float64 SPA flooding policy, matching damping and disabling the shortcut. For one excluded neighbor at LLR 30, plain v2 returns 29.99983 while the policy path returns 23.71900. The plain path safeguards exact unity; the policy path clips all products beyond `1-1e-10`. The policy has a separate version identity, so this is an unexposed numerical-contract difference, not a claim that its arithmetic violates its current code. Selecting float64/sum-product does not mean selecting the canonical v2 recurrence.
7. Ran 160 regression tests; all passed, including frozen-profile and public replay fixtures. The counterexamples expose missing boundary/invariant coverage rather than a general regression-suite failure.

## Results

**PARTIAL.** Ordinary message calculations match across the tested backends. Initial candidates, zero-budget terminal facts, and public capped work evidence do not consistently satisfy the shared contract. A second SPA stabilization path is hidden inside the composable numerical-policy implementation.

Correct the work-snapshot and independent-ledger validation first. Specify initial candidate, initial syndrome check, final candidate validity, termination reason, and counter scope as distinct fields. Share those decisions across scalar and compiled entry points. Keep historical profiles/receipts reproducible and make any changed decoding behavior or corrected evidence interpretation explicit and versioned.
