"""Fail-closed admission for the external clustered-RL-S source artifact.

This module deliberately does not implement a cluster traversal, inference rule,
training procedure, or substitute partition.  It only decides whether exact,
bounded author-supplied bytes meet a declared compatibility contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Literal, Mapping

import numpy as np


MAX_CLUSTER_ARTIFACT_BYTES = 1_000_000
MAX_CLUSTER_Q_CELLS = 100_000
MAX_CLUSTER_CHECKS = 10_000
MAX_NPY_HEADER_BYTES = 4_096
_SHA256_HEX = frozenset("0123456789abcdef")


def _require_digest(value: str, name: str) -> str:
    if type(value) is not str or len(value) != 64 or any(char not in _SHA256_HEX for char in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hexadecimal digest")
    return value


def _require_text(value: str, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _as_exact_pair(value: tuple[int, int] | list[int], name: str) -> tuple[int, int]:
    if not isinstance(value, (tuple, list)) or len(value) != 2 or any(type(item) is not int or item <= 0 for item in value):
        raise ValueError(f"{name} must be two positive integer dimensions")
    if math.prod(value) > MAX_CLUSTER_Q_CELLS:
        raise ValueError(f"{name} exceeds the bounded Q-table cell limit")
    return (value[0], value[1])


@dataclass(frozen=True)
class ClusterArtifactSpec:
    """Pinned identity and exact compatibility facts for one author artifact pair."""

    approved_root: str | Path
    q_table_path: str
    partition_path: str
    q_table_sha256: str
    partition_sha256: str
    source_id: str
    source_uri: str
    source_revision: str
    source_record_sha256: str
    graph_sha256: str
    channel: str
    kernel: str
    state_encoding: str
    action_encoding: str
    tie_breaking: str
    q_shape: tuple[int, int] | list[int]
    check_count: int
    max_bytes: int = MAX_CLUSTER_ARTIFACT_BYTES

    def __post_init__(self) -> None:
        for name in (
            "q_table_sha256", "partition_sha256", "source_record_sha256", "graph_sha256",
        ):
            _require_digest(getattr(self, name), name)
        for name in (
            "q_table_path", "partition_path", "source_id", "source_uri", "source_revision",
            "channel", "kernel", "state_encoding", "action_encoding", "tie_breaking",
        ):
            _require_text(getattr(self, name), name)
        if type(self.check_count) is not int or not 1 <= self.check_count <= MAX_CLUSTER_CHECKS:
            raise ValueError("check_count must be a bounded positive integer")
        if type(self.max_bytes) is not int or not 1 <= self.max_bytes <= MAX_CLUSTER_ARTIFACT_BYTES:
            raise ValueError("max_bytes must be a positive bounded integer")
        object.__setattr__(self, "q_shape", _as_exact_pair(self.q_shape, "q_shape"))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ClusterArtifactSpec":
        if not isinstance(value, Mapping):
            raise ValueError("cluster artifact specification must be a JSON object")
        allowed = {
            "approved_root", "q_table_path", "partition_path", "q_table_sha256",
            "partition_sha256", "source_id", "source_uri", "source_revision",
            "source_record_sha256", "graph_sha256", "channel", "kernel",
            "state_encoding", "action_encoding", "tie_breaking", "q_shape", "check_count",
            "max_bytes",
        }
        if set(value) - allowed:
            raise ValueError("cluster artifact specification has unknown fields")
        required = allowed - {"max_bytes"}
        if set(value) - {"max_bytes"} != required:
            raise ValueError("cluster artifact specification must contain every required field")
        return cls(**dict(value))

    def public_identity(self) -> dict[str, Any]:
        return {
            "source": {
                "id": self.source_id,
                "uri": self.source_uri,
                "revision": self.source_revision,
                "record_sha256": self.source_record_sha256,
            },
            "compatibility": {
                "graph_sha256": self.graph_sha256,
                "channel": self.channel,
                "kernel": self.kernel,
                "state_encoding": self.state_encoding,
                "action_encoding": self.action_encoding,
                "tie_breaking": self.tie_breaking,
                "q_shape": list(self.q_shape),
                "check_count": self.check_count,
            },
            "expected_hashes": {
                "q_table_sha256": self.q_table_sha256,
                "partition_sha256": self.partition_sha256,
            },
        }


@dataclass(frozen=True)
class ClusterArtifactQualification:
    """Structured admission result; qualification never asserts source support."""

    status: Literal["qualified", "unavailable", "incompatible"]
    reason: str
    identity: dict[str, Any]
    checks: dict[str, bool]
    q_table: np.ndarray | None = field(default=None, repr=False, compare=False)
    partition: tuple[tuple[int, ...], ...] | None = None

    @property
    def qualified(self) -> bool:
        return self.status == "qualified"

    def report(self) -> dict[str, Any]:
        """Stable machine-readable report for an external acquisition checkpoint."""
        return {
            "schema_version": 1,
            "kind": "cluster_artifact_qualification",
            "status": self.status,
            "qualified": self.qualified,
            "reason": self.reason,
            "identity": self.identity,
            "checks": dict(sorted(self.checks.items())),
            "source_support": "not_established_by_qualification",
            "reproduction_status": "not_established_by_qualification",
            "sch_06_status": "blocked_pending_authoritative_artifact_and_algorithm_execution",
            "external_training_cost": "unknown",
        }


def _confined_file(root: str | Path, relative_path: str, *, suffix: str) -> Path:
    approved_root = Path(root).resolve(strict=True)
    if not approved_root.is_dir():
        raise ValueError("approved cluster artifact root must be a directory")
    requested = Path(relative_path)
    if requested.is_absolute() or ".." in requested.parts or requested.suffix != suffix:
        raise ValueError("cluster artifact path escapes approved root or uses an unsupported format")
    candidate = approved_root / requested
    cursor = approved_root
    for part in requested.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("cluster artifact path may not traverse a symlink")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(candidate) from exc
    if not resolved.is_relative_to(approved_root) or not resolved.is_file():
        raise ValueError("cluster artifact path must identify a confined regular file")
    return resolved


def _checked_bytes(path: Path, expected: str, max_bytes: int, label: str) -> bytes:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"{label} exceeds size limit")
    raw = path.read_bytes()
    if len(raw) > max_bytes:
        raise ValueError(f"{label} exceeds size limit")
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"{label} SHA-256 does not match pinned bytes")
    return raw


def _read_npy_header(path: Path) -> tuple[tuple[int, ...], bool, np.dtype[Any], int]:
    with path.open("rb") as handle:
        major, minor = np.lib.format.read_magic(handle)
        if (major, minor) == (1, 0):
            shape, fortran_order, dtype = np.lib.format.read_array_header_1_0(
                handle, max_header_size=MAX_NPY_HEADER_BYTES
            )
        elif (major, minor) == (2, 0):
            shape, fortran_order, dtype = np.lib.format.read_array_header_2_0(
                handle, max_header_size=MAX_NPY_HEADER_BYTES
            )
        else:
            raise ValueError("Q-table must use NumPy .npy format version 1.0 or 2.0")
        return shape, fortran_order, dtype, handle.tell()


def _load_q_table(path: Path, spec: ClusterArtifactSpec) -> np.ndarray:
    shape, fortran_order, dtype, payload_offset = _read_npy_header(path)
    if tuple(shape) != spec.q_shape or fortran_order:
        raise ValueError("Q-table shape or memory order is incompatible with the pinned artifact")
    if dtype != np.dtype(np.float64) or dtype.hasobject:
        raise ValueError("Q-table must use primitive little-endian float64 values")
    cells = math.prod(shape)
    if cells > MAX_CLUSTER_Q_CELLS or cells * dtype.itemsize + payload_offset != path.stat().st_size:
        raise ValueError("Q-table payload dimensions are unsafe or malformed")
    table = np.load(path, allow_pickle=False, mmap_mode="r", max_header_size=MAX_NPY_HEADER_BYTES)
    if not isinstance(table, np.ndarray) or table.dtype != np.dtype(np.float64) or table.shape != spec.q_shape:
        raise ValueError("Q-table changed after header qualification")
    if not np.isfinite(table).all():
        raise ValueError("Q-table contains NaN or infinity")
    return np.asarray(table)


def _json_object(raw: bytes) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("partition JSON has duplicate keys")
            result[key] = value
        return result

    try:
        decoded = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("partition artifact must be valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise ValueError("partition artifact must be a JSON object")
    return decoded


def _load_partition(raw: bytes, spec: ClusterArtifactSpec) -> tuple[tuple[int, ...], ...]:
    decoded = _json_object(raw)
    required = {"format_version", "source", "compatibility", "partition"}
    if set(decoded) != required or decoded["format_version"] != 1:
        raise ValueError("partition artifact has an invalid strict schema")
    source = decoded["source"]
    compatibility = decoded["compatibility"]
    if not isinstance(source, dict) or not isinstance(compatibility, dict):
        raise ValueError("partition artifact source and compatibility facts must be objects")
    expected_source = {
        "id": spec.source_id, "uri": spec.source_uri, "revision": spec.source_revision,
        "record_sha256": spec.source_record_sha256,
    }
    expected_compatibility = {
        "graph_sha256": spec.graph_sha256, "channel": spec.channel, "kernel": spec.kernel,
        "state_encoding": spec.state_encoding, "action_encoding": spec.action_encoding,
        "tie_breaking": spec.tie_breaking, "q_table_sha256": spec.q_table_sha256,
        "q_shape": list(spec.q_shape), "check_count": spec.check_count,
    }
    if source != expected_source or compatibility != expected_compatibility:
        raise ValueError("partition artifact metadata is incompatible with the pinned specification")
    partitions = decoded["partition"]
    if not isinstance(partitions, list) or not partitions or len(partitions) > spec.check_count:
        raise ValueError("partition must contain a bounded ordered list of nonempty clusters")
    ordered: list[tuple[int, ...]] = []
    seen: set[int] = set()
    for cluster in partitions:
        if not isinstance(cluster, list) or not cluster:
            raise ValueError("partition clusters must be nonempty arrays")
        if any(type(check) is not int or not 0 <= check < spec.check_count for check in cluster):
            raise ValueError("partition contains an invalid check index")
        if len(set(cluster)) != len(cluster) or any(check in seen for check in cluster):
            raise ValueError("partition must cover each check exactly once")
        seen.update(cluster)
        ordered.append(tuple(cluster))
    if seen != set(range(spec.check_count)):
        raise ValueError("partition must cover every declared check exactly once")
    return tuple(ordered)


def _identity_with_actual_hashes(spec: ClusterArtifactSpec) -> dict[str, Any]:
    return spec.public_identity()


def _failure(spec: ClusterArtifactSpec, status: Literal["unavailable", "incompatible"], reason: str) -> ClusterArtifactQualification:
    checks = {
        "confined_non_executable_formats": False,
        "pinned_raw_hashes": False,
        "primitive_bounded_finite_q_table": False,
        "exact_partition_and_compatibility": False,
    }
    return ClusterArtifactQualification(status=status, reason=reason, identity=_identity_with_actual_hashes(spec), checks=checks)


def load_cluster_artifact(spec: ClusterArtifactSpec) -> ClusterArtifactQualification:
    """Qualify exact source bytes without making them executable decoder behavior."""
    if not isinstance(spec, ClusterArtifactSpec):
        raise TypeError("load_cluster_artifact requires a ClusterArtifactSpec")
    try:
        q_table_path = _confined_file(spec.approved_root, spec.q_table_path, suffix=".npy")
        partition_path = _confined_file(spec.approved_root, spec.partition_path, suffix=".json")
    except FileNotFoundError:
        return _failure(spec, "unavailable", "required author Q-table or ordered partition bytes are unavailable")
    except ValueError as exc:
        return _failure(spec, "incompatible", str(exc))
    try:
        _checked_bytes(q_table_path, spec.q_table_sha256, spec.max_bytes, "Q-table")
        partition_raw = _checked_bytes(partition_path, spec.partition_sha256, spec.max_bytes, "partition")
        q_table = _load_q_table(q_table_path, spec)
        partition = _load_partition(partition_raw, spec)
    except (OSError, ValueError) as exc:
        return _failure(spec, "incompatible", str(exc))
    return ClusterArtifactQualification(
        status="qualified",
        reason="exact bounded non-executable bytes satisfy the declared compatibility contract",
        identity=_identity_with_actual_hashes(spec),
        checks={
            "confined_non_executable_formats": True,
            "pinned_raw_hashes": True,
            "primitive_bounded_finite_q_table": True,
            "exact_partition_and_compatibility": True,
        },
        q_table=q_table,
        partition=partition,
    )
