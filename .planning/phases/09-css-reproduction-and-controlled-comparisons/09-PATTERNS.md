# Phase 9: CSS Reproduction and Controlled Comparisons - Pattern Map

**Mapped:** 2026-10-11  
**Files analyzed:** 17 proposed files/modules  
**Analogs found:** 17 / 17

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `literature_policies/*/paper_reproduction/{PAPER.md,target-receipts.*}` | config / evidence receipt | file-I/O, transform | `literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md` | role-match |
| `literature_policies/qualification-v1.json` | config / registry | transform | `src/bp_registry/literature.py` | role-match |
| `src/bp_registry/campaigns/targets.py` | model / utility | transform, file-I/O | same file's table and digitization receipts | exact |
| `src/bp_registry/campaigns/contracts.py` | model / config | request-response | same file's `CampaignAssessmentV1` | exact |
| `src/bp_registry/campaigns/statistics.py` | service / utility | batch, transform | same file's fixed-shot and finite-look assessments | exact |
| `src/bp_registry/campaigns/execution.py` | service | event-driven, file-I/O | same file's canonical terminal/replay path | exact |
| `src/bp_registry/campaigns/reporting.py` | service | batch, transform | same file's sealed-merge report reconstruction | exact |
| `src/bp_registry/manifests.py` | model / config | transform | `MbbpCoordinateVoteV7` contract | exact |
| `src/bp_registry/literature.py` | controller / compiler | file-I/O, transform | `parse_literature_policy` | exact |
| `src/bp_registry/canonical/phase6.py` | controller / event projection | event-driven | `phase6_events` | exact |
| `src/bp_registry/canonical/candidate_selection.py` | service / model | transform | `CoordinateMajorityVote` | exact |
| `tests/test_campaign_targets.py` | test | file-I/O, transform | existing receipt contract tests | exact |
| `tests/test_campaign_statistics.py` | test | batch, transform | fixed-shot / finite-look tests | exact |
| `tests/test_campaign_execution.py` | test | event-driven, file-I/O | existing canonical attempt/replay tests | role-match |
| `tests/test_phase6_public_execution.py` | integration test | event-driven | existing policy-file public execution tests | exact |
| `tests/canonical/test_voting.py` | unit test | transform | existing vote primitive tests | exact |
| `tests/canonical/test_mbbp.py` | integration test | event-driven | existing MBBP candidate/ledger tests | role-match |

## Pattern Assignments

### `literature_policies/*/paper_reproduction/{PAPER.md,target-receipts.*}` (evidence receipt, file-I/O)

**Analog:** `literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md` (tracked)

**Source-status pattern** (lines 3-8):
```markdown
- Author implementation identity: unverified. Do not infer source-exact execution from the canonical implementation.
- All ten `.spec.toml` files are **non-runnable source records**. Separate ... `.toml` files are runnable **canonical adaptations** ... Exact source-experiment qualification remains open.
```

**Experiment identity / unresolved-fact pattern** (lines 29-38):
```markdown
- Candidate repository artifact: `data/artifacts/b1-panteleev-kalachev-v3.npz`, with project-derived logical basis. It is source-pinned ... but its **paper-experiment identity is not yet verified** for this figure.
...
- Published curve data and uncertainty: not yet digitized. No statistical tolerance, full denominator, or source settings manifest is frozen for these figures.
```

Copy this per paper and target. Record author implementation, ordered matrix/logical identity, stopping/denominator, target locator and uncertainty separately; do not turn a qualified adaptation into a source-faithful result in prose.

### `literature_policies/qualification-v1.json` (registry config, transform)

**Analog:** `src/bp_registry/literature.py` (tracked), `qualify_yao_source_records` (lines 396-460) and `qualify_rabeti_source_record` (lines 553-607).

**Compiler disposition pattern** (lines 252-360):
```python
def parse_literature_policy(path: str | Path) -> LiteraturePolicy:
    path = Path(path)
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    ...
    if record_kind == "source_specification":
        return _source_specification(path, document, raw_identity)
    ...
    return LiteraturePolicy(... execution_status="runnable", ...)
```

The registry should remain a derived, explicit inventory: source spec digest, runnable counterpart digest/path where present, blockers, source execution status, source-faithful boolean, and assessment state. Preserve unresolved fields; do not infer them while compiling.

### `src/bp_registry/campaigns/targets.py` (receipt models, transform/file-I/O)

**Analog:** same file, `SourceIdentityV1` through `TableTargetReceiptV1` (lines 93-160) and `DigitizationTargetReceiptV1` (lines 319-370).

**Imports and model pattern** (lines 8-18):
```python
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from ..manifests import StrictModel
```

**Digest-bound receipt pattern** (lines 148-160):
```python
class TableTargetReceiptV1(StrictModel):
    schema: Literal["table_target_receipt_v1"]
    source: SourceIdentityV1
    source_snapshot: ByteSnapshotV1
    locator: TableCellLocatorV1
    reported: ValueBoundsV1
    denominator: SourceDenominatorV1

    def digest(self) -> str:
        return _receipt_digest("table-target-receipt-v1", self)
```

Extend this model family for source-experiment/native-availability and failure-count target evidence. Keep bounded fields, canonical receipt digests, path confinement and literal source precision; use `TableTargetReceiptV1` for authored Yao/Rabeti coordinates and `DigitizationTargetReceiptV1` for Bhatnagar only if a pinned two-pass extraction is needed.

### `src/bp_registry/campaigns/contracts.py` (assessment contract, request-response)

**Analog:** same file, `CampaignAssessmentV1` (lines 203-260) and stopping models (lines 111-166).

**Frozen-union and validator pattern** (lines 203-254):
```python
class CampaignAssessmentV1(StrictModel):
    schema: Literal["campaign_assessment_v1"]
    targets: tuple[TargetReferenceV1, ...]
    interval: ExactIntervalV1
    families: tuple[AssessmentFamilyV1, ...]
    stopping: FixedShotStoppingV1 | FiniteLookStoppingV1
    outcome_matrix: OutcomeMatrixV1
    decision_rule: Literal["target_interval_containment_v1"]
    resources: ScientificResourceCapsV1

    @model_validator(mode="after")
    def complete_frozen_assessment(self) -> "CampaignAssessmentV1":
        ...
```

Add a bounded, explicit failure-count stopping member to this union rather than overloading `FixedShotStoppingV1`. It needs required failures, hard cap/censoring semantics, stopping-success mapping and frozen resource limits. Its `primitive_bytes()`/`digest()` must cover every scientific decision.

### `src/bp_registry/campaigns/statistics.py` (failure-count assessment, batch/transform)

**Analog:** same file, `exact_binomial_rate` (lines 141-174), `paired_outcome_table` (lines 287-376), and `finite_look_assessment` (lines 738-855).

**Validated exact-report pattern** (lines 141-174):
```python
def exact_binomial_rate(*, failures: int, shots: int, alpha: float,
                        count_receipt_sha256: str) -> ExactBinomialRateV1:
    """A two-sided exact Clopper-Pearson rate report with integer evidence."""
    failures = _bounded_int(failures, name="failures")
    shots = _bounded_int(shots, name="shots", minimum=1)
    if failures > shots:
        raise ValueError("failures cannot exceed shots")
    alpha = _probability(alpha, name="alpha")
    ...
```

**Paired-control pattern** (lines 287-376): accept complete arm/sample identity only, reject missing/duplicate arms, and calculate the table from the frozen outcome matrix. Reuse it for matched list-selection versus vote and all three focused mechanism questions.

**Error/censoring pattern** (lines 738-855): return a typed incomplete/inconclusive outcome for incomplete evidence, never a fixed-shot verdict after hitting a failure-count cap. Implement negative-binomial inversion in a new helper beside the existing exact report, with deterministic receipts and coverage tests.

### `src/bp_registry/campaigns/execution.py` and `src/bp_registry/campaigns/reporting.py` (ledger/replay and reports, event-driven)

**Analog:** `src/bp_registry/campaigns/execution.py` (tracked), `_campaign_terminal_fact` through `verify_canonical_attempt` (lines 662-778); `src/bp_registry/campaigns/reporting.py` (tracked), module contract (lines 1-5).

**Terminal projection/replay pattern** (lines 662-679 and 728-778):
```python
def _campaign_terminal_fact(events: list[dict[str, Any]], *, unit_key: str) -> dict[str, Any]:
    terminal_fact = _terminal_fact(events, unit_key=unit_key)
    ...
    if terminal_fact["outcome"] not in {...}:
        raise ValueError("canonical terminal outcome cannot be mapped into the frozen campaign taxonomy")
    return terminal_fact
```

```python
def verify_canonical_attempt(*, record: Mapping[str, Any], plan: CampaignWorkPlan) -> dict[str, Any]:
    ...
    events = read_canonical_events(ledger)
    terminal_fact = _campaign_terminal_fact(events, unit_key=unit.key)
    if events != record["events"] or terminal_fact != record["terminal_fact"]:
        raise ValueError("canonical attempt terminal differs from retained ledger")
```

Project the voting terminal, electorate/exclusions, ballots, tie, aggregate and original-syndrome result into supported immutable event facts, then recompute them during replay. Reporting must consume verified merged receipts only, following `reporting.py` lines 1-5; it must retain failed, censored, and inconclusive evidence.

### `src/bp_registry/manifests.py`, `src/bp_registry/literature.py`, and `src/bp_registry/canonical/phase6.py` (public voting controller, event-driven)

**Analogs:** `src/bp_registry/manifests.py` (tracked), `MbbpCoordinateVoteV7` (lines 613-647); `src/bp_registry/literature.py` (tracked), policy parsing/projection (lines 252-360); `src/bp_registry/canonical/phase6.py` (tracked), `phase6_events` (lines 20-77).

**Public grammar** (`manifests.py`, lines 613-627):
```python
class MbbpCoordinateVoteV7(StrictModel):
    object: Literal["correction_bits"]
    electorate_rule: Literal["admitted_members"]
    aggregation: Literal["coordinate_majority"]
    tie_bit: Literal[0, 1]
```

**Projection seam** (`phase6.py`, lines 28-77):
```python
for member in result.members:
    events.append(("member", member.as_evidence()))
for origin in result.selection.origins:
    events.append(("candidate_origin", origin.as_evidence()))
...
if vote_tie_bit is not None:
    raise ValueError("public Phase 6 vote projection is not yet executable")
```

Replace the intentional rejection only after the parser, MBBP execution result, ledger event mapping, terminal semantics, and replay verifier all support the `vote` branch. Preserve the absent-vote list-selection branch byte-for-byte in behavior. Policy parsing must continue to use `LiteraturePolicy` execution identity (`literature.py`, lines 88-132) and reject undeclared executable keys.

### `src/bp_registry/canonical/candidate_selection.py` (vote kernel, transform)

**Analog:** same file, `VoteBallot` through `CoordinateMajorityVote.vote` (lines 297-387).

**Fail-closed electorate and deterministic aggregation** (lines 297-387):
```python
@dataclass(frozen=True)
class VoteBallot:
    member_id: LineageId
    correction: tuple[int, ...]
    eligible: bool = True
    def __post_init__(self) -> None:
        object.__setattr__(self, "correction", _binary_tuple(self.correction, name="vote ballot"))
        if self.eligible is not True:
            raise ValueError("ineligible ballots fail closed")
```

```python
declared = tuple(sorted(electorate, key=lambda item: item.value))
if not declared or len(set(declared)) != len(declared):
    raise ValueError("vote electorate must be nonempty and duplicate-free")
...
valid = _original_valid(original, correction)
```

Do not duplicate coordinate-majority math in campaigns. Build a visible exclusion receipt outside `VoteBallot`, call this primitive only with admitted original-valid candidates, and emit a typed no-eligible terminal without calling it on an empty electorate.

### Test files (unit and integration tests)

**Analogs:** `tests/test_campaign_targets.py` (tracked), lines 1-186; `tests/test_campaign_statistics.py` (tracked), lines 1-260 and finite-look tests at lines 738-855 of the source; `tests/test_phase6_public_execution.py` (tracked), lines 1-135; `tests/canonical/test_voting.py` (tracked), lines 1-109.

**Test style:** use direct typed fixture constructors, one behavior per test, `pytest.raises(ValueError, match=...)` for closed boundaries, and exact assertions for receipt IDs, terminal status, evidence payload, and replayed facts. Add:

- target/native-qualification fixtures for all three papers and authored/digitized receipt provenance;
- failure-count boundary/coverage/censoring tests, while locking existing fixed-shot results;
- policy-file vote parse, eligible/ineligible/no-eligible/tie/invalid-aggregate/order-invariance and replay tests;
- one retained Yao tracer and one matched two-arm fixture for each comparison family, asserting shared sample identity, full denominator, separate work, runtime/resource receipt and report verdict.

## Shared Patterns

### Immutable evidence and source qualification
**Sources:** `src/bp_registry/campaigns/targets.py` lines 48-160; `literature_policies/qualification-v1.json` lines 1-100.

Use `StrictModel`, bounded validators, canonical JSON bytes and domain-separated SHA-256 digests. Preserve literal revision/digest, target locator, denominator/stopping status and unresolved identity blockers. An absent native reference is an explicit evidence state, never a zero-valued measurement.

### Truth boundary and validation
**Source:** `src/bp_registry/canonical/candidate_selection.py` lines 22-32 and 343-387.

The selection/vote controller receives decoder-visible candidates only. `_original_valid` is applied after aggregation against the immutable original problem; hidden physical error never reaches a policy.

### Replayability and terminal accounting
**Sources:** `src/bp_registry/campaigns/execution.py` lines 683-778; `src/bp_registry/campaigns/reporting.py` lines 1-5.

Persist canonical events, terminal fact, work vector and hashes, then re-read the ledger and compare reconstructed evidence during verification. Reports rebuild denominators from sealed merge evidence and retain incomplete records.

### Matched comparisons and work
**Sources:** `src/bp_registry/campaigns/contracts.py` lines 361-429; `src/bp_registry/campaigns/statistics.py` lines 287-376 and 568-658.

Require one frozen paired plan and full sample identity. Record actual work separately from configured limits; include all terminal outcomes in the all-shot denominator and expose conditional acceptance separately.

## No Analog Found

| File / capability | Role | Data Flow | Reason |
|---|---|---|---|
| Failure-count stopping distribution and exact inverse interval | statistics service | batch, transform | Existing code supports fixed-shot and finite-look inference only; use its validation, receipt, and typed-result patterns while implementing the new negative-binomial mathematics. |
| Paper-specific native-reference availability receipt | evidence model | transform | Existing literature inventory tracks blockers but has no typed per-target native assessment receipt; extend target/evidence patterns without collapsing unavailable to zero. |

## Metadata

**Analog search scope:** `src/bp_registry/{campaigns,canonical}`, `literature_policies`, `tests`, `docs`  
**Files scanned:** 17 tracked analogs plus Phase 9 context/research  
**Tracked-source gate:** every named analog was verified with `git ls-files`  
**Pattern extraction date:** 2026-10-11
