"""Contracts for source-defined scalar BP4 schedule policies."""

from __future__ import annotations

import importlib.util

import numpy as np

from bp_registry.quaternary.algebra import Pauli
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem
from bp_registry.quaternary.schedules import QbpFloodingSchedule, QbpVariableSerialSchedule, QuaternaryEdgeTable


def test_quaternary_source_schedule_module_is_available() -> None:
    """D-07 requires a dedicated schedule surface, never binary-name reuse."""
    assert importlib.util.find_spec("bp_registry.quaternary.schedules") is not None


def test_quaternary_check_transform_contract_is_available() -> None:
    """D-07 exposes dedicated scalar-C2V normalization and offset policies."""
    module = importlib.import_module("bp_registry.quaternary.schedules")
    assert hasattr(module, "QuaternaryCheckTransform")


def _problem(checks: object, error: object, *, lineage: str = "original-qbp-schedule") -> QuaternaryOriginalProblem:
    code = PauliCode(checks=np.asarray(checks, dtype=np.uint8))
    return QuaternaryOriginalProblem(
        lineage_id=lineage,
        code=code,
        syndrome=code.syndrome(np.asarray(error, dtype=np.uint8)),
    )


def _priors(n: int) -> np.ndarray:
    return np.tile(np.asarray((0.70, 0.10, 0.15, 0.05), dtype=np.float64), (n, 1))


def test_quaternary_edge_identity_includes_pauli_labels_and_check_major_order() -> None:
    problem = _problem(((Pauli.Z, Pauli.X), (Pauli.X, Pauli.Z)), (Pauli.I, Pauli.I))
    table = QuaternaryEdgeTable.from_problem(problem)
    assert table.edges == ((0, 0, Pauli.Z), (0, 1, Pauli.X), (1, 0, Pauli.X), (1, 1, Pauli.Z))
    relabelled = _problem(((Pauli.Z, Pauli.X), (Pauli.Y, Pauli.Y)), (Pauli.I, Pauli.I))
    assert table.graph_sha256 != QuaternaryEdgeTable.from_problem(relabelled).graph_sha256


def test_flooding_uses_one_old_snapshot_then_commits_complete_new_buffers_and_work() -> None:
    problem = _problem(((Pauli.X, Pauli.Z),), (Pauli.Y, Pauli.I))
    session = ScalarLlrBp4Kernel().new_session(problem, _priors(problem.code.n))
    old_v2c = session.last.v2c.copy()
    trace = QbpFloodingSchedule(session).sweep()
    assert np.array_equal(old_v2c, np.vstack((session.kernel.prior_llrs(_priors(problem.code.n)[0]),) * 2))
    assert trace.schedule_kind == "qbp_flooding"
    assert trace.snapshot_boundary.startswith("read one complete old V2C")
    assert trace.commit_boundary.startswith("commit complete")
    assert trace.result.work.check_to_variable_updates == 2
    assert trace.result.work.variable_to_check_updates == 2
    assert trace.result.work.belief_assemblies == 2
    assert trace.result.work.bp_calls == 1


def test_variable_serial_makes_earlier_commits_visible_to_later_variables() -> None:
    problem = _problem(((Pauli.X, Pauli.X, Pauli.I), (Pauli.X, Pauli.I, Pauli.X)), (Pauli.Y, Pauli.I, Pauli.I))
    flooding = QbpFloodingSchedule(ScalarLlrBp4Kernel().new_session(problem, _priors(problem.code.n))).sweep()
    serial = QbpVariableSerialSchedule(ScalarLlrBp4Kernel().new_session(problem, _priors(problem.code.n))).sweep()
    assert serial.schedule_kind == "qbp_variable_serial"
    assert serial.node_order == (0, 1, 2)
    assert serial.commit_boundary.endswith("before the next variable")
    assert serial.result.c2v[1] != flooding.result.c2v[1]
    assert serial.result.work == flooding.result.work


def test_source_five_qubit_iiiyi_fixture_retains_schedule_sensitive_trace() -> None:
    checks = (
        (Pauli.X, Pauli.Z, Pauli.Z, Pauli.X, Pauli.I),
        (Pauli.I, Pauli.X, Pauli.Z, Pauli.Z, Pauli.X),
        (Pauli.X, Pauli.I, Pauli.X, Pauli.Z, Pauli.Z),
        (Pauli.Z, Pauli.X, Pauli.I, Pauli.X, Pauli.Z),
    )
    problem = _problem(checks, (Pauli.I, Pauli.I, Pauli.I, Pauli.Y, Pauli.I), lineage="original-qbp-iiiyi")
    priors = np.tile(np.asarray((0.90, 1.0 / 30.0, 1.0 / 30.0, 1.0 / 30.0)), (5, 1))
    flooding = QbpFloodingSchedule(ScalarLlrBp4Kernel().new_session(problem, priors))
    serial = QbpVariableSerialSchedule(ScalarLlrBp4Kernel().new_session(problem, priors))
    flood_trace = flooding.sweep()
    serial_trace = serial.sweep()
    assert flood_trace.result.c2v.shape == serial_trace.result.c2v.shape == (16,)
    assert not np.allclose(flood_trace.result.v2c, serial_trace.result.v2c)
    assert flood_trace.edge_order == serial_trace.edge_order
    flood_candidates = []
    for _ in range(3):
        candidate = flooding.sweep().result.candidate
        flood_candidates.append("".join("IXYZ"[int(value)] for value in candidate))
    serial_second = serial.sweep()
    serial_third = serial.sweep()
    assert flood_candidates == ["IIIII", "YYYYY", "IIIII"]
    assert serial_second.result.converged is False
    assert "".join("IXYZ"[int(value)] for value in serial_third.result.candidate) == "IIIYI"
    assert serial_third.result.converged is True
