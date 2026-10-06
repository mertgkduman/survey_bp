# Phase 7: Optional Postprocessing - Pattern Map

**Mapped:** 2026-10-05  
**Files analyzed:** 24 planned new or modified files  
**Analogs found:** 18 / 24

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/bp_registry/canonical/postprocessing/handoff.py` | model | transform | `canonical/problems.py` | role-match |
| `src/bp_registry/canonical/postprocessing/controller.py` | controller | event-driven | `canonical/phase6.py` | partial |
| `src/bp_registry/canonical/postprocessing/compatibility.py` | utility | transform | `canonical/problems.py` | role-match |
| `src/bp_registry/canonical/postprocessing/osd.py` | service | request-response | `reference.py` | partial |
| `src/bp_registry/canonical/postprocessing/lsd.py` | service | request-response | `reference.py` | partial |
| `src/bp_registry/canonical/postprocessing/si.py` | service | event-driven | `canonical/interventions.py` | partial |
| `src/bp_registry/canonical/postprocessing/otf.py` | service | transform | `canonical/transformations.py` | partial |
| `src/bp_registry/canonical/postprocessing/work.py` | model | batch | `canonical/budgets.py` | role-match |
| `src/bp_registry/canonical/execution.py` | controller | event-driven | `canonical/execution.py` | exact |
| `src/bp_registry/canonical/contracts.py` | model | transform | `canonical/contracts.py` | exact |
| `src/bp_registry/canonical/budgets.py` | model | batch | `canonical/budgets.py` | exact |
| `src/bp_registry/canonical/candidate_selection.py` | utility | transform | `canonical/candidate_selection.py` | exact |
| `src/bp_registry/ledger.py` | service | append-only event-driven | `ledger.py` | exact |
| `src/bp_registry/canonical/verification.py` | utility | transform | `canonical/phase6.py` | partial |
| `src/bp_registry/manifests.py` | model | request-response | `manifests.py` | exact |
| `src/bp_registry/literature.py` | compiler | transform | `literature.py` | exact |
| `src/bp_registry/reference.py` | adapter | request-response | `reference.py` | exact |
| `src/bp_registry/study.py` and `src/bp_registry/study_cli.py` | controller/route | request-response | `study.py` | role-match |
| `literature_policies/*/bp-*.toml` | config | transform | `literature_policies/yao-2024-guided-decimation/bpgd-t100-r002.toml` | exact |
| `literature_policies/*/*.spec.toml` | config | transform | `literature_policies/yao-2024-guided-decimation/bpgd-t100-r002.spec.toml` | exact |
| `tests/canonical/test_postprocessing_handoff.py` | test | event-driven | `tests/canonical/test_candidate_selection.py` | role-match |
| `tests/canonical/test_postprocessing_{osd,lsd,si,otf}.py` | test | request-response/transform | `tests/test_reference_smoke.py` | partial |
| `tests/test_phase7_public_execution.py` | test | request-response | `tests/test_phase6_public_execution.py` | exact |
| `notebooks/phase7-postprocessing-analysis.ipynb`, `src/bp_registry/phase7_analysis.py`, `scripts/execute_phase7_notebook.py`, `tests/test_phase7_notebook.py` | notebook/service/test | file-I/O | Phase 5 notebook set | exact |

## Pattern Assignments

### `canonical/postprocessing/{handoff,compatibility,controller,work}.py`

**Analogs:** `src/bp_registry/canonical/problems.py`, `candidate_selection.py`, `budgets.py`, and `phase6.py` (all tracked).

**Immutable problem and reconstruction boundary** ([`problems.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/problems.py:20), lines 20-103):

```python
@dataclass(frozen=True)
class OriginalProblem:
    lineage_id: str
    hx: np.ndarray
    hz: np.ndarray
    syndrome: np.ndarray

@dataclass(frozen=True)
class OriginalSpaceCandidate:
    lineage_id: str
    working: WorkingProblem
    candidate: np.ndarray
    local_order: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate", _readonly_binary(self.candidate, ndim=1, name="candidate"))
        if self.candidate.shape != (self.working.original.hz.shape[1],) or self.local_order < 0:
            raise ValueError("candidate length or local order is invalid")
```

Follow this for frozen failed-attempt handoffs: copied arrays must be immutable, shapes must be checked before a native call, and every fallback output must return as an `OriginalSpaceCandidate` before eligibility is decided. Preserve the working transform/lift identities and add a method-specific reliability translation declaration; no fallback may infer an inverse map.

**Stable, truth-free rank** ([`candidate_selection.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/candidate_selection.py:247), lines 247-294):

```python
ordered = tuple(sorted(origins, key=lambda item: _stable_key(item.lineage_id, item.local_ordinal)))
prevalidated = tuple(FrozenOrigin(
    origin,
    None if origin.candidate is None else _original_valid(original, origin.candidate),
    None,
    0,
) for origin in ordered)
...
selected = min(
    (item for item in frozen if item.eligible),
    key=lambda item: ((-item.score if score_policy.higher_is_better else item.score),
                      item.local_ordinal, item.lineage_id.value),
    default=None,
)
```

Use this freeze-before-select shape for D-02. Phase 7's controller key is `(original_residual_weight, original_channel_nll, declared_attempt_ordinal, lineage_id)` and must be computed from the frozen decoder-visible snapshot, never truth or completion order.

**Reserve, compute, commit** ([`budgets.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/budgets.py:447), lines 447-516):

```python
class BudgetTree:
    """Thread-safe hard limits with leaf-only committed accounting.

    Reservations temporarily occupy every ancestor allowance.  Committed work is
    stored only once, at its leaf; all scope summaries reduce those unique leaves.
    """
```

Give each controller call a fallback scope and one leaf per bounded substage. Use existing exact work fields (`fallback_calls`, `ranking_scans`, `bp_calls`, `candidate_checks`, `transformations`, `lifted_coordinates`, `original_checks`) and put OSD/LSD/SI/OTF-specific counters in a versioned `PostprocessingWork` evidence record. A failed reservation yields a capped terminal result but must retain an already original-valid candidate.

**Ledger projection** ([`phase6.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/phase6.py:12), lines 12-77):

```python
@dataclass(frozen=True)
class Phase6Projection:
    terminal_status: str
    events: tuple[tuple[str, Mapping[str, Any]], ...]
    candidate: tuple[int, ...] | None

events.append(("work_leaf", {"leaf_id": leaf_id, "scope": scope,
                              "work_vector": work.as_evidence(structural_event_version=4)}))
events.append(("termination", terminal))
```

Make a comparable `Phase7Projection` that emits the one complete-composition decision, selected failed origin, skipped reason or method result, all candidate lineage, BP-only/final outcomes, method work and terminal status. The controller must be called once after the composition lifecycle, not from branch or relay attempt code.

### `canonical/execution.py`, `contracts.py`, and `candidate_selection.py`

**Analogs:** same tracked files.

**Result extension seam** ([`execution.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/execution.py:127), lines 127-145):

```python
@dataclass(frozen=True)
class CanonicalExecutionResult:
    run_id: str
    shot_id: int
    termination: str
    evaluation: evaluator.DecoderEvaluation
    candidate: np.ndarray
    last_sweep: int
```

Extend the terminal lifecycle to retain a schedule-neutral posterior plus diagnostic candidate in a frozen handoff. Preserve the existing BP-only `CanonicalExecutionResult` evidence before adding a separately labeled final result.

**Closed seven-role registry** ([`contracts.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/contracts.py:17), lines 17-28):

```python
class PolicyRole(str, Enum):
    UPDATE = "update"
    SCHEDULE = "schedule"
    STATE_MEMORY = "state_memory"
    INTERVENTION = "intervention"
    STOPPING = "stopping"
    SELECTION = "selection"
    POSTPROCESSING = "postprocessing"
```

Add typed, closed postprocessing binding specs and compatibility metadata to this existing role. One binding admits exactly one enabled method. Follow `validate_composition` at [`contracts.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/contracts.py:374): unknown kinds fail before execution and a binding carries registry-owned provenance/invariants.

### `ledger.py` and `canonical/verification.py`

**Analog:** [`ledger.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/ledger.py:350), lines 350-420 and 680-737.

Use the existing canonical event grammar and structural replay route. The ledger already recognizes the `fallback` event family; add a versioned Phase 7 payload rather than an ad hoc sidecar. Replayer validation must require: one fallback at most; fallback only after no original-valid BP candidate; immutable chosen-origin evidence; method subwork; original checks for every proposed output; BP-only/final distinction; and explicit unavailable reasons for opaque native metrics. Retain failed, skipped, capped, and invalid outcomes.

### `manifests.py` and `literature.py`

**Analogs:** [`manifests.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/manifests.py:248) and [`literature.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/literature.py:1).

**Strict work-limit shape** ([`manifests.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/manifests.py:258), lines 258-307):

```python
class CanonicalWorkLimitsV2(StrictModel):
    ...
    fallback_calls: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)

    @model_validator(mode="after")
    def _complete_work_vector(self) -> "CanonicalWorkLimitsV2":
        if set(type(self).model_fields) != set(WorkVector.zero().as_evidence(structural_event_version=2)):
            raise ValueError("canonical work limit fields must exactly match WorkVector resources")
        return self
```

Version the public manifest/schema and require complete caps at the chosen structural event version. Admission must reject multi-method runtime overrides, nonfinite/mismatched reliability controls, and unregistered methods before artifacts or samples load.

**Executable admission table** ([`manifests.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/manifests.py:619), lines 619-714): Phase 6 checks a complete role-to-kind table and requires `"postprocessing": "identity"`. Replace only that identity-only condition with the registered closed Phase 7 choices while retaining exact complete-role comparison.

**Compiler pattern:** retain `literature.py`'s distinction between closed executable controls and separately hashed provenance/source explanations (lines 1-150, 220-320). Extend its existing single parser: typed `[postprocessing]`, component-level source/revision/equation anchor blocks, and a generated controlled-arm resolver that persists a full resolved manifest and provenance receipt before run. Preserve `.spec.toml` disposition for unresolved SI/OTF; do not create a second policy route or let prose modify numerical identity.

### `reference.py`

**Analog:** [`reference.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/reference.py:1), lines 1-116.

Follow the pinned-native adapter approach: constructor controls and provider/package identity are explicit; input/output arrays are validated; observed exposed fields are recorded; opaque internal work is `unavailable` with its reason. Add separate native `BpOsdDecoder` and `BpLsdDecoder` composite adapters. They are reference arms with their own BP lifecycle and cannot be presented as calls through the canonical fallback controller.

### Tests, public study path, and notebook

**Public integration test:** [`tests/test_phase6_public_execution.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/tests/test_phase6_public_execution.py:1), lines 1-112. Copy its compact public manifest, preflight, run, structural replay, and evidence-assertion sequence for `test_phase7_public_execution.py`.

**Notebook contract:** [`tests/test_phase5_notebook.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/tests/test_phase5_notebook.py:132), lines 132-143, requires the standard sections, one tagged parameter cell, bounded assessment labeling, and safe HTML escaping. Copy the shot-first retained-attempt inspection structure in [`tests/test_phase5_notebook.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/tests/test_phase5_notebook.py:29), lines 29-113: include BP-only and final outcomes, trigger/skip status, selected fallback origin/candidate lineage, method work, source/adaptation status, and native missingness.

**Read-only notebook executor:** [`scripts/execute_phase5_notebook.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/scripts/execute_phase5_notebook.py:23), lines 23-68:

```python
dataset = load_verified_evidence(evidence)
relative_evidence = Path(evidence).resolve(strict=True).relative_to(ROOT)
notebook = nbformat.read(source, as_version=4)
tagged = [cell for cell in notebook.cells if "phase5_parameters" in cell.metadata.get("tags", ())]
if len(tagged) != 1:
    raise ValueError("Phase 5 notebook requires one parameter cell")
...
notebook.metadata["phase5_evidence"] = {
    "ledger_sha256": dataset.ledger_sha256,
    "design_digest": dataset.design_digest,
    "assessment_status": dataset.assessment_status,
}
```

Make the Phase 7 equivalent read verified retained evidence only, require one parameter cell, bind ledger/design digests into executed metadata, and execute within the pinned project environment.

## Shared Patterns

### Original-problem validation and truth boundary
**Sources:** `canonical/problems.py:20-103`, `canonical/candidate_selection.py:247-294`.

Apply to every canonical fallback and generated arm: policies see only frozen decoder-visible posterior, candidate, original problem, declared channel parameters, and identity/transform metadata. They never receive sampled error, outcome, logical recovery, or completion order.

### Reliability convention
**Source:** `canonical/numerics.py:15-62,141-151`.

Use finite `float64` natural-log odds. Preserve `negative => hard bit 1`, exact-zero decision `0`, and `abs(llr)` as the OSD/LSD reliability ordering value. Reject NaN/Inf, wrong declared convention, wrong length, and incompatible transforms as a recorded fallback skip.

### Evidence and budgets
**Sources:** `canonical/budgets.py:18-120,447-516`; `ledger.py:350-420,680-737`.

Use versioned exact counters, leaf-only accounting, pre-reservation, and replayable terminal events. Do not turn native opaque work into zero.

### Policy identity and source provenance
**Sources:** `canonical/contracts.py:17-28,374-425`; `literature.py:1-150,220-320`.

Keep complete seven-role executable identity independent from citations, explanations, unresolved details, and component source records. Persist paper-specific complete variants as files; persist controlled-study arms as resolved manifests before execution.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `canonical/postprocessing/osd.py` | service | request-response | No canonical OSD service exists; use isolated pinned official seam after its build/import gate. |
| `canonical/postprocessing/lsd.py` | service | request-response | No canonical standalone-LSD adapter exists; wrap released `LsdDecoder` with existing native-adapter evidence rules. |
| `canonical/postprocessing/si.py` | service | event-driven | No existing inactivation controller; source-faithful configuration remains non-runnable until blockers resolve. |
| `canonical/postprocessing/otf.py` | service | transform | No existing Tanner-forest controller; canonical CSS adaptation requires focused algebra fixtures. |
| `canonical/postprocessing/work.py` | model | batch | Existing `WorkVector` cannot represent method-specific algebra without a versioned companion record. |
| `tests/canonical/test_postprocessing_{osd,lsd,si,otf}.py` | test | varied | Mechanism-specific contract/differential fixtures are new. |

## Metadata

**Analog search scope:** `src/bp_registry/canonical`, `src/bp_registry`, `tests`, `scripts`, `notebooks`, `literature_policies`, `docs`  
**Files scanned:** 22 tracked source/test/support files  
**Pattern extraction date:** 2026-10-05
