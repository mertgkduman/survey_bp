# Canonical kernel boundary fixes

The approved B01 → B02 → B03 sequence is implemented. A separately versioned stable SPA policy is also available for compiled binary and Pauli flooding, including CPU batches. Historical profiles, public schema meanings and audit evidence are preserved.

| Order | Change | Evidence |
|---|---|---|
| 023 / B01 | Direct construction and dataclass replacement now validate rule/profile/policy compatibility, CSR consistency and immutable buffer ownership. Flooding rejects conflicting profiles. Relay exposes its delegated profile. | 15 pre-fix failures; 175 focused passes; 19 Relay integration passes |
| 024 / B02 | Check-serial, variable-serial and layered updates apply the active damping to updated edges and use the selected profile at numerical boundaries. | Independent degree-two recurrence at three damping weights; nine pre-fix failures; 69 focused passes |
| 025 / B03 | Compiled BP4 sweep and decode pass the active v1 saturation instead of a hardcoded default. | Five caps, three syndromes, full buffers and stopping checks; seven pre-fix failures; 47 focused passes |
| 026 | `bp-flooding-policy-v3` implements stable SPA through linear-time prefix/suffix reductions. | Independent high-precision and tree inference, recurrence/rounding tests, CPU controls and matched measurements |

Counts in the focused suites overlap; they must not be added to the broad-suite count.

## Stable policy contract

Use `from bp_registry.resolution import STABLE_SPA_F64` and pass `policy=STABLE_SPA_F64` to the compiled binary or Pauli constructor. See [the API and compatibility guide](../../docs/canonical-stable-spa.md).

The new policy passes the 100-case, 600-digit parity envelope that exposed the former high-confidence distortion. The LLR-40 binary tree now produces the exact posterior `log(2)` within float64 tolerance. Eight exhaustive four-state tree cases, repeated full-buffer recurrence checks, small-LLR relative-accuracy checks and all six supported resolution formats across all three rounding scopes are qualified.

Prefix/suffix reduction takes linear work in check degree and avoids excluded-product division. Unary checks retain an explicit finite hard-constraint approximation, `log((2-epsilon)/epsilon)`. Quantization occurs at declared boundaries; fixed-point and half-precision policies still use float64 internal storage and arithmetic. This is not a claim of native packed SIMD execution.

The policy is **opt-in**. Existing generic profile defaults and public manifest versions retain their previous behavior, including the documented exact-unity approximation. Promoting the new policy through public schema defaults remains a separate versioned migration. Compiled support here covers flooding; arbitrary schedules, interventions and circuit policies are not implicitly admitted.

## Qualification

The independent post-fix probe run passes 14 grouped checks: existing probability oracles, pinned native ldpc/Relay and extracted aSCED checks, historical full-buffer/public evidence controls, the corrected cap, and two CPU control matrices. Each matrix retains 840 ledger rows. The second substitutes stable SPA where mathematically compatible and keeps explicit v2 min-sum controls.

The first broad run exposed ten Relay integration failures because its adapter lacked a profile property. That failure evidence is retained. The adapter now declares the delegated profile and passes the shared check. The final fresh-cache regression run passes **1,368 tests with one existing skip**. Production source is committed as `be7286e`.

## Limits

This closes the three reported boundary defects and qualifies the new policy within the stated matrix. It does not establish correctness of every future policy composition, exact infinite unary constraints, or statistical reproduction of publication curves. Phase 11 source and publication gates remain unchanged. Native implementations remain correspondence references, not substitutes for independent mathematical oracles.

## Reproduce

```bash
NUMBA_NUM_THREADS=4 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical tests/circuit tests/research
NUMBA_NUM_THREADS=4 OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/026-stable-spa-qualification/qualify.py
NUMBA_NUM_THREADS=4 OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/026-stable-spa-qualification/benchmark.py
.venv/bin/python .planning/spikes/026-stable-spa-qualification/verify.py
```

Run timing measurements separately from tests or other local CPU work. The verifier checks source hashes, historical audit immutability, regression receipts, ledger validity/work and single-versus-multiworker agreement.

## Measured CPU performance

On the retained 512-shot workloads, four-worker stable-policy batches are **1.49× faster for binary BB72** and **1.46× faster for Pauli GB46** than the same compiled single-shot policy. Seven warm repeats exclude graph construction and ledger serialization; first-call/JIT timings are separate. All 2,048 retained benchmark rows agree with single-shot decisions, stopping and work.

The linear check reducer versus the compiled quadratic stable reference measures **0.92× at degree 4**, **5.26× at degree 16**, **23.07× at degree 64**, **102.74× at degree 256**. This component comparison does not imply the same whole-decoder acceleration.
