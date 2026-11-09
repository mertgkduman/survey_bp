"""Canonical-adaptation MBBP-LD augmented bases and member-list controller.

The paper leaves its experimental partition/permutation and a few notation
details unresolved.  This module therefore accepts every redundant check as an
explicit GF(2) transform of the immutable original checks and labels its
execution a canonical adaptation.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Callable, Literal

import numpy as np
from bp_registry.compiled_contracts import immutable_snapshot

from .budgets import BudgetLimit, BudgetTree, WorkVector
from .candidate_selection import CandidateOrigin, FrequencyOverWeightScore, FrozenCandidateSelection, freeze_candidate_list
from .execution import CanonicalLocalStepExecutor, ScheduleProgress
from .kernel import BinarySpaKernel
from .lineage import LineageId, stable_lineage_id
from .numerics import MIN_SUM_CPU_F64
from .problems import OriginalProblem
from .schedules import CheckNodeSerialSchedule, EdgeTable
from .updates import NormalizedMinSumUpdate, ParameterAssignment


def _readonly_binary(value: object, *, ndim: int, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != ndim or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary integer array with {ndim} dimensions")
    copied = immutable_snapshot(array, dtype=np.uint8)
    return copied


def _identity(prefix: str, payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{prefix}-{sha256(canonical.encode('utf-8')).hexdigest()[:20]}"


@dataclass(frozen=True)
class AugmentedBasisSystem:
    """One immutable original-plus-redundant parity-check system."""

    member_id: str
    local_ordinal: int
    partition_identity: str
    permutation_identity: str
    redundant_transforms: tuple[tuple[int, ...], ...]
    check_matrix: np.ndarray
    syndrome: np.ndarray
    content_identity: str
    source_status: Literal["canonical_adaptation"] = "canonical_adaptation"

    def __post_init__(self) -> None:
        object.__setattr__(self, "check_matrix", _readonly_binary(self.check_matrix, ndim=2, name="augmented check matrix"))
        object.__setattr__(self, "syndrome", _readonly_binary(self.syndrome, ndim=1, name="augmented syndrome"))
        if self.check_matrix.shape[0] != self.syndrome.shape[0]:
            raise ValueError("augmented check rows and syndrome length differ")
        original_rows = self.check_matrix.shape[0] - len(self.redundant_transforms)
        if original_rows < 1 or any(
            len(transform) != original_rows or any(type(value) is not int or value not in (0, 1) for value in transform)
            or not any(transform)
            for transform in self.redundant_transforms
        ):
            raise ValueError("augmented basis has inconsistent redundant-transform row dimensions")

    def as_evidence(self) -> dict[str, object]:
        return {
            "member_id": self.member_id,
            "local_ordinal": self.local_ordinal,
            "partition_identity": self.partition_identity,
            "permutation_identity": self.permutation_identity,
            "redundant_transforms": [list(row) for row in self.redundant_transforms],
            "check_matrix": self.check_matrix.tolist(),
            "syndrome": self.syndrome.tolist(),
            "content_identity": self.content_identity,
            "source_status": self.source_status,
        }


@dataclass(frozen=True)
class MbbpBasis:
    """Declared input to one MBBP member's augmented parity-check basis."""

    member_id: str
    local_ordinal: int
    partition_identity: str
    permutation_identity: str
    redundant_transforms: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.member_id, str) or not self.member_id:
            raise ValueError("MBBP member identity must be nonempty")
        if type(self.local_ordinal) is not int or self.local_ordinal < 0:
            raise ValueError("MBBP member local ordinal must be nonnegative")
        if not all(isinstance(value, str) and value for value in (self.partition_identity, self.permutation_identity)):
            raise ValueError("MBBP partition and permutation identities must be declared")
        if not isinstance(self.redundant_transforms, tuple):
            raise ValueError("MBBP redundant transforms must be an ordered tuple")

    def augment(self, original: OriginalProblem) -> AugmentedBasisSystem:
        """Derive redundant rows and their syndrome with the same GF(2) map."""
        if not isinstance(original, OriginalProblem) or original.hz.shape[0] == 0:
            raise ValueError("MBBP augmentation requires a nonempty immutable original problem")
        check_count, variable_count = original.hz.shape
        transforms: list[tuple[int, ...]] = []
        redundant_rows: list[np.ndarray] = []
        redundant_syndromes: list[int] = []
        for transform in self.redundant_transforms:
            vector = _readonly_binary(transform, ndim=1, name="redundant check transformation")
            if vector.shape != (check_count,) or not np.any(vector):
                raise ValueError("redundant check transformation must be nonzero and original-check aligned")
            transforms.append(tuple(int(value) for value in vector.tolist()))
            redundant_rows.append(((vector.astype(np.int64) @ original.hz.astype(np.int64)) % 2).astype(np.uint8))
            redundant_syndromes.append(int((vector.astype(np.int64) @ original.syndrome.astype(np.int64)) % 2))
        redundant = np.asarray(redundant_rows, dtype=np.uint8).reshape((len(transforms), variable_count))
        matrix = np.vstack((original.hz, redundant))
        syndrome = np.concatenate((original.syndrome, np.asarray(redundant_syndromes, dtype=np.uint8)))
        payload = {
            "member_id": self.member_id,
            "local_ordinal": self.local_ordinal,
            "partition_identity": self.partition_identity,
            "permutation_identity": self.permutation_identity,
            "transforms": transforms,
            "original_hz": original.hz.tolist(),
            "original_syndrome": original.syndrome.tolist(),
        }
        return AugmentedBasisSystem(
            self.member_id, self.local_ordinal, self.partition_identity, self.permutation_identity,
            tuple(transforms), matrix, syndrome, _identity("basis", payload),
        )


@dataclass(frozen=True)
class MbbpSpec:
    """Closed canonical-adaptation execution controls for an MBBP list."""

    bases: tuple[MbbpBasis, ...]
    max_iterations: int
    alpha: float = 0.875
    max_member_c2v_updates: int | None = None
    source_status: Literal["canonical_adaptation"] = "canonical_adaptation"

    def __post_init__(self) -> None:
        if not self.bases or any(not isinstance(basis, MbbpBasis) for basis in self.bases):
            raise ValueError("MBBP requires at least one declared basis")
        ids = tuple(basis.member_id for basis in self.bases)
        if len(set(ids)) != len(ids):
            raise ValueError("MBBP member identities must be unique")
        if tuple(sorted(self.bases, key=lambda basis: (basis.local_ordinal, basis.member_id))) != self.bases:
            raise ValueError("MBBP basis descriptors must be declared in stable ordered form")
        if type(self.max_iterations) is not int or self.max_iterations < 1:
            raise ValueError("MBBP max_iterations must be a positive integer")
        if not math.isfinite(self.alpha) or self.alpha != 0.875:
            raise ValueError("canonical MBBP-LD requires normalized-min-sum alpha=0.875")
        if self.max_member_c2v_updates is not None and (
            type(self.max_member_c2v_updates) is not int or self.max_member_c2v_updates < 0
        ):
            raise ValueError("MBBP member C2V cap must be a nonnegative integer or absent")
        if self.source_status != "canonical_adaptation":
            raise ValueError("MBBP source gaps require canonical_adaptation status")


MemberStatus = Literal[
    "converged_original_valid", "converged_original_invalid", "iteration_cap", "budget_denied",
]


@dataclass(frozen=True)
class MbbpMember:
    """Terminal evidence for one fresh augmented-basis BP member."""

    member_id: str
    local_ordinal: int
    lineage_id: LineageId
    basis_identity: str
    initial_state_identity: str
    schedule: Literal["check_node_serial"]
    normalized_min_sum_alpha: float
    status: MemberStatus
    candidate: tuple[int, ...] | None
    original_valid: bool | None
    work: WorkVector
    terminal_posterior: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if self.candidate is not None and (
            not isinstance(self.candidate, tuple)
            or any(type(value) is not int or value not in (0, 1) for value in self.candidate)
        ):
            raise ValueError("MBBP terminal candidate must be a binary tuple")
        if self.terminal_posterior is not None and (
            self.candidate is None
            or len(self.terminal_posterior) != len(self.candidate)
            or not all(math.isfinite(value) for value in self.terminal_posterior)
        ):
            raise ValueError("MBBP terminal posterior must be finite and candidate-aligned")

    @property
    def converged(self) -> bool:
        return self.status in {"converged_original_valid", "converged_original_invalid"}

    @property
    def admitted(self) -> bool:
        return self.status == "converged_original_valid" and self.candidate is not None and self.original_valid is True

    def as_evidence(self) -> dict[str, object]:
        return {
            "member_id": self.member_id,
            "local_ordinal": self.local_ordinal,
            "lineage_id": self.lineage_id.value,
            "basis_identity": self.basis_identity,
            "initial_state_identity": self.initial_state_identity,
            "schedule": self.schedule,
            "normalized_min_sum_alpha": self.normalized_min_sum_alpha,
            "status": self.status,
            "candidate": None if self.candidate is None else list(self.candidate),
            "original_valid": self.original_valid,
            "admitted": self.admitted,
            "work": self.work.as_evidence(structural_event_version=4),
        }


@dataclass(frozen=True)
class MbbpResult:
    """Frozen MBBP member list and either an admitted choice or typed failure."""

    source_status: Literal["canonical_adaptation"]
    terminal_status: Literal[
        "selected_original_valid_candidate", "no_member_converged_zero_return", "no_admitted_member_candidate",
    ]
    members: tuple[MbbpMember, ...]
    selection: FrozenCandidateSelection
    selected_candidate: tuple[int, ...] | None
    selected_origin_id: LineageId | None
    source_zero_return: tuple[int, ...] | None
    work: WorkVector
    work_leaves: tuple[tuple[str, str, WorkVector], ...]

    def as_evidence(self) -> dict[str, object]:
        return {
            "source_status": self.source_status,
            "terminal_status": self.terminal_status,
            "members": [member.as_evidence() for member in self.members],
            "selection": self.selection.as_evidence(),
            "selected_candidate": None if self.selected_candidate is None else list(self.selected_candidate),
            "selected_origin_id": None if self.selected_origin_id is None else self.selected_origin_id.value,
            "source_zero_return": None if self.source_zero_return is None else list(self.source_zero_return),
            "work": self.work.as_evidence(structural_event_version=4),
            "work_leaves": [
                {"leaf_id": leaf_id, "scope": scope, "work": work.as_evidence(structural_event_version=4)}
                for leaf_id, scope, work in self.work_leaves
            ],
        }


class MbbpController:
    """Run fresh serial normalized-min-sum members over declared augmented bases."""

    def __init__(self, spec: MbbpSpec) -> None:
        if not isinstance(spec, MbbpSpec):
            raise ValueError("MBBP controller requires a validated MbbpSpec")
        self.spec = spec

    @staticmethod
    def _valid(matrix: np.ndarray, syndrome: np.ndarray, candidate: tuple[int, ...]) -> bool:
        observed = (matrix.astype(np.int64) @ np.asarray(candidate, dtype=np.int64)) % 2
        return bool(np.array_equal(observed.astype(np.uint8), syndrome))

    def _member(
        self, *, original: OriginalProblem, system: AugmentedBasisSystem, tree: BudgetTree, scope: str,
        error_rate: float,
        prior_llrs: np.ndarray | None = None,
        boundary_observer: Callable[[str, WorkVector | None, str | None], None] | None = None,
    ) -> MbbpMember:
        table = EdgeTable.from_check_matrix(system.check_matrix)
        alpha = ParameterAssignment(shape="scalar", value=self.spec.alpha)
        kernel = BinarySpaKernel(
            profile=MIN_SUM_CPU_F64,
            update_rule=NormalizedMinSumUpdate(alpha, profile=MIN_SUM_CPU_F64),
        )
        # These objects are intentionally created inside the member boundary.
        # Neither serial C2V state nor V2C messages can cross member identities.
        schedule = CheckNodeSerialSchedule(table, kernel=kernel)
        from .numerics import finite_saturate
        messages = (np.full(table.edge_count, kernel.prior(error_rate), dtype=np.float64) if prior_llrs is None else
                    finite_saturate(prior_llrs[np.array([v for _, v in table.edges], dtype=np.intp)],
                                    boundary="mbbp_initial_prior", profile=kernel.profile))
        executor = CanonicalLocalStepExecutor(tree, scope=scope)
        lineage_id = stable_lineage_id("member", {
            "basis_identity": system.content_identity, "member_id": system.member_id,
            "local_ordinal": system.local_ordinal,
        })
        initial_material = {
            "basis_identity": system.content_identity, "lineage_id": lineage_id.value,
            "alpha": self.spec.alpha, "schedule": "check_node_serial",
        }
        if prior_llrs is not None:
            initial_material["prior_sha256"] = sha256(prior_llrs.tobytes()).hexdigest()
        initial_identity = _identity("member-state", initial_material)
        progress = ScheduleProgress(iteration=0, local_steps=0, cursor=(0,))
        terminal_candidate: tuple[int, ...] | None = None
        terminal_posterior: tuple[float, ...] | None = None
        for iteration in range(self.spec.max_iterations):
            for check_index in range(schedule.unit_count):
                progress = ScheduleProgress(iteration=iteration, local_steps=progress.local_steps, cursor=(check_index,))
                if boundary_observer is not None:
                    boundary_observer(f"mbbp:{system.member_id}:{iteration}:{check_index}:before_work", None, None)
                step = schedule.execute_local_step(
                    executor, messages, system.syndrome, error_rate=error_rate, progress=progress,
                    is_converged=lambda candidate: self._valid(system.check_matrix, system.syndrome, tuple(candidate.tolist())),
                    prior_llrs=prior_llrs,
                )
                if boundary_observer is not None:
                    boundary_observer(
                        f"mbbp:{system.member_id}:{iteration}:{check_index}:after_work",
                        tree.summary("mbbp-ensemble"), tree.leaf_events()[-1][0] if step.admitted else None,
                    )
                if not step.admitted:
                    return MbbpMember(
                        system.member_id, system.local_ordinal, lineage_id, system.content_identity, initial_identity,
                        "check_node_serial", self.spec.alpha, "budget_denied", terminal_candidate, None,
                        tree.summary(scope), terminal_posterior,
                    )
                progress = step.progress
                if step.candidate is None or step.posterior is None:
                    raise ValueError("admitted MBBP local step must expose terminal candidate and posterior")
                terminal_candidate = tuple(int(value) for value in step.candidate.tolist())
                terminal_posterior = tuple(float(value) for value in step.posterior.tolist())
                if step.candidate is not None and self._valid(
                    system.check_matrix, system.syndrome, tuple(step.candidate.tolist()),
                ):
                    candidate = tuple(int(value) for value in step.candidate.tolist())
                    check_leaf = f"{scope}:original-syndrome-check:{iteration}:{check_index}"
                    if boundary_observer is not None:
                        boundary_observer(
                            f"mbbp:{system.member_id}:{iteration}:{check_index}:original_check:before_work", None, None,
                        )
                    check = tree.reserve(
                        scope, WorkVector(original_checks=1),
                        leaf_id=check_leaf,
                    )
                    if check is None:
                        return MbbpMember(
                            system.member_id, system.local_ordinal, lineage_id, system.content_identity, initial_identity,
                            "check_node_serial", self.spec.alpha, "budget_denied", terminal_candidate, None,
                            tree.summary(scope), terminal_posterior,
                        )
                    original_valid = self._valid(original.hz, original.syndrome, candidate)
                    check.commit_once()
                    if boundary_observer is not None:
                        boundary_observer(
                            f"mbbp:{system.member_id}:{iteration}:{check_index}:original_check:after_work",
                            tree.summary("mbbp-ensemble"), check_leaf,
                        )
                    return MbbpMember(
                        system.member_id, system.local_ordinal, lineage_id, system.content_identity, initial_identity,
                        "check_node_serial", self.spec.alpha,
                        "converged_original_valid" if original_valid else "converged_original_invalid",
                        candidate, original_valid, tree.summary(scope), terminal_posterior,
                    )
        return MbbpMember(
            system.member_id, system.local_ordinal, lineage_id, system.content_identity, initial_identity,
            "check_node_serial", self.spec.alpha, "iteration_cap", terminal_candidate, None, tree.summary(scope),
            terminal_posterior,
        )

    def run(
        self, original: OriginalProblem, *, error_rate: float, completion_order: tuple[str, ...] | None = None,
        prior_llrs: np.ndarray | None = None,
        boundary_observer: Callable[[str, WorkVector | None, str | None], None] | None = None,
    ) -> MbbpResult:
        """Execute declared members in any supplied completion order, then freeze order."""
        if not isinstance(original, OriginalProblem):
            raise ValueError("MBBP run requires an immutable OriginalProblem")
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 0.5:
            raise ValueError("MBBP error_rate must lie in (0, 0.5)")
        if prior_llrs is not None:
            from .intervention_session import _frozen_f64
            prior_llrs = _frozen_f64(prior_llrs, original.hz.shape[1], "prior_llrs")
        systems = {basis.member_id: basis.augment(original) for basis in self.spec.bases}
        declared_ids = tuple(basis.member_id for basis in self.spec.bases)
        order = declared_ids if completion_order is None else tuple(completion_order)
        if len(order) != len(declared_ids) or set(order) != set(declared_ids):
            raise ValueError("MBBP completion order must name every declared member exactly once")
        scopes = {member_id: f"mbbp-member:{member_id}" for member_id in declared_ids}
        limits = (() if self.spec.max_member_c2v_updates is None else tuple(
            BudgetLimit(scope, "check_to_variable_updates", self.spec.max_member_c2v_updates)
            for scope in scopes.values()
        ))
        tree = BudgetTree(limits=limits, parents={scope: "mbbp-ensemble" for scope in scopes.values()})
        attempted = []
        for member_id in order:
            if boundary_observer is not None:
                boundary_observer(f"mbbp:{member_id}:before_member", None, None)
            attempted.append(self._member(
                original=original, system=systems[member_id], tree=tree, scope=scopes[member_id],
                error_rate=error_rate, boundary_observer=boundary_observer,
                prior_llrs=prior_llrs,
            ))
            if boundary_observer is not None:
                boundary_observer(f"mbbp:{member_id}:after_member", None, None)
        members = tuple(sorted(attempted, key=lambda member: (member.local_ordinal, member.member_id)))
        origins = tuple(CandidateOrigin(
            lineage_id=member.lineage_id, local_ordinal=member.local_ordinal, candidate=member.candidate,
            eligible=member.admitted, reason=member.status,
        ) for member in members)
        selection = freeze_candidate_list(
            original, declared_origins=tuple(member.lineage_id for member in members), origins=origins,
            score_policy=FrequencyOverWeightScore(),
        )
        selected_origin = (None if selection.selected_origin_id is None else next(
            origin for origin in selection.origins if origin.lineage_id == selection.selected_origin_id
        ))
        no_member_converged = not any(member.converged for member in members)
        terminal_status = (
            "selected_original_valid_candidate" if selected_origin is not None else
            "no_member_converged_zero_return" if no_member_converged else
            "no_admitted_member_candidate"
        )
        leaves = tuple(sorted(tree.leaf_events(), key=lambda item: (item[1], item[0])))
        return MbbpResult(
            self.spec.source_status, terminal_status, members, selection,
            None if selected_origin is None else selected_origin.candidate,
            None if selected_origin is None else selected_origin.lineage_id,
            tuple(0 for _ in range(original.hz.shape[1])) if no_member_converged else None,
            tree.summary("mbbp-ensemble"), leaves,
        )
