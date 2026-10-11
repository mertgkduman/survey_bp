"""Adversarial coverage for immutable source-target receipts."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import copy
import json
import math

import pytest
from pydantic import ValidationError


def _table_receipt():
    from bp_registry.campaigns.targets import (
        ByteSnapshotV1,
        SourceDenominatorV1,
        SourceIdentityV1,
        TableCellLocatorV1,
        TableTargetReceiptV1,
        ValueBoundsV1,
    )

    return TableTargetReceiptV1(
        schema="campaign_table_target_v1",
        target_id="synthetic-table-p010",
        source=SourceIdentityV1(
            uri_or_doi="https://doi.org/10.0000/synthetic",
            revision="published-v1",
            accessed_on=date(2026, 10, 11),
        ),
        location=TableCellLocatorV1(table_id="Table 2", row_id="p=0.010", column_id="LER"),
        source_snapshot=ByteSnapshotV1.from_bytes("papers/synthetic/table-2.csv", b"p,ler\n.01,.02\n"),
        reported=ValueBoundsV1(value=0.02, lower_error=0.003, upper_error=0.004, precision=0.001),
        source_denominator=SourceDenominatorV1(status="unavailable", reason="paper reports no count"),
    )


def test_source_table_round_trip_and_digest_bind_source_precision_and_denominator():
    receipt = _table_receipt()
    encoded = receipt.model_dump_json(by_alias=True)
    assert type(receipt).model_validate_json(encoded) == receipt

    source_changed = receipt.model_copy(
        update={"source_snapshot": type(receipt.source_snapshot).from_bytes("papers/synthetic/table-2.csv", b"p,ler\n.01,.03\n")},
    )
    precision_changed = receipt.model_copy(
        update={"reported": receipt.reported.model_copy(update={"precision": 0.0001})},
    )
    observed = receipt.model_copy(
        update={"source_denominator": type(receipt.source_denominator)(status="observed", count=1000)},
    )
    assert len({receipt.digest(), source_changed.digest(), precision_changed.digest(), observed.digest()}) == 4
    assert receipt.source_snapshot.integrity_statement == "sha256_integrity_linkage_not_authorship_v1"


@pytest.mark.parametrize("path", ["/absolute.csv", "../escape.csv", "paper/../escape.csv"])
def test_source_snapshot_rejects_path_escape(path: str):
    from bp_registry.campaigns.targets import ByteSnapshotV1

    with pytest.raises(ValidationError):
        ByteSnapshotV1.from_bytes(path, b"x")


def test_source_snapshot_rejects_symlink_escape_and_tampering(tmp_path):
    from bp_registry.campaigns.targets import read_confined_snapshot

    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_bytes(b"not evidence")
    (evidence_root / "link.csv").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        read_confined_snapshot(evidence_root, "link.csv")

    source = evidence_root / "table.csv"
    source.write_bytes(b"source bytes")
    snapshot = read_confined_snapshot(evidence_root, "table.csv")
    assert snapshot.sha256 == sha256(b"source bytes").hexdigest()
    source.write_bytes(b"changed bytes")
    assert sha256(source.read_bytes()).hexdigest() != snapshot.sha256


def test_unavailable_denominator_never_infers_an_observed_count():
    from bp_registry.campaigns.targets import SourceDenominatorV1

    unavailable = SourceDenominatorV1(status="unavailable", reason="not published")
    assert unavailable.count is None
    with pytest.raises(ValidationError):
        SourceDenominatorV1(status="unavailable", count=10, reason="not published")
    with pytest.raises(ValidationError):
        SourceDenominatorV1(status="observed")


def _digitized_receipt():
    from bp_registry.campaigns.targets import (
        AxisCalibrationPointV1,
        ByteSnapshotV1,
        DigitizedClickV1,
        DigitizationExtractionPassV1,
        DigitizationTargetReceiptV1,
        FigureLocatorV1,
        FrozenDigitizationIntervalV1,
        SourceDenominatorV1,
        SourceIdentityV1,
        XYCalibrationV1,
    )

    calibration = XYCalibrationV1(
        x_scale="log10",
        y_scale="log10",
        x1=AxisCalibrationPointV1(pixel_x=10.0, pixel_y=200.0, value=0.001),
        x2=AxisCalibrationPointV1(pixel_x=110.0, pixel_y=200.0, value=0.01),
        y1=AxisCalibrationPointV1(pixel_x=10.0, pixel_y=190.0, value=0.1),
        y2=AxisCalibrationPointV1(pixel_x=10.0, pixel_y=90.0, value=0.001),
    )

    def extraction(pass_id: str, operator: str, at: str, pixel_x: float, pixel_y: float):
        x, y = calibration.transformed_values(pixel_x, pixel_y)
        return DigitizationExtractionPassV1(
            pass_id=pass_id,
            operator_label=operator,
            extracted_at=at,
            project_snapshot=ByteSnapshotV1.from_bytes(f"digitization/{pass_id}.wpd", pass_id.encode()),
            export_snapshot=ByteSnapshotV1.from_bytes(f"digitization/{pass_id}.csv", b"x,y\n" + f"{x},{y}\n".encode()),
            clicks=[DigitizedClickV1(point_id="p010", pixel_x=pixel_x, pixel_y=pixel_y, x=x, y=y)],
        )

    first = extraction("pass-a", "operator-a", "2026-10-11T12:00:00Z", 60.0, 140.0)
    second = extraction("pass-b", "operator-b", "2026-10-11T12:05:00Z", 61.0, 139.0)
    x_values = [first.clicks[0].x, second.clicks[0].x]
    y_values = [first.clicks[0].y, second.clicks[0].y]
    return DigitizationTargetReceiptV1(
        schema="campaign_digitization_target_v1",
        target_id="synthetic-figure-p010",
        source=SourceIdentityV1(uri_or_doi="https://doi.org/10.0000/synthetic", revision="published-v1", accessed_on=date(2026, 10, 11)),
        source_snapshot=ByteSnapshotV1.from_bytes("papers/synthetic/source.pdf", b"pdf bytes"),
        image_snapshot=ByteSnapshotV1.from_bytes("papers/synthetic/figure.png", b"image bytes"),
        figure=FigureLocatorV1(figure_id="Figure 3", page=8, panel_id="b", curve_id="BP", image_width=800, image_height=600, crop_left=10, crop_top=20, crop_width=500, crop_height=400, image_transform="source_page_to_crop_pixels_v1"),
        tool_name="WebPlotDigitizer",
        tool_version="4.7",
        calibration=calibration,
        passes=[first, second],
        intervals=[FrozenDigitizationIntervalV1(point_id="p010", x_lower=min(x_values), x_upper=max(x_values), y_lower=min(y_values), y_upper=max(y_values), x_spread=max(x_values) - min(x_values), y_spread=max(y_values) - min(y_values))],
        source_denominator=SourceDenominatorV1(status="unavailable", reason="paper reports no count"),
    )


def test_digitization_round_trip_binds_calibration_clicks_and_repeated_precision():
    receipt = _digitized_receipt()
    encoded = receipt.model_dump(mode="json", by_alias=True)
    rebuilt = type(receipt).model_validate_json(json.dumps(encoded))
    assert rebuilt.digest() == receipt.digest()
    assert receipt.intervals[0].x_spread > 0.0
    assert receipt.intervals[0].y_spread > 0.0

    axis_drift = copy.deepcopy(encoded)
    axis_drift["calibration"]["x_scale"] = "linear"
    with pytest.raises(ValidationError):
        type(receipt).model_validate_json(json.dumps(axis_drift))

    click_drift = copy.deepcopy(encoded)
    click_drift["passes"][0]["clicks"][0]["pixel_x"] += 1.0
    with pytest.raises(ValidationError):
        type(receipt).model_validate_json(json.dumps(click_drift))


def test_digitization_rejects_single_pass_bad_log_calibration_and_tuned_interval():
    receipt = _digitized_receipt()
    payload = receipt.model_dump(mode="json", by_alias=True)

    one_pass = copy.deepcopy(payload)
    one_pass["passes"] = one_pass["passes"][:1]
    with pytest.raises(ValidationError):
        type(receipt).model_validate_json(json.dumps(one_pass))

    invalid_log = copy.deepcopy(payload)
    invalid_log["calibration"]["x1"]["value"] = 0.0
    with pytest.raises(ValidationError):
        type(receipt).model_validate_json(json.dumps(invalid_log))

    tuned_interval = copy.deepcopy(payload)
    tuned_interval["intervals"][0]["y_upper"] += 0.01
    with pytest.raises(ValidationError):
        type(receipt).model_validate_json(json.dumps(tuned_interval))
