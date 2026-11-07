"""Closed, source-defined schedule policies for scalar LLR-BP4.

Only the schedules whose four-state freshness semantics have been qualified live
here.  The similarly named binary schedules remain outside this module because
their update units and state ownership do not establish quaternary compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math

import numpy as np

from .algebra import Pauli
from .kernel import QbpSession, QbpSweep
from .numerics import commutation_llr, llrs_to_probabilities
from .problems import QuaternaryOriginalProblem


QuaternaryEdge = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class QuaternaryCheckTransform:
    """One source-backed transform of a scalar commutation C2V message only."""

    kind: str
    parameter: float

    def __post_init__(self) -> None:
        if self.kind not in {"qbp_c2v_normalization", "qbp_c2v_offset"}:
            raise ValueError("unsupported quaternary C2V transform; binary update names are not admitted")
        if isinstance(self.parameter, bool) or not isinstance(self.parameter, (int, float, np.integer, np.floating)):
            raise ValueError("quaternary C2V transform parameter must be finite and positive")
        parameter = float(self.parameter)
        if not math.isfinite(parameter) or parameter <= 0.0:
            raise ValueError("quaternary C2V transform parameter must be finite and positive")
        object.__setattr__(self, "parameter", parameter)

    @classmethod
    def normalization(cls, alpha_c: object) -> "QuaternaryCheckTransform":
        return cls("qbp_c2v_normalization", alpha_c)

    @classmethod
    def offset(cls, beta: object) -> "QuaternaryCheckTransform":
        return cls("qbp_c2v_offset", beta)

    @property
    def equation_identity(self) -> str:
        return "lai-kuo-2021-c2v-divide-alpha-c" if self.kind == "qbp_c2v_normalization" else "lai-kuo-2021-c2v-signed-offset-beta"

    @property
    def application_point(self) -> str:
        return "scalar_commutation_c2v_after_check_reduction_before_variable_assembly"

    def apply(self, message: object) -> float:
        if isinstance(message, bool) or not isinstance(message, (int, float, np.integer, np.floating)):
            raise ValueError("quaternary C2V transforms require one scalar commutation check message")
        value = float(message)
        if not math.isfinite(value):
            raise ValueError("quaternary C2V transforms require a finite scalar commutation check message")
        if self.kind == "qbp_c2v_normalization":
            return value / self.parameter
        return math.copysign(max(0.0, abs(value) - self.parameter), value)

    def as_evidence(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "parameter": self.parameter,
            "equation_identity": self.equation_identity,
            "application_point": self.application_point,
        }


def _transforms(value: tuple[QuaternaryCheckTransform, ...] | list[QuaternaryCheckTransform] | None) -> tuple[QuaternaryCheckTransform, ...]:
    result = () if value is None else tuple(value)
    if any(not isinstance(transform, QuaternaryCheckTransform) for transform in result):
        raise ValueError("quaternary schedule transforms must be declared QuaternaryCheckTransform values")
    return result


def _apply_transforms(message: float, transforms: tuple[QuaternaryCheckTransform, ...]) -> float:
    result = message
    for transform in transforms:
        result = transform.apply(result)
    return result


@dataclass(frozen=True, slots=True)
class QuaternaryEdgeTable:
    """Stable check-major Pauli-labelled graph identity for one BP4 problem."""

    check_count: int
    variable_count: int
    edges: tuple[QuaternaryEdge, ...]

    def __post_init__(self) -> None:
        if type(self.check_count) is not int or type(self.variable_count) is not int:
            raise ValueError("quaternary edge-table counts must be integers")
        if self.check_count < 0 or self.variable_count < 0:
            raise ValueError("quaternary edge-table counts must be nonnegative")
        expected = tuple(sorted(self.edges))
        if self.edges != expected or len(set(self.edges)) != len(self.edges):
            raise ValueError("quaternary edges must be unique and check-major ordered")
        for check, variable, label in self.edges:
            if not 0 <= check < self.check_count or not 0 <= variable < self.variable_count:
                raise ValueError("quaternary edge is outside the declared graph")
            if label not in (int(Pauli.X), int(Pauli.Y), int(Pauli.Z)):
                raise ValueError("quaternary edges require a nonidentity Pauli label")

    @classmethod
    def from_problem(cls, problem: QuaternaryOriginalProblem) -> "QuaternaryEdgeTable":
        if not isinstance(problem, QuaternaryOriginalProblem):
            raise ValueError("quaternary edge tables require an immutable original problem")
        rows, columns = np.nonzero(problem.code.checks != Pauli.I)
        edges = tuple(sorted((int(row), int(column), int(problem.code.checks[row, column])) for row, column in zip(rows, columns, strict=True)))
        return cls(problem.code.checks.shape[0], problem.code.n, edges)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def graph_sha256(self) -> str:
        payload = {
            "check_count": self.check_count,
            "variable_count": self.variable_count,
            "edges": self.edges,
            "pauli_order": "I,X,Y,Z",
        }
        return sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class QuaternaryScheduleSweep:
    """One committed source-schedule pass with explicit freshness evidence."""

    schedule_kind: str
    iteration_meaning: str
    node_order: tuple[int, ...]
    edge_order: tuple[QuaternaryEdge, ...]
    snapshot_boundary: str
    commit_boundary: str
    result: QbpSweep
    transform_order: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schedule_kind not in {"qbp_flooding", "qbp_variable_serial"}:
            raise ValueError("unsupported quaternary schedule kind")
        if not self.iteration_meaning or not self.snapshot_boundary or not self.commit_boundary:
            raise ValueError("quaternary schedule evidence must describe its boundaries")
        if not isinstance(self.result, QbpSweep):
            raise ValueError("quaternary schedule evidence requires a QbpSweep")
        if any(not item for item in self.transform_order):
            raise ValueError("quaternary schedule transform order must contain equation identities")


class QbpFloodingSchedule:
    """Parallel BP4: one complete old V2C snapshot then one complete commit."""

    def __init__(self, session: QbpSession, *, transforms: tuple[QuaternaryCheckTransform, ...] | list[QuaternaryCheckTransform] | None = None) -> None:
        if not isinstance(session, QbpSession):
            raise ValueError("qbp flooding requires a QbpSession")
        self.session = session
        self.edge_table = QuaternaryEdgeTable.from_problem(session.problem)
        self.transforms = _transforms(transforms)

    def sweep(self) -> QuaternaryScheduleSweep:
        result = self.session.sweep() if not self.transforms else self._transformed_sweep()
        return QuaternaryScheduleSweep(
            schedule_kind="qbp_flooding",
            iteration_meaning="one complete parallel C2V/belief/V2C pass",
            node_order=tuple(range(self.edge_table.variable_count)),
            edge_order=self.edge_table.edges,
            snapshot_boundary="read one complete old V2C buffer before any C2V computation",
            commit_boundary="commit complete C2V, beliefs, candidate, and V2C buffers together",
            result=result,
            transform_order=tuple(transform.equation_identity for transform in self.transforms),
        )

    def _transformed_sweep(self) -> QbpSweep:
        # One engine owns reservation, snapshot, beliefs, damping and commit.
        # A transform changes only the explicitly declared C2V stage.
        return self.session.sweep(_check_transform=lambda message: _apply_transforms(message, self.transforms))


class QbpVariableSerialSchedule:
    """Source variable-node serial BP4 with a persisted original-qubit order.

    A pass calculates a variable's incident C2V values from the current V2C
    buffer, then immediately makes that variable's V2C update available to all
    later variables.  Local arrays make the pass atomic if arithmetic fails.
    """

    def __init__(self, session: QbpSession, *, variable_order: tuple[int, ...] | list[int] | None = None,
                 transforms: tuple[QuaternaryCheckTransform, ...] | list[QuaternaryCheckTransform] | None = None) -> None:
        if not isinstance(session, QbpSession):
            raise ValueError("qbp variable serial requires a QbpSession")
        self.session = session
        self.edge_table = QuaternaryEdgeTable.from_problem(session.problem)
        self.transforms = _transforms(transforms)
        order = tuple(range(self.edge_table.variable_count)) if variable_order is None else tuple(variable_order)
        if (
            len(order) != self.edge_table.variable_count
            or set(order) != set(range(self.edge_table.variable_count))
            or any(type(variable) is not int for variable in order)
        ):
            raise ValueError("variable serial order must be a permutation of original qubit indices")
        self.variable_order = order

    def sweep(self) -> QuaternaryScheduleSweep:
        session = self.session
        if session._terminal != "running":
            return self._evidence(session.last)
        next_iteration = session._iteration + 1
        work = session._sweep_work()
        reservation = session.budgets.reserve(
            session.budget_scope, work, leaf_id=f"qbp-serial:{session.problem.lineage_id}:{next_iteration}"
        )
        if reservation is None:
            session._terminal = "capped"
            session._last = session._snapshot(converged=False, terminal="capped", work=session.budgets.summary(session.budget_scope))
            return self._evidence(session.last)
        try:
            c2v = session._c2v.copy()
            v2c = session._v2c.copy()
            beliefs = session._beliefs.copy()
            for variable in self.variable_order:
                incident = session._variable_incident[variable]
                for edge in incident:
                    check = int(session._checks[edge])
                    reduced = [
                        commutation_llr(
                            v2c[index], int(session._labels[index]), profile=session.kernel.profile
                        )
                        for index in session._check_incident[check]
                        if index != edge
                    ]
                    c2v[edge] = _apply_transforms(
                        session.kernel.check_message(reduced, int(session.problem.syndrome[check])), self.transforms
                    )
                beliefs[variable] = session.kernel.posterior(
                    session.priors[variable], c2v[list(incident)], session._labels[list(incident)]
                )
                for edge in incident:
                    proposal = session.kernel.variable_message(
                        beliefs[variable], c2v[edge], int(session._labels[edge])
                    )
                    v2c[edge] = session.kernel.damp_variable_messages(v2c[edge], proposal)
            marginals = np.asarray([llrs_to_probabilities(row, profile=session.kernel.profile) for row in beliefs])
            candidate = session.kernel.candidate_from_beliefs(beliefs)
        except Exception:
            reservation.rollback()
            session._terminal = "numerical_failure"
            session._last = session._snapshot(converged=False, terminal="numerical_failure", work=session.budgets.summary(session.budget_scope))
            raise
        reservation.commit_once()
        session._iteration = next_iteration
        session._c2v = c2v
        session._v2c = v2c
        session._beliefs = beliefs
        session._marginals = marginals
        session._candidate = candidate
        converged = session._is_converged()
        session._terminal = "converged" if converged else "running"
        session._last = session._snapshot(
            converged=converged, terminal=session._terminal, work=session.budgets.summary(session.budget_scope)
        )
        return self._evidence(session.last)

    def _evidence(self, result: QbpSweep) -> QuaternaryScheduleSweep:
        return QuaternaryScheduleSweep(
            schedule_kind="qbp_variable_serial",
            iteration_meaning="one ordered pass over every original qubit",
            node_order=self.variable_order,
            edge_order=self.edge_table.edges,
            snapshot_boundary="each variable reads the current V2C buffer at its declared turn",
            commit_boundary="each variable commits its incident V2C updates before the next variable",
            result=result,
            transform_order=tuple(transform.equation_identity for transform in self.transforms),
        )


__all__ = ["QbpFloodingSchedule", "QbpVariableSerialSchedule", "QuaternaryCheckTransform", "QuaternaryEdgeTable", "QuaternaryScheduleSweep"]
