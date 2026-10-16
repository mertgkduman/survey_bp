#!/usr/bin/env python3
"""Prepare and verify a non-authorizing Q-BPGD Figure 7 evidence package.

This command deliberately separates primary-source observations from the
project's continued-message implementation.  It cannot admit source shots or
promote the frozen A5 target; those actions require the later reviewed decision
materialization task.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = ROOT / "data/source-targets/phase11-qbpgd-figure7-review.json"
A5_TARGET = ROOT / "data/source-targets/phase11-qbpgd-figure7-a5.json"
A5_PROVENANCE = ROOT / "data/artifacts/quaternary-a5.provenance.json"

PDF_SOURCE = {
    "id": "yao-2023-qbpgd-v2-pdf",
    "path": "/tmp/phase11-qbpgd-v2.pdf",
    "sha256": "cdc0af68a2edb55ab8c961989333258aac2cb8e30b7943a14c076dab4e719404",
    "citation": "Yao et al., Q-BPGD v2, arXiv:2312.10950v2",
}
A5_SOURCE = {
    "id": "a5-official-polynomial-transcription",
    "uri": "https://arxiv.org/src/1904.02703v3",
    "sha256": "139a695295d1392f82a65977c28eb41e43169efc68ff00d87978832cf8c5b693",
    "citation": "Official A5 source definition, arXiv:1904.02703v3",
}
POINTS = (0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10)
REQUIRED_FIELDS = frozenset({
    "message_lifecycle",
    "update_and_tie_order",
    "normalization",
    "fixation_and_decimation",
    "update_equations",
    "curve_panel_identity",
    *(f"coordinate_p_{point:0.02f}" for point in POINTS),
    "digitization_uncertainty",
    "tolerance",
    "a5_construction",
    "figure_settings",
    "author_implementation_identity",
    "stopping_rule",
    "denominator",
    "numerical_conventions",
    "source_route_fidelity",
})
VALID_VERDICTS = frozenset({"compatible", "unresolved", "incompatible"})
VALID_LOCATOR_KINDS = frozenset({"primary_pdf", "authoritative_source"})


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: object) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def _entry(
    field_id: str,
    *,
    source: dict[str, str],
    page: int,
    locator: str,
    excerpt: str,
    interpretation: str,
    confidence: str,
    verdict: str,
    blocker: str | None,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "field_id": field_id,
        "source": source,
        "locator": {"kind": "primary_pdf" if source["id"] == PDF_SOURCE["id"] else "authoritative_source", "page": page, "anchor": locator},
        "excerpt": excerpt,
        "excerpt_sha256": sha256(excerpt.encode("utf-8")).hexdigest(),
        "normalized_interpretation": interpretation,
        "confidence": confidence,
        "compatibility_verdict": verdict,
        "discrepancy_or_blocker": blocker,
        "reviewer_state": "pending_human_review",
    }
    if details is not None:
        entry["details"] = details
    return entry


def _source_settings() -> dict[str, object]:
    return {
        "code": "A5 [[180,10,15<=d<=18]]",
        "channel": "depolarizing",
        "qbp_iterations": 100,
        "qbpgd_iterations_per_round": 10,
        "epsilon": "1e-10",
        "round_limit": 180,
        "early_syndrome_stop": True,
        "points_p": list(POINTS),
        "bp_osd": {"order": 10, "provenance": "third_party_ref_15_figure_6"},
        "stopping": {"error_cases": 100, "denominator": "trials_until_100_error_cases"},
    }


def build_candidate() -> dict[str, object]:
    """Build the whole candidate from source observations and stable blockers."""
    a5_target = json.loads(A5_TARGET.read_text(encoding="utf-8"))
    provenance = json.loads(A5_PROVENANCE.read_text(encoding="utf-8"))
    settings = _source_settings()
    entries = [
        _entry(
            "message_lifecycle", source=PDF_SOURCE, page=14, locator="Section 6 paragraph after Eq. (43); Algorithm 3 lines 3-15",
            excerpt="Q-BPGD iterates between Q-BP and decimation in rounds with r going from 1 to n, with early termination upon Q-BP convergence.",
            interpretation="The source establishes rounds and early stopping but does not state whether Q-BP messages are reset or continued between rounds.",
            confidence="high", verdict="unresolved", blocker="continued_message_lifecycle_unresolved; D-14 persistence remains a project interpretation, not source evidence.",
        ),
        _entry(
            "update_and_tie_order", source=PDF_SOURCE, page=14, locator="Algorithm 3 lines 4-15; Eqs. (41)-(43)",
            excerpt="vi = arg max over undecimated nodes of gamma(vi); gamma_i^* = arg max over j in {0,1,2,3} p_vi,j.",
            interpretation="The source orders Q-BP, syndrome check, target argmax, state argmax, and fixation, but gives no tie rule for either argmax.",
            confidence="high", verdict="unresolved", blocker="tie_rule_unresolved; the canonical lowest-index selection is not inherited as source-equivalent.",
        ),
        _entry(
            "normalization", source=PDF_SOURCE, page=14, locator="Eqs. (38)-(40); Algorithm 3 lines 1 and 10-14",
            excerpt="Each variable node contains information of four normalized probabilities; the fixation vectors are written as (1-epsilon, epsilon, epsilon, epsilon).",
            interpretation="The paper names normalized node probabilities and literal fixation vectors but does not specify the message normalization interface used by the implementation.",
            confidence="high", verdict="unresolved", blocker="normalization_interface_unresolved; D-15 cannot be treated as a source-defined numerical convention.",
        ),
        _entry(
            "fixation_and_decimation", source=PDF_SOURCE, page=14, locator="Algorithm 3 lines 1-16; Eq. (42)",
            excerpt="For r = 1 to n, run Q-BP for T iterations; on no syndrome match, select the most reliable undecimated node and replace its channel message by the epsilon fixation vector for the selected Pauli state.",
            interpretation="Source-backed: at most n rounds, early syndrome stop, selection among undecimated variables, and epsilon=1e-10 literal fixation vectors.",
            confidence="high", verdict="compatible", blocker=None,
        ),
        _entry(
            "update_equations", source=PDF_SOURCE, page=14, locator="Section 6 paragraph beginning 'For detailed descriptions of Q-BP'; Eqs. (38)-(43)",
            excerpt="For detailed descriptions of Q-BP, we refer readers to [67] and [31, Algorithm 1]; an efficient log domain implementation is discussed in [68].",
            interpretation="The pinned paper supplies Q-BPGD control equations but delegates Q-BP message equations to other works, so it cannot by itself qualify the platform's scalar Q-BP kernel as the author implementation.",
            confidence="high", verdict="unresolved", blocker="qbp_update_equations_not_bound_to_author_implementation; no authoritative implementation identity is pinned.",
        ),
        _entry(
            "curve_panel_identity", source=PDF_SOURCE, page=15, locator="Figure 7 caption",
            excerpt="Performance of various decoders on the [[180, 10, 15 <= d <= 18]] A5 code over depolarizing noise; Q-BP and Q-BPGD have locally collected points, while BP-OSD-10 points are taken from [15, Figure 6].",
            interpretation="Figure 7 is the A5 depolarizing panel with Q-BP, Q-BPGD T=10, and third-party BP-OSD-10 series.",
            confidence="high", verdict="unresolved", blocker="Figure identity is resolved, but the Q-BP and Q-BPGD ordinate coordinates are not source-extracted or reviewed.",
        ),
        _entry(
            "digitization_uncertainty", source=PDF_SOURCE, page=15, locator="Figure 7 plotted panel",
            excerpt="The figure supplies a logarithmic Block Error Rate plot and x-axis labels from 0.04 through 0.10, without a numerical coordinate table.",
            interpretation="No reviewed digitization method, image calibration, or ordinate interval is present in the source package.",
            confidence="high", verdict="unresolved", blocker="digitization_uncertainty_unreviewed; no y-coordinate may be used as a source target.",
        ),
        _entry(
            "tolerance", source=PDF_SOURCE, page=15, locator="Figure 7 caption and panel",
            excerpt="The caption states the simulated stopping count but supplies no coordinate-extraction tolerance or curve-agreement acceptance rule.",
            interpretation="No source-qualified numerical tolerance exists for Figure 7 comparison.",
            confidence="high", verdict="unresolved", blocker="figure_tolerance_unresolved; numerical resemblance cannot authorize source equivalence.",
        ),
        _entry(
            "a5_construction", source=A5_SOURCE, page=1, locator="Official A5 source transcription recorded in quaternary-a5.provenance.json",
            excerpt="l=90; a(x)=1+x^28+x^80+x^89; b(x)=1+x^2+x^21+x^25; Hx=[A|B] and Hz=[B^T|A^T].",
            interpretation="The frozen project A5 artifact is reconstructed from the official polynomial source; its distance remains source-reported bounds, not independently re-proven here.",
            confidence="high", verdict="compatible", blocker=None,
        ),
        _entry(
            "figure_settings", source=PDF_SOURCE, page=14, locator="Section 6 final paragraph before Figure 7",
            excerpt="Figure 7 presents Q-BPGD with T=10 on A5 over depolarizing noise, compared with Q-BP T=100 and BP-OSD order 10 from [15, Figure 6].",
            interpretation="The Figure 7 settings are frozen for review as A5/depolarizing, Q-BPGD T=10, Q-BP T=100, and third-party BP-OSD order 10.",
            confidence="high", verdict="compatible", blocker=None,
        ),
        _entry(
            "author_implementation_identity", source=PDF_SOURCE, page=14, locator="Section 6 implementation statement",
            excerpt="In our software implementation for the simulation results in this section, we set epsilon = 1 x 10^-10 for numerical stability.",
            interpretation="The paper establishes that an implementation existed and names epsilon, but provides no repository URL, revision, artifact digest, or executable identity for it.",
            confidence="high", verdict="unresolved", blocker="author_implementation_identity_unverified; name-only existence is insufficient under T-11-19A.",
        ),
        _entry(
            "stopping_rule", source=PDF_SOURCE, page=15, locator="Figure 7 caption",
            excerpt="The data points of Q-BP and Q-BPGD are collected by running simulations until we observe 100 error cases.",
            interpretation="Source-backed stopping rule: stop each Q-BP/Q-BPGD point after 100 observed error cases.",
            confidence="high", verdict="compatible", blocker=None,
        ),
        _entry(
            "denominator", source=PDF_SOURCE, page=15, locator="Figure 7 caption",
            excerpt="The data points of Q-BP and Q-BPGD are collected by running simulations until we observe 100 error cases.",
            interpretation="The paper reports an error-count stopping rule, but it does not report per-point trial denominators or a denominator convention in the Figure 7 caption.",
            confidence="high", verdict="unresolved", blocker="figure7_point_denominators_unreported; exact trial counts cannot be reconstructed from the figure.",
        ),
        _entry(
            "numerical_conventions", source=PDF_SOURCE, page=14, locator="Section 6, Eqs. (38)-(43), and implementation sentence",
            excerpt="The paper gives normalized four-state probabilities and epsilon=1 x 10^-10 for numerical stability; it refers to external works for detailed Q-BP and log-domain implementation descriptions.",
            interpretation="Only the literal epsilon and probability model are source stated; float precision, clipping, convergence tolerance, update schedule, and exact normalization implementation are not pinned.",
            confidence="high", verdict="unresolved", blocker="numerical_conventions_incomplete; platform float64/saturation choices remain canonical adaptation.",
        ),
        _entry(
            "source_route_fidelity", source=PDF_SOURCE, page=14, locator="Section 6 and Algorithm 3",
            excerpt="The source supplies Algorithm 3 control flow, depolarizing priors, fixation vectors, epsilon, and Figure 7 settings.",
            interpretation="The current platform route remains canonical_adaptation because lifecycle, ties, normalization interface, full Q-BP equations/numerics, author implementation identity, figure ordinates, uncertainty, tolerance, and denominators are unresolved.",
            confidence="high", verdict="unresolved", blocker="source_equivalence_blocked_by_unresolved_required_fields; zero source shots admitted.",
        ),
    ]
    for point in POINTS:
        entries.append(_entry(
            f"coordinate_p_{point:0.02f}", source=PDF_SOURCE, page=15, locator="Figure 7 x-axis tick and plotted curves",
            excerpt=f"Figure 7 x-axis includes the displayed probability tick {point:0.02f} and curves for Q-BP and Q-BPGD, T = 10.",
            interpretation=f"x={point:0.02f} is a displayed Figure 7 point location; neither Q-BP nor Q-BPGD y-coordinate or extraction interval is entered without reviewed digitization.",
            confidence="high", verdict="unresolved", blocker=f"figure7_y_coordinate_unreviewed_at_p_{point:0.02f}; no plotted ordinate or extraction interval is admitted.",
            details={
                "p": point,
                "curves": {
                    "qbp": {"y": None, "extraction_interval": None, "status": "blocked_metadata"},
                    "qbpgd": {"y": None, "extraction_interval": None, "status": "blocked_metadata"},
                    "bp_osd_10": {"status": "third_party_ref_15_not_a_qbpgd_target"},
                },
                "evidence_bindings": {
                    "settings_field_id": "figure_settings",
                    "author_identity_field_id": "author_implementation_identity",
                    "stopping_field_id": "stopping_rule",
                    "denominator_field_id": "denominator",
                    "uncertainty_field_id": "digitization_uncertainty",
                    "tolerance_field_id": "tolerance",
                },
            },
        ))
    candidate: dict[str, object] = {
        "schema": "phase11-qbpgd-figure7-review-v1",
        "review_id": "phase11_qbpgd_figure7_review_v1",
        "primary_sources": [PDF_SOURCE, A5_SOURCE],
        "a5": {
            "target_receipt_sha256": a5_target["target_receipt_sha256"],
            "artifact_raw_sha256": a5_target["artifact"]["raw_sha256"],
            "artifact_provenance_sha256": a5_target["artifact"]["provenance_sha256"],
            "provenance_semantic_sha256": provenance["artifact"]["semantic_sha256"],
            "source_snapshot_sha256": provenance["source"]["source_snapshot_sha256"],
            "distance_status": provenance["distance"],
        },
        "frozen_settings": settings,
        "frozen_settings_sha256": digest(settings),
        "evidence_entries": sorted(entries, key=lambda item: str(item["field_id"])),
        "proposed_fidelity": "canonical_adaptation",
        "source_execution": {
            "eligible": False,
            "admitted_shots": 0,
            "reason": "review package is non-authorizing and has unresolved required source-equivalence fields",
        },
        "authorizes_execution": False,
        "review_decision": "pending_human_review",
        "reviewer": None,
        "review_digest": None,
    }
    candidate["review_digest"] = digest({key: value for key, value in candidate.items() if key != "review_digest"})
    return candidate


def _error(message: str) -> None:
    raise ValueError(message)


def verify_candidate(review: dict[str, Any]) -> None:
    if review.get("schema") != "phase11-qbpgd-figure7-review-v1":
        _error("unexpected review schema")
    expected = build_candidate()
    if review.get("review_digest") != digest({key: value for key, value in review.items() if key != "review_digest"}):
        _error("review digest does not match canonical review bytes")
    if review.get("authorizes_execution") is not False or review.get("review_decision") != "pending_human_review":
        _error("candidate must remain non-authorizing and pending human review")
    source_execution = review.get("source_execution")
    if not isinstance(source_execution, dict) or source_execution.get("eligible") is not False or source_execution.get("admitted_shots") != 0:
        _error("candidate must retain zero admitted source shots")
    if review.get("proposed_fidelity") != "canonical_adaptation":
        _error("candidate cannot promote fidelity before review")
    if review.get("a5") != expected["a5"]:
        _error("A5 identity or provenance digest drifted")
    if review.get("frozen_settings") != expected["frozen_settings"] or review.get("frozen_settings_sha256") != expected["frozen_settings_sha256"]:
        _error("frozen Figure 7 settings drifted")
    entries = review.get("evidence_entries")
    if not isinstance(entries, list):
        _error("evidence entries must be a list")
    by_id = {entry.get("field_id"): entry for entry in entries if isinstance(entry, dict)}
    if set(by_id) != REQUIRED_FIELDS or len(by_id) != len(entries):
        missing = sorted(REQUIRED_FIELDS - set(by_id))
        extra = sorted(set(by_id) - REQUIRED_FIELDS)
        _error(f"incomplete required-field coverage; missing={missing}; extra={extra}")
    for field_id, entry in by_id.items():
        source = entry.get("source")
        locator = entry.get("locator")
        excerpt = entry.get("excerpt")
        if not isinstance(source, dict) or source.get("sha256") not in {PDF_SOURCE["sha256"], A5_SOURCE["sha256"]}:
            _error(f"{field_id}: source is not a pinned primary or authoritative source")
        if not isinstance(locator, dict) or locator.get("kind") not in VALID_LOCATOR_KINDS or not isinstance(locator.get("page"), int) or locator["page"] < 1 or not locator.get("anchor"):
            _error(f"{field_id}: invalid primary locator")
        if not isinstance(excerpt, str) or entry.get("excerpt_sha256") != sha256(excerpt.encode("utf-8")).hexdigest():
            _error(f"{field_id}: excerpt digest mismatch")
        if not entry.get("normalized_interpretation") or entry.get("compatibility_verdict") not in VALID_VERDICTS:
            _error(f"{field_id}: incomplete interpretation or compatibility verdict")
        if entry.get("reviewer_state") != "pending_human_review":
            _error(f"{field_id}: candidate has a premature reviewer state")
        if entry["compatibility_verdict"] != "compatible" and not entry.get("discrepancy_or_blocker"):
            _error(f"{field_id}: unresolved evidence requires a stable blocker")
    for point in POINTS:
        entry = by_id[f"coordinate_p_{point:0.02f}"]
        details = entry.get("details")
        if not isinstance(details, dict) or details.get("p") != point:
            _error(f"coordinate p={point:0.02f} missing point inventory")
        curves = details.get("curves")
        if not isinstance(curves, dict) or any(curves.get(curve, {}).get("y") is not None for curve in ("qbp", "qbpgd")):
            _error(f"coordinate p={point:0.02f} fabricates an unreviewed ordinate")
        if details.get("evidence_bindings") != {
            "settings_field_id": "figure_settings",
            "author_identity_field_id": "author_implementation_identity",
            "stopping_field_id": "stopping_rule",
            "denominator_field_id": "denominator",
            "uncertainty_field_id": "digitization_uncertainty",
            "tolerance_field_id": "tolerance",
        }:
            _error(f"coordinate p={point:0.02f} lacks field-level provenance bindings")
    blocked = {field_id for field_id, entry in by_id.items() if entry["compatibility_verdict"] != "compatible"}
    if not {"message_lifecycle", "update_and_tie_order", "normalization", "author_implementation_identity", "source_route_fidelity"} <= blocked:
        _error("required canonical-adaptation blockers are missing")


def prepare(output: Path) -> None:
    candidate = build_candidate()
    verify_candidate(candidate)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"review": str(output), "review_digest": candidate["review_digest"], "authorizes_execution": False}, sort_keys=True))


def materialize(_: Path) -> None:
    raise ValueError("materialize is reserved for Task 3 after the blocking human review; this route cannot modify the frozen target")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--output", type=Path, default=DEFAULT_REVIEW)
    verify_parser = subparsers.add_parser("verify-candidate")
    verify_parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    materialize_parser = subparsers.add_parser("materialize")
    materialize_parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            prepare(args.output)
        elif args.command == "verify-candidate":
            review = json.loads(args.review.read_text(encoding="utf-8"))
            verify_candidate(review)
            print(json.dumps({"review": str(args.review), "review_digest": review["review_digest"], "verified": True}, sort_keys=True))
        else:
            materialize(args.review)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
