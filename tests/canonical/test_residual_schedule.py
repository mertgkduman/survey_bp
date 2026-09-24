"""Source-lifecycle oracle tests for the pinned Huang--Ueng sRBP schedule."""

from __future__ import annotations

import importlib
import importlib.util

import numpy as np


def _residual_module():
    """Make the absent Phase 3 policy a deliberate, assertion-based RED."""
    spec = importlib.util.find_spec("bp_registry.canonical.residual")
    assert spec is not None, "Phase 3 must provide bp_registry.canonical.residual"
    return importlib.import_module("bp_registry.canonical.residual")


def test_tracer_residual_schedule_contract_is_closed_to_conventional_srbp():
    residual = _residual_module()
    assert hasattr(residual, "SyndromeResidualSchedule")
    assert hasattr(residual, "ResidualCache")
    assert hasattr(residual, "ResidualSelection")
    assert residual.SyndromeResidualSchedule.policy_name == "huang_ueng_conventional_srbp"
    assert residual.SyndromeResidualSchedule.tie_rule == "canonical_edge_order"
    assert residual.SyndromeResidualSchedule.stopping_adaptation == "D-09 after residual-selected local unit"


def test_tracer_initializes_full_pool_selects_first_tie_and_reserves_one_local_unit():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable

    residual = _residual_module()
    table = EdgeTable.from_edges(2, 2, [(1, 1), (0, 1), (1, 0), (0, 0)])
    schedule = residual.SyndromeResidualSchedule(table, kernel=BinarySpaKernel())
    v2c = np.asarray([1.0, 1.0, 1.0, 1.0])
    c2v = np.asarray([0.0, 0.0, 0.0, 0.0])
    cache = schedule.initialize(v2c, c2v, np.asarray([0, 0]), error_rate=0.1)

    assert cache.values.shape == (4,)
    assert cache.setup_work.residual_precomputations == 4
    assert cache.setup_work.residual_differences == 4
    proposal = schedule.propose_local_step(v2c, c2v, cache, np.asarray([0, 0]), error_rate=0.1)
    assert proposal.selection.index == 0
    assert proposal.selection.comparisons == 3
    assert proposal.local_step.proposed_work.candidate_checks == 1
    assert proposal.decode_work.priority_comparisons == 3

    result = schedule.execute_local_step(
        CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt"),
        proposal,
        v2c=v2c,
        c2v=c2v,
        cache=cache,
        progress=ScheduleProgress(iteration=0, local_steps=0),
        is_converged=lambda _candidate: False,
    )
    assert result.admitted is True
    assert result.selection.edge == (0, 0)
    assert result.progress.local_steps == 1
    assert result.progress.iteration == 0
    assert result.cache.values[result.selection.index] == 0.0
    assert result.candidate.shape == (2,)
