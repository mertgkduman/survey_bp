# Phase 4: Memory Policies and Relay-BP - Pattern Map

**Mapped:** 2026-09-24  
**Files analyzed:** 20 anticipated new or modified files  
**Analogs found:** 19 / 20

## File Classification

| New/Modified File | Role | Data flow | Closest tracked analog | Match quality |
|---|---|---|---|---|
| `src/bp_registry/canonical/memory.py` | service/policy | transform, stateful local-step | `canonical/updates.py` | role-match |
| `src/bp_registry/canonical/relay.py` | controller | sequential request-response | `canonical/execution.py` | role-match |
| `src/bp_registry/canonical/contracts.py` | model/config | validation | itself | exact extension |
| `src/bp_registry/canonical/compatibility.py` | utility | validation | `canonical/contracts.py` | role-match |
| `src/bp_registry/canonical/execution.py` | controller | streaming/event-driven | itself | exact extension |
| `src/bp_registry/canonical/budgets.py` | service | accounting/transform | itself | exact extension |
| `src/bp_registry/canonical/verification.py` | utility | transform | `canonical/verification.py` | exact extension |
| `src/bp_registry/native/relay_v022.py` | native-reference adapter | request-response | `reference.py` | role-match |
| `src/bp_registry/ledger.py` | ledger/model | append-only event-driven | itself | exact extension |
| `data/manifests/phase4-*.json` | config | file-I/O | `data/manifests/phase3-pilot-bb144.json` | role-match |
| `scripts/run_phase4_pilots.py` | controller/script | batch | `scripts/run_phase3_pilots.py` | exact role/flow |
| `scripts/execute_phase4_notebook.py` | utility/script | file-I/O | `scripts/execute_phase3_notebook.py` | exact role/flow |
| `notebooks/phase4-memory-relay-analysis.ipynb` | notebook | batch/analysis | `notebooks/phase3-pilot-analysis.ipynb` | role-match |
| `tests/canonical/test_memory_policies.py` | test | transform/stateful | `test_update_rules.py` | role-match |
| `tests/canonical/test_memory_composition.py` | test | validation/stateful | `test_contracts.py` | role-match |
| `tests/canonical/test_relay.py` | test | controller/event-driven | `test_schedule_semantics.py` | partial |
| `tests/canonical/test_relay_differential.py` | test | request-response/native | `tests/test_reference_smoke.py` | partial |
| `tests/canonical/test_phase4_evidence.py` | test | ledger/file-I/O | `tests/test_phase3_pilots.py` | role-match |
| existing Phase 3 pilot manifests/inventory | config/evidence | file-I/O | `artifacts.py` | partial |
| native v0.2.2 instrumentation branch | external source patch | event-driven | none in this repository | no analog |

All analog paths above are git-tracked (`git ls-files` checked). The implementation must not use `.gsd` mirrors as analogs.

## Pattern Assignments

### `canonical/memory.py`, `compatibility.py`, and `contracts.py`

**Analogs:** `src/bp_registry/canonical/updates.py`, `src/bp_registry/canonical/contracts.py`, and `tests/canonical/test_update_rules.py`.

Use strict frozen Pydantic data models for persisted specifications; use immutable dataclasses for resolved runtime state. Reuse Phase 3's assignment/refresh transaction rather than a global RNG or eager mutation. Extend the closed policy registry and preserve old V2/V3 readers exactly. A composition must retain every binding ID, target, ordered position, history-advance boundary, lifetime, refresh/reset behavior, source evidence, graph identity, and resolved assignment.

**Strict persisted model** — `contracts.py:17-19,76-99`:
```python
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)

class PolicySpec(_Strict):
    kind: str = Field(min_length=1, max_length=64)
    binding_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    state_lifetime: Literal["shot", "search", "member", "leg", "branch", "attempt", "iteration", "message"]
```

**Closed ownership and deterministic identity** — `contracts.py:308-367`:
```python
if spec.binding_id in binding_ids:
    raise ValueError(f"duplicate binding_id {spec.binding_id!r}")
overlap = owned_state.intersection(spec.owned_state)
if overlap:
    raise ValueError(f"owned state overlaps across bindings: {sorted(overlap)!r}")
...
encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
return ResolvedComposition(tuple(bindings), hashlib.sha256(encoded.encode("utf-8")).hexdigest())
```

**Seeded, graph-bound assignment with admission before state advance** — `updates.py:180-228` as tested in `test_update_rules.py:180-228`:
```python
denied = plan.refresh(initial, boundary="source_iteration", ..., budgets=_Budget(False), budget_scope="attempt")
assert not denied.admitted and denied.state == initial and denied.assignment is None
first = plan.refresh(initial, boundary="source_iteration", ..., budgets=_Budget(), budget_scope="attempt")
replay = plan.refresh(initial, boundary="source_iteration", ..., budgets=_Budget(), budget_scope="attempt")
assert first.admitted and first.assignment == replay.assignment
```

**Integration guidance:** Create an ordered *collection* of memory bindings rather than overloading the existing single `state_memory` role. `validate_composition` is the admission point: reject undefined target/update/schedule/history-boundary combinations with a persisted reason. Ensure each source-named preset resolves to its explicit order; never infer a global default. Reuse `ParameterGeneratorSpec`/`ParameterRefreshPlan` concepts for disordered values, but add decoder-local identity and resolved per-leg values to the Phase 4 evidence grammar.

### `canonical/relay.py` and `canonical/execution.py`

**Analogs:** `src/bp_registry/canonical/execution.py`, `canonical/lineage.py`, `canonical/schedules.py`.

Build Relay as an engine-owned sequential leg controller. Each leg gets its own lineage node, fresh message/history state, its declared update/schedule procedure, explicit per-leg work leaves, and a candidate record. Transfer only a versioned finite posterior payload after a committed terminal leg. Freeze source-score selection before calling the independent evaluator.

**Engine opens a shot with composition identity and ledger context** — `execution.py:619-669`:
```python
parsed = parse_canonical_manifest(manifest)
resolved = validate_composition(parsed.policies)
PolicyRuntime(resolved).traverse_lifecycle()
budgets = _budget_tree(execution_controls)
...
ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=sample_seed_identity, **common)
attempt_id = _attempt_lineage_id(working, attempt_ordinal)
ledger.event(..., kind="attempt", data={**common, "attempt_lineage_id": attempt_id.value, ...})
```

**Reservation precedes mutation** — `execution.py:747-758` and `budgets.py:387-414`:
```python
attempt_reservation = budgets.reserve("attempt", WorkVector(bp_calls=1), leaf_id=f"attempt:{shot_id}:bp-call")
if attempt_reservation is None:
    termination = budgets.last_termination
    terminal_with_work(termination.reason, budget_termination=_termination_evidence(termination), ...)
    return CanonicalExecutionResult(...)
attempt_reservation.commit_once()
```

**Typed leg/candidate ancestry and frozen selection** — `lineage.py:28-40,196-246`:
```python
"leg": frozenset({"member", "leg"}),
"candidate": frozenset({"working", "attempt", "branch", "leg"}),
...
if tuple(sorted(candidates, key=lambda item: (item.local_ordinal, item.lineage_id.value))) != candidates:
    raise ValueError("candidate selection must use declared stable order")
node = graph.append_node("selection", {...}, parent=selected_id, relation="select")
```

**Integration guidance:** keep `run_canonical_structural_shot` as the public route and factor a leg executor from its existing schedule branches. The Relay controller should not duplicate `EdgeTable`, update rules, candidate evaluation, or budget code. It must reset C2V/V2C/current iteration/memory history as declared, retain only real posterior LLR through a transfer, implement first-on-equal-score selection, and never receive hidden truth.

### `contracts.py`, `ledger.py`, and `verification.py`: real posterior transfer and evidence

**Analogs:** `RelayPayload` in `contracts.py`, canonical structural events in `ledger.py`, and hash-linked lineage in `lineage.py`.

Replace the binary-only `RelayPayload` deliberately with a new versioned kind while maintaining the old reader. The payload needs representation ID, finite float64 vector, length, producer leg lineage, numerical-profile ID, clipping/saturation evidence, and SHA-256. `SearchPlan` must admit it only for relayed relationships.

**Existing narrow transfer gate** — `contracts.py:256-290`:
```python
class RelayPayload(_Strict):
    kind: Literal["canonical-relay-v1"]
    values: tuple[int, ...] = Field(min_length=1)
...
if self.relationship is SearchRelationship.RELAYED and self.relay_payload is None:
    raise ValueError("relayed relationships require a registered relay payload")
```

**Versioned append-only event contract** — `ledger.py:386-442,506-571`:
```python
_CANONICAL_EVENT_KINDS = frozenset({..., "relay_transfer", "candidate", "selection", ...})
...
event["event_id"] = _canonical_event_id(event)
_validate_canonical_event(event)
...
handle.write(_canonical_event_bytes(event).decode("utf-8") + "\n")
handle.flush()
os.fsync(handle.fileno())
```

**Integration guidance:** do not broaden a legacy ledger grammar in place. Add a Phase 4 structural version and exact deterministic terminal reconstruction in `canonical/verification.py`; preserve older grammar behavior. Emit `relay_transfer` with payload digest/shape/producer and one `relay_transfers` work leaf only after handoff commits. Use `trace_link` and `trace_truncated` events with confined hash-linked sidecars for bounded posterior/history and leg traces.

### `canonical/budgets.py`

**Analog:** `src/bp_registry/canonical/budgets.py:356-445`.

Use the existing hierarchical `BudgetTree`; add named Phase 4 work dimensions and per-leg parent scopes rather than a single Relay iteration total. The atomic reservation pattern supports the requirement that denied memory refreshes leave target/history/RNG/cursor unchanged.

```python
if leaf_id in self._leaves or leaf_id in self._pending:
    raise ValueError("leaf work IDs must be unique")
...
if ... > limit.limit:
    self._last_termination = BudgetTermination(..., reason="count_budget_exhausted")
    return None
...
if commit:
    self._leaves[reservation.leaf_id] = _LeafEvent(...)
```

### `native/relay_v022.py`

**Analog:** `src/bp_registry/reference.py:16-112`.

Model the adapter as a strict source-pinned envelope that consumes decoder-visible matrix/syndrome/prior only, validates shapes/types, returns observed fields, and reports inaccessible native internals as typed unavailable facts. Keep author v0.2.2, the local fork, and any instrumentation patch as separate identities/config translations.

```python
@dataclass(frozen=True)
class NativeResult:
    candidate: np.ndarray
    converged: bool
    iterations: int
    metric_facts: tuple[MetricFact, ...] = ()
...
if raw_h.ndim != 2 or raw_s.shape != (raw_h.shape[0],):
    raise ValueError("check matrix and syndrome dimensions disagree")
```

**No exact repository analog** exists for a pinned foreign-worktree observer patch. Keep that patch outside canonical source, pin exact commit/diff digest, and require unmodified-versus-patched fixture equivalence before trusting extra facts.

### Phase 4 manifests, pilots, and notebook

**Analogs:** `scripts/run_phase3_pilots.py`, `scripts/execute_phase3_notebook.py`, `notebooks/phase3-pilot-analysis.ipynb`, and Phase 3 manifest files.

The Phase 4 runner should create identified manifests, preflight, run only through the public command boundary, independently verify every run, preserve all events/results, and explicitly prove a rejected undefined configuration. It must use immutable calibration/evaluation sample namespaces, retain incomplete outcomes, include native/canonical identity separately, and reconcile B1's semantic digest before admission.

**Public batch runner and transparent result aggregate** — `run_phase3_pilots.py:127-189`:
```python
_json_command(repository_root, "preflight", str(manifest_path))
_json_command(repository_root, "canonical", str(manifest_path), "--output", str(run_output))
verified.append(_json_command(repository_root, "verify-run", str(run_output)))
...
if not matched or any(item["relation"] != "pilot_adaptation" ... for item in terminals):
    raise ValueError("pilot terminal identity or transparent assessment label drifted")
```

**Notebook environment/confined execution** — `execute_phase3_notebook.py:36-65,82-105`:
```python
expected = repository_root / ".venv" / "bin" / "python"
if actual.resolve() != expected.resolve():
    raise RuntimeError(...)
source = _confined_path(repository_root, input_path, required_parent=notebook_root)
destination = _confined_path(repository_root, output_path, required_parent=result_root)
...
environment["MPLBACKEND"] = "Agg"
```

**Integration guidance:** Phase 4 differs because its notebook may invoke identified stages when compatible evidence is absent. Preserve the Phase 3 digest/identity guard, then add compatibility keys for manifest, source/policy, code/environment, sample namespace, and stage. The notebook must expose all tuning candidates, uncertainty, caps, failures/inconclusive runs, fresh evaluation, paired disagreements, traces, and work/runtime tails; do not overwrite mismatched prior evidence.

### Tests

**Analogs:** `tests/canonical/test_update_rules.py`, `test_contracts.py`, `test_schedule_semantics.py`, `test_work_accounting.py`, `tests/test_phase3_pilots.py`.

Follow the existing independent-oracle style: hand-calculated endpoint fixtures, frozen strict-schema rejection tests, and byte-identical denial tests. Keep phase-specific tests in new files rather than weakening broad legacy expectations.

**Exact equation and denial pattern** — `test_update_rules.py:37-49,52-80`:
```python
assert update.check_to_variable(incoming, syndrome=syndrome) == expected
with pytest.raises(Exception, match="nonfinite"):
    update.check_to_variable(np.asarray([np.inf]), syndrome=0)
...
assert result.admitted is False
np.testing.assert_array_equal(messages, np.asarray([1.0, -2.0]))
assert progress == ScheduleProgress(...)
```

**Persisted contract/replay pattern** — `test_contracts.py:48-72,130-145`:
```python
assert parsed.model_dump_json() == contracts.parse_canonical_manifest(
    json.loads(parsed.model_dump_json())
).model_dump_json()
with pytest.raises(ValueError, match="known policy kind"):
    contracts.parse_canonical_manifest(unknown)
```

**Phase 4 test allocation:**

- `test_memory_policies.py`: source equations, endpoints, target operands, history/reset boundaries, EWA/Relay reparameterization.
- `test_memory_composition.py`: order, repeated kinds/binding ownership, compatibility rejection, seeded draw replay, refresh retain/reset, denied atomic state.
- `test_relay.py`: leg initialization, posterior-only transfer, source/canonical presets, stable tie selection, candidate lineage, per-leg work.
- `test_relay_differential.py`: exact v0.2.2 translation, instrumented/unmodified terminal equivalence, unavailable native facts.
- `test_phase4_evidence.py`: payload/ledger reconstruction, sidecar caps/missingness, artifact gate, sample separation, notebook stage reuse/mismatch behavior.

## Shared Patterns

### Validation and schema evolution
**Sources:** `contracts.py:17-19,308-367`; `artifacts.py:94-153`.

Use `extra="forbid"`, finite values, closed version dispatch, explicit graph/digest checks, and new versions rather than reinterpreting saved data.

### Atomic state and work accounting
**Sources:** `budgets.py:387-445`; `execution.py:747-758`; `test_update_rules.py:52-80`.

Compute proposed output/state/evidence first, reserve total work, validate, then commit all target/history/RNG/cursor together. On rejection, record termination but retain every owned state unchanged.

### Provenance and truth boundary
**Sources:** `lineage.py:160-164,196-246`; `execution.py:891-907`.

Create leg/candidate/selection lineage from decoder-visible values; call the evaluator only after the frozen selection. Native references report observations and missingness rather than manufactured internals.

### Ledger and sidecars
**Sources:** `ledger.py:395-442,506-571`.

Use stable content IDs, finite canonical JSON, one open shot owner, durable append, and only relative hash-linked sidecars. Bound trace bytes/records and emit explicit truncation/missingness.

## No Analog Found

| File/responsibility | Role | Data flow | Reason |
|---|---|---|---|
| Exact author v0.2.2 Relay instrumentation branch | external native patch | event-driven | Current native adapter covers opaque `ldpc` only; no pinned foreign observer-patch pattern exists. |

## Metadata

**Analog search scope:** `src/bp_registry/canonical`, `src/bp_registry`, `tests/canonical`, `tests`, `scripts`, `notebooks`, and `data/manifests`  
**Files scanned:** 18 primary source/test artifacts plus upstream context and research  
**Pattern extraction date:** 2026-09-24
