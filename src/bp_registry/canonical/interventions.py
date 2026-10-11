"""Source-linked CSS freezing, syndrome-flip, and sign-only controllers.

The source families are distinct.  Freezing originates in quaternary BP,
BP-SF changes a working syndrome with an XOR lift, and BSFBP flips a posterior
inside normalized min-sum.  All three implementations here are qualified CSS
adaptations and make no author-code equivalence claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from threading import RLock
from typing import Mapping, Sequence

import numpy as np

from .budgets import BudgetLimit, BudgetTree, WallClockLimit, WorkVector
from .intervention_session import BpSession, after_phase5_work, before_phase5_work, decoder_stream_identity
from .kernel import BinarySpaKernel
from .numerics import MIN_SUM_CPU_F64, NumericalFailure
from .problems import OriginalProblem
from .schedules import EdgeTable
from .transformations import lift_candidate, transform_fixed_coordinates, transform_syndrome
from .updates import NormalizedMinSumUpdate, ParameterAssignment


def _positive(value: int, name: str) -> None:
    if type(value) is not int or not 1 <= value <= 100_000:
        raise ValueError(f"{name} must be a finite positive integer")


def _owner(prefix: str, original: OriginalProblem, seed: str, rate: float) -> str:
    if not isinstance(seed, str) or not seed:
        raise ValueError("decoder root seed must be a nonempty string")
    material = [prefix, original.lineage_id, original.hz.tolist(), original.syndrome.tolist(), seed, rate]
    return prefix + "-" + sha256(json.dumps(material, separators=(",", ":"), allow_nan=False).encode()).hexdigest()[:20]


def _bits(array: np.ndarray) -> tuple[int, ...]:
    return tuple(int(bit) for bit in array)


def _original_valid(original: OriginalProblem, candidate: Sequence[int]) -> bool:
    bits = np.asarray(candidate)
    if bits.shape != (original.hz.shape[1],) or not np.issubdtype(bits.dtype, np.integer) or np.any((bits != 0) & (bits != 1)):
        return False
    return bool(np.array_equal((original.hz.astype(np.int64) @ bits.astype(np.int64)) % 2, original.syndrome))


def _checked(budgets: BudgetTree, leaf_id: str, compute, *, lifted: int = 0):
    before_phase5_work(leaf_id)
    reservation = budgets.reserve(
        "attempt", WorkVector(original_checks=1, lifted_coordinates=lifted), leaf_id=leaf_id,
    )
    if reservation is None:
        return False, None
    try:
        result = compute()
    except BaseException:
        reservation.rollback()
        raise
    reservation.commit_once()
    after_phase5_work(leaf_id, budgets)
    return True, result


def _deadline(wall_clock: WallClockLimit | None) -> bool:
    return wall_clock is not None and wall_clock.check(
        "candidate_selection_boundary", scope="attempt",
    ) is not None


class IdempotentActionGate:
    """Owner-local one-leaf transaction with duplicate idempotency and stale rejection."""

    def __init__(self, owner: str, budgets: BudgetTree) -> None:
        if not isinstance(owner, str) or not owner:
            raise ValueError("action owner must be nonempty")
        self.owner = owner
        self.budgets = budgets
        self.revision = 0
        self._committed: dict[str, tuple[int, WorkVector, str, object]] = {}
        self._lock = RLock()

    def commit(
        self, key: str, *, expected_revision: int, work: WorkVector,
        leaf_id: str, value: object,
    ) -> object | None:
        if not isinstance(key, str) or not key or type(expected_revision) is not int or not isinstance(work, WorkVector):
            raise ValueError("action proposal requires a typed key, revision, and work")
        with self._lock:
            previous = self._committed.get(key)
            record = (expected_revision, work, leaf_id, value)
            if previous is not None:
                if previous != record:
                    raise ValueError("repeated action key conflicts with committed evidence")
                return previous[3]
            if expected_revision != self.revision:
                raise ValueError("stale intervention proposal revision")
            before_phase5_work(leaf_id)
            reservation = self.budgets.reserve("attempt", work, leaf_id=leaf_id)
            if reservation is None:
                return None
            reservation.commit_once()
            after_phase5_work(leaf_id, self.budgets)
            self._committed[key] = record
            self.revision += 1
            return value


@dataclass(frozen=True, slots=True)
class FreezingSpec:
    period_sweeps: int
    lifetime_sweeps: int
    retry_cap: int
    root_seed: str
    fixed_value: int = 0

    def __post_init__(self) -> None:
        for name in ("period_sweeps", "lifetime_sweeps", "retry_cap"):
            _positive(getattr(self, name), name)
        if self.fixed_value != 0 or not isinstance(self.root_seed, str) or not self.root_seed:
            raise ValueError("binary CSS freezing fixes zero and requires a decoder seed")


@dataclass(frozen=True, slots=True)
class FreezingTrial:
    order: int
    check_index: int
    target_index: int
    fixed_value: int
    neighbor_stream: str
    working_lineage_id: str
    session_owner: str
    initial_state_digest: str | None
    final_state_digest: str | None
    diagnostic_candidate: tuple[int, ...] | None
    lifted_candidate: tuple[int, ...] | None
    original_valid: bool | None
    termination: str
    action_leaf: str | None
    sweep_leaves: tuple[str, ...]
    release_leaf: str | None
    release_view_original: str
    remaining_fixations: tuple[int, ...] = ()
    reset_rule: str = "fresh_structural_branch_then_release_to_original"


@dataclass(frozen=True, slots=True)
class FreezingResult:
    qualification: str
    source_revision: str
    source_kernel_family: str
    native_status: str
    root_owner: str
    baseline_candidate: tuple[int, ...]
    frustrated_checks: tuple[int, ...]
    trials: tuple[FreezingTrial, ...]
    selected_candidate: tuple[int, ...] | None
    termination: str
    work: WorkVector
    leaves: tuple[tuple[str, str, WorkVector], ...]


class FreezingController:
    """Poulin–Chung-inspired frustrated-check, temporary zero-freeze adaptation."""

    def __init__(self, spec: FreezingSpec | Mapping[str, object]) -> None:
        self.spec = spec if isinstance(spec, FreezingSpec) else FreezingSpec(**spec)

    def run(
        self, original: OriginalProblem, *, error_rate: float, budgets: BudgetTree,
        wall_clock: WallClockLimit | None = None,
        damping_gamma: float | None = None,
    ) -> FreezingResult:
        root = _owner("freezing", original, self.spec.root_seed, error_rate)
        table = EdgeTable.from_check_matrix(original.hz)
        baseline = BpSession(table, original.syndrome, error_rate=error_rate, owner_identity=root + ":baseline", damping_gamma=damping_gamma)
        baseline_valid = False
        baseline_term = "failed_period"
        for index in range(self.spec.period_sweeps):
            try:
                moved = baseline.advance(budgets=budgets, leaf_id=f"{root}:baseline:sweep:{index}", bp_call_start=index == 0, wall_clock=wall_clock)
            except (NumericalFailure, ValueError, FloatingPointError):
                baseline_term = "numerical_failure"
                break
            if not moved.admitted:
                baseline_term = moved.termination or "count_budget_exhausted"
                break
            if _deadline(wall_clock):
                baseline_term = "wall_clock_deadline"
                break
            admitted, baseline_valid = _checked(
                budgets, f"{root}:baseline:check:{index}",
                lambda: baseline.original_syndrome_valid(original.hz),
            )
            if not admitted:
                baseline_term = "count_budget_exhausted"
                break
            if baseline_valid:
                baseline_term = "baseline_valid"
                break
        diagnostic = _bits(baseline.state.candidate)
        frustrated: tuple[int, ...] = ()
        trials: list[FreezingTrial] = []
        selected = diagnostic if baseline_valid else None
        termination = baseline_term if baseline_term != "failed_period" else "no_proposal"
        if not baseline_valid and baseline_term == "failed_period":
            if _deadline(wall_clock):
                return FreezingResult(
                    "controlled_css_adaptation", "arxiv:0801.1241", "quaternary_depolarizing_bp", "author_code_unverified",
                    root, diagnostic, frustrated, tuple(trials), selected, "wall_clock_deadline",
                    budgets.summary("attempt"), budgets.leaf_events(),
                )
            gate = IdempotentActionGate(root, budgets)
            choices: list[tuple[int, int, str]] = []
            seen: set[int] = set()
            target_order_leaf = root + ":target-order"
            before_phase5_work(target_order_leaf)
            target_order = budgets.reserve(
                "attempt", WorkVector(order_generation=1, order_selection=1, ranking_scans=original.hz.shape[0] + original.hz.shape[1]),
                leaf_id=target_order_leaf,
            )
            if target_order is None:
                return FreezingResult(
                    "controlled_css_adaptation", "arxiv:0801.1241", "quaternary_depolarizing_bp", "author_code_unverified",
                    root, diagnostic, frustrated, tuple(trials), selected, "count_budget_exhausted",
                    budgets.summary("attempt"), budgets.leaf_events(),
                )
            try:
                mismatched = (original.hz.astype(np.int64) @ baseline.state.candidate.astype(np.int64)) % 2 != original.syndrome
                frustrated = tuple(int(index) for index in np.flatnonzero(mismatched))
                for check in frustrated:
                    stream = decoder_stream_identity(root, "freezing", f"check:{check}", 0, "neighbor_draw")
                    seed = int(stream.rsplit("-", 1)[-1][:16], 16)
                    neighbors = sorted(int(i) for i in np.flatnonzero(original.hz[check]))
                    drawn = np.random.default_rng(seed).permutation(neighbors)
                    for variable in drawn:
                        target = int(variable)
                        if target not in seen:
                            choices.append((check, target, stream))
                            seen.add(target)
            except BaseException:
                target_order.rollback()
                raise
            target_order.commit_once()
            after_phase5_work(target_order_leaf, budgets)
            for order, (check, target, stream) in enumerate(choices[:self.spec.retry_cap]):
                owner = f"{root}:trial:{order}:target:{target}"
                action_leaf = owner + ":freeze"
                if _deadline(wall_clock):
                    termination = "wall_clock_deadline"
                    break
                admitted = gate.commit(
                    owner, expected_revision=gate.revision,
                    work=WorkVector(intervention_actions=1, fixation_actions=1, transformations=1),
                    leaf_id=action_leaf, value=target,
                )
                if admitted is None:
                    trials.append(FreezingTrial(
                        order, check, target, 0, stream, "", owner, None, None,
                        None, None, None, "count_budget_exhausted", None, (), None,
                        original.lineage_id,
                    ))
                    termination = "count_budget_exhausted"
                    break
                working, cert = transform_fixed_coordinates(original, (target,), (0,))
                session = BpSession(
                    EdgeTable.from_check_matrix(working.check_matrix), working.syndrome,
                    error_rate=error_rate, owner_identity=owner, damping_gamma=damping_gamma,
                )
                initial = session.state.digest
                sweep_leaves: list[str] = []
                lifted: tuple[int, ...] | None = None
                valid: bool | None = None
                local_term = "lifetime_expired"
                if _deadline(wall_clock):
                    local_term = "wall_clock_deadline"
                else:
                    contradiction_leaf = owner + ":contradiction-check"
                    before_phase5_work(contradiction_leaf)
                    contradiction = budgets.reserve("attempt", WorkVector(candidate_checks=1), leaf_id=contradiction_leaf)
                    if contradiction is None:
                        local_term = "count_budget_exhausted"
                    else:
                        try:
                            contradictory = bool(np.any(
                                (np.count_nonzero(working.check_matrix, axis=1) == 0)
                                & (working.syndrome == 1)
                            ))
                        except BaseException:
                            contradiction.rollback()
                            raise
                        contradiction.commit_once()
                        after_phase5_work(contradiction_leaf, budgets)
                        local_term = "contradictory_empty_check" if contradictory else "lifetime_expired"
                if local_term == "contradictory_empty_check":
                    pass
                elif local_term == "wall_clock_deadline" or local_term == "count_budget_exhausted":
                    pass
                else:
                    for sweep in range(self.spec.lifetime_sweeps):
                        leaf = f"{owner}:sweep:{sweep}"
                        try:
                            moved = session.advance(budgets=budgets, leaf_id=leaf, bp_call_start=sweep == 0, wall_clock=wall_clock)
                        except (NumericalFailure, ValueError, FloatingPointError):
                            local_term = "numerical_failure"
                            break
                        if not moved.admitted:
                            local_term = moved.termination or "count_budget_exhausted"
                            break
                        sweep_leaves.append(leaf)
                        if _deadline(wall_clock):
                            local_term = "wall_clock_deadline"
                            break
                        try:
                            checked, lift = _checked(
                                budgets, f"{owner}:lift-check:{sweep}",
                                lambda: lift_candidate(working, cert, session.state.candidate),
                                lifted=original.hz.shape[1],
                            )
                        except ValueError:
                            local_term = "invalid_lift"
                            break
                        if not checked:
                            local_term = "count_budget_exhausted"
                            break
                        assert lift is not None
                        lifted = _bits(lift.candidate)
                        valid = lift.working_valid and lift.original_valid
                        if valid:
                            local_term = "valid_original_candidate"
                            selected = lifted
                            break
                release_leaf: str | None = None
                if selected is None and local_term not in ("count_budget_exhausted", "wall_clock_deadline"):
                    release_leaf = owner + ":release"
                    released = gate.commit(
                        release_leaf, expected_revision=gate.revision,
                        work=WorkVector(intervention_actions=1, transformations=1),
                        leaf_id=release_leaf, value=original.lineage_id,
                    )
                    if released is None:
                        release_leaf = None
                        local_term = "count_budget_exhausted"
                    else:
                        # Reconstruct from the immutable original and no remaining
                        # fixations.  The parent graph is never modified.
                        release_view, _ = transform_fixed_coordinates(original, (), ())
                        if not np.array_equal(release_view.check_matrix, original.hz):
                            raise ValueError("freeze release did not restore original graph")
                trials.append(FreezingTrial(
                    order, check, target, 0, stream, working.lineage_id, owner,
                    initial, session.state.digest, _bits(session.state.candidate),
                    lifted, valid, local_term, action_leaf, tuple(sweep_leaves),
                    release_leaf, original.lineage_id,
                ))
                if selected is not None:
                    termination = "freeze_valid"
                    break
                if local_term in ("count_budget_exhausted", "wall_clock_deadline"):
                    termination = local_term
                    break
            else:
                termination = (
                    "retry_cap_reached" if self.spec.retry_cap < len(choices)
                    else "no_eligible_target" if not choices else "no_proposal"
                )
        return FreezingResult(
            "controlled_css_adaptation", "arxiv:0801.1241",
            "quaternary_depolarizing_bp", "author_code_unverified",
            root, diagnostic, frustrated, tuple(trials), selected, termination,
            budgets.summary("attempt"), budgets.leaf_events(),
        )


@dataclass(frozen=True, slots=True)
class SyndromeFlipSpec:
    baseline_sweeps: int
    attempt_sweeps: int
    top_k: int
    max_weight: int
    test_cap: int
    root_seed: str

    def __post_init__(self) -> None:
        for name in ("baseline_sweeps", "attempt_sweeps", "top_k", "max_weight", "test_cap"):
            _positive(getattr(self, name), name)
        if self.baseline_sweeps < 2 or not isinstance(self.root_seed, str) or not self.root_seed:
            raise ValueError("syndrome flip needs two baseline decisions and a decoder seed")


@dataclass(frozen=True, slots=True)
class SyndromeFlipTest:
    order: int
    test_vector: tuple[int, ...]
    transformed_syndrome: tuple[int, ...]
    working_lineage_id: str
    lift_digest: str
    session_owner: str
    initial_state_digest: str | None
    final_state_digest: str | None
    working_candidate: tuple[int, ...] | None
    raw_original_valid: bool | None
    lifted_candidate: tuple[int, ...] | None
    working_valid: bool | None
    original_valid: bool | None
    eligible: bool
    termination: str
    action_leaf: str | None
    sweep_leaves: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SyndromeFlipResult:
    qualification: str
    source_revision: str
    source_code_commit: str
    ordering_status: str
    root_owner: str
    stream_identity: str
    original_lineage_id: str
    baseline_candidate: tuple[int, ...]
    baseline_oscillations: tuple[int, ...]
    ranked_targets: tuple[int, ...]
    tests: tuple[SyndromeFlipTest, ...]
    selected_candidate: tuple[int, ...] | None
    selected_test_order: int | None
    termination: str
    work: WorkVector
    leaves: tuple[tuple[str, str, WorkVector], ...]


def select_syndrome_flip_test(
    rows: Sequence[SyndromeFlipTest], original: OriginalProblem,
) -> SyndromeFlipTest | None:
    """Choose the first declared certified original-valid test, regardless of arrival."""
    eligible = [
        row for row in rows
        if row.eligible and row.working_valid and row.original_valid
        and row.lifted_candidate is not None and _original_valid(original, row.lifted_candidate)
    ]
    return min(eligible, key=lambda row: row.order, default=None)


class SyndromeFlipController:
    """BP-SF with stable oscillation ranking and certified syndrome XOR lifts."""

    def __init__(self, spec: SyndromeFlipSpec | Mapping[str, object]) -> None:
        self.spec = spec if isinstance(spec, SyndromeFlipSpec) else SyndromeFlipSpec(**spec)

    def run(
        self, original: OriginalProblem, *, error_rate: float, budgets: BudgetTree,
        wall_clock: WallClockLimit | None = None,
        damping_gamma: float | None = None,
        kernel: BinarySpaKernel | None = None,
    ) -> SyndromeFlipResult:
        root = _owner("syndrome-flip", original, self.spec.root_seed, error_rate)
        n = original.hz.shape[1]
        stream = decoder_stream_identity(root, "bpsf", "test_vector_order", 0, "test_selection")
        baseline = BpSession(
            EdgeTable.from_check_matrix(original.hz), original.syndrome,
            error_rate=error_rate, owner_identity=root + ":baseline", damping_gamma=damping_gamma,
            kernel=kernel,
        )
        counts = np.zeros(n, dtype=np.int64)
        # BP-SF Algorithm 1 initializes the prior hard decision to the all-zero
        # vector, so nonzero decisions in the first update count as flips.
        previous = tuple(0 for _ in range(n))
        baseline_valid = False
        baseline_term = "failed_baseline"
        for sweep in range(self.spec.baseline_sweeps):
            try:
                moved = baseline.advance(budgets=budgets, leaf_id=f"{root}:baseline:sweep:{sweep}", bp_call_start=sweep == 0, wall_clock=wall_clock)
            except (NumericalFailure, ValueError, FloatingPointError):
                baseline_term = "numerical_failure"
                break
            if not moved.admitted:
                baseline_term = moved.termination or "count_budget_exhausted"
                break
            current = _bits(baseline.state.candidate)
            counts += np.asarray(
                [int(a != b) for a, b in zip(previous, current, strict=True)],
                dtype=np.int64,
            )
            previous = current
            if _deadline(wall_clock):
                baseline_term = "wall_clock_deadline"
                break
            admitted, baseline_valid = _checked(
                budgets, f"{root}:baseline:check:{sweep}",
                lambda: baseline.original_syndrome_valid(original.hz),
            )
            if not admitted:
                baseline_term = "count_budget_exhausted"
                break
            if baseline_valid:
                baseline_term = "baseline_valid"
                break
        ranked: tuple[int, ...] = ()
        tests: list[SyndromeFlipTest] = []
        selected: SyndromeFlipTest | None = None
        termination = baseline_term
        if not baseline_valid and baseline_term == "failed_baseline":
            if _deadline(wall_clock):
                termination = "wall_clock_deadline"
            else:
                generation_leaf = root + ":test-order"
                before_phase5_work(generation_leaf)
                generation = budgets.reserve(
                    "attempt", WorkVector(order_generation=1, ranking_scans=n),
                    leaf_id=generation_leaf,
                )
                if generation is None:
                    return SyndromeFlipResult(
                        "controlled_css_adaptation", "arxiv:2507.00254v1",
                        "0417d33fc2ffb3b442d0397bb09954fc1c6c3938",
                        "seeded_declared_order_replaces_unseeded_parallel_arrival", root, stream,
                        original.lineage_id, _bits(baseline.state.candidate),
                        tuple(int(x) for x in counts), ranked, tuple(tests),
                        None, None, "count_budget_exhausted",
                        budgets.summary("attempt"), budgets.leaf_events(),
                    )
                else:
                    try:
                        ranked = tuple(sorted(range(n), key=lambda index: (-int(counts[index]), index))[:self.spec.top_k])
                        vectors: list[tuple[int, ...]] = []
                        for weight in range(1, min(self.spec.max_weight, len(ranked)) + 1):
                            for indices in combinations(ranked, weight):
                                t = [0] * n
                                for index in indices:
                                    t[index] = 1
                                vectors.append(tuple(t))
                        rng = np.random.default_rng(int(stream.rsplit("-", 1)[-1][:16], 16))
                        declared = tuple(vectors[int(i)] for i in rng.permutation(len(vectors)))
                    except BaseException:
                        generation.rollback()
                        raise
                    generation.commit_once()
                    after_phase5_work(generation_leaf, budgets)
                gate = IdempotentActionGate(root, budgets)
                for order, t in enumerate(declared[:self.spec.test_cap]):
                    owner = f"{root}:test:{order}"
                    action_leaf = owner + ":transform"
                    if _deadline(wall_clock):
                        termination = "wall_clock_deadline"
                        break
                    admitted = gate.commit(
                        owner, expected_revision=gate.revision,
                        work=WorkVector(intervention_actions=1, transformations=1),
                        leaf_id=action_leaf, value=t,
                    )
                    if admitted is None:
                        tests.append(SyndromeFlipTest(
                            order, t, (), "", "",
                            owner, None, None, None, None, None, None, None, False,
                            "count_budget_exhausted", None, (),
                        ))
                        termination = "count_budget_exhausted"
                        break
                    working, cert = transform_syndrome(original, np.asarray(t, dtype=np.uint8))
                    session = BpSession(
                        EdgeTable.from_check_matrix(working.check_matrix), working.syndrome,
                        error_rate=error_rate, owner_identity=owner, damping_gamma=damping_gamma,
                        kernel=kernel,
                    )
                    initial = session.state.digest
                    sweep_leaves: list[str] = []
                    lifted: tuple[int, ...] | None = None
                    working_valid: bool | None = None
                    original_valid: bool | None = None
                    local_term = "attempt_sweep_cap"
                    for sweep in range(self.spec.attempt_sweeps):
                        leaf = f"{owner}:sweep:{sweep}"
                        try:
                            moved = session.advance(budgets=budgets, leaf_id=leaf, bp_call_start=sweep == 0, wall_clock=wall_clock)
                        except (NumericalFailure, ValueError, FloatingPointError):
                            local_term = "numerical_failure"
                            break
                        if not moved.admitted:
                            local_term = moved.termination or "count_budget_exhausted"
                            break
                        sweep_leaves.append(leaf)
                        if _deadline(wall_clock):
                            local_term = "wall_clock_deadline"
                            break
                        try:
                            checked, lift = _checked(
                                budgets, f"{owner}:lift-check:{sweep}",
                                lambda: lift_candidate(working, cert, session.state.candidate),
                                lifted=n,
                            )
                        except ValueError:
                            local_term = "invalid_lift"
                            break
                        if not checked:
                            local_term = "count_budget_exhausted"
                            break
                        assert lift is not None
                        lifted = _bits(lift.candidate)
                        working_valid, original_valid = lift.working_valid, lift.original_valid
                        if working_valid and original_valid:
                            local_term = "valid_original_candidate"
                            break
                        local_term = lift.reason or "working_syndrome_invalid"
                    row = SyndromeFlipTest(
                        order, t, _bits(working.syndrome), working.lineage_id, cert.digest,
                        owner, initial, session.state.digest, _bits(session.state.candidate),
                        _original_valid(original, session.state.candidate),
                        lifted, working_valid, original_valid,
                        bool(working_valid and original_valid), local_term, action_leaf,
                        tuple(sweep_leaves),
                    )
                    tests.append(row)
                    if row.eligible:
                        selected = row
                        break
                    if local_term in ("count_budget_exhausted", "wall_clock_deadline"):
                        termination = local_term
                        break
                else:
                    termination = "test_cap_reached" if self.spec.test_cap < len(declared) else "no_proposal"
                if selected is not None:
                    termination = "syndrome_flip_valid"
        selected_candidate = _bits(baseline.state.candidate) if baseline_valid else None if selected is None else selected.lifted_candidate
        return SyndromeFlipResult(
            "controlled_css_adaptation", "arxiv:2507.00254v1",
            "0417d33fc2ffb3b442d0397bb09954fc1c6c3938",
            "seeded_declared_order_replaces_unseeded_parallel_arrival", root, stream,
            original.lineage_id, _bits(baseline.state.candidate),
            tuple(int(x) for x in counts), ranked, tuple(tests),
            selected_candidate, None if selected is None else selected.order,
            termination, budgets.summary("attempt"), budgets.leaf_events(),
        )


@dataclass(frozen=True, slots=True)
class SignFlipSpec:
    alpha: float
    trunk_sweeps: int
    continuation_sweeps: int

    def __post_init__(self) -> None:
        if type(self.alpha) not in (int, float) or not np.isfinite(self.alpha) or not 0 < self.alpha <= 1:
            raise ValueError("normalized min-sum alpha must be finite in (0,1]")
        _positive(self.trunk_sweeps, "trunk_sweeps")
        _positive(self.continuation_sweeps, "continuation_sweeps")


@dataclass(frozen=True, slots=True)
class SignFlipResult:
    qualification: str
    source_revision: str
    native_status: str
    numerical_profile: str
    trigger: str
    root_owner: str
    mismatched_checks: tuple[int, ...]
    target_scores: tuple[int, ...]
    target_index: int | None
    prior_before: tuple[float, ...]
    prior_after: tuple[float, ...]
    v2c_before: tuple[float, ...]
    v2c_after_action: tuple[float, ...]
    c2v_before: tuple[float, ...]
    c2v_after_action: tuple[float, ...]
    posterior_before: tuple[float, ...]
    posterior_after_action: tuple[float, ...]
    action_state_digest: str | None
    continuation_state_digest: str | None
    selected_candidate: tuple[int, ...] | None
    termination: str
    work: WorkVector
    leaves: tuple[tuple[str, str, WorkVector], ...]


class SignFlipController:
    """Sign-only Global adaptation after a failed normalized-min-sum trunk."""

    def __init__(self, spec: SignFlipSpec | Mapping[str, object]) -> None:
        self.spec = spec if isinstance(spec, SignFlipSpec) else SignFlipSpec(**spec)

    def run(
        self, original: OriginalProblem, *, error_rate: float, budgets: BudgetTree,
        wall_clock: WallClockLimit | None = None,
        damping_gamma: float | None = None,
    ) -> SignFlipResult:
        root = _owner("sign-flip", original, f"alpha:{self.spec.alpha}", error_rate)
        assignment = ParameterAssignment(shape="scalar", value=float(self.spec.alpha))
        kernel = BinarySpaKernel(
            profile=MIN_SUM_CPU_F64, update_rule=NormalizedMinSumUpdate(alpha=assignment),
        )
        session = BpSession(
            EdgeTable.from_check_matrix(original.hz), original.syndrome,
            error_rate=error_rate, owner_identity=root, kernel=kernel, damping_gamma=damping_gamma,
        )
        trigger = "failed_normalized_min_sum_trunk"
        termination = "no_proposal"
        baseline_valid = False
        for sweep in range(self.spec.trunk_sweeps):
            try:
                moved = session.advance(budgets=budgets, leaf_id=f"{root}:trunk:{sweep}", bp_call_start=sweep == 0, wall_clock=wall_clock)
            except (NumericalFailure, ValueError, FloatingPointError):
                termination = "numerical_failure"
                trigger = "trunk_numerical_failure"
                break
            if not moved.admitted:
                termination = moved.termination or "count_budget_exhausted"
                trigger = "trunk_denied"
                break
            if _deadline(wall_clock):
                termination = "wall_clock_deadline"
                trigger = "trunk_deadline"
                break
            checked, baseline_valid = _checked(
                budgets, f"{root}:trunk-check:{sweep}",
                lambda: session.original_syndrome_valid(original.hz),
            )
            if not checked:
                termination = "count_budget_exhausted"
                trigger = "trunk_denied"
                break
            if baseline_valid:
                trigger = "baseline_valid"
                termination = "baseline_valid"
                break
        before = session.state
        checks: tuple[int, ...] = ()
        scores: tuple[int, ...] = ()
        target: int | None = None
        if trigger == "failed_normalized_min_sum_trunk":
            if _deadline(wall_clock):
                termination = "wall_clock_deadline"
                trigger = "trunk_deadline"
            else:
                target_reservation_leaf = root + ":target-order"
                before_phase5_work(target_reservation_leaf)
                target_reservation = budgets.reserve(
                    "attempt", WorkVector(order_generation=1, order_selection=1, ranking_scans=original.hz.shape[0] + original.hz.shape[1]),
                    leaf_id=target_reservation_leaf,
                )
                if target_reservation is None:
                    termination = "count_budget_exhausted"
                    trigger = "trunk_denied"
                else:
                    try:
                        mismatched_mask = (original.hz.astype(np.int64) @ before.candidate.astype(np.int64)) % 2 != original.syndrome
                        checks = tuple(int(index) for index in np.flatnonzero(mismatched_mask))
                        scores = tuple(int(np.sum(original.hz[list(checks), index])) if checks else 0 for index in range(original.hz.shape[1]))
                        target = None if not checks or max(scores, default=0) == 0 else min(
                            index for index, score in enumerate(scores) if score == max(scores)
                        )
                    except BaseException:
                        target_reservation.rollback()
                        raise
                    target_reservation.commit_once()
                    after_phase5_work(target_reservation_leaf, budgets)
        action_state: str | None = None
        continuation_state: str | None = None
        selected = _bits(before.candidate) if baseline_valid else None
        after = before
        if trigger == "failed_normalized_min_sum_trunk" and termination not in ("count_budget_exhausted", "numerical_failure", "wall_clock_deadline"):
            if target is None:
                termination = "no_eligible_target"
            else:
                try:
                    moved = session.stage_posterior_sign(target, budgets=budgets, leaf_id=f"{root}:posterior-sign:{before.revision}", wall_clock=wall_clock)
                except ValueError:
                    termination = "stale_proposal"
                else:
                    if not moved.admitted:
                        termination = moved.termination or "count_budget_exhausted"
                    else:
                        after = session.state
                        action_state = after.digest
                        for sweep in range(self.spec.continuation_sweeps):
                            try:
                                moved = session.advance(
                                    budgets=budgets, leaf_id=f"{root}:continuation:{sweep}",
                                    bp_call_start=sweep == 0, wall_clock=wall_clock,
                                )
                            except (NumericalFailure, ValueError, FloatingPointError):
                                termination = "numerical_failure"
                                break
                            if not moved.admitted:
                                termination = moved.termination or "count_budget_exhausted"
                                break
                            continuation_state = session.state.digest
                            if _deadline(wall_clock):
                                termination = "wall_clock_deadline"
                                break
                            checked, valid = _checked(
                                budgets, f"{root}:continuation-check:{sweep}",
                                lambda: session.original_syndrome_valid(original.hz),
                            )
                            if not checked:
                                termination = "count_budget_exhausted"
                                break
                            if valid:
                                selected = _bits(session.state.candidate)
                                termination = "sign_flip_valid"
                                break
                        else:
                            termination = "continuation_cap_reached"
        return SignFlipResult(
            "bsfbp_sign_only_controlled_adaptation", "doi:10.1109/TQE.2023.3279379",
            "author_code_unverified", MIN_SUM_CPU_F64.profile_id, trigger, root,
            checks, scores, target,
            tuple(float(x) for x in before.prior), tuple(float(x) for x in after.prior),
            tuple(float(x) for x in before.v2c), tuple(float(x) for x in after.v2c),
            tuple(float(x) for x in before.c2v), tuple(float(x) for x in after.c2v),
            tuple(float(x) for x in before.posterior), tuple(float(x) for x in after.posterior),
            action_state, continuation_state, selected, termination,
            budgets.summary("attempt"), budgets.leaf_events(),
        )


def reconstruct_freezing_result(
    spec: FreezingSpec | Mapping[str, object], original: OriginalProblem,
    error_rate: float, expected: FreezingResult,
    *, budget_limits: tuple[BudgetLimit, ...] = (),
) -> FreezingResult:
    if not isinstance(expected, FreezingResult):
        raise ValueError("freezing replay requires typed evidence")
    rebuilt = FreezingController(spec).run(
        original, error_rate=error_rate, budgets=BudgetTree(limits=budget_limits, parents={}),
    )
    if rebuilt != expected:
        raise ValueError("freezing replay disagrees with target, release, or work")
    return rebuilt


def reconstruct_syndrome_flip_result(
    spec: SyndromeFlipSpec | Mapping[str, object], original: OriginalProblem,
    error_rate: float, expected: SyndromeFlipResult,
    *, budget_limits: tuple[BudgetLimit, ...] = (),
) -> SyndromeFlipResult:
    if not isinstance(expected, SyndromeFlipResult):
        raise ValueError("syndrome-flip replay requires typed evidence")
    rebuilt = SyndromeFlipController(spec).run(
        original, error_rate=error_rate, budgets=BudgetTree(limits=budget_limits, parents={}),
    )
    if rebuilt != expected:
        raise ValueError("syndrome-flip replay disagrees with test, lift, or work")
    return rebuilt


def reconstruct_sign_flip_result(
    spec: SignFlipSpec | Mapping[str, object], original: OriginalProblem,
    error_rate: float, expected: SignFlipResult,
    *, budget_limits: tuple[BudgetLimit, ...] = (),
) -> SignFlipResult:
    if not isinstance(expected, SignFlipResult):
        raise ValueError("sign-flip replay requires typed evidence")
    rebuilt = SignFlipController(spec).run(
        original, error_rate=error_rate, budgets=BudgetTree(limits=budget_limits, parents={}),
    )
    if rebuilt != expected:
        raise ValueError("sign-flip replay disagrees with target, session state, or work")
    return rebuilt
