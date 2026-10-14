# Phase 11: Quaternary Reproduction and Comparisons - Pattern Map

**Mapped:** 2026-10-14  
**Files analyzed:** 17 planned implementation, test, and evidence surfaces  
**Analogs found:** 16 / 17

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/bp_registry/campaigns/contracts.py` | model/config | request-response | same file: `CampaignAssessmentV1`, `CampaignSpecV1` | exact extension |
| `src/bp_registry/campaigns/targets.py` | model/service | file-I/O | same file: `DigitizationTargetReceiptV1` | exact extension |
| `src/bp_registry/campaigns/controlled_execution.py` | service | file-I/O | same file: `run_fair_controlled_unit` | role/data-flow match |
| `src/bp_registry/campaigns/statistics.py` | utility/model | transform | same file: `paired_outcome_table` | exact extension |
| `src/bp_registry/campaigns/sizing.py` | model/utility | transform | same file: `PairedDesignV1`, `paired_design_size` | exact extension |
| `src/bp_registry/campaigns/cli.py` | controller/route | request-response | existing campaign lifecycle commands | role match |
| `src/bp_registry/quaternary/execution.py` | service | event-driven | `run_quaternary_qbpgd`, `run_quaternary_mbp4`, `run_quaternary_asced` | role match |
| `src/bp_registry/quaternary/sampling.py` | model/utility | transform | `JointPauliChannel`, `sample_joint_pauli` | exact reuse/possible extension |
| `src/bp_registry/quaternary/evaluator.py` | service | request-response | `evaluate_pauli_candidate` | exact reuse |
| `src/bp_registry/quaternary/native_asced.py` | adapter/model | file-I/O | `NativeAscedIdentity`, `NativeAscedResult` | partial, gate first |
| `tests/test_phase11_source_targets.py` | test | file-I/O | `tests/test_campaign_contracts.py`, target receipt tests | role match |
| `tests/test_phase11_quaternary_campaign.py` | test | event-driven | `tests/test_campaign_execution.py` | role/data-flow match |
| `tests/test_phase11_joint_separate.py` | test | request-response | `tests/canonical/quaternary/test_sampling.py`, `test_evaluator.py` | composition match |
| `tests/test_phase11_correlation_statistics.py` | test | transform | `tests/test_campaign_statistics.py` | exact extension |
| `tests/test_phase11_resource_gate.py` | test | request-response | campaign execution/gate tests | role match |
| `tests/canonical/quaternary/test_phase11_mbp4_target.py` | test | event-driven | `tests/canonical/quaternary/test_mbp4.py` | exact extension |
| `data/source-targets/phase11-*.json`, `data/manifests/phase11-*.json` | config/evidence | file-I/O | existing source-target and public manifest receipts | role match |

## Pattern Assignments

### `src/bp_registry/campaigns/contracts.py` (model/config, request-response)

**Analog:** `src/bp_registry/campaigns/contracts.py:627` (`CampaignAssessmentV1`) and `:705` (`CampaignSpecV1`).

Use `StrictModel`, versioned literal schema names, bounded fields, tuple coercion, whole-contract validators, canonical bytes, and a domain-separated digest. The new Pauli campaign and cross-point design must freeze point order, reference point, arms, all-shot mapping, alpha allocation, receipt digests, and unavailable/inconclusive states before dispatch.

```python
class CampaignAssessmentV1(StrictModel):
    schema_name: Literal["campaign_assessment_v1"] = Field(alias="schema", serialization_alias="schema")
    ...
    @model_validator(mode="after")
    def complete_frozen_assessment(self) -> "CampaignAssessmentV1":
        ...
    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))
    def digest(self) -> str:
        return _digest("bp-registry-campaign-assessment-v1", self.primitive_bytes())
```

### `src/bp_registry/campaigns/targets.py` and `data/source-targets/phase11-*.json` (model/service and evidence, file-I/O)

**Analog:** `src/bp_registry/campaigns/targets.py:421` (`TableTargetReceiptV1`) and `:592` (`DigitizationTargetReceiptV1`).

Model source details as a sealed receipt, validate every point/extraction relationship, and emit a digest. aSCED Figure 2 needs its own frozen digitization receipt; Q-BPGD and MBP4 targets retain unresolved metadata as explicit blocked/inconclusive facts.

```python
@model_validator(mode="after")
def complete_digitization_target(self) -> "DigitizationTargetReceiptV1":
    ...
    if set(interval_by_id) != set(expected_ids):
        raise ValueError("frozen intervals must cover each extracted point exactly once")
    return self

def digest(self) -> str:
    return _receipt_digest("bp-registry-campaign-digitization-target-v1", self)
```

### `src/bp_registry/campaigns/controlled_execution.py` (service, file-I/O)

**Analog:** `src/bp_registry/campaigns/controlled_execution.py:27-44, 167-293` (`_publish_exact`, `run_fair_controlled_unit`).

Adapt the receipt-first execution flow to a Pauli physical sample. Publish exact canonical bytes, reject symlinks/conflicts, bind the materialized-sample digest in every arm receipt, retain each arm's event ledger and independent validation, then replay without recomputing decoder work. Do not copy its CSS-specific `FairLegController` or shared-initial-BP semantics.

```python
if path.exists():
    if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
        raise ValueError("controlled evidence path conflicts with immutable bytes")
    return
...
materialized = materialize_campaign_sample(...)
... "materialized_sample_sha256": materialized.materialized_sample_sha256,
```

### `src/bp_registry/quaternary/sampling.py`, `evaluator.py`, and `execution.py` (model/service, transform and event-driven)

**Analogs:** `sampling.py:94-180,309-365`; `evaluator.py:125-166`; `execution.py:335-571`.

Reuse the categorical `I,X,Y,Z` channel and one sampled Pauli vector. Materialize narrow binary inputs from only the corresponding syndrome and marginal prior; preserve component terminal state/work; combine available guesses; call the independent evaluator once. The quaternary public runners show the required event order: preflight, sample, decoder events, candidate freeze, evaluation, termination.

```python
channel = JointPauliChannel.explicit(probabilities, n=count)
# sampler ledger binds channel identity, Pauli order, and sample identity

result = evaluate_pauli_candidate(candidate, hidden_truth=hidden_truth)

events.extend((
    _event("candidate_freeze", {...}),
    _event("evaluation", {...}),
    _event("termination", {...}),
))
```

### `src/bp_registry/campaigns/statistics.py` and `sizing.py` (utility/model, transform)

**Analogs:** `statistics.py:549-797`; `sizing.py:15-124`.

Keep the current strict full-identity join and all-shot mapping for each point. Add a separate versioned cross-point receipt/result, rather than relaxing `paired_outcome_table`, which intentionally rejects mixed points. Allocate simultaneous exact intervals across all four discordant-cell rates per lead contrast. Extend the sizing contract using the same disjoint calibration/evaluation namespaces and `powered`/`blocked_precision` terminal discipline.

```python
if len(campaign_points) != 1:
    raise ValueError("paired comparison must use one identical campaign, cohort, and point")
if any(set(arms) != expected_arms for arms in by_sample.values()):
    raise ValueError("paired comparison has a partial matched sample")
...
return PairedSizingResultV1(
    status="powered" if required is not None else "blocked_precision",
    design_sha256=design.digest(), ...,
)
```

### `src/bp_registry/quaternary/native_asced.py` (adapter/model, file-I/O)

**Analog:** `src/bp_registry/quaternary/native_asced.py:50-196` and `tests/canonical/quaternary/test_asced_evidence.py:1-180`.

Only add an injected-error adapter after a separate source/rights qualification. Preserve the pinned native identity and create a distinct `instrumented_native` evidence identity with source diff, original/modified digests, translation round-trip, injected-vector digest, and build receipt. Phase 10's aggregate receipt remains unavailable for matched-shot inference.

## Shared Patterns

### Immutable evidence and safe files

**Sources:** `campaigns/contracts.py:24-35`; `campaigns/controlled_execution.py:27-44`.

Canonical JSON is the sole identity representation. Evidence publication must be idempotent only for identical regular-file bytes; reject symlinks, substitutions, and plan/sample digest drift.

### Paired completeness and failure semantics

**Source:** `campaigns/statistics.py:586-642`.

Infrastructure interruption remains incomplete. Nonconvergence/no proposal/invalid syndrome enter the frozen all-shot failure mapping. Do not drop a partially nonconverged binary pair when a terminal combined candidate can be evaluated.

### Truth boundary

**Sources:** `quaternary/sampling.py:309-365`; `quaternary/evaluator.py:125-166`.

Sampling owns hidden Pauli truth. Decoder arms receive only declared observations and priors. Evaluate against the immutable original problem outside decoder policy code.

### Tests

**Sources:** `tests/canonical/quaternary/test_sampling.py:1-178`; `test_evaluator.py:1-207`; `test_campaign_contracts.py:1-431`; `test_campaign_execution.py:2069-2614`; `test_campaign_statistics.py` paired-table tests.

Use deterministic small fixtures, explicit tamper cases, replay equality, and tests for unavailable/partial evidence. Test through public contracts and preserve independent hand-oracle evaluation.

## No Analog Found

| File/Capability | Role | Data Flow | Reason |
|---|---|---|---|
| qualified injected-native aSCED source patch/binding | native adapter | file-I/O | Existing adapter admits only the pinned aggregate Phase 10 receipt; this work requires a new qualification checkpoint and must remain absent if approval is unavailable. |
| cross-point paired-contrast contract/result | model/utility | transform | Current paired table deliberately accepts one campaign/cohort/point; reuse its primitives but define a new versioned contract. |

## Metadata

**Analog search scope:** `src/bp_registry/campaigns`, `src/bp_registry/quaternary`, `tests/canonical/quaternary`, `tests`, `scripts`  
**Files scanned:** 21 tracked implementation and test analogs  
**Pattern extraction date:** 2026-10-14
