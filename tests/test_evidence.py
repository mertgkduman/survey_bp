"""Contracts for source-linked records and event-sourced screening."""


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

