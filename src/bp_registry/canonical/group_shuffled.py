"""Hsu et al. non-disjoint group-shuffled BP construction for binary CSS adaptation.

The source's explicit size-two, overlap-one example is the only supported
configuration.  A sampled check order is converted to overlapping adjacent
pairs; no learned policy or external parameter artifact is involved.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import numbers

import numpy as np

from .numerics import DEFAULT_BINARY_SPA_F64, finite_saturate
from .schedules import EdgeTable, ScheduledLocalStepResult, _binary_syndrome


SOURCE_ID = "hsu-ndgsbp-2012-v1"
SOURCE_URI = "https://arxiv.org/html/1202.1060"


@dataclass(frozen=True, slots=True)
class GroupTraversal:
    """A complete source-iteration order and its overlapping check groups."""

    iteration: int
    order: tuple[int, ...]
    groups: tuple[tuple[int, int], ...]
    derived_identity: str

    def evidence(self) -> dict[str, object]:
        return {
            "source_id": SOURCE_ID,
            "source_uri": SOURCE_URI,
            "source_configuration": "group_size=2;overlap=1",
            "iteration": self.iteration,
            "order": self.order,
            "groups": self.groups,
            "derived_identity": self.derived_identity,
            "membership_multiplicity": tuple(
                (check, sum(check in group for group in self.groups))
                for check in self.order
            ),
        }


def groups_from_order(order: tuple[int, ...] | list[int], *, check_count: int) -> tuple[tuple[int, int], ...]:
    """Realize the paper's (c1,c2),(c2,c3),... worked construction."""
    if isinstance(check_count, bool) or not isinstance(check_count, numbers.Integral) or check_count < 2:
        raise ValueError("Hsu groups require at least two checks")
    if not isinstance(order, (tuple, list)) or len(order) != check_count:
        raise ValueError("check order must contain every check exactly once")
    if any(isinstance(check, (bool, np.bool_)) or not isinstance(check, numbers.Integral) for check in order):
        raise ValueError("check order must use exact integer IDs")
    normalized = tuple(int(check) for check in order)
    if set(normalized) != set(range(int(check_count))):
        raise ValueError("check order must be a permutation of canonical check IDs")
    return tuple((normalized[index], normalized[index + 1]) for index in range(len(normalized) - 1))


@dataclass(frozen=True, slots=True)
class HsuGroupPlan:
    """Purpose-separated schedule RNG, independent of physical-error sampling."""

    check_count: int
    root_identity: str

    def __post_init__(self) -> None:
        if isinstance(self.check_count, bool) or not isinstance(self.check_count, numbers.Integral) or self.check_count < 2:
            raise ValueError("Hsu groups require at least two checks")
        if not isinstance(self.root_identity, str) or len(self.root_identity) != 64 or any(ch not in "0123456789abcdef" for ch in self.root_identity):
            raise ValueError("schedule root_identity must be a lowercase SHA-256 hex digest")

    def traversal(self, *, attempt_identity: str, iteration: int) -> GroupTraversal:
        if not isinstance(attempt_identity, str) or not attempt_identity:
            raise ValueError("attempt_identity must be a nonempty string")
        if isinstance(iteration, bool) or not isinstance(iteration, numbers.Integral) or iteration < 0:
            raise ValueError("source iteration must be a nonnegative integer")
        material = {
            "purpose": "hsu_group_order",
            "source_id": SOURCE_ID,
            "root_identity": self.root_identity,
            "attempt_identity": attempt_identity,
            "iteration": int(iteration),
            "check_count": int(self.check_count),
        }
        identity = sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        generator = np.random.Generator(np.random.PCG64(int(identity[:32], 16)))
        order = tuple(int(check) for check in generator.permutation(int(self.check_count)))
        return GroupTraversal(int(iteration), order, groups_from_order(order, check_count=self.check_count), identity)


class HsuGroupSchedule:
    """Distinct overlapping-CN schedule on the canonical binary BP kernel."""

    schedule_name = "group_shuffled"
    stopping_adaptation = "D-09 checks after each group rather than after source traversal"

    def __init__(self, edge_table: EdgeTable, *, kernel: object, root_identity: str, attempt_identity: str) -> None:
        if not isinstance(edge_table, EdgeTable):
            raise ValueError("Hsu schedule requires a canonical EdgeTable")
        if not isinstance(attempt_identity, str) or not attempt_identity:
            raise ValueError("Hsu schedule requires an attempt identity")
        if getattr(kernel, "update_rule", None) is not None or getattr(kernel, "profile", None) != DEFAULT_BINARY_SPA_F64:
            raise ValueError("Hsu source-qualified groups require plain SPA with the default numerical profile")
        self.edge_table = edge_table
        self.kernel = kernel
        self.plan = HsuGroupPlan(edge_table.check_count, root_identity)
        self.attempt_identity = attempt_identity
        self._check_edges = tuple(
            tuple(index for index, (check, _) in enumerate(edge_table.edges) if check == current)
            for current in range(edge_table.check_count)
        )
        self._edge_variables = tuple(variable for _, variable in edge_table.edges)
        self._variable_edges = tuple(
            tuple(index for index, variable in enumerate(self._edge_variables) if variable == current)
            for current in range(edge_table.variable_count)
        )
        self._c2v = np.zeros(edge_table.edge_count, dtype=np.float64)
        self._traversals: list[GroupTraversal] = []

    @property
    def unit_count(self) -> int:
        return self.edge_table.check_count - 1

    def refresh_order(self, progress: object, *, budgets: object) -> tuple[bool, object | None]:
        """Reserve the RNG draw before creating a new source-iteration traversal."""
        from .budgets import WorkVector

        iteration = getattr(progress, "iteration", None)
        cursor = getattr(progress, "cursor", None)
        if isinstance(iteration, bool) or not isinstance(iteration, numbers.Integral) or iteration < 0 or cursor != (0,):
            raise ValueError("Hsu order refresh requires a source-iteration boundary")
        if len(self._traversals) > iteration:
            return True, None
        if len(self._traversals) != iteration:
            raise ValueError("Hsu traversal state does not match source iteration")
        reservation = budgets.reserve(
            "attempt",
            WorkVector(order_generation=self.edge_table.check_count),
            leaf_id=f"attempt:hsu-order:{iteration}",
        )
        if reservation is None:
            return False, budgets.last_termination
        try:
            traversal = self.plan.traversal(attempt_identity=self.attempt_identity, iteration=int(iteration))
            reservation.commit_once()
            self._traversals.append(traversal)
            return True, None
        except BaseException:
            if reservation.active:
                reservation.rollback()
            raise

    def _selected_group(self, progress: object) -> tuple[int, int]:
        iteration = getattr(progress, "iteration", None)
        cursor = getattr(progress, "cursor", None)
        if isinstance(iteration, bool) or not isinstance(iteration, numbers.Integral) or iteration != len(self._traversals) - 1:
            raise ValueError("Hsu group requires its admitted source order")
        if not isinstance(cursor, tuple) or len(cursor) != 1 or isinstance(cursor[0], bool) or not isinstance(cursor[0], numbers.Integral):
            raise ValueError("Hsu group cursor must contain one integer")
        index = int(cursor[0])
        if not 0 <= index < self.unit_count:
            raise ValueError("Hsu group cursor is outside the traversal")
        return self._traversals[iteration].groups[index]

    def _group_work(self, group: tuple[int, int]) -> object:
        from .budgets import WorkVector

        group_edges = tuple(index for check in group for index in self._check_edges[check])
        affected = {self._edge_variables[index] for index in group_edges}
        return WorkVector(
            check_to_variable_updates=len(group_edges),
            variable_to_check_updates=sum(len(self._variable_edges[variable]) for variable in affected),
            belief_assemblies=self.edge_table.variable_count,
            candidate_constructions=1,
            convergence_checks=1,
            candidate_checks=1,
            order_selection=1,
        )

    def _compute_group(self, messages: np.ndarray, syndrome: np.ndarray, *, error_rate: float, group: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        entry = finite_saturate(messages, boundary="hsu_group_entry_v2c")
        if entry.shape != (self.edge_table.edge_count,):
            raise ValueError("Hsu messages must have one value per canonical edge")
        snapshot = np.array(entry, dtype=np.float64, copy=True)
        next_c2v = np.array(self._c2v, dtype=np.float64, copy=True)
        group_edges: list[int] = []
        for check in group:
            indices = self._check_edges[check]
            for edge_index in indices:
                incoming = snapshot[[other for other in indices if other != edge_index]]
                next_c2v[edge_index] = self.kernel.check_message(incoming, int(syndrome[check]))
                group_edges.append(edge_index)
        next_c2v = finite_saturate(next_c2v, boundary="hsu_group_complete_c2v")
        beliefs = self.kernel.assemble_beliefs(
            self.edge_table.variable_count, self._edge_variables, next_c2v, self.kernel.prior(error_rate),
        )
        candidate = np.array(self.kernel.candidate_from_beliefs(beliefs), dtype=np.uint8, copy=True)
        updated = np.array(snapshot, dtype=np.float64, copy=True)
        affected = {self._edge_variables[index] for index in group_edges}
        for variable in affected:
            for edge_index in self._variable_edges[variable]:
                updated[edge_index] = self.kernel.variable_message(float(beliefs[variable]), float(next_c2v[edge_index]))
        return finite_saturate(updated, boundary="hsu_group_complete_v2c"), candidate, next_c2v

    def execute_local_step(
        self, executor: object, messages: np.ndarray, syndrome: np.ndarray, *,
        error_rate: float, progress: object, is_converged: object,
    ) -> ScheduledLocalStepResult:
        from .execution import LocalStepProposal, ScheduleProgress

        group = self._selected_group(progress)
        bits = _binary_syndrome(self.edge_table, syndrome)
        work = self._group_work(group)
        candidate_box: list[np.ndarray] = []
        c2v_box: list[np.ndarray] = []

        def compute() -> np.ndarray:
            updated, candidate, c2v = self._compute_group(messages, bits, error_rate=error_rate, group=group)
            candidate_box.append(candidate)
            c2v_box.append(c2v)
            return updated

        result = executor.execute(
            LocalStepProposal(f"hsu-group:{progress.iteration}:{progress.cursor[0]}", work, compute),
            messages=messages, progress=progress, policy_state={}, cache={},
            is_converged=lambda _messages: bool(candidate_box and is_converged(candidate_box[-1])),
        )
        if not result.admitted:
            return ScheduledLocalStepResult(False, progress, None, work, result.termination)
        self._c2v[...] = c2v_box[-1]
        next_progress = ScheduleProgress(progress.iteration, result.progress.local_steps, (progress.cursor[0] + 1,), progress.rng_state)
        return ScheduledLocalStepResult(True, next_progress, candidate_box[-1], work)

    def evidence(self) -> dict[str, object]:
        return {
            "schedule": self.schedule_name,
            "atomic_unit": "one_overlapping_check_group",
            "source_id": SOURCE_ID,
            "source_uri": SOURCE_URI,
            "source_configuration": "group_size=2;overlap=1",
            "root_identity": self.plan.root_identity,
            "attempt_identity": self.attempt_identity,
            "rng_algorithm": "numpy.PCG64",
            "numpy_version": np.__version__,
            "traversals": tuple(traversal.evidence() for traversal in self._traversals),
            "graph_sha256": self.edge_table.graph_sha256,
            "stopping_adaptation": self.stopping_adaptation,
        }
