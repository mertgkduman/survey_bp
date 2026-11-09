# Canonical kernel: shared-policy completeness audit

Audited production baseline: **d031436** (implementation c512723). Spikes
050–053 continue the approved mathematics → upstream → policy → execution order.
The user requires existing/source-defined counterparts only. No production code,
historical results, numerical defaults, packaging scope or publication gate was
changed by this audit.

## Verdict

**The core mathematics and broad policy architecture are well supported; the
entire expanded public interface should not be frozen until F01 and F02 close.**
Neither finding requires redesigning binary or quaternary BP. Both concern
admitted composition/identity semantics that HTML would otherwise expose as
stable behavior. The appropriate next work is these bounded corrections and
their targeted qualification, not another unrestricted hunt for tiny issues.

No finite audit can promise that behavior will never need correction. A practical
freeze means explicit versioned contracts, tested accepted combinations, clear
exclusions, and preserved replay when future policies or corrections are added.

## Findings in recommended correction order

| ID | Severity / location | Observed defect | Required correction | Existing-result impact |
|---|---|---|---|---|
| **F01** | Medium; `canonical/memory_execution.py:54` | Local schedules admit affine-prior memory followed by fixed-prior PD-prime. Changing affine alpha changes the incoming field but every PD-prime output remains identical. | Reject this combination for layered/check-serial/variable-serial scheduling, matching flooding. Keep fixed-prior PD-prime and compatible compositions. A new recurrence requires a separately defined policy. | Investigate only results that used this exact local composition. Individual affine/PD-prime results are unaffected. |
| **F02** | High for reproducible circuit comparisons; `circuit/shared_policies.py:60` and `canonical/policy_decoder.py:294` | Sinter's batch-local row number enters the random key. One eight-shot call versus eight one-shot calls changes attempt/sweep-randomized predictions, even though all candidates satisfy the original detectors. | Version an explicit transport-independent random identity. Use content-based identity for the stateless adapter, or explicit stable sample IDs in a higher-level sampler. Preserve shared-v1 replay; test chunking, permutation, workers/instances and every identity-dependent policy family. | Any randomized experiment using the new shared Sinter adapter needs its batch/randomization contract recorded and selective rerun after migration. Deterministic legacy interfaces are not implicated. |

F01 is a cheap admission correction and prevents an ineffective composition from
being displayed as a meaningful control. F02 is the more consequential scientific
reproducibility issue and must close before publishing new randomized shared
circuit comparisons. A global call counter is insufficient because worker and
resume order can change it. No source-free Pauli adaptation is needed for either.

Evidence: [F01 operand observations](052-shared-policy-closure/fixed-prior-counterexample.json),
[F02 inputs and outputs](053-shared-evidence/chunking-counterexample.json).
The first is a pre-existing local admission gap exposed by the expanded policy
surface; the second is in the new shared Sinter transport. Generated ledgers are
internally replayable in both cases, demonstrating why replay alone is not a
scientific correctness oracle.

## Verification and comprehension map

| Contract | Evidence | Verdict / boundary |
|---|---|---|
| Binary SPA/MS/NMS/OMS, signed heterogeneous channel priors, prior shortcut and stopping | 1,152 independent factor-sum/minimum-cost comparisons; maximum posterior error 1.34e-15 | Pass for tested declared finite recurrences; no claim of exact loopy inference or optimal quantum coset decoding |
| Compiled precision, six formats, three scopes, two check rules, damping and coefficient rounding | 1,728 independent factor/quantization comparisons; maximum error 8.89e-16 | Pass; numerical resolution uses float64 storage/arithmetic, not native low-bit acceleration |
| Native ordinary BP correspondence | 972 installed ldpc 2.4.1 comparisons; exact candidates/iterations, posterior error at most 8.89e-16 | Pass under explicit prior, damping, cap, schedule and stopping alignment; native build commit unknown, binary hashed |
| Source-defined affine-prior recurrence | 216 pinned Relay inner-loop comparisons with heterogeneous priors; maximum error 1.50e-15 | Pass; not a full Relay controller or published-curve reproduction |
| Schedule/rule/memory/backend admission | 432 configurations: 200 accepted, 232 expected rejections; 800 primary shots plus 1,600 replay/repeat calls | Broad support passes; F01 identifies an additional invalid multi-memory composition |
| Structural and ensemble controllers | Nine controllers, two graphs, three channel vectors, all syndromes: 216 cases plus replay | Original-problem validation and selection invariants pass; source qualification and required operands remain explicit |
| Randomized schedule lifetime | Nine schedule/scope checks | Configuration/attempt/sweep refresh counts pass; F02 shows transport must preserve the chosen logical identity |
| Pauli family and named MBP4/Q-BPGD/aSCED paths | Unchanged source hashes; carried exact-tree, covariance and source-scoped policy qualification | Preserve family-specific equations and existing counterparts; no generic binary-to-Pauli ports |
| GPU subset | Source hashes match; four stored 1,024-shot H200 ledgers pass fresh content binding | Carried hardware/CPU replay qualification only; no new GPU execution or timing |
| Circuit affine semantics and packed Sinter transport | Deterministic offsets, separator-linked mechanisms, undetected logical prior, nine detector/ten observable bits, padding and empty batches | Pass on independent fixtures; DEM fault semantics are distinct from Pauli code-capacity variables |
| Result ownership, admission, export and replay | Immutable columns, invalid cast rejection, stale evidence rejection and exclusive ledger writes | Pass; a content digest is integrity metadata, not an authenticity signature |
| Regression and compatibility | Fresh 290 tests pass; source/hash-bound prior 2,462 broad passes/20 skips and 387 final affected passes; 82 legacy receipts identical; 24 real Sinter smoke shots replay | Carried and fresh evidence are separated; suites overlap and are not additive |

The 200 accepted matrix configurations are not a promise that the full Cartesian
product of policy families is supported. Existing graph-specific admission still
requires valid layer partitions, residual/group operands, row transforms and
source-specific controller settings. Full case inputs and invariant verdicts are
in [050](050-shared-mathematics/README.md), [051](051-shared-upstream/README.md),
[052](052-shared-policy-closure/README.md), [053](053-shared-evidence/README.md).

## What “gold standards” means here

The mathematical reference is local extrinsic sum-product and exact inference
on compatible trees, as described by
[Kschischang, Frey and Loeliger](https://web.stanford.edu/~montanar/TEACHING/Stat375/papers/sumprod.pdf).
Min-sum, damping, memory, finite precision and early stopping are explicit
modifications; native agreement does not replace independent equation checks.

The [ldpc API](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html) provides practical
channel, schedule and update controls; installed execution was compared here.
[Relay's pinned min-sum implementation](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs)
provides a source-defined inner memory reference and was also executed.
[aSCED's pinned SPA implementation](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp)
retains its previously documented zero-message and author-artifact qualifications.
It was source-reviewed here; its full ensemble was not newly reproduced.

[Sionna 2.2.0](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html)
offers CN/VN update hooks, schedules, message callbacks and state return. This is
an architectural comparison, not executed Sionna parity. Its input logit sign,
finite clipping and fixed-iteration interface must be aligned before numerical
comparison. A broad hook interface does not itself prove a literature algorithm.

The [Stim DEM specification](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/file_format_dem_detector_error_model.md)
and [Sinter API](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/sinter_api.md)
define detector/observable XOR semantics and little-endian packed batches.
Sinter provides no global per-shot ID to `decode_shots_bit_packed`; F02 is our
identity-design gap, not an upstream ban on randomized decoders.

## Coverage and intentional limits

CPU binary and circuit-fault execution support the same existing six schedules,
five memory kinds, nine controllers, indexed/generated parameters and compatible
compiled flooding policies. The [executable inventory](052-shared-policy-closure/capabilities.json)
and [usage guide](../../docs/shared-policy-support.md) describe the actual APIs.
The named Pauli counterparts retain their separate recurrences and recovery
semantics. GPU retains qualified float64 flooding and damping; branch-heavy
controllers, arbitrary histories, indexed/generated coefficients and reduced
precision remain excluded.

Layered execution requires a graph partition; Restart Belief requires its declared
distance/weight scope; MBBP requires explicit row transforms. SI requires opposite
CSS stabilizers. Source circuit OTF, executable cluster-learned scheduling,
adaptive MBP4 and new learned/TRW policies remain explicitly incomplete or outside
the implemented source contract. OSD/LSD are optional separate postprocessors.
Those limitations are not evidence that the ordinary BP kernel is defective.

Compiled ordinary flooding remains useful on CPU, while dynamic controllers use
scalar execution. Existing bounded timing showed roughly 56× warm flooding speedup
on its retained fixture; it excluded JIT/setup/I/O and was not an isolated scaling
benchmark. This audit introduces no performance claim or new optimization.

## Existing results and freeze criteria

This audit changes no decoder behavior. A tracked-file scan under data, manifests,
experiments and presentation results found no shared-v1 campaign and no explicit
affine-prior/PD-prime binding chain. Matches were design/schema documents; the
[impact receipt](053-shared-evidence/result-impact.json) preserves the search scope.
Untracked/private campaigns were not exhaustively inspected.

There is no evidence supporting a blanket rerun of available results. Preserve
their recorded source, numerical profile and settings. After the two corrections,
rerun only affected experiments if they exist; new randomized identity semantics
must have a version boundary and old receipts must remain replayable.

Freeze the accepted contracts after F01/F02 regressions and targeted legacy checks
pass, then let HTML consume that exact inventory. Paper/source reproduction,
publication-scale statistics, Phase 5 human review, paused Phase 7 and Phase 11
scientific gaps remain separate. Release packaging remains outside this task.
