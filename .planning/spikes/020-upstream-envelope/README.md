---
spike: 020
idea: canonical-kernel-audit
name: upstream-envelope
type: comparison
validates: "Given aligned boundary inputs, native and canonical numerical behavior is explained against an independent oracle"
verdict: VALIDATED
related: [013-v3-upstream-audit, 019-numerical-envelope, 021-policy-entry-closure]
tags: [upstream, numerics, boundaries]
---

# Spike 020: Upstream numerical envelope

## Research and choice

Compare actual installed ldpc 2.4.1, unchanged extracted pinned aSCED C++, and isolated pinned Relay inner BP. Retain binary/source hashes and scope from spike 013. [ldpc BP documentation](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html), [aSCED SPA source at 8167720](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp), and [Relay at 14cb31a](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs) establish implementation scope.

| Approach | Choice |
|---|---|
| Native execution against independently computed expected behavior | Primary |
| Treat any upstream result as automatically correct | Rejected |
| Sionna phi-domain implementation as additional design reference | Documentation only; PyTorch is not installed |

## Run

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/020-upstream-envelope/probe.py
```

## Results

All four grouped correspondence/classification checks pass. Nine aligned ldpc SPA cases span prior LLR .1–500. At LLR 40, 100 and 500, installed ldpc returns negative-infinite posteriors. Canonical outputs stay finite but differ from exact SPA as quantified by 019. This is not a claim that either is globally exact. ldpc build identity is a binary hash, not an established source commit.

Ten explicit policy-v2 min-sum/normalized-min-sum cases through LLR 500 agree with native ldpc and the independent linear result within 2e-11. Five extracted aSCED check-update cases reconfirm zero/zero NaNs in its total-product division; canonical exclusion stays finite. 189 pinned Relay min-sum/affine-memory inner-BP cases retain their correspondence.

[Sionna's phi-domain reference](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.cn_update_phi.html) supports considering a stable log-domain default. Sionna was not executed or installed. Native agreement does not replace exact inference, specify a universal saturation convention, or qualify full aSCED/Relay control flow.

`results.json` retains native nonfinite outputs as strings, precise alignment, oracle values, pinned identities and production hashes. No production behavior changes.
