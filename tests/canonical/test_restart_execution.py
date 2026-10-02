"""Phase 5 session reset, continuation, transaction, and stream contracts."""

from __future__ import annotations

import numpy as np
import pytest


def _restart_original(h, syndrome):
    from bp_registry.canonical.problems import OriginalProblem

    matrix = np.asarray(h, dtype=np.uint8)
    return OriginalProblem(
        "original-restart-fixture", np.zeros((1, matrix.shape[1]), dtype=np.uint8),
        matrix, np.asarray(syndrome, dtype=np.uint8),
    )


def _restart_spec(**overrides):
    return {
        "preset": "b1_tcap8_mechanism", "code_id": "b1-ghp-882",
        "eta": 2, "t_cap": 8, "root_sweeps": 1, "residual_sweeps": 2,
        **overrides,
    }


def test_restart_distance_preset_rejects_b1_and_adaptation_qualifies():
    from bp_registry.canonical.restarting import RestartSpec

    with pytest.raises(ValueError, match="distance"):
        RestartSpec(preset="source_exact_distance", code_id="b1-ghp-882", eta=2, t_cap=8, root_sweeps=1, residual_sweeps=2)
    spec = RestartSpec(**_restart_spec())
    assert spec.qualification == "pilot_adaptation"
    assert spec.source_random_stream == "not_applicable"


def test_restart_b1_gate_branches_from_valid_root_above_proven_t8():
    """A syndrome-valid root is not sufficient for source early acceptance."""
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.restarting import RestartController

    original = _restart_original(np.eye(9, dtype=np.uint8), np.ones(9, dtype=np.uint8))
    result = RestartController(_restart_spec(eta=1, residual_sweeps=1)).run(
        original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}),
    )

    assert result.root_termination == "root_valid"
    assert sum(result.root_candidate) == 9
    assert result.root_weight == 9
    assert result.root_acceptance_threshold == 8
    assert result.root_acceptance_rule == "proven_lower_bound_t8_weight_gate_without_defect_shortcut"
    assert result.root_defect_gate_status == "unavailable_without_declared_xi_and_applicable_t"
    assert not result.root_accepted
    assert result.termination != "root_valid"
    assert len(result.branches) == 1


def test_restart_exact_distance_gate_branches_from_overweight_valid_root():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.restarting import RestartController

    original = _restart_original(np.eye(2, dtype=np.uint8), np.ones(2, dtype=np.uint8))
    result = RestartController({
        "preset": "source_exact_distance", "code_id": "two-bit-fixture",
        "eta": 1, "t_cap": 1, "root_sweeps": 1, "residual_sweeps": 1,
        "exact_distance": 3,
    }).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))

    assert result.root_termination == "root_valid"
    assert sum(result.root_candidate) == 2
    assert result.root_acceptance_threshold == 1
    assert result.root_acceptance_rule == "exact_t_weight_gate_without_defect_shortcut"
    assert not result.root_accepted
    assert result.termination != "root_valid"
    assert len(result.branches) == 1


def test_restart_b1_gate_accepts_root_within_proven_t8():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.restarting import RestartController

    original = _restart_original(np.eye(8, dtype=np.uint8), np.ones(8, dtype=np.uint8))
    result = RestartController(_restart_spec(eta=1, residual_sweeps=1)).run(
        original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}),
    )

    assert result.root_weight == result.root_acceptance_threshold == 8
    assert result.root_accepted
    assert result.termination == "root_valid"
    assert result.selected_candidate == result.root_candidate
    assert result.branches == ()


def test_restart_root_branch_residual_reset_inserted_and_t_cap():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.restarting import RestartController

    original = _restart_original([[1, 1], [1, 1]], [0, 1])
    result = RestartController(_restart_spec()).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    assert result.root_candidate is not None
    assert result.root_llr_order == tuple(sorted(result.root_llr_order))
    assert len(result.branches) <= 2
    assert result.source_random_stream == "not_applicable"
    assert result.qualification == "development_fixture"
    assert result.code_identity_status == "dimension_mismatch_fixture"
    assert all(branch.residuals for branch in result.branches)
    assert all(row.initial_iteration == 0 for branch in result.branches for row in branch.residuals)
    assert all(row.residual_syndrome == tuple(int(x) for x in (original.syndrome ^ ((original.hz @ row.inserted_error) % 2))) for branch in result.branches for row in branch.residuals)
    assert len({row.session_owner for branch in result.branches for row in branch.residuals}) == sum(len(branch.residuals) for branch in result.branches)


def test_restart_replay_rejects_residual_and_work_tampering():
    from dataclasses import replace
    from bp_registry.canonical.budgets import BudgetTree, WorkVector
    from bp_registry.canonical.restarting import RestartController, reconstruct_restart_result

    original = _restart_original([[1, 1], [1, 1]], [0, 1])
    spec = _restart_spec()
    result = RestartController(spec).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    reconstruct_restart_result(spec, original, 0.1, result)
    first = result.branches[0]
    changed = replace(first.residuals[0], residual_syndrome=(0, 0))
    with pytest.raises(ValueError, match="replay"):
        reconstruct_restart_result(spec, original, 0.1, replace(result, branches=(replace(first, residuals=(changed, *first.residuals[1:])), *result.branches[1:])))
    with pytest.raises(ValueError, match="replay"):
        reconstruct_restart_result(spec, original, 0.1, replace(result, work=result.work + WorkVector(bp_calls=1)))


def test_restart_strict_lower_weight_keeps_stable_tie_and_valid_lifts():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.restarting import RestartController

    original = _restart_original(
        [[0, 0, 1, 1, 1], [0, 0, 1, 1, 0], [1, 1, 1, 0, 1]],
        [1, 0, 0],
    )
    result = RestartController(_restart_spec(eta=3, residual_sweeps=3)).run(
        original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}),
    )
    assert result.termination == "restart_valid"
    assert result.selected_origin == (0, 1)
    assert sum(result.selected_candidate) == 2
    assert result.branches[1].residuals[0].original_weight == 3
    assert result.branches[2].residuals[0].original_weight == 2
    assert np.array_equal((original.hz @ result.selected_candidate) % 2, original.syndrome)
    assert all(row.original_valid is True for branch in result.branches for row in branch.residuals if row.termination == "valid_original_candidate")


def test_restart_denied_and_contradiction_leaves_remain_unique():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.restarting import RestartController

    original = _restart_original([[1, 1], [1, 1]], [0, 1])
    denied_budget = BudgetTree(limits=[BudgetLimit("attempt", "branch_expansions", 0)], parents={})
    denied = RestartController(_restart_spec()).run(original, error_rate=0.1, budgets=denied_budget)
    assert denied.termination == "count_budget_exhausted"
    assert denied.branches[0].open_leaf is None
    assert denied.work.branch_expansions == 0
    normal_budget = BudgetTree(limits=(), parents={})
    normal = RestartController(_restart_spec()).run(original, error_rate=0.1, budgets=normal_budget)
    assert any(row.termination == "contradictory_empty_check" for branch in normal.branches for row in branch.residuals)
    assert len({leaf[0] for leaf in normal.leaves}) == len(normal.leaves)
    assert normal.work == normal_budget.summary("attempt")
    assert normal.work.candidate_checks > 0


def _session():
    from bp_registry.canonical.intervention_session import InterventionSession
    from bp_registry.canonical.schedules import EdgeTable

    h = np.asarray([[1, 1], [0, 1]], dtype=np.uint8)
    return InterventionSession(EdgeTable.from_check_matrix(h), np.asarray([1, 0], dtype=np.uint8), error_rate=0.1)


def test_session_continue_and_fresh_reset_clear_all_undeclared_state():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable

    session = _session()
    factory = BinarySpaKernel().new_session(
        EdgeTable.from_check_matrix(np.asarray([[1, 1], [0, 1]], dtype=np.uint8)),
        np.asarray([1, 0], dtype=np.uint8), error_rate=0.1,
    )
    assert factory.state.graph_identity == session.state.graph_identity
    budgets = BudgetTree(limits=(), parents={})
    start = session.state
    steps = session.continue_units(2, budgets=budgets, leaf_prefix="continued")
    assert all(step.admitted for step in steps)
    assert session.state.source_iteration == 2
    assert session.state.graph_identity == start.graph_identity
    assert session.state.owner_identity == start.owner_identity
    assert session.state.digest != start.digest
    branch = session.reset_fresh(budgets=budgets, leaf_id="branch-reset")
    assert branch is not session
    assert branch.state.source_iteration == 0
    assert branch.state.revision == 0
    assert branch.state.fixed_indices == ()
    assert branch.state.owner_identity != session.state.owner_identity
    assert np.array_equal(branch.state.v2c, start.v2c)
    assert np.array_equal(branch.state.posterior, start.posterior)
    assert session.state.source_iteration == 2


def test_session_incompatible_preservation_rejects_prior_graph_and_owner_mismatch():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.schedules import EdgeTable

    session = _session()
    budgets = BudgetTree(limits=(), parents={})
    start = session.state
    with pytest.raises(ValueError, match="incompatible"):
        session.reset_fresh(budgets=budgets, leaf_id="bad-prior", preserve=("v2c",), error_rate=0.2)
    different = EdgeTable.from_check_matrix(np.asarray([[1, 0], [1, 1]], dtype=np.uint8))
    with pytest.raises(ValueError, match="incompatible"):
        session.reset_fresh(budgets=budgets, leaf_id="bad-graph", preserve=("v2c",), edge_table=different)
    with pytest.raises(ValueError, match="incompatible"):
        session.reset_fresh(budgets=budgets, leaf_id="bad-owner", preserve=("v2c",), owner_identity="foreign")
    assert session.state is start
    assert budgets.summary("attempt").intervention_actions == 0


def test_session_posterior_mutation_preserves_prior_and_changes_outgoing_messages():
    from bp_registry.canonical.budgets import BudgetTree

    session = _session()
    budgets = BudgetTree(limits=(), parents={})
    session.continue_units(1, budgets=budgets, leaf_prefix="pre-sign")
    before = session.state
    changed = session.mutate_posterior_sign(1, budgets=budgets, leaf_id="sign-action")
    assert changed.admitted
    assert np.array_equal(session.state.prior, before.prior)
    assert session.state.posterior[1] == -before.posterior[1]
    assert not np.array_equal(session.state.v2c, before.v2c)
    assert session.state.mutation_evidence["preserved"] == ("prior", "c2v", "graph", "syndrome")
    assert session.state.mutation_evidence["recomputed"] == ("target_v2c", "target_hard_decision")


def test_session_numerical_failure_rolls_back_reservation_and_state(monkeypatch):
    from bp_registry.canonical.budgets import BudgetTree

    session = _session()
    budgets = BudgetTree(limits=(), parents={})
    before = session.state
    monkeypatch.setattr(session.schedule, "sweep", lambda *args, **kwargs: (_ for _ in ()).throw(FloatingPointError("fixture")))
    with pytest.raises(FloatingPointError):
        session.advance(budgets=budgets, leaf_id="failed-sweep")
    assert session.state is before
    assert budgets.summary("attempt").bp_calls == 0


def test_proposal_stale_duplicate_and_foreign_owner_have_distinct_rejection():
    from bp_registry.canonical.budgets import BudgetTree

    session = _session()
    foreign = _session()
    budgets = BudgetTree(limits=(), parents={})
    proposal = session.propose_finite_prior(0, 25.0)
    assert session.commit_intervention(proposal, budgets=budgets, leaf_id="fix-0").admitted
    with pytest.raises(ValueError, match="stale"):
        session.commit_intervention(proposal, budgets=budgets, leaf_id="fix-again")
    with pytest.raises(ValueError, match="foreign"):
        foreign.commit_intervention(proposal, budgets=budgets, leaf_id="fix-foreign")
    assert budgets.summary("attempt").intervention_actions == 1


def test_stream_identity_is_purpose_separated_and_worker_invariant():
    from bp_registry.canonical.intervention_session import decoder_stream_identity

    target = decoder_stream_identity("root", "decoder", "freeze", 2, "target")
    assert target == decoder_stream_identity("root", "decoder", "freeze", 2, "target")
    assert target != decoder_stream_identity("root", "decoder", "freeze", 2, "tie")
    assert target != decoder_stream_identity("root", "other", "freeze", 2, "target")
    with pytest.raises(ValueError):
        decoder_stream_identity("root", "decoder", "freeze", 2, "physical_sampling")


def test_leaf_work_extension_preserves_historical_serialization():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree, WorkVector

    new = WorkVector(fixation_actions=1, transformations=2, lifted_coordinates=3, original_checks=4, ranking_scans=5)
    assert "fixation_actions" not in new.as_evidence(structural_event_version=2)
    assert "fixation_actions" not in new.as_evidence(structural_event_version=3)
    assert new.as_evidence(structural_event_version=4)["fixation_actions"] == 1
    tree = BudgetTree(limits=(BudgetLimit("attempt", "transformations", 2),), parents={})
    token = tree.reserve("attempt", new, leaf_id="new-categories")
    assert token is not None
    token.commit_once()
    assert tree.reserve("attempt", WorkVector(transformations=1), leaf_id="denied") is None
    assert tree.summary("attempt") == new
