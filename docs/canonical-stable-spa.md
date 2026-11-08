# Stable SPA and numerical compatibility

`bp-flooding-policy-v3` selects stable extrinsic sum-product updates in the binary and four-state compiled flooding engines. Use `STABLE_SPA_F64` explicitly:

```python
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.resolution import STABLE_SPA_F64

engine = CompiledBinaryFlooding.from_check_matrix(H, policy=STABLE_SPA_F64)
result = engine.run(syndrome, error_rate=0.08, max_iterations=20)
batch = engine.run_batch(syndromes, error_rate=0.08,
                         max_iterations=20, workers=4)
batch.write_ledger("events.jsonl")
```

`CompiledBp4Graph.from_code(code, priors, policy=STABLE_SPA_F64)` supports the same policy for joint Pauli decoding. The constant uses float64 messages, damping 0.1 (old-message weight), MAP Pauli decisions, and an initial prior-candidate convergence check. Disable that shortcut or change damping explicitly with `dataclasses.replace`; the complete effective policy appears in batch evidence.

This is an **opt-in policy**, not a change to historical profile defaults or public manifest schemas. Existing v1/v2 policies and numerical profiles retain their recorded meanings. Plain v3 profile execution still uses its documented tanh-product approximation, including its high-confidence limitation. Public manifest and publication qualification remain separate from this compiled-policy API.

## Mathematical contract

For finite binary LLRs, the check update combines extrinsic evidence with stable two-input box-plus. Prefixes reduce in canonical forward order and suffixes in reverse order; each outgoing message excludes its own incoming edge. Work is linear in check degree. There is no division by a product, so exact-zero inputs are supported. Small-magnitude pairs use a bounded tanh formula to avoid cancellation; its product is bounded away from unity. Large pairs use log-domain corrections.

The check syndrome changes the sign. Checks with at least one extrinsic neighbor implement finite-input SPA to floating-point precision. A unary check has an infinite exact hard-constraint message; this implementation deliberately emits the finite value `log((2-epsilon)/epsilon)` with syndrome sign. `product_epsilon` applies only to that unary convention in policy v3. There is no additional check clipping before the selected resolution boundary. Nonfinite messages are rejected.

BP4 first projects each I/X/Y/Z three-LLR vector into commute/anticommute log odds using log-sum-exp, then applies the same binary parity reduction. Pauli labels and MAP tie order remain explicit. Damping follows the fresh extrinsic update; it does not change the current posterior decision.

## Resolution and CPU support

Float64, float32, float16, int8, int16 and int32 boundary formats compose with the policy. Fixed-point formats require an explicit scale. `scalar_edges`, `all_messages` and `all_state` retain their existing boundary meanings. Arithmetic and storage remain float64 internally; these formats do not claim native packed integer or half-precision SIMD execution. Coefficients may remain float64 or round to the message format.

CPU parallelism is across independent shots. A single shot retains its declared reduction and stopping order. The configured Numba thread ceiling must permit the requested worker count; the batch API restores the caller's thread mask. No fastmath is enabled. Construction validates and owns immutable graph buffers once, outside decoding loops.

Compatibility is deliberately scoped: v3 is a sum-product flooding policy. Existing v2 policies provide min-sum, normalized and offset variants. This qualification does not extend compiled execution to arbitrary schedules, interventions, circuit decoding or public publication campaigns.

## Evidence

See `.planning/spikes/026-stable-spa-qualification/` for independent 600-digit parity checks, exhaustive four-state tree inference, full-buffer recurrence checks, rounding and batch tests, retained ledgers, and matched timing measurements. Upstream investigations remain in spikes 013 and 020; no new upstream speed or complete-decoder reproduction claim follows from this policy.
