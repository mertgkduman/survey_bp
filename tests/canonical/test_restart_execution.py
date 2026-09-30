"""Phase 5 session reset, continuation, transaction, and stream contracts."""

from __future__ import annotations

import numpy as np
import pytest


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
