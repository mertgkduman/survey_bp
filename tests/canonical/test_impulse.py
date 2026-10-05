"""Independent algebra fixtures for exact shortening used by impulse adaptations."""

from __future__ import annotations

from dataclasses import replace
from itertools import product

import numpy as np
import pytest


def _impulse_spec(**overrides):
    return {
        "realization": "exact_shortening", "selection": "minimum_original_weight",
        "baseline_sweeps": 1, "attempt_sweeps": 1, "attempt_cap": 2,
        **overrides,
    }


def test_baseline_success_has_no_impulse_attempts():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.impulse import ImpulseController

    original = _original([[1]], [0])
    result = ImpulseController(_impulse_spec()).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    assert result.termination == "baseline_valid"
    assert result.selected_candidate == (0,)
    assert result.attempts == ()
    assert result.work.transformations == 0


def test_trigger_fresh_shortening_contradiction_and_cap():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.impulse import ImpulseController

    original = _original([[1, 1], [1, 1]], [0, 1])
    result = ImpulseController(_impulse_spec()).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    assert result.baseline_diagnostic_candidate is not None
    assert result.termination == "no_proposal"
    assert tuple(row.target_index for row in result.attempts) == (0, 1)
    assert len({row.session_owner for row in result.attempts}) == 2
    assert all(row.initial_iteration == 0 for row in result.attempts)
    assert all(row.realization == "exact_shortening" for row in result.attempts)
    assert all(not row.original_valid for row in result.attempts)
    assert result.work.transformations == 2


def test_source_semantic_forced_one_keeps_graph_and_json_finite():
    import json
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.impulse import ImpulseController

    original = _original([[1, 1], [1, 1]], [0, 1])
    spec = _impulse_spec(realization="semantic_forced_one", attempt_cap=1)
    result = ImpulseController(spec).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    assert result.attempts[0].graph_identity == result.baseline_graph_identity
    assert result.attempts[0].forced_value == 1
    assert result.attempts[0].source_operator == "negative_infinite_llr"
    assert result.attempts[0].qualification == "source_operator_semantic_adaptation"
    assert "Infinity" not in json.dumps(result.as_evidence(), allow_nan=False)


@pytest.mark.parametrize(
    ("realization", "forced_value", "operator", "identity"),
    (
        ("semantic_forced_zero", 0, "positive_infinite_llr", "impulse_positive_infinite_semantic_v1"),
        ("semantic_forced_one", 1, "negative_infinite_llr", "impulse_negative_infinite_semantic_v1"),
    ),
)
def test_forced_zero_and_one_have_closed_distinct_semantics(realization, forced_value, operator, identity):
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.impulse import ImpulseController, reconstruct_impulse_result

    original = _original([[1, 1], [1, 1]], [0, 1])
    spec = _impulse_spec(realization=realization, attempt_cap=1)
    result = ImpulseController(spec).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))

    assert result.canonical_identity == identity
    assert result.attempts[0].forced_value == forced_value
    assert result.attempts[0].source_operator == operator
    assert result.attempts[0].diagnostic_candidate[0] == forced_value
    reconstruct_impulse_result(spec, original, 0.1, result)


def test_forced_value_rejects_contradictory_realization():
    from bp_registry.canonical.impulse import ImpulseSpec

    with pytest.raises(ValueError, match="forced value"):
        ImpulseSpec(
            realization="semantic_forced_zero", forced_value=1,
            selection="first_convergence", baseline_sweeps=1, attempt_sweeps=1, attempt_cap=1,
        )
    with pytest.raises(ValueError, match="forced value"):
        ImpulseSpec(
            realization="semantic_forced_one", forced_value=0,
            selection="first_convergence", baseline_sweeps=1, attempt_sweeps=1, attempt_cap=1,
        )


def test_phase5_contract_and_dispatch_keep_forced_value_in_public_evidence():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.contracts import Phase5InterventionContract
    from bp_registry.canonical.phase5 import execute_phase5_controller

    spec = Phase5InterventionContract.model_validate({
        "kind": "impulse", "variant": "impulse_positive_infinite_semantic_v1",
        "source_revision": "arxiv:2606.18240v1", "qualification": "source_operator_semantic_adaptation",
        "native_availability": "unverified", "trigger": "baseline_invalid", "operator": "semantic_forced_zero",
        "selection": "first_convergence", "lift_rule": "identity", "reset_rule": "fresh_per_coordinate",
        "preserved_fields": ["original_graph", "original_syndrome"], "unresolved": ["finite_source_surrogate"],
        "stream_status": "not_applicable", "realization": "semantic_forced_zero", "forced_value": 0,
        "v2c_clip": 25.0, "baseline_sweeps": 1, "attempt_sweeps": 1, "attempt_cap": 1,
    })
    outcome = execute_phase5_controller(
        spec, _original([[1, 1], [1, 1]], [0, 1]), error_rate=0.1,
        budgets=BudgetTree(limits=(), parents={}), max_iterations=1, owner_identity="forced-zero-dispatch",
    )

    assert outcome.header["canonical_identity"] == "impulse_positive_infinite_semantic_v1"
    assert outcome.header["v2c_clip"] == 25.0
    assert outcome.header["v2c_clip_boundary"] == "post_v2c_construction_pre_state_commit"
    assert outcome.attempts[0]["forced_value"] == 0


def test_v2c_clip_applies_only_at_committed_v2c_boundary():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.schedules import EdgeTable, FloodingSweep, FloodingWork

    class _OversizedV2C:
        def sweep(self, old_v2c, syndrome, *, error_rate, source_iteration, prior_llrs, transform_v2c=None):
            fresh = np.asarray([40.0, -30.0])
            assert transform_v2c is not None
            clipped = transform_v2c(fresh)
            return FloodingSweep(
                2, np.asarray(old_v2c), np.asarray([60.0, -70.0]), clipped,
                np.asarray([80.0, -90.0]), np.asarray([0, 1], dtype=np.uint8),
                FloodingWork(2, 2, 2, 2),
            )

    session = BpSession(
        EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), np.asarray([0], dtype=np.uint8),
        error_rate=0.1, v2c_clip=25.0,
    )
    session.schedule = _OversizedV2C()
    moved = session.advance(budgets=BudgetTree(limits=(), parents={}), leaf_id="clip-boundary", bp_call_start=True)

    assert moved.admitted
    assert np.array_equal(session.state.v2c, np.asarray([25.0, -25.0]))
    assert np.array_equal(session.state.c2v, np.asarray([60.0, -70.0]))
    assert np.array_equal(session.state.posterior, np.asarray([80.0, -90.0]))


def test_v2c_clip_requires_the_registered_finite_source_control():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.impulse import ImpulseController, ImpulseSpec, reconstruct_impulse_result
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.schedules import EdgeTable

    with pytest.raises(ValueError, match="v2c clip"):
        ImpulseSpec(**_impulse_spec(v2c_clip=24.0))
    with pytest.raises(ValueError, match="v2c clip"):
        BpSession(EdgeTable.from_edges(1, 1, [(0, 0)]), np.asarray([0], dtype=np.uint8), error_rate=0.1, v2c_clip=float("inf"))
    with pytest.raises(ValueError, match="cannot be combined"):
        BpSession(EdgeTable.from_edges(1, 1, [(0, 0)]), np.asarray([0], dtype=np.uint8), error_rate=0.1, v2c_clip=25.0, damping_gamma=0.5)
    original = _original([[1, 1], [1, 1]], [0, 1])
    clipped_spec = _impulse_spec(v2c_clip=25.0, attempt_cap=1)
    clipped = ImpulseController(clipped_spec).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    unclipped = ImpulseController(_impulse_spec(attempt_cap=1)).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    assert clipped.v2c_clip == 25.0
    assert clipped.v2c_clip_boundary == "post_v2c_construction_pre_state_commit"
    assert clipped.baseline_initial_digest != unclipped.baseline_initial_digest
    reconstruct_impulse_result(clipped_spec, original, 0.1, clipped)


def test_impulse_replay_rejects_changed_branch_and_work():
    from dataclasses import replace
    from bp_registry.canonical.budgets import BudgetTree, WorkVector
    from bp_registry.canonical.impulse import ImpulseController, reconstruct_impulse_result

    original = _original([[1, 1], [1, 1]], [0, 1])
    spec = _impulse_spec()
    result = ImpulseController(spec).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    reconstruct_impulse_result(spec, original, 0.1, result)
    altered = replace(result.attempts[0], target_index=1)
    with pytest.raises(ValueError, match="replay"):
        reconstruct_impulse_result(spec, original, 0.1, replace(result, attempts=(altered, *result.attempts[1:])))
    with pytest.raises(ValueError, match="replay"):
        reconstruct_impulse_result(spec, original, 0.1, replace(result, work=result.work + WorkVector(bp_calls=1)))


def test_minimum_weight_and_first_convergence_are_stable_under_worker_order():
    from dataclasses import replace
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.impulse import ImpulseController, select_impulse_candidate

    original = _original([[1, 1, 0], [0, 1, 1]], [1, 0])
    impossible = _original([[1, 1, 1], [1, 1, 1]], [0, 1])
    result = ImpulseController(_impulse_spec()).run(impossible, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    heavier = replace(result.attempts[0], order=0, target_index=0, lifted_candidate=(0, 1, 1), original_valid=True)
    lighter = replace(result.attempts[1], order=1, target_index=1, lifted_candidate=(1, 0, 0), original_valid=True)
    for rows in ((heavier, lighter), (lighter, heavier)):
        assert select_impulse_candidate(rows, original, mode="minimum_original_weight") == lighter
        assert select_impulse_candidate(rows, original, mode="first_convergence") == heavier
    forged = replace(lighter, lifted_candidate=(0, 0, 0))
    assert select_impulse_candidate((forged,), original, mode="minimum_original_weight") is None


def test_attempt_cap_and_budget_denial_keep_unique_committed_work():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.impulse import ImpulseController

    original = _original([[1, 1, 1], [1, 1, 1]], [0, 1])
    capped = ImpulseController(_impulse_spec(attempt_cap=1)).run(
        original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}),
    )
    assert capped.termination == "attempt_cap_reached"
    assert len(capped.attempts) == 1
    assert len({row[0] for row in capped.leaves}) == len(capped.leaves)
    denied_budget = BudgetTree(limits=[BudgetLimit("attempt", "intervention_actions", 0)], parents={})
    denied = ImpulseController(_impulse_spec()).run(original, error_rate=0.1, budgets=denied_budget)
    assert denied.termination == "count_budget_exhausted"
    assert len(denied.attempts) == 1
    assert denied.attempts[0].action_leaf is None
    assert denied.work.intervention_actions == 0
    assert denied.work == denied_budget.summary("attempt")


def test_first_convergence_stops_at_first_declared_valid_attempt():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.impulse import ImpulseController

    original = _original(
        [[1, 1, 1, 1, 1], [0, 1, 0, 1, 1], [1, 0, 0, 1, 1]],
        [0, 0, 1],
    )
    first = ImpulseController(_impulse_spec(
        selection="first_convergence", attempt_sweeps=5, attempt_cap=5,
    )).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    minimum = ImpulseController(_impulse_spec(
        selection="minimum_original_weight", attempt_sweeps=5, attempt_cap=5,
    )).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}))
    assert first.termination == "impulse_valid"
    assert first.selected_origin == 0
    assert len(first.attempts) == 1
    assert minimum.termination == "impulse_valid"
    assert len(minimum.attempts) == 5
    assert minimum.work.bp_calls > first.work.bp_calls
    assert np.array_equal((original.hz @ first.selected_candidate) % 2, original.syndrome)


def _original(h, s):
    from bp_registry.canonical.problems import OriginalProblem

    matrix = np.asarray(h, dtype=np.uint8)
    return OriginalProblem("original-shortening-fixture", np.zeros((1, matrix.shape[1]), dtype=np.uint8), matrix, np.asarray(s, dtype=np.uint8))


def test_shortening_lift_exhaustive_matches_independent_gf2_oracle():
    from bp_registry.canonical.transformations import lift_candidate, transform_fixed_coordinates

    cases = 0
    for flat in product((0, 1), repeat=6):
        h = np.asarray(flat, dtype=np.uint8).reshape(2, 3)
        for syndrome in product((0, 1), repeat=2):
            original = _original(h, syndrome)
            for mask in product((0, 1), repeat=3):
                fixed = tuple(i for i, flag in enumerate(mask) if flag)
                free = tuple(i for i in range(3) if i not in fixed)
                for assignment in product((0, 1), repeat=len(fixed)):
                    working, certificate = transform_fixed_coordinates(original, fixed, assignment)
                    assert working.column_map == free
                    assert working.row_map == (0, 1)
                    for y in product((0, 1), repeat=len(free)):
                        lifted = lift_candidate(working, certificate, np.asarray(y, dtype=np.uint8))
                        expected = np.zeros(3, dtype=np.uint8)
                        expected[list(fixed)] = assignment
                        expected[list(free)] = y
                        assert np.array_equal(lifted.candidate, expected)
                        assert lifted.working_valid == bool(np.array_equal((working.check_matrix @ y) % 2, working.syndrome))
                        assert lifted.original_valid == bool(np.array_equal((h @ expected) % 2, syndrome))
                        assert lifted.working_valid == lifted.original_valid
                        cases += 1
    assert cases == 16384


def test_all_fixed_success_and_contradiction_and_bad_lift_certificate():
    from bp_registry.canonical.transformations import lift_candidate, transform_fixed_coordinates

    original = _original([[1]], [1])
    good, good_map = transform_fixed_coordinates(original, (0,), (1,))
    bad, bad_map = transform_fixed_coordinates(original, (0,), (0,))
    assert good.check_matrix.shape == (1, 0)
    assert lift_candidate(good, good_map, np.empty(0, dtype=np.uint8)).original_valid
    denied = lift_candidate(bad, bad_map, np.empty(0, dtype=np.uint8))
    assert not denied.working_valid and not denied.original_valid
    assert denied.reason == "contradictory_empty_check"
    with pytest.raises(ValueError):
        lift_candidate(good, replace(good_map, fixed_values=(0,)), np.empty(0, dtype=np.uint8))
    with pytest.raises(ValueError):
        lift_candidate(good, good_map, np.asarray([1], dtype=np.uint8))


def test_shortening_idempotent_and_concurrent_order_invariant():
    from concurrent.futures import ThreadPoolExecutor
    from bp_registry.canonical.transformations import lift_candidate, transform_fixed_coordinates

    original = _original([[1, 1, 0], [0, 1, 1]], [1, 0])
    first = transform_fixed_coordinates(original, (1,), (1,))
    second = transform_fixed_coordinates(original, (1,), (1,))
    assert first[0].lineage_id == second[0].lineage_id
    assert first[1].digest == second[1].digest
    candidates = [np.asarray(bits, dtype=np.uint8) for bits in product((0, 1), repeat=2)]
    with ThreadPoolExecutor(max_workers=3) as executor:
        shuffled = list(executor.map(lambda y: lift_candidate(*first, y), reversed(candidates)))
    serial = [lift_candidate(*first, y) for y in candidates]
    assert sorted(tuple(item.candidate) for item in shuffled) == sorted(tuple(item.candidate) for item in serial)
