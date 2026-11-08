# Canonical kernel audit after circuit and CUDA extensions

Date: 2026-11-08. Production baseline: **b598ad1**. Scope: the user's approved
mathematics → upstream → policies → execution sequence, continued as spikes
043–046 after circuit-policy-v1 and CUDA were added. No production code, old
result, frozen profile or reproduction verdict changed during this audit.

## Decision

The evidence supports the ordinary BP mathematics and a useful range of policy
implementations. **No fundamental kernel redesign is indicated.** Binary BP,
joint-Pauli BP, circuit/Sinter decoding and CUDA are implemented, with explicit
capability boundaries. Three small contract gaps in the new circuit interface
should be closed before declaring that interface frozen for HTML/public use.
They do not demonstrate that existing ordinary-domain results are wrong.

This is a practical readiness assessment, not a promise that software will never
need a correction or that every literature algorithm is representable by every
backend. Once the bounded fixes below pass their regressions, proceed with HTML
over the documented capabilities. Further policy families can be versioned
extensions instead of changes to existing result meanings.

## Evidence, in the approved order

| Spike | Verdict | Fresh evidence | Scope limitation |
|---|---|---|---|
| [043: mathematics](043-circuit-cuda-mathematics/README.md) | PARTIAL | 1,152 circuit comparisons against independent probability/min-cost factor recurrences; eight CUDA-simulator exact-tree marginal checks | E01 concerns extreme finite coefficient overflow; simulator execution is not new hardware qualification |
| [044: upstream](044-new-path-upstream/README.md) | VALIDATED | 360 native ldpc comparisons; four multi-byte Stim/Sinter affine projection cases | Explicitly aligned numerical/stopping settings; source/API inspection is labelled separately from execution |
| [045: policy composition](045-policy-admission/README.md) | PARTIAL | 336 configurations: 188 accepted, 148 expected rejections; 1,504 primary shots, 380 with multiple attempts; repeated calls/shots; 24 memory identity cases | E02 exposes inactive controls; matrix covers targeted combinations, not every conceivable composition |
| [046: execution/evidence](046-public-evidence/README.md) | PARTIAL | Public result guards, replay/export checks, four stored GPU ledgers freshly validated; 120 focused regressions pass | E03 concerns manually constructed invalid results; prior hardware timing/CPU replay is carried evidence |

The twelve diagnostic groups contain **nine passes and three failed invariants**.
The fresh regression suite has **120 passes**. These counts describe different
checks and must not be merged into a claim that the findings are fixed.

Maximum fresh circuit-oracle posterior error is 8.88e-16; native comparison error
is 1.78e-15; CUDA-simulator exact marginal error is 1.67e-16, all against a
prespecified 2e-12 absolute/relative tolerance. Decisions, stopping and convergence
match exactly in the aligned native cases. Prior 192 Pauli exact-tree and 100
covariance checks were carried only after checking unchanged implementation hashes.

## Remaining fixes, recommended order

The order below closes result integrity, backend consistency, then UI admission.
The fixes are independent and bounded; none calls for changing ordinary BP equations.

| Order | Finding | Demonstrated trigger and consequence | Required closure |
|---|---|---|---|
| 1 | **E03: execution-dtype result admission** | Public CircuitBatchResult accepts a matching input array/ledger containing fault 256, then casts its stored array to uint8 zero. Four of five invalid-value probes diverge after conversion; negative iterations are also admitted. Independent replay rejects all five exports. | Validate field ranks, binary/boolean domains and nonnegative integral iterations before lossless normalization and evidence binding. Exercise direct construction and dataclass replacement. Keep valid generated results unchanged. |
| 2 | **E01: numerical failure parity** | NMS parameter=1e308 is finite and admitted. On a one-fault DEM, scalar execution raises NumericalFailure, while compiled/auto clips an overflowing check result and reports convergence. | Check finite intermediates before saturation, or impose a shared mathematically justified admission boundary. Scalar/compiled/auto must agree on failure. Ordinary normalization coefficients and all historical profiles retain their meanings. |
| 3 | **E02: inactive policy controls** | Non-default solution_limit/relay_alpha outside Relay, and bias outside guided/beam, are accepted but never consumed. Eight cases produce identical complete per-shot evidence while policy identities differ. | Reject non-default inapplicable fields or publish explicit inactive-field semantics. Expose only active controls in HTML. Retain default-valued shared fields if necessary for compatibility. |

Counterexamples are reproducible from
[043 overflow](043-circuit-cuda-mathematics/overflow-counterexample.json),
[045 controls](045-policy-admission/ineffective-controls.json), and
[046 conversion](046-public-evidence/conversion-counterexamples.json).

E02 matters for ordinary user configuration and policy sweeps. E03 concerns a
public constructor/import boundary, with independent replay containing the error.
E01 is a numerical guard gap at an extreme coefficient; no error in conventional
NMS coefficients was observed. These are finite closure tasks, not grounds for
another open-ended search for hypothetical edge cases.

## What standards and upstream comparisons establish

The independent reference is factor-graph sum-product, plus declared min-sum
approximations, Pauli commutation algebra, explicit numerical conventions and
original-problem validation. Exact tree marginals are appropriate oracles where
damping and saturation are inactive; a loopy BP output need not equal global MAP.
See [Kschischang, Frey and Loeliger](https://web.stanford.edu/~montanar/TEACHING/Stat375/papers/sumprod.pdf).

There is no single repository whose defaults form a universal standard:

- [ldpc](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html): installed 2.4.1 binary
  was hashed and executed with aligned parallel SPA/MS/NMS and heterogeneous
  channels. SPA comparison is one sweep because intrinsic circuit damping differs
  from the native settings. The queried v2.4.1 source tag was absent; build commit
  is explicitly unknown. The 360 comparisons cover a fresh native binary run.
- [Relay at 14cb31a](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs):
  pinned source explains alpha=0's special iteration-scaling convention and
  source-specific prior memory. New circuit Relay uses the existing canonical
  controller with heterogeneous priors; it is a declared adaptation.
- [aSCED at 8167720](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp):
  previous extracted-function/source correspondence remains scoped to those
  functions. It does not establish full author ensemble reproduction.
- [Stim DEM v1.15.0](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/file_format_dem_detector_error_model.md)
  and [Sinter v1.15.0](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/sinter_api.md):
  the adapter preserves one variable per independent error mechanism, correlated
  targets across separators, deterministic affine offsets, and little-endian
  detector/observable packing. Undetected logical mechanisms are inferred from
  priors without access to sampled truth.
- [Sionna 2.2.0](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html):
  callable node rules, schedules, callbacks and state provide an interface
  comparison. Sionna was not executed; learned/differentiable equivalence is not claimed.

## Current capability boundary

This updates, rather than overwrites, the historical
[036 capability map](036-completeness-policies/CAPABILITIES.md). Old D findings in
that map were fixed in 038–042; its circuit/GPU inventory predates the latest work.

| Area | Available now | Boundary |
|---|---|---|
| Binary/CSS code capacity | Canonical SPA/MS/NMS/OMS, versioned numerics, scalar schedules and qualified compiled flooding/CPU batches | Different numerical versions remain different policies; not all scalar schedules or assignments are compiled |
| Correlated quaternary code capacity | Joint I/X/Y/Z priors, commutation messages, qualified scalar/compiled BP4 and decisions | Pauli/symplectic decoding, not a general arbitrary-alphabet decoder |
| Literature policies | Ordinary memory primitives, Relay, guided/perturbative/search/list policies; MBP4, Q-BPGD and qualified aSCED paths | Each has a source status and compatibility boundary; mapped, adapted and reproduced remain separate claims |
| Circuit/Sinter | Per-mechanism priors, four check rules, five ordinary memory primitives, Relay and finite-prior guided/beam adaptations; packed Sinter protocol and ledgers | Binary fault-space problem; ordinary attempts compiled on CPU; memory/Relay use canonical Python; no promise of every literature policy or serial circuit schedule |
| CUDA code capacity | Binary and joint-Pauli float64 stable SPA and MS/NMS/OMS flooding, damping, qualified decisions/stopping, bounded batching | Explicit compatible subset; no generic memory/controller GPU port, reduced-precision throughput or circuit CUDA path |
| Evidence | Immutable ordinary outputs, exclusive JSONL export, original-problem verification and replay | E03 public construction guard remains; hashes bind content, not author authenticity |

Separate CPU, CUDA and circuit frontends or compiled kernels are compatible with
the architecture when each implements an explicit canonical contract. They need
not share a programming language. They must agree on equations, operand order,
numerics, stopping, original-space decisions and work under matched settings.
Circuit SPA currently uses canonical exact-unity v3 with 0.1 old-message damping;
CUDA stable SPA uses its separately versioned log-domain policy. Those identities
must not be collapsed merely because both labels contain “SPA” or “v3”.

Future policy admission should name regime, prior representation, update operands,
assignment shape, schedule, memory lifecycle, controller and backend. Keep the
independent oracle separate from that capability declaration. New equations need
new qualification; unsupported combinations should fail before execution.

## Performance and publication implications

The existing source-matched qualification has 20 H200 tests and 4,096 benchmark
shots with exact CPU candidate/iteration/convergence agreement and stored CPU
replay. Its measured warm GPU speedup is 38.1–123.6x against two CPU workers on
the tested batches. This includes transfers and result binding but excludes JIT
and JSON export. Binary JSON export takes about 0.60–0.66 seconds, while warm GPU
decoding takes about 0.007–0.010 seconds. This is useful batched acceleration,
not a universal whole-pipeline speedup claim. Keep export throughput visible in
future performance work instead of changing decoder equations to chase speed.

The prior full suite (2,285 passed, 17 skipped) and source-matched hardware receipts
were retained; the fresh focused suite passed 120 tests. See
[carried evidence](046-public-evidence/carried-qualification.json) and
[implementation qualification](../quick/261108-meg-implement-compatible-circuit-policies-an/SUMMARY.md).

Release packaging remains skipped at the user's request. Phase 11 is still 17/25
plans complete, with source-curve and other scientific gates open. Kernel
correctness/usefulness does not by itself certify unpublished curve reproductions
or complete the circuit publication campaign. No milestone or publication gate
was advanced by this audit.

## Bounded acceptance for the next step

Close E03 → E01 → E02 with targeted failing-then-passing regression cases, preserve
these audit receipts, and rerun the affected circuit/policy/evidence checks. No
new GPU allocation or complete literature campaign is required for those guards.
Then build HTML from the documented admitted subset; reopen mathematical audit
only when equations, numerical profiles, state lifecycles or backends change.
