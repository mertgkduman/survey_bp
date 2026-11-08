---
spike: 044
idea: canonical-kernel-audit
name: new-path-upstream
type: comparison
validates: "Aligned native BP and pinned source interfaces explain new-path behavior."
verdict: VALIDATED
related: [009, 033, 035, 043]
tags: [upstream, circuit]
---

# New-path upstream correspondence

## Research and competing approaches

Native execution checks practical conventions; exact local inference (043) checks
the mathematics independently. Source/API comparison checks breadth and names but
cannot establish executable equivalence. Use all three with separate claims.

| Primary reference | Comparison and boundaries |
|---|---|
| [ldpc BP API](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html) | Execute installed ldpc 2.4.1 using heterogeneous channels, parallel scheduling and explicit syndrome interpretation; hash its binary. Docs identify themselves as 2.1.0, so do not infer build identity from their version. |
| [Relay min-sum at 14cb31a](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs) | Retain prior pinned execution evidence. Scalar alpha=0 has source-specific iteration-scaling meaning; source memory can change priors every iteration. Circuit Relay is a declared adaptation, not the full source procedure. |
| [aSCED SPA at 8167720](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp) | Retain source-qualified zero-message differences and prior extracted-function checks. Full author ensemble/splitter reproduction remains a separate research question. |
| [Stim DEM at v1.15.0](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/file_format_dem_detector_error_model.md) | Verify independent mechanisms, correlated targets, deterministic affine offsets and undetected logical mechanisms. A separator does not create independent faults. |
| [Sinter API at v1.15.0](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/sinter_api.md) | Check little-endian packed detector/observable shapes and task identities; policy names/metadata must distinguish changed configurations when resuming. |
| [Sionna 2.2.0](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html) | Interface-only comparison: explicit update/callback/schedule/state controls. No Sionna execution or learned-policy equivalence is claimed. |

The attempted ldpc Git tag v2.4.1 does not exist at the queried repository URL.
Record installed binary provenance rather than inventing a source commit.

## Prespecified alignment

Seed 4401; twelve heterogeneous channels in [.03,.45], three nonzero syndromes.
MS/NMS: alpha 1/.8/.55, caps 1/3/6. SPA: first sweep only, because the new
circuit SPA has intrinsic 0.1 damping and native ldpc here is undamped.
No active saturation or exact ties; atol=rtol=2e-12 for posterior state.

## Run

`OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/044-new-path-upstream/probe.py`

Results and native binary identities are retained; no production behavior changes.

## Results and investigation trail

Both groups pass: 360 aligned native comparisons reproduce candidates, iteration
counts and convergence exactly; maximum posterior discrepancy is 1.78e-15.
Four independent affine projection cases also verify multi-byte Sinter output,
zero padding and MAP treatment of an unobserved logical mechanism.

The evidence supports the stated aligned subset. Multi-sweep damped SPA, complete
Relay/aSCED author pipelines and differentiable Sionna execution were not compared
as equivalent decoders. The lack of a matching ldpc tag was handled by hashing the
actual loaded binary and retaining its installed version, with build commit unknown.
