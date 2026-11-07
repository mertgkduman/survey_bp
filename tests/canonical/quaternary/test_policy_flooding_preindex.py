"""Check exact policy reductions after graph and flooding quantization reuse."""

from __future__ import annotations

import numpy as np

from bp_registry.quaternary.algebra import Pauli
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.mbp4 import FixedAlphaMbp4Kernel, Mbp4Spec, reconstruct_mbp4
from bp_registry.quaternary.numerics import commutation_llr
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem
from bp_registry.quaternary.schedules import QbpFloodingSchedule, QuaternaryCheckTransform


def _fixture() -> tuple[QuaternaryOriginalProblem, np.ndarray]:
    code = PauliCode(checks=np.asarray([
        [Pauli.X, Pauli.Y, Pauli.Z, Pauli.I, Pauli.I],
        [Pauli.I, Pauli.Y, Pauli.I, Pauli.X, Pauli.I],
        [Pauli.X, Pauli.I, Pauli.Z, Pauli.X, Pauli.I],
    ], dtype=np.uint8))
    error = np.asarray([Pauli.Y, Pauli.I, Pauli.Z, Pauli.I, Pauli.I], dtype=np.uint8)
    problem = QuaternaryOriginalProblem("original-policy-incidence", code, code.syndrome(error))
    priors = np.tile([.83, .07, .06, .04], (code.n, 1))
    return problem, priors


def test_transformed_flooding_uses_each_old_edge_once_with_exact_exclusion(monkeypatch) -> None:
    import bp_registry.quaternary.kernel as engine

    problem, priors = _fixture()
    session = ScalarLlrBp4Kernel().new_session(problem, priors)
    transforms = (QuaternaryCheckTransform.normalization(1.5), QuaternaryCheckTransform.offset(.1))
    expected = []
    for edge, check in enumerate(session._checks):
        reduced = [
            commutation_llr(session._v2c[other], int(session._labels[other]), profile=session.kernel.profile)
            for other in np.flatnonzero(session._checks == check) if other != edge
        ]
        value = session.kernel.check_message(reduced, int(problem.syndrome[check]))
        for transform in transforms:
            value = transform.apply(value)
        expected.append(value)
    calls = 0
    original = engine.commutation_llr

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(engine, "commutation_llr", counted)
    result = QbpFloodingSchedule(session, transforms=transforms).sweep().result
    np.testing.assert_array_equal(result.c2v, expected)
    assert calls == len(session._labels)
    assert result.work.check_to_variable_updates == len(session._labels)


def test_mbp4_flooding_reuses_quantization_and_preserves_replay(monkeypatch) -> None:
    problem, priors = _fixture()
    spec = Mbp4Spec(alpha=1.5, schedule="qbp_flooding", max_iterations=2)
    session = FixedAlphaMbp4Kernel(spec).new_session(problem, priors)
    expected = []
    for edge, check in enumerate(session._checks):
        reduced = [
            session.scalar_commutation(session._v2c[other], int(session._labels[other]))
            for other in np.flatnonzero(session._checks == check) if other != edge
        ]
        expected.append(session.kernel.check_message(reduced, int(problem.syndrome[check])))
    calls = 0
    original = session.scalar_commutation

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(session, "scalar_commutation", counted)
    first = session.sweep()
    np.testing.assert_array_equal(first.c2v, expected)
    assert calls == len(session._labels)
    assert first.work.check_to_variable_updates == len(session._labels)
    result = session.run()
    reconstruct_mbp4(spec, problem, priors, result)
