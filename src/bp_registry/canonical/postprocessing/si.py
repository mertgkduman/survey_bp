"""Source-blocked SI and a separately named deterministic CSS adaptation.

The paper-v3 procedure motivates the reduction.  Its tie, GF(2) solution, and
author-code conventions remain unresolved, so this module never labels the
executable path source faithful.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import numpy as np

from ..budgets import BudgetTree, WorkVector
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

    def reduce(
        self, original: OriginalProblem, posterior_llr: np.ndarray, *, inactivation_count: int | None = None,
    ) -> SiReduction:
        ordered = self.ordered_stabilizers(original, posterior_llr)
        count = self.max_inactivations if inactivation_count is None else inactivation_count
        if type(count) is not int or not 1 <= count <= min(self.max_inactivations, len(ordered)):
            raise ValueError("SI inactivation count is outside the declared adaptation bounds")
        selected = ordered[:count]
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

    def run(
        self,
        original: OriginalProblem,
        posterior_llr: np.ndarray,
        *,
        rerun: Callable[[WorkingProblem], np.ndarray],
        budgets: BudgetTree,
        scope: str,
    ) -> "SiResult":
        """Run only SI-owned reruns, solves, lifts, and original checks.

        ``rerun`` is a declared caller-owned binding of the same canonical BP
        kernel.  This method never retries a different postprocessor.
        """
        if not callable(rerun) or not isinstance(budgets, BudgetTree) or not isinstance(scope, str) or not scope:
            raise ValueError("SI run requires a declared rerun callable and budget scope")
        ordered = self.ordered_stabilizers(original, posterior_llr)
        trials: list[SiTrial] = []
        work: list[SiTrialWork] = []
        valid: list[tuple[int, int, tuple[int, ...]]] = []

        def reserve(trial_index: int, stage: str, vector: WorkVector) -> SiTrialWork | None:
            leaf_id = f"{scope}:si:{original.lineage_id}:trial:{trial_index}:{stage}"
            reservation = budgets.reserve(scope, vector, leaf_id=leaf_id)
            if reservation is None:
                return None
            reservation.commit_once()
            leaf = SiTrialWork(trial_index, stage, vector, leaf_id)
            work.append(leaf)
            return leaf

        for trial_index, count in enumerate(range(1, min(self.max_inactivations, len(ordered)) + 1)):
            trial_lineage = (f"{scope}:si:{original.lineage_id}:trial:{trial_index}",)
            if reserve(trial_index, "ranking", WorkVector(ranking_scans=original.hx.shape[0])) is None:
                trials.append(SiTrial(trial_index, None, None, None, None, False, "capped_ranking", trial_lineage))
                return _si_result("capped", trials, valid, work, budgets, scope)
            selected = ordered[:count]
            removed = tuple(sorted({int(column) for stabilizer in selected for column in np.flatnonzero(original.hx[stabilizer])}))
            reduction_work = WorkVector(fixation_actions=len(removed), transformations=1)
            if reserve(trial_index, "reduction", reduction_work) is None:
                trials.append(SiTrial(trial_index, None, None, None, None, False, "capped_reduction", trial_lineage))
                return _si_result("capped", trials, valid, work, budgets, scope)
            reduction = self.reduce(original, posterior_llr, inactivation_count=count)
            if reserve(trial_index, "rerun", WorkVector(bp_calls=1, candidate_checks=1)) is None:
                trials.append(SiTrial(trial_index, reduction, None, None, None, False, "capped_rerun", trial_lineage))
                return _si_result("capped", trials, valid, work, budgets, scope)
            try:
                reduced_candidate = _binary_vector(rerun(reduction.working), reduction.working.check_matrix.shape[1], "SI rerun candidate")
            except Exception:
                trials.append(SiTrial(trial_index, reduction, None, None, None, False, "invalid_rerun_candidate", trial_lineage))
                continue
            if not np.array_equal(
                (reduction.working.check_matrix.astype(np.int64) @ reduced_candidate.astype(np.int64)) % 2,
                reduction.working.syndrome,
            ):
                trials.append(SiTrial(trial_index, reduction, tuple(reduced_candidate.tolist()), None, None, False, "rerun_syndrome_invalid", trial_lineage))
                continue
            if reserve(trial_index, "solve", WorkVector(candidate_constructions=1)) is None:
                trials.append(SiTrial(trial_index, reduction, tuple(reduced_candidate.tolist()), None, None, False, "capped_solve", trial_lineage))
                return _si_result("capped", trials, valid, work, budgets, scope)
            inactivated = _solve_inactivated_support(reduction, reduced_candidate)
            if inactivated is None:
                trials.append(SiTrial(trial_index, reduction, tuple(reduced_candidate.tolist()), None, None, False, "inactivated_system_unsolved", trial_lineage))
                continue
            if reserve(trial_index, "lift", WorkVector(lifted_coordinates=original.hz.shape[1])) is None:
                trials.append(SiTrial(trial_index, reduction, tuple(reduced_candidate.tolist()), tuple(inactivated.tolist()), None, False, "capped_lift", trial_lineage))
                return _si_result("capped", trials, valid, work, budgets, scope)
            lifted = _recombine(reduction, reduced_candidate, inactivated)
            if reserve(trial_index, "original_check", WorkVector(original_checks=1, candidate_checks=1)) is None:
                trials.append(SiTrial(trial_index, reduction, tuple(reduced_candidate.tolist()), tuple(inactivated.tolist()), tuple(lifted.tolist()), False, "capped_original_check", trial_lineage))
                return _si_result("capped", trials, valid, work, budgets, scope)
            original_valid = bool(np.array_equal((original.hz.astype(np.int64) @ lifted.astype(np.int64)) % 2, original.syndrome))
            trial = SiTrial(
                trial_index, reduction, tuple(reduced_candidate.tolist()), tuple(inactivated.tolist()),
                tuple(lifted.tolist()), original_valid, "original_valid" if original_valid else "original_syndrome_invalid", trial_lineage,
            )
            trials.append(trial)
            if original_valid:
                valid.append((int(np.count_nonzero(lifted)), trial_index, trial.lifted_candidate))
        return _si_result("success" if valid else "unsuccessful", trials, valid, work, budgets, scope)


def _binary_vector(value: np.ndarray, length: int, name: str) -> np.ndarray:
    candidate = np.asarray(value)
    if candidate.shape != (length,) or not np.issubdtype(candidate.dtype, np.integer) or np.any((candidate != 0) & (candidate != 1)):
        raise ValueError(f"{name} must be a binary vector with the reduced column length")
    result = np.array(candidate, dtype=np.uint8, copy=True)
    result.setflags(write=False)
    return result


def _solve_inactivated_support(reduction: SiReduction, reduced_candidate: np.ndarray) -> np.ndarray | None:
    rows = np.asarray(reduction.removed_checks, dtype=int)
    columns = np.asarray(reduction.removed_qubits, dtype=int)
    matrix = reduction.original.hz[np.ix_(rows, columns)].astype(np.uint8, copy=True)
    retained = reduction.original.hz[np.ix_(rows, np.asarray(reduction.working.column_map, dtype=int))]
    rhs = reduction.original.syndrome[rows] ^ ((retained.astype(np.int64) @ reduced_candidate.astype(np.int64)) % 2).astype(np.uint8)
    augmented = np.column_stack((matrix, rhs)).astype(np.uint8, copy=False)
    pivot_row = 0
    pivots: list[int] = []
    for column in range(matrix.shape[1]):
        candidates = np.flatnonzero(augmented[pivot_row:, column])
        if candidates.size == 0:
            continue
        pivot = pivot_row + int(candidates[0])
        augmented[[pivot_row, pivot]] = augmented[[pivot, pivot_row]]
        for row in range(augmented.shape[0]):
            if row != pivot_row and augmented[row, column]:
                augmented[row] ^= augmented[pivot_row]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == augmented.shape[0]:
            break
    if np.any(np.all(augmented[:, :-1] == 0, axis=1) & (augmented[:, -1] == 1)):
        return None
    solution = np.zeros(matrix.shape[1], dtype=np.uint8)
    for row, column in enumerate(pivots):
        solution[column] = augmented[row, -1]
    solution.setflags(write=False)
    return solution


def _recombine(reduction: SiReduction, reduced_candidate: np.ndarray, inactivated: np.ndarray) -> np.ndarray:
    full = np.zeros(reduction.original.hz.shape[1], dtype=np.uint8)
    full[list(reduction.working.column_map)] = reduced_candidate
    full[list(reduction.removed_qubits)] = inactivated
    full.setflags(write=False)
    return full


@dataclass(frozen=True, slots=True)
class SiTrial:
    trial_index: int
    reduction: SiReduction | None
    rerun_candidate: tuple[int, ...] | None
    inactivated_solution: tuple[int, ...] | None
    lifted_candidate: tuple[int, ...] | None
    original_valid: bool
    status: str
    lineage: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SiResult:
    status: str
    trials: tuple[SiTrial, ...]
    selected_candidate: tuple[int, ...] | None
    work: tuple[SiTrialWork, ...]
    termination: str | None
    source_status: SiSourceStatus


def _si_result(
    status: str, trials: list[SiTrial], valid: list[tuple[int, int, tuple[int, ...]]],
    work: list[SiTrialWork], budgets: BudgetTree, scope: str,
) -> SiResult:
    selected = min(valid, default=None)
    final_status = "success_capped" if status == "capped" and selected is not None else status
    return SiResult(final_status, tuple(trials), None if selected is None else selected[2], tuple(work),
                    None if status != "capped" else "count_budget_exhausted", canonical_adaptation_status())


class SiPostprocessor:
    """One optional SI method binding for the generic postprocessing controller."""

    def __init__(self, spec: StabilizerInactivationSpec, *, rerun: Callable[[WorkingProblem], np.ndarray]) -> None:
        if not isinstance(spec, StabilizerInactivationSpec) or not callable(rerun):
            raise ValueError("SI postprocessor needs a closed spec and a declared same-kernel rerun")
        self.spec, self._rerun = spec, rerun

    def run(self, snapshot):
        """Adapt one frozen failed BP snapshot without invoking another fallback."""
        from . import PostprocessingResult

        budgets = BudgetTree(limits=(), parents={})
        result = self.spec.run(
            snapshot.working.original, snapshot.posterior_llr, rerun=self._rerun,
            budgets=budgets, scope=f"si:{snapshot.attempt_lineage_id}",
        )
        success = result.selected_candidate is not None
        return PostprocessingResult(
            "success" if success else result.status,
            tuple(snapshot.candidate.tolist()), result.selected_candidate, success if success else False,
            snapshot.attempt_lineage_id, 1,
        )
