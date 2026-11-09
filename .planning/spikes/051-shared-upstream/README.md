---
spike: 051
idea: canonical-kernel-audit
name: shared-upstream
type: standard
validates: "Given aligned native implementations, when shared execution runs, then agreement and source-specific differences are explicit."
verdict: VALIDATED
related: [043, 044, 045, 046, 049]
tags: [shared-policies, completeness]
---

# Shared policy upstream correspondence

Baseline d031436. Continues the approved mathematics → upstream → policy → execution audit. User scope: existing/source-defined counterparts only; no new cross-family adaptations. Production and historical evidence remain unchanged during this audit.

## Research and approach
Independent mathematical oracles, aligned native execution, composition probes and evidence replay answer distinct questions. Prior qualification is carried only for matching source identities. CLI evidence is appropriate to this numerical question; HTML follows the audit.

## Research
Primary sources checked: [ldpc BP API](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html), [Relay min-sum at 14cb31a](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs), [aSCED SPA at 8167720](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp), [Sionna 2.2.0 API](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html), [Stim DEM v1.15.0](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/file_format_dem_detector_error_model.md), [Sinter API v1.15.0](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/sinter_api.md).

| Approach | Strength | Limit | Use |
|---|---|---|---|
| Independent factor enumeration | Can detect shared backend defects | Small graphs, explicit finite conventions | Spike 050 |
| Installed ldpc and pinned Relay binaries | Checks real execution, memory and stopping | Must align damping, caps, priors, initial return and ties | Fresh runs here |
| aSCED source and prior extracted-function receipts | Explains named algorithm and zero-message conventions | Does not reproduce author splitter/ensemble curves | Carry existing qualification |
| Sionna interface comparison | Shows CN/VN hooks, schedules, state and numerical policies | No installed Sionna execution or learned-policy equivalence claim | Architecture comparison only |
| Stim/Sinter specifications | Defines fault and packed transport semantics | No BP correctness oracle | Spike 053 |

## Alignment and run
Seeds 5101/5102; heterogeneous rates in [.08,.45] / [.1,.45], nonzero syndromes, caps 1/3/6. SPA explicitly uses zero damping and binary min_llr decisions; min-sum uses explicit alpha and cap 25. Float64 posterior tolerance 2e-12, exact candidates and iteration counts. Run `OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/051-shared-upstream/probe.py`.

## Results
All groups pass: 972 ldpc comparisons and 216 pinned Relay inner-loop comparisons. Each retains complete channel inputs and settings; source/binary digests and numerical maxima are in results.json. Installed ldpc is 2.4.1; its build commit remains unknown. Relay commit is verified against exact source bytes. These are aligned algorithm checks, not statistical curve reproductions.

## Investigation trail
The first ldpc probe incorrectly reused STABLE_SPA_F64's Pauli hard-decision default. BinaryPolicy correctly rejected it. The probe now explicitly selects min_llr; initial results and log are preserved as a harness correction, not a production defect. Relay passed both invocations.

## Interpretation
There is no universal gold-standard implementation. Sum-product equations, min-sum approximations, numerical safeguards, stopping, randomization and quantum candidate evaluation require separate contracts. Source-specific differences (including native zero-syndrome shortcuts and aSCED zero-message behavior) remain documented rather than forced into artificial equality. The shared interface offers broad existing policy families, while compiled and GPU dispatch deliberately expose narrower subsets. No new source-free Pauli adaptations are implied.
