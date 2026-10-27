# Canonical numerical profiles

New **plain flooding sum-product** decoders use float64 v2 by default in both
canonical families. The side-by-side [HTML](decoder-numerics-v1-v2.html) and
[PDF](decoder-numerics-v1-v2.pdf) show the update rules; both are built from
[`scripts/build_decoder_profile_comparison.py`](../scripts/build_decoder_profile_comparison.py).
Regenerate them with
`.venv/bin/python scripts/build_decoder_profile_comparison.py` from the
repository root.

| Family | New direct constructor | New public manifest | Resolved profile |
| --- | --- | --- | --- |
| Binary SPA | `BinarySpaKernel()` or `CompiledBinaryFlooding.from_check_matrix(...)` | schema `9`, `cpu-float64-spa-v2` by default | `binary-spa-flooding-f64-v2` |
| Four-state BP4 | `ScalarLlrBp4Kernel()` or `CompiledBp4Graph.from_check_matrix(...)` | `quaternary_experiment_v3`, `quaternary-bp4-f64-v2` by default | `quaternary-bp4-f64-v2` |

Runnable development manifests are
[`examples/canonical-v2-default.json`](../examples/canonical-v2-default.json)
and [`examples/quaternary-v2-default.json`](../examples/quaternary-v2-default.json).
Both omit the profile selector deliberately: their new schema versions supply
the v2 default and preflight records the resolved value. Use the checked v1
manifests for a frozen replay, or explicitly pass `REFERENCE_CPU_F64` and
`QBP4_F64_V1` to direct constructors for an ablation.

## Shared update equations

With old variable-to-check messages `m`, each flooding sweep first computes
all check-to-variable messages `R`, then posteriors `B`, then extrinsic
variable-to-check proposals `u`. The check update for both families is

\[
R_{c\to v}=2\operatorname{atanh}\!\left[(-1)^{s_c}
\prod_{w\in\partial c\setminus v}\tanh(m_{w\to c}/2)\right].
\]

For binary SPA, `m` is a bit LLR and the variable equations are

\[
B_v=\lambda_v+\sum_{c\in\partial v}R_{c\to v},\qquad
u_{v\to c}=B_v-R_{c\to v}.
\]

For BP4, `m` is the commute/anticommute projection of three
identity-referenced Pauli LLRs. With `a` in `X,Y,Z` and `A_{cv}(a)=1` when
`a` anticommutes with the edge label,

\[
B_v^a=\lambda_v^a+\sum_{c\in\partial v}A_{cv}(a)R_{c\to v},\qquad
u_{v\to c}^a=B_v^a-A_{cv}(a)R_{c\to v}.
\]

The BP4 prior is in `I,X,Y,Z` order internally. Its edge projection is
`log(P(commute)/P(anticommute))`; for a depolarizing prior `p0`, it starts at
`log[(1-2p0/3)/(2p0/3)]`. A binary CSS component uses marginal error
probability `q=2p0/3`. The physical sampling rate `p` and decoder prior `p0`
are separate experimental inputs.

## Numerical and stopping differences

- **v1:** clip finite prior, check, posterior, and variable LLRs to `[-25,25]`.
  Check messages use a stable ordered box-plus fold. The BP4 hard decision
  resolves nonidentity ties in internal `X,Y,Z` order. BP4 may accept the
  iteration-zero prior candidate when its syndrome matches.
- **v2:** retain finite float64 priors, posteriors, and extrinsic proposals
  without global clipping. Compute the check product directly; if its
  magnitude reaches one, use `sign(product) * (1-1e-10)` before `atanh`.
  The default has no separate check-message cap. Damp only the outgoing
  variable message, `m_new=0.1 m_old+0.9 u`. BP4 uses the strict four-state
  decision ladder (I, then X, then Z, otherwise Y) and always completes a
  sweep before accepting a candidate. Binary SPA retains its zero-LLR bit-0
  tie rule and first-valid stopping after a completed sweep.

The v2 check implementation substitutes `tanh(m/2)=sign(m)` for `|m|>40`
before the product. Products are accumulated in graph edge order. The v2
profile rejects nonfinite internal values. The code-capacity kernels here
require strictly positive four-state BP4 priors; exact-zero support from the
separate Python reference described in the investigation is not implemented.
These are float64 policies, so the presentation's Q8 rounding, scale, and
saturation settings are distinct experiments.

## Versioned compatibility

Historical public schemas, result ledgers, numerical profiles, and source
procedures retain their exact v1 meaning. Existing min-sum, memory,
intervention, Relay, Q-BPGD, MBP4, and circuit adapter routes remain on their
declared profiles until each combination has an explicit compatibility and
replay contract. The new v2 public schemas admit plain flooding SPA or BP4
only; supplying another update, schedule, or intervention is rejected.
The BP4 v2 resolver labels its numerical kernel and whole run as a
`canonical_adaptation`, since its clipping, damping, and tie policy are not
claimed to be the cited source's exact numerical procedure.
Compiled and Python plain flooding implementations share the v2 equations,
but floating-point reduction order can still differ. Stored profile IDs and
independent outcomes should be used when comparing runs.
