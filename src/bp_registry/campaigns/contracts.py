"""Strict campaign-specification and acyclic one-unit plan records."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import base64
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


class CampaignArmV1(StrictModel):
    """One canonical decoder arm confined to its caller-owned campaign root."""

    arm_id: str = Field(min_length=1, max_length=128)
    manifest_path: str = Field(min_length=1, max_length=512)
    manifest_sha256: str = Field(pattern=_SHA256)
    decoder_seed_identity: str = Field(min_length=1, max_length=256)

    @field_validator("manifest_path")
    @classmethod
    def confined_manifest_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("manifest_path must be a confined relative path")
        return value


class SharedSamplerContractV1(StrictModel):
    """All material that must agree before one physical error can be paired."""

    code_id: str = Field(min_length=1, max_length=256)
    artifact_raw_sha256: str = Field(pattern=_SHA256)
    artifact_semantic_sha256: str = Field(pattern=_SHA256)
    matrix_sha256: str = Field(pattern=_SHA256)
    channel_family: Literal["css_code_capacity_v1"]
    x_error_rate: float = Field(ge=0.0, le=1.0)
    z_error_rate: float = Field(ge=0.0, le=1.0)
    sampler_algorithm: Literal["bp_registry_sample_shot_v1"]
    sampler_version: Literal["v1"]
    physical_sample_namespace: str = Field(min_length=1, max_length=256)
    physical_sample_seed: int = Field(ge=0, le=2**63 - 1)

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json"))

    def digest(self) -> str:
        return _digest("bp-registry-shared-sampler-v1", self.primitive_bytes())


class CampaignWorkCoordinateV1(StrictModel):
    """Arm-neutral point and finite physical sample identifiers."""

    cohort_id: str = Field(min_length=1, max_length=256)
    point_id: str = Field(min_length=1, max_length=256)
    sample_namespace: str = Field(min_length=1, max_length=256)
    sample_ids: tuple[int, ...] = Field(min_length=1, max_length=_MAX_EVENTS)

    @field_validator("sample_ids", mode="before")
    @classmethod
    def coerce_sequence_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def unique_sample_ids(self) -> "CampaignWorkCoordinateV1":
        if (len(set(self.sample_ids)) != len(self.sample_ids)
                or any(type(value) is not int or value < 0 or value > _MAX_EVENTS for value in self.sample_ids)):
            raise ValueError("sample_ids must be unique bounded integers")
        return self


class CampaignWorkSpecV1(StrictModel):
    """Strict primitive input for a complete, paired canonical campaign."""

    schema_name: Literal["campaign_work_spec_v1"] = Field(alias="schema", serialization_alias="schema")
    arms: tuple[CampaignArmV1, ...] = Field(min_length=2, max_length=128)
    shared_sampler: SharedSamplerContractV1
    coordinates: tuple[CampaignWorkCoordinateV1, ...] = Field(min_length=1, max_length=_MAX_EVENTS)
    look_sample_boundaries: tuple[int, ...] = Field(min_length=1, max_length=1_000)
    units_per_shard: int = Field(ge=1, le=_MAX_EVENTS)
    assessment: CampaignAssessmentV1
    source_lock_sha256: str = Field(pattern=_SHA256)
    environment_lock_sha256: str = Field(pattern=_SHA256)
    dependency_lock_sha256: str = Field(pattern=_SHA256)
    target_arm_ids: dict[str, str] = Field(min_length=1, max_length=1_000)
    source_denominator_required_by_target: dict[str, bool] = Field(default_factory=dict)
    source_denominators: dict[str, int | None] = Field(default_factory=dict)

    @field_validator("arms", "coordinates", "look_sample_boundaries", mode="before")
    @classmethod
    def tuple_fields(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def complete_pairing_contract(self) -> "CampaignWorkSpecV1":
        arm_ids = tuple(arm.arm_id for arm in self.arms)
        coordinate_ids = tuple((item.cohort_id, item.point_id, item.sample_namespace) for item in self.coordinates)
        sample_count = sum(len(item.sample_ids) for item in self.coordinates)
        if len(set(arm_ids)) != len(arm_ids) or len(set(coordinate_ids)) != len(coordinate_ids):
            raise ValueError("campaign work arm and coordinate identities must be unique")
        if any(item.sample_namespace != self.shared_sampler.physical_sample_namespace for item in self.coordinates):
            raise ValueError("all coordinates must use the shared physical sample namespace")
        if (tuple(sorted(self.look_sample_boundaries)) != self.look_sample_boundaries
                or len(set(self.look_sample_boundaries)) != len(self.look_sample_boundaries)
                or self.look_sample_boundaries[-1] != sample_count):
            raise ValueError("look boundaries must cover each planned physical sample exactly once")
        target_ids = {target.target_id for target in self.assessment.targets}
        if set(self.target_arm_ids) != target_ids or any(arm_id not in arm_ids for arm_id in self.target_arm_ids.values()):
            raise ValueError("each assessed target requires one declared arm")
        if set(self.source_denominator_required_by_target) - target_ids or set(self.source_denominators) - target_ids:
            raise ValueError("source denominator fields reference an unknown target")
        if sample_count * len(self.arms) > self.assessment.resources.max_events:
            raise ValueError("paired work expansion exceeds frozen event cap")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-campaign-work-spec-v1", self.primitive_bytes())


class MaterializedPhysicalSampleV1(StrictModel):
    """Immutable byte-level physical sample retained before either arm decodes."""

    schema_name: Literal["materialized_physical_sample_v1"] = Field(alias="schema", serialization_alias="schema")
    physical_sample_identity: str = Field(pattern=_SHA256)
    sample_seed_identity: str = Field(pattern=_SHA256)
    cohort_id: str = Field(min_length=1, max_length=256)
    point_id: str = Field(min_length=1, max_length=256)
    sample_namespace: str = Field(min_length=1, max_length=256)
    sample_id: int = Field(ge=0, le=_MAX_EVENTS)
    sampler_contract_sha256: str = Field(pattern=_SHA256)
    x_dtype: Literal["uint8"]
    x_shape: tuple[int, ...] = Field(min_length=1, max_length=2)
    x_bytes_b64: str
    z_dtype: Literal["uint8"]
    z_shape: tuple[int, ...] = Field(min_length=1, max_length=2)
    z_bytes_b64: str
    observations: dict[str, dict[str, Any]] = Field(min_length=1, max_length=8)
    physical_error_sha256: str = Field(pattern=_SHA256)
    materialized_sample_sha256: str = Field(pattern=_SHA256)

    @field_validator("x_shape", "z_shape", mode="before")
    @classmethod
    def tuple_shapes(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def byte_digests_bind_payload(self) -> "MaterializedPhysicalSampleV1":
        try:
            x_bytes, z_bytes = base64.b64decode(self.x_bytes_b64, validate=True), base64.b64decode(self.z_bytes_b64, validate=True)
        except Exception as error:
            raise ValueError("materialized sample has invalid base64 bytes") from error
        error_payload = canonical_json_bytes({"x": self.x_bytes_b64, "z": self.z_bytes_b64})
        if self.physical_error_sha256 != _digest("bp-registry-physical-error-v1", error_payload):
            raise ValueError("materialized sample physical error digest differs from bytes")
        unsigned = self.model_dump(mode="json", by_alias=True, exclude={"materialized_sample_sha256"})
        if self.materialized_sample_sha256 != _digest("bp-registry-materialized-sample-v1", canonical_json_bytes(unsigned)):
            raise ValueError("materialized sample digest differs from bytes")
        if not x_bytes or not z_bytes:
            raise ValueError("materialized error vectors must be nonempty")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))


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
