"""Exact prespecified paired power and disjoint calibration identity."""

from __future__ import annotations

from itertools import product

import pytest
from scipy.stats import binomtest


def _small_enumerated_power(n: int, *, discordance: float, effect: float, alpha: float) -> float:
    left_only = (discordance + effect) / 2
    right_only = (discordance - effect) / 2
    probability = 0.0
    for outcomes in product((0, 1, 2), repeat=n):
        count_left = outcomes.count(1)
        count_right = outcomes.count(2)
        discordant = count_left + count_right
        if discordant and binomtest(count_left, discordant, 0.5).pvalue <= alpha:
            probability += (1 - discordance) ** outcomes.count(0) * left_only ** count_left * right_only ** count_right
    return probability


def _paired_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "paired_design_v1",
        "family_id": "schedule",
        "arm_order": ["flooding", "serial"],
        "estimand": "paired_all_shot_risk_difference_v1",
        "minimum_relevant_difference": 0.2,
        "calibration_discordance": 0.4,
        "target_power": 0.08,
        "familywise_alpha": 0.1,
        "family_size": 1,
        "max_pairs": 8,
        "calibration_namespace": "pilot-only",
        "evaluation_namespace": "evaluation-only",
        "calibration_receipt_sha256": "a" * 64,
        "evaluation_namespace_sha256": "b" * 64,
    }
    payload.update(updates)
    return payload


def test_paired_power_matches_enumerated_small_case_and_minimal_n() -> None:
    from bp_registry.campaigns.sizing import PairedDesignV1, paired_design_size

    design = PairedDesignV1.model_validate(_paired_payload())
    result = paired_design_size(design)
    enumerated = [_small_enumerated_power(n, discordance=0.4, effect=0.2, alpha=0.1) for n in range(1, 9)]
    assert result.achieved_power_at_cap == pytest.approx(enumerated[-1])
    eligible = [n for n, power in enumerate(enumerated, start=1) if power >= design.target_power]
    assert result.required_n == (min(eligible) if eligible else None)
    assert result.status == ("powered" if eligible else "blocked_precision")
    assert result.design_sha256 == design.digest()


def test_blocked_precision_retains_achieved_power_and_assumptions() -> None:
    from bp_registry.campaigns.sizing import PairedDesignV1, paired_design_size

    design = PairedDesignV1.model_validate(_paired_payload(target_power=0.99, max_pairs=5))
    result = paired_design_size(design)
    assert result.status == "blocked_precision"
    assert result.required_n is None
    assert 0.0 <= result.achieved_power_at_cap < design.target_power
    assert result.assumptions["max_pairs"] == 5


@pytest.mark.parametrize("updates", (
    {"evaluation_namespace": "pilot-only"},
    {"evaluation_namespace_sha256": "a" * 64},
    {"calibration_discordance": 0.1},
    {"minimum_relevant_difference": float("nan")},
    {"max_pairs": True},
    {"family_size": 0},
))
def test_paired_boundary_rejects_overlap_and_invalid_inputs(updates: dict[str, object]) -> None:
    from bp_registry.campaigns.sizing import PairedDesignV1

    with pytest.raises(ValueError):
        PairedDesignV1.model_validate(_paired_payload(**updates))
