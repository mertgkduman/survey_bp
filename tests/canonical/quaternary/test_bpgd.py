"""Replayable four-state guided-decimation contracts."""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import replace

import numpy as np
import pytest

from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem
from bp_registry.quaternary.numerics import QBP4_F64_V1


def _problem() -> QuaternaryOriginalProblem:
    return QuaternaryOriginalProblem(
        lineage_id="original-qbpgd-fixture",
        code=PauliCode(checks=np.asarray(((1, 3),), dtype=np.uint8)),
        syndrome=np.asarray((0,), dtype=np.uint8),
    )


def _module():
    # Keeping the import in the test body makes the first RED run an assertion
    # failure rather than a collection error while the production module is absent.
    assert importlib.util.find_spec("bp_registry.quaternary.qbpgd") is not None
    return importlib.import_module("bp_registry.quaternary.qbpgd")


def _run(*, epsilon: float = 0.01, rounds: int = 2, budget: BudgetTree | None = None):
    module = _module()
    kernel = module.ScalarLlrBp4Kernel(profile=QBP4_F64_V1)
    priors = np.asarray(((0.25, 0.25, 0.25, 0.25), (0.25, 0.25, 0.25, 0.25)), dtype=np.float64)
    session = kernel.new_session(_problem(), priors, budgets=BudgetTree(limits=(), parents={}) if budget is None else budget)
    spec = module.QbpgdSpec(iterations_per_round=1, epsilon=epsilon, round_limit=rounds)
    return module, spec, priors, module.QbpgdController(spec).run(session)


def test_qbpgd_reliability_uses_four_state_marginals_with_stable_qubit_and_pauli_ties() -> None:
    module = _module()
    target, pauli, reliability, targets, paulis = module.select_qbpgd_target(
        np.asarray(((0.25, 0.25, 0.25, 0.25), (0.10, 0.80, 0.05, 0.05)), dtype=np.float64),
        eligibility=(0, 1),
    )
    assert target == 1
    assert pauli == 1
    assert reliability == pytest.approx(0.80)
    assert targets == (1,)
    assert paulis == (1,)
    target, pauli, _, targets, paulis = module.select_qbpgd_target(
        np.full((2, 4), 0.25, dtype=np.float64), eligibility=(0, 1),
    )
    assert (target, pauli, targets, paulis) == (0, 0, (0, 1), (0, 1, 2, 3))


def test_qbpgd_raw_literal_fixation_normalizes_only_by_common_sum_and_continues_messages() -> None:
    module, spec, priors, result = _run(epsilon=0.01)
    assert result.run_fidelity == "canonical_adaptation"
    assert result.component_fidelity["depolarizing_setup"] == "source_backed"
    assert result.source_author_code_identity == "unverified"
    assert result.interpretation_ids["continued_messages"] == "D-14"
    assert len(result.rounds) == 2
    first = result.rounds[0]
    assert first.raw_prior is not None and first.resolved_prior is not None
    expected_raw = np.asarray((1.0 - spec.epsilon, spec.epsilon, spec.epsilon, spec.epsilon))
    expected_raw = np.roll(expected_raw, first.selected_pauli)
    assert np.allclose(first.raw_prior, expected_raw)
    assert np.allclose(first.resolved_prior, expected_raw / expected_raw.sum())
    assert first.message_digest_after == result.rounds[1].message_digest_before
    assert first.eligibility_set == (0, 1)
    assert result.work.fixation_actions == len([round_ for round_ in result.rounds if round_.selected_target is not None])
    module.reconstruct_qbpgd(spec, _problem(), priors, result)


def test_qbpgd_replay_rejects_changed_transition_and_work_and_never_accepts_truth() -> None:
    module, spec, priors, result = _run()
    altered = replace(result, termination="early_success" if result.termination != "early_success" else "round_cap_reached")
    with pytest.raises(ValueError, match="replay"):
        module.reconstruct_qbpgd(spec, _problem(), priors, altered)
    limited = BudgetTree(limits=(BudgetLimit("attempt", "bp_calls", 0),), parents={})
    _, _, _, capped = _run(budget=limited)
    assert capped.termination == "work_cap"
    assert capped.work.bp_calls == 0
    assert "truth" not in str(__import__("inspect").signature(module.QbpgdController.run))
