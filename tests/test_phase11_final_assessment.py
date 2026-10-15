"""Terminal, evidence-bounded Phase 11 assessment regressions."""

from __future__ import annotations

from pathlib import Path


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
