#!/usr/bin/env python3
"""Prepare and verify the non-authorizing aSCED Figure 2 review candidate.

The candidate is deliberately an evidence inventory rather than a digitization
claim.  It carries every selected curve/point and uses a field-level blocked
state wherever the retained primary evidence does not support a value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = ROOT / "data/source-targets/phase11-asced-figure2-gb46.json"
NATIVE_PATH = ROOT / "data/native/phase11-asced-matched-input-qualification.json"
CROP_PATH = ROOT / "data/source-targets/phase11-asced-figure2-crop.png"
DEFAULT_REVIEW_PATH = ROOT / "data/source-targets/phase11-asced-figure2-review.json"

SCHEMA = "phase11_asced_figure2_review_v1"
SOURCE_PDF_SHA256 = "0eec129dde3026f8225ec7d5f2884dbefe37566c9f71d105cae0195e4e4abca5"
CROP_SHA256 = "e9f8ddb7d2d65ffd4deee1d0eec0d874fd38c011e0ac3783c9ca5b62b5e6abb0"
TARGET_RECEIPT_SHA256 = "b136b0aa81cc67bca48fc2bdfdb444f51cb6e77d9dd78715094252fece224013"
POINTS = (
    ("p003", 0.03), ("p004", 0.04), ("p005", 0.05), ("p006", 0.06),
    ("p007", 0.07), ("p008", 0.08), ("p009", 0.09), ("p010", 0.10),
)
BLOCKED_POINT_FIELDS = (
    "axis_calibration_anchors",
    "digitization_uncertainty",
    "extraction_tool_operator",
    "raw_click_coordinates",
    "tolerance",
    "transformed_coordinate_interval",
)


class ReviewError(RuntimeError):
    """Raised when a package would be incomplete, drifted, or authorizing."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReviewError(f"cannot load JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ReviewError(f"JSON evidence {path} must be an object")
    return value


def _file_sha256(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError as error:
        raise ReviewError(f"required source crop is unavailable: {path}") from error


def _resolved(value: Any) -> dict[str, Any]:
    return {"status": "resolved", "value": value}


def _blocked(field_id: str) -> dict[str, str]:
    return {"status": "blocked", "blocker_id": field_id}


def _point(member_id: str, curve_id: str, point_id: str, p: float) -> dict[str, Any]:
    prefix = f"{member_id}.{curve_id}.{point_id}"
    return {
        "point_id": point_id,
        "declared_x": _resolved({"parameter": "p", "value": p}),
        "bindings": {
            "source_snapshot": _resolved(SOURCE_PDF_SHA256),
            "source_crop": _resolved(CROP_SHA256),
            "figure_locator": _resolved({"figure": "Figure 2", "page": 4, "panel": "GB46"}),
            "legend_mapping": _resolved(curve_id),
            "axis_definitions": _resolved({"x": "p_linear", "y": "LER_log10"}),
        },
        "evidence_fields": {field: _blocked(f"{prefix}.{field}") for field in BLOCKED_POINT_FIELDS},
    }


def _curve(member_id: str, curve_name: str, legend_label: str, role: str) -> dict[str, Any]:
    curve_id = f"{member_id}.{curve_name}"
    return {
        "curve_id": curve_id,
        "legend_label": legend_label,
        "role": role,
        "points": [_point(member_id, curve_name, point_id, p) for point_id, p in POINTS],
    }


def _member(target: dict[str, Any], member_id: str, construction: str) -> dict[str, Any]:
    member = next((item for item in target.get("members", []) if item.get("member_id") == member_id), None)
    if not isinstance(member, dict):
        raise ReviewError(f"target lacks expected member {member_id}")
    if construction == "ordinary":
        curves = [
            _curve(member_id, "bp4_baseline", "Baseline", "baseline"),
            _curve(member_id, "bp4_asced_k16_delta2_l4", "K = 16, Δ = 2, L = 4", "variant"),
        ]
    else:
        curves = [
            _curve(member_id, "obp4_baseline", "Baseline", "baseline"),
            _curve(member_id, "obp4_asced_k16_delta2_l4", "K = 16, Δ = 2, L = 4", "variant"),
        ]
    return {
        "member_id": member_id,
        "construction": construction,
        "target_slot": member["target_slot"],
        "decoder_settings": _resolved(member["decoder"]),
        "stopping_rule": _resolved(member["stopping"]),
        "source_denominator": _blocked(f"{member_id}.source_denominator"),
        "curves": curves,
    }


def _all_blockers(members: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for member in members:
        blockers.append(member["source_denominator"]["blocker_id"])
        for curve in member["curves"]:
            for point in curve["points"]:
                blockers.extend(field["blocker_id"] for field in point["evidence_fields"].values())
    return sorted(blockers)


def build_candidate() -> dict[str, Any]:
    """Construct the whole candidate from pinned target, crop, and native receipts."""
    target = _load_json(TARGET_PATH)
    native = _load_json(NATIVE_PATH)
    if target.get("target_receipt_sha256") != TARGET_RECEIPT_SHA256:
        raise ReviewError("aSCED source target receipt digest drifted")
    if target.get("source_panel") != {"figure": "Figure 2", "code": "GB46"}:
        raise ReviewError("aSCED target no longer identifies Figure 2 GB46")
    if native.get("terminal") != "declined_unavailable" or native.get("matched_input_status") != "unavailable":
        raise ReviewError("native matched-input availability changed")
    if _file_sha256(CROP_PATH) != CROP_SHA256:
        raise ReviewError("pinned Figure 2 crop digest drifted")

    members = [
        _member(target, "asced-figure2-gb46-ordinary", "ordinary"),
        _member(target, "asced-figure2-gb46-overcomplete", "overcomplete"),
    ]
    candidate: dict[str, Any] = {
        "schema": SCHEMA,
        "review_state": "pending_human_review",
        "execution_authorized": False,
        "source_snapshot": {
            "uri": "https://arxiv.org/pdf/2605.06547v2",
            "revision": "arXiv:2605.06547v2",
            "sha256": SOURCE_PDF_SHA256,
            "integrity_statement": "sha256_integrity_linkage_not_authorship_v1",
        },
        "source_crop": {
            "relative_path": "data/source-targets/phase11-asced-figure2-crop.png",
            "sha256": CROP_SHA256,
            "source_page": 4,
            "source_page_rect_points": [300.0, 55.0, 555.0, 275.0],
            "render_scale": 4,
            "rendered_dimensions": [1020, 880],
        },
        "figure": {
            "figure": "Figure 2",
            "code": "GB46",
            "code_parameters": "[[46, 2, 9]] generalized bicycle",
            "channel": "depolarizing",
            "axes": {"x": {"quantity": "p", "transform": "linear"}, "y": {"quantity": "LER", "transform": "log10"}},
            "legend": {
                "baseline": "Baseline",
                "selected_variant": "K = 16, Δ = 2, L = 4",
                "unselected_configurations": ["K = 4, Δ = 2, L = 1", "K = 16, Δ = 4, L = 1", "K = 64, Δ = 2, L = 16"],
            },
        },
        "numerical_conventions": {
            "source_pauli_channel": "depolarizing",
            "metric": "logical_error_rate",
            "source_curve_coordinates": "not inferred from rendered plot before human review",
        },
        "target_binding": {
            "target_relative_path": "data/source-targets/phase11-asced-figure2-gb46.json",
            "target_receipt_sha256": TARGET_RECEIPT_SHA256,
            "target_document_sha256": _file_sha256(TARGET_PATH),
            "target_membership": [member["member_id"] for member in members],
        },
        "native_route": {
            "qualification_relative_path": "data/native/phase11-asced-matched-input-qualification.json",
            "qualification_sha256": _file_sha256(NATIVE_PATH),
            "terminal": native["terminal"],
            "matched_input_status": native["matched_input_status"],
            "source_fidelity_claim": native["source_fidelity_claim"],
            "canonical_fidelity": "canonical_adaptation",
        },
        "resource_bound": {
            "source_shots_admitted": 0,
            "execution_authorized": False,
            "reason": "candidate review package cannot authorize execution",
        },
        "members": members,
    }
    candidate["unresolved_field_ids"] = _all_blockers(members)
    candidate["candidate_sha256"] = _candidate_digest(candidate)
    return candidate


def _candidate_digest(candidate: dict[str, Any]) -> str:
    contents = dict(candidate)
    contents.pop("candidate_sha256", None)
    return _sha256_bytes(_canonical_bytes(contents))


def verify_candidate(review_path: Path) -> dict[str, Any]:
    """Fail closed unless the byte inventory is complete and remains non-authorizing."""
    review = _load_json(review_path)
    expected = build_candidate()
    if review != expected:
        raise ReviewError("candidate differs from the complete pinned Figure 2 inventory")
    if review.get("candidate_sha256") != _candidate_digest(review):
        raise ReviewError("candidate digest drifted")
    if review.get("execution_authorized") is not False or review.get("review_state") != "pending_human_review":
        raise ReviewError("candidate may not authorize execution or record a review decision")
    return {
        "schema": "phase11_asced_figure2_review_verification_v1",
        "candidate_sha256": review["candidate_sha256"],
        "members": len(review["members"]),
        "curves": sum(len(member["curves"]) for member in review["members"]),
        "points": sum(len(curve["points"]) for member in review["members"] for curve in member["curves"]),
        "unresolved_fields": len(review["unresolved_field_ids"]),
        "status": "candidate_structurally_complete_non_authorizing",
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "verify-candidate"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--review", type=Path, default=DEFAULT_REVIEW_PATH)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            candidate = build_candidate()
            _write_json(args.review, candidate)
            print(json.dumps(verify_candidate(args.review), sort_keys=True))
        else:
            print(json.dumps(verify_candidate(args.review), sort_keys=True))
    except ReviewError as error:
        print(f"review-candidate error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
