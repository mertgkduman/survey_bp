"""Numerical and source-equation contracts for the canonical scalar BP4 kernel."""

from __future__ import annotations

import importlib.util
from hashlib import sha256
from pathlib import Path
import numpy as np
import pytest

from bp_registry.quaternary.algebra import anticommutes
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import (
    QBP4_F64_V1,
    QBP4_F64_V2,
    QuaternaryNumericalFailure,
    check_message,
    commutation_llr,
    llrs_to_probabilities,
    ordered_boxplus,
    pauli_hard_decision,
    probabilities_to_llrs,
)
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem
from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.problems import compile_css_artifact
from bp_registry.canonical.budgets import BudgetLimit, BudgetTree

from .test_vector_oracle import exact_one_check, vector_bp4_one_check


def test_scalar_llr_bp4_kernel_is_available() -> None:
    """QBP-01 needs a production-owned scalar LLR-BP4 session, not an adapter."""
    assert importlib.util.find_spec("bp_registry.quaternary.kernel") is not None, (
        "bp_registry.quaternary.kernel is absent"
    )


def test_numerics_profile_persists_complete_binding_contract() -> None:
    evidence = QBP4_F64_V1.as_evidence()
    assert evidence["profile_id"] == "quaternary-bp4-f64-v1"
    assert evidence["saturation"] == 25.0
    assert evidence["saturation_boundary"] == "symmetric_after_every_public_message_or_belief_primitive"
    assert evidence["oracle_gate"] == "vector_and_exact_tree_fixtures_required_before_public_manifest"


def test_v2_default_keeps_large_beliefs_and_preserves_v1_evidence() -> None:
    assert ScalarLlrBp4Kernel().profile is QBP4_F64_V2
    assert QBP4_F64_V1.as_evidence()["profile_id"] == "quaternary-bp4-f64-v1"
    prior = np.asarray((1.0 - 3e-14, 1e-14, 1e-14, 1e-14))
    assert probabilities_to_llrs(prior, profile=QBP4_F64_V2).min() > 25.0
    assert probabilities_to_llrs(prior, profile=QBP4_F64_V1).max() == 25.0
    assert check_message(np.asarray((100.0,)), syndrome=0, profile=QBP4_F64_V2) == pytest.approx(23.718998, abs=1e-5)
    assert check_message(np.asarray((30.0,)), syndrome=0, profile=QBP4_F64_V2) > 25.0
    assert pauli_hard_decision(np.asarray((-1., 0., -1.)), profile=QBP4_F64_V2).name == "Y"
    assert pauli_hard_decision(np.asarray((-1., 0., -1.)), profile=QBP4_F64_V1).name == "X"


def test_commutation_llr_matches_direct_four_state_mass_ratio() -> None:
    probabilities = np.asarray((0.40, 0.10, 0.35, 0.15), dtype=np.float64)
    llrs = probabilities_to_llrs(probabilities)
    for label in (1, 2, 3):
        anticommute = np.asarray(anticommutes(np.full(4, label, dtype=np.uint8), np.arange(4, dtype=np.uint8)), dtype=bool)
        expected = np.log(probabilities[~anticommute].sum()) - np.log(probabilities[anticommute].sum())
        assert commutation_llr(llrs, label) == pytest.approx(expected)


def test_logsum_and_boxplus_are_ordered_finite_and_symmetrically_clipped() -> None:
    assert ordered_boxplus(np.asarray((), dtype=np.float64), profile=QBP4_F64_V1) == 25.0
    assert check_message(np.asarray((100.0,), dtype=np.float64), syndrome=1, profile=QBP4_F64_V1) == -25.0
    assert -25.0 <= ordered_boxplus(np.asarray((4.0, -3.0, 2.0), dtype=np.float64), profile=QBP4_F64_V1) <= 25.0
    with pytest.raises(QuaternaryNumericalFailure, match="nonfinite"):
        ordered_boxplus(np.asarray((np.nan,), dtype=np.float64))


def test_four_state_normalization_and_persisted_zero_tie_rule() -> None:
    posterior = llrs_to_probabilities(np.asarray((0.0, 0.0, 0.0), dtype=np.float64))
    assert np.allclose(posterior, 0.25)
    assert pauli_hard_decision(np.asarray((0.0, 0.0, 0.0), dtype=np.float64), profile=QBP4_F64_V1).name == "X"
    assert pauli_hard_decision(np.asarray((0.0, 0.0, 0.0), dtype=np.float64)).name == "Y"
    assert pauli_hard_decision(np.asarray((0.3, 0.2, 0.1), dtype=np.float64)).name == "I"
    assert pauli_hard_decision(np.asarray((0.1, -0.4, -0.4), dtype=np.float64)).name == "Y"


def test_decoder_priors_require_explicit_positive_smoothing() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        probabilities_to_llrs(np.asarray((1.0, 0.0, 0.0, 0.0), dtype=np.float64))


def _one_check_problem(*, observed: int) -> QuaternaryOriginalProblem:
    return QuaternaryOriginalProblem(
        lineage_id="original-qbp-tree",
        code=PauliCode(checks=np.asarray(((1, 3),), dtype=np.uint8)),
        syndrome=np.asarray((observed,), dtype=np.uint8),
    )


def test_kernel_tree_sweep_matches_independent_vector_and_exact_posteriors() -> None:
    priors = np.asarray(((0.55, 0.10, 0.25, 0.10), (0.25, 0.30, 0.20, 0.25)), dtype=np.float64)
    session = ScalarLlrBp4Kernel().new_session(_one_check_problem(observed=0), priors)
    sweep = session.sweep()
    vector_messages, vector_marginals = vector_bp4_one_check(priors, np.asarray((1, 3), dtype=np.uint8), syndrome=0)
    assert np.allclose(sweep.marginals, vector_marginals, atol=1e-12)
    assert np.allclose(sweep.marginals, exact_one_check(priors, np.asarray((1, 3), dtype=np.uint8), syndrome=0), atol=1e-12)
    for edge, label in enumerate((1, 3)):
        anticommuting = np.asarray(anticommutes(np.full(4, label, dtype=np.uint8), np.arange(4, dtype=np.uint8)), dtype=bool)
        expected = np.log(vector_messages[edge, ~anticommuting].sum() / vector_messages[edge, anticommuting].sum())
        assert sweep.c2v[edge] == pytest.approx(expected)


def test_session_snapshots_are_immutable_and_kernel_signature_has_no_truth() -> None:
    kernel = ScalarLlrBp4Kernel()
    sweep = kernel.new_session(_one_check_problem(observed=1), np.full((2, 4), 0.25, dtype=np.float64)).sweep()
    with pytest.raises(ValueError):
        sweep.marginals[0, 0] = 0.0
    assert "truth" not in str(__import__("inspect").signature(kernel.new_session))


def test_session_reserves_full_sweep_work_before_state_mutation_when_capped() -> None:
    budget = BudgetTree(limits=(BudgetLimit("attempt", "bp_calls", 0),), parents={})
    session = ScalarLlrBp4Kernel().new_session(_one_check_problem(observed=0), np.full((2, 4), 0.25, dtype=np.float64), budgets=budget)
    result = session.sweep()
    assert result.terminal == "capped"
    assert result.iteration == 0
    assert budget.summary("attempt").bp_calls == 0


def test_gb46_sweep_retains_preindexed_message_oracle() -> None:
    """The performance refactor must preserve ordered floating point buffers."""
    root = Path(__file__).resolve().parents[3]
    code = compile_css_artifact(
        parse_pinned_gb46_css((root / "data/artifacts/gb46-h44.alist").read_bytes()),
        source_artifact_identity="gb46-h44-pinned-alist",
    )
    rng = np.random.default_rng(11019)
    error = np.zeros(code.n, dtype=np.uint8)
    selected = rng.random(code.n) < .08
    error[selected] = rng.choice(np.asarray([1, 2, 3], dtype=np.uint8), size=int(selected.sum()))
    problem = QuaternaryOriginalProblem("original-gb46-sweep-oracle", code, code.syndrome(error))
    priors = np.tile([.92, .08/3, .08/3, .08/3], (code.n, 1))
    sweep = ScalarLlrBp4Kernel(profile=QBP4_F64_V1).new_session(problem, priors).sweep(stop_on_convergence=False)
    assert sha256(sweep.c2v.tobytes()).hexdigest() == "72d96a38bbc24e37300c0bf2ab2b1470956129cdda71335b2f427efc7dd5f08c"
    assert sha256(sweep.v2c.tobytes()).hexdigest() == "0281382a85bd14f96f40eaa7b7739cc6b525da6f423d39d6aa580b24ca9e7bf6"
    assert sha256(sweep.beliefs.tobytes()).hexdigest() == "31df7094d2f093cd94b7c6092f213deabbbe95bd7c3ebf1d978687944df66db4"
