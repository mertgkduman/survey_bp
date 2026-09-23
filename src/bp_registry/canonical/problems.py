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

    def __post_init__(self) -> None:
        if self.parent_edge.parent != LineageId("original", self.original.lineage_id):
            raise ValueError("working problem must directly name its original parent")


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
