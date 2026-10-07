"""Contracts for the source-defined fixed-alpha MBP4 recurrence."""

from __future__ import annotations

import importlib
import importlib.util

import numpy as np
import pytest

from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
from bp_registry.quaternary.algebra import Pauli
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem


def _module():
    # Make the initial RED phase an assertion failure rather than collection failure.
    assert importlib.util.find_spec("bp_registry.quaternary.mbp4") is not None
    return importlib.import_module("bp_registry.quaternary.mbp4")


def _problem() -> QuaternaryOriginalProblem:
    code = PauliCode(checks=np.asarray(((Pauli.X, Pauli.Z), (Pauli.Z, Pauli.X)), dtype=np.uint8))
    return QuaternaryOriginalProblem(
        lineage_id="original-mbp4-fixture",
        code=code,
        syndrome=code.syndrome(np.asarray((Pauli.Y, Pauli.I), dtype=np.uint8)),
    )


def _priors() -> np.ndarray:
    return np.asarray(((0.70, 0.10, 0.15, 0.05), (0.55, 0.20, 0.05, 0.20)), dtype=np.float64)


def test_fixed_alpha_mbp4_posterior_scales_anticommuting_sum_but_not_destination_inhibition() -> None:
    module = _module()
    kernel = module.FixedAlphaMbp4Kernel(module.Mbp4Spec(alpha=0.5, schedule="qbp_flooding"))
    prior = np.asarray((0.70, 0.10, 0.15, 0.05), dtype=np.float64)
    messages = np.asarray((1.25, -0.50), dtype=np.float64)
    labels = np.asarray((Pauli.X, Pauli.Z), dtype=np.uint8)

    posterior = kernel.posterior(prior, messages, labels)
    ordinary = ScalarLlrBp4Kernel().posterior(prior, messages, labels)
    outgoing = kernel.variable_message(posterior, messages[0], Pauli.X)

    # alpha=1/2 doubles every posterior anticommuting contribution.
    assert posterior.tolist() == pytest.approx((
        ScalarLlrBp4Kernel().prior_llrs(prior)[0] - 1.0,
        ScalarLlrBp4Kernel().prior_llrs(prior)[1] + 1.5,
        ScalarLlrBp4Kernel().prior_llrs(prior)[2] + 2.5,
    ))
    assert not np.allclose(posterior, ordinary)
    # MBP4 Eq. (18) inhibits the destination edge by the original Delta,
    # whereas normalized BP4 would subtract Delta / alpha.
    assert outgoing.tolist() == pytest.approx((posterior[0], posterior[1] - 1.25, posterior[2] - 1.25))


def test_fixed_alpha_mbp4_alpha_one_reduces_to_plain_bp_and_differs_from_normalized_bp4() -> None:
    module = _module()
    prior = np.asarray((0.70, 0.10, 0.15, 0.05), dtype=np.float64)
    messages = np.asarray((1.25, -0.50), dtype=np.float64)
    labels = np.asarray((Pauli.X, Pauli.Z), dtype=np.uint8)
    ordinary = ScalarLlrBp4Kernel()
    alpha_one = module.FixedAlphaMbp4Kernel(module.Mbp4Spec(alpha=1.0, schedule="qbp_flooding"))
    half = module.FixedAlphaMbp4Kernel(module.Mbp4Spec(alpha=0.5, schedule="qbp_flooding"))

    assert np.allclose(alpha_one.posterior(prior, messages, labels), ordinary.posterior(prior, messages, labels))
    mbp_outgoing = half.variable_message(half.posterior(prior, messages, labels), messages[0], Pauli.X)
    normalized_outgoing = half.normalized_variable_message(half.posterior(prior, messages, labels), messages[0], Pauli.X)
    assert not np.allclose(mbp_outgoing, normalized_outgoing)


@pytest.mark.parametrize("schedule", ("qbp_flooding", "qbp_variable_serial"))
def test_fixed_alpha_mbp4_runs_source_qualified_flooding_or_serial_with_work_and_replay(schedule: str) -> None:
    module = _module()
    spec = module.Mbp4Spec(alpha=0.75, schedule=schedule, max_iterations=2)
    session = module.FixedAlphaMbp4Kernel(spec).new_session(_problem(), _priors())
    result = session.run()

    assert result.spec.alpha == pytest.approx(0.75)
    assert result.spec.schedule == schedule
    assert result.equation_identity == "kuo-lai-2023-mbp4-fixed-inhibition-eq15-18"
    assert result.schedule_freshness
    assert result.initial_state_digest != result.state_digest
    assert result.work.bp_calls >= 1
    module.reconstruct_mbp4(spec, _problem(), _priors(), result)


def test_fixed_alpha_mbp4_rejects_invalid_alpha_schedules_adaptive_search_and_binary_memory() -> None:
    module = _module()
    for alpha in (0.0, -1.0, np.inf, np.nan, True):
        with pytest.raises(ValueError, match="alpha"):
            module.Mbp4Spec(alpha=alpha, schedule="qbp_flooding")
    for schedule in ("layered", "binary_serial", "memory"):
        with pytest.raises(ValueError, match="schedule"):
            module.Mbp4Spec(alpha=0.7, schedule=schedule)
    with pytest.raises(ValueError, match="AMBP4|adaptive"):
        module.Mbp4Spec(alpha=0.7, schedule="qbp_flooding", algorithm="ambp4")
    with pytest.raises(ValueError, match="alpha search|fixed alpha"):
        module.Mbp4Spec(alpha=(1.0, 0.8), schedule="qbp_flooding")
    with pytest.raises(ValueError, match="work cap"):
        module.FixedAlphaMbp4Kernel(module.Mbp4Spec(alpha=0.7, schedule="qbp_flooding", max_iterations=1)).new_session(
            _problem(), _priors(), budgets=BudgetTree(limits=(BudgetLimit("attempt", "bp_calls", 0),), parents={})
        ).run()
