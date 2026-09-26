"""Outcome and paired-comparison arithmetic for Phase 4 CSS pilots.

The caller supplies independently evaluated, retained per-shot classifications.
This module never sees a hidden physical error or chooses a decoder candidate.
"""

from __future__ import annotations

from collections import Counter
import math
from typing import Mapping, Sequence


CELLS = (
    "valid_correct",
    "valid_wrong_logical",
    "invalid_correct",
    "invalid_wrong_logical",
    "no_proposal",
)
VALID_SELECTED_CELLS = frozenset({"valid_correct", "valid_wrong_logical"})


def wilson_interval(failures: int, denominator: int, *, z: float = 1.959963984540054) -> list[float] | None:
    """Return a two-sided Wilson interval, or undefined for an empty denominator."""
    if denominator < 0 or failures < 0 or failures > denominator or not math.isfinite(z) or z <= 0:
        raise ValueError("invalid binomial count or confidence quantile")
    if denominator == 0:
        return None
    p = failures / denominator
    adjusted = 1 + z * z / denominator
    center = (p + z * z / (2 * denominator)) / adjusted
    half = z * math.sqrt(p * (1 - p) / denominator + z * z / (4 * denominator * denominator)) / adjusted
    return [max(0.0, center - half), min(1.0, center + half)]


def exact_paired_binomial_p(discordant_a_only: int, discordant_b_only: int) -> float:
    """Two-sided exact McNemar/binomial p-value for paired success discordance."""
    if min(discordant_a_only, discordant_b_only) < 0:
        raise ValueError("discordant counts cannot be negative")
    total = discordant_a_only + discordant_b_only
    if total == 0:
        return 1.0
    tail = sum(math.comb(total, count) for count in range(min(discordant_a_only, discordant_b_only) + 1)) / (2 ** total)
    return min(1.0, 2 * tail)


def summarize_matched_cohort(
    shots: Sequence[Mapping[str, object]], *, arm_names: tuple[str, str],
) -> dict[str, object]:
    """Summarize two complete matched arms without dropping invalid or empty proposals.

    Each shot has a unique ``shot_id`` and nonempty ``sample_identity``.  Each
    arm has ``status='completed'``, ``diagnostic_cell``, and ``selected``.  An
    invalid-syndrome proposal may have a logical *projection* classification,
    but cannot count as a correct recovery.  ``no_proposal`` is an all-shot
    failure, separate from an interrupted command (which rejects aggregation).
    """
    if len(arm_names) != 2 or arm_names[0] == arm_names[1] or not shots:
        raise ValueError("paired cohort requires two distinct arms and at least one shot")
    counts = {name: Counter({cell: 0 for cell in CELLS}) for name in arm_names}
    selected_valid = {name: 0 for name in arm_names}
    valid_wrong = {name: 0 for name in arm_names}
    failures = {name: 0 for name in arm_names}
    selected_counts = {name: 0 for name in arm_names}
    pairs = {f"{arm_names[0]}_{a}_{arm_names[1]}_{b}": 0 for a in (0, 1) for b in (0, 1)}
    seen_ids: set[int] = set()
    seen_samples: set[str] = set()
    for shot in shots:
        shot_id, sample = shot.get("shot_id"), shot.get("sample_identity")
        if not isinstance(shot_id, int) or shot_id < 0 or shot_id in seen_ids or not isinstance(sample, str) or not sample or sample in seen_samples:
            raise ValueError("paired cohort has missing or duplicate shot/sample identity")
        seen_ids.add(shot_id)
        seen_samples.add(sample)
        arms = shot.get("arms")
        if not isinstance(arms, Mapping) or set(arms) != set(arm_names):
            raise ValueError(f"shot {shot_id} does not contain the exact paired arms")
        successes: list[int] = []
        for name in arm_names:
            arm = arms[name]
            if not isinstance(arm, Mapping) or arm.get("status") != "completed":
                raise ValueError(f"shot {shot_id}/{name} is incomplete; retain it outside an outcome denominator")
            if arm.get("sample_identity") != sample:
                raise ValueError(f"shot {shot_id}/{name} physical sample differs from the paired identity")
            cell, selected = arm.get("diagnostic_cell"), arm.get("selected")
            if cell not in CELLS or not isinstance(selected, bool):
                raise ValueError(f"shot {shot_id}/{name} has an invalid diagnostic classification")
            if cell == "no_proposal" and selected:
                raise ValueError(f"shot {shot_id}/{name} selects a nonexistent proposal")
            counts[name][cell] += 1
            selected_counts[name] += int(selected)
            if selected and cell in VALID_SELECTED_CELLS:
                selected_valid[name] += 1
                valid_wrong[name] += int(cell == "valid_wrong_logical")
            success = int(selected and cell == "valid_correct")
            failures[name] += 1 - success
            successes.append(success)
        pairs[f"{arm_names[0]}_{successes[0]}_{arm_names[1]}_{successes[1]}"] += 1
    denominator = len(shots)
    arms_summary: dict[str, object] = {}
    for name in arm_names:
        arms_summary[name] = {
            "diagnostic_cells": {cell: counts[name][cell] for cell in CELLS},
            "selected_proposals": selected_counts[name],
            "all_shot_failure": {
                "failures": failures[name], "denominator": denominator,
                "estimate": failures[name] / denominator,
                "wilson_95": wilson_interval(failures[name], denominator),
                "no_proposal_counted_as_failure": True,
            },
            "selected_valid_syndrome_logical_error": {
                "failures": valid_wrong[name], "denominator": selected_valid[name],
                "estimate": valid_wrong[name] / selected_valid[name] if selected_valid[name] else None,
                "wilson_95": wilson_interval(valid_wrong[name], selected_valid[name]),
            },
        }
    a, b = arm_names
    a_only, b_only = pairs[f"{a}_1_{b}_0"], pairs[f"{a}_0_{b}_1"]
    return {
        "schema_version": 1,
        "complete_matched_shots": denominator,
        "shot_ids": sorted(seen_ids),
        "arms": arms_summary,
        "paired_success": {
            "table": pairs,
            "first_only": a_only,
            "second_only": b_only,
            "exact_two_sided_p": exact_paired_binomial_p(a_only, b_only),
            "test_scope": "descriptive exact paired test; no claim of equivalence or multiplicity adjustment",
        },
        "invalid_correct_interpretation": "linear logical projection only; invalid syndrome is an all-shot decoder failure",
    }
