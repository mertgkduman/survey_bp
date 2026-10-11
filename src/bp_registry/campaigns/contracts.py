"""Strict campaign-specification and acyclic one-unit plan records."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, field_validator

from ..manifests import StrictModel


_SHA256 = r"^[0-9a-f]{64}$"
_MAX_EVENTS = 1_000_000
_MAX_EVIDENCE_BYTES = 64 * 1024 * 1024


def canonical_json_bytes(value: object) -> bytes:
    """Return the sole compact, finite JSON representation used for identities."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _digest(domain: str, payload: bytes) -> str:
    return sha256(domain.encode("ascii") + b"\0" + payload).hexdigest()


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
