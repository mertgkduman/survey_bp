"""The Phase 5 memory composition follows the cited damped-message recurrence."""

from __future__ import annotations

import numpy as np


def test_v2c_damping_uses_previous_damped_output_and_resets_on_new_attempt():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.numerics import REFERENCE_CPU_F64
    from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule

    table = EdgeTable.from_check_matrix(np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8))
    syndrome = np.asarray([1, 0], dtype=np.uint8)
    session = BpSession(table, syndrome, error_rate=0.1, damping_gamma=0.5)
    reference = FloodingSchedule(table, kernel=BinarySpaKernel(profile=REFERENCE_CPU_F64))
    initial = reference.initialize(0.1)
    first_fresh = reference.sweep(initial, syndrome, error_rate=0.1, source_iteration=0)
    budget = BudgetTree(limits=(), parents={})

    first = session.advance(budgets=budget, leaf_id="damped:first")
    assert first.admitted
    first_damped = 0.5 * initial + 0.5 * first_fresh.new_v2c
    np.testing.assert_allclose(session.state.v2c, first_damped)
    np.testing.assert_allclose(session.state.private_histories[0], first_damped)

    second_fresh = reference.sweep(session.state.v2c, syndrome, error_rate=0.1, source_iteration=1)
    second = session.advance(budgets=budget, leaf_id="damped:second")
    assert second.admitted
    second_damped = 0.5 * first_damped + 0.5 * second_fresh.new_v2c
    np.testing.assert_allclose(session.state.v2c, second_damped)
    np.testing.assert_allclose(session.state.private_histories[0], second_damped)

    child = session.reset_fresh(budgets=budget, leaf_id="damped:reset")
    np.testing.assert_allclose(child.state.v2c, initial)
    np.testing.assert_allclose(child.state.private_histories[0], initial)
    assert child.state.source_iteration == 0
    assert child.state.digest != session.state.digest


def test_gamma_one_matches_undamped_messages_and_candidate():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.schedules import EdgeTable

    table = EdgeTable.from_check_matrix(np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8))
    syndrome = np.asarray([1, 0], dtype=np.uint8)
    plain = BpSession(table, syndrome, error_rate=0.1)
    damped = BpSession(table, syndrome, error_rate=0.1, damping_gamma=1.0)
    for index in range(3):
        assert plain.advance(budgets=BudgetTree(limits=(), parents={}), leaf_id=f"plain:{index}").admitted
        assert damped.advance(budgets=BudgetTree(limits=(), parents={}), leaf_id=f"damped:{index}").admitted
        np.testing.assert_allclose(damped.state.v2c, plain.state.v2c)
        np.testing.assert_allclose(damped.state.posterior, plain.state.posterior)
        np.testing.assert_array_equal(damped.state.candidate, plain.state.candidate)


def test_damped_impulse_reaches_fresh_shortened_attempts():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.impulse import ImpulseController
    from bp_registry.canonical.problems import OriginalProblem

    original = OriginalProblem(
        "original-damped-impulse-inconsistent-fixture",
        np.zeros((1, 2), dtype=np.uint8),
        np.asarray([[1, 1], [1, 1]], dtype=np.uint8),
        np.asarray([0, 1], dtype=np.uint8),
    )
    result = ImpulseController({
        "realization": "exact_shortening", "selection": "minimum_original_weight",
        "baseline_sweeps": 1, "attempt_sweeps": 1, "attempt_cap": 2,
    }).run(original, error_rate=0.1, budgets=BudgetTree(limits=(), parents={}), damping_gamma=0.5)
    assert len(result.attempts) == 2
    assert all(row.initial_state_digest for row in result.attempts)
    assert result.work.transformations == 2
