"""Syndrome-transform certificates and original-check boundary fixtures."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest


def _problem(h, syndrome):
    from bp_registry.canonical.problems import OriginalProblem

    matrix = np.asarray(h, dtype=np.uint8)
    return OriginalProblem(
        "original-perturbative-fixture", np.zeros((1, matrix.shape[1]), dtype=np.uint8),
        matrix, np.asarray(syndrome, dtype=np.uint8),
    )


def test_freezing_eligibility_lifetime_release_retry_and_cap():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.interventions import FreezingController, FreezingSpec

    original = _problem([[1, 1], [1, 1]], [0, 1])
    before = original.hz.copy()
    spec = FreezingSpec(period_sweeps=1, lifetime_sweeps=1, retry_cap=2, root_seed="freeze-seed")
    result = FreezingController(spec).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    assert result.qualification == "controlled_css_adaptation"
    assert result.selected_candidate is None
    assert len(result.trials) <= 2
    assert all(row.fixed_value == 0 for row in result.trials)
    assert all(row.release_view_original == original.lineage_id for row in result.trials)
    assert all(row.release_leaf and row.reset_rule == "fresh_structural_branch_then_release_to_original" for row in result.trials)
    assert result.source_kernel_family == "quaternary_depolarizing_bp"
    assert np.array_equal(original.hz, before)
    assert len({row.target_index for row in result.trials}) == len(result.trials)


def test_syndrome_flip_oscillation_certificate_and_original_invalid_rejection():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.interventions import SyndromeFlipController, SyndromeFlipSpec

    original = _problem([[1, 1], [1, 1]], [0, 1])
    spec = SyndromeFlipSpec(baseline_sweeps=2, attempt_sweeps=1, top_k=2, max_weight=1, test_cap=2, root_seed="sf-seed")
    result = SyndromeFlipController(spec).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    assert result.qualification == "controlled_css_adaptation"
    assert result.baseline_oscillations is not None
    assert result.original_lineage_id == original.lineage_id
    assert all(row.test_vector is not None and row.lift_digest for row in result.tests)
    assert all(not row.eligible for row in result.tests)


def test_sign_flip_posterior_global_target_and_message_continuation():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.interventions import SignFlipController, SignFlipSpec

    original = _problem([[1, 1], [1, 1]], [0, 1])
    result = SignFlipController(SignFlipSpec(alpha=0.8, trunk_sweeps=1, continuation_sweeps=1)).run(
        original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}),
    )
    assert result.qualification == "bsfbp_sign_only_controlled_adaptation"
    assert result.trigger == "failed_normalized_min_sum_trunk"
    assert result.target_index == 0
    assert result.prior_before == result.prior_after
    assert result.v2c_before == result.v2c_after_action
    assert result.c2v_before == result.c2v_after_action
    assert result.posterior_after_action[result.target_index] == -result.posterior_before[result.target_index]
    assert result.continuation_state_digest != result.action_state_digest


def test_intervention_idempotent_stale_and_concurrent_one_leaf():
    from concurrent.futures import ThreadPoolExecutor
    from bp_registry.canonical.budgets import BudgetTree, WorkVector
    from bp_registry.canonical.interventions import IdempotentActionGate

    budget = BudgetTree(limits=(), parents={})
    gate = IdempotentActionGate("owner", budget)
    def commit(_):
        return gate.commit("same", expected_revision=0, work=WorkVector(intervention_actions=1), leaf_id="one", value="done")
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(commit, range(8)))
    assert outcomes == ["done"] * 8
    assert gate.revision == 1
    assert budget.summary("attempt").intervention_actions == 1
    with pytest.raises(ValueError, match="stale"):
        gate.commit("new", expected_revision=0, work=WorkVector(intervention_actions=1), leaf_id="two", value="bad")


def test_syndrome_flip_first_declared_valid_is_worker_order_invariant():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.interventions import SyndromeFlipController, SyndromeFlipSpec, select_syndrome_flip_test

    original = _problem(
        [[0, 0, 1, 1, 1], [0, 0, 1, 1, 0], [1, 1, 1, 0, 1]],
        [1, 0, 0],
    )
    result = SyndromeFlipController(SyndromeFlipSpec(2, 3, 5, 1, 5, "seed")).run(
        original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}),
    )
    assert result.termination == "syndrome_flip_valid"
    assert result.selected_test_order == 1
    assert len(result.tests) == 2
    assert not result.tests[0].eligible
    assert result.tests[1].eligible
    assert result.tests[1].working_valid and not result.tests[1].raw_original_valid
    assert result.tests[1].original_valid
    assert select_syndrome_flip_test(result.tests, original) == result.tests[1]
    assert select_syndrome_flip_test(tuple(reversed(result.tests)), original) == result.tests[1]
    assert np.array_equal((original.hz @ result.selected_candidate) % 2, original.syndrome)


def test_sign_flip_staged_action_rejects_duplicate_and_preserves_messages():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.schedules import EdgeTable

    h = np.asarray([[1, 1]], dtype=np.uint8)
    session = BpSession(EdgeTable.from_check_matrix(h), np.asarray([1], dtype=np.uint8), error_rate=0.1)
    budget = BudgetTree(limits=(), parents={})
    session.advance(budgets=budget, leaf_id="trunk")
    before = session.state
    action = session.stage_posterior_sign(0, budgets=budget, leaf_id="stage")
    assert action.admitted
    assert np.array_equal(session.state.v2c, before.v2c)
    assert np.array_equal(session.state.c2v, before.c2v)
    assert session.state.pending_sign_target == 0
    with pytest.raises(ValueError, match="pending"):
        session.stage_posterior_sign(0, budgets=budget, leaf_id="duplicate")
    assert budget.summary("attempt").intervention_actions == 1
    session.advance(budgets=budget, leaf_id="continuation")
    assert session.state.pending_sign_target is None


def test_freezing_syndrome_and_sign_replay_reject_semantic_tampering():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.interventions import (
        FreezingController, FreezingSpec, SyndromeFlipController, SyndromeFlipSpec,
        SignFlipController, SignFlipSpec, reconstruct_freezing_result,
        reconstruct_syndrome_flip_result, reconstruct_sign_flip_result,
    )

    original = _problem([[1, 1], [1, 1]], [0, 1])
    cases = (
        (FreezingSpec(1, 1, 2, "seed"), FreezingController, reconstruct_freezing_result, "termination"),
        (SyndromeFlipSpec(2, 1, 2, 1, 2, "seed"), SyndromeFlipController, reconstruct_syndrome_flip_result, "termination"),
        (SignFlipSpec(0.8, 1, 1), SignFlipController, reconstruct_sign_flip_result, "termination"),
    )
    for spec, controller, replay, field in cases:
        result = controller(spec).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
        assert replay(spec, original, 0.1, result) == result
        with pytest.raises(ValueError, match="replay"):
            replay(spec, original, 0.1, replace(result, **{field: "forged_terminal"}))


def test_syndrome_certificate_lift_and_original_invalid_without_it():
    from bp_registry.canonical.problems import OriginalProblem
    from bp_registry.canonical.transformations import lift_candidate, transform_syndrome

    original = OriginalProblem(
        "original-syndrome-fixture", np.zeros((1, 2), dtype=np.uint8),
        np.asarray([[1, 1]], dtype=np.uint8), np.asarray([1], dtype=np.uint8),
    )
    working, certificate = transform_syndrome(original, np.asarray([1, 0], dtype=np.uint8))
    assert np.array_equal(working.syndrome, np.asarray([0], dtype=np.uint8))
    raw = np.asarray([0, 0], dtype=np.uint8)
    assert np.array_equal((original.hz @ raw) % 2, [0])
    lifted = lift_candidate(working, certificate, raw)
    assert lifted.working_valid and lifted.original_valid
    assert np.array_equal(lifted.candidate, np.asarray([1, 0], dtype=np.uint8))
    with pytest.raises(ValueError):
        lift_candidate(working, replace(certificate, test_vector=(0, 0)), raw)
    with pytest.raises(ValueError):
        transform_syndrome(original, row_mask=np.asarray([1], dtype=np.uint8))
