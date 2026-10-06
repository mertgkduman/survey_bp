"""Terminal-snapshot contracts shared by optional Phase 7 processors."""

from __future__ import annotations

import numpy as np
import pytest


def _working():
    from bp_registry.canonical.lineage import LineageEdge, LineageId
    from bp_registry.canonical.problems import OriginalProblem, WorkingProblem

    original = OriginalProblem(
        "handoff-original",
        np.zeros((1, 3), dtype=np.uint8),
        np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8),
        np.asarray([1, 0], dtype=np.uint8),
    )
    return WorkingProblem(
        "handoff-working", original,
        LineageEdge("identity", LineageId("original", original.lineage_id), LineageId("working", "handoff-working")),
    )


def _failed_attempt(*, candidate=(0, 0, 0), beliefs=(1.0, -2.0, 3.0), converged=False):
    from bp_registry.canonical.execution import AtomicFloodingResult
    from bp_registry.canonical.schedules import FloodingSweep, FloodingWork

    sweep = FloodingSweep(
        edge_count=3,
        old_v2c=np.zeros(3, dtype=np.float64),
        check_to_variable=np.zeros(3, dtype=np.float64),
        new_v2c=np.zeros(3, dtype=np.float64),
        beliefs=np.asarray(beliefs, dtype=np.float64),
        candidate=np.asarray(candidate, dtype=np.uint8),
        proposed_work=FloodingWork(1, 1, 3, 3),
    )
    return AtomicFloodingResult(np.zeros(3, dtype=np.float64), 1, None, sweep, converged)


def test_single_attempt_freezes_immutable_terminal_snapshot_before_fallback():
    from bp_registry.canonical import postprocessing

    assert hasattr(postprocessing, "adapt_flooding_attempt"), "the flooding handoff adapter must be public"
    adapt_flooding_attempt = postprocessing.adapt_flooding_attempt

    result = adapt_flooding_attempt(
        _failed_attempt(), working=_working(), error_rate=0.1,
        attempt_lineage_id="attempt-0", declared_attempt_ordinal=0,
    )

    assert result.disposition == "compatible"
    assert result.reason is None
    assert len(result.snapshots) == 1
    snapshot = result.snapshots[0]
    assert snapshot.candidate.tolist() == [0, 0, 0]
    assert snapshot.posterior_llr.tolist() == [1.0, -2.0, 3.0]
    assert snapshot.candidate.flags.writeable is False
    assert snapshot.posterior_llr.flags.writeable is False
    assert snapshot.original_residual_weight == 1
    assert snapshot.termination == "iteration_cap"
    assert snapshot.transform_identity == "identity"


@pytest.mark.parametrize("beliefs, reason", [((1.0, np.nan, 3.0), "nonfinite_terminal_posterior"), ((1.0, 2.0), "terminal_posterior_shape_mismatch")])
def test_single_attempt_marks_unusable_terminal_reliability_incompatible(beliefs, reason):
    from bp_registry.canonical.postprocessing import adapt_flooding_attempt

    result = adapt_flooding_attempt(
        _failed_attempt(beliefs=beliefs), working=_working(), error_rate=0.1,
        attempt_lineage_id="attempt-0", declared_attempt_ordinal=0,
    )

    assert result.disposition == "incompatible"
    assert result.reason == reason
    assert result.snapshots == ()


def test_single_attempt_original_validity_suppresses_fallback_and_hidden_truth_is_not_an_input():
    from bp_registry.canonical.postprocessing import adapt_flooding_attempt

    result = adapt_flooding_attempt(
        _failed_attempt(candidate=(0, 1, 0), converged=True), working=_working(), error_rate=0.1,
        attempt_lineage_id="attempt-0", declared_attempt_ordinal=0,
    )

    assert result.disposition == "composition_success"
    assert result.snapshots == ()
    assert result.reason == "original_valid_bp_candidate"
