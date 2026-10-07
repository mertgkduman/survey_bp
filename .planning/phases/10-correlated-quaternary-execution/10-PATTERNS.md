# Phase 10: Correlated Quaternary Execution - Pattern Map

**Mapped:** 2026-10-06  
**Files classified:** 22  
**Analogs found:** 22 / 22

Phase 10 needs a separate quaternary kernel family. Do not widen the binary
`OriginalProblem`, `BinarySpaKernel`, or binary policy registry: their types and
mathematical semantics are deliberately binary. Reuse their lifecycle, immutable
value, preflight, work-accounting, and evidence patterns at the integration seam.

## File Classification

| New/Modified File | Role | Data Flow | Closest tracked analog | Match |
|---|---|---|---|---|
| `src/bp_registry/quaternary/algebra.py` | utility/model | transform | `src/bp_registry/css.py` | role-match |
| `src/bp_registry/quaternary/problems.py` | model | transform | `src/bp_registry/canonical/problems.py` | role-match |
| `src/bp_registry/quaternary/numerics.py` | utility | transform | `src/bp_registry/canonical/numerics.py` | role-match |
| `src/bp_registry/quaternary/kernel.py` | service | request-response | `src/bp_registry/canonical/kernel.py` | role-match |
| `src/bp_registry/quaternary/schedules.py` | service | event-driven | `src/bp_registry/canonical/schedules.py` | role-match |
| `src/bp_registry/quaternary/contracts.py` | config | request-response | `src/bp_registry/canonical/contracts.py` | role-match |
| `src/bp_registry/quaternary/compatibility.py` | service | request-response | `src/bp_registry/canonical/compatibility.py` | role-match |
| `src/bp_registry/quaternary/qbpgd.py` | controller | event-driven | `src/bp_registry/canonical/guided_decimation.py` | role-match |
| `src/bp_registry/quaternary/mbp4.py` | service | event-driven | `src/bp_registry/canonical/memory_execution.py` | partial |
| `src/bp_registry/quaternary/asced.py` | controller | event-driven | `src/bp_registry/canonical/mbbp.py` | role-match |
| `src/bp_registry/quaternary/execution.py` | controller | request-response | `src/bp_registry/canonical/execution.py` | role-match |
| `src/bp_registry/quaternary/evaluator.py` | service | request-response | `src/bp_registry/evaluator.py` | role-match |
| `src/bp_registry/quaternary/sampling.py` | service | request-response | `src/bp_registry/sampling.py` | role-match |
| `src/bp_registry/quaternary/native_asced.py` | service | process I/O | `src/bp_registry/reference.py` | role-match |
| `src/bp_registry/artifacts.py` | config | file-I/O | `src/bp_registry/artifacts.py` | exact |
| `src/bp_registry/manifests.py` | config | file-I/O | `src/bp_registry/manifests.py` | exact |
| `src/bp_registry/runner.py` | controller | batch | `src/bp_registry/runner.py` | exact |
| `src/bp_registry/cli.py` | controller | request-response | `src/bp_registry/cli.py` | exact |
| `src/bp_registry/ledger.py` | service | append-only event-driven | `src/bp_registry/ledger.py` | exact |
| `tests/canonical/quaternary/conftest.py` | test | transform | `tests/canonical/conftest.py` | role-match |
| `tests/canonical/quaternary/test_*.py` | test | request-response/event-driven | `tests/canonical/test_guided_decimation.py` | role-match |
| `data/manifests/quaternary-*.json` | config | file-I/O | `data/manifests/canonical-three-qubit-development.json` | role-match |

## Pattern Assignments

### `quaternary/algebra.py`, `problems.py`, and artifact compilation (model, transform)

**Analogs:** `src/bp_registry/css.py`, `src/bp_registry/canonical/problems.py`, and `src/bp_registry/artifacts.py`.

Build a new immutable Pauli check/code type with its own semantic bytes and hash;
keep ordered check rows, edge Pauli labels, combined syndrome order, and optional
logical basis in the hashed identity. Compile CSS only at this boundary. Preserve
the original Pauli problem and represent aSCED paths as explicit transformed
working problems with a lineage edge.

**Immutable binary/value validation** — `canonical/problems.py:11-17,20-32`:

```python
def _readonly_binary(value: np.ndarray, *, ndim: int, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != ndim or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary integer array with {ndim} dimensions")
    copied = np.array(array, dtype=np.uint8, copy=True)
    copied.setflags(write=False)
    return copied

@dataclass(frozen=True)
class OriginalProblem:
    lineage_id: str
    hx: np.ndarray
    hz: np.ndarray
    syndrome: np.ndarray
```

**Identity versus certified transform guard** — `canonical/problems.py:47-85`:

```python
if self.parent_edge.relation not in {"identity", "transform"}:
    raise ValueError("working problem requires an identity edge or certified transform edge from its original")
...
if identity:
    if ... or not np.array_equal(h, self.original.hz) or not np.array_equal(s, self.original.syndrome):
        raise ValueError("identity working problem cannot change graph, syndrome, maps, or lift")
elif not self.transform_identity or not self.lift_identity:
    raise ValueError("working problem requires an identity edge unless transform and lift identities are explicit")
```

**GF(2) qualification primitive** — `css.py:37-61`:

```python
def gf2_rank(matrix: np.ndarray) -> int:
    a = _bits(matrix, "matrix")
    ... # Gaussian elimination over GF(2)

def in_row_space(matrix: np.ndarray, vector: np.ndarray) -> bool:
    rows = _bits(matrix, "matrix")
    candidate = _bit_vector(vector, "vector", rows.shape[1])
    return gf2_rank(np.vstack((rows, candidate))) == gf2_rank(rows)
```

**Confined version dispatch** — `artifacts.py:94-152`:

```python
def load_artifact(root, relative_path, *, expected_raw_sha256=None,
                  expected_semantic_sha256=None, max_bytes=MAX_ARTIFACT_BYTES):
    artifact = _confined_file(root, relative_path)
    ...
    decoder = _DECODERS.get(version)
    if decoder is None:
        raise ValueError(f"unsupported CSS artifact format version {version}")
    code = decoder(decoded)
    semantic_digest = semantic_sha256(code)
```

### `quaternary/numerics.py`, `kernel.py`, and `schedules.py` (kernel service, transform/event-driven)

**Analogs:** `src/bp_registry/canonical/kernel.py` and `src/bp_registry/canonical/numerics.py`.

Use the same small pure-method layout: validate at the public boundary, then keep
check-message calculation, belief assembly, excluded variable message, hard
decision, and convergence separately testable. Define a new quaternary numerical
profile; binary `REFERENCE_CPU_F64` must never identify a QBP run. Schedule
implementations own message freshness and must only admit flooding and the
source-defined serial order.

**Pure kernel surface** — `canonical/kernel.py:20-79`:

```python
@dataclass(frozen=True)
class KernelResult:
    candidate: np.ndarray
    converged: bool
    iterations: int

class BinarySpaKernel:
    def check_message(self, incoming, syndrome, *, check_index=0, edge_index=0, source_iteration=0) -> float: ...
    def assemble_beliefs(self, variable_count, edge_variables, messages, prior) -> np.ndarray: ...
    def variable_message(self, belief: float, check_message: float) -> float: ...
    def candidate_from_beliefs(self, beliefs: np.ndarray) -> np.ndarray: ...
```

**Bounded run/convergence sequence** — `canonical/kernel.py:81-100`:

```python
for iteration in range(1, max_iterations + 1):
    sweep = schedule.sweep(v2c, s, error_rate=error_rate)
    candidate = sweep.candidate
    if np.array_equal((h.astype(np.int64) @ candidate) % 2, s):
        return KernelResult(candidate, True, iteration)
    v2c = sweep.new_v2c
return KernelResult(candidate, False, max_iterations)
```

### `quaternary/contracts.py` and `compatibility.py` (config/service, request-response)

**Analogs:** `src/bp_registry/canonical/contracts.py` and `src/bp_registry/canonical/compatibility.py`.

Create a closed quaternary policy vocabulary and compatibility table. Bind source
revision, equations/order, numerical profile, source status, and lifecycle state
in the strict manifest spec. Reject binary policy names, AMBP4, non-CSS aSCED,
and unqualified combinations during preflight before artifact resolution or
sampling.

**Strict frozen models** — `manifests.py:35-38` and `canonical/contracts.py:12-18`:

```python
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
```

**Preflight sequencing** — `manifests.py:961-989`:

```python
_verify_canonical_environment(manifest.environment)
validate_composition(manifest.policies)
artifact = load_artifact(..., expected_raw_sha256=manifest.artifact.raw_sha256,
                         expected_semantic_sha256=manifest.artifact.semantic_sha256)
code = artifact.code.validate()
for name, expected in manifest.artifact.matrix_hashes.model_dump().items():
    if hashes[name] != expected:
        raise ValueError("Phase 5 matrix identity does not match the artifact")
```

### `quaternary/qbpgd.py` (controller, event-driven)

**Analog:** `src/bp_registry/canonical/guided_decimation.py`.

Use a controller that receives only posterior/marginal state and an explicit
budget tree. It must propose, reserve, commit, and record one fixation at a
time. Q-BPGD's four-state reliability, I/X/Y/Z tie order, raw source weights,
ratio-preserving normalized decoder prior, continued edge-message buffer, and
lowest-index qubit tie are all quaternary-specific fields/events.

**Controller test pattern and replay proof** — `tests/canonical/test_guided_decimation.py:60-78`:

```python
result = controller.run(session, check_matrix=h, budgets=budget)
assert result.work == budget.summary("attempt")
assert len(result.rounds) <= 2
reconstruct_guided_result(spec, h, syndrome, 0.1, result)
with pytest.raises(ValueError, match="replay"):
    reconstruct_guided_result(..., replace(result, termination="no_eligible_target"))
```

**Reserve before mutation** — `tests/canonical/test_guided_decimation.py:198-226`:

```python
proposal = session.propose_finite_prior(...)
assert proposal.anticipated_work.fixation_actions == 1
transition = session.commit_intervention(proposal, budgets=budget, leaf_id="fix-test")
assert transition.admitted
assert budget.summary("attempt") == proposal.anticipated_work
```

### `quaternary/mbp4.py` and `asced.py` (kernel/controller, event-driven)

**Analogs:** `src/bp_registry/canonical/memory_execution.py`, `src/bp_registry/canonical/mbbp.py`, `src/bp_registry/canonical/transformations.py`, and `src/bp_registry/canonical/candidate_selection.py`.

MBP4 is a separate QBP recurrence, not a binary memory adapter. aSCED should
follow the ensemble pattern: immutable original problem, one certified working
graph per `(batch, virtual-syndrome)` path, all path results/work retained, then
stable selection only from candidates valid against the original syndrome. Store
both extended-path and original validity. Validate ordinary/overcomplete checks
and their row order before creating paths.

**Stable selection must not depend on completion order** — `canonical/problems.py:101-103`:

```python
def select_stable_candidate(candidates):
    """Select by declared stable lineage/local order, never completion arrival."""
    return min(candidates, key=lambda candidate: (candidate.local_order, candidate.lineage_id), default=None)
```

**No-selection zero-return pattern** — `tests/test_phase6_public_execution.py:50-64`:

```python
projection = phase6_events(original, bases=(basis,), result=result)
assert projection.terminal == "no_member_converged_zero_return"
assert "selection" not in kinds and "original_check" not in kinds and "evaluation" not in kinds
```

### `quaternary/sampling.py` and `evaluator.py` (services, request-response)

**Analogs:** `src/bp_registry/sampling.py` and `src/bp_registry/evaluator.py`.

Put the joint channel sampler and hidden Pauli truth in new types. Sample exactly
one categorical `I/X/Y/Z` value per qubit and derive symplectic truth from it.
Keep exact physical zeroes. Require an explicit decoder smoothing policy before
LLR conversion. The evaluator must be independently implemented from kernel
algebra and classify only after candidate production.

**Existing evaluation boundary** — `evaluator.py:33-83`:

```python
def evaluate_candidate(code, *, true_x=None, true_z=None, candidate_x=None, candidate_z=None) -> Evaluation:
    ...
    if not np.array_equal(... proposed_x ..., expected_z_check) or not np.array_equal(... proposed_z ..., expected_x_check):
        return Evaluation("invalid_syndrome", None)
    residual_x, residual_z = original_x ^ proposed_x, original_z ^ proposed_z
    if not residual_x.any() and not residual_z.any():
        return Evaluation("exact", True)
    stabilizer_equivalent = in_row_space(...) and in_row_space(...)
```

**Truth-sealing test** — `tests/canonical/test_guided_decimation.py:229-264`:

```python
first = run(truth_one, tmp_path / "one.jsonl")
second = run(truth_two, tmp_path / "two.jsonl")
assert [row["data"] for row in one if row["kind"] != "termination"] == [
    row["data"] for row in two if row["kind"] != "termination"
]
assert first.evaluation.outcome == "exact"
assert second.evaluation.outcome == "logical_failure"
```

### `quaternary/execution.py`, public manifest/runner/CLI/ledger seams (controller/config/event-driven)

**Analogs:** `src/bp_registry/canonical/execution.py`, `src/bp_registry/manifests.py`, `src/bp_registry/runner.py`, `src/bp_registry/cli.py`, and `src/bp_registry/ledger.py`.

Make quaternary execution an engine-owned, truth-sealed public route. Extend the
public manifest dispatch rather than weakening historic schemas. Require Pauli
artifact/hash, resolved full priors and channel identity/order, quaternary policy
composition, budgets, source/evidence labels, and numerical profile. Emit path
events, work events, selection, independent evaluation, and terminal event; reuse
the canonical ledger grammar and replay/validation entry points.

**Decoder-visible immutable capability view** — `canonical/execution.py:67-82,85-118`:

```python
@dataclass(frozen=True)
class CapabilityView:
    values: Mapping[str, Any]

def capability_view(self, values):
    return CapabilityView(MappingProxyType({str(key): _freeze_value(value) for key, value in values.items()}))
```

**Public result evidence labels** — `cli.py:226-250`:

```python
return {
    "title": f"{report['run_id']} — {manifest.evidence.relation} {manifest.evidence.fixture} {manifest.evidence.assessment_status}",
    "relation": manifest.evidence.relation,
    "fixture": manifest.evidence.fixture,
    "assessment_status": manifest.evidence.assessment_status,
    "manifest_sha256": digest,
}
```

### `quaternary/native_asced.py` (isolated reference service, process I/O)

**Analog:** `src/bp_registry/reference.py`.

Represent the pinned author repository as a distinct native identity and record
available data plus explicit unavailable counters/reasons. Keep checkout,
environment/build overlay, driver output, Pauli-order translation, and aggregate
native evidence outside canonical execution. Never call native output a canonical
kernel result or claim unavailable shared shots are paired.

**Explicit native missingness** — `reference.py:23-63`:

```python
facts = self.metric_facts or (
    MetricFact.observed("native_iterations", self.iterations, ...),
    unavailable_metric("native_edge_updates", ..., reason=_EDGE_UPDATES_UNAVAILABLE),
    unavailable_metric("native_control_flow_events", ..., reason=_CONTROL_FLOW_UNAVAILABLE),
)
if by_metric[metric].missingness.value != "unavailable":
    raise ValueError(f"native {metric} must remain unavailable without SDK instrumentation")
```

## Shared Patterns

### Immutable original observation and lineage
**Sources:** `canonical/problems.py:47-85`; `canonical/problems.py:101-103`.  
**Apply to:** QBP execution, Q-BPGD, MBP4, and every aSCED path.

Original checks/syndrome never change. Any virtual syndrome/augmented graph gets
a certified transform identity, parent edge, row/column maps, and stable local
order. aSCED selection filters only by original-syndrome validity.

### Budgets and all-path work
**Source:** `canonical/budgets.py:18-65`.  
**Apply to:** kernel sweeps, Q-BPGD rounds, MBP4 updates, and aSCED paths.

Use the existing typed `WorkVector` categories and reserve/commit path. Record
work even for non-selected, invalid, exhausted, and terminal paths; document the
four-state unit meanings in the quaternary manifest/schema.

### Strict public preflight
**Sources:** `manifests.py:35-38,932-989`; `artifacts.py:94-152`.  
**Apply to:** public QBP manifests and CLI commands.

Validate closed policy combinations, schema, environment, artifact content and
semantic hash before sampling. Reject malformed probability rows, silent
normalization/smoothing, unsupported QBP compositions, and non-CSS aSCED there.

### Truth boundary and independent evaluation
**Sources:** `canonical/execution.py:67-82`; `evaluator.py:33-83`.  
**Apply to:** every policy and native comparison.

Policies get copied decoder-visible observation, priors, and state only. The
independent evaluator receives hidden truth after candidate selection and reports
the four established outcome names plus unavailable logical action when no basis
exists.

### Native reference isolation
**Source:** `reference.py:23-79`.  
**Apply to:** `native_asced.py` and bounded evidence integration.

The native identity, build, output, and metrics stay distinct. Missing native
instrumentation is evidence, never filled with inferred values.

## No Analog Found

| File/Capability | Role | Data Flow | Reason |
|---|---|---|---|
| Four-state scalar LLR BP4 recurrence | service | transform | No quaternary kernel exists; copy binary purity and lifecycle shape only. |
| Joint categorical Pauli sampler | service | request-response | Existing sampler draws independent X/Z bits and cannot preserve Y correlation. |
| General stabilizer Pauli evaluator | service | request-response | Existing evaluator is CSS-specific; retain outcome vocabulary and independent boundary only. |
| Source-defined MBP4 recurrence | service | event-driven | Existing memory policies are binary and cannot define MBP4. |
| CSS aSCED splitter/overcomplete construction | controller | event-driven | MBBP supplies lineage/selection patterns, not paper-specific splitter mathematics. |
| Pinned `quantum_asced` environment/driver | service | process I/O | Existing native adapters are Python SDK adapters; use only identity/missingness pattern. |

## Metadata

**Analog search scope:** `src/bp_registry`, `src/bp_registry/canonical`, `tests/canonical`, `tests`, `data/manifests`  
**Files scanned:** 24 tracked implementation/test/config files  
**Pattern extraction date:** 2026-10-06
