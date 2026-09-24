# Phase 3: Update Rules and Scheduling - Pattern Map

**Mapped:** 2026-09-23  
**Files analyzed:** 13 planned new or modified files  
**Analogs found:** 11 / 13

All named analogs below were checked with `git ls-files`; they are tracked repository sources (not runtime or install mirrors).

## File Classification

| New/Modified File | Role | Data Flow | Closest Tracked Analog | Match Quality |
|---|---|---|---|---|
| `src/bp_registry/canonical/updates.py` | service / policy implementation | transform | `src/bp_registry/canonical/kernel.py` | role-match |
| `src/bp_registry/canonical/contracts.py` | model / config validation | request-response | `src/bp_registry/canonical/contracts.py` | exact |
| `src/bp_registry/canonical/schedules.py` | service / schedule executor | event-driven | `src/bp_registry/canonical/schedules.py` | exact |
| `src/bp_registry/canonical/residual.py` | service / stateful cache | event-driven | `src/bp_registry/canonical/schedules.py` | role-match |
| `src/bp_registry/canonical/cluster_schedule.py` | service / artifact-backed schedule | file-I/O + event-driven | `src/bp_registry/artifacts.py` | partial |
| `src/bp_registry/canonical/execution.py` | controller / lifecycle executor | event-driven | `src/bp_registry/canonical/execution.py` | exact |
| `src/bp_registry/canonical/budgets.py` | model / utility | transform | `src/bp_registry/canonical/budgets.py` | exact |
| `src/bp_registry/runner.py` | controller / pilot integration | request-response | `src/bp_registry/runner.py` | exact |
| `tests/canonical/test_update_rules.py` | test | transform | `tests/canonical/test_numerics.py` | role-match |
| `tests/canonical/test_schedule_semantics.py` | test | event-driven | `tests/canonical/test_flooding.py` | role-match |
| `tests/canonical/test_residual_schedule.py` | test | event-driven | `tests/canonical/test_budgets.py` | role-match |
| `tests/canonical/test_cluster_schedule.py` | test | file-I/O + event-driven | `tests/test_source_artifact.py` | role-match |
| `notebooks/phase3-pilot-analysis.ipynb` | analysis / presentation | batch | — | none |

## Pattern Assignments

### `src/bp_registry/canonical/updates.py` (policy implementation, transform)

**Analog:** `src/bp_registry/canonical/kernel.py`

Preserve kernel operations as small deterministic functions with numerical behavior delegated to `numerics.py`.  Add MS/NMS/OMS as a check-message policy or kernel implementation; do not put schedule state or hidden truth in this module.

**Imports and pure-operation pattern** ([kernel.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/kernel.py:1-12), [lines 26-52](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/kernel.py:26)):

```python
class BinarySpaKernel:
    def check_message(self, incoming: np.ndarray, syndrome: int) -> float:
        return check_to_variable(incoming, syndrome=syndrome)

    def variable_message(self, belief: float, check_message: float) -> float:
        return float(finite_saturate(belief - check_message, boundary="variable_update"))

    def candidate_from_beliefs(self, beliefs: np.ndarray) -> np.ndarray:
        return hard_decision(beliefs)
```

**Apply:** resolve scalar, iteration, check, and edge assignments against `EdgeTable` before the local update.  Validate finite nonnegative normalization/offset values before committing a plan; retain the existing degree-one and saturation conventions from `numerics.py`.

### `src/bp_registry/canonical/contracts.py` (model/config validation, request-response)

**Analog:** `src/bp_registry/canonical/contracts.py`

New update and schedule kinds, parameter-generator specifications, refresh scope, source/adaptation labels, and evidence must remain strict frozen persisted data.  Extend the closed registry and validator together.

**Strict-model and closed-registry pattern** ([contracts.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/contracts.py:15), [lines 60-80](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/contracts.py:60)):

```python
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)

_POLICY_KINDS: dict[PolicyRole, frozenset[str]] = {
    PolicyRole.UPDATE: frozenset({"identity", "binary_spa"}),
    PolicyRole.SCHEDULE: frozenset({"identity", "flooding"}),
}

class PolicySpec(_Strict):
    kind: str = Field(min_length=1, max_length=64)
    binding_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
```

**Composition rejection pattern** ([contracts.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/contracts.py:225)):

```python
if spec.kind not in _POLICY_KINDS[role]:
    raise ValueError(f"unknown policy kind {spec.kind!r}; expected a known policy kind for {role.value}")
```

**Tests to copy:** `tests/canonical/test_contracts.py:55-65` creates valid evidence and asserts invalid persisted data is rejected with `pytest.raises`.

### `src/bp_registry/canonical/schedules.py` (schedule executor, event-driven)

**Analog:** `src/bp_registry/canonical/schedules.py`

Keep `EdgeTable` as the one graph-indexed identity source.  Implement layer, CN serial, VN serial, randomized traversal, and source-defined order plans here only where they share order/state semantics; put residual and imported-cluster state in their dedicated modules.

**Canonical identity and immutable proposal pattern** ([schedules.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/schedules.py:18), [lines 82-103](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/schedules.py:82)):

```python
@dataclass(frozen=True, slots=True)
class EdgeTable:
    """The canonical check-major, variable-minor edge identity for one graph."""
    check_count: int
    variable_count: int
    edges: tuple[Edge, ...]

@dataclass(frozen=True, slots=True)
class FloodingSweep:
    edge_count: int
    old_v2c: np.ndarray
    check_to_variable: np.ndarray
    new_v2c: np.ndarray
    beliefs: np.ndarray
    candidate: np.ndarray
    proposed_work: FloodingWork
```

**Fresh/stale buffer discipline** ([schedules.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/schedules.py:123)):

```python
old_snapshot = np.array(old, dtype=np.float64, copy=True)
for check, edge_indices in enumerate(self._check_edges):
    for edge_index in edge_indices:
        incoming = old_snapshot[[other for other in edge_indices if other != edge_index]]
        c2v[edge_index] = self.kernel.check_message(incoming, int(syndrome_bits[check]))
```

**Apply:** every new local unit must explicitly name which messages are read stale and which newly committed values later units may read.  Emit its exact `WorkVector` proposal and cursor/progress without mutating schedule state.

### `src/bp_registry/canonical/residual.py` (stateful cache, event-driven)

**Analog:** `src/bp_registry/canonical/schedules.py` and `src/bp_registry/canonical/budgets.py`

Use `EdgeTable` position for the sole deterministic equal-residual tie break.  Expose a non-mutating next-selection/proposed-work result, including the mandatory post-unit convergence-check work, then invalidate only the source-specified dependency set on commit.  Never let a rejected budget reservation consume an order, cache, RNG draw, or priority mutation.

**Edge identity source** ([schedules.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/schedules.py:18)):

```python
"""The canonical check-major, variable-minor edge identity for one graph."""
```

**Atomic leaf reservation to use for each selected residual** ([budgets.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/budgets.py:193), [lines 253-270](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/budgets.py:253)):

```python
step_reservation = self.budgets.reserve(self.scope, proposed_step, leaf_id=leaf_id)
if step_reservation is None:
    return terminal
check_reservation = self.budgets.reserve(self.scope, proposed_check, leaf_id=check_leaf_id)
if check_reservation is None:
    step_reservation.rollback()
    return terminal
try:
    next_state = compute_without_mutation(state)
    evaluate_convergence(next_state)
    step_reservation.commit_once()
    check_reservation.commit_once()
except Exception:
    if step_reservation.active:
        step_reservation.rollback()
    if check_reservation.active:
        check_reservation.rollback()
    raise
```

This is the required composition of existing `Reservation` semantics with a new local-step proposal: reserve both mandatory leaves before a state mutation, calculate into temporary state, perform convergence, then commit state and both leaves only when all work succeeds.  An implementation may instead reserve one combined leaf only if the full atomic-work evidence remains separately recoverable.

### `src/bp_registry/canonical/cluster_schedule.py` (artifact-backed service, file-I/O + event-driven)

**Analog:** `src/bp_registry/artifacts.py` (strict provenance and artifact identity) plus `src/bp_registry/canonical/schedules.py` (local unit).

**Required pattern:** accept only a pinned, non-executable artifact whose hash, graph identity, dtype, finite values, dimensions, partition membership, and state/action encoding pass before scheduling.  The artifact-unavailable case must be an explicit unsupported/blocked terminal, never a synthetic Q-table or generic partition.  This is a partial analog because no current source implements learned schedule artifacts.

**Confined, versioned loader pattern** ([artifacts.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/artifacts.py:94)):

```python
artifact = _confined_file(root, relative_path)
if artifact.stat().st_size > max_bytes:
    raise ValueError("artifact exceeds size limit")
raw_bytes = artifact.read_bytes()
raw_digest = hashlib.sha256(raw_bytes).hexdigest()
if expected_raw_sha256 is not None:
    if raw_digest != _require_digest(expected_raw_sha256, "expected raw SHA-256"):
        raise ValueError("raw SHA-256 does not match artifact bytes")
```

**Integration seam:** return the same local-step proposal shape consumed by the generic executor, with a greedy source-defined cluster unit and declared work.  Do not add training or a selector-variant registry in Phase 3.

### `src/bp_registry/canonical/execution.py` (lifecycle executor, event-driven)

**Analog:** `src/bp_registry/canonical/execution.py`

Generalize `AtomicFloodingExecutor`, retaining its reserve-before-calculation and terminal evidence behavior.  Before any local state mutation, the generic loop must reserve both the *local* unit and its mandatory following convergence-check work; it then calculates into copies, checks convergence, and commits the corresponding leaves/state together.

**Existing atomic lifecycle** ([execution.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/execution.py:130), [lines 149-171](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/execution.py:149)):

```python
for iteration in range(1, max_iterations + 1):
    proposed = WorkVector.from_flooding_counts(
        edge_count=self.schedule.edge_table.edge_count,
        variable_count=self.schedule.edge_table.variable_count,
    )
    reservation = self.budgets.reserve(self.scope, proposed, leaf_id=f"{self.scope}:flooding:{iteration}")
    if reservation is None:
        return AtomicFloodingResult(state, iteration - 1, self.budgets.last_termination, last_sweep)
    try:
        sweep = self.schedule.sweep(state, syndrome, error_rate=error_rate)
```

**Terminal evidence seam** ([execution.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/execution.py:419)):

```python
"qualified_iterations": {
    "count": data.get("iterations", 0), "schedule": "flooding",
    "atomic_unit": "complete_double_buffered_sweep",
},
"work_vector": work.as_evidence(),
```

Replace the flooding literals with schedule-supplied progress: source iteration, atomic local-unit name, completed traversals, local cursor, and stopping adaptation.  Keep hidden truth outside the executor’s policy/schedule capability views.

### `src/bp_registry/canonical/budgets.py` (work model, transform)

**Analog:** `src/bp_registry/canonical/budgets.py`

Add separate nonnegative fields for convergence checks, order generation/selection, residual C2V precomputation, and priority maintenance.  Update `zero`, `sum`, evidence serialization, resource validation, manifests, and all exact-dictionary fixtures as one schema migration.

**Field and qualified-iteration pattern** ([budgets.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/budgets.py:19), [lines 71-86](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/budgets.py:71)):

```python
class WorkVector:
    check_to_variable_updates: int = 0
    variable_to_check_updates: int = 0
    belief_assemblies: int = 0
    residual_priority_evaluations: int = 0
    bp_calls: int = 0

class QualifiedIteration:
    count: int
    schedule: str
    atomic_unit: str

    def as_evidence(self) -> dict[str, int | str]:
        return {"count": self.count, "schedule": self.schedule, "atomic_unit": self.atomic_unit}
```

**Tests to copy:** `tests/canonical/test_work_accounting.py:25-43` asserts the complete evidence dictionary including zeroes and rejects negative counts. `tests/canonical/test_budgets.py:144-157` verifies an exception rolls back both the reservation and message state.

### `src/bp_registry/runner.py` (pilot integration, request-response)

**Analog:** `src/bp_registry/runner.py` and `tests/test_sampling.py`

Integrate only via validated manifests and the canonical structural-shot entry point.  Preserve the physical sample identity while deriving parameter-assignment, schedule-order, and cluster-partition identities from separate persisted purpose labels.  B1 and HGP pilot artifact metadata must retain actual GF(2) rank (do not claim a generated `9 x 12` Gallager constituent is full-row-rank) plus construction/order/hash provenance.

**Preflight and compact decoder boundary** ([runner.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/runner.py:118), [lines 148-169](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/runner.py:148)):

```python
if not isinstance(manifest, CanonicalExperimentV2):
    raise ValueError("canonical execution requires a strict CanonicalExperimentV2 manifest")
composition = validate_executable_canonical_baseline(manifest.policies)

return {
    "max_iterations": manifest.budgets.attempt.max_iterations,
    "error_rate": manifest.error_rate,
    "policies": manifest.policies.model_dump(mode="json"),
}
```

**Sample replay oracle** ([tests/test_sampling.py](/hpc/group/pfisterlab/mg551/storage/survey_bp/tests/test_sampling.py:35)):

```python
first = sampler(code, manifest_identity="a" * 64, shot_id=9, seed=1, x_error_rate=0.4)
replay = sampler(code, manifest_identity="a" * 64, shot_id=9, seed=99, x_error_rate=0.4)
assert first.sample_identity == replay.sample_identity
assert (first.hidden_x == replay.hidden_x).all()
```

Pilot scheduling/parameter seeds must be tested by changing their realized policy evidence while asserting this physical sample identity and syndrome remain unchanged.

### New canonical test files (tests)

**Analogs:** `tests/canonical/test_numerics.py`, `tests/canonical/test_flooding.py`, `tests/canonical/test_budgets.py`, and `tests/test_source_artifact.py`.

Use direct imports inside tests and compact explicit graph fixtures, as current canonical tests do.  Tests should compare actual arrays with `np.testing`, test invalid inputs with `pytest.raises`, and use monkeypatch only at an explicit seam to prove rollback.

| File | Copy from | Required focused cases |
|---|---|---|
| `test_update_rules.py` | `test_numerics.py` | MS sign/minimum and degree-one oracle; NMS/OMS scalar, graph-indexed, generated and refreshed assignments; saturation and invalid finite/domain inputs |
| `test_schedule_semantics.py` | `test_flooding.py` | declared layer membership/order; CN/VN fresh-vs-stale visibility; three randomized refresh scopes; local convergence and partial cursor evidence |
| `test_residual_schedule.py` | `test_budgets.py:144-157` | cache equals full recomputation after each unit; canonical-edge tie; exact leaf work; no state/RNG/cache mutation after denied reservation |
| `test_cluster_schedule.py` | `test_source_artifact.py` | hash/shape/dtype/finiteness/graph compatibility rejection; greedy local unit; missing artifact fails closed |

### `notebooks/phase3-pilot-analysis.ipynb` (analysis, batch)

**No close code analog exists.** Use the tracked ledger/result conventions as its input contract and write generated tables/plots from retained evidence.  Keep the notebook runnable and label all outputs `pilot`/`adaptation` with assessment status; it must show outcomes, convergence, qualified iterations, raw work, setup/decode runtime, and bounded traces.  Do not make it an alternate decoder implementation.

## Shared Patterns

### Closed persisted policy configuration

**Source:** `src/bp_registry/canonical/contracts.py:15-17, 60-80, 225-269`  
**Apply to:** update-rule parameters, schedule specs, random-refresh rules, source/adaptation metadata, and cluster artifact references.

Use frozen Pydantic models with `extra="forbid"`, finite numeric validation, a closed supported-kind registry, and explicit evidence/invariants.  Persist data, never import paths or callables from a manifest.

### Canonical graph identity and schedule visibility

**Source:** `src/bp_registry/canonical/schedules.py:18-60, 106-165`  
**Apply to:** all edge/check/variable-specific parameters, residual tie breaking, layer/serial traversal, and replay evidence.

`EdgeTable` has stable check-major/variable-minor ordering.  Explicitly copy/read buffers for each local update so a schedule’s fresh/stale semantics are inspectable rather than incidental.

### Work reservation, rollback, and local convergence

**Source:** `src/bp_registry/canonical/budgets.py:193-219, 253-270`; `src/bp_registry/canonical/execution.py:149-171`  
**Apply to:** every schedule setup and decoding leaf.

Reserve both the exact local work and its mandatory convergence-check work before mutation; each reservation commits once or rolls back.  Commit the convergence-check leaf after the check completes, with the local state and work leaves consistently committed only after the full local unit succeeds.  A denied reservation must leave decoder, schedule, cache, and RNG state unchanged.

### Truth boundary and independent randomness

**Source:** `src/bp_registry/canonical/execution.py:49-74`; `tests/test_sampling.py:35-46`  
**Apply to:** parameter generation, schedule randomization, residual/cluster tie identity, pilots, and tests.

Policies receive decoder-visible state only.  Parameter and schedule streams use distinct persisted identities; sampling remains independently replayable for matched comparisons.

### Exact evidence dictionaries

**Source:** `tests/canonical/test_work_accounting.py:25-43`; `src/bp_registry/canonical/execution.py:419-434`  
**Apply to:** `WorkVector`, terminal ledger payloads, manifests, result fixtures, tables, and notebook parsing.

When the work schema or terminal schedule metadata changes, migrate every exact expected dictionary and preserve explicit zero values and qualified units.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `notebooks/phase3-pilot-analysis.ipynb` | analysis / presentation | batch | Repository has no tracked notebook; derive inputs from ledger/result evidence rather than creating a new execution path. |
| `src/bp_registry/canonical/cluster_schedule.py` artifact loader portion | service | file-I/O | No tracked learned-policy artifact loader exists; use strict existing artifact provenance conventions and fail closed. |

## Metadata

**Analog search scope:** `src/bp_registry/canonical/`, `src/bp_registry/`, `tests/canonical/`, `tests/`, `data/`, `docs/`  
**Tracked source files inspected:** 16  
**Pattern extraction date:** 2026-09-23
