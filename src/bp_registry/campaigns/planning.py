"""Freeze campaign unit membership before an executor receives any work."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Final, Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from ..manifests import StrictModel
from .contracts import CampaignWorkSpecV1, canonical_json_bytes
from .identity import decoder_randomness_identity, physical_sample_identity, unit_key


_MAX_UNITS: Final = 1_000_000
_MAX_SHARDS: Final = 100_000
_MAX_SERIALIZED_BYTES: Final = 64 * 1024 * 1024


def _plan_digest(payload: object) -> str:
    return sha256(
        b"bp-registry-campaign-plan-v1\0" + canonical_json_bytes(payload)
    ).hexdigest()


def _shard_id(*, look: int, unit_keys: Sequence[str]) -> str:
    return sha256(
        b"bp-registry-campaign-shard-v2\0" + canonical_json_bytes({
            "look": look, "unit_keys": list(unit_keys),
        })
    ).hexdigest()


class CampaignCoordinateV1(StrictModel):
    """One arm-neutral cohort/point namespace and its physical sample IDs."""

    cohort_id: str = Field(min_length=1, max_length=256)
    point_id: str = Field(min_length=1, max_length=256)
    sample_namespace: str = Field(min_length=1, max_length=256)
    sample_ids: tuple[int, ...] = Field(min_length=1, max_length=_MAX_UNITS)

    @field_validator("sample_ids", mode="before")
    @classmethod
    def tuple_sample_ids(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def unique_bounded_sample_ids(self) -> "CampaignCoordinateV1":
        if any(type(sample_id) is not int or sample_id < 0 or sample_id > _MAX_UNITS for sample_id in self.sample_ids):
            raise ValueError("sample IDs must be bounded nonnegative integers")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample IDs must be unique")
        return self

    def sort_key(self) -> tuple[str, str, str]:
        return self.cohort_id, self.point_id, self.sample_namespace


@dataclass(frozen=True, slots=True)
class UnitKey:
    """An immutable arm-specific contribution to exactly one sample group."""

    key: str
    campaign_spec_digest: str
    cohort_id: str
    point_id: str
    sample_namespace: str
    sample_id: int
    arm_id: str
    physical_sample_identity: str
    decoder_randomness_identity: str

    def payload(self) -> dict[str, object]:
        return {
            "unit_key": self.key,
            "campaign_spec_digest": self.campaign_spec_digest,
            "cohort_id": self.cohort_id,
            "point_id": self.point_id,
            "sample_namespace": self.sample_namespace,
            "sample_id": self.sample_id,
            "arm_id": self.arm_id,
            "physical_sample_identity": self.physical_sample_identity,
            "decoder_randomness_identity": self.decoder_randomness_identity,
        }


@dataclass(frozen=True, slots=True)
class ShardPlan:
    """A bounded contiguous set of frozen units assigned later to any executor."""

    shard_id: str
    look: int
    unit_keys: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {"shard_id": self.shard_id, "look": self.look, "unit_keys": list(self.unit_keys)}


@dataclass(frozen=True, slots=True)
class CampaignWorkPlan:
    """Complete deterministic work plan, including finite-look prefixes and tails."""

    campaign_spec_digest: str
    units: tuple[UnitKey, ...]
    shards: tuple[ShardPlan, ...]
    look_boundaries: tuple[int, ...]
    units_per_sample_group: int
    campaign_plan_preimage: bytes
    campaign_plan_digest: str
    work_spec: CampaignWorkSpecV1 | None = None

    @property
    def unit_keys(self) -> tuple[str, ...]:
        return tuple(unit.key for unit in self.units)

    def completed_prefix(self, look: int) -> tuple[str, ...]:
        if type(look) is not int or not 1 <= look <= len(self.look_boundaries):
            raise ValueError("look must be a declared completed look")
        unit_boundary = self.look_boundaries[look - 1] * self.units_per_sample_group
        return self.unit_keys[:unit_boundary]

    def authorized_tail(self, look: int) -> tuple[str, ...]:
        unit_boundary = self.look_boundaries[look - 1] * self.units_per_sample_group
        return self.unit_keys[unit_boundary:]


def _bounded_int(value: int, *, name: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [1, {maximum}]")
    return value


def _validate_digest(value: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("campaign_spec_digest must be a lowercase SHA-256 digest")
    return value


def freeze_work_plan(
    *,
    campaign_spec_digest: str,
    coordinates: Sequence[CampaignCoordinateV1],
    arm_seed_identities: Mapping[str, str],
    look_sample_boundaries: Sequence[int],
    units_per_shard: int,
    max_total_units: int = _MAX_UNITS,
    max_shards: int = _MAX_SHARDS,
    max_serialized_bytes: int = _MAX_SERIALIZED_BYTES,
) -> CampaignWorkPlan:
    """Derive and seal all work before local or scheduler allocation is chosen."""
    digest = _validate_digest(campaign_spec_digest)
    shard_width = _bounded_int(units_per_shard, name="units_per_shard", maximum=_MAX_UNITS)
    unit_cap = _bounded_int(max_total_units, name="max_total_units", maximum=_MAX_UNITS)
    shard_cap = _bounded_int(max_shards, name="max_shards", maximum=_MAX_SHARDS)
    byte_cap = _bounded_int(max_serialized_bytes, name="max_serialized_bytes", maximum=_MAX_SERIALIZED_BYTES)
    if not coordinates:
        raise ValueError("coordinates must not be empty")
    typed_coordinates = tuple(coordinates)
    if any(not isinstance(coordinate, CampaignCoordinateV1) for coordinate in typed_coordinates):
        raise ValueError("coordinates must contain validated CampaignCoordinateV1 records")
    if len({coordinate.sort_key() for coordinate in typed_coordinates}) != len(typed_coordinates):
        raise ValueError("campaign coordinates must be unique")
    if not arm_seed_identities:
        raise ValueError("arm_seed_identities must not be empty")
    arms = tuple(sorted(arm_seed_identities.items()))
    if any(not isinstance(arm, str) or not arm or not isinstance(seed, str) or not seed for arm, seed in arms):
        raise ValueError("arm IDs and decoder seed identities must be nonempty strings")

    ordered_groups = tuple(
        (coordinate, sample_id)
        for coordinate in sorted(typed_coordinates, key=CampaignCoordinateV1.sort_key)
        for sample_id in sorted(coordinate.sample_ids)
    )
    boundaries = tuple(look_sample_boundaries)
    if (not boundaries or any(type(boundary) is not int for boundary in boundaries)
            or tuple(sorted(boundaries)) != boundaries or len(set(boundaries)) != len(boundaries)
            or boundaries[0] < 1 or boundaries[-1] != len(ordered_groups)):
        raise ValueError("look_sample_boundaries must be increasing and end at the complete sample set")
    expected_count = len(ordered_groups) * len(arms)
    if expected_count > unit_cap:
        raise ValueError("expanded campaign exceeds max_total_units")

    units = tuple(
        UnitKey(
            key=unit_key(campaign_spec_digest=digest, cohort_id=coordinate.cohort_id,
                         point_id=coordinate.point_id, sample_namespace=coordinate.sample_namespace,
                         sample_id=sample_id, arm_id=arm_id),
            campaign_spec_digest=digest, cohort_id=coordinate.cohort_id, point_id=coordinate.point_id,
            sample_namespace=coordinate.sample_namespace, sample_id=sample_id, arm_id=arm_id,
            physical_sample_identity=physical_sample_identity(
                campaign_spec_digest=digest, cohort_id=coordinate.cohort_id, point_id=coordinate.point_id,
                sample_namespace=coordinate.sample_namespace, sample_id=sample_id,
            ),
            decoder_randomness_identity=decoder_randomness_identity(
                campaign_spec_digest=digest, arm_id=arm_id, sample_id=sample_id,
                decoder_seed_identity=seed_identity,
            ),
        )
        for coordinate, sample_id in ordered_groups
        for arm_id, seed_identity in arms
    )
    if len({unit.key for unit in units}) != len(units):
        raise ValueError("expanded campaign contains duplicate unit keys")

    shards: list[ShardPlan] = []
    previous_boundary = 0
    for look, boundary in enumerate(boundaries, start=1):
        look_units = units[previous_boundary * len(arms):boundary * len(arms)]
        for start in range(0, len(look_units), shard_width):
            keys = tuple(unit.key for unit in look_units[start:start + shard_width])
            shards.append(ShardPlan(shard_id=_shard_id(look=look, unit_keys=keys), look=look, unit_keys=keys))
        previous_boundary = boundary
    if len(shards) > shard_cap:
        raise ValueError("expanded campaign exceeds max_shards")
    if len({shard.shard_id for shard in shards}) != len(shards):
        raise ValueError("expanded campaign contains duplicate shard IDs")
    if tuple(key for shard in shards for key in shard.unit_keys) != tuple(unit.key for unit in units):
        raise ValueError("shards must cover every unit exactly once in frozen order")

    unsigned_payload = {
        "schema": "campaign_work_plan_v1",
        "campaign_spec_digest": digest,
        "units": [unit.payload() for unit in units],
        "shards": [shard.payload() for shard in shards],
        "look_sample_boundaries": list(boundaries),
    }
    preimage = canonical_json_bytes(unsigned_payload)
    if len(preimage) > byte_cap:
        raise ValueError("serialized campaign plan exceeds max_serialized_bytes")
    return CampaignWorkPlan(
        campaign_spec_digest=digest, units=units, shards=tuple(shards), look_boundaries=boundaries,
        units_per_sample_group=len(arms),
        campaign_plan_preimage=preimage, campaign_plan_digest=_plan_digest(unsigned_payload),
    )


def freeze_campaign_work_spec(spec: CampaignWorkSpecV1) -> CampaignWorkPlan:
    """Freeze a complete paired document through the established work algebra."""
    if not isinstance(spec, CampaignWorkSpecV1):
        raise ValueError("freeze_campaign_work_spec requires CampaignWorkSpecV1")
    plan = freeze_work_plan(
        campaign_spec_digest=spec.digest(),
        coordinates=tuple(CampaignCoordinateV1(
            cohort_id=item.cohort_id, point_id=item.point_id,
            sample_namespace=item.sample_namespace, sample_ids=item.sample_ids,
        ) for item in spec.coordinates),
        arm_seed_identities={arm.arm_id: arm.decoder_seed_identity for arm in spec.arms},
        look_sample_boundaries=spec.look_sample_boundaries,
        units_per_shard=spec.units_per_shard,
        max_total_units=spec.assessment.resources.max_events,
        max_shards=min(_MAX_SHARDS, spec.assessment.resources.max_events),
        max_serialized_bytes=spec.assessment.resources.max_evidence_bytes,
    )
    return CampaignWorkPlan(
        campaign_spec_digest=plan.campaign_spec_digest, units=plan.units, shards=plan.shards,
        look_boundaries=plan.look_boundaries, units_per_sample_group=plan.units_per_sample_group,
        campaign_plan_preimage=plan.campaign_plan_preimage, campaign_plan_digest=plan.campaign_plan_digest,
        work_spec=spec,
    )


def validate_executor_allocation(plan: CampaignWorkPlan, allocation: Mapping[str, int]) -> bool:
    """Accept only a pure frozen-shard-to-slot mapping; it cannot repartition work."""
    if not isinstance(plan, CampaignWorkPlan):
        raise ValueError("executor allocation requires a frozen CampaignWorkPlan")
    expected = {shard.shard_id for shard in plan.shards}
    if set(allocation) != expected:
        raise ValueError("executor allocation must assign exactly the frozen shard IDs")
    if any(type(slot) is not int or slot < 0 for slot in allocation.values()):
        raise ValueError("executor slots must be nonnegative integers")
    return True
