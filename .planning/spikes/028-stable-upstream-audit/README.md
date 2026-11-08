---
spike: 028
idea: canonical-kernel-audit
name: stable-upstream-audit
type: standard
validates: "Given the corrected kernel, when boundaries are exercised, then native and canonical comparisons use explicit mathematical and numerical alignment"
verdict: VALIDATED
related: [023, 024, 025, 026]
tags: [freeze-audit, boundaries]
---

# Stable upstream audit

## Research
Reuse the independent equations, pinned upstream identities and qualified contracts in spikes 019–026. Numerical and implementation agreement are tested separately.

## Investigation Trail
Baseline 12cf2b1, production be7286e. No production changes.

## Results
All six grouped comparisons/classifications pass. Stable SPA matches native ldpc in 63 aligned moderate-range cases to 1.84e-15 posterior error. Eight high-confidence cases match independent exact parity within 2e-11, with native divergence explicitly retained. 84 native NMS controls and 189 pinned Relay inner-memory controls pass; 24 NMS tie-coordinate differences are confined to the stated 2e-11 zero envelope. Five extracted aSCED zero cases retain their prior classification.

## Research
Primary references: [ldpc BP](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html), [Sionna v2.1.0 source](https://github.com/NVlabs/sionna/blob/v2.1.0/src/sionna/phy/fec/ldpc/decoding.py), [pinned Relay](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs), [pinned aSCED](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp).

Sionna offers callable node updates, ordered callbacks, scheduling and reusable state. Those are useful extension-interface comparisons, not proof that arbitrary compositions are mathematically compatible. Its source also bounds float64 phi arguments independently of the optional output clipping parameter. Six NumPy-transcribed cases quantify that envelope; this is explicitly not Sionna/PyTorch execution. The fetched source bytes are SHA-256 identified, with tag rather than independently resolved commit identity. No new package was installed.

## Run
`OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/028-stable-upstream-audit/probe.py`

## Investigation Trail
Compared native terminal iterations rather than assuming the same stopping rule. Extended rate values above 0.5 to exercise prior sign. Read the actual Sionna implementation after documentation review and found mandatory internal phi bounds; recorded this distinction instead of treating a named log-domain algorithm as an unlimited-precision oracle. Historical Relay/aSCED probes were imported without rewriting their evidence directories.
