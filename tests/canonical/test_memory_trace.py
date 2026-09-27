"""Bounded observation coverage for ordinary-memory sweeps."""

from __future__ import annotations

import numpy as np

from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.schedules import EdgeTable
from bp_registry.canonical.tracing import TracePlan, TraceSink


def _memory():
    return MemoryCompositionSpec.model_validate({"bindings": [{
        "binding_id": "affine", "kind": "affine_prior", "target": "prior",
        "parameters": {"alpha": 0.5}, "order": 0, "history_owner": "history:affine",
        "state_lifetime": "attempt", "advance_boundary": "source_iteration",
        "refresh_boundary": "attempt_start", "source_status": "canonical_adaptation",
    }]})


def test_memory_trace_observes_only_committed_sweeps_and_candidate_origin(tmp_path):
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule

    sink = TraceSink(TracePlan(tmp_path, max_records=4, max_bytes=16_384))
    schedule = MemoryFloodingSchedule(
        EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), kernel=BinarySpaKernel(), memory=_memory(),
        trace_sink=sink, trace_context={"configuration_identity": "arm", "decoder_identity": "shot"},
    )
    initial = schedule.initialize(0.1)
    proposal = schedule.sweep(initial, np.ones(1, dtype=np.uint8), error_rate=0.1)
    assert sink.finish().sidecar_path is None
    # A fresh sink is used because finalization intentionally closes an observer.
    sink = TraceSink(TracePlan(tmp_path, max_records=4, max_bytes=16_384))
    schedule = MemoryFloodingSchedule(
        EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), kernel=BinarySpaKernel(), memory=_memory(),
        trace_sink=sink, trace_context={"configuration_identity": "arm", "decoder_identity": "shot"},
    )
    initial = schedule.initialize(0.1)
    proposal = schedule.sweep(initial, np.ones(1, dtype=np.uint8), error_rate=0.1)
    schedule.commit(proposal)
    schedule.observe_candidate(origin={"candidate_lineage_id": "candidate-0", "status": "diagnostic"}, candidate=proposal.candidate)
    result = sink.finish()
    document = TraceSink.load(tmp_path, result.sidecar_path, expected_sha256=result.sha256)
    assert [record["kind"] for record in document["records"]] == ["memory_sweep", "memory_candidate"]
    payload = document["records"][0]["payload"]
    assert "beliefs" in payload and "history_sha256" in payload and "history_values" in payload
    assert "posterior" in payload["history_values"]["affine"]
    assert "hidden_truth" not in str(document)


def test_memory_trace_caps_are_explicit_and_do_not_change_memory_execution(tmp_path):
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule

    sink = TraceSink(TracePlan(tmp_path, max_records=1, max_bytes=4_096))
    schedule = MemoryFloodingSchedule(
        EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), kernel=BinarySpaKernel(), memory=_memory(),
        trace_sink=sink,
    )
    messages = schedule.initialize(0.1)
    for iteration in range(2):
        proposal = schedule.sweep(messages, np.ones(1, dtype=np.uint8), error_rate=0.1, source_iteration=iteration)
        schedule.commit(proposal)
        messages = proposal.new_v2c
    result = sink.finish()
    assert result.records == 1 and result.truncated and result.dropped_records == 1
    assert schedule.evidence()["committed_iterations"] == 2
