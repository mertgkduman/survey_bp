"""Fail-closed controlled-evaluation receipt regressions for Phase 11."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/results/phase11-production-authorization.json"
GB46 = ROOT / "data/studies/phase11-gb46-joint-separate.json"
BB72 = ROOT / "data/studies/phase11-bb72-joint-separate.json"


def _module():
    from bp_registry.campaigns import controlled_evaluation

    return controlled_evaluation


def _receipt_path(tmp_path: Path, code_id: str) -> Path:
    return tmp_path / code_id.lower() / "evaluation-receipt.json"


def test_gb46_deny_tracer_writes_digest_bound_zero_dispatch_receipt(tmp_path: Path) -> None:
    module = _module()
    destination = _receipt_path(tmp_path, "GB46")

    receipt = module.execute_authorized_controlled_manifest(
        root=ROOT, package_path=PACKAGE, design_path=GB46, receipt_path=destination,
    )

    assert receipt["code_id"] == "GB46"
    assert receipt["campaign_id"] == "gb46-controlled"
    assert receipt["terminal_status"] == "denied"
    assert receipt["dispatch"]["state"] == "zero_dispatch"
    assert receipt["dispatch"]["scheduler_submissions"] == []
    assert receipt["attempted_pairs"] == []
    assert receipt["complete_pairs"] == []
    assert receipt["evidence_scope"]["assessment_ready_ledger_refs"] == []
    assert destination.is_file()
    assert json.loads(destination.read_text(encoding="utf-8"))["receipt_sha256"] == receipt["receipt_sha256"]
    module.verify_controlled_evaluation_receipt(
        root=ROOT, package_path=PACKAGE, design_path=GB46, receipt_path=destination,
    )


def test_gb46_stale_design_or_foreign_allow_fails_closed_without_dispatch(tmp_path: Path) -> None:
    module = _module()
    destination = _receipt_path(tmp_path, "GB46")
    altered = tmp_path / "altered-gb46.json"
    payload = json.loads(GB46.read_text(encoding="utf-8"))
    payload["study_id"] = "foreign-controlled-manifest"
    altered.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    receipt = module.execute_authorized_controlled_manifest(
        root=ROOT, package_path=PACKAGE, design_path=altered, receipt_path=destination,
    )

    assert receipt["terminal_status"] == "stale_identity"
    assert receipt["dispatch"]["state"] == "zero_dispatch"
    assert receipt["attempted_pairs"] == []


def test_bb72_cross_code_denial_retains_qualified_artifact_caveats_and_its_own_output(tmp_path: Path) -> None:
    module = _module()
    gb46_destination = _receipt_path(tmp_path, "GB46")
    bb72_destination = _receipt_path(tmp_path, "BB72")
    module.execute_authorized_controlled_manifest(
        root=ROOT, package_path=PACKAGE, design_path=GB46, receipt_path=gb46_destination,
    )

    receipt = module.execute_authorized_controlled_manifest(
        root=ROOT, package_path=PACKAGE, design_path=BB72, receipt_path=bb72_destination,
    )

    assert receipt["code_id"] == "BB72"
    assert receipt["terminal_status"] == "denied"
    assert receipt["dispatch"]["state"] == "zero_dispatch"
    assert receipt["approved_envelope"]["requested_pairs_per_point"] == 2454
    assert receipt["approved_envelope"]["manifest_sha256"] == "db6cbc41ef296bf87310ca0d17b05b7efa02636b31f94f3ead56962ef799baf5"
    assert receipt["code_qualification"]["distance_qualification"] == (
        "source_reported_distance_6_not_platform_verified"
    )
    assert receipt["code_qualification"]["logical_operator_qualification"] == (
        "project_derived_logicals_not_independent_distance_verification"
    )
    with pytest.raises(ValueError, match="code|receipt"):
        module.verify_controlled_evaluation_receipt(
            root=ROOT, package_path=PACKAGE, design_path=BB72, receipt_path=gb46_destination,
        )


def test_verify_all_requires_exact_terminal_coverage_and_exposes_no_calibration_evidence(tmp_path: Path) -> None:
    module = _module()
    gb46_destination = _receipt_path(tmp_path, "GB46")
    bb72_destination = _receipt_path(tmp_path, "BB72")
    module.execute_authorized_controlled_manifest(
        root=ROOT, package_path=PACKAGE, design_path=GB46, receipt_path=gb46_destination,
    )
    module.execute_authorized_controlled_manifest(
        root=ROOT, package_path=PACKAGE, design_path=BB72, receipt_path=bb72_destination,

    )

    verification_path = tmp_path / "verification.json"
    verification = module.write_controlled_evaluation_verification(
        root=ROOT, package_path=PACKAGE,
        receipt_paths={"GB46": gb46_destination, "BB72": bb72_destination},
        verification_path=verification_path,
    )

    assert verification["terminal_coverage"] == {"BB72": "denied", "GB46": "denied"}
    assert verification["assessment_ready"]["complete_pair_count_by_code"] == {"BB72": 0, "GB46": 0}
    assert verification["assessment_ready"]["ledger_refs"] == []
    assert verification["calibration_scope"] == "forecast_provenance_only"
    assert verification["receipt_sha256"] == sha256(
        module.canonical_receipt_bytes({k: v for k, v in verification.items() if k != "receipt_sha256"})
    ).hexdigest()
    assert json.loads(verification_path.read_text(encoding="utf-8"))["receipt_sha256"] == verification["receipt_sha256"]


def test_allow_receipt_without_an_approved_nonzero_bounded_dispatch_is_rejected(tmp_path: Path) -> None:
    module = _module()
    destination = _receipt_path(tmp_path, "GB46")
    receipt = module.execute_authorized_controlled_manifest(
        root=ROOT, package_path=PACKAGE, design_path=GB46, receipt_path=destination,
    )
    receipt["authorization"]["decision"] = "allow"
    receipt["dispatch"]["state"] = "zero_dispatch"
    receipt["receipt_sha256"] = module.receipt_digest(receipt)
    destination.write_bytes(module.canonical_receipt_bytes(receipt))

    with pytest.raises(ValueError, match="allow|dispatch"):
        module.verify_controlled_evaluation_receipt(
            root=ROOT, package_path=PACKAGE, design_path=GB46, receipt_path=destination,
        )
