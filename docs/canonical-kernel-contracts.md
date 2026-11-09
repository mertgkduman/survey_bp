# Canonical execution contracts before HTML integration

The D03 → D04 → D01 → D02 → D05 corrections close the five findings from the
[completeness audit](../.planning/spikes/CANONICAL-KERNEL-COMPLETENESS-AUDIT.md).
The [qualification receipts](../.planning/spikes/042-batch-evidence-fix/README.md)
separate mathematical checks, upstream comparisons, policy coverage, regression
tests and CPU timing. Historical spikes 008–037 retain their original results.

The subsequent [circuit-policy and CUDA implementation](circuit-policies-and-gpu.md)
adds explicit opt-in execution paths. It preserves the legacy contracts below
and keeps publication studies separate from backend qualification.

The opt-in [shared policy decoder](shared-policy-support.md) now carries the
existing compatible binary schedules, memory, interventions and ensembles across
CPU code-capacity and Stim/Sinter fault graphs, with heterogeneous priors and
existing compiled precision policies. Its executable inventory records the
separate Pauli counterparts and GPU exclusions; older interfaces below retain
their frozen behavior.

The F01/F02 corrections reject changing-prior PD-prime compositions on local
schedules and give new shared Sinter execution a versioned, observation-based
random identity. Shared-v2 predictions and per-shot execution are independent of
batch partition and ordering; shared-v1 evidence replays with its historical
batch-index identity. See [identity semantics and migration](shared-policy-support.md#random-identity-and-historical-replay).
The [closure and result-impact report](../.planning/spikes/CANONICAL-KERNEL-SHARED-POLICY-FIXES.md)
records the passing regression, historical replay and preserved campaign inventory
for HTML integration.

## Capability and admission map

Resolve a configuration by regime, mathematical family, prior representation,
rule and assignment, numerical version, schedule, memory/controller and backend.
The table describes qualified boundaries. It does not license a Cartesian
product of its rows. Existing constructors, manifest preflight and compatibility
resolvers remain the executable admission authorities. HTML should display
their accepted configurations, identities, exclusions and evidence status.

| Contract | Priors and rules | Schedule and state | Backend and admission authority | Qualified boundary |
|---|---|---|---|---|
| Binary scalar BP | Scalar channel prior; SPA/MS; scalar, source-iteration or graph-resolved NMS/OMS | Flooding, layered, check-serial, variable-serial; explicit memory order | `BinarySpaKernel`, schedule constructors, `canonical/compatibility.py`, manifest preflight | Local/standalone context is `source-iteration-v2`; custom composition still requires admission |
| Binary compiled flooding | Scalar channel prior; corrected profile v3 or explicit flooding policies v2/v3 | Fixed flooding; declared damping and numerical policy | `CompiledBinaryFlooding`, bound prior, `binary_batch` | Compiled alpha/beta are scalar; no arbitrary indexed arrays, callbacks or controller batching |
| Joint-Pauli scalar BP | Positive I/X/Y/Z prior rows; family-specific update and memory contracts | Qualified flooding/serial schedules and C2V transforms | Quaternary problem/kernel/schedule constructors and compatibility resolver | Separate family semantics; zero-mass priors and generic q-ary updates remain outside this contract |
| Joint-Pauli compiled flooding | Positive heterogeneous joint priors; corrected profile v3 or policy v2/v3 | Fixed flooding and declared policy | `CompiledBp4Graph`, `pauli_batch` | Single/batch parity across the 432 configuration matrix; no universal memory/controller composition |
| Circuit independent-fault BP | Per-mechanism binary LLRs; deterministic effects as affine biases; legacy SPA/MS | Flooding; detector/observable projection | `DemBinaryModel`, `CompiledCanonicalBpDecoder` | Direct/factory/replacement admission validated; stable policy v3 is not part of this circuit loop |
| Circuit policy BP | Heterogeneous fault priors; canonical SPA/MS/NMS/OMS | Ordered ordinary memory, Relay, bounded finite-prior guided/beam adaptations | `CircuitPolicy`, `PolicyBpSinterDecoder`; compiled ordinary attempts and scalar memory/Relay | Explicit circuit-policy-v1; packed Sinter, per-batch ledgers, original detector validation; no universal paper-equivalence claim |
| CUDA flooding | Binary scalar channel or joint-Pauli priors; explicit float64 stable SPA v3 / MS v2, scalar alpha/beta | Flooding, damping, independent-shot batching | `CudaFlooding` over validated compiled graphs | CUDA hardware/simulator identity is explicit; no arbitrary memory, controllers, reduced precision or silent CPU fallback |
| Conventional residual | Source-qualified scalar SPA | Huang–Ueng cache lifecycle; undamped | Residual constructor and manifest compatibility | Damping, arbitrary memory and compiled stable-policy residual are excluded |
| Hsu overlapping groups | Plain SPA, preserving historical profile selection | Size-two, overlap-one source groups; dedicated RNG; D-09 local stopping | `HsuGroupSchedule`, manifest preflight | Update-rule overlays reject at construction |
| Randomized traversal | Admitted base layered/node-serial rule | Declared order refresh; canonical IDs and source iteration preserved | `RandomizedTraversalPlan` plus base schedule | Order generation does not change assignment indexing |
| Memory and search | Qualified affine prior, V2C damping, PDBP/PD-prime/momentum; Relay, BPGD, beam, restarting, MBBP | Ordered history, reset/fork/commit and full work/lineage | Existing memory/controller resolvers and public preflight | Source recurrences and interactions require their own evidence; no blanket compiled support |
| Named Pauli modifications | MBP4, Q-BPGD, aSCED and overcomplete ensembles | Named recurrence, intervention, splitter/lift and selection contracts | Their existing family-specific constructors | Selected compiled paths only; adaptive MBP4, missing author artifacts and correlated extensions remain explicitly limited |
| Artifact-gated or future methods | Clustered learned scheduling; learned updates, TRW/fractional/differentiable variants | External artifacts or new operand/equation contracts | Existing artifact gates; future qualification | Availability of a generic hook does not establish a reproduced algorithm |

The six compiled message formats are float16/32/64 and int8/16/32, with declared
rounding scopes and coefficient resolution. Internal storage/arithmetic remains
float64; format support is not a claim of native low-bit acceleration. The
[earlier inventory](../.planning/spikes/036-completeness-policies/CAPABILITIES.md)
retains the full audit-time inventory and its then-open findings. The table above
supersedes only those finding statuses, not the inventory's scientific limits.

## Context and historical replay

`BinarySpaKernel` defaults to `update_context_version="source-iteration-v2"`.
NMS/OMS receive the completed source-traversal count, canonical check ID and
canonical edge ID. Partial traversals, local-step counters and shuffled order do
not advance the parameter index. Missing iteration values fail the admitted
computation and roll back its mutation/reservation.

For historical standalone or local behavior, construct the kernel with
`update_context_version="legacy-zero-v1"`. This reproduces the earlier implicit
zero index. Explicit flooding and atomic flooding already accepted correct
context and retain that behavior under both modes. Standalone results and local
schedule evidence identify the context version. For byte-for-byte replay of a
complete historical ledger, use baseline source `6f68961` with its recorded
environment. Public numerical identities and manifest defaults are unchanged.

Serial results carry the posterior actually used for their candidate after
custom prior and belief transformations. Denied updates expose neither a new
candidate nor a posterior. No extra belief assembly is performed for reporting.

## Owned state and execution identity

Original binary and Pauli problems, logical maps, the audited derived/history
objects and session snapshots own immutable byte-backed numeric storage. Caller
aliases and `setflags(write=True)` cannot mutate those arrays. This is an
ownership contract, not a Python security sandbox or a claim that every internal
scratch array is immutable.

`DemBinaryModel.dem_sha256` identifies the source DEM.
`DemBinaryModel.execution_sha256` additionally binds the validated graph,
normalized priors, observable projection, affine biases and source error count.
A valid replacement receives its own execution identity. Construction rejects
invalid CSR, shape, scalar, binary-label and finite-prior inputs before native
decoding, including direct and dataclass-replacement paths.

## CPU batch evidence and verification

`CpuBatchResult` owns immutable inputs and outputs. Backend evidence
`numba-cpu-batch-v2` includes dimensions and `result_binding_sha256`, covering
the result arrays and execution metadata. Replacing a result while retaining
stale evidence fails admission. Ledger export checks the binding, serializes to
a temporary sibling file, and replaces the destination only after success.
This binding is an integrity check, not a signature or a scientific assessment.

```python
from bp_registry.cpu_batch import verify_cpu_batch_ledger

batch = graph.run_batch(syndromes, error_rate=0.08, max_iterations=20, workers=2)
batch.write_ledger("events.jsonl")
verification = verify_cpu_batch_ledger("events.jsonl", graph, error_rate=0.08)
```

For a Pauli graph, omit `error_rate`; its priors are already bound. Verification
checks graph/prior/numerical identity, replays single-shot outputs, independently
computes candidate parity, and verifies work and termination. It accepts
historical v1 ledgers without rewriting them. An empty JSONL file verifies zero
shots and carries no verifiable graph claim. Decoder validity remains distinct
from logical success, source fidelity and publication assessment.

CPU batches parallelize independent shots, with no fastmath or within-shot
reordering. The paired benchmark includes result construction and binding in
the measured batch cost, and keeps compilation and ledger I/O separate. Its
host allocation exposes two sibling hardware threads on one physical core;
the timings do not establish scaling across physical cores.

## Extension requirements

New policies must declare operands/shapes, coordinate identity, update order,
source/local context, history and reset/fork/commit behavior, numerical and
stopping rules, admission constraints and emitted evidence. Qualification needs
an independent numerical oracle where available, identity and parameter-sensitive
cases, order-sensitive cases, and denial/failure/reset cases. Historical
contracts remain replayable through named versions or pinned source snapshots.
Public stable-policy exposure and publication campaigns retain their existing
gates; these corrections do not complete paper reproductions or the circuit
publication stage.
