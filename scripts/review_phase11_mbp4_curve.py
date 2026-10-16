#!/usr/bin/env python3
"""Prepare and verify the non-authorizing MBP4 Figure 6 curve review.

The Figure 6 plot is evidence for a selected MBP4 ``alpha=1.5`` curve, but
it is not an executable source target.  This command preserves that boundary:
it binds the exact PDF, plot geometry, and fixed-inhibition recurrence while
making every absent campaign fact a named blocker.  Materialization belongs to
Task 3 after the blocking human review and is deliberately unavailable here.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = ROOT / "data/source-targets/phase11-mbp4-curve-review.json"
MECHANISM_TARGET = ROOT / "data/source-targets/phase11-mbp4-figures8-9-five-qubit.json"
MECHANISM_ASSESSMENT = ROOT / "data/results/phase11-mbp4-figures8-9/assessment.json"
SOURCE_PDF = Path("/tmp/phase11-mbp4.pdf")

SOURCE = {
    "citation": "Kuo and Lai, Modified Belief Propagation Decoding Algorithms for Quantum LDPC Codes, arXiv:2104.13659",
    "id": "kuo-lai-2021-mbp4-primary-pdf",
    "path": "/tmp/phase11-mbp4.pdf",
    "sha256": "37d3a734c1e617eecc45ed1cd641dd92b89adfd7e15390ef403d90637c547f23",
}

# The PDF's Figure 6 red down-triangle vector markers.  These are PDF-space
# positions (points), ordered left-to-right, not inferred physical epsilon or
# logical-error-rate values.  Their axis transformation remains blocked below.
ALPHA_1_5_MARKER_CENTERS = (
    (83.40110778808594, 188.94699096679688),
    (103.21946716308594, 177.64712524414062),
    (123.03788757324219, 167.50827026367188),
    (142.85629272460938, 156.85194396972656),
    (162.67471313476562, 143.10565185546875),
    (182.49307250976562, 132.23590087890625),
    (202.31149291992188, 99.10411071777344),
    (222.12989807128906, 92.74429321289062),
    (241.94833374023438, 83.02734375),
    (261.76666259765625, 79.1103515625),
    (281.5850830078125, 70.85488891601562),
)

REQUIRED_FIELDS = frozenset({
    "source_identity",
    "curve_panel_identity",
    "curve_legend_identity",
    "code_channel",
    "alpha_beta",
    "schedule",
    "numerical_profile",
    "iteration_cap",
    "denominator",
    "stopping_rule",
    "axis_transform",
    "coordinate_extraction",
    "digitization_uncertainty",
    "interval_method",
    "tolerance",
    "resource_ceiling",
    "author_implementation_identity",
    "recurrence_compatibility",
})
BLOCKERS = tuple(sorted({
    "author_implementation_identity",
    "beta",
    "denominator",
    "digitization_uncertainty",
    "interval_method",
    "iteration_cap",
    "numerical_profile",
    "resource_ceiling",
    "schedule",
    "stopping_rule",
    "tolerance",
    "transformed_coordinates",
}))


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: object) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _entry(
    field_id: str,
    excerpt: str,
    interpretation: str,
    *,
    verdict: str,
    blocker: str | None,
    anchor: str,
) -> dict[str, object]:
    return {
        "compatibility_verdict": verdict,
        "discrepancy_or_blocker": blocker,
        "excerpt": excerpt,
        "excerpt_sha256": sha256(excerpt.encode("utf-8")).hexdigest(),
        "field_id": field_id,
        "locator": {"anchor": anchor, "kind": "primary_pdf", "page": 10},
        "normalized_interpretation": interpretation,
        "reviewer_state": "pending_human_review",
        "source": SOURCE,
    }


def _evidence_entries() -> list[dict[str, object]]:
    return [
        _entry("source_identity", "Figure 6 appears on PDF page 10 of the pinned MBP4 primary source.", "The candidate binds the supplied primary-PDF SHA-256; it does not establish author-code identity.", verdict="compatible", blocker=None, anchor="pinned PDF identity and Figure 6 page"),
        _entry("curve_panel_identity", "Fig. 6. Decoding the [[5, 1, 3]] code using Algorithm 1 with various alpha.", "The selected panel is Figure 6, not the deterministic Figures 8-9 mechanism.", verdict="compatible", blocker=None, anchor="Figure 6 caption"),
        _entry("curve_legend_identity", "The Figure 6 legend labels MBP4 alpha=1, alpha=1.4, alpha=1.5, alpha=1.6, alpha=1.8, Uncoded, and BDD, t=1.", "The reviewed selected series is MBP4 alpha=1.5, drawn with red down-triangle markers.", verdict="compatible", blocker=None, anchor="Figure 6 legend"),
        _entry("code_channel", "The Figure 6 x-axis is epsilon (depolarizing error rate) and the caption identifies the [[5, 1, 3]] code.", "The series is a depolarizing-channel logical-error-rate plot for the five-qubit code.", verdict="compatible", blocker=None, anchor="Figure 6 axes and caption"),
        _entry("alpha_beta", "Fig. 6. Decoding the [[5, 1, 3]] code using Algorithm 1 with various alpha.", "Alpha=1.5 is identified by the legend. Figure 6 does not state a beta value, so beta is not inherited from Figures 8-9.", verdict="unresolved", blocker="beta is absent from the Figure 6 statistical-panel contract", anchor="Figure 6 caption and legend"),
        _entry("schedule", "Fig. 6. Decoding the [[5, 1, 3]] code using Algorithm 1 with various alpha.", "The figure cites Algorithm 1 but does not state the curve's execution schedule as a frozen campaign setting.", verdict="unresolved", blocker="schedule is not explicit for the Figure 6 curve", anchor="Figure 6 caption"),
        _entry("numerical_profile", "The Figure 6 caption identifies Algorithm 1 and alpha variants but supplies no precision, clipping, normalization, or tie conventions.", "The canonical numerical profile cannot be promoted to a source-equivalent profile.", verdict="unresolved", blocker="numerical profile is not reported for Figure 6", anchor="Figure 6 caption and panel"),
        _entry("iteration_cap", "Fig. 6. Decoding the [[5, 1, 3]] code using Algorithm 1 with various alpha.", "No exact maximum iteration count is printed for the statistical curve.", verdict="unresolved", blocker="iteration cap is not reported for Figure 6", anchor="Figure 6 caption and surrounding page text"),
        _entry("denominator", "‘Uncoded’ is uncoded block error rate of N = 5.", "N=5 describes the uncoded block calculation; it is not a stochastic trial denominator for the MBP4 points.", verdict="unresolved", blocker="per-point stochastic denominator is not reported", anchor="Figure 6 caption"),
        _entry("stopping_rule", "Fig. 6. Decoding the [[5, 1, 3]] code using Algorithm 1 with various alpha.", "The panel does not state a trial/error stopping rule.", verdict="unresolved", blocker="stopping rule is not reported for Figure 6", anchor="Figure 6 caption and panel"),
        _entry("axis_transform", "The x-axis is epsilon (depolarizing error rate) and the y-axis is logical error rate; both axes display logarithmic decade ticks.", "The axis semantics are known, but a reviewed calibration for source coordinates is not yet frozen.", verdict="unresolved", blocker="axis calibration and transform parameters are not reviewed", anchor="Figure 6 axes"),
        _entry("coordinate_extraction", "The selected alpha=1.5 series is represented by red down-triangle markers in Figure 6.", "Eleven PDF-space marker centers are inventoried, while their physical coordinates and intervals remain unreviewed.", verdict="unresolved", blocker="physical epsilon and logical-error coordinates require reviewed digitization", anchor="Figure 6 selected series"),
        _entry("digitization_uncertainty", "Figure 6 provides plotted markers rather than a tabulated coordinate list.", "No uncertainty model has been approved for converting PDF-space marker centers into physical coordinates.", verdict="unresolved", blocker="digitization uncertainty is not specified", anchor="Figure 6 selected series"),
        _entry("interval_method", "Figure 6 shows logical-error-rate curves without error bars or a stated confidence-interval procedure.", "No interval method is available for a source-faithful statistical assessment.", verdict="unresolved", blocker="interval method is not reported", anchor="Figure 6 panel"),
        _entry("tolerance", "Figure 6 has no stated numerical curve-agreement tolerance.", "Visual agreement cannot become an acceptance threshold.", verdict="unresolved", blocker="curve tolerance is not reported", anchor="Figure 6 caption and panel"),
        _entry("resource_ceiling", "Figure 6 reports a curve but gives no compute, time, memory, or work bound.", "A later campaign must independently freeze a resource ceiling.", verdict="unresolved", blocker="resource ceiling is not reported", anchor="Figure 6 caption and panel"),
        _entry("author_implementation_identity", "The Figure 6 page identifies Algorithm 1 but supplies no repository URL, revision, or executable artifact digest.", "No author implementation is pinned, so canonical recurrence compatibility is not implementation equivalence.", verdict="unresolved", blocker="author implementation identity is not verified", anchor="Figure 6 and surrounding primary-source page"),
        _entry("recurrence_compatibility", "Figure 6 identifies Algorithm 1 with MBP4 alpha variants.", "The platform fixed-inhibition MBP4 recurrence supports an alpha=1.5 canonical route; unresolved schedule/numerics/author-code facts prevent source-equivalence promotion.", verdict="compatible", blocker=None, anchor="Figure 6 caption; src/bp_registry/quaternary/mbp4.py fixed-inhibition boundary"),
    ]


def _points() -> list[dict[str, object]]:
    points: list[dict[str, object]] = []
    for ordinal, marker_center in enumerate(ALPHA_1_5_MARKER_CENTERS, start=1):
        points.append({
            "axis_coordinates": {
                "raw_pdf_coordinates": list(marker_center),
                "status": "blocked_metadata",
                "transformed_interval": None,
            },
            "field_blockers": ["transformed_coordinates", "digitization_uncertainty", "interval_method", "tolerance"],
            "point_id": f"mbp4_alpha_1_5_marker_{ordinal:02d}",
            "source_locator": {
                "anchor": f"Figure 6 red down-triangle marker {ordinal:02d} ordered left-to-right",
                "kind": "primary_pdf_vector_marker",
                "page": 10,
            },
        })
    return points


def build_candidate() -> dict[str, object]:
    if not SOURCE_PDF.is_file():
        raise ValueError(f"primary source PDF is unavailable: {SOURCE_PDF}")
    if file_sha256(SOURCE_PDF) != SOURCE["sha256"]:
        raise ValueError("primary source PDF SHA-256 differs from the pinned source")
    mechanism_target = json.loads(MECHANISM_TARGET.read_text(encoding="utf-8"))
    mechanism_assessment = json.loads(MECHANISM_ASSESSMENT.read_text(encoding="utf-8"))
    if mechanism_target["target_id"] == "phase11-mbp4-figure6-alpha-1.5-curve":
        raise ValueError("Figure 6 target identity collides with Figures 8-9 mechanism")
    if mechanism_assessment["claim_scope"] != "deterministic_mechanism_only_not_a_curve_or_ranking":
        raise ValueError("existing mechanism assessment claim scope drifted")
    candidate: dict[str, object] = {
        "authorizes_execution": False,
        "curve": {
            "legend_label": "MBP4, alpha=1.5",
            "panel": "Figure 6",
            "point_count": len(ALPHA_1_5_MARKER_CENTERS),
            "points": _points(),
            "series_id": "mbp4_alpha_1_5",
        },
        "evidence_entries": sorted(_evidence_entries(), key=lambda entry: str(entry["field_id"])),
        "field_blockers": list(BLOCKERS),
        "mechanism_evidence": {
            "assessment_path": "data/results/phase11-mbp4-figures8-9/assessment.json",
            "assessment_sha256": file_sha256(MECHANISM_ASSESSMENT),
            "claim_scope": mechanism_assessment["claim_scope"],
            "relation": "separate_non_aliasing_evidence",
            "target_id": mechanism_target["target_id"],
        },
        "recurrence_compatibility": {
            "canonical_route": "fixed_inhibition_mbp4_alpha",
            "source_locator": "Figure 6 caption; Algorithm 1",
            "status": "compatible_but_not_source_equivalent",
            "unresolved_fields": ["schedule", "numerical_profile", "author_implementation_identity"],
        },
        "review_decision": "pending_human_review",
        "review_digest": None,
        "review_id": "phase11_mbp4_curve_review_v1",
        "schema": "phase11-mbp4-figure6-curve-review-v1",
        "source": SOURCE,
        "source_execution": {
            "admitted_shots": 0,
            "eligible": False,
            "status": "blocked_metadata",
        },
        "target_id": "phase11-mbp4-figure6-alpha-1.5-curve",
    }
    candidate["review_digest"] = digest({key: value for key, value in candidate.items() if key != "review_digest"})
    return candidate


def verify_candidate(review: dict[str, Any]) -> None:
    expected = build_candidate()
    if review.get("review_digest") != digest({key: value for key, value in review.items() if key != "review_digest"}):
        raise ValueError("review digest does not match canonical review bytes")
    if review["authorizes_execution"] or review["source_execution"]["eligible"] or review["source_execution"]["admitted_shots"] != 0:
        raise ValueError("candidate must remain non-authorizing with zero admitted shots")
    entries = {entry["field_id"]: entry for entry in review["evidence_entries"]}
    if set(entries) != REQUIRED_FIELDS or len(entries) != len(review["evidence_entries"]):
        raise ValueError("required field coverage is incomplete")
    for field_id, entry in entries.items():
        if entry["source"] != SOURCE or entry["locator"]["page"] != 10:
            raise ValueError(f"{field_id}: primary-source identity or locator drifted")
        if entry["excerpt_sha256"] != sha256(entry["excerpt"].encode("utf-8")).hexdigest():
            raise ValueError(f"{field_id}: excerpt digest mismatch")
        if entry["reviewer_state"] != "pending_human_review":
            raise ValueError(f"{field_id}: candidate prematurely records a review outcome")
        if entry["compatibility_verdict"] == "unresolved" and not entry["discrepancy_or_blocker"]:
            raise ValueError(f"{field_id}: unresolved evidence lacks a field-level blocker")
    points = review["curve"]["points"]
    if len(points) != len(ALPHA_1_5_MARKER_CENTERS):
        raise ValueError("selected series point coverage is incomplete")
    for ordinal, point in enumerate(points, start=1):
        if point["point_id"] != f"mbp4_alpha_1_5_marker_{ordinal:02d}":
            raise ValueError("point inventory ordering or identity drifted")
        if point["axis_coordinates"]["raw_pdf_coordinates"] != list(ALPHA_1_5_MARKER_CENTERS[ordinal - 1]):
            raise ValueError("raw PDF marker coordinate drifted")
        if point["axis_coordinates"]["transformed_interval"] is not None or not point["field_blockers"]:
            raise ValueError("unreviewed coordinate transformation must remain explicitly blocked")
    if review != expected:
        raise ValueError("review content differs from the complete digest-bound primary-source candidate")


def prepare(output: Path) -> None:
    candidate = build_candidate()
    verify_candidate(candidate)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"authorizes_execution": False, "review": str(output), "review_digest": candidate["review_digest"]}, sort_keys=True))


def materialize(_: Path) -> None:
    raise ValueError("materialize is reserved for Task 3 after the blocking human review")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--output", type=Path, default=DEFAULT_REVIEW)
    verify_parser = commands.add_parser("verify-candidate")
    verify_parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    materialize_parser = commands.add_parser("materialize")
    materialize_parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            prepare(args.output)
        elif args.command == "verify-candidate":
            verify_candidate(json.loads(args.review.read_text(encoding="utf-8")))
            print(json.dumps({"review": str(args.review), "verified": True}, sort_keys=True))
        else:
            materialize(args.review)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
