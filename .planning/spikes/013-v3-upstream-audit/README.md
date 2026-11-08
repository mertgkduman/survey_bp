---
spike: 013
idea: canonical-kernel-audit
name: v3-upstream-audit
type: comparison
verdict: VALIDATED
---

# Spike 013: Pinned upstream comparisons

## What This Validates

Explained numerical agreement and intentional differences, not complete decoder or published-curve reproduction.

## Research and Approach

Primary sources: [ldpc BP documentation](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html), [Relay min-sum at 14cb31a](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs), and [aSCED BP4 at 8167720](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP4_Decoder.cpp).

| Approach | Decision | Scope |
|---|---|---|
| Execute installed native ldpc and isolated pinned Relay | Use | Complete inner BP with aligned settings |
| Compile unchanged extracted aSCED functions | Use | Projection, decision and check-update primitives only |
| Treat source agreement as a mathematical oracle | Reject | Source code can contain numerical and decision defects |

The installed ldpc is 2.4.1, recorded by module hash; its exact build commit is not established. Documentation version is separate. Relay and aSCED commits and source hashes are recorded. Native Relay comparisons cover the frozen min-sum/affine-memory contract, not a new v3 Relay profile.

## Run

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/013-v3-upstream-audit/probe.py
```

Requires the existing pinned source/package directories documented in spike 009 and a C++17 compiler. No installation is performed.

## Results and Investigation Trail

All five grouped checks passed. 180 native ldpc comparisons (SPA v3 with damping zero and frozen min-sum) reached maximum posterior error 1.78e-15. Another 84 normalized-min-sum policy-v2 comparisons reached 8.88e-16. Candidate disagreements were confined to zero or roundoff-scale beliefs under the prespecified 2e-11 threshold. 189 pinned Relay inner-BP comparisons passed.

The 29 extracted aSCED projection/decision cases reproduce the source. V3 intentionally differs in 12 of 27 decision patterns; three source decisions are not MAP. Five extracted check-update cases show that source total-product division generates NaNs at zero messages, while canonical exclusion stays finite. These are documented differences, not targets to imitate.

`results.json` retains counterexamples, case counts, environment, source/binary/function hashes and production hashes. Scope excludes complete aSCED execution, full Relay control flow, statistical reproduction and hardware speed claims. Verdict VALIDATED applies only to the stated correspondences.
