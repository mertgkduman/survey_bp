# Phase 2: Canonical CSS Execution and Policy Contracts - Pattern Map

**Mapped:** 2026-09-22  
**Files analyzed:** 29 planned new/modified files  
**Analogs found:** 26 / 29

## File Classification

| New/Modified File | Role | Data Flow | Closest tracked analog | Match quality |
|---|---|---|---|---|
| `src/bp_registry/canonical/contracts.py` | model/provider | transform | `src/bp_registry/manifests.py` | role-match |
| `canonical/problems.py` | model | transform | `src/bp_registry/sampling.py` | role-match |
| `canonical/numerics.py` | utility | transform | none | none |
| `canonical/kernel.py` | service | transform | `src/bp_registry/reference.py` | partial |
| `canonical/schedules.py` | provider | event-driven | none | none |
| `canonical/budgets.py` | service | event-driven | `src/bp_registry/ledger.py` | partial |
| `canonical/execution.py` | service | request-response | `src/bp_registry/runner.py` | role-match |
| `canonical/lineage.py` | model/service | event-driven | `src/bp_registry/evidence.py` | role-match |
| `canonical/tracing.py` | service | file-I/O | `src/bp_registry/ledger.py` | role-match |
| `canonical/profiling.py` | utility | batch | `src/bp_registry/cli.py` | partial |
| `src/bp_registry/manifests.py` | config/model | request-response | itself | extend |
| `src/bp_registry/runner.py` | controller | request-response | itself | extend |
| `src/bp_registry/ledger.py` | service | file-I/O | itself | extend |
| `src/bp_registry/cli.py` | controller | request-response | itself | extend |
| `tests/canonical/conftest.py` | test fixture | transform | `tests/conftest.py`, `tests/test_manifest.py` | role-match |
| `tests/canonical/test_contracts.py` | test | request-response | `tests/test_manifest.py` | exact |
| `tests/canonical/test_numerics.py`, `test_flooding.py` | test | transform | `tests/test_css_small.py` | role-match |
| `tests/canonical/test_budgets.py`, `test_work_accounting.py` | test | event-driven | `tests/test_ledger.py` | role-match |
| `tests/canonical/test_truth_boundary.py` | test | request-response | `tests/test_reference_smoke.py` | exact |
| `tests/canonical/test_policy_evidence.py` | test | request-response | `tests/test_evidence.py` | role-match |
| `tests/canonical/test_tracing.py` | test | file-I/O | `tests/test_ledger.py` | role-match |
| `tests/test_canonical_cli.py` | integration test | request-response | `tests/test_phase1_cli.py` | exact |
| `tests/fixtures/canonical-*` | fixture/config | file-I/O | `data/manifests/project-three-qubit-fixture.json` | role-match |
| `docs/canonical-engine.md` | documentation | request-response | `docs/phase1-pilot.md` | role-match |
| `docs/profiling-and-tracing-strategy.md` | documentation | batch | none | none |
| `docs/research-novelty-and-depth-register.md` | documentation | event-driven | `docs/phase1-source-decisions.md` | partial |

All named analogs above are git-tracked (`git ls-files -- <path>` verified). `canonical/` abbreviates `src/bp_registry/canonical/` after its first use.

## Pattern Assignments

### `canonical/contracts.py` and `src/bp_registry/manifests.py` (persisted contracts)

**Analog:** `src/bp_registry/manifests.py`.

Copy its strict, frozen Pydantic base and version-dispatch style; add `allow_inf_nan=False` for canonical numerical fields. Do not change V1 meanings.

```python
# src/bp_registry/manifests.py:27-30
class StrictModel(BaseModel):
    """The persisted manifest never coerces settings or silently keeps extras."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

# src/bp_registry/manifests.py:265-271
def parse_manifest(value: ManifestV1 | dict[str, Any] | str | Path) -> ManifestV1:
    if isinstance(value, ManifestV1):
        return value
    decoded = _read_value(value)
    if decoded.get("schema_version") != 1:
        raise ValueError(f"unsupported manifest schema version {decoded.get('schema_version')!r}")
```

Use `@field_validator(..., mode="before")` to convert JSON lists to tuples and `@model_validator(mode="after")` for whole-composition checks, as in `DecoderV1` (`manifests.py:89-111`) and `ExpectedOutputV1` (`143-171`). Keep runtime policy objects out of serialized manifests.

### `canonical/problems.py` and `canonical/execution.py` (truth-sealed execution)

**Analogs:** `src/bp_registry/sampling.py`, `src/bp_registry/runner.py`, and `src/bp_registry/evaluator.py`.

Construct an immutable decoder-visible original/working problem from observation only. The runner, not the engine or policy, retains the sampled truth and calls evaluator only after selection freezes.

```python
# src/bp_registry/sampling.py:24-40
@dataclass(frozen=True)
class HiddenTruth:
    """Physical errors retained for independent evaluation, never native decoding."""
    x: np.ndarray
    z: np.ndarray

@dataclass(frozen=True)
class ShotSample:
    shot_id: int
    sample_identity: str
    hidden: HiddenTruth
    observation: DecoderObservation
    observations: Mapping[str, DecoderObservation]

# src/bp_registry/runner.py:136-150
sample = sampling.sample_shot(...)
native = reference.decode(code.hz, sample.observation.syndrome, ...)
evaluation = evaluator.evaluate_candidate(
    code, true_x=sample.hidden.x, true_z=sample.hidden.z,
    candidate_x=native.candidate,
)
```

The evaluator’s input validation and explicit four-outcome result (`evaluator.py:13-19, 56-83`) must remain independent of policy selection.

### `canonical/numerics.py`, `canonical/kernel.py`, and `canonical/schedules.py` (pure flooding kernel)

**Analog:** `src/bp_registry/reference.py` is only a boundary/validation analog; there is no project-owned update-loop analog.

Copy the narrow pure-function input validation and frozen result style, but implement the researched float64 box-plus and double-buffering from scratch. Never call `ldpc.BpDecoder` from this package.

```python
# src/bp_registry/reference.py:18-27
def _binary_uint8(value: np.ndarray, *, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.dtype.kind not in {"b", "i", "u"}:
        raise ValueError(f"{name} must have a binary integer or bool dtype")
    if np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must contain only binary values")
    return array.astype(np.uint8, copy=False)

# src/bp_registry/reference.py:45-59
if raw_h.ndim != 2 or raw_s.shape != (raw_h.shape[0],):
    raise ValueError("check matrix and syndrome dimensions disagree")
...
if raw_candidate.shape != (h.shape[1],):
    raise RuntimeError("native reference returned wrong candidate shape")
```

Canonical-only requirements with no analog: stable `np.logaddexp` box-plus, named saturation/finiteness boundaries, degree-one rule, canonical edge table/order, old `v2c` → complete `c2v` → complete new `v2c`, and atomic sweep rollback.

### `canonical/budgets.py`, `canonical/tracing.py`, and `src/bp_registry/ledger.py` (durable scoped evidence)

**Analog:** `src/bp_registry/ledger.py`.

Preserve validated canonical JSONL, append+flush+fsync, ownership, terminal reconciliation, and explicit unavailable facts. Version a richer canonical event grammar; do not broaden ledger v1’s `begin`/`terminal` validation ambiguously.

```python
# src/bp_registry/ledger.py:73-90
kind = event.get("kind")
if kind not in {"begin", "terminal"}:
    raise ValueError("ledger event kind must be begin or terminal")
if event.get("ledger_version") != LEDGER_VERSION:
    raise ValueError(...)
_key(event.get("run_id"), event.get("shot_id"))

# src/bp_registry/ledger.py:111-118
payload = json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False)
with path.open("a", encoding="utf-8") as handle:
    handle.write(payload + "\\n")
    handle.flush()
    os.fsync(handle.fileno())
```

For no-double-counting, retain the current state-machine posture (`ledger.py:121-143`) and terminal-only summary rule (`ledger.py:307-320`). New leaf work deltas must be uniquely identified and ancestor totals derived, not independently emitted as consumption.

### `canonical/lineage.py` (append-only identities)

**Analog:** `src/bp_registry/evidence.py:48-84`.

Reuse canonical JSON content identity and idempotent/conflict semantics for typed lineage entities and edges.

```python
# src/bp_registry/evidence.py:48-57
def _canonical_payload(event: Mapping[str, Any], *, include_event_id: bool = False) -> str:
    payload = {key: value for key, value in event.items()
               if key != "event_order" and (include_event_id or key != "event_id")}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def stable_event_id(event: Mapping[str, Any]) -> str:
    return f"event-{sha256(_canonical_payload(event).encode('utf-8')).hexdigest()[:20]}"
```

Use distinct type-prefixed IDs/parent-edge fields for original problem, working problem, attempt/member/leg/branch, candidate, lift, validation, and selection.

### `canonical/profiling.py` and `src/bp_registry/cli.py` (operational integration)

**Analogs:** `src/bp_registry/cli.py:276-309`, `src/bp_registry/artifacts.py:70-91`.

Extend the parser with a canonical command while retaining all existing commands. Keep filesystem output roots confined and validated like artifacts; profile adapters return explicit missingness/reason rather than zero. The CLI delegates to runner/engine, never kernel arithmetic.

```python
# src/bp_registry/cli.py:276-289
commands = parser.add_subparsers(dest="command", required=True)
preflight_command = commands.add_parser("preflight")
preflight_command.add_argument("manifest", type=Path)
pilot_command = commands.add_parser("pilot")
pilot_command.add_argument("manifest", type=Path)
pilot_command.add_argument("--output", type=Path, required=True)

# src/bp_registry/artifacts.py:70-91
requested = Path(relative_path)
if requested.is_absolute() or ".." in requested.parts:
    raise ValueError("artifact path escapes approved root")
...
if cursor.is_symlink():
    raise ValueError("artifact path may not traverse a symlink")
```

### Tests, fixtures, and documentation

**Analogs:** `tests/test_manifest.py`, `tests/test_ledger.py`, `tests/test_reference_smoke.py`, `tests/test_phase1_cli.py`.

Follow import-inside-test and small independently constructed oracle conventions. Use adversarial monkeypatch probes for boundary claims and subprocess CLI only for public documented behavior.

```python
# tests/test_manifest.py:100-115
parsed = parse_manifest(value)
assert parsed.model_dump(mode="json") == value
assert ManifestV1.model_validate_json(parsed.model_dump_json()) == parsed
with pytest.raises(ValueError):
    parse_manifest({**value, "unknown_key": "ignored"})

# tests/test_ledger.py:39-59
with LedgerWriter(path) as writer:
    writer.begin(run_id="r1", shot_id=1, sample_seed_identity="seed-1")
    writer.terminal(run_id="r1", shot_id=1, termination="completed", ...)
rows = reconcile(path)
assert len(rows) == 1
assert summarize(path)["total_final"] == 1
```

`tests/test_reference_smoke.py:91-138` is the exact truth-boundary injection pattern: replace sampling/evaluation/native collaborators, run the public function, then assert the durable terminal fields. `tests/test_phase1_cli.py:13-29` is the CLI subprocess pattern (JSON stdout and `OMP_NUM_THREADS=1`). Write docs around a checked-in deterministic canonical fixture and test every documented command.

## Shared Patterns

### Strict validation and immutable inputs

**Sources:** `manifests.py:27-30, 340-367`; `artifacts.py:70-134`; `css.py:47-108`.

Apply to manifests, policy specs, numerical profiles, trace plans, and sidecar roots: strict/frozen schemas, finite bounded fields, version dispatch, preflight before execution, copied/validated arrays, confined file paths, and SHA-256 as identity/integrity only.

### Hidden-truth boundary

**Sources:** `sampling.py:24-40`; `runner.py:136-150`; `evaluator.py:33-83`.

Policies and canonical engine receive only original/working decoder-visible problem views. The runner holds `HiddenTruth`; selection freezes before independent evaluation annotations.

### Errors and missingness

**Sources:** `runner.py:167-180`; `ledger.py:145-158`; `reference.py:10-16`.

Convert failures to typed terminal evidence with stage/scope/reason. Preserve unavailable counters as `None` plus a reason; never synthesize a zero.

### Determinism and identity

**Sources:** `sampling.py:70-73, 76-110`; `manifests.py:370-374`; `evidence.py:48-84`.

Derive physical sample randomness from manifest identity + shot ID; use independent decoder-local RNG identity; canonicalize serialized IDs/payloads and make duplicate writes idempotent only when content matches.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `canonical/numerics.py` | utility | transform | No project-owned LLR/SP kernel exists. |
| `canonical/schedules.py` | provider | event-driven | Native adapter exposes only opaque parallel scheduling. |
| `docs/profiling-and-tracing-strategy.md` | documentation | batch | No profiling/cohort document exists. |

## Metadata

**Analog search scope:** `src/bp_registry`, `tests`, `docs`, `data/manifests`  
**Tracked source gate:** passed for every named analog  
**Files scanned:** 20 source/test/document candidates  
**Pattern extraction date:** 2026-09-22
