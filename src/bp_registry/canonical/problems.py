"""Narrow immutable decoder-visible problem and lifted-candidate values."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .lineage import LineageEdge, LineageId


def _readonly_binary(value: np.ndarray, *, ndim: int, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != ndim or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary integer array with {ndim} dimensions")
    copied = np.array(array, dtype=np.uint8, copy=True)
    copied.setflags(write=False)
    return copied


@dataclass(frozen=True)
class OriginalProblem:
    lineage_id: str
    hx: np.ndarray
    hz: np.ndarray
    syndrome: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "hx", _readonly_binary(self.hx, ndim=2, name="hx"))
        object.__setattr__(self, "hz", _readonly_binary(self.hz, ndim=2, name="hz"))
        object.__setattr__(self, "syndrome", _readonly_binary(self.syndrome, ndim=1, name="syndrome"))
        if self.hx.shape[1] != self.hz.shape[1] or self.syndrome.shape != (self.hz.shape[0],):
            raise ValueError("original problem dimensions disagree")


@dataclass(frozen=True)
class WorkingProblem:
    lineage_id: str
    original: OriginalProblem
    parent_edge: LineageEdge
    check_matrix: np.ndarray | None = None
    syndrome: np.ndarray | None = None
    column_map: tuple[int, ...] | None = None
    row_map: tuple[int, ...] | None = None
    transform_identity: str | None = None
    lift_identity: str | None = None

    def __post_init__(self) -> None:
        identity = self.parent_edge.relation == "identity"
        if (
            self.parent_edge.relation not in {"identity", "transform"}
            or self.parent_edge.parent != LineageId("original", self.original.lineage_id)
            or self.parent_edge.child != LineageId("working", self.lineage_id)
        ):
            raise ValueError("working problem requires an identity edge or certified transform edge from its original")
        rows, columns = self.original.hz.shape
        row_map = tuple(range(rows)) if self.row_map is None else tuple(self.row_map)
        column_map = tuple(range(columns)) if self.column_map is None else tuple(self.column_map)
        if (len(set(row_map)) != len(row_map) or len(set(column_map)) != len(column_map)
                or any(type(index) is not int or not 0 <= index < rows for index in row_map)
                or any(type(index) is not int or not 0 <= index < columns for index in column_map)):
            raise ValueError("working problem maps must be unique bounded original indices")
        h = _readonly_binary(
            self.original.hz if self.check_matrix is None else self.check_matrix,
            ndim=2, name="working check_matrix",
        )
        s = _readonly_binary(
            self.original.syndrome if self.syndrome is None else self.syndrome,
            ndim=1, name="working syndrome",
        )
        if h.shape != (len(row_map), len(column_map)) or s.shape != (len(row_map),):
            raise ValueError("working matrix/syndrome shapes disagree with ordered maps")
        if identity:
            if (row_map != tuple(range(rows)) or column_map != tuple(range(columns))
                    or not np.array_equal(h, self.original.hz) or not np.array_equal(s, self.original.syndrome)
                    or self.transform_identity not in {None, "identity"}
                    or self.lift_identity not in {None, "identity"}):
                raise ValueError("identity working problem cannot change graph, syndrome, maps, or lift")
        elif not self.transform_identity or not self.lift_identity:
            raise ValueError("working problem requires an identity edge unless transform and lift identities are explicit")
        object.__setattr__(self, "check_matrix", h)
        object.__setattr__(self, "syndrome", s)
        object.__setattr__(self, "row_map", row_map)
        object.__setattr__(self, "column_map", column_map)
        object.__setattr__(self, "transform_identity", self.transform_identity or "identity")
        object.__setattr__(self, "lift_identity", self.lift_identity or "identity")


@dataclass(frozen=True)
class OriginalSpaceCandidate:
    lineage_id: str
    working: WorkingProblem
    candidate: np.ndarray
    local_order: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate", _readonly_binary(self.candidate, ndim=1, name="candidate"))
        if self.candidate.shape != (self.working.original.hz.shape[1],) or self.local_order < 0:
            raise ValueError("candidate length or local order is invalid")


def select_stable_candidate(candidates: list[OriginalSpaceCandidate] | tuple[OriginalSpaceCandidate, ...]) -> OriginalSpaceCandidate | None:
    """Select by declared stable lineage/local order, never completion arrival."""
    return min(candidates, key=lambda candidate: (candidate.local_order, candidate.lineage_id), default=None)
