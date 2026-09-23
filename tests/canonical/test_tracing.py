"""Durable lineage and semantic-observation contracts for canonical CSS runs."""

from __future__ import annotations

import numpy as np
import pytest


def test_lineage_graph_rejects_mutation_conflicts_and_invalid_parent_edges():
    from bp_registry.canonical.lineage import LineageGraph, stable_lineage_id

    graph = LineageGraph()
    original = graph.append_node("original", {"sample": "seed-a"})
    working = graph.append_node("working", {"lift": "identity"}, parent=original, relation="transform")
    attempt = graph.append_node("attempt", {"binding": "attempt-0"}, parent=working, relation="attempt")
    candidate = graph.append_node("candidate", {"ordinal": 0, "bits": [1, 0]}, parent=attempt, relation="candidate")
    validation = graph.append_node("validation", {"valid": True}, parent=candidate, relation="validate")
    selection = graph.append_node("selection", {"selected": candidate.id.value}, parent=validation, relation="select")
    evaluation = graph.append_node("evaluation", {"outcome": "success"}, parent=selection, relation="evaluate")

    assert [node.kind for node in graph.nodes()] == [
        "original", "working", "attempt", "candidate", "validation", "selection", "evaluation",
    ]
    assert graph.parents(candidate.id) == (attempt.id,)
    assert graph.parents(evaluation.id) == (selection.id,)
    with pytest.raises(ValueError, match="conflicting immutable lineage node"):
        graph.append_node("candidate", {"ordinal": 1}, node_id=candidate.id)
    with pytest.raises(ValueError, match="not allowed"):
        graph.append_node("candidate", {"bits": [0]}, parent=original, relation="candidate")
    with pytest.raises(ValueError, match="unknown parent"):
        graph.append_node("working", {}, parent=stable_lineage_id("original", {"other": 1}), relation="transform")


def test_lineage_ids_are_semantic_not_timing_or_append_order():
    from bp_registry.canonical.lineage import LineageGraph

    left, right = LineageGraph(), LineageGraph()
    left_original = left.append_node("original", {"syndrome": [1, 0]})
    left_working = left.append_node("working", {"binding": "identity", "local_ordinal": 0}, parent=left_original, relation="transform")
    left_candidate = left.append_node("candidate", {"binding": "select", "local_ordinal": 2, "bits": [0, 1]}, parent=left_working, relation="candidate")

    right_original = right.append_node("original", {"syndrome": [1, 0]})
    # An unrelated sibling may arrive first without perturbing the candidate identity.
    right.append_node("working", {"binding": "identity", "local_ordinal": 1}, parent=right_original, relation="transform")
    right_working = right.append_node("working", {"binding": "identity", "local_ordinal": 0}, parent=right_original, relation="transform")
    right_candidate = right.append_node("candidate", {"binding": "select", "local_ordinal": 2, "bits": [0, 1]}, parent=right_working, relation="candidate")

    assert left_candidate.id == right_candidate.id


def test_candidate_retention_keeps_rejected_evidence_and_selected_payload():
    from bp_registry.canonical.lineage import CandidateRecord, LineageGraph, SelectionRecord

    graph = LineageGraph()
    original = graph.append_node("original", {"sample": "seed"})
    attempt = graph.append_node("attempt", {"binding": "b", "local_ordinal": 0}, parent=original, relation="attempt")
    selected = CandidateRecord.create(
        graph=graph, parent=attempt.id, payload=np.array([1, 0], dtype=np.uint8),
        score=1.5, validations=("syndrome_match",), reason="best", local_ordinal=0,
    )
    rejected = CandidateRecord.create(
        graph=graph, parent=attempt.id, payload=np.array([0, 0], dtype=np.uint8),
        score=0.5, validations=("syndrome_match",), reason="lower_score", local_ordinal=1,
    )
    record = SelectionRecord.freeze(graph=graph, candidates=(selected, rejected), selected_id=selected.lineage_id)

    assert record.selected_id == selected.lineage_id
    assert selected.retained_payload == (1, 0)
    assert rejected.retained_payload is None
    assert rejected.payload_sha256 and rejected.score == 0.5
    assert rejected.validations == ("syndrome_match",)
    assert rejected.reason == "lower_score"
    with pytest.raises(ValueError, match="frozen selection"):
        record.annotate_evaluation({"truth_outcome": "success"})
    annotation = graph.append_evaluation(record, {"truth_outcome": "success"})
    assert annotation.parents == (record.lineage_id,)
    assert record.selected_id == selected.lineage_id
    assert tuple(item.lineage_id for item in record.candidates) == (selected.lineage_id, rejected.lineage_id)


def test_candidate_payload_rejects_coercion_and_nonvectors():
    from bp_registry.canonical.lineage import CandidateRecord, LineageGraph

    graph = LineageGraph()
    original = graph.append_node("original", {"sample": "seed"})
    attempt = graph.append_node(
        "attempt", {"ordinal": 0}, parent=original, relation="attempt",
    )
    invalid_payloads = (
        np.array([0.0, 1.0]),
        np.array(["0", "1"]),
        np.array([False, True]),
        np.array([0, 2], dtype=np.int64),
        np.array(1, dtype=np.int64),
        np.array([[0, 1]], dtype=np.int64),
    )

    for payload in invalid_payloads:
        with pytest.raises(
            ValueError, match="one-dimensional non-boolean integer binary vector",
        ):
            CandidateRecord.create(
                graph=graph,
                parent=attempt.id,
                payload=payload,
                score=None,
                validations=(),
                reason="invalid-input",
                local_ordinal=0,
            )


def test_sparse_canonical_events_remain_when_semantic_tracing_is_off_or_empty(tmp_path):
    from bp_registry.ledger import (
        CanonicalEventWriter,
        ShotOwnershipError,
        query_canonical_events,
        read_canonical_events,
    )
    from bp_registry.canonical.tracing import TracePlan, TraceSink

    trace = TraceSink(TracePlan.disabled(tmp_path))
    assert trace.finish().sidecar_path is None
    with CanonicalEventWriter(tmp_path / "canonical.jsonl") as writer:
        writer.begin(run_id="canonical", shot_id=2, sample_seed_identity="sample-a")
        writer.event(run_id="canonical", shot_id=2, kind="attempt", data={"lineage_id": "attempt-a"})
        writer.event(run_id="canonical", shot_id=2, kind="candidate", data={"lineage_id": "candidate-a"})
        writer.event(run_id="canonical", shot_id=2, kind="selection", data={"candidate_id": "candidate-a"})
        writer.terminal(run_id="canonical", shot_id=2, termination="completed", data={"semantic_digest": "a" * 64})
    assert [event["kind"] for event in read_canonical_events(tmp_path / "canonical.jsonl")] == [
        "shot_begin", "attempt", "candidate", "selection", "termination",
    ]
    assert [event["kind"] for event in query_canonical_events(tmp_path / "canonical.jsonl", run_id="canonical", kind="candidate")] == ["candidate"]
    with CanonicalEventWriter(tmp_path / "bad-order.jsonl") as writer:
        with pytest.raises(ShotOwnershipError, match="not owned"):
            writer.event(run_id="canonical", shot_id=3, kind="attempt")


def test_semantic_trace_filters_and_explicitly_truncates_without_control_flow(tmp_path):
    from bp_registry.canonical.tracing import TracePlan, TraceSink

    plan = TracePlan(root=tmp_path, level="filtered", iterations=frozenset({2}), edges=frozenset({"e-1"}), max_records=1, max_bytes=4_096)
    sink = TraceSink(plan)
    sink.observe(kind="iteration", iteration=1, payload={"belief": [0.0, 1.0]})
    sink.observe(kind="edge", iteration=2, edge="e-1", payload={"message": np.array([1, 0], dtype=np.uint8)})
    sink.observe(kind="edge", iteration=2, edge="e-1", payload={"message": np.array([0, 1], dtype=np.uint8)})
    result = sink.finish()

    assert result.truncated is True and result.dropped_records == 1
    assert result.records == 1 and result.sidecar_path is not None
    assert TraceSink.load(tmp_path, result.sidecar_path, expected_sha256=result.sha256)["records"][0]["edge"] == "e-1"


def test_byte_cap_persists_a_truncation_fact_even_when_no_optional_record_fits(tmp_path):
    from bp_registry.canonical.tracing import TracePlan, TraceSink

    sink = TraceSink(TracePlan(root=tmp_path, max_records=10, max_bytes=256))
    sink.observe(kind="iteration", iteration=0, payload={"large": "x" * 512})
    result = sink.finish()

    assert result.records == 0 and result.truncated is True and result.sidecar_path is not None
    loaded = TraceSink.load(tmp_path, result.sidecar_path, expected_sha256=result.sha256)
    assert loaded["truncated"] is True and loaded["dropped_records"] == 1


def test_sidecars_reject_escaping_paths_bad_payloads_and_hash_mismatches(tmp_path):
    from bp_registry.canonical.tracing import TracePlan, TraceSink

    with pytest.raises(ValueError, match="relative"):
        TracePlan(root=tmp_path, relative_dir="../escape")
    sink = TraceSink(TracePlan(root=tmp_path, max_records=3, max_bytes=4_096))
    with pytest.raises(ValueError, match="finite"):
        sink.observe(kind="iteration", iteration=0, payload={"bad": float("nan")})
    sink.observe(kind="iteration", iteration=0, payload={"typed": np.array([[1, 2]], dtype=np.int16)})
    result = sink.finish()
    assert result.sidecar_path is not None
    with pytest.raises(ValueError, match="SHA-256"):
        TraceSink.load(tmp_path, result.sidecar_path, expected_sha256="0" * 64)
    sidecar = tmp_path / result.sidecar_path
    sidecar.write_bytes(b"\xffnot-utf8")
    with pytest.raises(ValueError, match="UTF-8 JSON"):
        TraceSink.load(tmp_path, result.sidecar_path)
