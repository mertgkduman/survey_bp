"""Golden double-buffering and canonical-order contracts for flooding SPA."""

from __future__ import annotations

import importlib
import importlib.util

import numpy as np
import pytest


def _api():
    assert importlib.util.find_spec("bp_registry.canonical.schedules") is not None, (
        "canonical flooding requires a project-owned schedules module"
    )
    schedules = importlib.import_module("bp_registry.canonical.schedules")
    from bp_registry.canonical.kernel import BinarySpaKernel

    return schedules.EdgeTable, schedules.FloodingSchedule, BinarySpaKernel


def test_flooding_reads_complete_old_snapshot_then_commits_complete_new_buffer():
    EdgeTable, FloodingSchedule, BinarySpaKernel = _api()
    table = EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])
    schedule = FloodingSchedule(table, kernel=BinarySpaKernel())
    old_v2c = np.array([1.5, -0.7, 0.2, 2.0])

    sweep = schedule.sweep(old_v2c, np.array([0, 1], dtype=np.uint8), error_rate=0.2)

    np.testing.assert_allclose(sweep.old_v2c, old_v2c)
    np.testing.assert_allclose(sweep.check_to_variable, [-0.7, 1.5, -2.0, -0.2])
    np.testing.assert_allclose(sweep.beliefs, [np.log(4.0) - 2.7, np.log(4.0) + 1.3])
    np.testing.assert_allclose(sweep.new_v2c, [np.log(4.0) - 2.0, np.log(4.0) - 0.2, np.log(4.0) - 0.7, np.log(4.0) + 1.5])
    np.testing.assert_array_equal(sweep.candidate, np.array([1, 0], dtype=np.uint8))
    assert sweep.proposed_work.as_evidence() == {
        "check_to_variable": 4,
        "variable_to_check": 4,
        "belief_assembly": 2,
        "candidate_checks": 2,
    }
    assert not np.shares_memory(sweep.old_v2c, old_v2c)
    np.testing.assert_allclose(old_v2c, [1.5, -0.7, 0.2, 2.0])


def test_reverse_input_enumeration_has_one_edge_table_messages_and_work_identity():
    EdgeTable, FloodingSchedule, BinarySpaKernel = _api()
    edges = [(0, 0), (0, 1), (1, 0), (1, 1)]
    forward = EdgeTable.from_edges(2, 2, edges)
    reverse = EdgeTable.from_edges(2, 2, list(reversed(edges)))
    assert forward == reverse
    assert forward.edges == ((0, 0), (0, 1), (1, 0), (1, 1))

    old_v2c = np.array([1.5, -0.7, 0.2, 2.0])
    syndrome = np.array([0, 1], dtype=np.uint8)
    left = FloodingSchedule(forward, kernel=BinarySpaKernel()).sweep(old_v2c, syndrome, error_rate=0.2)
    right = FloodingSchedule(reverse, kernel=BinarySpaKernel()).sweep(old_v2c, syndrome, error_rate=0.2)
    np.testing.assert_allclose(left.check_to_variable, right.check_to_variable)
    np.testing.assert_allclose(left.new_v2c, right.new_v2c)
    np.testing.assert_array_equal(left.candidate, right.candidate)
    assert left.proposed_work == right.proposed_work


def test_empty_and_malformed_graph_encodings_have_defined_pre_mutation_behavior():
    EdgeTable, FloodingSchedule, BinarySpaKernel = _api()
    empty = FloodingSchedule(EdgeTable.from_edges(0, 0, []), kernel=BinarySpaKernel()).sweep(
        np.array([], dtype=np.float64), np.array([], dtype=np.uint8), error_rate=0.2
    )
    assert empty.edge_count == 0
    assert empty.candidate.shape == (0,)
    assert empty.proposed_work.as_evidence() == {
        "check_to_variable": 0,
        "variable_to_check": 0,
        "belief_assembly": 0,
        "candidate_checks": 0,
    }

    with pytest.raises(ValueError, match="duplicate"):
        EdgeTable.from_edges(1, 1, [(0, 0), (0, 0)])
    with pytest.raises(ValueError, match="bounds"):
        EdgeTable.from_edges(1, 1, [(1, 0)])

    schedule = FloodingSchedule(EdgeTable.from_edges(1, 1, [(0, 0)]), kernel=BinarySpaKernel())
    old_v2c = np.array([0.4])
    with pytest.raises(ValueError, match="syndrome"):
        schedule.sweep(old_v2c, np.array([2]), error_rate=0.2)
    np.testing.assert_allclose(old_v2c, [0.4])
