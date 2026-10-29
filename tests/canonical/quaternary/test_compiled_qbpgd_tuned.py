"""Persistent compiled Q-BPGD matches the canonical controller's round order."""

from dataclasses import replace

import numpy as np
import pytest

from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem
from bp_registry.quaternary.qbpgd import QbpgdController, QbpgdSpec, ScalarLlrBp4Kernel, reconstruct_qbpgd


@pytest.mark.parametrize("damping", [0.0, 0.2])
@pytest.mark.parametrize("round_limit", [1, 2])
def test_compiled_v2_qbpgd_matches_controller(damping: float, round_limit: int) -> None:
    code = PauliCode(checks=np.asarray(((3, 3),), dtype=np.uint8))
    syndrome = np.asarray((1,), dtype=np.uint8)
    priors = np.asarray(((0.7, 0.1, 0.1, 0.1), (0.7, 0.1, 0.1, 0.1)), dtype=np.float64)
    profile = replace(QBP4_F64_V2, v2c_damping=damping)
    problem = QuaternaryOriginalProblem(
        lineage_id="original-compiled-qbpgd-parity", code=code, syndrome=syndrome,
    )
    spec = QbpgdSpec(iterations_per_round=2, epsilon=1e-10, round_limit=round_limit)
    expected = QbpgdController(spec).run(ScalarLlrBp4Kernel(profile=profile).new_session(problem, priors))
    actual = CompiledBp4Graph.from_code(code, priors, profile=profile).run_qbpgd(
        syndrome, iterations_per_round=2, epsilon=1e-10, round_limit=round_limit,
    )
    assert tuple(actual.candidate) == expected.candidate
    assert actual.iterations == expected.work.bp_calls
    assert actual.rounds == len(expected.rounds)
    assert actual.fixations == expected.work.fixation_actions
    assert actual.converged == (expected.termination == "early_success")
    reconstruct_qbpgd(spec, problem, priors, expected, profile=profile)
    if damping:
        with pytest.raises(ValueError, match="replay"):
            reconstruct_qbpgd(spec, problem, priors, expected)
