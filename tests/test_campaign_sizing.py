"""Exact prespecified paired power and disjoint calibration identity."""

from __future__ import annotations

from itertools import product
from hashlib import sha256
import json
from pathlib import Path

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


def _profile_receipt(method: str = "relay", *, missing: bool = False) -> dict[str, object]:
    measurements = {
        key: {"status": "observed", "value": value, "unit": unit}
        for key, value, unit in (
            ("execution_wall_ns", 10_000_000, "ns"),
            ("execution_cpu_ns", 8_000_000, "ns"),
            ("replay_wall_ns", 5_000_000, "ns"),
            ("peak_rss_bytes", 100_000_000, "bytes"),
            ("storage_bytes", 2_000, "bytes"),
            ("evidence_bytes", 1_000, "bytes"),
        )
    }
    if missing:
        measurements["peak_rss_bytes"] = {"status": "unavailable", "reason": "No process peak observed."}
    return {"schema": "mechanism_profile_receipt_v1", "method": method,
            "profile_namespace": "pilot-only", "source_receipt_sha256": "c" * 64,
            "replay_receipt_sha256": "d" * 64, "verified": True,
            "publication_slurm_authorization": "deny", "measurements": measurements}


def test_representative_profile_projection_uses_own_verified_method_and_positive_n() -> None:
    from bp_registry.campaigns.sizing import PairedDesignV1, project_measured_resources

    design = PairedDesignV1.model_validate(_paired_payload(max_pairs=20, target_power=0.2))
    projection = project_measured_resources(
        design=design, method="relay", profile=_profile_receipt(),
        local_wall_cap_ns=100_000_000, local_storage_cap_bytes=10_000,
        local_rss_cap_bytes=200_000_000, safety_numerator=2, safety_denominator=1,
    )
    assert projection["bounded_n"] > 0
    assert projection["bounded_n"] <= design.max_pairs
    assert projection["profile_method"] == "relay"
    assert projection["publication_slurm_authorization"] == "deny"
    assert projection["site_ceiling_status"] == "unavailable"


def test_relay_beam_mbbp_projection_rejects_cross_method_or_yao_costs() -> None:
    from bp_registry.campaigns.sizing import PairedDesignV1, project_measured_resources

    design = PairedDesignV1.model_validate(_paired_payload())
    for method in ("beam", "mbbp", "yao"):
        with pytest.raises(ValueError, match="method"):
            project_measured_resources(
                design=design, method="relay", profile=_profile_receipt(method),
                local_wall_cap_ns=100_000_000, local_storage_cap_bytes=10_000,
                local_rss_cap_bytes=200_000_000, safety_numerator=2, safety_denominator=1)


def test_schedule_projection_uses_its_own_arm_receipt() -> None:
    from bp_registry.campaigns.sizing import PairedDesignV1, project_measured_resources

    design = PairedDesignV1.model_validate(_paired_payload())
    schedule = _profile_receipt("spa_flooding")
    projection = project_measured_resources(
        design=design, method="spa_flooding", profile=schedule,
        local_wall_cap_ns=100_000_000, local_storage_cap_bytes=10_000,
        local_rss_cap_bytes=200_000_000, safety_numerator=2, safety_denominator=1)
    assert projection["bounded_n"] > 0
    with pytest.raises(ValueError, match="method"):
        project_measured_resources(
            design=design, method="spa_check_node_serial", profile=schedule,
            local_wall_cap_ns=100_000_000, local_storage_cap_bytes=10_000,
            local_rss_cap_bytes=200_000_000, safety_numerator=2, safety_denominator=1)


def test_missing_mechanism_measurement_blocks_local_readiness() -> None:
    from bp_registry.campaigns.sizing import PairedDesignV1, project_measured_resources

    design = PairedDesignV1.model_validate(_paired_payload())
    result = project_measured_resources(
        design=design, method="relay", profile=_profile_receipt(missing=True),
        local_wall_cap_ns=100_000_000, local_storage_cap_bytes=10_000,
        local_rss_cap_bytes=200_000_000, safety_numerator=2, safety_denominator=1)
    assert result["status"] == "blocked_no_matched_evidence"
    assert result["bounded_n"] == 0
    assert result["missing_measurements"] == ["peak_rss_bytes"]


ROOT = Path(__file__).resolve().parents[1]
CONTROLLED = ROOT / "data/studies/phase9-controlled-design-v1.json"


def test_positive_n_and_distinct_representative_profile_origins() -> None:
    from bp_registry.campaigns.sizing import PairedDesignV1, paired_design_size

    receipt = json.loads(CONTROLLED.read_text())
    assert receipt["evaluation_started"] is False
    assert receipt["publication_slurm_authorization"] == "deny"
    assert set(receipt["families"]) == {"schedule", "relay_beam", "mbbp_list_vote"}
    assert receipt["site_ceilings"] == {key: "unavailable" for key in
                                        ("wall", "cores", "memory", "storage", "accounting")}
    expected_methods = {
        "schedule": {"spa_flooding", "spa_check_node_serial"},
        "relay_beam": {"beam", "relay"}, "mbbp_list_vote": {"mbbp"},
    }
    for family, record in receipt["families"].items():
        n = record["bounded_evaluative_n"]
        assert n > 0
        assert record["status"] == "bounded_exploratory"
        assert record["powered_required_n"] > n
        assert record["bounded_achieved_power"] < receipt["target_power"]
        assert record["projected_total"]["wall_ns"] <= record["local_caps"]["wall_ns"]
        assert record["projected_total"]["storage_bytes"] <= record["local_caps"]["storage_bytes"]
        assert record["projected_total"]["rss_bytes"] <= record["local_caps"]["rss_bytes"]
        design = PairedDesignV1.model_validate(record["paired_design"])
        assert design.digest() == record["paired_design_sha256"]
        assert design.calibration_namespace != design.evaluation_namespace
        assert design.calibration_discordance == 1.0
        assert paired_design_size(design.model_copy(update={"max_pairs": n})).achieved_power_at_cap == pytest.approx(
            record["bounded_achieved_power"])
        assert set(record["calibration_profiles"]) == expected_methods[family]
        for method, item in record["calibration_profiles"].items():
            path = ROOT / item["path"]
            assert sha256(path.read_bytes()).hexdigest() == item["sha256"]
            profile = json.loads(path.read_text())
            assert profile["method"] == method
            assert profile["verified"] is True
            assert profile["publication_slurm_authorization"] == "deny"
            assert profile["profile_namespace"] == design.calibration_namespace
            assert profile["measurements"]["execution_wall_ns"]["value"] > 0
            assert profile["measurements"]["replay_wall_ns"]["value"] > 0
            assert profile["measurements"]["peak_rss_bytes"]["value"] > 0
            assert profile["mechanism_work"]


def test_every_controlled_family_binds_public_sample_major_order() -> None:
    from bp_registry.campaigns.contracts import OrderedCampaignWorkSpecV1
    from bp_registry.campaigns.cli import _preflight_ordered_arms
    from bp_registry.campaigns.planning import freeze_ordered_campaign_work_spec

    receipt = json.loads(CONTROLLED.read_text())
    for family, record in receipt["families"].items():
        order_path = ROOT / record["ordered_work_path"]
        public_path = ROOT / record["public_ordered_plan_path"]
        assert sha256(order_path.read_bytes()).hexdigest() == record["ordered_work_file_sha256"]
        assert sha256(public_path.read_bytes()).hexdigest() == record["public_ordered_plan_sha256"]
        spec = OrderedCampaignWorkSpecV1.model_validate(json.loads(order_path.read_text())["ordered_campaign_work_spec"])
        frozen = freeze_ordered_campaign_work_spec(spec)
        public = json.loads(public_path.read_text())
        assert frozen.campaign_plan_digest == record["ordered_plan_digest"] == public["campaign_plan_digest"]
        assert spec.digest() == record["ordered_work_spec_sha256"]
        assert list(spec.execution_order.arm_order) == record["arm_order"]
        assert _preflight_ordered_arms(spec, ROOT) == "controlled_planning_only"
        assert len(public["groups"]) == record["bounded_evaluative_n"]
        assert len(public["units"]) == record["bounded_evaluative_n"] * len(record["arm_order"])
        for ordinal, group in enumerate(public["groups"], start=1):
            assert group["group_ordinal"] == ordinal
            member_arms = [item["arm_id"] for item in public["units"] if item["group_ordinal"] == ordinal]
            assert member_arms == record["arm_order"]
