# Phase 05: Guided and Perturbative BP Interventions - Pattern Map

**Mapped:** 2026-09-30  
**Files analyzed:** 25 anticipated new or modified files  
**Analogs found:** 24 / 25

## File Classification

| New/Modified File | Role | Data flow | Closest tracked analog | Match quality |
|---|---|---|---|---|
| `src/bp_registry/canonical/interventions.py` | policy/service | event-driven transform | `canonical/memory.py` | role-match |
| `src/bp_registry/canonical/transformations.py` | model/utility | transform | `canonical/problems.py` | role-match |
| `src/bp_registry/canonical/intervention_session.py` | service | stateful streaming | `canonical/memory_execution.py` | role-match |
| `src/bp_registry/canonical/guided_decimation.py` | controller | stateful request-response | `canonical/relay.py` | role-match |
| `src/bp_registry/canonical/impulse.py` | controller | branching request-response | `canonical/relay.py` | partial |
| `src/bp_registry/canonical/restarting.py` | controller | branching request-response | `canonical/relay.py` | partial |
| `src/bp_registry/canonical/problems.py`, `kernel.py` | model/kernel | transform, streaming | themselves | exact extension |
| `src/bp_registry/canonical/{contracts,execution,budgets,verification}.py` | config/controller/accounting/verifier | validation, event-driven | themselves | exact extension |
| `src/bp_registry/{manifests,ledger,cli,runner}.py` | public config/ledger/controller | file-I/O, event-driven | themselves | exact extension |
| `src/bp_registry/phase5_analysis.py` | analysis utility | batch transform | `phase4_analysis.py` | exact role |
| `data/manifests/phase5-*.json` | config | file-I/O | `data/manifests/phase4-memory-relay-b1.json` | role-match |
| `docs/evidence/phase5-source-decisions.json` | evidence config | file-I/O | `docs/evidence/phase5-source-status-20260926.json` | exact role |
| `scripts/{run,execute,preview}_phase5_*.py` | batch/notebook controller | batch, file-I/O | `scripts/{run_phase4_pilots,execute_phase4_notebook,preview_phase4_notebook}.py` | role-match |
| `notebooks/phase5-interventions-analysis.ipynb` | notebook | batch analysis | `notebooks/phase4-memory-relay-analysis.ipynb` | role-match |
| `tests/canonical/test_{guided_decimation,impulse,perturbative_interventions,restart_execution}.py` | test | stateful transform/controller | `tests/canonical/test_relay.py` | role-match |
| `tests/{test_phase5_public_execution,test_phase5_notebook}.py` | integration test | file-I/O, request-response | `tests/canonical/test_phase4_notebook.py` | role-match |

All named analogs are tracked sources: checked with `git ls-files`. No `.gsd` mirror is used.

## Pattern Assignments

### Intervention contracts, transformations, and session

**Apply to:** `canonical/interventions.py`, `transformations.py`, `intervention_session.py`, and extensions to `problems.py` and `kernel.py`.

**Analogs:** `src/bp_registry/canonical/problems.py:11-67`, `kernel.py:50-92`, `memory.py:102-125`, and `memory_execution.py:257-277`.

**Immutable binary values and stable candidate order** (`problems.py:11-17,52-67`):

```python
copied = np.array(array, dtype=np.uint8, copy=True)
copied.setflags(write=False)
...
return min(candidates, key=lambda candidate: (candidate.local_order, candidate.lineage_id), default=None)
```

Keep `OriginalProblem` immutable. Make each transformed working view carry ordered maps, its transformation/lift certificate, and a lineage edge. A lifted candidate must be an original-coordinate immutable `OriginalSpaceCandidate`; choose minimum weight and declared order before any hidden-truth evaluation.

**Vector-prior kernel seam** (`kernel.py:50-63`):

```python
prior_values = np.asarray(prior, dtype=np.float64)
if prior_values.ndim == 0:
    beliefs = np.full(variable_count, float(prior_values), dtype=np.float64)
elif prior_values.shape == (variable_count,):
    beliefs = np.array(prior_values, dtype=np.float64, copy=True)
else:
    raise ValueError("prior must be scalar or have one value per variable")
```

Factor the flooding initialization in `BinarySpaKernel.run()` into explicit session construction and whole-round continuation. Session operations must separately expose fresh reset, prior mutation, posterior mutation, and commit; do not infer resets from attempt boundaries.

**Propose then commit owned state** (`memory.py:105-125`, `memory_execution.py:271-277`):

```python
proposal = policy.propose(state.field, value, boundary="source_iteration")
...
if sweep.owner is not self._owner or sweep.revision != self._revision:
    raise ValueError("memory commit received a foreign or stale sweep")
self._histories = sweep.histories
self._revision += 1
```

Use immutable proposals containing trigger, variant, target order, requested mutation, reset/preserved fields, and anticipated work. Commit only after authorization. This supports BPGD continuation, freezing lifetime/release, sign-flip message continuation, and restart branch reset without a generic restart loop.

**Algebra oracle to preserve independently** (`tools/validate_intervention_design.py:37-61,65-80`):

```python
residual = tuple(a ^ b for a, b in zip(syndrome, contribution, strict=True))
shortened = tuple(tuple(row[i] for i in free) for row in matrix)
...
working_valid = product(shortened, candidate) == residual
original_valid = product(matrix, lifted) == syndrome
if working_valid != original_valid:
    raise AssertionError("shortening equivalence failed")
```

Implement shortening/fixation and syndrome-flip certificate lifts in production NumPy code, while retaining the oracle as an independent test authority. Finite LLR bias and algebraic fixing must be distinct operators.

### BPGD, impulse, freezing/flips, and restarting controllers

**Apply to:** `guided_decimation.py`, `impulse.py`, `interventions.py`, and `restarting.py`.

**Analog:** `src/bp_registry/canonical/relay.py:426-465,489-509` and `canonical/execution.py:730-770`.

**Reserve before mutating or branching** (`relay.py:442-465`):

```python
transfer_reservation = budgets.reserve(
    scope, WorkVector(relay_transfers=1), leaf_id=transfer_leaf_id,
)
if transfer_reservation is None:
    return finish("budget_exhausted", "budget_exhausted")
prior = previous.as_array()
...
transfer_reservation.commit_once()
```

For each decimation round, fresh impulse attempt, freeze period, syndrome test, sign action, or restart residual solve: construct a private proposal, reserve its complete leaf work, then mutate/construct the child. Denied work must produce terminal evidence and retain the parent state exactly.

**Explicit state reset boundary** (`relay.py:489-503`):

```python
# Each leg resets C2V/V2C state to channel priors.
messages = np.asarray([base_prior[variable] for _check, variable in edge_table.edges], dtype=np.float64)
posterior = np.array(prior, dtype=np.float64, copy=True)
schedule = FloodingSchedule(edge_table, kernel=prior_kernel, profile=kernel.profile)
```

Use this shape for fresh impulse/BP-SF/restart branches. BPGD and posterior sign flip must instead invoke the session continuation operation and record their preserved buffers. Controller inputs must remain decoder-visible; only `execution.py` evaluates a selected original-space candidate.

**Stable selection and truth boundary** (`execution.py:747-769`):

```python
selected = select_stable_candidate((OriginalSpaceCandidate(candidate_id.value, working, candidate, 0),))
...
# This is the first use of hidden truth; the controller and selection never receive it.
evaluation_result = evaluate(validated, true_x=hidden_truth.x, true_z=hidden_truth.z,
                             candidate_x=selected.candidate)
```

Use declared test/index order for ties and first-success, never worker arrival order. Lift and validate against the original syndrome before selection; retain invalid, contradictory, failed, cap-hit, and no-proposal branches.

### Contracts, execution, budgets, ledger, verification, and public manifests

**Apply to:** extensions in `canonical/contracts.py`, `execution.py`, `budgets.py`, `verification.py`, `manifests.py`, `ledger.py`, `cli.py`, and `runner.py`.

**Strict versioned schema** (`canonical/contracts.py:17-19`):

```python
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)
```

Add an intervention manifest/ledger version and closed dispatch; preserve V1–V5 interpretation. Persist semantic exact fixes and finite numerical realization separately, since persisted infinities are forbidden.

**Leaf-only accounting** (`canonical/budgets.py:400-425,429-460`):

```python
class Reservation:
    """One-shot token which either commits a complete leaf vector or rolls back."""
    def commit_once(self) -> None:
        self._tree._finalize(self, commit=True)
...
def reserve(self, scope: str, delta: WorkVector, *, leaf_id: str) -> Reservation | None:
```

Extend `WorkVector` and scopes for transformations, fixation/actions, ranking scans, lift coordinates, and original validation. Reuse leaf IDs and parent aggregation; never add controller-local totals.

**Append-only canonical event grammar** (`ledger.py:386-442,506-571`):

```python
_CANONICAL_EVENT_KINDS = frozenset({..., "candidate", "selection", "termination", ...})
...
event["event_id"] = _canonical_event_id(event)
_validate_canonical_event(event)
handle.write(_canonical_event_bytes(event).decode("utf-8") + "\n")
handle.flush()
os.fsync(handle.fileno())
```

Reuse `attempt`, `candidate`, `selection`, `termination`, `work`, and trace events when their meanings remain unchanged. Add versioned intervention/branch payloads with source variant/qualification, trigger, target or test vector, state digests, reset/preservation, working lineage, lift certificate, original validity, and work leaves. Extend exact terminal reconstruction in `canonical/verification.py` before exposing runs publicly.

**Public execution boundary** (`execution.py:779-805`, `cli.py:263-310`):

```python
parsed = parse_canonical_manifest(manifest)
if isinstance(parsed, CanonicalManifestV4):
    return _run_relay_structural_shot(...)
...
resolved = validate_composition(parsed.policies)
PolicyRuntime(resolved).traverse_lifecycle()
budgets = _budget_tree(execution_controls)
```

Route the new manifest version through structural execution, `preflight`, CLI run, and verification, using the same resolved public context and matched sample identity. Reject unsupported policy/operator/source combinations before sampling or decoder mutation.

### Pilot manifests, analysis, notebook, HTML, and tests

**Apply to:** `data/manifests/phase5-*.json`, `docs/evidence/phase5-source-decisions.json`, `phase5_analysis.py`, Phase 5 scripts/notebook, and `tests/*phase5*`.

**Analogs:** `src/bp_registry/phase4_analysis.py:52-131`, `scripts/execute_phase4_notebook.py`, `scripts/phase4_notebook_support.py`, `notebooks/phase4-memory-relay-analysis.ipynb`, and `tests/canonical/test_phase4_notebook.py:41-86,144-169`.

**Paired sample and qualification gate** (`phase4_analysis.py:70-98`):

```python
if not isinstance(shot_id, int) or shot_id < 0 or shot_id in seen_ids ...:
    raise ValueError("paired cohort has missing or duplicate shot/sample identity")
...
if arm.get("sample_identity") != sample:
    raise ValueError(f"shot {shot_id}/{name} physical sample differs from the paired identity")
if cell == "no_proposal" and selected:
    raise ValueError(f"shot {shot_id}/{name} selects a nonexistent proposal")
```

Phase 5 analysis must display every attempted path, including denied and invalid paths, and retain `pilot_adaptation`/`not_assessed` labels. Start from calibration, freeze caps and arm availability in a saved B1 manifest, then use the frozen matched evaluation samples.

**Notebook evidence integrity** (`tests/canonical/test_phase4_notebook.py:41-86,144-169`):

```python
record = support.ensure_stage(tmp_path, first, producer=lambda: _record(first), predecessor_verified=True)
...
with pytest.raises(ValueError, match="snapshot digest"):
    support.load_stage(tmp_path, expected)
...
assert "development_fixture" in html and "not_assessed" in html
```

Copy the confinement, identity-digest, fixture execution, and rendered-HTML assertions. The new notebook is shot-first (baseline plus selected arm), with expandable attempt records. The new Plotly HTML/export integration has **no installed local analog**: plan a `human-verify` checkpoint for the flagged package, pin/probe the approved release, then test `legendgroup`/`groupclick`, `legendonly` initial traces, self-contained export, escaped manifest/source text, and evidence links.

## Shared Patterns

### Immutable original and independent evaluation

**Sources:** `canonical/problems.py:20-62`; `canonical/execution.py:760-769`.

Policies and controllers receive only original observation, working view, priors, and committed decoder state. Hidden physical truth and logical outcomes enter only after a decoder-visible original-space candidate is selected.

### Atomic proposal/work/state transaction

**Sources:** `canonical/budgets.py:400-460`; `canonical/memory_execution.py:271-277`; `canonical/relay.py:442-465`.

Compute child state privately, reserve a full uniquely identified leaf, validate, commit the state and leaf once, then emit evidence. A rejected reservation changes no mutable parent-owned state.

### Versioning, finite persistence, and replay

**Sources:** `canonical/contracts.py:17-19`; `ledger.py:386-442,506-571`; `manifests.py:535-675`.

Use strict frozen models, finite JSON, explicit version dispatch, content/digest validation, and deterministic event IDs. Historical manifest and ledger readers retain their prior semantics.

### Source qualification

**Sources:** `canonical/relay.py:145-176`; `docs/evidence/phase5-source-status-20260926.json`.

Each named controller preset persists source anchors, procedure/variant, native-code availability, unresolved details, and source/adaptation status. BPGD, impulse, syndrome flip, and sign flip remain unavailable or clearly named interpretations until primary-source decisions close the stated gaps.

## No Analog Found

| File/concern | Role | Data flow | Reason |
|---|---|---|---|
| Plotly grouped-legend and standalone HTML helper | visualization/export utility | batch/file-I/O | The repository has notebook HTML preview but no Plotly dependency or grouped interactive chart implementation. |

## Metadata

**Analog search scope:** `src/bp_registry`, `tests`, `scripts`, `tools`, `notebooks`, `data/manifests`, `docs/evidence`  
**Tracked source files scanned:** 81  
**Pattern extraction date:** 2026-09-30
