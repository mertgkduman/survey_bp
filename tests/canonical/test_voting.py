"""Coordinate-majority voting must be closed, deterministic, and validated."""

from __future__ import annotations

import numpy as np
import pytest

from bp_registry.canonical.lineage import LineageGraph, LineageId
from bp_registry.canonical.problems import OriginalProblem


def _original() -> OriginalProblem:
    return OriginalProblem(
        "vote-fixture",
        hx=np.zeros((1, 3), dtype=np.uint8),
        hz=np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8),
        syndrome=np.asarray([1, 0], dtype=np.uint8),
    )


def _graph_parent() -> tuple[LineageGraph, LineageId]:
    graph = LineageGraph()
    original = graph.append_node("original", {"sample": "vote-fixture"})
    parent = graph.append_node("attempt", {"ordinal": 0}, parent=original, relation="attempt")
    return graph, parent.id


def _ballots(*bits: tuple[int, ...]):
    from bp_registry.canonical.candidate_selection import VoteBallot

    return tuple(VoteBallot(LineageId("leg", f"leg-member-{index}"), bit) for index, bit in enumerate(bits))


def test_vote_evidence_names_correction_bit_object() -> None:
    from bp_registry.canonical.candidate_selection import CoordinateMajorityVote

    graph, parent = _graph_parent()
    ballots = _ballots((1, 0, 0), (1, 0, 0))
    result = CoordinateMajorityVote(tie_bit=0).vote(
        _original(), graph=graph, parent=parent,
        electorate=tuple(ballot.member_id for ballot in ballots), ballots=ballots,
    )

    assert result.as_evidence()["object"] == "correction_bits"


def test_invalid_coordinate_majority_is_retained_but_never_eligible() -> None:
    from bp_registry.canonical.candidate_selection import CoordinateMajorityVote

    graph, parent = _graph_parent()
    ballots = _ballots((1, 0, 0), (0, 1, 1))
    result = CoordinateMajorityVote(tie_bit=0).vote(
        _original(), graph=graph, parent=parent,
        electorate=tuple(ballot.member_id for ballot in ballots), ballots=ballots,
    )

    assert result.correction == (0, 0, 0)
    assert result.original_valid is False
    assert result.eligible is False
    assert result.as_evidence()["ballots"] == [
        {"correction": [1, 0, 0], "member_id": "leg-member-0"},
        {"correction": [0, 1, 1], "member_id": "leg-member-1"},
    ]


def test_vote_fails_closed_for_incomplete_duplicate_wrong_length_or_nonbinary_ballots() -> None:
    from bp_registry.canonical.candidate_selection import CoordinateMajorityVote, VoteBallot

    graph, parent = _graph_parent()
    member_a = LineageId("leg", "leg-member-a")
    member_b = LineageId("leg", "leg-member-b")
    with pytest.raises(ValueError, match="exactly one ballot"):
        CoordinateMajorityVote(tie_bit=0).vote(
            _original(), graph=graph, parent=parent, electorate=(member_a, member_b),
            ballots=(VoteBallot(member_a, (1, 0, 0)),),
        )
    with pytest.raises(ValueError, match="exactly one ballot"):
        CoordinateMajorityVote(tie_bit=0).vote(
            _original(), graph=graph, parent=parent, electorate=(member_a,),
            ballots=(VoteBallot(member_a, (1, 0, 0)), VoteBallot(member_a, (1, 0, 0))),
        )
    with pytest.raises(ValueError, match="length"):
        CoordinateMajorityVote(tie_bit=0).vote(
            _original(), graph=graph, parent=parent, electorate=(member_a,),
            ballots=(VoteBallot(member_a, (1, 0)),),
        )
    with pytest.raises(ValueError, match="binary"):
        VoteBallot(member_a, (1, 2, 0))
    with pytest.raises(ValueError, match="ineligible"):
        VoteBallot(member_a, (1, 0, 0), eligible=False)


def test_vote_tie_and_worker_order_are_deterministic() -> None:
    from bp_registry.canonical.candidate_selection import CoordinateMajorityVote

    first_graph, first_parent = _graph_parent()
    second_graph, second_parent = _graph_parent()
    ballots = _ballots((1, 0, 0), (0, 1, 1))
    electorate = tuple(ballot.member_id for ballot in ballots)
    first = CoordinateMajorityVote(tie_bit=1).vote(
        _original(), graph=first_graph, parent=first_parent, electorate=electorate, ballots=ballots,
    )
    second = CoordinateMajorityVote(tie_bit=1).vote(
        _original(), graph=second_graph, parent=second_parent, electorate=tuple(reversed(electorate)),
        ballots=tuple(reversed(ballots)),
    )

    assert first.correction == second.correction == (1, 1, 1)
    assert first.as_evidence() == second.as_evidence()
