"""Terminal, evidence-bounded Phase 11 assessment regressions."""

from __future__ import annotations

from pathlib import Path
from hashlib import sha256

import pytest

from bp_registry.campaigns.contracts import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[1]


def test_tracer_gb46_terminal_assessment_is_three_row_and_inconclusive() -> None:
    """A denied zero-dispatch receipt retains its frozen rows without an effect claim."""
    from bp_registry.campaigns import statistics

    assert hasattr(statistics, "build_phase11_assessment")
    build_phase11_assessment = statistics.build_phase11_assessment

    assessment = build_phase11_assessment(root=ROOT)
    gb46 = assessment["primary_controlled"]["GB46"]

    assert [row["point_id"] for row in gb46["rows"]] == [
        "lower_y", "independence", "higher_y",
    ]
    assert all(tuple(row)[:2] == ("point_id", "d_y") for row in gb46["rows"])
    assert gb46["status"] == "inconclusive_zero_complete_pairs"
    assert gb46["permitted_claim"] == "no_controlled_effect_claim"
    assert gb46["complete_pair_count"] == 0
    assert gb46["calibration_substitution_prohibited"] is True


def test_bb72_terminal_assessment_retains_provenance_and_method_exclusions() -> None:
    """BB72 cannot borrow GB46 support or hide methods ineligible for its code."""
    from bp_registry.campaigns.statistics import build_phase11_assessment

    bb72 = build_phase11_assessment(root=ROOT)["primary_controlled"]["BB72"]

    assert bb72["code_qualification"]["distance_qualification"] == (
        "source_reported_distance_6_not_platform_verified"
    )
    assert bb72["code_qualification"]["logical_operator_qualification"] == (
        "project_derived_logicals_not_independent_distance_verification"
    )
    assert {row["method_id"] for row in bb72["unsupported_method_exclusions"]} == {
        "canonical_asced", "mbp4", "qbpgd",
    }
    assert bb72["permitted_claim"] == "no_controlled_effect_claim"


def test_phase11_index_has_complete_lane_matrix_and_rejects_lane_tamper() -> None:
    """The public index keeps all source, primary, and policy conclusions apart."""
    from bp_registry.campaigns.statistics import build_phase11_assessment, verify_phase11_assessment

    assessment = build_phase11_assessment(root=ROOT)
    matrix = assessment["completeness_matrix"]
    assert {(row["lane"], row["item_id"]) for row in matrix} >= {
        ("source_reproduction", "asced_figure2"),
        ("source_reproduction", "qbpgd_figure7"),
        ("source_reproduction", "mbp4_figures8_9"),
        ("primary_controlled", "GB46"),
        ("primary_controlled", "BB72"),
        ("policy_comparisons", "phase11_policy_comparisons"),
    }
    assessment["primary_controlled"]["GB46"]["receipt_path"] = (
        "data/results/phase11-controlled-evaluation/bb72/evaluation-receipt.json"
    )
    with pytest.raises(ValueError, match="digest|differs"):
        verify_phase11_assessment(root=ROOT, assessment=assessment)


@pytest.mark.parametrize("mutation", ["source", "receipt", "calibration", "claim"])
def test_phase11_verifier_rejects_resigned_cross_lane_and_claim_substitutions(mutation: str) -> None:
    """A valid-looking digest cannot authorize a changed source or controlled conclusion."""
    from bp_registry.campaigns.statistics import build_phase11_assessment, verify_phase11_assessment

    assessment = build_phase11_assessment(root=ROOT)
    if mutation == "source":
        assessment["source_reproduction"]["asced_figure2"]["assessment_path"] = "data/results/missing.json"
    elif mutation == "receipt":
        assessment["primary_controlled"]["GB46"]["receipt_path"] = (
            "data/results/phase11-controlled-evaluation/bb72/evaluation-receipt.json"
        )
    elif mutation == "calibration":
        assessment["primary_controlled"]["BB72"]["calibration_substitution_prohibited"] = False
    else:
        assessment["primary_controlled"]["GB46"]["permitted_claim"] = "decoder_superiority"
    assessment["assessment_sha256"] = sha256(canonical_json_bytes({
        key: value for key, value in assessment.items() if key != "assessment_sha256"
    })).hexdigest()

    with pytest.raises(ValueError, match="differs"):
        verify_phase11_assessment(root=ROOT, assessment=assessment)
