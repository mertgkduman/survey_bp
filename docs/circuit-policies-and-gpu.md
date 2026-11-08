# Circuit policies and CUDA execution

The circuit and CUDA interfaces are opt-in. Existing CPU graph defaults, the legacy
`CanonicalBpSinterDecoder`, manifests and recorded results retain their meanings.
These additions implement compatible subsets of the canonical policy contracts;
they do not establish new literature-curve reproduction results.

## Circuit decoding

`PolicyBpSinterDecoder` projects each independent Stim DEM error mechanism to one
binary fault variable, retaining its own signed LLR. Correlated detector targets
and `^` decomposition separators remain a single mechanism. Probability-zero
mechanisms are removed; probability-one mechanisms contribute affine detector and
observable offsets. Candidate selection sees detector residuals and original
fault-prior cost, never sampled faults or logical truth.

| Policy | Execution |
|---|---|
| SPA | Canonical binary float64 v3 exact-unity check rule and 0.1 old-message damping |
| MS / NMS / OMS | Canonical min-sum float64 v1, scalar normalization or offset |
| Ordered memory | Existing affine prior, V2C damping, PDBP field mix, PD-prime delta mix and posterior momentum schedules |
| Relay | Existing Relay controller, posterior-only transfer, finite affine-prior leg memory and heterogeneous-prior candidate scoring |
| Guided | Bounded finite-prior adaptation: bias the most reliable remaining marginal toward its decision, then start a fresh attempt |
| Beam | Bounded finite-prior adaptation: branch both signs of the least reliable remaining marginal; retain parents by residual weight, original prior cost, then attempt ID |

Guided/beam here are explicitly **canonical circuit adaptations**, not a claim to
implement every detail of a paper's named decoder. Finite bias changes the attempt
prior; it does not remove variables or constrain a bit absolutely. All candidates
are checked against the original detector problem. The first valid search layer
stops; candidates within that layer use the same original-prior score. Failed
branches count against `max_attempts`, and all their sweeps remain in the ledger.

`max_iterations` is per attempt/leg; `max_attempts` includes the initial attempt.
Single/guided/beam attempt initialization checks the prior decision before any
sweep. Relay retains its existing leg semantics. Memory resets per attempt, using
the existing declared composition order. Relay and ordinary memory composition
cannot be combined through this interface. Serial schedules, arbitrary callbacks,
hard reductions, OSD/LSD and Pauli memory policies are not admitted.

Controller-specific non-default fields are rejected when they have no execution
operand: `solution_limit` and `relay_alpha` apply only to Relay, `bias` applies
only to guided/beam, and `beam_width` applies only to beam. Shared default values
remain accepted and retain the same serialized policy identity. Interfaces and
parameter sweeps should expose these fields only for their active controllers.

Both scalar and compiled NMS reject nonfinite intermediate messages before
saturation, raising `NumericalFailure`. Finite coefficients remain admitted;
initial convergence and zero-iteration returns do not execute unused updates.

Ordinary attempts use Numba CPU compilation when `backend="auto"` (the default).
Memory and Relay use the inspectable canonical Python implementation.
`backend="scalar"` explicitly requests the oracle; `backend="compiled"` rejects
unsupported combinations. A ledger records the selected backend and numerical
profile. Circuit v3 SPA and CUDA stable SPA have distinct numerical identities.

```python
import numpy as np
import stim
import hashlib
import json
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder

factory = PolicyBpSinterDecoder(
    CircuitPolicy(
        rule="normalized_min_sum", parameter=0.8,
        controller="beam", max_iterations=20,
        max_attempts=9, beam_width=2, bias=20.0,
    ),
    ledger_directory="results/circuit-ledgers",
)
dem = stim.DetectorErrorModel(
    "error(0.1) D0 L0\nerror(0.2) D0 D1\nerror(0.15) D1"
)
decoder = factory.compile_decoder_for_dem(dem=dem)
result = decoder.decode_detailed(np.array([[1, 0], [0, 1]], dtype=np.uint8))
result.write_ledger("results/circuit-ledgers/manual.jsonl")
decoder.verify_ledger("results/circuit-ledgers/manual.jsonl")

# Bind Sinter's decoder name to the policy when caching/resuming statistics.
decoder_key = "canonical-policy-" + hashlib.sha256(
    json.dumps(factory.policy.model_dump(mode="json"), sort_keys=True).encode()
).hexdigest()
# In sinter.collect:
# decoders=[decoder_key], custom_decoders={decoder_key: factory}
```

For Sinter, configure `ledger_directory` to persist every packed batch, including
batches executed in worker processes. Each uniquely named JSONL records the
model/configuration/input identity, selected faults and observables, every
attempt/leg, posterior, stopping and work. Manual detailed calls return their
ledger without writing automatically. Exclusive atomic publication protects
existing evidence. Replay requires the original compiled DEM/configuration.
Direct `CircuitBatchResult` construction requires binary integer/boolean matrices,
boolean convergence, and nonnegative integer iterations representable as int64.
Arrays are validated before lossless conversion and immutable ledger binding;
floating-point columns and overflowing integer conversions are rejected.
When resuming Sinter statistics, retain a policy-specific decoder key as above
or equivalent task metadata; reusing one name for changed policies can mix
scientifically different runs.

## GPU code-capacity decoding

`CudaFlooding` accepts validated `CompiledBinaryFlooding` and `CompiledBp4Graph`
objects with explicit policies. Supported policies are float64 stable log-domain
SPA v3 and float64 min-sum v2, including scalar NMS/OMS, damping, all existing
Pauli decision rules, initial shortcut control, and Pauli fixed-iteration runs.
Float64 resolution scopes have the same arithmetic; reduced precision and
arbitrary schedules/controllers/memory chains are rejected.

The implementation uses one CUDA block per shot and parallelizes edges, checks
and variables inside it. Check and variable reductions retain canonical order.
No floating-point atomics or fast math are used. Graph buffers stay on the
device; batch workspace is bounded and large batches are chunked. A nonfinite
state rejects the entire batch. An unavailable device produces an explicit error.
Result arrays and compact metadata are bound and made immutable before return.
Full per-shot JSON is serialized only when the ledger is requested or exported,
so provenance formatting does not dominate batch decoding time.

```python
import numpy as np
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.gpu import CudaFlooding
from bp_registry.resolution import STABLE_SPA_F64

h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
graph = CompiledBinaryFlooding.from_check_matrix(h, policy=STABLE_SPA_F64)
gpu = CudaFlooding.from_binary(graph, error_rate=0.1)
result = gpu.run_batch(np.array([[1, 0], [0, 1]], dtype=np.uint8),
                       max_iterations=20)
result.write_ledger("gpu-batch.jsonl")
gpu.verify_ledger("gpu-batch.jsonl")  # independent canonical CPU replay

# For an existing explicit-policy joint-Pauli graph:
# gpu = CudaFlooding.from_pauli(pauli_graph)
```

Use a GPU allocation with a working CUDA driver/toolkit and Numba CUDA support.
The development cluster uses `module load CUDA/12.8`. No new mandatory
dependency was added to CPU execution. CUDA simulation is available only with
`NUMBA_ENABLE_CUDASIM=1` plus `allow_simulator=True`; its records identify it as
simulation and it is not performance evidence.

The GPU ledger binds graph/prior bytes, policy, syndrome batch, outputs and actual
per-shot iteration/work counts, and records the runtime/device and elapsed call
time including transfers and any JIT compilation. First-call compilation and warm
throughput must be reported separately; JSONL export time is also separate.
These timings compare one GPU with the declared number of CPU workers, not an
entire CPU socket. Float64 does not promise universal
bitwise agreement across CPU/GPU transcendental libraries; qualification checks
both message tolerances and exact candidate/stopping agreement on fixed fixtures.

Implementation references: [Numba CUDA kernel API](https://nvidia.github.io/numba-cuda/reference/kernel.html),
[device memory management](https://nvidia.github.io/numba-cuda/user/memory.html),
and [simulator limitations](https://nvidia.github.io/numba-cuda/user/simulator.html).
The existing project numerical contracts remain the algorithm specification.

## Measured qualification

On an NVIDIA H200, 20 hardware checks passed. On four fixed 1,024-shot batches,
all candidates, convergence flags and iteration counts matched the compiled CPU
exactly; all 4,096 stored shots also passed CPU replay. Median warm times across
three trials, with a 20-iteration cap:

| Case | Two CPU workers | GPU | Decode speedup |
|---|---:|---:|---:|
| Binary stable SPA, B1 n=882 | 1,245 ms | 10.07 ms | 123.6× |
| Binary NMS, B1 n=882 | 255 ms | 6.71 ms | 38.1× |
| Joint-Pauli stable SPA, BB72 | 479 ms | 5.25 ms | 91.3× |
| Joint-Pauli NMS, BB72 | 203 ms | 3.26 ms | 62.1× |

GPU times include transfers, allocation and immutable result/evidence binding.
They exclude first-call compilation and JSON export. Export took 0.60–0.66 s for
each binary ledger and 0.09 s for each Pauli ledger, so verbose evidence export can
dominate total workflow time. These measurements do not claim a full-socket CPU
comparison or a speedup for every batch size, policy or GPU.

The pinned Relay circuit check (54 detectors, 1,818 independent faults, 8,874
edges; four shots, three NMS sweeps maximum) matched scalar faults, observables
and iteration counts. Compiled CPU calls averaged about 49.6 ms versus 2.29 s
scalar, a 46.2× improvement on this bounded fixture.

[Hardware, timing and replay receipts](../.planning/quick/261108-meg-implement-compatible-circuit-policies-an/gpu-final/gpu-qualification.json)
and the [task summary](../.planning/quick/261108-meg-implement-compatible-circuit-policies-an/SUMMARY.md)
record the configurations, seeds, runtime, tests and remaining publication scope.
