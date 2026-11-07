---
spike: 009
idea: canonical-kernel-audit
name: open-source-cross-check
type: comparison
validates: "Given pinned upstream implementations and aligned settings, when matched inputs run, then agreement or discrepancies are explained"
verdict: PARTIAL
related: [008-mathematical-correctness, 010-policy-extensibility]
tags: [upstream, native, provenance]
---

# Spike 009: Open-source cross-check

## What This Validates

Cross-check the mathematical kernel and selected policy mechanisms against independent upstream implementations. Upstream agreement is evidence of implementation correspondence, not an exemption from the mathematical oracle.

## Research

| Reference | Pin and primary source | Experiment | Limitation |
|---|---|---|---|
| quantumgizmos/ldpc | Installed release 2.4.1 and compiled module SHA-256 in results; [official API](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html) | Native SPA/min-sum posteriors and decisions | A matching Git tag was unavailable; do not claim a proven source-commit-to-wheel build chain |
| trmue/relay | `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`, [min_sum.rs](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs) | Native F64 min-sum, affine prior memory | Inner BP mechanism; full relay restart equivalence remains outside this probe |
| kit-cel/quantum_asced | `816772071486615dfc7d71d1e15df597edc58a26`, [BP4_Decoder.cpp](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP4_Decoder.cpp) | Compile unchanged projection and decision functions in a minimal C++ host | Extracted-function execution, not full aSCED matched-shot decoding |

Existing isolated native packages avoid dependency changes and avoid accidentally importing the installed non-author Relay fork. Source checkout bytes are checked against their pinned Git objects, and aSCED additionally against the established project source digest. Native binary hashes are recorded; this audit does not rebuild or independently attest the old Relay binary's compiler chain.

The alternative of treating all native defaults as equivalent is rejected: damping, tie rules, clipping, schedule, syndrome-versus-received input, and stopping differ. Align these explicitly. The default canonical v2 SPA has damping 0.1; the native comparison therefore selects damping 0, identified in results.

## How to Run

```sh
OMP_NUM_THREADS=1 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/009-open-source-cross-check/probe.py
```

Requires the already qualified local checkouts/packages identified at the top of `probe.py`. Missing or mismatched sources produce a failed diagnostic, never a substitute implementation. The aSCED host is built in an automatically removed temporary directory.

## What to Expect

Three passing grouped correspondence checks. These include explained differences, so the overall scientific verdict remains PARTIAL. `results.json` preserves exact cases, hashes, identities, and limitations.

## Investigation Trail

1. Retrieved official upstream source through the GitHub connector and inspected the pinned local checkouts. Release tag lookups `v2.4.1` and `2.4.1` for ldpc failed; retained the installed distribution identity plus binary hashes instead of inventing a Git pin.
2. Ran 180 native ldpc comparisons: two graphs, three priors, SPA/min-sum, all nonzero syndromes, and iteration caps 1/2/5. Compared posteriors at the actual native terminal iteration. Maximum absolute posterior difference was 1.78e-15, below the prespecified 2e-11 tolerance. Fifty-eight decision discrepancies occur only at zero or numerically near-zero beliefs: native chooses one at zero, canonical chooses zero. No unexplained candidate discrepancy remains in this fixture set. This is not a claim that iteration counts are identical after a tie changes a candidate.
3. Ran 189 native Relay inner-BP comparisons across gamma absent/0.2/0.6 and caps 1/3/7, with min-sum alpha=1 and bound=25. Posterior vectors agree within 2e-11; candidate differences are checked to be zero-belief ties. The independently composed canonical prior is `(1-gamma)*channel + gamma*previous_posterior`.
4. Compiled the exact aSCED projection and decision function bodies unchanged. All 29 probes agree after translating native I/X/Z/Y to project I/X/Y/Z. Three reproduce the nonmaximal Y decision from spike 008. Thus its provenance is confirmed, but the mathematical deficiency remains.
5. Source inspection also found aSCED's total-product/division check implementation, unlike this project's explicit excluded-neighbor product. It can encounter 0/0 for exact-zero incoming messages; no full native check-node edge-case execution was performed, so this remains a source-review concern, not a measured native failure.

## Results

**PARTIAL.** Ordinary BP equations and selected affine-memory behavior agree with independent upstream native implementations in the tested domain. This validates useful mechanisms but does not certify every source decoder, full Relay control flow, aSCED ensembles, or published curves.

The aSCED tie ladder belongs in an explicitly named source-compatibility policy. A generic maximum-posterior decision must choose a member of the maximizing set. Preserve the current profile for existing evidence and introduce any corrected behavior under a new identity. Source-defined variations in ties, saturation, damping, and initial stopping must remain configurable and documented.
