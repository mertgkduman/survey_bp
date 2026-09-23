"""Public identity and structural reuse checks for canonical CSS evidence.

The ledger's content hashes make records durable, but they do not establish that
the record belongs to the currently preflighted public experiment.  This module
keeps that identity separate from hidden truth and gives both the runner and
CLI one reuse boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


class CanonicalStructuralVerificationError(ValueError):
    """Persisted canonical evidence is well-formed but not reusable."""


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def public_execution_identity(
    *, manifest_sha256: str, artifact_raw_sha256: str, artifact_semantic_sha256: str,
    compact_manifest: Mapping[str, Any], sample_seed_identity: str, run_id: str,
    shot_id: int, check_type: str, syndrome: Sequence[int],
) -> str:
    """Hash every public input that can change a structural shot or its lineage."""
    if type(shot_id) is not int or shot_id < 0:
        raise ValueError("public execution identity requires a nonnegative shot ID")
    payload = {
        "domain": "bp-registry-public-execution-v1",
        "manifest_sha256": manifest_sha256,
        "artifact_raw_sha256": artifact_raw_sha256,
        "artifact_semantic_sha256": artifact_semantic_sha256,
        "compact_manifest": dict(compact_manifest),
        "sample_seed_identity": sample_seed_identity,
        "run_id": run_id,
        "shot_id": shot_id,
        "check_type": check_type,
        "syndrome": list(syndrome),
    }
    return "sha256:" + sha256(_canonical_json(payload)).hexdigest()


@dataclass(frozen=True, slots=True)
class PublicShotContext:
    """Immutable preflighted context used to validate one public run/shot."""

    manifest_sha256: str
    artifact_raw_sha256: str
    artifact_semantic_sha256: str
    compact_manifest: Mapping[str, Any]
    sample_seed_identity: str
    run_id: str
    shot_id: int
    check_type: str
    syndrome: tuple[int, ...]

    @property
    def execution_identity(self) -> str:
        return public_execution_identity(
            manifest_sha256=self.manifest_sha256,
            artifact_raw_sha256=self.artifact_raw_sha256,
            artifact_semantic_sha256=self.artifact_semantic_sha256,
            compact_manifest=self.compact_manifest,
            sample_seed_identity=self.sample_seed_identity,
            run_id=self.run_id,
            shot_id=self.shot_id,
            check_type=self.check_type,
            syndrome=self.syndrome,
        )


def validate_canonical_shot(events: Sequence[Mapping[str, Any]], context: PublicShotContext) -> Mapping[str, Any]:
    """Reject a stale, duplicate, or identity-mismatched persisted shot.

    Task 2 extends this entry point into complete semantic reconstruction.  The
    early check here is deliberately strict enough to make terminal reuse safe
    before the executor ever returns a previous result.
    """
    stream = [
        event for event in events
        if event.get("run_id") == context.run_id and event.get("shot_id") == context.shot_id
    ]
    if not stream:
        raise CanonicalStructuralVerificationError("canonical shot has no structural evidence")
    if stream[0].get("kind") != "shot_begin":
        raise CanonicalStructuralVerificationError("canonical shot must start with shot_begin")
    terminals = [event for event in stream if event.get("kind") == "termination"]
    if len(terminals) != 1 or stream[-1] is not terminals[0]:
        raise CanonicalStructuralVerificationError("canonical shot must have exactly one final termination")
    if stream[0].get("sample_seed_identity") != context.sample_seed_identity:
        raise CanonicalStructuralVerificationError("canonical shot sample identity differs from preflight")
    expected = {
        "manifest_sha256": context.manifest_sha256,
        "artifact_raw_sha256": context.artifact_raw_sha256,
        "artifact_semantic_sha256": context.artifact_semantic_sha256,
        "canonical_identity": context.execution_identity,
    }
    for event in stream:
        data = event.get("data")
        if not isinstance(data, Mapping):
            raise CanonicalStructuralVerificationError("canonical structural event lacks typed data")
        for field, value in expected.items():
            if data.get(field) != value:
                raise CanonicalStructuralVerificationError(
                    f"canonical {field} differs from current public execution identity"
                )
    return terminals[0]
