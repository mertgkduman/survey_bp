"""A local result reports the same posterior that produced its candidate."""
import numpy as np
import pytest
from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.schedules import CheckNodeSerialSchedule, VariableNodeSerialSchedule, EdgeTable


@pytest.mark.parametrize("cls", (CheckNodeSerialSchedule, VariableNodeSerialSchedule))
@pytest.mark.parametrize("mode", ("ordinary", "prior", "field", "both", "noop"))
def test_reported_posterior_is_the_committed_decision_input(cls, mode):
    kernel = BinarySpaKernel()
    table = EdgeTable.from_check_matrix(np.ones((2, 2), dtype=np.uint8))
    schedule = cls(table, kernel=kernel)
    seen, calls = [], []
    original_decision = kernel.candidate_from_beliefs
    def decision(beliefs):
        seen.append(beliefs.copy())
        return original_decision(beliefs)
    kernel.candidate_from_beliefs = decision
    def transform(beliefs, _c2v):
        calls.append(1)
        return beliefs if mode == "noop" else beliefs + np.array([-8., 3.])
    result = schedule.execute_local_step(CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt"), np.array([1., 2., 3., 4.]), np.array([0, 0]),
        error_rate=.2, progress=ScheduleProgress(0, 0, (0,)), is_converged=lambda _: False,
        prior_llrs=np.array([-2., 4.]) if mode in ("prior", "both") else None,
        transform_beliefs=transform if mode in ("field", "both", "noop") else None)
    assert result.admitted and len(seen) == 1
    assert len(calls) == int(mode in ("field", "both", "noop"))
    np.testing.assert_array_equal(result.posterior, seen[0])
    np.testing.assert_array_equal(result.candidate, original_decision(result.posterior))
    with pytest.raises(ValueError):
        result.posterior.setflags(write=True)


@pytest.mark.parametrize("cls", (CheckNodeSerialSchedule, VariableNodeSerialSchedule))
def test_denied_step_exposes_no_posterior_and_calls_no_transform(cls):
    table = EdgeTable.from_check_matrix(np.ones((2, 2), dtype=np.uint8))
    schedule = cls(table, kernel=BinarySpaKernel())
    tree = BudgetTree(limits=(BudgetLimit("attempt", "convergence_checks", 0),))
    messages = np.array([1., 2., 3., 4.])
    def unexpected(*_):
        pytest.fail("denied computation must not run")
    result = schedule.execute_local_step(CanonicalLocalStepExecutor(tree, scope="attempt"), messages, np.array([0, 0]),
        error_rate=.2, progress=ScheduleProgress(0, 0, (0,)), is_converged=unexpected, transform_beliefs=unexpected)
    assert not result.admitted and result.posterior is None and result.candidate is None
    np.testing.assert_array_equal(messages, [1., 2., 3., 4.])
    np.testing.assert_array_equal(schedule._c2v, np.zeros(4))
    assert tree.leaf_events() == ()
