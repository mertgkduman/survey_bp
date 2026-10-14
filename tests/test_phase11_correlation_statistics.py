"""Exact regressions for the Phase 11 fixed-marginal correlation sweep."""

from __future__ import annotations

from hashlib import sha256
import importlib
from pathlib import Path

import pytest

from bp_registry.campaigns.contracts import PauliMatchedPairV1, canonical_json_bytes


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "data/studies/phase11-fixed-marginal-design.json"


def _digest(domain: str, value: object) -> str:
    return sha256(domain.encode("ascii") + b"\0" + canonical_json_bytes(value)).hexdigest()


def _pair(*, point: str, ordinal: int, joint_failure: bool, separate_failure: bool) -> PauliMatchedPairV1:
    """Make a sealed complete matched pair with hand-selected all-shot outcomes."""
    physical = sha256(f"{point}:{ordinal}".encode()).hexdigest()
    materialized = sha256(f"materialized:{point}:{ordinal}".encode()).hexdigest()

    def arm(arm_id: str, failed: bool) -> dict[str, object]:
        status = "wrong_logical_action" if failed else "exact"
        return {
            "arm_id": arm_id,
            "materialized_sample_sha256": materialized,
            "candidate_x": [1], "candidate_z": [1],
            "terminal_status": status,
            "all_shot": "failure" if failed else "success",
            "evaluation": {"outcome": status},
            "work": {"sweeps": ordinal + 1},
        }

    components = [
        {"component": component, "candidate": [1], "terminal_status": "exact", "iterations": ordinal,
         "work": {"sweeps": ordinal + 1}, "syndrome_sha256": sha256(f"{component}:{point}:{ordinal}".encode()).hexdigest()}
        for component in ("X", "Z")
    ]
    unsigned = {
        "schema": "pauli_matched_pair_v1", "decision_ids": ("D-05", "D-06", "D-08"),
        "physical_sample_identity": physical, "physical_error_sha256": sha256(f"error:{point}:{ordinal}".encode()).hexdigest(),
        "materialized_sample_sha256": materialized, "joint": arm("joint", joint_failure),
        "separate": arm("separate", separate_failure), "components": components,
    }
    return PauliMatchedPairV1.model_validate({
        **unsigned,
        "record_sha256": _digest("bp-registry-pauli-matched-pair-v1", unsigned),
    })


def _hand_counted_rows() -> dict[str, tuple[PauliMatchedPairV1, ...]]:
    return {
        "lower_y": tuple(_pair(point="lower_y", ordinal=index, joint_failure=index == 0, separate_failure=index < 2) for index in range(4)),
        "independence": tuple(_pair(point="independence", ordinal=index, joint_failure=index < 2, separate_failure=index == 0) for index in range(4)),
        "higher_y": tuple(_pair(point="higher_y", ordinal=index, joint_failure=index < 3, separate_failure=index == 0) for index in range(4)),
    }


def test_tracer_rational_fixed_marginal_design_is_exact_and_digest_bound() -> None:
    api = importlib.import_module("bp_registry.campaigns.statistics")
    assert hasattr(api, "load_fixed_marginal_design"), (
        "campaign statistics must provide the immutable fixed-marginal design loader"
    )
    load_fixed_marginal_design = api.load_fixed_marginal_design

    design = load_fixed_marginal_design(DESIGN)
    assert design.point_order == ("lower_y", "independence", "higher_y")
    assert design.design_sha256 == sha256(DESIGN.read_bytes()).hexdigest()
    assert tuple(row.probabilities for row in design.rows) == (
        (1681 / 1800, 59 / 1800, 1 / 1800, 59 / 1800),
        (841 / 900, 29 / 900, 1 / 900, 29 / 900),
        (19 / 20, 1 / 60, 1 / 60, 1 / 60),
    )
    assert tuple(row.q_x for row in design.rows) == pytest.approx((1 / 30,) * 3)
    assert tuple(row.q_z for row in design.rows) == pytest.approx((1 / 30,) * 3)
    assert tuple(row.total_nonidentity for row in design.rows) == pytest.approx((119 / 1800, 59 / 900, 1 / 20))
    assert tuple(row.x_z_covariance for row in design.rows) == pytest.approx((-1 / 1800, 0.0, 7 / 450))
    assert "fixed-total" not in design.study_label.lower()


def test_hand_counted_contrasts_have_frozen_order_and_simultaneous_bounds() -> None:
    from bp_registry.campaigns.statistics import assess_correlation_sweep

    result = assess_correlation_sweep(design_path=DESIGN, point_pairs=_hand_counted_rows())
    assert tuple(row.point_id for row in result.rows) == ("lower_y", "independence", "higher_y")
    assert tuple(row.d_y for row in result.rows) == pytest.approx((-0.25, 0.25, 0.5))
    assert [(contrast.contrast_id, contrast.change) for contrast in result.contrasts] == [
        ("lower_y_minus_independence", -0.5),
        ("higher_y_minus_independence", 0.25),
    ]
    assert result.simultaneous_family.method == "bonferroni_exact_six_arm_rates_v1"
    for row in result.rows:
        assert row.d_y_interval[0] <= row.d_y <= row.d_y_interval[1]
    for contrast in result.contrasts:
        assert contrast.interval[0] <= contrast.change <= contrast.interval[1]


def test_fixed_marginal_sweep_rejects_overlapping_point_samples() -> None:
    from bp_registry.campaigns.statistics import assess_correlation_sweep

    rows = _hand_counted_rows()
    duplicate = rows["lower_y"][0]
    with pytest.raises(ValueError, match="disjoint"):
        assess_correlation_sweep(
            design_path=DESIGN,
            point_pairs={**rows, "higher_y": (duplicate, *rows["higher_y"][1:])},
        )


def test_sizing_receipt_is_deterministic_and_binds_frozen_inputs() -> None:
    api = importlib.import_module("bp_registry.campaigns.sizing")
    assert hasattr(api, "calibrate_paired_sweep_design"), (
        "campaign sizing must provide a fixed-marginal paired-sweep preflight receipt"
    )
    calibrate = api.calibrate_paired_sweep_design
    pilot = "3" * 64
    first = calibrate(design_path=DESIGN, pilot_evidence_identity=pilot)
    second = calibrate(design_path=DESIGN, pilot_evidence_identity=pilot)
    assert first.receipt_sha256 == second.receipt_sha256
    assert first.design_sha256 == sha256(DESIGN.read_bytes()).hexdigest()
    assert first.paired_design.max_pairs == 5_000
    assert first.paired_sizing.status in {"powered", "blocked_precision"}
    assert first.stopping_rule == "fixed paired count per point; no comparison outcome can change sizing"


def test_sizing_rejects_empty_duplicate_and_partial_pilot_pairs() -> None:
    from bp_registry.campaigns.sizing import calibrate_paired_sweep_design

    with pytest.raises(ValueError, match="pilot"):
        calibrate_paired_sweep_design(
            design_path=DESIGN, pilot_evidence_identity="3" * 64, pilot_pairs={},
        )
    rows = _hand_counted_rows()
    with pytest.raises(ValueError, match="disjoint"):
        calibrate_paired_sweep_design(
            design_path=DESIGN, pilot_evidence_identity="3" * 64,
            pilot_pairs={**rows, "higher_y": (rows["lower_y"][0], *rows["higher_y"][1:])},
        )
