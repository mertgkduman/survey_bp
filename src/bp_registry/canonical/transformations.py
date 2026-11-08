"""Exact CSS working-problem transforms with total, checked original lifts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json

import numpy as np
from bp_registry.compiled_contracts import immutable_snapshot

from .lineage import LineageEdge, LineageId, stable_lineage_id
from .problems import OriginalProblem, WorkingProblem


def _bits(value: object, *, length: int, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != (length,) or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary vector of length {length}")
    result = immutable_snapshot(array, dtype=np.uint8)
    return result


def _digest(data: dict[str, object]) -> str:
    return sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class FinitePriorBias:
    """A graph-preserving numerical field, not an exact bit constraint."""

    original_lineage_id: str
    target_index: int
    signed_llr: float

    def __post_init__(self) -> None:
        if not self.original_lineage_id or type(self.target_index) is not int or self.target_index < 0 or not np.isfinite(self.signed_llr):
            raise ValueError("finite-prior bias requires a source, target, and finite LLR")


@dataclass(frozen=True, slots=True)
class FixationMap:
    original_lineage_id: str
    fixed_indices: tuple[int, ...]
    fixed_values: tuple[int, ...]
    free_columns: tuple[int, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class LiftMap:
    """A lineage-bound total reconstruction certificate."""

    mode: str
    original_lineage_id: str
    working_lineage_id: str
    fixed_indices: tuple[int, ...]
    fixed_values: tuple[int, ...]
    free_columns: tuple[int, ...]
    test_vector: tuple[int, ...]
    syndrome_delta: tuple[int, ...]
    digest: str

    def content(self) -> dict[str, object]:
        return {
            "mode": self.mode, "original_lineage_id": self.original_lineage_id,
            "working_lineage_id": self.working_lineage_id,
            "fixed_indices": self.fixed_indices, "fixed_values": self.fixed_values,
            "free_columns": self.free_columns, "test_vector": self.test_vector,
            "syndrome_delta": self.syndrome_delta,
        }


@dataclass(frozen=True, slots=True)
class LiftResult:
    candidate: np.ndarray
    working_valid: bool
    original_valid: bool
    reason: str | None
    certificate_digest: str


def make_fixation_map(
    original: OriginalProblem, fixed_indices: tuple[int, ...], fixed_values: tuple[int, ...],
) -> FixationMap:
    """Validate and identify one exact, ordered original-coordinate assignment."""
    if not isinstance(original, OriginalProblem):
        raise ValueError("shortening requires an immutable original problem")
    n = original.hz.shape[1]
    fixed = tuple(fixed_indices)
    values = tuple(fixed_values)
    if (len(fixed) != len(values) or len(set(fixed)) != len(fixed)
            or any(type(index) is not int or not 0 <= index < n for index in fixed)
            or tuple(sorted(fixed)) != fixed
            or any(type(value) is not int or value not in (0, 1) for value in values)):
        raise ValueError("exact fixed coordinates need ordered unique indices and binary values")
    free = tuple(index for index in range(n) if index not in fixed)
    content = {"original": original.lineage_id, "fixed": fixed, "values": values, "free": free}
    return FixationMap(original.lineage_id, fixed, values, free, _digest(content))


def transform_fixed_coordinates(
    original: OriginalProblem, fixed_indices: tuple[int, ...], fixed_values: tuple[int, ...],
) -> tuple[WorkingProblem, LiftMap]:
    """Shorten exact fixed coordinates while retaining every original check row."""
    fixation = make_fixation_map(original, fixed_indices, fixed_values)
    fixed, values, free = fixation.fixed_indices, fixation.fixed_values, fixation.free_columns
    fixed_vector = np.asarray(values, dtype=np.uint8)
    contribution = (original.hz[:, fixed].astype(np.int64) @ fixed_vector.astype(np.int64)) % 2
    residual = np.asarray(original.syndrome ^ contribution.astype(np.uint8), dtype=np.uint8)
    transform_payload = {
        "operator": "exact_fixed_coordinates", "original": original.lineage_id,
        "fixation_digest": fixation.digest, "fixed": fixed, "values": values, "free": free,
    }
    transform_id = stable_lineage_id("transformation", transform_payload)
    working_id = stable_lineage_id("working", {**transform_payload, "residual": residual.tolist()})
    lift_id = stable_lineage_id("lift", {"working": working_id.value, "operator": "restore_fixed"})
    working = WorkingProblem(
        working_id.value, original,
        LineageEdge("transform", LineageId("original", original.lineage_id), working_id),
        check_matrix=original.hz[:, free], syndrome=residual,
        column_map=free, row_map=tuple(range(original.hz.shape[0])),
        transform_identity=transform_id.value, lift_identity=lift_id.value,
    )
    certificate = LiftMap(
        "restore_fixed", original.lineage_id, working.lineage_id,
        fixed, values, free, (), (), "",
    )
    return working, replace(certificate, digest=_digest(certificate.content()))


def transform_syndrome(
    original: OriginalProblem, test_vector: np.ndarray | None = None, *, row_mask: np.ndarray | None = None,
) -> tuple[WorkingProblem, LiftMap]:
    """Build s XOR Ht, recording t itself as the necessary lift certificate."""
    if row_mask is not None or test_vector is None:
        raise ValueError("a row mask cannot certify a syndrome lift; supply an original-coordinate test vector")
    t = _bits(test_vector, length=original.hz.shape[1], name="syndrome test vector")
    delta = np.asarray((original.hz.astype(np.int64) @ t.astype(np.int64)) % 2, dtype=np.uint8)
    working_s = np.asarray(original.syndrome ^ delta, dtype=np.uint8)
    payload = {"operator": "syndrome_xor", "original": original.lineage_id, "t": t.tolist()}
    transform_id = stable_lineage_id("transformation", payload)
    working_id = stable_lineage_id("working", {**payload, "working_syndrome": working_s.tolist()})
    lift_id = stable_lineage_id("lift", {"working": working_id.value, "operator": "xor_test_vector"})
    columns = tuple(range(original.hz.shape[1]))
    working = WorkingProblem(
        working_id.value, original,
        LineageEdge("transform", LineageId("original", original.lineage_id), working_id),
        check_matrix=original.hz, syndrome=working_s,
        column_map=columns, row_map=tuple(range(original.hz.shape[0])),
        transform_identity=transform_id.value, lift_identity=lift_id.value,
    )
    certificate = LiftMap(
        "xor_test_vector", original.lineage_id, working.lineage_id,
        (), (), columns, tuple(int(bit) for bit in t), tuple(int(bit) for bit in delta), "",
    )
    return working, replace(certificate, digest=_digest(certificate.content()))


def lift_candidate(working: WorkingProblem, certificate: LiftMap, candidate: np.ndarray) -> LiftResult:
    """Validate a certificate, lift all coordinates, then check original Hc=s."""
    if not isinstance(working, WorkingProblem) or not isinstance(certificate, LiftMap):
        raise ValueError("lift requires a working problem and typed certificate")
    if (certificate.digest != _digest(certificate.content())
            or certificate.original_lineage_id != working.original.lineage_id
            or certificate.working_lineage_id != working.lineage_id
            or working.lift_identity != stable_lineage_id("lift", {"working": working.lineage_id, "operator": certificate.mode}).value):
        raise ValueError("lift certificate is corrupt or belongs to another working problem")
    y = _bits(candidate, length=working.check_matrix.shape[1], name="working candidate")
    original = working.original
    n = original.hz.shape[1]
    if certificate.mode == "restore_fixed":
        fixed, values, free = certificate.fixed_indices, certificate.fixed_values, certificate.free_columns
        if (len(fixed) != len(values) or set(fixed).intersection(free)
                or tuple(sorted((*fixed, *free))) != tuple(range(n))
                or tuple(free) != working.column_map
                or any(value not in (0, 1) for value in values)):
            raise ValueError("fixed-coordinate lift map is not a total original-coordinate partition")
        expected_h = original.hz[:, free]
        expected_s = original.syndrome ^ ((original.hz[:, fixed].astype(np.int64) @ np.asarray(values, dtype=np.int64)) % 2).astype(np.uint8)
        if not np.array_equal(working.check_matrix, expected_h) or not np.array_equal(working.syndrome, expected_s):
            raise ValueError("fixed-coordinate working view disagrees with its algebraic certificate")
        full = np.zeros(n, dtype=np.uint8)
        full[list(fixed)] = values
        full[list(free)] = y
    elif certificate.mode == "xor_test_vector":
        if certificate.fixed_indices or certificate.fixed_values or certificate.free_columns != tuple(range(n)):
            raise ValueError("syndrome XOR certificate has invalid coordinate maps")
        t = _bits(certificate.test_vector, length=n, name="test vector")
        delta = _bits(certificate.syndrome_delta, length=original.hz.shape[0], name="syndrome delta")
        if (not np.array_equal((original.hz.astype(np.int64) @ t.astype(np.int64)) % 2, delta)
                or not np.array_equal(working.check_matrix, original.hz)
                or not np.array_equal(working.syndrome, original.syndrome ^ delta)):
            raise ValueError("syndrome transform lacks a valid Ht certificate")
        full = np.asarray(y ^ t, dtype=np.uint8)
    else:
        raise ValueError("unknown lift mode")
    working_valid = bool(np.array_equal((working.check_matrix.astype(np.int64) @ y.astype(np.int64)) % 2, working.syndrome))
    original_valid = bool(np.array_equal((original.hz.astype(np.int64) @ full.astype(np.int64)) % 2, original.syndrome))
    full = immutable_snapshot(full)
    reason = None if working_valid and original_valid else (
        "contradictory_empty_check" if working.check_matrix.shape[1] == 0 and not working_valid
        else "working_syndrome_invalid" if not working_valid else "original_syndrome_invalid"
    )
    return LiftResult(full, working_valid, original_valid, reason, certificate.digest)
