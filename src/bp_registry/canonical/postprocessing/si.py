"""Source-blocked SI and a separately named deterministic CSS adaptation.

The paper-v3 procedure motivates the reduction.  Its tie, GF(2) solution, and
author-code conventions remain unresolved, so this module never labels the
executable path source faithful.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from ..budgets import WorkVector
from ..lineage import LineageEdge, LineageId, stable_lineage_id
from ..problems import OriginalProblem, WorkingProblem
from .work import SiTrialWork


_SOURCE_BLOCKERS = (
    "equal_reliability_tie_rule_unknown",
    "gf2_solution_selection_unknown",
    "author_code_identity_unknown",
)


@dataclass(frozen=True, slots=True)
class SiSourceStatus:
    """Pinned source qualification kept separate from executable controls."""

    disposition: Literal["non_runnable", "runnable"]
    qualification: Literal["source_faithful", "canonical_adaptation"]
    blockers: tuple[str, ...]
    adaptation_controls: tuple[str, ...] = ()
    paper_revision: str = "arXiv:2205.06125v3"


def source_faithful_status() -> SiSourceStatus:
    """The source-faithful SI route cannot execute until all source gaps close."""
    return SiSourceStatus("non_runnable", "source_faithful", _SOURCE_BLOCKERS)


def canonical_adaptation_status() -> SiSourceStatus:
    """Declare the controls that make the CSS adaptation reproducible."""
    return SiSourceStatus(
        "runnable", "canonical_adaptation", _SOURCE_BLOCKERS,
        ("ascending_stabilizer_id_ties", "zero_free_variables_gf2"),
    )


def _gf2_rank(matrix: np.ndarray) -> int:
    value = np.array(matrix, dtype=np.uint8, copy=True)
    rank = 0
    for column in range(value.shape[1]):
        pivots = np.flatnonzero(value[rank:, column])
        if pivots.size == 0:
            continue
        pivot = rank + int(pivots[0])
        value[[rank, pivot]] = value[[pivot, rank]]
        for row in range(value.shape[0]):
            if row != rank and value[row, column]:
                value[row] ^= value[rank]
        rank += 1
        if rank == value.shape[0]:
            break
    return rank


def _finite_reliability(value: np.ndarray, *, length: int) -> np.ndarray:
    reliability = np.asarray(value, dtype=np.float64)
    if reliability.shape != (length,) or not np.all(np.isfinite(reliability)):
        raise ValueError("SI reliability must be finite and match the original variable count")
    copied = np.array(reliability, copy=True)
    copied.setflags(write=False)
    return copied


@dataclass(frozen=True, slots=True)
class SiReduction:
    """One certified removal of opposite-check support and incident checks."""

    original: OriginalProblem
    working: WorkingProblem
    source_status: SiSourceStatus
    stabilizer_order: tuple[int, ...]
    removed_qubits: tuple[int, ...]
    removed_checks: tuple[int, ...]
    trial_work: tuple[SiTrialWork, ...]

    def __post_init__(self) -> None:
        if self.source_status.qualification != "canonical_adaptation":
            raise ValueError("only the declared canonical adaptation can create an SI reduction")
        if not self.stabilizer_order or len(set(self.stabilizer_order)) != len(self.stabilizer_order):
            raise ValueError("SI reduction requires unique ordered stabilizer IDs")
        if not self.removed_qubits or tuple(sorted(set(self.removed_qubits))) != self.removed_qubits:
            raise ValueError("SI reduction requires increasing unique removed qubits")
        if tuple(sorted(set(self.removed_checks))) != self.removed_checks:
            raise ValueError("SI reduction requires increasing unique removed checks")
        self._validate_certificate()

    def _validate_certificate(self) -> None:
        hz, hx = self.original.hz, self.original.hx
        selected_support = tuple(sorted({
            int(column) for stabilizer in self.stabilizer_order
            for column in np.flatnonzero(hx[stabilizer])
        }))
        if selected_support != self.removed_qubits:
            raise ValueError("SI removal certificate disagrees with selected stabilizer support")
        incident = tuple(int(row) for row in np.flatnonzero(np.any(hz[:, self.removed_qubits], axis=1)))
        if incident != self.removed_checks:
            raise ValueError("SI removal certificate disagrees with incident original checks")
        retained_rows = tuple(row for row in range(hz.shape[0]) if row not in set(self.removed_checks))
        retained_columns = tuple(column for column in range(hz.shape[1]) if column not in set(self.removed_qubits))
        if (self.working.row_map != retained_rows or self.working.column_map != retained_columns
                or not np.array_equal(self.working.check_matrix, hz[np.ix_(retained_rows, retained_columns)])
                or not np.array_equal(self.working.syndrome, self.original.syndrome[list(retained_rows)])):
            raise ValueError("SI working problem is not the certified reduced original problem")


@dataclass(frozen=True, slots=True)
class StabilizerInactivationSpec:
    """Closed canonical controls for a CSS SI adaptation, not a paper replica."""

    max_inactivations: int

    def __post_init__(self) -> None:
        if type(self.max_inactivations) is not int or self.max_inactivations < 1:
            raise ValueError("max_inactivations must be a positive integer")

    def ordered_stabilizers(self, original: OriginalProblem, posterior_llr: np.ndarray) -> tuple[int, ...]:
        if not isinstance(original, OriginalProblem):
            raise ValueError("SI requires an immutable original CSS problem")
        reliability = _finite_reliability(posterior_llr, length=original.hz.shape[1])
        if original.hx.shape[0] == 0:
            raise ValueError("SI requires at least one opposite check")
        commutator = (original.hx.astype(np.int64) @ original.hz.astype(np.int64).T) % 2
        if np.any(commutator):
            raise ValueError("SI requires CSS Hx and Hz checks to commute")
        if _gf2_rank(original.hx) != original.hx.shape[0]:
            raise ValueError("SI rejects dependent opposite-check rows before rerun")
        supports = tuple(tuple(int(column) for column in np.flatnonzero(row)) for row in original.hx)
        if any(not support for support in supports):
            raise ValueError("SI rejects an opposite check with empty support")
        scores = tuple(float(np.sum(np.abs(reliability[list(support)]))) for support in supports)
        return tuple(sorted(range(original.hx.shape[0]), key=lambda item: (scores[item], item)))

    def reduce(self, original: OriginalProblem, posterior_llr: np.ndarray) -> SiReduction:
        ordered = self.ordered_stabilizers(original, posterior_llr)
        selected = ordered[:self.max_inactivations]
        removed_qubits = tuple(sorted({
            int(column) for stabilizer in selected for column in np.flatnonzero(original.hx[stabilizer])
        }))
        removed_checks = tuple(int(row) for row in np.flatnonzero(np.any(original.hz[:, removed_qubits], axis=1)))
        retained_rows = tuple(row for row in range(original.hz.shape[0]) if row not in set(removed_checks))
        retained_columns = tuple(column for column in range(original.hz.shape[1]) if column not in set(removed_qubits))
        content = {
            "original": original.lineage_id, "stabilizers": selected,
            "removed_qubits": removed_qubits, "removed_checks": removed_checks,
        }
        transform = stable_lineage_id("transformation", {"operator": "si_remove_support_and_incident_checks", **content})
        working_id = stable_lineage_id("working", {**content, "syndrome": original.syndrome[list(retained_rows)].tolist()})
        lift_id = stable_lineage_id("lift", {"working": working_id.value, "operator": "si_solve_and_restore"})
        working = WorkingProblem(
            working_id.value, original,
            LineageEdge("transform", LineageId("original", original.lineage_id), working_id),
            check_matrix=original.hz[np.ix_(retained_rows, retained_columns)],
            syndrome=original.syndrome[list(retained_rows)],
            column_map=retained_columns, row_map=retained_rows,
            transform_identity=transform.value, lift_identity=lift_id.value,
        )
        work = (
            SiTrialWork(0, "ranking", WorkVector(ranking_scans=original.hx.shape[0])),
            SiTrialWork(0, "reduction", WorkVector(fixation_actions=len(removed_qubits), transformations=1)),
        )
        return SiReduction(original, working, canonical_adaptation_status(), selected, removed_qubits, removed_checks, work)
