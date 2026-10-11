"""Strict campaign-specification and acyclic one-unit plan records."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ..manifests import StrictModel


_SHA256 = r"^[0-9a-f]{64}$"
_MAX_EVENTS = 1_000_000
_MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
_MAX_STORAGE_BYTES = 1_024 * 1024 * 1024
_MAX_DECODER_WORK = 1_000_000_000_000
_TERMINAL_STATUSES = frozenset({
    "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
    "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
    "infrastructure_interruption",
})


def canonical_json_bytes(value: object) -> bytes:
    """Return the sole compact, finite JSON representation used for identities."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _digest(domain: str, payload: bytes) -> str:
    return sha256(domain.encode("ascii") + b"\0" + payload).hexdigest()


def _finite_probability(value: float, *, name: str, allow_zero: bool = False) -> float:
    if not math.isfinite(value) or value < 0.0 or value >= 1.0 or (not allow_zero and value == 0.0):
        raise ValueError(f"{name} must be a finite probability in the declared range")
    return value


class ScientificResourceCapsV1(StrictModel):
    """Digest-bound scientific limits; scheduler allocation is intentionally absent."""

    max_shots: int = Field(ge=1, le=_MAX_EVENTS)
    max_looks: int = Field(ge=1, le=1_000)
    max_batch_size: int = Field(ge=1, le=_MAX_EVENTS)
    max_decoder_work: int = Field(ge=1, le=_MAX_DECODER_WORK)
    max_events: int = Field(ge=1, le=_MAX_EVENTS)
    max_evidence_bytes: int = Field(ge=1, le=_MAX_EVIDENCE_BYTES)
    max_storage_bytes: int = Field(ge=1, le=_MAX_STORAGE_BYTES)


class TargetReferenceV1(StrictModel):
    """One frozen target interval and its content-addressed provenance receipt."""

    target_id: str = Field(min_length=1, max_length=128)
    target_receipt_sha256: str = Field(pattern=_SHA256)
    lower: float
    upper: float
    absolute_tolerance: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def valid_target_band(self) -> "TargetReferenceV1":
        for name in ("lower", "upper", "absolute_tolerance"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        if self.lower > self.upper:
            raise ValueError("target lower bound cannot exceed its upper bound")
        return self


class ExactIntervalV1(StrictModel):
    method: Literal["exact_clopper_pearson"]
    confidence_level: float

    @field_validator("confidence_level")
    @classmethod
    def finite_confidence_level(cls, value: float) -> float:
        return _finite_probability(value, name="confidence_level")


class AssessmentFamilyV1(StrictModel):
    family_id: str = Field(min_length=1, max_length=128)
    alpha: float
    member_target_ids: tuple[str, ...] = Field(min_length=1, max_length=1_000)

    @field_validator("member_target_ids", mode="before")
    @classmethod
    def tuple_members(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("alpha")
    @classmethod
    def finite_alpha(cls, value: float) -> float:
        return _finite_probability(value, name="family alpha")

    @model_validator(mode="after")
    def unique_members(self) -> "AssessmentFamilyV1":
        if len(set(self.member_target_ids)) != len(self.member_target_ids) or any(not member for member in self.member_target_ids):
            raise ValueError("assessment-family target membership must be nonempty and unique")
        return self


class FixedShotStoppingV1(StrictModel):
    mode: Literal["fixed_shot"]
    final_shots: int = Field(ge=1, le=_MAX_EVENTS)
    batch_size: int = Field(ge=1, le=_MAX_EVENTS)

    @model_validator(mode="after")
    def full_final_batch(self) -> "FixedShotStoppingV1":
        if self.batch_size > self.final_shots:
            raise ValueError("fixed-shot batch_size cannot exceed final_shots")
        return self


class LookAlphaAllocationV1(StrictModel):
    family_id: str = Field(min_length=1, max_length=128)
    target_id: str = Field(min_length=1, max_length=128)
    look: int = Field(ge=1, le=_MAX_EVENTS)
    alpha: float

    @field_validator("alpha")
    @classmethod
    def finite_local_alpha(cls, value: float) -> float:
        return _finite_probability(value, name="local alpha")


class FiniteLookStoppingV1(StrictModel):
    mode: Literal["finite_look"]
    cumulative_looks: tuple[int, ...] = Field(min_length=1, max_length=1_000)
    batch_sizes: tuple[int, ...] = Field(min_length=1, max_length=1_000)
    minimum_terminal_shots: int = Field(ge=1, le=_MAX_EVENTS)
    stop_rule: Literal["all_primary_decisions_resolved_or_maximum_reached"]
    alpha_allocations: tuple[LookAlphaAllocationV1, ...] = Field(min_length=1, max_length=1_000_000)

    @field_validator("cumulative_looks", "batch_sizes", mode="before")
    @classmethod
    def tuple_ints(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("alpha_allocations", mode="before")
    @classmethod
    def tuple_allocations(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def whole_batch_boundaries(self) -> "FiniteLookStoppingV1":
        if len(self.cumulative_looks) != len(self.batch_sizes):
            raise ValueError("finite-look boundaries and batch sizes must have equal length")
        previous = 0
        for boundary, batch_size in zip(self.cumulative_looks, self.batch_sizes, strict=True):
            if boundary <= previous or boundary > _MAX_EVENTS or batch_size < 1 or batch_size > _MAX_EVENTS:
                raise ValueError("finite-look boundaries must be strictly increasing bounded integers")
            if (boundary - previous) % batch_size:
                raise ValueError("each finite-look increment must contain whole declared batches")
            previous = boundary
        if self.minimum_terminal_shots > self.cumulative_looks[-1]:
            raise ValueError("minimum terminal evidence cannot exceed the final look")
        return self


class OutcomeTreatmentV1(StrictModel):
    terminal_status: Literal[
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
        "infrastructure_interruption",
    ]
    all_shot: Literal["success", "failure", "incomplete"]
    conditional: Literal["accepted", "excluded", "incomplete"]


class OutcomeMatrixV1(StrictModel):
    rule_id: Literal["all_shot_v1"]
    treatments: tuple[OutcomeTreatmentV1, ...] = Field(min_length=len(_TERMINAL_STATUSES), max_length=len(_TERMINAL_STATUSES))

    @field_validator("treatments", mode="before")
    @classmethod
    def tuple_treatments(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def total_no_silent_drop_mapping(self) -> "OutcomeMatrixV1":
        mapping = {item.terminal_status: item for item in self.treatments}
        if set(mapping) != _TERMINAL_STATUSES or len(mapping) != len(self.treatments):
            raise ValueError("outcome matrix must cover each terminal status exactly once")
        interruption = mapping["infrastructure_interruption"]
        if interruption.all_shot != "incomplete" or interruption.conditional != "incomplete":
            raise ValueError("infrastructure interruption must remain incomplete")
        for status in ("invalid_syndrome", "no_proposal", "nonconvergence", "timeout"):
            treatment = mapping[status]
            if treatment.all_shot != "failure" or treatment.conditional != "excluded":
                raise ValueError(f"{status} must be all-shot failure and conditionally excluded")
        return self


class CampaignAssessmentV1(StrictModel):
    """All outcome-independent assessment semantics that must freeze before launch."""

    schema_name: Literal["campaign_assessment_v1"] = Field(alias="schema", serialization_alias="schema")
    targets: tuple[TargetReferenceV1, ...] = Field(min_length=1, max_length=1_000)
    interval: ExactIntervalV1
    families: tuple[AssessmentFamilyV1, ...] = Field(min_length=1, max_length=1_000)
    stopping: FixedShotStoppingV1 | FiniteLookStoppingV1
    outcome_matrix: OutcomeMatrixV1
    decision_rule: Literal["target_interval_containment_v1"]
    resources: ScientificResourceCapsV1

    @field_validator("targets", "families", mode="before")
    @classmethod
    def tuple_records(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def complete_frozen_assessment(self) -> "CampaignAssessmentV1":
        target_ids = tuple(target.target_id for target in self.targets)
        family_ids = tuple(family.family_id for family in self.families)
        if len(set(target_ids)) != len(target_ids) or len(set(family_ids)) != len(family_ids):
            raise ValueError("target and family identities must be unique")
        if any(member not in target_ids for family in self.families for member in family.member_target_ids):
            raise ValueError("assessment family references an unknown target")
        if set(member for family in self.families for member in family.member_target_ids) != set(target_ids):
            raise ValueError("every target must belong to a declared comparison family")
        if isinstance(self.stopping, FixedShotStoppingV1):
            if self.resources.max_looks != 1 or self.resources.max_shots != self.stopping.final_shots:
                raise ValueError("fixed-shot resources must declare exactly one final look")
        else:
            if self.resources.max_looks != len(self.stopping.cumulative_looks) or self.resources.max_shots != self.stopping.cumulative_looks[-1]:
                raise ValueError("finite-look resources must match the declared final look")
            if self.resources.max_batch_size < max(self.stopping.batch_sizes):
                raise ValueError("resource batch cap cannot be below a declared finite-look batch")
            expected = {
                (family.family_id, target_id, look)
                for family in self.families
                for target_id in family.member_target_ids
                for look in self.stopping.cumulative_looks
            }
            allocations = {(item.family_id, item.target_id, item.look): item.alpha for item in self.stopping.alpha_allocations}
            if set(allocations) != expected or len(allocations) != len(self.stopping.alpha_allocations):
                raise ValueError("finite-look alpha allocations must cover every family target and declared look exactly once")
            for family in self.families:
                spent = sum(value for (family_id, _, _), value in allocations.items() if family_id == family.family_id)
                if spent > family.alpha + 1e-15:
                    raise ValueError("finite-look alpha allocations cannot exceed their family alpha")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-campaign-assessment-v1", self.primitive_bytes())


class CampaignSpecV1(StrictModel):
    """Primitive scientific inputs for one fixed-shot CSS campaign unit.

    Executor and scheduler observations deliberately have no field here.  They
    may be recorded in a receipt, but cannot change this specification digest.
    """

    schema_name: Literal["campaign_spec_v1"] = Field(alias="schema", serialization_alias="schema")
    inner_manifest_path: str = Field(min_length=1, max_length=512)
    inner_manifest_sha256: str = Field(pattern=_SHA256)
    source_lock_sha256: str = Field(pattern=_SHA256)
    environment_lock_sha256: str = Field(pattern=_SHA256)
    cohort_id: str = Field(min_length=1, max_length=128)
    point_id: str = Field(min_length=1, max_length=128)
    sample_namespace: str = Field(min_length=1, max_length=256)
    sample_id: int = Field(ge=0, le=1_000_000)
    arm_id: str = Field(min_length=1, max_length=128)
    decoder_seed_identity: str = Field(min_length=1, max_length=256)
    final_look: int = Field(ge=1, le=1_000_000)
    alpha: float = Field(gt=0.0, lt=1.0)
    outcome_rule: Literal["all_terminal_shots_are_logical_failures"]
    max_events: int = Field(ge=1, le=_MAX_EVENTS)
    max_evidence_bytes: int = Field(ge=1, le=_MAX_EVIDENCE_BYTES)
    assessment: CampaignAssessmentV1 | None = None

    @field_validator("inner_manifest_path")
    @classmethod
    def confined_relative_manifest_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("inner_manifest_path must be a confined relative path")
        return value

    @field_validator("alpha")
    @classmethod
    def finite_alpha(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("alpha must be finite")
        return value

    @model_validator(mode="after")
    def assessment_stopping_matches_campaign_look(self) -> "CampaignSpecV1":
        """Legacy one-unit records have no assessment; assessed campaigns bind its look index."""
        if self.assessment is None:
            return self
        expected_final_look = (
            1
            if isinstance(self.assessment.stopping, FixedShotStoppingV1)
            else len(self.assessment.stopping.cumulative_looks)
        )
        if self.final_look != expected_final_look:
            raise ValueError("campaign final_look must equal the frozen assessment final look")
        return self

    def primitive_bytes(self) -> bytes:
        """Canonical bytes before any derived unit or plan identity exists."""
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-campaign-spec-v1", self.primitive_bytes())


@dataclass(frozen=True, slots=True)
class CampaignPlanV1:
    """The one-unit frozen plan derived from a primitive campaign specification."""

    campaign_spec: CampaignSpecV1
    campaign_spec_digest: str
    unit_key: str
    shard_id: str
    campaign_plan_preimage: bytes
    campaign_plan_digest: str

    @property
    def campaign_spec_bytes(self) -> bytes:
        return self.campaign_spec.primitive_bytes()

    @property
    def physical_sample_identity(self) -> str:
        payload = canonical_json_bytes({
            "campaign_spec_digest": self.campaign_spec_digest,
            "cohort_id": self.campaign_spec.cohort_id,
            "point_id": self.campaign_spec.point_id,
            "sample_namespace": self.campaign_spec.sample_namespace,
            "sample_id": self.campaign_spec.sample_id,
        })
        return _digest("bp-registry-campaign-physical-sample-v1", payload)

    @property
    def decoder_randomness_identity(self) -> str:
        payload = canonical_json_bytes({
            "campaign_spec_digest": self.campaign_spec_digest,
            "cohort_id": self.campaign_spec.cohort_id,
            "point_id": self.campaign_spec.point_id,
            "sample_id": self.campaign_spec.sample_id,
            "arm_id": self.campaign_spec.arm_id,
            "decoder_seed_identity": self.campaign_spec.decoder_seed_identity,
        })
        return _digest("bp-registry-campaign-decoder-randomness-v1", payload)


def build_one_unit_plan(spec: CampaignSpecV1) -> CampaignPlanV1:
    """Derive one unit before hashing the unsigned plan that seals it."""
    spec_digest = spec.digest()
    coordinate = {
        "campaign_spec_digest": spec_digest,
        "cohort_id": spec.cohort_id,
        "point_id": spec.point_id,
        "sample_id": spec.sample_id,
        "arm_id": spec.arm_id,
    }
    unit_key = _digest("bp-registry-campaign-unit-v1", canonical_json_bytes(coordinate))
    shard_id = _digest("bp-registry-campaign-shard-v1", canonical_json_bytes({"unit_keys": [unit_key]}))
    unsigned_plan = {
        "schema": "campaign_plan_v1",
        "campaign_spec_digest": spec_digest,
        "unit_keys": [unit_key],
        "shards": [{"shard_id": shard_id, "unit_keys": [unit_key]}],
    }
    preimage = canonical_json_bytes(unsigned_plan)
    return CampaignPlanV1(
        campaign_spec=spec,
        campaign_spec_digest=spec_digest,
        unit_key=unit_key,
        shard_id=shard_id,
        campaign_plan_preimage=preimage,
        campaign_plan_digest=_digest("bp-registry-campaign-plan-v1", preimage),
    )
