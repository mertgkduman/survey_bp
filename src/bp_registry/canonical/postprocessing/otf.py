"""Ordered Tanner forest as a bounded, explicit binary-CSS adaptation.

This module records the source identity of arXiv:2409.01440 and BPOTF
``da6caa`` without claiming its circuit/detector procedure.  It accepts only
an immutable original CSS ``H_Z`` problem and uses no hidden simulation truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import numpy as np

from ..budgets import BudgetTree, WorkVector
from ..lineage import LineageEdge, LineageId, stable_lineage_id
from ..problems import OriginalProblem, WorkingProblem
from ..schedules import EdgeTable
from .work import OtfWork


_PAPER_REVISION = "arXiv:2409.01440"
_CODE_REVISION = "BPOTF:da6caa4509dadb8620d8cac38108b4816897b18b"
_SOURCE_BLOCKERS = (
    "faithful_detector_circuit_transfer_deferred_to_phases_12_13",
    "pinned_bpotf_detector_sparsification_unfinished",
    "pinned_bpotf_llr_otf_path_unfinished",
)


@dataclass(frozen=True, slots=True)
class OtfSourceStatus:
    disposition: Literal["non_runnable", "runnable"]
    qualification: Literal["source_faithful", "canonical_css_adaptation"]
    paper_revision: str
    code_revision: str
    blockers: tuple[str, ...]


def source_faithful_status() -> OtfSourceStatus:
    """Keep the source circuit procedure non-runnable in Phase 7."""
    return OtfSourceStatus("non_runnable", "source_faithful", _PAPER_REVISION, _CODE_REVISION, _SOURCE_BLOCKERS)


def canonical_css_adaptation_status() -> OtfSourceStatus:
    """Declare the separately named original-H_Z adaptation."""
    return OtfSourceStatus("runnable", "canonical_css_adaptation", _PAPER_REVISION, _CODE_REVISION, _SOURCE_BLOCKERS)


def posterior_error_probability(posterior_llr: np.ndarray, *, length: int) -> np.ndarray:
    """Convert finite log(P(0)/P(1)) odds into P(error=1), stably."""
    llr = np.asarray(posterior_llr, dtype=np.float64)
    if llr.shape != (length,) or not np.all(np.isfinite(llr)):
        raise ValueError("OTF posterior natural-log odds must be finite and match original columns")
    result = np.empty(length, dtype=np.float64)
    positive = llr >= 0.0
    low = np.exp(-llr[positive])
    high = np.exp(llr[~positive])
    result[positive] = low / (1.0 + low)
    result[~positive] = 1.0 / (1.0 + high)
    result.setflags(write=False)
    return result


class _UnionFind:
    def __init__(self, count: int) -> None:
        self.parent = list(range(count))
        self.rank = [0] * count

    def copy(self) -> "_UnionFind":
        cloned = _UnionFind(len(self.parent))
        cloned.parent, cloned.rank = self.parent.copy(), self.rank.copy()
        return cloned

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> bool:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return False
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1
        return True


@dataclass(frozen=True, slots=True)
class ForestConstruction:
    """Inspectable ordered-pass result, bound to one immutable original H_Z."""

    original: OriginalProblem
    status: Literal["complete", "capped"]
    source_status: OtfSourceStatus
    probabilities: tuple[float, ...]
    ordered_columns: tuple[int, ...]
    accepted_columns: tuple[int, ...]
    cycle_rejected_columns: tuple[int, ...]
    cap_denied_columns: tuple[int, ...]
    working: WorkingProblem
    work: tuple[OtfWork, ...]

    def __post_init__(self) -> None:
        column_count = self.original.hz.shape[1]
        all_columns = self.accepted_columns + self.cycle_rejected_columns + self.cap_denied_columns
        if (self.source_status.qualification != "canonical_css_adaptation"
                or len(self.probabilities) != column_count
                or len(set(self.ordered_columns)) != column_count
                or set(self.ordered_columns) != set(range(column_count))
                or len(set(all_columns)) != len(all_columns)
                or set(all_columns) != set(range(column_count))):
            raise ValueError("OTF construction has an invalid original-column certificate")
        if self.working.original is not self.original or self.working.column_map != self.accepted_columns:
            raise ValueError("OTF working problem must be certified from accepted original columns")
        if self.status == "complete" and self.cap_denied_columns:
            raise ValueError("complete OTF construction cannot contain cap-denied columns")
        if self.status == "capped" and not self.cap_denied_columns:
            raise ValueError("capped OTF construction must retain cap-denied columns")
        if not self.is_acyclic():
            raise ValueError("OTF accepted Tanner graph is cyclic")
        if self.status == "complete" and not self.is_ordered_maximal():
            raise ValueError("OTF accepted Tanner graph is not maximal under its ordered pass")

    @property
    def edge_table(self) -> EdgeTable:
        return EdgeTable.from_check_matrix(self.working.check_matrix)

    def is_acyclic(self) -> bool:
        forest = _UnionFind(self.original.hz.shape[0] + self.original.hz.shape[1])
        offset = self.original.hz.shape[0]
        for column in self.accepted_columns:
            for check in np.flatnonzero(self.original.hz[:, column]):
                if not forest.union(int(check), offset + column):
                    return False
        return True

    def is_ordered_maximal(self) -> bool:
        """Independently replay the completed modified-Kruskal certificate."""
        if self.status != "complete":
            return False
        forest = _UnionFind(self.original.hz.shape[0] + self.original.hz.shape[1])
        offset = self.original.hz.shape[0]
        accepted: list[int] = []
        rejected: list[int] = []
        for column in self.ordered_columns:
            trial = forest.copy()
            edges = tuple(int(check) for check in np.flatnonzero(self.original.hz[:, column]))
            if all(trial.union(check, offset + column) for check in edges):
                forest = trial
                accepted.append(column)
            else:
                rejected.append(column)
        return tuple(accepted) == self.accepted_columns and tuple(rejected) == self.cycle_rejected_columns


@dataclass(frozen=True, slots=True)
class OrderedTannerForestSpec:
    """Closed controls for deterministic original-H_Z ordered Tanner forests."""

    max_accepted_columns: int | None = None
    column_ids: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        if self.max_accepted_columns is not None and (type(self.max_accepted_columns) is not int or self.max_accepted_columns < 0):
            raise ValueError("OTF accepted-column cap must be a nonnegative integer when declared")
        if self.column_ids is not None:
            if (not self.column_ids or any(type(item) is not int or item < 0 for item in self.column_ids)
                    or len(set(self.column_ids)) != len(self.column_ids)):
                raise ValueError("OTF original column IDs must be unique nonnegative integers")

    def build(
        self, original: OriginalProblem, posterior_llr: np.ndarray, *,
        budgets: BudgetTree | None = None, scope: str = "otf",
    ) -> ForestConstruction:
        if not isinstance(original, OriginalProblem):
            raise ValueError("OTF requires an immutable original CSS problem")
        if budgets is not None and not isinstance(budgets, BudgetTree):
            raise ValueError("OTF budgets must be a BudgetTree when supplied")
        if not isinstance(scope, str) or not scope:
            raise ValueError("OTF work scope must be nonempty")
        columns = original.hz.shape[1]
        ids = tuple(range(columns)) if self.column_ids is None else self.column_ids
        if len(ids) != columns:
            raise ValueError("OTF original column IDs must match original H_Z columns")
        degrees = np.sum(original.hz, axis=0)
        if np.any(degrees == 0):
            raise ValueError("OTF rejects disconnected degree-zero original H_Z columns")
        probabilities = posterior_error_probability(posterior_llr, length=columns)
        ordered = tuple(sorted(range(columns), key=lambda column: (-float(probabilities[column]), ids[column])))
        work: list[OtfWork] = []

        def reserve(stage: str, vector: WorkVector, column: int | None = None) -> bool:
            leaf_id = f"{scope}:otf:{original.lineage_id}:{stage}:{'all' if column is None else column}"
            if budgets is not None:
                reservation = budgets.reserve(scope, vector, leaf_id=leaf_id)
                if reservation is None:
                    return False
                reservation.commit_once()
            work.append(OtfWork(stage, vector, column, leaf_id if budgets is not None else None))
            return True

        if not reserve("sort", WorkVector(ranking_scans=columns)):
            return self._construction(original, probabilities, ordered, (), (), ordered, tuple(work))
        forest = _UnionFind(original.hz.shape[0] + columns)
        offset = original.hz.shape[0]
        accepted: list[int] = []
        rejected: list[int] = []
        for position, column in enumerate(ordered):
            if self.max_accepted_columns is not None and len(accepted) >= self.max_accepted_columns:
                return self._construction(original, probabilities, ordered, tuple(accepted), tuple(rejected), ordered[position:], tuple(work))
            incidence = tuple(int(check) for check in np.flatnonzero(original.hz[:, column]))
            if not reserve("union_find_probe", WorkVector(transformations=len(incidence)), column):
                return self._construction(original, probabilities, ordered, tuple(accepted), tuple(rejected), ordered[position:], tuple(work))
            trial = forest.copy()
            if all(trial.union(check, offset + column) for check in incidence):
                if not reserve("accepted_column", WorkVector(fixation_actions=1), column):
                    return self._construction(original, probabilities, ordered, tuple(accepted), tuple(rejected), ordered[position:], tuple(work))
                forest = trial
                accepted.append(column)
            else:
                rejected.append(column)
        return self._construction(original, probabilities, ordered, tuple(accepted), tuple(rejected), (), tuple(work))

    def run(
        self,
        original: OriginalProblem,
        posterior_llr: np.ndarray,
        *,
        rerun: Callable[[WorkingProblem], np.ndarray],
        budgets: BudgetTree,
        scope: str,
    ) -> "OtfResult":
        """Run the declared same BP kernel once on the certified forest.

        The caller owns the kernel binding.  This method owns only OTF graph
        work, forest-space validation, total zero-extension, and immutable
        original-syndrome validation; it cannot invoke another fallback.
        """
        if not callable(rerun) or not isinstance(budgets, BudgetTree) or not isinstance(scope, str) or not scope:
            raise ValueError("OTF run requires a declared same-kernel rerun, BudgetTree, and scope")
        construction = self.build(original, posterior_llr, budgets=budgets, scope=scope)
        work = list(construction.work)

        def reserve(stage: str, vector: WorkVector) -> bool:
            leaf_id = f"{scope}:otf:{original.lineage_id}:{stage}"
            reservation = budgets.reserve(scope, vector, leaf_id=leaf_id)
            if reservation is None:
                return False
            reservation.commit_once()
            work.append(OtfWork(stage, vector, None, leaf_id))
            return True

        if not reserve("forest_bp", WorkVector(bp_calls=1, candidate_checks=1)):
            return _otf_result("capped", construction, None, None, False, work)
        try:
            forest_candidate = _binary_vector(
                rerun(construction.working), construction.working.check_matrix.shape[1], "OTF forest rerun candidate",
            )
        except Exception:
            return _otf_result("invalid_rerun_candidate", construction, None, None, False, work)
        observed_forest = (construction.working.check_matrix.astype(np.int64) @ forest_candidate.astype(np.int64)) % 2
        if not np.array_equal(observed_forest.astype(np.uint8), construction.working.syndrome):
            return _otf_result("forest_syndrome_invalid", construction, tuple(forest_candidate.tolist()), None, False, work)
        if not reserve("lift", WorkVector(lifted_coordinates=original.hz.shape[1])):
            return _otf_result("capped", construction, tuple(forest_candidate.tolist()), None, False, work)
        lifted = np.zeros(original.hz.shape[1], dtype=np.uint8)
        lifted[list(construction.working.column_map)] = forest_candidate
        lifted.setflags(write=False)
        if not reserve("original_check", WorkVector(original_checks=1, candidate_checks=1)):
            return _otf_result("capped", construction, tuple(forest_candidate.tolist()), tuple(lifted.tolist()), False, work)
        original_valid = bool(np.array_equal(
            (original.hz.astype(np.int64) @ lifted.astype(np.int64) % 2).astype(np.uint8), original.syndrome,
        ))
        if not original_valid:
            return _otf_result("original_syndrome_invalid", construction, tuple(forest_candidate.tolist()), tuple(lifted.tolist()), False, work)
        return _otf_result(
            "success_capped" if construction.status == "capped" else "success",
            construction, tuple(forest_candidate.tolist()), tuple(lifted.tolist()), True, work,
        )

    @staticmethod
    def _construction(
        original: OriginalProblem, probabilities: np.ndarray, ordered: tuple[int, ...], accepted: tuple[int, ...],
        rejected: tuple[int, ...], cap_denied: tuple[int, ...], work: tuple[OtfWork, ...],
    ) -> ForestConstruction:
        content = {"original": original.lineage_id, "accepted_columns": accepted, "ordered_columns": ordered}
        transform = stable_lineage_id("transformation", {"operator": "otf_ordered_tanner_forest", **content})
        working_id = stable_lineage_id("working", content)
        lift_id = stable_lineage_id("lift", {"working": working_id.value, "operator": "otf_zero_extend_omitted_columns"})
        working = WorkingProblem(
            working_id.value, original,
            LineageEdge("transform", LineageId("original", original.lineage_id), working_id),
            check_matrix=original.hz[:, accepted], syndrome=original.syndrome,
            column_map=accepted, row_map=tuple(range(original.hz.shape[0])),
            transform_identity=transform.value, lift_identity=lift_id.value,
        )
        return ForestConstruction(
            original, "capped" if cap_denied else "complete", canonical_css_adaptation_status(),
            tuple(float(item) for item in probabilities), ordered, accepted, rejected, cap_denied, working, work,
        )


def _binary_vector(value: np.ndarray, length: int, name: str) -> np.ndarray:
    candidate = np.asarray(value)
    if candidate.shape != (length,) or not np.issubdtype(candidate.dtype, np.integer) or np.any((candidate != 0) & (candidate != 1)):
        raise ValueError(f"{name} must be a binary vector with the forest column length")
    result = np.array(candidate, dtype=np.uint8, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class OtfResult:
    """Complete one-method OTF evidence, including unsuccessful outcomes."""

    status: str
    construction: ForestConstruction
    forest_candidate: tuple[int, ...] | None
    lifted_candidate: tuple[int, ...] | None
    original_valid: bool
    selected_candidate: tuple[int, ...] | None
    work: tuple[OtfWork, ...]
    termination: str | None


def _otf_result(
    status: str, construction: ForestConstruction, forest_candidate: tuple[int, ...] | None,
    lifted_candidate: tuple[int, ...] | None, original_valid: bool, work: list[OtfWork],
) -> OtfResult:
    selected = lifted_candidate if original_valid else None
    capped = status in {"capped", "success_capped"}
    return OtfResult(
        status, construction, forest_candidate, lifted_candidate, original_valid, selected,
        tuple(work), "count_budget_exhausted" if capped else None,
    )


class OtfPostprocessor:
    """One closed OTF binding compatible with the generic one-shot controller."""

    def __init__(self, spec: OrderedTannerForestSpec, *, rerun: Callable[[WorkingProblem], np.ndarray]) -> None:
        if not isinstance(spec, OrderedTannerForestSpec) or not callable(rerun):
            raise ValueError("OTF postprocessor needs a closed spec and declared same-kernel rerun")
        self.spec, self._rerun = spec, rerun

    def run(self, snapshot):
        """Adapt a frozen failed snapshot without a detector or circuit representation."""
        from . import PostprocessingResult

        result = self.spec.run(
            snapshot.working.original, snapshot.posterior_llr, rerun=self._rerun,
            budgets=BudgetTree(limits=(), parents={}), scope=f"otf:{snapshot.attempt_lineage_id}",
        )
        success = result.selected_candidate is not None
        return PostprocessingResult(
            "success" if success else result.status,
            tuple(snapshot.candidate.tolist()), result.selected_candidate, success if success else False,
            snapshot.attempt_lineage_id, 1,
        )
