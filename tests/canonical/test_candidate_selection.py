"""Adversarial fixtures for deterministic, truth-free list selection."""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest

from bp_registry.canonical.lineage import LineageId
from bp_registry.canonical.problems import OriginalProblem


def test_candidate_selection_module_exports_policy_seam() -> None:
    """The reusable selection seam is a Phase 6 production requirement."""
    assert importlib.util.find_spec("bp_registry.canonical.candidate_selection") is not None


def _original() -> OriginalProblem:
    return OriginalProblem(
        "selection-fixture",
        hx=np.zeros((1, 3), dtype=np.uint8),
        hz=np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8),
        syndrome=np.asarray([1, 0], dtype=np.uint8),
    )


def _origin(*, kind: str, value: str, ordinal: int, candidate: tuple[int, ...] | None,
            eligible: bool, reason: str):
    from bp_registry.canonical.candidate_selection import CandidateOrigin

    return CandidateOrigin(
        lineage_id=LineageId(kind, f"{kind}-{value}"),
        local_ordinal=ordinal,
        candidate=candidate,
        eligible=eligible,
        reason=reason,
    )


def test_complete_origins_retain_rejected_pruned_denied_and_candidate_less_rows() -> None:
    from bp_registry.canonical.candidate_selection import StableFirstScore, freeze_candidate_list

    origins = (
        _origin(kind="attempt", value="admitted", ordinal=0, candidate=(1, 0, 0), eligible=True, reason="admitted"),
        _origin(kind="branch", value="pruned", ordinal=1, candidate=(0, 1, 0), eligible=False, reason="pruned_by_width"),
        _origin(kind="leg", value="denied", ordinal=2, candidate=None, eligible=False, reason="budget_denied"),
        _origin(kind="attempt", value="rejected", ordinal=3, candidate=(0, 0, 0), eligible=False, reason="rejected_invalid"),
    )
    frozen = freeze_candidate_list(_original(), declared_origins=tuple(item.lineage_id for item in origins),
                                   origins=origins, score_policy=StableFirstScore())

    assert tuple(item.reason for item in frozen.origins) == (
        "admitted", "pruned_by_width", "budget_denied", "rejected_invalid",
    )
    assert frozen.selected_origin_id == origins[0].lineage_id
    assert frozen.origins[2].candidate_digest is None
    assert frozen.origins[2].original_valid is None


def test_declared_origin_set_and_candidate_eligibility_fail_closed() -> None:
    from bp_registry.canonical.candidate_selection import StableFirstScore, freeze_candidate_list

    origin = _origin(kind="attempt", value="only", ordinal=0, candidate=(1, 0, 0), eligible=True, reason="admitted")
    with pytest.raises(ValueError, match="complete"):
        freeze_candidate_list(_original(), declared_origins=(), origins=(origin,), score_policy=StableFirstScore())
    with pytest.raises(ValueError, match="candidate-less"):
        _origin(kind="attempt", value="broken", ordinal=1, candidate=None, eligible=True, reason="broken")


def test_duplicate_grouping_preserves_all_origins_and_frequency_score() -> None:
    from bp_registry.canonical.candidate_selection import FrequencyOverWeightScore, freeze_candidate_list

    origins = (
        _origin(kind="attempt", value="first", ordinal=2, candidate=(1, 0, 0), eligible=True, reason="admitted"),
        _origin(kind="branch", value="second", ordinal=1, candidate=(1, 0, 0), eligible=True, reason="duplicate"),
        _origin(kind="leg", value="other", ordinal=0, candidate=(0, 1, 1), eligible=True, reason="admitted"),
    )
    frozen = freeze_candidate_list(_original(), declared_origins=tuple(item.lineage_id for item in origins),
                                   origins=origins, score_policy=FrequencyOverWeightScore())

    groups = frozen.duplicate_groups
    assert len(groups) == 2
    shared = next(group for group in groups if len(group.member_origin_ids) == 2)
    assert shared.member_origin_ids == (origins[1].lineage_id, origins[0].lineage_id)
    assert shared.frequency == 2
    assert frozen.selected_origin_id == origins[1].lineage_id


def test_rejected_duplicate_cannot_inflate_frequency_or_change_selection() -> None:
    from bp_registry.canonical.candidate_selection import FrequencyOverWeightScore, freeze_candidate_list

    original = OriginalProblem(
        "frequency-fixture",
        hx=np.zeros((1, 4), dtype=np.uint8),
        hz=np.asarray([[1, 1, 0, 0], [0, 1, 1, 0]], dtype=np.uint8),
        syndrome=np.asarray([1, 0], dtype=np.uint8),
    )
    origins = (
        _origin(kind="attempt", value="heavy", ordinal=0, candidate=(0, 1, 1, 1), eligible=True, reason="admitted"),
        _origin(kind="branch", value="rejected-heavy", ordinal=1, candidate=(0, 1, 1, 1), eligible=False, reason="pruned"),
        _origin(kind="leg", value="lighter", ordinal=2, candidate=(0, 1, 1, 0), eligible=True, reason="admitted"),
    )
    frozen = freeze_candidate_list(
        original, declared_origins=tuple(item.lineage_id for item in origins), origins=origins,
        score_policy=FrequencyOverWeightScore(),
    )

    heavy_group = next(group for group in frozen.duplicate_groups if group.candidate_digest == origins[0].candidate_digest)
    assert heavy_group.member_origin_ids == (origins[0].lineage_id,)
    assert heavy_group.frequency == 1
    assert frozen.origins[1].frequency == 0
    # If the rejected duplicate counted, the heavy score would be 2 / 4 and
    # beat the lighter admitted candidate's 1 / 3.
    assert frozen.selected_origin_id == origins[2].lineage_id


def test_worker_arrival_permutations_and_declared_ties_have_identical_evidence() -> None:
    from bp_registry.canonical.candidate_selection import StableFirstScore, freeze_candidate_list

    earlier = _origin(kind="attempt", value="earlier", ordinal=0, candidate=(1, 0, 0), eligible=True, reason="admitted")
    later = _origin(kind="branch", value="later", ordinal=1, candidate=(1, 0, 0), eligible=True, reason="admitted")
    first = freeze_candidate_list(_original(), declared_origins=(earlier.lineage_id, later.lineage_id),
                                  origins=(later, earlier), score_policy=StableFirstScore())
    second = freeze_candidate_list(_original(), declared_origins=(later.lineage_id, earlier.lineage_id),
                                   origins=(earlier, later), score_policy=StableFirstScore())

    assert first.as_evidence_bytes() == second.as_evidence_bytes()
    assert first.selected_origin_id == earlier.lineage_id


def test_nonfinite_score_is_rejected_before_selection() -> None:
    from bp_registry.canonical.candidate_selection import CandidateScorePolicy, freeze_candidate_list

    class Nonfinite(CandidateScorePolicy):
        name = "nonfinite"
        higher_is_better = False

        def score(self, origin, frequency: int) -> float:
            return float("nan")

    origin = _origin(kind="attempt", value="nonfinite", ordinal=0, candidate=(1, 0, 0), eligible=True, reason="admitted")
    with pytest.raises(ValueError, match="nonfinite"):
        freeze_candidate_list(_original(), declared_origins=(origin.lineage_id,), origins=(origin,), score_policy=Nonfinite())
