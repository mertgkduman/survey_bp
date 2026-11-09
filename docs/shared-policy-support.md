# Shared policy support

`BinaryPolicyDecoder` and `SharedPolicySinterDecoder` execute the same canonical
binary schedules and controllers. The first accepts a parity-check matrix or
an `EdgeTable`; the second obtains that graph and heterogeneous fault priors from
a Stim detector error model. Both expose replayable detailed results. The new
contracts are `binary-policy-v1` and `circuit-shared-policy-ledger-v1`.
Historical manifests and `CircuitPolicy` / `PolicyBpSinterDecoder` retain their
existing defaults and meanings.

The scope follows the requested **existing/source-defined counterparts only**.
Reusing binary equations on a binary fault graph does not make an experiment a
reproduction of a paper's circuit curves. Controller receipts retain their
existing source revision and qualification, including existing adaptations.
No new binary-to-Pauli memory or intervention equations are introduced.

| Policy | Binary CPU and Stim/Sinter | Joint-Pauli CPU | GPU |
|---|---|---|---|
| SPA, MS, NMS, OMS | Shared execution; ordinary scalar coefficients compile | Existing family-specific compiled flooding | Existing qualified float64 flooding |
| Indexed/generated NMS/OMS coefficients | Scalar, source iteration, check and edge assignments; three refresh scopes | Existing scalar flooding coefficients only | Existing scalar coefficients only |
| Flooding, layered, check-serial, variable-serial | All shared; explicit layer partitions | Existing flooding and variable-serial counterparts | Flooding |
| Randomized traversal, Hsu groups, residual BP | Shared existing schedule algorithms | No implemented counterpart admitted | Excluded |
| Affine prior, V2C damping, PDBP, PD-prime, momentum | Existing ordered memory on flooding and supported local schedules | Existing named MBP4 recurrence and numerical damping; no generic binary-memory ports | Existing numerical damping |
| Guided decimation | Existing continuing BPGD controller | Existing Q-BPGD counterpart | Excluded |
| Impulse, freezing, syndrome flip, sign flip | Shared existing binary controllers; supported session damping | No new Pauli port | Excluded |
| Relay, beam, Restart Belief, MBBP list/vote | Shared existing controllers, subject to required operands below | Existing aSCED/overcomplete ensembles remain distinct algorithms | Excluded |
| Message precision and coefficient rounding | Existing v2/v3 flooding policies: float16/32/64, int8/16/32, three scopes | Existing compiled policies | Existing float64 subset |

These rows describe available implementations, not their unrestricted Cartesian
product. `BinaryPolicy` rejects inactive controls and unsupported combinations.
Graph-dependent validation runs when the decoder is constructed. The executable
inventory is `bp_registry.policy_capabilities.capability_inventory()`.

## Use the shared decoder

```python
import numpy as np
from bp_registry.canonical.policy_decoder import BinaryPolicy, BinaryPolicyDecoder
from bp_registry.circuit import SharedPolicySinterDecoder

policy = BinaryPolicy(schedule="check_node_serial", max_iterations=30)
h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
cpu = BinaryPolicyDecoder(h, policy)
result = cpu.decode([1, 1], prior_llrs=[2.0, 1.0, 3.0])
assert cpu.verify_ledger(result.ledger_json)

# Supply this decoder in sinter.collect(custom_decoders={"shared": decoder}, ...).
decoder = SharedPolicySinterDecoder(policy, ledger_directory="shot-ledgers")
compiled = decoder.compile_decoder_for_dem(dem=stim_dem)
batch = compiled.decode_detailed(detection_events)
batch.write_ledger("batch.jsonl")
assert compiled.verify_ledger("batch.jsonl")["verified"]
```

CPU decoding takes exactly one of `error_rate` (uniform binary channel) or
`prior_llrs` (one finite log P(0)/P(1) value per variable). Circuit decoding uses
the DEM's per-mechanism priors. Deterministic detector and observable biases,
whole-mechanism semantics for `^` separators, and little-endian Sinter packing
are preserved. No controller receives sampled faults or logical truth.

For a source controller, supply its existing controls in `options`. The
controller owns its update rule, schedule and iteration limits:

```python
policy = BinaryPolicy(
    controller="syndrome_flip",
    options={"baseline_sweeps": 10, "attempt_sweeps": 10,
             "top_k": 4, "max_weight": 2, "test_cap": 8,
             "root_seed": "syndrome-flip-1"},
    damping_gamma=0.5,  # Existing fresh-message weight for this session policy.
)
```

The other option schemas are the existing `InterventionSpec`, `ImpulseSpec`,
`FreezingSpec`, `SignFlipSpec`, `RestartSpec`, `MbbpSpec`, `FairLegConfig`, and the
shared runner's `RelayOptions`. Relay accepts explicit leg limits, ordered
affine-prior bindings and optional existing disordered memory tuning. MBBP
accepts `vote_tie_bit=0` or `1` to select the existing coordinate-vote terminal.
`damping_gamma` applies only to its admitted continuing intervention sessions;
ordinary execution uses `MemoryCompositionSpec` instead.

Fresh branches receive their correctly mapped priors after shortening. A reset
onto a changed graph requires an explicit mapped vector. Syndrome-flip trials
retain the existing heuristic's prior convention and XOR lift; they are not
silently reinterpreted as posterior conditioning. MBBP preserves its existing
frequency/weight selection. Beam's existing prior-weight score uses the supplied
per-variable channel. Results distinguish successful controller selection from a
diagnostic failure output, even when that output satisfies the original checks.

## Compiled precision controls

```python
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy

policy = BinaryPolicy(
    max_iterations=30,
    flooding_policy=BpFloodingPolicy(
        check_rule="min_sum", alpha=0.875, beta=0.0, damping=0.1,
        resolution=ResolutionPolicy("int8", 16, "all_messages"),
        version="bp-flooding-policy-v2",
        check_stabilization="exact_unity", product_epsilon=1e-10,
    ),
)
```

This delegates every sweep to the existing compiled policy arithmetic, extended
to vector priors. It supports existing rounding and coefficient semantics;
storage/arithmetic remain float64. It does not claim native low-bit throughput.
Explicit precision policies own all check/damping/resolution controls and use
the compiled backend. Regular scalar-parameter flooding also compiles by
default. Indexed updates, memory, schedules and controllers use scalar CPU;
requesting `backend="compiled"` for those paths raises an admission error.

Ordinary graph setup stays sparse and caches the compiled CSR indexes. Structural
source controllers retain their existing dense working-matrix implementations;
their costs and detailed ledger construction should be included when comparing
end-to-end throughput. `iterations` counts committed local units for local
schedules and BP sweeps across all attempts for flooding controllers; the ledger
states the unit and carries source-traversal/work evidence. These counts are not
interchangeable performance measures.

## Required operands and remaining exclusions

Layered scheduling needs a conflict-free partition of the graph. Hsu grouping
needs at least two checks; residual scheduling needs a nonempty edge pool and
undamped SPA. Restart Belief requires its declared distance/weight gate; a DEM
does not establish a quantum code distance. Its existing B1 mechanism must not
be presented as a distance-qualified circuit algorithm. MBBP requires explicit
GF(2) row transforms with the original graph's dimensions.

Joint-Pauli BP keeps its own positive four-state prior, symplectic check and
recovery contracts. MBP4, Q-BPGD, Pauli C2V normalization/offset and aSCED remain
available through those existing APIs. A binary DEM does not supply the Pauli
variables or CSS splitters needed to run those named algorithms unchanged.

Optional SI still needs opposite CSS stabilizers. The existing OTF CSS adaptation
does not establish the unfinished source circuit procedure. Clustered learned
scheduling currently has an artifact gate, not an executable scheduler. These
are explicit operand/source/implementation limitations, rather than runnable
features hidden behind a shared name. Adaptive MBP4 and new learned/TRW policies
remain future implementations. The GPU kernel retains its previously qualified
subset; no new GPU timing or feature qualification is claimed here.

This extension is opt-in. Existing experiments remain associated with their
recorded kernel versions and configurations. New policy choices require new
experiments when their outcomes are to be compared; no historical campaign was
rerun or relabelled as part of this change.
