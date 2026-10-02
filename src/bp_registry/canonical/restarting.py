"""Bounded Restart Belief mechanism with explicit B1 distance qualification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Literal, Mapping

import numpy as np

from .budgets import BudgetLimit, BudgetTree, WallClockLimit, WorkVector
from .intervention_session import BpSession
from .lineage import stable_lineage_id
from .numerics import NumericalFailure
from .problems import OriginalProblem
from .schedules import EdgeTable
from .transformations import lift_candidate, transform_fixed_coordinates, transform_syndrome


Preset = Literal["source_exact_distance", "b1_tcap8_mechanism"]


@dataclass(frozen=True, slots=True)
class RestartSpec:
    preset: Preset
    code_id: str
    eta: int
    t_cap: int
    root_sweeps: int
    residual_sweeps: int
    exact_distance: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code_id, str) or not self.code_id:
            raise ValueError("Restart Belief needs a code identity")
        for name in ("eta", "t_cap", "root_sweeps", "residual_sweeps"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 100_000:
                raise ValueError(f"{name} must be a finite positive integer")
        if self.preset == "b1_tcap8_mechanism":
            if (self.code_id != "b1-ghp-882" or self.exact_distance is not None
                    or self.t_cap != 8 or self.eta > 8 or self.residual_sweeps > 10):
                raise ValueError("B1 mechanism requires unknown distance, t_cap=8, eta<=8, and <=10 residual sweeps")
        elif self.preset == "source_exact_distance":
            if self.code_id == "b1-ghp-882" or type(self.exact_distance) is not int or self.exact_distance < 2:
                raise ValueError("source exact-distance preset rejects B1's bounded, unknown distance")
            if self.t_cap != (self.exact_distance - 1) // 2:
                raise ValueError("source t_cap must equal floor((d-1)/2) from exact distance")
        else:
            raise ValueError("unknown Restart Belief preset")

    @property
    def qualification(self) -> str:
        return (
            "pilot_adaptation" if self.preset == "b1_tcap8_mechanism"
            else "source_distance_parameterized_conservative_gate"
        )

    @property
    def root_acceptance_rule(self) -> str:
        if self.preset == "b1_tcap8_mechanism":
            return "proven_lower_bound_t8_weight_gate_without_defect_shortcut"
        return "exact_t_weight_gate_without_defect_shortcut"

    @property
    def source_random_stream(self) -> str:
        return "not_applicable"


@dataclass(frozen=True, slots=True)
class RestartCandidate:
    branch_order: int
    residual_order: int
    candidate: tuple[int, ...]
    original_valid: bool
    original_weight: int
    lineage_id: str


def select_lower_restart_candidate(
    incumbent: RestartCandidate | None, challenger: RestartCandidate | None,
    original: OriginalProblem,
) -> RestartCandidate | None:
    """Only a valid, strictly lighter original-coordinate candidate replaces."""
    if challenger is None or not challenger.original_valid or not _valid(original, challenger.candidate):
        return incumbent
    if challenger.original_weight != sum(challenger.candidate):
        raise ValueError("restart candidate declares a false original weight")
    if incumbent is None:
        return challenger
    if not incumbent.original_valid or not _valid(original, incumbent.candidate):
        raise ValueError("restart incumbent is not originally valid")
    return challenger if challenger.original_weight < incumbent.original_weight else incumbent


@dataclass(frozen=True, slots=True)
class RestartResidual:
    order: int
    inserted_error: tuple[int, ...]
    inserted_indices: tuple[int, ...]
    residual_syndrome: tuple[int, ...]
    working_lineage_id: str | None
    residual_lineage_id: str | None
    session_owner: str | None
    initial_state_digest: str | None
    final_state_digest: str | None
    initial_iteration: int
    raw_candidate: tuple[int, ...] | None
    residual_candidate: tuple[int, ...] | None
    lifted_candidate: tuple[int, ...] | None
    lift_digests: tuple[str, ...]
    original_valid: bool | None
    original_weight: int | None
    termination: str
    insertion_leaf: str | None
    transformation_leaf: str | None
    reset_leaf: str | None
    sweep_leaves: tuple[str, ...]
    validation_leaf: str | None
    next_target: int | None
    reset_fields: tuple[str, ...] = ("channel_prior", "v2c", "c2v", "posterior", "cursor", "cache", "histories")
    preserved_fields: tuple[str, ...] = ("inserted_error",)
    force_zero_operator: str = "exact_shortening_semantic_zero_adaptation"


@dataclass(frozen=True, slots=True)
class RestartBranch:
    order: int
    root_target: int
    lineage_id: str
    open_leaf: str | None
    residuals: tuple[RestartResidual, ...]
    termination: str


@dataclass(frozen=True, slots=True)
class RestartResult:
    preset: Preset
    canonical_identity: str
    qualification: str
    source_revision: str
    source_code_commit: str
    source_random_stream: str
    code_identity_status: str
    b1_distance_status: str
    b1_distance_bounds: tuple[int, int] | None
    root_owner: str
    original_lineage_id: str
    root_initial_digest: str
    root_final_digest: str
    root_candidate: tuple[int, ...]
    root_weight: int
    root_acceptance_threshold: int
    root_acceptance_rule: str
    root_defect_gate_status: str
    root_accepted: bool
    root_posterior: tuple[float, ...]
    root_llr_order: tuple[int, ...]
    root_termination: str
    branches: tuple[RestartBranch, ...]
    selected_candidate: tuple[int, ...] | None
    selected_origin: tuple[int, int] | None
    termination: str
    work: WorkVector
    leaves: tuple[tuple[str, str, WorkVector], ...]
    timing_scopes: tuple[str, ...] = ("setup", "decode", "lift_validation", "serialization", "analysis")


def _bits(value: np.ndarray) -> tuple[int, ...]:
    return tuple(int(bit) for bit in value)


def _valid(original: OriginalProblem, candidate: tuple[int, ...]) -> bool:
    bits = np.asarray(candidate)
    return bool(
        bits.shape == (original.hz.shape[1],)
        and np.issubdtype(bits.dtype, np.integer)
        and np.all((bits == 0) | (bits == 1))
        and np.array_equal((original.hz.astype(np.int64) @ bits.astype(np.int64)) % 2, original.syndrome)
    )


def _reserve_compute(budgets: BudgetTree, leaf_id: str, work: WorkVector, compute):
    reservation = budgets.reserve("attempt", work, leaf_id=leaf_id)
    if reservation is None:
        return False, None
    try:
        result = compute()
    except BaseException:
        reservation.rollback()
        raise
    reservation.commit_once()
    return True, result


def _deadline(wall_clock: WallClockLimit | None) -> bool:
    return wall_clock is not None and wall_clock.check(
        "candidate_selection_boundary", scope="attempt",
    ) is not None


class RestartController:
    """Deterministic root, branch, residual, and strict-lower-weight machine."""

    def __init__(self, spec: RestartSpec | Mapping[str, object]) -> None:
        self.spec = spec if isinstance(spec, RestartSpec) else RestartSpec(**spec)

    def run(
        self, original: OriginalProblem, *, error_rate: float, budgets: BudgetTree,
        wall_clock: WallClockLimit | None = None,
        damping_gamma: float | None = None,
    ) -> RestartResult:
        if not isinstance(original, OriginalProblem):
            raise ValueError("restart requires an immutable original CSS problem")
        n = original.hz.shape[1]
        if n == 0:
            raise ValueError("restart needs at least one original coordinate")
        material = ["restart", original.lineage_id, original.hz.tolist(), original.syndrome.tolist(), error_rate, asdict(self.spec)]
        root_owner = "restart-" + sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()[:20]
        root = BpSession(
            EdgeTable.from_check_matrix(original.hz), original.syndrome,
            error_rate=error_rate, owner_identity=root_owner, damping_gamma=damping_gamma,
        )
        initial = root.state.digest
        root_valid = False
        root_term = "root_sweep_cap"
        for sweep in range(self.spec.root_sweeps):
            try:
                moved = root.advance(budgets=budgets, leaf_id=f"{root_owner}:root:sweep:{sweep}", bp_call_start=sweep == 0, wall_clock=wall_clock)
            except (NumericalFailure, ValueError, FloatingPointError):
                root_term = "numerical_failure"
                break
            if not moved.admitted:
                root_term = moved.termination or "count_budget_exhausted"
                break
            if _deadline(wall_clock):
                root_term = "wall_clock_deadline"
                break
            checked, root_valid = _reserve_compute(
                budgets, f"{root_owner}:root:check:{sweep}", WorkVector(original_checks=1),
                lambda: root.original_syndrome_valid(original.hz),
            )
            if not checked:
                root_term = "count_budget_exhausted"
                break
            if root_valid:
                root_term = "root_valid"
                break
        llr: tuple[float, ...] = ()
        order: tuple[int, ...] = ()
        root_candidate = _bits(root.state.candidate)
        root_weight = sum(root_candidate)
        root_acceptance_threshold = self.spec.t_cap
        root_accepted = root_valid and root_weight <= root_acceptance_threshold
        branches: list[RestartBranch] = []
        incumbent: RestartCandidate | None = None
        termination = root_term if root_term != "root_sweep_cap" else "no_proposal"
        if root_accepted:
            termination = "root_valid"
        elif root_term in {"root_valid", "root_sweep_cap"}:
            if _deadline(wall_clock):
                termination = "wall_clock_deadline"
            else:
                admitted, root_order = _reserve_compute(
                    budgets, f"{root_owner}:root:llr-order", WorkVector(order_generation=1, ranking_scans=n),
                    lambda: self._root_llr_order(root),
                )
                if not admitted:
                    termination = "count_budget_exhausted"
                else:
                    assert root_order is not None
                    llr, order = root_order
                    for branch_order, root_target in enumerate(order[:self.spec.eta]):
                        branch = self._branch(original, root, budgets, branch_order, root_target, wall_clock=wall_clock)
                        branches.append(branch)
                        if branch.termination == "count_budget_exhausted":
                            termination = "count_budget_exhausted"
                            break
                        if branch.termination == "wall_clock_deadline":
                            termination = "wall_clock_deadline"
                            break
                        for row in branch.residuals:
                            if row.original_valid and row.lifted_candidate is not None:
                                candidate = RestartCandidate(
                                    branch_order, row.order, row.lifted_candidate, True,
                                    sum(row.lifted_candidate),
                                    stable_lineage_id("candidate", {
                                        "branch": branch.lineage_id, "residual": row.order,
                                        "bits": row.lifted_candidate,
                                    }).value,
                                )
                                incumbent = select_lower_restart_candidate(incumbent, candidate, original)
                    else:
                        termination = (
                            "restart_valid" if incumbent is not None else
                            "branch_cap_reached" if self.spec.eta < n else "no_proposal"
                        )
        b1_dimensions_match = original.hz.shape == (441, 882) and original.hx.shape == (441, 882)
        qualification = (
            "development_fixture" if self.spec.code_id == "b1-ghp-882" and not b1_dimensions_match
            else self.spec.qualification
        )
        code_status = (
            "dimension_mismatch_fixture" if self.spec.code_id == "b1-ghp-882" and not b1_dimensions_match
            else "dimension_compatible_graph_unverified" if self.spec.code_id == "b1-ghp-882"
            else "declared_code_identity_unverified"
        )
        return RestartResult(
            self.spec.preset,
            "restart_belief_b1_tcap8_mechanism_v1" if self.spec.preset == "b1_tcap8_mechanism" else "restart_belief_exact_distance_v1",
            qualification, "arxiv:2511.13281v1",
            "275535ec981763166c8549d91959dc6e371ec4b1",
            self.spec.source_random_stream, code_status,
            "source_bounded" if self.spec.code_id == "b1-ghp-882" else "exact_declared",
            (18, 24) if self.spec.code_id == "b1-ghp-882" else None,
            root_owner, original.lineage_id, initial, root.state.digest,
            root_candidate, root_weight, root_acceptance_threshold,
            self.spec.root_acceptance_rule,
            "unavailable_without_declared_xi_and_applicable_t", root_accepted,
            llr, order, root_term, tuple(branches),
            root_candidate if root_accepted else None if incumbent is None else incumbent.candidate,
            None if incumbent is None else (incumbent.branch_order, incumbent.residual_order),
            termination, budgets.summary("attempt"), budgets.leaf_events(),
        )

    def _branch(
        self, original: OriginalProblem, root: BpSession, budgets: BudgetTree,
        branch_order: int, root_target: int, *, wall_clock: WallClockLimit | None = None,
    ) -> RestartBranch:
        owner = root.owner_identity
        branch_id = stable_lineage_id("branch", {
            "root": owner, "order": branch_order, "target": root_target,
        }).value
        open_leaf = f"{owner}:branch:{branch_order}:open"
        if _deadline(wall_clock):
            return RestartBranch(branch_order, root_target, branch_id, None, (), "wall_clock_deadline")
        reservation = budgets.reserve("attempt", WorkVector(branch_expansions=1), leaf_id=open_leaf)
        if reservation is None:
            return RestartBranch(branch_order, root_target, branch_id, None, (), "count_budget_exhausted")
        reservation.commit_once()
        inserted: list[int] = []
        next_target: int | None = root_target
        rows: list[RestartResidual] = []
        branch_term = "t_cap_reached"
        for residual_order in range(min(self.spec.t_cap, original.hz.shape[1])):
            if next_target is None:
                branch_term = "no_eligible_target"
                break
            target = next_target
            insertion_leaf = f"{branch_id}:insert:{residual_order}:{target}"
            if _deadline(wall_clock):
                rows.append(self._denied_row(original, inserted, target, residual_order, "wall_clock_deadline"))
                branch_term = "wall_clock_deadline"
                break
            reservation = budgets.reserve(
                "attempt", WorkVector(intervention_actions=1, fixation_actions=1),
                leaf_id=insertion_leaf,
            )
            if reservation is None:
                rows.append(self._denied_row(original, inserted, target, residual_order, "count_budget_exhausted"))
                branch_term = "count_budget_exhausted"
                break
            reservation.commit_once()
            inserted.append(target)
            transform_leaf = f"{branch_id}:residual:{residual_order}:transform"
            if _deadline(wall_clock):
                rows.append(self._denied_row(original, inserted, target, residual_order, "wall_clock_deadline", insertion_leaf))
                branch_term = "wall_clock_deadline"
                break
            admitted, transformed = _reserve_compute(
                budgets, transform_leaf, WorkVector(transformations=2),
                lambda: self._transformed_views(original, inserted),
            )
            if not admitted:
                rows.append(self._denied_row(original, inserted, target, residual_order, "count_budget_exhausted", insertion_leaf))
                branch_term = "count_budget_exhausted"
                break
            assert transformed is not None
            error, residual_syndrome, residual_view, xor_cert, shortened, short_cert = transformed
            reset_leaf = f"{branch_id}:residual:{residual_order}:fresh-reset"
            try:
                session = root.reset_fresh(
                    budgets=budgets, leaf_id=reset_leaf,
                    edge_table=EdgeTable.from_check_matrix(shortened.check_matrix),
                    syndrome=shortened.syndrome, wall_clock=wall_clock,
                )
            except ValueError as error_value:
                if "denied by count budget" not in str(error_value) and "wall-clock deadline" not in str(error_value):
                    raise
                reason = "wall_clock_deadline" if "wall-clock deadline" in str(error_value) else "count_budget_exhausted"
                rows.append(self._denied_row(original, inserted, target, residual_order, reason, insertion_leaf, transform_leaf))
                branch_term = reason
                break
            initial = session.state.digest
            sweep_leaves: list[str] = []
            residual_candidate: tuple[int, ...] | None = None
            lifted_candidate: tuple[int, ...] | None = None
            valid: bool | None = None
            weight: int | None = None
            validation_leaf: str | None = None
            next_target = None
            local_term = "residual_sweep_cap"
            contradiction_leaf = f"{branch_id}:residual:{residual_order}:contradiction-check"
            if _deadline(wall_clock):
                local_term = "wall_clock_deadline"
                checked = False
                contradiction = None
            else:
                checked, contradiction = _reserve_compute(
                    budgets, contradiction_leaf, WorkVector(candidate_checks=1),
                    lambda: bool(np.any(
                        (np.count_nonzero(shortened.check_matrix, axis=1) == 0)
                        & (shortened.syndrome == 1)
                    )),
                )
            if local_term == "wall_clock_deadline":
                pass
            elif not checked:
                local_term = "count_budget_exhausted"
            elif contradiction:
                local_term = "contradictory_empty_check"
            else:
                for sweep in range(self.spec.residual_sweeps):
                    leaf = f"{branch_id}:residual:{residual_order}:sweep:{sweep}"
                    try:
                        moved = session.advance(budgets=budgets, leaf_id=leaf, bp_call_start=sweep == 0, wall_clock=wall_clock)
                    except (NumericalFailure, ValueError, FloatingPointError):
                        local_term = "numerical_failure"
                        break
                    if not moved.admitted:
                        local_term = moved.termination or "count_budget_exhausted"
                        break
                    sweep_leaves.append(leaf)
                    validation_leaf = f"{branch_id}:residual:{residual_order}:lift-check:{sweep}"
                    if _deadline(wall_clock):
                        validation_leaf = None
                        local_term = "wall_clock_deadline"
                        break
                    try:
                        checked, lifts = _reserve_compute(
                            budgets, validation_leaf,
                            WorkVector(original_checks=1, lifted_coordinates=2 * original.hz.shape[1]),
                            lambda: self._lift(shortened, short_cert, residual_view, xor_cert, session.state.candidate),
                        )
                    except ValueError:
                        validation_leaf = None
                        local_term = "invalid_lift"
                        break
                    if not checked:
                        validation_leaf = None
                        local_term = "count_budget_exhausted"
                        break
                    assert lifts is not None
                    residual_lift, original_lift = lifts
                    residual_candidate = _bits(residual_lift.candidate)
                    lifted_candidate = _bits(original_lift.candidate)
                    valid = bool(residual_lift.working_valid and residual_lift.original_valid and original_lift.working_valid and original_lift.original_valid)
                    weight = sum(lifted_candidate)
                    if valid:
                        local_term = "valid_original_candidate"
                        break
                    local_term = original_lift.reason or residual_lift.reason or "original_syndrome_invalid"
            if not valid and local_term not in ("count_budget_exhausted", "wall_clock_deadline", "numerical_failure", "invalid_lift", "contradictory_empty_check"):
                target_leaf = f"{branch_id}:residual:{residual_order}:next-target"
                if _deadline(wall_clock):
                    local_term = "wall_clock_deadline"
                else:
                    target_reservation = budgets.reserve(
                        "attempt", WorkVector(order_selection=1, ranking_scans=original.hz.shape[1]),
                        leaf_id=target_leaf,
                    )
                    if target_reservation is None:
                        local_term = "count_budget_exhausted"
                    else:
                        try:
                            eligible = [index for index in range(original.hz.shape[1]) if index not in inserted]
                            if eligible:
                                # Shortened posterior positions are mapped back to original columns.
                                local_scores = {
                                    original_index: float(session.state.posterior[shortened.column_map.index(original_index)])
                                    for original_index in eligible
                                }
                                next_target = min(eligible, key=lambda index: (local_scores[index], index))
                            else:
                                local_term = "no_eligible_target"
                        except BaseException:
                            target_reservation.rollback()
                            raise
                        target_reservation.commit_once()
            row = RestartResidual(
                residual_order, _bits(error), tuple(inserted), _bits(residual_syndrome),
                shortened.lineage_id, residual_view.lineage_id, session.owner_identity,
                initial, session.state.digest, 0, _bits(session.state.candidate),
                residual_candidate, lifted_candidate, (short_cert.digest, xor_cert.digest),
                valid, weight, local_term, insertion_leaf, transform_leaf, reset_leaf,
                tuple(sweep_leaves), validation_leaf, next_target,
            )
            rows.append(row)
            if local_term in ("count_budget_exhausted", "wall_clock_deadline", "numerical_failure", "invalid_lift", "contradictory_empty_check", "no_eligible_target"):
                branch_term = local_term
                break
            if valid:
                branch_term = "valid_original_candidate"
                break
            if next_target is None:
                branch_term = "no_eligible_target"
                break
        else:
            branch_term = "t_cap_reached"
        return RestartBranch(branch_order, root_target, branch_id, open_leaf, tuple(rows), branch_term)

    @staticmethod
    def _root_llr_order(root: BpSession) -> tuple[tuple[float, ...], tuple[int, ...]]:
        llr = tuple(float(value) for value in root.state.posterior)
        return llr, tuple(sorted(range(len(llr)), key=lambda index: (llr[index], index)))

    @staticmethod
    def _transformed_views(original: OriginalProblem, inserted: list[int]):
        error = np.zeros(original.hz.shape[1], dtype=np.uint8)
        error[inserted] = 1
        residual_syndrome = original.syndrome ^ (
            (original.hz.astype(np.int64) @ error.astype(np.int64)) % 2
        ).astype(np.uint8)
        return error, residual_syndrome, *RestartController._views(original, error, residual_syndrome)

    @staticmethod
    def _views(original: OriginalProblem, error: np.ndarray, residual_syndrome: np.ndarray):
        residual_view, xor_cert = transform_syndrome(original, error)
        if not np.array_equal(residual_view.syndrome, residual_syndrome):
            raise ValueError("inserted error and residual syndrome disagree")
        residual_id = stable_lineage_id("original", {
            "source": original.lineage_id, "inserted": _bits(error),
            "residual_syndrome": _bits(residual_syndrome),
        }).value
        residual_original = OriginalProblem(residual_id, original.hx, original.hz, residual_syndrome)
        fixed = tuple(int(index) for index in np.flatnonzero(error))
        shortened, short_cert = transform_fixed_coordinates(residual_original, fixed, tuple(0 for _ in fixed))
        return residual_view, xor_cert, shortened, short_cert

    @staticmethod
    def _lift(shortened, short_cert, residual_view, xor_cert, candidate):
        residual_lift = lift_candidate(shortened, short_cert, candidate)
        original_lift = lift_candidate(residual_view, xor_cert, residual_lift.candidate)
        return residual_lift, original_lift

    @staticmethod
    def _denied_row(
        original: OriginalProblem, inserted: list[int], target: int, order: int,
        reason: str, insertion_leaf: str | None = None, transformation_leaf: str | None = None,
    ) -> RestartResidual:
        # The terminal is emitted before an algebraic residual transformation
        # was admitted, so do not manufacture error/syndrome evidence after it.
        committed = tuple(inserted)
        return RestartResidual(
            order, (), committed, (), None, None, None,
            None, None, 0, None, None, None, (), None, None, reason,
            insertion_leaf, transformation_leaf, None, (), None, None,
        )


def reconstruct_restart_result(
    spec: RestartSpec | Mapping[str, object], original: OriginalProblem,
    error_rate: float, expected: RestartResult, *, budget_limits: tuple[BudgetLimit, ...] = (),
) -> RestartResult:
    """Independently regenerate root, branches, residual algebra, selection, and leaves."""
    if not isinstance(expected, RestartResult):
        raise ValueError("restart replay requires typed evidence")
    rebuilt = RestartController(spec).run(
        original, error_rate=error_rate, budgets=BudgetTree(limits=budget_limits, parents={}),
    )
    if rebuilt != expected:
        raise ValueError("restart replay disagrees with residual transitions or work")
    return rebuilt
