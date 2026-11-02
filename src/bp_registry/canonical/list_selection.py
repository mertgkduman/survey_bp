"""Deterministic original-space selection from an explicitly scored candidate list.

This is a project-owned Phase 6 primitive. A source-specific controller must
declare its own eligibility and score policy; this module does not define a
BeamSearch ranking rule or a voting object.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Sequence

import numpy as np

from .problems import OriginalProblem


ScoreKind = Literal["hamming_weight", "declared_score"]
ScoreDirection = Literal["minimize", "maximize"]
TieRule = Literal["generation_order", "candidate_id"]


@dataclass(frozen=True, slots=True)
class ListCandidate:
    candidate_id: str
    origin_id: str
    generation_order: int
    bits: tuple[int, ...] | None
    declared_eligible: bool
    eligibility_basis: str
    declared_score: int | float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or not self.candidate_id:
            raise ValueError("candidate_id must be nonempty")
        if not isinstance(self.origin_id, str) or not self.origin_id:
            raise ValueError("origin_id must be nonempty")
        if type(self.generation_order) is not int or self.generation_order < 0:
            raise ValueError("generation_order must be a nonnegative integer")
        if type(self.declared_eligible) is not bool:
            raise ValueError("declared_eligible must be a boolean")
        if not isinstance(self.eligibility_basis, str) or not self.eligibility_basis:
            raise ValueError("eligibility_basis must describe the source or controller rule")
        if self.bits is not None:
            bits = tuple(self.bits)
            if any(type(bit) is not int or bit not in (0, 1) for bit in bits):
                raise ValueError("candidate bits must be binary integers")
            object.__setattr__(self, "bits", bits)
        if self.declared_score is not None:
            if type(self.declared_score) not in (int, float):
                raise ValueError("declared score must be numeric and finite")
            try:
                finite = math.isfinite(self.declared_score)
            except (OverflowError, ValueError):
                finite = False
            if not finite:
                raise ValueError("declared score must be numeric and finite")


@dataclass(frozen=True, slots=True)
class ListSelectionSpec:
    score_kind: ScoreKind
    score_basis: str
    direction: ScoreDirection
    tie_rule: TieRule

    def __post_init__(self) -> None:
        if self.score_kind not in ("hamming_weight", "declared_score"):
            raise ValueError("selection score kind is unsupported")
        if not isinstance(self.score_basis, str) or not self.score_basis:
            raise ValueError("selection score basis must identify the source or equation")
        if self.score_kind == "hamming_weight" and self.score_basis != "original_hamming_weight":
            raise ValueError("hamming-weight selection requires its original-coordinate score basis")
        if self.direction not in ("minimize", "maximize"):
            raise ValueError("selection score direction is unsupported")
        if self.tie_rule not in ("generation_order", "candidate_id"):
            raise ValueError("selection tie rule is unsupported")


@dataclass(frozen=True, slots=True)
class ListCandidateAssessment:
    candidate_id: str
    origin_id: str
    generation_order: int
    bits: tuple[int, ...] | None
    declared_eligible: bool
    eligibility_basis: str
    original_valid: bool | None
    eligible: bool
    score: int | float | None
    rejection_reason: str | None

    def as_evidence(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "origin_id": self.origin_id,
            "generation_order": self.generation_order,
            "bits": None if self.bits is None else list(self.bits),
            "declared_eligible": self.declared_eligible,
            "eligibility_basis": self.eligibility_basis,
            "original_valid": self.original_valid,
            "eligible": self.eligible,
            "score": self.score,
            "rejection_reason": self.rejection_reason,
        }


@dataclass(frozen=True, slots=True)
class ListSelectionResult:
    spec: ListSelectionSpec
    assessments: tuple[ListCandidateAssessment, ...]
    selected_id: str | None
    selected_origin: str | None
    selected_bits: tuple[int, ...] | None

    def as_evidence(self) -> dict[str, object]:
        return {
            "score_kind": self.spec.score_kind,
            "score_basis": self.spec.score_basis,
            "direction": self.spec.direction,
            "tie_rule": self.spec.tie_rule,
            "candidates": [assessment.as_evidence() for assessment in self.assessments],
            "selected_id": self.selected_id,
            "selected_origin": self.selected_origin,
            "selected_bits": None if self.selected_bits is None else list(self.selected_bits),
            "selection_status": "no_eligible_candidate" if self.selected_id is None else "selected",
        }


def select_candidate_list(
    original: OriginalProblem, candidates: Sequence[ListCandidate], *, spec: ListSelectionSpec,
) -> ListSelectionResult:
    """Validate against the original syndrome, then score eligible candidates.

    Hidden physical error truth is intentionally absent from this interface.
    The returned assessments retain every candidate in declared generation order.
    """
    if not isinstance(original, OriginalProblem) or not isinstance(spec, ListSelectionSpec):
        raise ValueError("selection requires an original problem and explicit policy")
    if any(not isinstance(candidate, ListCandidate) for candidate in candidates):
        raise ValueError("selection requires typed list candidates")
    if len({candidate.candidate_id for candidate in candidates}) != len(candidates):
        raise ValueError("candidate IDs must be unique within a selection")
    ordered = sorted(candidates, key=lambda item: (item.generation_order, item.candidate_id))
    assessments: list[ListCandidateAssessment] = []
    width = original.hz.shape[1]
    matrix = original.hz.astype(np.int64)
    for candidate in ordered:
        if spec.score_kind == "hamming_weight" and candidate.declared_score is not None:
            raise ValueError("hamming-weight selection rejects unused declared scores")
        bits = candidate.bits
        if bits is None:
            original_valid = None
            reason = "candidate_unavailable"
        elif len(bits) != width:
            original_valid = False
            reason = "original_shape_mismatch"
        else:
            original_valid = bool(np.array_equal((matrix @ np.asarray(bits, dtype=np.int64)) % 2, original.syndrome))
            reason = None if original_valid else "original_syndrome_mismatch"
        score = (sum(bits) if bits is not None and spec.score_kind == "hamming_weight"
                 else candidate.declared_score if spec.score_kind == "declared_score" else None)
        if reason is None and not candidate.declared_eligible:
            reason = "declared_ineligible"
        if reason is None and score is None:
            reason = "missing_declared_score"
        assessments.append(ListCandidateAssessment(
            candidate.candidate_id, candidate.origin_id, candidate.generation_order,
            bits, candidate.declared_eligible, candidate.eligibility_basis,
            original_valid, reason is None, score, reason,
        ))
    eligible = [row for row in assessments if row.eligible]

    def key(row: ListCandidateAssessment) -> tuple[object, ...]:
        assert row.score is not None
        rank = row.score if spec.direction == "minimize" else -row.score
        tie = ((row.generation_order, row.candidate_id) if spec.tie_rule == "generation_order"
               else (row.candidate_id, row.generation_order))
        return rank, *tie

    selected = min(eligible, key=key, default=None)
    return ListSelectionResult(
        spec, tuple(assessments),
        None if selected is None else selected.candidate_id,
        None if selected is None else selected.origin_id,
        None if selected is None else selected.bits,
    )
