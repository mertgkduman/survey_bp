"""Deterministic, truth-free candidate selection and coordinate voting.

Candidate policies receive only candidates expressed in the original problem
coordinates and decoder-visible provenance.  Original-syndrome validation is
recorded independently and only gates admission after a list or vote has been
frozen; hidden physical errors never enter this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import math
from typing import ClassVar, Iterable

import numpy as np

from .lineage import LineageGraph, LineageId, stable_lineage_id
from .problems import OriginalProblem


def _binary_tuple(value: Iterable[int], *, name: str) -> tuple[int, ...]:
    result = tuple(value)
    if not result or any(type(bit) is not int or bit not in (0, 1) for bit in result):
        raise ValueError(f"{name} must be a nonempty binary tuple")
    return result


def _digest(bits: tuple[int, ...]) -> str:
    return sha256(json.dumps(bits, separators=(",", ":")).encode("utf-8")).hexdigest()


def _original_valid(original: OriginalProblem, candidate: tuple[int, ...]) -> bool:
    if len(candidate) != original.hz.shape[1]:
        raise ValueError("candidate length differs from the immutable original problem")
    observed = (original.hz.astype(np.int64) @ np.asarray(candidate, dtype=np.int64)) % 2
    return bool(np.array_equal(observed.astype(np.uint8), original.syndrome))


def _stable_key(lineage_id: LineageId, local_ordinal: int) -> tuple[int, str]:
    return (local_ordinal, lineage_id.value)


@dataclass(frozen=True)
class CandidateOrigin:
    """One declared origin, retained whether it can ultimately be selected."""

    lineage_id: LineageId
    local_ordinal: int
    candidate: tuple[int, ...] | None
    eligible: bool
    reason: str
    candidate_digest: str | None = field(init=False)

    def __post_init__(self) -> None:
        if type(self.local_ordinal) is not int or self.local_ordinal < 0:
            raise ValueError("origin local ordinal must be a nonnegative integer")
        if not isinstance(self.eligible, bool) or not isinstance(self.reason, str) or not self.reason:
            raise ValueError("origin eligibility must be boolean and reason must be nonempty")
        if self.candidate is None:
            if self.eligible:
                raise ValueError("candidate-less origins cannot be eligible")
            object.__setattr__(self, "candidate_digest", None)
            return
        bits = _binary_tuple(self.candidate, name="origin candidate")
        object.__setattr__(self, "candidate", bits)
        object.__setattr__(self, "candidate_digest", _digest(bits))


class CandidateScorePolicy:
    """A registered score rule with an explicit optimization direction."""

    name: ClassVar[str]
    higher_is_better: ClassVar[bool]

    def score(self, origin: CandidateOrigin, frequency: int) -> float:
        raise NotImplementedError


class StableFirstScore(CandidateScorePolicy):
    name = "stable_first"
    higher_is_better = False

    def score(self, origin: CandidateOrigin, frequency: int) -> float:
        return 0.0


class MinimumOriginalWeightScore(CandidateScorePolicy):
    name = "minimum_original_weight"
    higher_is_better = False

    def score(self, origin: CandidateOrigin, frequency: int) -> float:
        assert origin.candidate is not None
        return float(sum(origin.candidate))


class FrequencyOverWeightScore(CandidateScorePolicy):
    name = "frequency_over_weight_plus_one"
    higher_is_better = True

    def score(self, origin: CandidateOrigin, frequency: int) -> float:
        assert origin.candidate is not None
        if type(frequency) is not int or frequency < 1:
            raise ValueError("candidate frequency must be a positive integer")
        return float(frequency / (sum(origin.candidate) + 1))


_SCORE_POLICIES: dict[str, CandidateScorePolicy] = {}


def register_score_policy(policy: CandidateScorePolicy) -> CandidateScorePolicy:
    if not isinstance(policy.name, str) or not policy.name or type(policy.higher_is_better) is not bool:
        raise ValueError("score policy requires a name and explicit optimization direction")
    if policy.name in _SCORE_POLICIES:
        raise ValueError(f"score policy already registered: {policy.name}")
    _SCORE_POLICIES[policy.name] = policy
    return policy


def score_policy(name: str) -> CandidateScorePolicy:
    try:
        return _SCORE_POLICIES[name]
    except KeyError as error:
        raise ValueError(f"unknown candidate score policy: {name}") from error


for _policy in (StableFirstScore(), MinimumOriginalWeightScore(), FrequencyOverWeightScore()):
    register_score_policy(_policy)


@dataclass(frozen=True)
class FrozenOrigin:
    """An origin after independent original-syndrome validation and scoring."""

    source: CandidateOrigin
    original_valid: bool | None
    score: float | None
    frequency: int

    @property
    def lineage_id(self) -> LineageId:
        return self.source.lineage_id

    @property
    def local_ordinal(self) -> int:
        return self.source.local_ordinal

    @property
    def candidate_digest(self) -> str | None:
        return self.source.candidate_digest

    @property
    def candidate(self) -> tuple[int, ...] | None:
        return self.source.candidate

    @property
    def reason(self) -> str:
        return self.source.reason

    @property
    def eligible(self) -> bool:
        return self.source.eligible and self.candidate is not None and self.original_valid is True

    def as_evidence(self) -> dict[str, object]:
        return {
            "candidate": None if self.candidate is None else list(self.candidate),
            "candidate_digest": self.candidate_digest,
            "eligible": self.eligible,
            "frequency": self.frequency,
            "lineage_id": self.lineage_id.value,
            "local_ordinal": self.local_ordinal,
            "original_valid": self.original_valid,
            "reason": self.reason,
            "score": self.score,
            "source_eligible": self.source.eligible,
        }


@dataclass(frozen=True)
class DuplicateGroup:
    """A payload grouping that preserves each distinct source origin."""

    candidate_digest: str
    member_origin_ids: tuple[LineageId, ...]

    @property
    def frequency(self) -> int:
        return len(self.member_origin_ids)

    def as_evidence(self) -> dict[str, object]:
        return {"candidate_digest": self.candidate_digest, "frequency": self.frequency,
                "member_origin_ids": [item.value for item in self.member_origin_ids]}


@dataclass(frozen=True)
class FrozenCandidateSelection:
    """A fully retained candidate list and its stable, decoder-visible choice."""

    lineage_id: LineageId
    score_policy: str
    origins: tuple[FrozenOrigin, ...]
    duplicate_groups: tuple[DuplicateGroup, ...]
    selected_origin_id: LineageId | None

    def as_evidence(self) -> dict[str, object]:
        return {
            "duplicate_groups": [group.as_evidence() for group in self.duplicate_groups],
            "origins": [origin.as_evidence() for origin in self.origins],
            "score_policy": self.score_policy,
            "selected_origin_id": None if self.selected_origin_id is None else self.selected_origin_id.value,
            "selection_lineage_id": self.lineage_id.value,
        }

    def as_evidence_bytes(self) -> bytes:
        return json.dumps(self.as_evidence(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _complete_declared_origins(declared_origins: tuple[LineageId, ...], origins: tuple[CandidateOrigin, ...]) -> None:
    declared = tuple(declared_origins)
    observed = tuple(origin.lineage_id for origin in origins)
    if (len(set(declared)) != len(declared) or len(set(observed)) != len(observed)
            or set(declared) != set(observed)):
        raise ValueError("declared origin set must be complete and duplicate-free")


def _duplicate_groups(origins: tuple[FrozenOrigin, ...]) -> tuple[DuplicateGroup, ...]:
    """Group only admitted original-valid payloads for frequency-based scores.

    Disqualified duplicates stay in ``FrozenCandidateSelection.origins`` but
    cannot increase the score of an admitted member.
    """
    buckets: dict[str, list[FrozenOrigin]] = {}
    for origin in origins:
        if origin.source.eligible and origin.original_valid is True and origin.candidate_digest is not None:
            buckets.setdefault(origin.candidate_digest, []).append(origin)
    groups = [DuplicateGroup(
        candidate_digest=digest,
        member_origin_ids=tuple(item.lineage_id for item in sorted(members, key=lambda item: _stable_key(item.lineage_id, item.local_ordinal))),
    ) for digest, members in buckets.items()]
    return tuple(sorted(groups, key=lambda group: _stable_key(
        next(item for item in origins if item.lineage_id == group.member_origin_ids[0]).lineage_id,
        next(item for item in origins if item.lineage_id == group.member_origin_ids[0]).local_ordinal,
    )))


def freeze_candidate_list(
    original: OriginalProblem,
    *,
    declared_origins: tuple[LineageId, ...],
    origins: tuple[CandidateOrigin, ...],
    score_policy: CandidateScorePolicy,
) -> FrozenCandidateSelection:
    """Freeze a complete list before selection using only decoder-visible facts."""
    _complete_declared_origins(declared_origins, origins)
    if not isinstance(score_policy, CandidateScorePolicy):
        raise ValueError("candidate score policy must use the typed policy base")
    ordered = tuple(sorted(origins, key=lambda item: _stable_key(item.lineage_id, item.local_ordinal)))
    prevalidated = tuple(FrozenOrigin(
        origin,
        None if origin.candidate is None else _original_valid(original, origin.candidate),
        None,
        0,
    ) for origin in ordered)
    groups = _duplicate_groups(prevalidated)
    frequencies = {member.value: group.frequency for group in groups for member in group.member_origin_ids}
    frozen: list[FrozenOrigin] = []
    for origin in prevalidated:
        if not origin.eligible:
            frozen.append(origin)
            continue
        frequency = frequencies[origin.lineage_id.value]
        score = score_policy.score(origin.source, frequency)
        if not isinstance(score, (int, float)) or not math.isfinite(score):
            raise ValueError("nonfinite candidate score is forbidden")
        frozen.append(FrozenOrigin(
            origin.source, origin.original_valid, float(score), frequency,
        ))
    selected = min(
        (item for item in frozen if item.eligible),
        key=lambda item: ((-item.score if score_policy.higher_is_better else item.score),
                          item.local_ordinal, item.lineage_id.value),
        default=None,
    )
    payload = {
        "origins": [item.as_evidence() for item in frozen],
        "score_policy": score_policy.name,
        "selected_origin_id": None if selected is None else selected.lineage_id.value,
    }
    return FrozenCandidateSelection(
        lineage_id=stable_lineage_id("selection", payload), score_policy=score_policy.name,
        origins=tuple(frozen), duplicate_groups=groups,
        selected_origin_id=None if selected is None else selected.lineage_id,
    )


@dataclass(frozen=True)
class VoteBallot:
    """Exactly one eligible correction-bit ballot from a declared member."""

    member_id: LineageId
    correction: tuple[int, ...]
    eligible: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "correction", _binary_tuple(self.correction, name="vote ballot"))
        if self.eligible is not True:
            raise ValueError("ineligible ballots fail closed")


@dataclass(frozen=True)
class VoteResult:
    """Complete voter evidence and a post-aggregation original-syndrome fact."""

    lineage_id: LineageId
    candidate_lineage_id: LineageId
    electorate: tuple[LineageId, ...]
    ballots: tuple[VoteBallot, ...]
    tie_bit: int
    correction: tuple[int, ...]
    original_valid: bool

    @property
    def eligible(self) -> bool:
        return self.original_valid

    def as_evidence(self) -> dict[str, object]:
        return {
            "aggregation": "coordinate_majority",
            "ballots": [{"correction": list(ballot.correction), "member_id": ballot.member_id.value}
                        for ballot in self.ballots],
            "candidate_lineage_id": self.candidate_lineage_id.value,
            "correction": list(self.correction),
            "electorate": [member.value for member in self.electorate],
            "eligible": self.eligible,
            "original_valid": self.original_valid,
            "object": "correction_bits",
            "tie_bit": self.tie_bit,
            "vote_lineage_id": self.lineage_id.value,
        }


class CoordinateMajorityVote:
    """Closed one-ballot-per-member coordinate-majority aggregation."""

    def __init__(self, *, tie_bit: int) -> None:
        if type(tie_bit) is not int or tie_bit not in (0, 1):
            raise ValueError("coordinate-majority tie bit must be 0 or 1")
        self.tie_bit = tie_bit

    def vote(
        self,
        original: OriginalProblem,
        *,
        graph: LineageGraph,
        parent: LineageId,
        electorate: tuple[LineageId, ...],
        ballots: tuple[VoteBallot, ...],
    ) -> VoteResult:
        declared = tuple(sorted(electorate, key=lambda item: item.value))
        if not declared or len(set(declared)) != len(declared):
            raise ValueError("vote electorate must be nonempty and duplicate-free")
        ordered_ballots = tuple(sorted(ballots, key=lambda item: item.member_id.value))
        members = tuple(ballot.member_id for ballot in ordered_ballots)
        if len(set(members)) != len(members) or set(members) != set(declared):
            raise ValueError("vote requires exactly one ballot from every eligible electorate member")
        if any(len(ballot.correction) != original.hz.shape[1] for ballot in ordered_ballots):
            raise ValueError("vote ballot length differs from the immutable original problem")
        counts = np.asarray([ballot.correction for ballot in ordered_ballots], dtype=np.int64).sum(axis=0)
        threshold = len(ordered_ballots) / 2
        correction = tuple(int(1 if count > threshold else 0 if count < threshold else self.tie_bit) for count in counts)
        candidate = graph.append_node(
            "candidate",
            {"aggregation": "coordinate_majority", "ballot_members": [item.value for item in members],
             "object": "correction_bits",
             "correction": list(correction), "tie_bit": self.tie_bit},
            parent=parent, relation="candidate",
        )
        valid = _original_valid(original, correction)
        validation = graph.append_node("validation", {"original_valid": valid}, parent=candidate, relation="validate")
        selection = graph.append_node(
            "selection",
            {"aggregate_candidate_id": candidate.id.value, "original_valid": valid,
             "selected_id": candidate.id.value if valid else None},
            parent=validation, relation="select",
        )
        return VoteResult(selection.id, candidate.id, declared, ordered_ballots, self.tie_bit, correction, valid)
