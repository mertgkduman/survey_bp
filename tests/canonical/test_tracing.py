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
