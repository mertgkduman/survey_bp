"""Truth-free MBBP-LD public decisions and structural event projection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from .candidate_selection import CoordinateMajorityVote, VoteBallot, VoteResult
from .lineage import LineageGraph, LineageId
from .mbbp import MbbpBasis, MbbpMember, MbbpResult
from .problems import OriginalProblem


VoteExclusionDisposition = Literal[
    "nonconvergence", "budget_denied", "original_invalid", "missing_candidate",
]


@dataclass(frozen=True)
class VoteExclusion:
    """One declared member that cannot enter the public vote electorate."""

    member_id: str
    local_ordinal: int
    lineage_id: LineageId
    status: str
    disposition: VoteExclusionDisposition
    candidate: tuple[int, ...] | None
    original_valid: bool | None

    def as_evidence(self) -> dict[str, object]:
        return {
            "candidate": None if self.candidate is None else list(self.candidate),
            "disposition": self.disposition,
            "lineage_id": self.lineage_id.value,
            "local_ordinal": self.local_ordinal,
            "member_id": self.member_id,
            "original_valid": self.original_valid,
            "status": self.status,
        }


@dataclass(frozen=True)
class PublicMbbpDecision:
    """Closed list or coordinate-vote terminal over frozen member evidence."""

    branch: Literal["list", "vote"]
    terminal_status: str
    members: tuple[MbbpMember, ...]
    exclusions: tuple[VoteExclusion, ...]
    electorate: tuple[LineageId, ...]
    ballots: tuple[VoteBallot, ...]
    vote: VoteResult | None
    selected_candidate: tuple[int, ...] | None
    selected_origin_id: LineageId | None
    source_zero_return: tuple[int, ...] | None

    @property
    def original_valid(self) -> bool | None:
        return None if self.vote is None else self.vote.original_valid

    def as_evidence(self) -> dict[str, object]:
        return {
            "ballots": [{"correction": list(ballot.correction), "member_id": ballot.member_id.value}
                        for ballot in self.ballots],
            "branch": self.branch,
            "electorate": [member.value for member in self.electorate],
            "exclusions": [exclusion.as_evidence() for exclusion in self.exclusions],
            "members": [member.as_evidence() for member in self.members],
            "original_valid": self.original_valid,
            "selected_candidate": None if self.selected_candidate is None else list(self.selected_candidate),
            "selected_origin_id": None if self.selected_origin_id is None else self.selected_origin_id.value,
            "source_zero_return": None if self.source_zero_return is None else list(self.source_zero_return),
            "terminal_status": self.terminal_status,
            "vote": None if self.vote is None else self.vote.as_evidence(),
        }


def _exclusion(member: MbbpMember) -> VoteExclusion:
    if member.status == "budget_denied":
        disposition: VoteExclusionDisposition = "budget_denied"
    elif member.status == "converged_original_invalid" or member.original_valid is False:
        disposition = "original_invalid"
    elif member.candidate is None:
        disposition = "missing_candidate"
    else:
        disposition = "nonconvergence"
    return VoteExclusion(member.member_id, member.local_ordinal, member.lineage_id, member.status,
                         disposition, member.candidate, member.original_valid)


def _vote_parent(original: OriginalProblem, electorate: tuple[LineageId, ...]) -> tuple[LineageGraph, LineageId]:
    """Make deterministic logical ancestry for the aggregate, without truth data."""
    graph = LineageGraph()
    root = graph.append_node("original", {"original_lineage_id": original.lineage_id, "syndrome": original.syndrome.tolist()})
    working = graph.append_node("working", {"object": "original_correction_bits"}, parent=root, relation="identity")
    attempt = graph.append_node("attempt", {"aggregation": "coordinate_majority", "electorate": [member.value for member in electorate]}, parent=working, relation="attempt")
    return graph, attempt.id


def execute_declared_mbbp_decision(original: OriginalProblem, *, result: MbbpResult,
                                   vote_tie_bit: int | None) -> PublicMbbpDecision:
    """Choose a declared list or vote terminal from immutable member terminals."""
    if not isinstance(original, OriginalProblem) or not isinstance(result, MbbpResult):
        raise ValueError("public MBBP decisions require immutable original and frozen result values")
    members = tuple(sorted(result.members, key=lambda member: (member.local_ordinal, member.member_id)))
    if vote_tie_bit is None:
        return PublicMbbpDecision("list", result.terminal_status, members, (), (), (), None,
                                  result.selected_candidate, result.selected_origin_id, result.source_zero_return)
    if type(vote_tie_bit) is not int or vote_tie_bit not in (0, 1):
        raise ValueError("declared coordinate-majority vote requires tie bit zero or one")
    admitted = tuple(member for member in members if member.admitted)
    exclusions = tuple(_exclusion(member) for member in members if not member.admitted)
    electorate = tuple(sorted((member.lineage_id for member in admitted), key=lambda identifier: identifier.value))
    ballots = tuple(sorted((VoteBallot(member.lineage_id, member.candidate) for member in admitted if member.candidate is not None), key=lambda ballot: ballot.member_id.value))
    if not electorate:
        return PublicMbbpDecision("vote", "no_eligible_vote_candidate", members, exclusions, electorate, ballots,
                                  None, None, None, None)
    graph, parent = _vote_parent(original, electorate)
    vote = CoordinateMajorityVote(tie_bit=vote_tie_bit).vote(original, graph=graph, parent=parent,
                                                               electorate=electorate, ballots=ballots)
    if not vote.original_valid:
        return PublicMbbpDecision("vote", "vote_aggregate_original_invalid", members, exclusions,
                                  vote.electorate, vote.ballots, vote, None, None, None)
    return PublicMbbpDecision("vote", "vote_selected_original_valid_candidate", members, exclusions,
                              vote.electorate, vote.ballots, vote, vote.correction, vote.candidate_lineage_id, None)


@dataclass(frozen=True)
class Phase6Projection:
    """Ordered public facts; evaluation remains outside this projection."""

    terminal: str
    events: tuple[tuple[str, Mapping[str, Any]], ...]
    candidate: tuple[int, ...] | None


_LEDGER_KIND = {
    "basis": "transform", "member": "attempt", "candidate_origin": "candidate",
    "duplicate_group": "branch", "selection": "selection", "original_check": "original_check",
    "work_leaf": "work", "vote_electorate": "branch", "vote_exclusion": "branch",
    "vote_ballot": "candidate", "vote_aggregate": "candidate", "vote_validation": "original_check",
}


def phase6_ledger_kind(kind: str) -> str:
    """Encode an explicit Phase 6 event type in the compatible ledger envelope."""
    return _LEDGER_KIND[kind]


def phase6_events(original: OriginalProblem, *, bases: tuple[MbbpBasis, ...], result: MbbpResult,
                  vote_tie_bit: int | None = None) -> Phase6Projection:
    """Project all frozen members into list or declared-vote public evidence."""
    events: list[tuple[str, Mapping[str, Any]]] = [
        ("header", {"original_lineage_id": original.lineage_id, "syndrome": original.syndrome.tolist(),
                    "source_status": result.source_status}),
    ]
    augmented = {basis.member_id: basis.augment(original) for basis in bases}
    for basis in bases:
        events.append(("basis", augmented[basis.member_id].as_evidence()))
    decision = execute_declared_mbbp_decision(original, result=result, vote_tie_bit=vote_tie_bit)
    for member in decision.members:
        events.append(("member", member.as_evidence()))
    if decision.branch == "list":
        for origin in result.selection.origins:
            events.append(("candidate_origin", origin.as_evidence()))
        for group in result.selection.duplicate_groups:
            events.append(("duplicate_group", group.as_evidence()))
        if decision.selected_candidate is not None:
            events.append(("selection", result.selection.as_evidence()))
            events.append(("original_check", {"candidate": list(decision.selected_candidate), "valid": True,
                                                "selected_origin_id": decision.selected_origin_id.value if decision.selected_origin_id else None}))
    else:
        for exclusion in decision.exclusions:
            events.append(("vote_exclusion", exclusion.as_evidence()))
        events.append(("vote_electorate", {"aggregation": "coordinate_majority",
                       "electorate": [member.value for member in decision.electorate],
                       "object": "correction_bits", "tie_bit": vote_tie_bit}))
        for ballot in decision.ballots:
            events.append(("vote_ballot", {"correction": list(ballot.correction), "member_id": ballot.member_id.value}))
        if decision.vote is not None:
            vote_evidence = decision.vote.as_evidence()
            events.append(("vote_aggregate", {"candidate_lineage_id": vote_evidence["candidate_lineage_id"],
                           "correction": vote_evidence["correction"], "vote_lineage_id": vote_evidence["vote_lineage_id"]}))
            events.append(("vote_validation", {"eligible": decision.vote.eligible,
                           "original_valid": decision.vote.original_valid, "vote_lineage_id": decision.vote.lineage_id.value}))
    for leaf_id, scope, work in result.work_leaves:
        events.append(("work_leaf", {"leaf_id": leaf_id, "scope": scope,
                                      "work_vector": work.as_evidence(structural_event_version=4)}))
    terminal: dict[str, Any] = {
        "terminal_status": decision.terminal_status,
        "work_vector": result.work.as_evidence(structural_event_version=4),
    }
    if decision.branch == "vote":
        terminal.update({"candidate": None if decision.selected_candidate is None else list(decision.selected_candidate),
                         "selected_origin_id": None if decision.selected_origin_id is None else decision.selected_origin_id.value,
                         "vote": None if decision.vote is None else decision.vote.as_evidence()})
    elif decision.terminal_status == "no_member_converged_zero_return":
        terminal["source_zero_return"] = list(decision.source_zero_return or ())
        terminal["selection"] = None
    else:
        terminal["selected_origin_id"] = None if decision.selected_origin_id is None else decision.selected_origin_id.value
        terminal["candidate"] = None if decision.selected_candidate is None else list(decision.selected_candidate)
    events.append(("termination", terminal))
    return Phase6Projection(decision.terminal_status, tuple(events), decision.selected_candidate)
