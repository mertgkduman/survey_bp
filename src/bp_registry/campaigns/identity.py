"""Domain-separated identities for topology-independent campaign work.

The hashes in this module bind inputs to a reproducible work identity.  They
are integrity linkage and deliberately do not establish authorship.
"""

from __future__ import annotations

from hashlib import sha256
import re
from typing import Final

from pydantic import Field, model_validator

from ..manifests import StrictModel
from .contracts import canonical_json_bytes


_SHA256: Final = re.compile(r"^[0-9a-f]{64}$")
_MAX_SAMPLE_ARTIFACT_BYTES: Final = 64 * 1024 * 1024


def _digest(domain: str, payload: object) -> str:
    return sha256(domain.encode("ascii") + b"\0" + canonical_json_bytes(payload)).hexdigest()


def _sha256(value: str, *, name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _label(value: str, *, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ValueError(f"{name} must be a nonempty bounded string")
    return value


def _sample_id(value: int) -> int:
    if type(value) is not int or not 0 <= value <= 1_000_000:
        raise ValueError("sample_id must be a bounded nonnegative integer")
    return value


def physical_sample_identity(
    *,
    campaign_spec_digest: str,
    cohort_id: str,
    point_id: str,
    sample_namespace: str,
    sample_id: int,
) -> str:
    """Identify physical randomness without arm or executor inputs."""
    return _digest("bp-registry-campaign-physical-sample-v1", {
        "campaign_spec_digest": _sha256(campaign_spec_digest, name="campaign_spec_digest"),
        "cohort_id": _label(cohort_id, name="cohort_id"),
        "point_id": _label(point_id, name="point_id"),
        "sample_namespace": _label(sample_namespace, name="sample_namespace"),
        "sample_id": _sample_id(sample_id),
    })


def decoder_randomness_identity(
    *, campaign_spec_digest: str, arm_id: str, sample_id: int, decoder_seed_identity: str,
) -> str:
    """Identify decoder-local randomness without execution topology inputs."""
    return _digest("bp-registry-campaign-decoder-randomness-v1", {
        "campaign_spec_digest": _sha256(campaign_spec_digest, name="campaign_spec_digest"),
        "arm_id": _label(arm_id, name="arm_id"),
        "sample_id": _sample_id(sample_id),
        "decoder_seed_identity": _label(decoder_seed_identity, name="decoder_seed_identity"),
    })


def unit_key(
    *, campaign_spec_digest: str, cohort_id: str, point_id: str, sample_id: int, arm_id: str,
) -> str:
    """Identify one atomic arm contribution before the plan digest exists."""
    return _digest("bp-registry-campaign-unit-v1", {
        "campaign_spec_digest": _sha256(campaign_spec_digest, name="campaign_spec_digest"),
        "cohort_id": _label(cohort_id, name="cohort_id"),
        "point_id": _label(point_id, name="point_id"),
        "sample_id": _sample_id(sample_id),
        "arm_id": _label(arm_id, name="arm_id"),
    })


class PersistedSampleReceiptV1(StrictModel):
    """A byte-bound physical sample for backends without reproducible sampling."""

    campaign_spec_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    cohort_id: str = Field(min_length=1, max_length=256)
    point_id: str = Field(min_length=1, max_length=256)
    sample_namespace: str = Field(min_length=1, max_length=256)
    sample_id: int = Field(ge=0, le=1_000_000)
    physical_sample_identity: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_bytes: int = Field(ge=0, le=_MAX_SAMPLE_ARTIFACT_BYTES)

    @model_validator(mode="after")
    def identity_matches_coordinates(self) -> "PersistedSampleReceiptV1":
        expected = physical_sample_identity(
            campaign_spec_digest=self.campaign_spec_digest, cohort_id=self.cohort_id,
            point_id=self.point_id, sample_namespace=self.sample_namespace,
            sample_id=self.sample_id,
        )
        if self.physical_sample_identity != expected:
            raise ValueError("persisted sample identity differs from its arm-neutral coordinates")
        return self


def verify_persisted_sample(receipt: PersistedSampleReceiptV1, artifact: bytes) -> bytes:
    """Validate bytes before any backend is allowed to decode them."""
    if not isinstance(receipt, PersistedSampleReceiptV1):
        raise ValueError("persisted sample receipt must be validated")
    if not isinstance(artifact, bytes):
        raise ValueError("persisted sample artifact must be bytes")
    if len(artifact) != receipt.artifact_bytes:
        raise ValueError("persisted sample byte count differs from receipt")
    if sha256(artifact).hexdigest() != receipt.artifact_sha256:
        raise ValueError("persisted sample digest differs from receipt")
    return artifact
