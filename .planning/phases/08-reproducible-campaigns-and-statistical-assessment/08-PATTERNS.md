# Phase 8: Reproducible Campaigns and Statistical Assessment - Pattern Map

**Mapped:** 2026-10-11  
**Files analyzed:** 16 proposed files  
**Analogs found:** 16 / 16

## File Classification

| New/Modified File | Role | Data Flow | Closest tracked analog | Match |
|---|---|---|---|---|
| `src/bp_registry/campaigns/contracts.py` | model | transform | `src/bp_registry/manifests.py` | exact |
| `src/bp_registry/campaigns/identity.py` | utility | transform | `src/bp_registry/manifests.py` and `sampling.py` | exact |
| `src/bp_registry/campaigns/planning.py` | service | batch | `scripts/run_fair_beam_relay_campaign.py` | role-match |
| `src/bp_registry/campaigns/execution.py` | service | batch | `scripts/run_fair_beam_relay_campaign.py` | exact |
| `src/bp_registry/campaigns/slurm.py` | adapter | request-response | `scripts/run_fair_beam_relay_campaign_slurm.sh` | partial |
| `src/bp_registry/campaigns/shards.py` | service | file-I/O | `src/bp_registry/ledger.py` | exact |
| `src/bp_registry/campaigns/statistics.py` | utility | transform | `scripts/run_fair_beam_relay_campaign.py` | exact |
| `src/bp_registry/campaigns/targets.py` | model | file-I/O | `src/bp_registry/artifacts.py` | role-match |
| `src/bp_registry/campaigns/profiling_gate.py` | service | batch | `src/bp_registry/canonical/profiling.py` | exact |
| `src/bp_registry/campaigns/reporting.py` | service | transform | `src/bp_registry/phase4_analysis.py` | role-match |
| `tests/test_campaign_contracts.py` | test | transform | `tests/test_manifest.py` | role-match |
| `tests/test_campaign_shards.py` | test | file-I/O | `tests/test_ledger.py` | exact |
| `tests/test_campaign_execution.py` | test | batch | `tests/test_run_fair_beam_relay_campaign.py` | exact |
| `tests/test_campaign_statistics.py` | test | transform | `tests/test_run_fair_beam_relay_campaign.py` | exact |
| `tests/test_campaign_targets.py` | test | file-I/O | `tests/test_source_artifact.py` | role-match |
| `tests/test_campaign_profile_gate.py` | test | batch | `tests/canonical/test_profiling.py` | exact |

`src/bp_registry/campaigns/__init__.py` is an implied package marker; follow the minimal exports pattern in `src/bp_registry/canonical/__init__.py`. No existing generic campaign package exists, so introduce this subsystem without changing public experiment-manifest dispatch.

## Pattern Assignments

### Contracts and identities

**Files:** `campaigns/contracts.py`, `identity.py`, `targets.py`  
**Analog:** `src/bp_registry/manifests.py` (tracked), `src/bp_registry/sampling.py` (tracked)

Use frozen strict Pydantic records. Make every persisted campaign, target, shard receipt, stopping plan, outcome/denominator matrix, and assessment plan an exact-field model. Use a namespaced string schema identifier (`campaign_spec_v1`), because numeric experiment schema 8 is already occupied.

**Strict-model pattern** ([`manifests.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/manifests.py:36)):
```python
class StrictModel(BaseModel):
    """The persisted manifest never coerces settings or silently keeps extras."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
```

**Bounded nested-budget validation** ([`manifests.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/manifests.py:259)):
```python
class CanonicalBudgetsV2(StrictModel):
    max_shots: int = Field(ge=1, le=MAX_SHOTS)
    shot: CanonicalBudgetScopeV2
    search: CanonicalBudgetScopeV2

    @model_validator(mode="after")
    def nested_scopes_do_not_expand_the_shot_limit(self) -> "CanonicalBudgetsV2":
        if self.search.max_iterations > self.shot.max_iterations:
            raise ValueError("canonical nested iteration budgets may not exceed their parent scope")
        return self
```

**Canonical identity bytes and digest** ([`manifests.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/manifests.py:1198)):
```python
def manifest_digest(manifest: ManifestRecord) -> str:
    document = manifest.model_dump(mode="json")
    payload = json.dumps(document, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

**Arm-neutral sampling anchor** ([`sampling.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/sampling.py:70)):
```python
def _rng(identity: str, shot_id: int) -> np.random.Generator:
    material = hashlib.sha256(
        f"bp-registry-sample-v1\0{identity}\0{shot_id}".encode()
    ).digest()
    words = np.frombuffer(material, dtype="<u4").astype(np.uint32, copy=False)
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(words)))
```

The campaign identity utility should use the same canonical JSON and SHA-256 convention, but its sample namespace must deliberately omit arm, worker, process, completion order, and branch count. Keep decoder-local identity arm-scoped in the contract rather than altering `sampling.sample_shot`.

### Planning, execution, and Slurm adapter

**Files:** `campaigns/planning.py`, `execution.py`, `slurm.py`  
**Analog:** `scripts/run_fair_beam_relay_campaign.py` (tracked)

Treat the frozen campaign plan as the source of task identity. Executor implementations consume a supplied unit/shard plan; they never decide sample membership or assessment policy. Local and Slurm adapters must map the same sorted unit keys to the same shards and only add executor observations.

**Freeze-and-seal preflight** ([`run_fair_beam_relay_campaign.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/scripts/run_fair_beam_relay_campaign.py:97)):
```python
def prepare(design_path: Path, output: Path) -> dict:
    _design(design_path)
    frozen = output / "design.json"
    _write_once(frozen, design_path.read_bytes())
    seal = _seal(frozen)
    _write_once(output / "seal.json", json.dumps(seal, indent=2, sort_keys=True).encode() + b"\n")
    return seal
```

**Bounded local execution with deterministic ordered inputs** ([`run_fair_beam_relay_campaign.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/scripts/run_fair_beam_relay_campaign.py:181)):
```python
if workers == 1:
    for shot_id in range(spec["shots"]):
        yield _shot(spec, controls, code, shot_id)
else:
    arguments = zip(repeat(spec), repeat(controls), repeat(code), range(spec["shots"]))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(_compute_shot, arguments, chunksize=1)
```

**Fail closed on frozen-input and replay drift** ([`run_fair_beam_relay_campaign.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/scripts/run_fair_beam_relay_campaign.py:191)):
```python
design = _checked(design_path, output)
rows = _rows(ledger)
if [row.get("shot_id") for row in rows] != list(range(len(rows))):
    raise ValueError("shard has duplicate, reordered, or out-of-range shots")
for shot_id, expected in enumerate(_computed_shots(spec, controls, code, workers=workers)):
    if shot_id < len(rows) and _deterministic(rows[shot_id]) != _deterministic(expected):
        raise ValueError(f"deterministic replay differs at {cohort}/{rate}/{profile}/{shot_id}")
```

The Slurm adapter has no direct general analogue. Keep it deliberately thin: construct bounded array argv/environment from a validated `ShardPlan`, map `SLURM_ARRAY_TASK_ID` to exactly one shard ID, and record scheduler data as observations in the shard receipt. It must not reinterpret sample keys, counters, stop looks, or results.

### Shards, merge, and resume

**Files:** `campaigns/shards.py`, `reporting.py`  
**Analog:** `src/bp_registry/ledger.py` (tracked), `src/bp_registry/study.py` (tracked)

Use one caller-owned byte snapshot for integrity checks, then validate canonical events and reconstruct outcomes from verified terminal evidence. Shards are staged privately, sealed immutably, and merged by exact unit-key coverage. Resume is verified set subtraction, never reopening a sealed ledger.

**Canonical evidence bytes** ([`ledger.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/ledger.py:402)):
```python
def _canonical_event_bytes(event: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(event), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
```

**Snapshot validation and duplicate conflict detection** ([`ledger.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/ledger.py:572)):
```python
previous = seen.get(event["event_id"])
if previous is not None:
    if previous != event:
        raise ValueError(f"conflicting canonical event ID at line {number}")
    continue
key = _key(event["run_id"], event["shot_id"])
if event["kind"] == "shot_begin":
    if state is not None:
        raise ValueError("canonical shot_begin is duplicated or follows a terminal event")
elif state != "open":
    raise ValueError("canonical structural event requires a prior open shot_begin")
```

**Durable append** ([`ledger.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/ledger.py:148)):
```python
with path.open("a", encoding="utf-8") as handle:
    handle.write(payload + "\n")
    handle.flush()
    os.fsync(handle.fileno())
```

**Receipt-bound cache/replay pattern** ([`study.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/study.py:280)):
```python
key = sha256(manifest_bytes + source_identity.encode()).hexdigest()
receipt = {"schema_version": 1, "cache_key": key,
           "manifest_sha256": sha256(manifest_bytes).hexdigest(),
           "source_sha256": source_identity}
if (output / "result.json").exists():
    if not receipt_path.is_file() or json.loads(receipt_path.read_text()) != receipt:
        raise ValueError("cached result is missing or conflicts with its source receipt")
    verified = verify_run(output)
```

Atomic publication (`tempfile` in the destination parent, file `fsync`, `os.replace`, directory `fsync`) is an intentional Phase 8 strengthening of the ledger append pattern. Validate receipt digest, campaign/source/environment identities, JSONL snapshot, replay, exact expected keys, and terminal states before accepting any shard. Reports must receive only merged verified terminals; keep partial/open/rejected work in the merge receipt and produce a deterministic missing-key plan.

### Statistics and outcome accounting

**Files:** `campaigns/statistics.py`, `reporting.py`  
**Analog:** `scripts/run_fair_beam_relay_campaign.py` (tracked), `src/bp_registry/phase4_analysis.py` (tracked)

Use SciPy `binomtest(...).proportion_ci(method="exact")` for Phase 8 fixed and finite-look rate intervals; do not copy the old script's direct beta implementation. Reuse its paired-discordance and Holm ordering shape, while persisting the declared alpha allocation, look boundary, raw and adjusted values, and outcome/denominator mapping.

**Paired exact test and deterministic Holm order** ([`run_fair_beam_relay_campaign.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/scripts/run_fair_beam_relay_campaign.py:304)):
```python
discordant = beam_only + relay_only
raw_p = float(binomtest(beam_only, discordant, 0.5).pvalue) if discordant else 1.0
ordered = sorted(contrasts, key=lambda key: (contrasts[key]["raw_p"], key))
for position, key in enumerate(ordered):
    running = max(running, min(1.0, contrasts[key]["raw_p"] * (len(ordered) - position)))
    contrasts[key]["holm_p"] = running
```

**All-shot plus conditional denominators** ([`phase4_analysis.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/phase4_analysis.py:79)):
```python
if not isinstance(arm, Mapping) or arm.get("status") != "completed":
    raise ValueError(f"shot {shot_id}/{name} is incomplete; retain it outside an outcome denominator")
if arm.get("sample_identity") != sample:
    raise ValueError(f"shot {shot_id}/{name} physical sample differs from the paired identity")
success = int(selected and cell == "valid_correct")
failures[name] += 1 - success
```

The new statistics records must reject zero denominators, retain zero/all-failure intervals, distinguish final-only from finite-look decisions, and make partial work inconclusive. Use `binomtest` for paired p-values as research directs, rather than retaining the legacy hand-rolled `exact_paired_binomial_p` in `phase4_analysis.py`.

### Profiling gate

**Files:** `campaigns/profiling_gate.py`, `tests/test_campaign_profile_gate.py`  
**Analog:** `src/bp_registry/canonical/profiling.py` (tracked), `tests/canonical/test_profiling.py` (tracked)

Keep timing/resource facts typed observational evidence. Preserve explicit unavailable measurements and only authorize a campaign from pre-outcome representative, semantically matching clean/profile pairs.

**Allowlisted environment and exact parse** ([`profiling.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/profiling.py:71)):
```python
environment = dict(self.environment)
if set(environment) - _ALLOWLISTED_ENVIRONMENT:
    raise ValueError("profile environment contains a non-allowlisted field")
if not isinstance(value, Mapping) or set(value) != {
    "runtime", "adapter_overhead", "python_allocation_peak", "environment",
    "raw_context", "enabled", "level",
}:
    raise ValueError("profile evidence has an invalid field set")
```

**Timing-independent semantic replay** ([`profiling.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/profiling.py:296)):
```python
_SEMANTIC_FIELDS = ("candidate", "termination", "work", "lineage", "semantic_trace_digest")
def compare_semantics(clean: Mapping[str, object], profiled: Mapping[str, object]) -> SemanticAgreement:
    mismatches = [field for field in _SEMANTIC_FIELDS
                  if field not in clean or field not in profiled or clean[field] != profiled[field]]
    return SemanticAgreement(not mismatches, tuple(mismatches))
```

**Pre-outcome representative cohort** ([`profiling.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/profiling.py:223)):
```python
if self.cohort == "representative":
    if not self.selected_before_outcome:
        raise ValueError("representative profiling must be selected before outcomes")
    if not 0 < float(self.inclusion_probability) <= 1:
        raise ValueError("representative inclusion probability must be in (0, 1]")
```

The authorization receipt should bind campaign digest, gate shard/merge/replay receipts, measured throughput/storage/memory and safety margin, declared budget, and a decision/reason. It should deny large dispatch on missing required evidence or projected budget exceedance.

## Shared Patterns

### Immutable, content-addressed inputs

Source: [`study.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/study.py:280). Bind canonical document bytes, source hashes, and environment identity before execution; on reuse, require byte-equal receipt and independent verification.

### Fail closed at evidence boundaries

Source: [`ledger.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/ledger.py:609). Parse one byte snapshot, verify event IDs and lifecycle, reject conflicts/duplicates/incomplete terminals, and never infer a missing measurement or denominator.

### Determinism independent of process topology

Source: [`sampling.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/sampling.py:76). Derive physical samples from explicit namespace plus shot ID, not workers; arm-specific decoder randomness remains separate.

### Test expected corruption and boundary behavior

Sources: [`test_run_fair_beam_relay_campaign.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/tests/test_run_fair_beam_relay_campaign.py:18), [`test_profiling.py`](/hpc/group/pfisterlab/mg551/storage/survey_bp/tests/canonical/test_profiling.py:25). Use `tmp_path`, deterministic fixtures, and `pytest.raises` for drift, malformed evidence, duplicate/missing keys, missing resource facts, zero/all failure, and scheduler-plan equivalence.

## No Analog Found

| File | Gap | Planner direction |
|---|---|---|
| `campaigns/slurm.py` | Existing Slurm wrapper is campaign-specific shell glue, not a validated adapter. | Keep a small pure plan-to-argv mapper plus a synthetic executor test; do not put scientific state in shell code. |
| `campaigns/targets.py` | No existing figure/digitization receipt model. | Reuse strict/hash/file-confinement patterns, then implement the research-specified raw-click/calibration/pass provenance contract. |
| `campaigns/statistics.py` finite looks | No generic optional-stopping implementation exists. | Implement only declared finite looks and alpha allocation; no anytime/peeking API. |

## Metadata

**Analog search scope:** `src/bp_registry`, `scripts`, `tests`  
**Tracked-source gate:** verified all named analog source paths with `git ls-files`  
**Pattern extraction date:** 2026-10-11
