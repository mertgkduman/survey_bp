"""Regression coverage for the Q-BPGD Figure 7 A5 source target."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


ARTIFACT = Path("data/artifacts/quaternary-a5.json")
PROVENANCE = Path("data/artifacts/quaternary-a5.provenance.json")
TARGET = Path("data/source-targets/phase11-qbpgd-figure7-a5.json")
MANIFEST = Path("data/manifests/phase11-qbpgd-figure7-a5.json")
STUDY = Path("scripts/run_phase11_source_studies.py")
ROOT = Path(__file__).resolve().parents[1]
REVIEW_SCRIPT = ROOT / "scripts/review_phase11_qbpgd_figure7.py"
REVIEW = ROOT / "data/source-targets/phase11-qbpgd-figure7-review.json"

REQUIRED_REVIEW_FIELDS = {
    "message_lifecycle",
    "update_and_tie_order",
    "normalization",
    "fixation_and_decimation",
    "update_equations",
    "curve_panel_identity",
    *(f"coordinate_p_{point:0.02f}" for point in (0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10)),
    "digitization_uncertainty",
    "tolerance",
    "a5_construction",
    "figure_settings",
    "author_implementation_identity",
    "stopping_rule",
    "denominator",
    "numerical_conventions",
    "source_route_fidelity",
}


def test_a5_tracer_reconstructs_the_official_polynomial_css_artifact():
    from bp_registry.quaternary.problems import construct_qbpgd_a5_css

    code, receipt = construct_qbpgd_a5_css()

    assert code.n == 180
    assert receipt["construction"] == {
        "l": 90,
        "a_exponents": [0, 28, 80, 89],
        "b_exponents": [0, 2, 21, 25],
        "circulant_convention": "row_i_column_(i+exponent)_mod_l",
    }
    assert receipt["checks"]["commutes"] is True
    assert receipt["checks"]["claimed_parameters"] == {"n": 180, "k": 10}
    assert receipt["distance"]["status"] == "source_reported_bounds"
    assert receipt["distance"]["independently_verified"] is False
    assert receipt["artifact"]["pauli_semantic_sha256"] == sha256(code.semantic_bytes()).hexdigest()


def test_a5_artifact_and_provenance_bind_reconstructed_bytes_and_source_bounds():
    from bp_registry.quaternary.problems import build_qbpgd_a5_css_artifact
    from bp_registry.css import CssCode, semantic_sha256

    assert ARTIFACT.is_file() and PROVENANCE.is_file()
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    code = CssCode(**{key: artifact[key] for key in ("hx", "hz", "lx", "lz")}).validate()
    rebuilt, receipt = build_qbpgd_a5_css_artifact()

    assert code.hx.tolist() == rebuilt.hx.tolist()
    assert sha256(ARTIFACT.read_bytes()).hexdigest() == provenance["artifact"]["raw_sha256"]
    assert semantic_sha256(code) == provenance["artifact"]["semantic_sha256"] == receipt["artifact"]["semantic_sha256"]
    assert provenance["independent_validation"]["commutator_nonzero_entries"] == 0
    assert provenance["distance"] == {"independently_verified": False, "status": "source_reported_bounds", "value": "15<=d<=18"}


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(STUDY), *arguments], text=True, capture_output=True, check=False)


def test_figure7_target_freezes_a5_qbpgd_settings_and_explicit_fidelity_blockers(tmp_path: Path):
    assert TARGET.is_file() and MANIFEST.is_file()
    target = json.loads(TARGET.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert target["paper"] == {"figure": "Figure 7", "code": "A5", "channel": "depolarizing"}
    assert target["settings"] == {
        "qbpgd": {"iterations_per_round": 10, "epsilon": 1e-10, "maximum_decimation_rounds": 180, "early_syndrome_stop": True},
        "ordinary_qbp": {"iterations": 100},
    }
    assert target["source_stopping"] == {"error_cases": 100, "denominator": "trials_until_100_error_cases"}
    assert target["artifact"]["raw_sha256"] == sha256(ARTIFACT.read_bytes()).hexdigest()
    assert target["artifact"]["provenance_sha256"] == sha256(PROVENANCE.read_bytes()).hexdigest()
    assert target["run_fidelity"] == "canonical_adaptation"
    assert target["source_author_code_identity"] == "unverified"
    assert {"continued_message_lifecycle_unresolved", "tie_rule_unresolved", "normalization_interface_unresolved", "figure_coordinates_unreviewed"}.issubset(target["qualification_blockers"])
    assert manifest["target_document_sha256"] == sha256(TARGET.read_bytes()).hexdigest()

    assessment = tmp_path / "assessment.json"
    process = _run("preflight", "--target", str(TARGET), "--manifest", str(MANIFEST), "--assessment", str(assessment))
    assert process.returncode == 0, process.stderr
    receipt = json.loads(assessment.read_text(encoding="utf-8"))
    assert receipt["status"] == "inconclusive"
    assert receipt["admitted_shots"] == 0
    assert receipt["run_fidelity"] == "canonical_adaptation"


def test_figure7_bounded_qualification_records_decimation_work_and_replays(tmp_path: Path):
    assessment = tmp_path / "qualification.json"
    process = _run("run", "--target", str(TARGET), "--manifest", str(MANIFEST), "--assessment", str(assessment))
    assert process.returncode == 0, process.stderr
    receipt = json.loads(assessment.read_text(encoding="utf-8"))

    assert receipt["status"] == "inconclusive"
    assert receipt["admitted_shots"] == 1
    qualification = receipt["qualification"]
    assert qualification["replay"] == "passed"
    assert qualification["performance_verdict"] == "not_assessed"
    assert qualification["execution_kind"] == "one-sweep_canonical_adaptation_qualification_probe"
    assert "not a Figure 7 performance point" in qualification["limitation"]
    assert qualification["work"]["bp_calls"] <= 1
    assert qualification["work"]["candidate_checks"] >= 1
    assert qualification["elapsed_seconds"] <= 30
    assert qualification["rounds"]
    assert qualification["rounds"][0]["sweeps"] == 1
    assert qualification["rounds"][0]["ranking_scan_count"] == 180
    verify = _run("verify", "--target", str(TARGET), "--manifest", str(MANIFEST), "--assessment", str(assessment))
    assert verify.returncode == 0, verify.stderr


def test_figure7_verifier_rejects_resigned_qualification_claim(tmp_path: Path):
    """A copied preflight and recomputed receipt digest cannot bless altered evidence."""
    assessment = tmp_path / "qualification.json"
    run = _run("run", "--target", str(TARGET), "--manifest", str(MANIFEST), "--assessment", str(assessment))
    assert run.returncode == 0, run.stderr
    changed = json.loads(assessment.read_text(encoding="utf-8"))
    changed["qualification"]["performance_verdict"] = "fabricated_performance_claim"
    changed["assessment_sha256"] = sha256(
        json.dumps({key: value for key, value in changed.items() if key != "assessment_sha256"}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    assessment.write_text(json.dumps(changed, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    verify = _run("verify", "--target", str(TARGET), "--manifest", str(MANIFEST), "--assessment", str(assessment))
    assert verify.returncode == 2
    assert "qualification deterministic evidence" in verify.stderr


def _verify_review(review: Path = REVIEW) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REVIEW_SCRIPT), "verify-candidate", "--review", str(review)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def _redigest_review(review: dict[str, object]) -> None:
    review["review_digest"] = sha256(
        json.dumps(
            {key: value for key, value in review.items() if key != "review_digest"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def test_figure7_review_covers_every_required_field_without_authorizing_execution():
    result = _verify_review()
    assert result.returncode == 0, result.stderr
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    assert review["review_decision"] == "pending_human_review"
    assert review["authorizes_execution"] is False
    entries = {entry["field_id"]: entry for entry in review["evidence_entries"]}
    assert set(entries) == REQUIRED_REVIEW_FIELDS
    for field_id, entry in entries.items():
        assert entry["source"]["sha256"]
        assert entry["locator"]["kind"] in {"primary_pdf", "authoritative_source"}
        assert entry["locator"]["page"] >= 1
        assert entry["excerpt_sha256"]
        assert entry["normalized_interpretation"]
        assert entry["compatibility_verdict"] in {"compatible", "unresolved", "incompatible"}
        assert entry["reviewer_state"] == "pending_human_review", field_id


def test_figure7_review_blocks_canonical_interpretation_inheritance_and_source_shots():
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    entries = {entry["field_id"]: entry for entry in review["evidence_entries"]}
    for field_id in {
        "message_lifecycle",
        "update_and_tie_order",
        "normalization",
        "curve_panel_identity",
        "digitization_uncertainty",
        "tolerance",
        "author_implementation_identity",
        "numerical_conventions",
        "source_route_fidelity",
    }:
        assert entries[field_id]["compatibility_verdict"] == "unresolved"
        assert entries[field_id]["discrepancy_or_blocker"]
    assert review["proposed_fidelity"] == "canonical_adaptation"
    assert review["source_execution"]["admitted_shots"] == 0
    assert review["source_execution"]["eligible"] is False
    for point in (0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10):
        bindings = entries[f"coordinate_p_{point:0.02f}"]["details"]["evidence_bindings"]
        assert set(bindings) == {
            "settings_field_id",
            "author_identity_field_id",
            "stopping_field_id",
            "denominator_field_id",
            "uncertainty_field_id",
            "tolerance_field_id",
        }


def test_figure7_review_verifier_rejects_drift_and_non_primary_evidence(tmp_path: Path):
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    review["a5"]["artifact_raw_sha256"] = "0" * 64
    review["authorizes_execution"] = True
    _redigest_review(review)
    tampered = tmp_path / "tampered-review.json"
    tampered.write_text(json.dumps(review), encoding="utf-8")
    result = _verify_review(tampered)
    assert result.returncode != 0
    assert "A5" in result.stderr or "authorizing" in result.stderr

    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    review["evidence_entries"] = review["evidence_entries"][1:]
    _redigest_review(review)
    missing = tmp_path / "missing-field.json"
    missing.write_text(json.dumps(review), encoding="utf-8")
    result = _verify_review(missing)
    assert result.returncode != 0
    assert "coverage" in result.stderr

    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    review["evidence_entries"][0]["locator"]["kind"] = "search_result"
    _redigest_review(review)
    non_primary = tmp_path / "non-primary.json"
    non_primary.write_text(json.dumps(review), encoding="utf-8")
    result = _verify_review(non_primary)
    assert result.returncode != 0
    assert "locator" in result.stderr
