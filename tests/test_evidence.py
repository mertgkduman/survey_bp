"""Contracts for source-linked records and event-sourced screening."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest


def test_source_claim_has_revision_and_anchor():
    from bp_registry import evidence

    claim = evidence.Claim(
        work_id="bpgd", revision_id="v2", anchor="Figure 2",
        statement="A curve uses the declared CSS setting",
    )
    assert claim.work_id == "bpgd"
    assert claim.revision_id == "v2"
    assert claim.anchor == "Figure 2"


def test_duplicate_source_event_does_not_duplicate_history():
    from bp_registry import evidence

    event = {"event_id": "search-1", "kind": "search", "query": "belief propagation"}
    history = evidence.replay_events([event, event])
    assert len(history) == 1
    assert history[0]["event_id"] == "search-1"


def test_conflicting_revision_decisions_are_preserved():
    from bp_registry import evidence

    events = [
        {"event_id": "d1", "kind": "decision", "work_id": "w", "decision": "include"},
        {"event_id": "d2", "kind": "decision", "work_id": "w", "decision": "exclude"},
    ]
    assert [e["decision"] for e in evidence.replay_events(events)] == ["include", "exclude"]


def test_protocol_has_reproducible_mapping_fields():
    protocol_path = Path("data/evidence/protocol.json")
    assert protocol_path.exists(), "versioned evidence protocol must be present"
    from bp_registry import evidence

    protocol = json.loads(protocol_path.read_text())
    evidence.validate_protocol(protocol)
    assert protocol["research_questions"]
    assert protocol["searches"]
    assert protocol["screening"]["title_and_abstract"]
    assert protocol["screening"]["full_text"]
    assert protocol["adjudication"]
    assert protocol["snowballing"]
    assert protocol["extraction_dictionary"]
    assert protocol["update_rule"]


def test_search_import_preserves_adjacent_raw_hits_and_empty_search(tmp_path):
    from bp_registry import evidence

    event_path = tmp_path / "events.jsonl"
    registry = evidence.EvidenceRegistry(event_path)
    event = {
        "kind": "search",
        "source_uri": "https://export.arxiv.org/api/query",
        "query": 'all:"guided decimation"',
        "cutoff": "2026-09-21",
        "raw_hits": [
            {"raw_hit_id": "a-1", "normalized_work_id": "work-a", "revision_id": "v1"},
            {"raw_hit_id": "a-2", "normalized_work_id": "work-a", "revision_id": "v2"},
        ],
        "timestamp": "2026-09-21T00:00:00Z",
    }
    imported = registry.import_search_event(event)
    assert [hit["raw_hit_id"] for hit in imported["raw_hits"]] == ["a-1", "a-2"]
    assert registry.works["work-a"]["revision_ids"] == ["v1", "v2"]

    empty = registry.import_search_event(
        {
            "kind": "search",
            "source_uri": "https://export.arxiv.org/api/query",
            "query": 'all:"not-a-claimed-result"',
            "cutoff": "2026-09-21",
            "raw_hits": [],
            "timestamp": "2026-09-21T00:01:00Z",
        }
    )
    assert empty["raw_hits"] == []
    assert [record["query"] for record in registry.history()] == [
        'all:"guided decimation"',
        'all:"not-a-claimed-result"',
    ]


def test_repeated_and_concurrent_identical_imports_are_idempotent(tmp_path):
    from bp_registry import evidence

    registry = evidence.EvidenceRegistry(tmp_path / "events.jsonl")
    event = {
        "event_id": "stable-search-event",
        "kind": "search",
        "source_uri": "https://export.arxiv.org/api/query",
        "query": "same query",
        "cutoff": "2026-09-21",
        "raw_hits": [],
        "timestamp": "2026-09-21T00:00:00Z",
    }
    with ThreadPoolExecutor(max_workers=8) as pool:
        events = list(pool.map(registry.import_search_event, [event] * 8))
    assert {record["event_id"] for record in events} == {"stable-search-event"}
    assert len(registry.history()) == 1


def test_same_event_id_with_different_content_is_a_conflict(tmp_path):
    from bp_registry import evidence

    registry = evidence.EvidenceRegistry(tmp_path / "events.jsonl")
    registry.import_search_event(
        {
            "event_id": "conflict",
            "kind": "search",
            "source_uri": "https://example.org",
            "query": "first",
            "cutoff": "2026-09-21",
            "raw_hits": [],
            "timestamp": "2026-09-21T00:00:00Z",
        }
    )
    with pytest.raises(evidence.EventConflictError):
        registry.import_search_event(
            {
                "event_id": "conflict",
                "kind": "search",
                "source_uri": "https://example.org",
                "query": "changed",
                "cutoff": "2026-09-21",
                "raw_hits": [],
                "timestamp": "2026-09-21T00:00:00Z",
            }
        )


def test_screening_history_reloads_in_original_order(tmp_path):
    from bp_registry import evidence

    event_path = tmp_path / "events.jsonl"
    registry = evidence.EvidenceRegistry(event_path)
    registry.screen("work-a", "v1", stage="title_and_abstract", decision="include", reason="scope")
    registry.screen("work-a", "v2", stage="full_text", decision="include", reason="CSS evidence")
    registry.screen("work-b", "v1", stage="title_and_abstract", decision="exclude", reason="not BP")

    reloaded = evidence.EvidenceRegistry(event_path)
    assert [(event["work_id"], event["revision_id"], event["decision"]) for event in reloaded.history()] == [
        ("work-a", "v1", "include"),
        ("work-a", "v2", "include"),
        ("work-b", "v1", "exclude"),
    ]
