# Stabilized kernel contracts and compiled CPU execution

The audit in `.planning/spikes/CANONICAL-KERNEL-AUDIT.md` is historical evidence against revision `3aacb2c`. Its counterexamples remain unchanged. This migration addresses the seven findings without reinterpreting historical numerical profiles or claiming new paper-curve reproduction.

## Corrected contracts

| Finding | Resolution |
|---|---|
| F01: BP4 chooses outside the maximizing set | Generic BP4 v3 chooses `argmin(0, Gamma_X, Gamma_Y, Gamma_Z)`, with ties I, X, Y, Z. Scalar and compiled implementations are checked over equality patterns. The old strict aSCED ladder remains available explicitly in v2 and `strict_pauli` source compatibility. |
| F02: terminal work resets | Capped and failed scalar, transformed, serial and MBP4 snapshots retain cumulative committed work. Denied/rolled-back requests add no committed work. New scalar public receipts carry `cumulative-v2`; independent sweep-count reconciliation supplements replay. |
| F03: omitted damping | All scalar BP4 schedules use the same damping primitive. Flooding applies it to the full proposed buffer; serial applies it immediately after each variable's extrinsic proposal, before later variables read it. Identity-transform and probability-domain serial tests qualify these boundaries. |
| F04: initial candidates disagree | New plain v3 and explicit flooding-policy v2 compiled routes initialize decisions from the selected priors. Zero-iteration convergence reports candidate validity. The stopping rule still controls whether initialization may terminate decoding. Historical compiled v1/v2 shortcuts remain frozen. |
| F05: hidden stabilization differences | Flooding-policy v2 requires `check_stabilization` (`exact_unity` or `epsilon_band`) and `product_epsilon`. Scalar and compiled paths share the log-ratio safeguard. Neutral-policy comparisons specify every numerical setting. |
| F06: finite prior overflows | Binary v3 and flooding-policy v2 use `log1p(-p)-log(p)`, including subnormal probabilities. Frozen v2 retains single-ratio initialization. |
| F07: mixed update/profile admission | `BinarySpaKernel` derives an omitted profile from the supplied update rule; conflicting explicit profiles fail before execution. |

The maximum-posterior decision follows the minimum-LLR principle in [Lai–Kuo Algorithm 1](https://arxiv.org/html/2104.00304v3#S3). Choosing I first on an exact I/nonidentity tie is an explicit canonical tie convention. Source-specific decision conventions remain separate.

Plain v3 deliberately retains the v2 exact-unity check safeguard. Its nonmonotonic behavior near machine saturation is therefore still an explicit numerical adaptation. This change does not promote box-plus, retune damping, or invalidate earlier profile-specific holdouts.

## Version selection

- Unversioned `BinarySpaKernel()` and compiled plain SPA select `binary-spa-flooding-f64-v3`.
- Unversioned `ScalarLlrBp4Kernel()` and `CompiledBp4Graph.from_code(...)` select `quaternary-bp4-f64-v3`.
- Public binary schema **10** selects v3 plain flooding; schemas 2–9 retain their bindings.
- Public quaternary schema **quaternary_experiment_v4** selects v3 scalar flooding or variable serial, with compatible normalization/offset transforms and identity intervention. Existing schemas retain their bindings.
- Plain min-sum v1, paper-specific routines, MBP4 and historical Q-BPGD keep explicit existing numerical contracts. Use flooding-policy v2 for corrected min-sum initialization in the compiled policy path.
- Old capped scalar receipts still replay byte-for-byte. Their verifier reports `work_accounting_verified: false`; their original work totals are not repaired or suitable for corrected work comparisons.

To verify archived audit source hashes after migration:

```sh
.venv/bin/python .planning/spikes/verify_kernel_audit.py --source-revision 3aacb2c
```

## Profile admission and public receipt verification

Follow-up spikes 016–018 close V3-A01–A03 from the v3 audit. Plain scalar and compiled SPA reject a min-sum profile without an explicit min-sum rule, including changed-saturation variants. Use `BinarySpaKernel(update_rule=MinSumUpdate())` for scalar min-sum.

Numerical profiles validate fixed descriptive fields at construction: precision, tie rules, encoding and reserved profile identities cannot relabel existing arithmetic. V1 saturation and v2/v3 cap, epsilon and damping remain configurable; the Pauli scalar check-rule choice remains available. Named profile serialization is unchanged. Non-reserved study labels remain supported with complete validated numerical evidence; the two existing v2-undamped aliases enforce their recorded settings. Use the explicit resolution policy for supported quantization, not a fabricated `dtype` field.

Public quaternary verification now compares every deterministic summary field against replay, including nested provenance, omitted or extra claims, and JSON value types. Output/ledger/manifest locations are excluded from that comparison so bundles can be moved; manifest content and ledger identity are still checked. Historical accounting remains explicitly selected and replayable. The decoder is replayed once, and temporary files are removed on comparison failure.

These checks run during construction or verification; compiled message-loop bodies are unchanged. The original timing artifacts remain historical measurements, not a new performance claim. Current source and post-fix qualification are checked with:

```sh
PYTHONPATH=src .venv/bin/python .planning/spikes/018-public-summary-fix/verify_fixes.py
```

See [the fix report](../.planning/spikes/KERNEL-V3-FIXES.md) for regression evidence and the unchanged exact-unity approximation.

## CPU support

| Composition | Single-shot compiled | CPU batch |
|---|---|---|
| Binary plain SPA v3 | Yes | Yes, first-valid stopping |
| BP4 plain SPA v3 | Yes | Yes, first-valid or fixed-iteration stopping |
| Explicit flooding-policy v2 SPA/MS/NMS/OMS, including combined scale/offset | Yes | Yes |
| Float64/32/16 and fixed-point int8/16/32 message policies | Yes | Yes, declared rounding scopes and coefficient rounding |
| Variable serial, transformed scalar BP4, MBP4, interventions, relay/branch controllers | Existing qualified routes only | Not admitted by this batch API |
| Historical profiles/policy v1 | Existing replay/single-shot routes | Rejected; select a corrected contract explicitly |

Quantized modes round float64 coordinates at declared boundaries; they are not native int8/float16 SIMD kernels. The batch API does not perform sampling, evaluate hidden truth, or substitute for campaign budget admission. It decodes supplied syndrome rows with a bounded iteration cap. There is no silent fallback to a different algorithm.

Two optimizations preserve the per-shot arithmetic order: SPA evaluates each edge's `tanh` once per sweep and reuses it in the original excluded-neighbor fold; min-sum finds the two smallest magnitudes and sign count in one scan per check. Repeated minima and zero signs are covered explicitly. No `fastmath` or reassociated product reductions are enabled.

Independent shots run through the same compiled decode functions as single-shot calls. Buffers are local to each shot, results retain input row order, and the caller's Numba thread mask is restored even after failure. Set `NUMBA_NUM_THREADS` before importing Numba to match the available allocation; pass `workers` explicitly. See Numba's [thread controls](https://numba.readthedocs.io/en/stable/user/threading-layer.html) and [parallel-loop contract](https://numba.readthedocs.io/en/stable/user/parallel.html).

```python
import numpy as np
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy

policy = BpFloodingPolicy(
    check_rule="min_sum", resolution=ResolutionPolicy("int8", 16, "all_messages"),
    damping=0.1, alpha=0.8, beta=0.1, hard_decision="map_pauli",
    zero_syndrome_shortcut=False, version="bp-flooding-policy-v2",
    check_stabilization="exact_unity", product_epsilon=1e-10,
)
graph = CompiledBinaryFlooding.from_check_matrix(H, rule="min_sum", policy=policy)
result = graph.run_batch(np.asarray(syndromes, dtype=np.uint8),
                         error_rate=0.08, max_iterations=20, workers=4)
result.write_ledger("events.jsonl")
```

For Pauli decoding, construct `CompiledBp4Graph.from_code(code, priors, policy=policy)` and call `run_batch` without `error_rate`. Omit `policy` for plain v3 SPA. `stop_on_convergence=False` requests a fixed number of Pauli sweeps; `converged` still reports final syndrome validity.

CPU ledgers identify the graph/prior and syndrome batch hashes, complete numerical contract, thread count, candidate, terminal reason and work per shot. Their `compiled-flooding-v1` work convention includes sweep work, the initial candidate, and actual convergence checks; graph/prior binding is outside the decode work scope. It is deliberately distinguished from scalar session accounting.

## Verification and timing

The stabilization tests cover equality patterns, finite priors, denied/failed work, old receipt replay, public schema round-trips, independent serial equations, neutral numerical policies, and scalar/compiled/batched parity. The format matrix spans all six supported formats and all three rounding scopes.

Run the bounded benchmark after other local CPU tests finish:

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 .venv/bin/python \
  scripts/benchmark_kernel_cpu_batch.py --output /tmp/bp-cpu-benchmark \
  --shots 256 --workers 4 --repeats 5
```

It retains inputs, per-shot ledgers, source hashes, versions, first-call overhead, repeated warm timings, and exact output comparisons. Binary single-shot timing uses the existing bound-prior API. A separate comparison loads the pinned pre-fix compiled implementation and compares both backends under frozen v2 settings, so numerical migration is not confused with a speed improvement. Results are local development measurements, not HPC allocation guarantees or statistical decoder-performance evidence.

### Saved measurements (2026-11-07)

At revision `dfe0306`, 256 matched observations per case, 20-iteration caps and five warm repeats gave:

| Comparison | Binary SPA / BB72 | BP4 SPA / GB46 |
|---|---:|---:|
| Optimized single-shot vs pre-fix compiled, both frozen v2 | 2.78× | 2.27× |

| Corrected profile/policy | One-thread batch vs optimized single-shot | Four-thread batch vs optimized single-shot |
|---|---:|---:|
| BB72 SPA | 1.09× | 1.32× |
| BB72 quantized NMS+OMS | 1.18× | 1.36× |
| GB46 SPA | 1.06× | 1.28× |
| GB46 quantized NMS+OMS | 1.04× | 1.22× |

These are separate comparisons, not a combined speedup claim. The shared host was not isolated. First-call timings, individual repetitions, environment details and source hashes are in the [qualified benchmark report](../.planning/debug/kernel-cpu-benchmark-qualified/report.json). Frozen-v2 buffer/output equality and corrected-profile single/batch equality were asserted before accepting timings.

Historical stabilization validation: the broad canonical/research suite passed 984 tests with one skip; 276 affected-path tests passed after the shared-loop refactor; 87 focused tests passed after the final legacy guards. These sets overlap. Both new public examples execute and replay. At the original stabilized source revision `dfe0306`, independent artifact validation checks 2,048 CPU ledger records against original check matrices, candidate validity, work equations and thread-count equivalence (this verifier deliberately rejects a changed source hash; use `verify_fixes.py` above for the current contract fixes):

```sh
.venv/bin/python .planning/debug/verify_kernel_stabilization.py
```

Binary graphs without edges terminate immediately with a prior decision and zero sweeps. Batch ledgers identify this structural terminal as `empty_graph`, separately from a policy's initial convergence shortcut.
