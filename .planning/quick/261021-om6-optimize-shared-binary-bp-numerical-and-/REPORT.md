# Production binary BP shared-path profile

## Change

The production binary SPA box-plus pair now uses validated scalar clipping and arithmetic without allocating two-element NumPy arrays for every fold. It retains the existing `binary-spa-flooding-f64-v1` numerical profile, floating-point reduction order, nonfinite failure boundaries, and exact-zero decision. Binary flooding also preindexes immutable excluded-neighbor edge IDs and uses the fresh array already returned by `finite_saturate` as its owned old-message snapshot. The policy `check_message` callback, source-iteration/check/edge identities, memory transforms, work counts, and publication interfaces remain in place. Other binary schedules use the same scalar SPA primitive, but only the flooding schedule received the graph-index change.

## Matched timing and exactness

`scripts/benchmark_binary_policy_sweeps.py` ran three fresh-session repetitions of three successive BB72 sweeps per rule on host `dcc-core-ferc-u-ab39-5-6`, CPU 56 affinity, with OMP/OpenBLAS/MKL thread counts at one. The workload used one seeded syndrome, the same graph/prior, and explicit scalar normalization or offset assignments. Session construction is excluded from per-sweep timing.

| Binary flooding rule | Before ms/sweep | After ms/sweep | Before/after |
|---|---:|---:|---:|
| SPA | 17.668 | 7.004 | 2.52× |
| Min-sum | 3.561 | 3.133 | 1.14× |
| Normalized min-sum | 3.543 | 3.167 | 1.12× |
| Offset min-sum | 3.116 | 2.869 | 1.09× |

The [before](./before.json) and [after](./after.json) records match exactly on host, affinity, graph and syndrome hashes, 517 scalar box-plus output bit patterns, and all three sweeps' old V2C, C2V, beliefs, new V2C, candidate, and proposed-work hashes for every rule. The scalar regression oracle additionally compares 4,101 pairs against the former NumPy expression, bit for bit, at three saturation limits (25, 12.3, 500), including signed zero and tiny values. It checks invalid-input behavior.

## Verification and limits

Focused numerical, flooding, memory, and Relay differential tests passed **68/68**. Additional schedule, residual, local-memory, intervention, group-shuffled, Relay, cluster, trace, and policy tests passed **128/128**. Python compilation and `git diff --check` passed. Existing flooding tests verify that the returned old snapshot does not share memory with the caller's input.

These measurements cover one code and one syndrome, so the speedups are engineering evidence rather than a population estimate. They do not convert typed binary and quaternary work units or authorize a publication campaign. The opt-in compiled binary plain kernel remains a separate development backend; this change accelerates the shared Python execution used by policy compositions. Full-shot, whole-campaign throughput with ledger and budget work remains to be measured before making a backend or resource decision.
