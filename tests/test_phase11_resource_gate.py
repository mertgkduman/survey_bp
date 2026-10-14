"""Default-deny authorization package regressions for Phase 11."""

from __future__ import annotations

import json
import importlib
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _api():
    module = importlib.import_module("bp_registry.campaigns.profiling_gate")
    assert hasattr(module, "build_phase11_dispatch_package"), "Phase 11 must expose a dispatch-package builder"
    assert hasattr(module, "validate_phase11_dispatch_package"), "Phase 11 must validate its default-deny package"
    return module


def test_phase11_proposal_is_decision_ready_but_default_deny() -> None:
    package = _api().build_phase11_dispatch_package(ROOT)

    assert package["receipt"]["decision"] == "deny"
    assert package["receipt"]["dispatch_token"] is None
    assert {item["code_id"] for item in package["calibrations"]} == {"GB46", "BB72"}
    assert package["precision_feasibility"]["status"] == "powered"
    assert "missing_site_ceiling:max_wall_time_ns" in package["receipt"]["reasons"]
    assert "missing_accounting_partition_evidence" in package["receipt"]["reasons"]
    assert "source_route_ineligible" in package["receipt"]["reasons"]


@pytest.mark.parametrize("mutation", [
    lambda payload: payload["site_capability"].update({"installed_slurm_clients": True}),
    lambda payload: payload["calibrations"][0].update({"manifest_sha256": "0" * 64}),
    lambda payload: payload["receipt"].update({"decision": "allow", "dispatch_token": "forged"}),
])
def test_phase11_resource_gate_rejects_client_only_stale_or_allowing_packages(mutation) -> None:
    package = _api().build_phase11_dispatch_package(ROOT)
    mutation(package)

    with pytest.raises(ValueError, match="(site|calibration|deny|dispatch)"):
        _api().validate_phase11_dispatch_package(ROOT, package)


def test_checked_in_phase11_authorization_package_is_valid_and_deny_only() -> None:
    package = json.loads((ROOT / "data/results/phase11-production-authorization.json").read_text(encoding="utf-8"))
    _api().validate_phase11_dispatch_package(ROOT, package)
    assert package["receipt"]["decision"] == "deny"


def test_public_cli_verifies_only_the_exact_default_deny_authorization_package(tmp_path: Path) -> None:
    package = ROOT / "data/results/phase11-production-authorization.json"
    command = [sys.executable, "scripts/run_phase11_controlled.py", "verify-authorization", "--package", str(package)]

    valid = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)

    assert valid.returncode == 0, valid.stdout
    receipt = json.loads(valid.stdout)
    assert receipt["status"] == "ok"
    assert receipt["receipt"]["decision"] == "deny"
    assert receipt["receipt"]["dispatch_token"] is None
    assert all(not campaign["source_eligible"] for campaign in receipt["requested_campaigns"])

    tampered = json.loads(package.read_text(encoding="utf-8"))
    tampered["requested_campaigns"][0]["source_eligible"] = True
    altered = tmp_path / "allowing.json"
    altered.write_text(json.dumps(tampered), encoding="utf-8")
    rejected = subprocess.run(
        [*command[:-1], str(altered)], cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert rejected.returncode == 2
    assert json.loads(rejected.stdout)["status"] == "error"


def test_record_authorization_preserve_deny_seals_the_verified_package(tmp_path: Path) -> None:
    """A reviewed denial is durable evidence, never an implicit dispatch path."""
    package_path = tmp_path / "authorization.json"
    package_path.write_bytes((ROOT / "data/results/phase11-production-authorization.json").read_bytes())
    package = json.loads(package_path.read_text(encoding="utf-8"))

    result = subprocess.run(
        [
            sys.executable, "scripts/run_phase11_controlled.py", "record-authorization",
            "--package", str(package_path), "--decision", "preserve_deny",
            "--reviewer", "chat_user", "--reason",
            "Missing site ceilings, account/partition, quota/cost, runtime profiles, and source-route eligibility.",
            "--reviewed-package-sha256", package["package_sha256"],
        ],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )

    assert result.returncode == 0, result.stdout
    stored = json.loads(package_path.read_text(encoding="utf-8"))
    receipt = stored["receipt"]
    assert receipt["schema"] == "phase11_authorization_receipt_v1"
    assert receipt["decision"] == "deny"
    assert receipt["reviewer"] == "chat_user"
    assert receipt["reviewed_package_sha256"] == package["package_sha256"]
    assert receipt["dispatch_token"] is None
    assert set(receipt["denied_campaign_ids"]) == {
        "gb46-controlled", "bb72-controlled", "gb46-source", "bb72-source",
    }
    _api().validate_phase11_dispatch_package(ROOT, stored)


def test_record_authorization_ineligible_allow_request_is_sealed_as_deny(tmp_path: Path) -> None:
    """A resume request cannot turn a package with failed gates into an allow."""
    package_path = tmp_path / "authorization.json"
    package_path.write_bytes((ROOT / "data/results/phase11-production-authorization.json").read_bytes())
    package = json.loads(package_path.read_text(encoding="utf-8"))

    result = subprocess.run(
        [
            sys.executable, "scripts/run_phase11_controlled.py", "record-authorization",
            "--package", str(package_path), "--decision", "authorize_exact_manifests",
            "--reviewer", "chat_user", "--reason", "Attempt an exact manifest review.",
            "--reviewed-package-sha256", package["package_sha256"],
            "--approved-manifest-sha256", package["calibrations"][0]["manifest_sha256"],
        ],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )

    assert result.returncode == 0, result.stdout
    receipt = json.loads(package_path.read_text(encoding="utf-8"))["receipt"]
    assert receipt["decision"] == "deny"
    assert receipt["approved_manifest_sha256s"] == []
    assert "authorization_request_ineligible_manifest" in receipt["reasons"]
    assert receipt["dispatch_token"] is None


def test_record_authorization_stale_digest_rewrites_a_sealed_deny(tmp_path: Path) -> None:
    """A stale review cannot preserve or create any prior authorization."""
    package_path = tmp_path / "authorization.json"
    package_path.write_bytes((ROOT / "data/results/phase11-production-authorization.json").read_bytes())

    result = subprocess.run(
        [
            sys.executable, "scripts/run_phase11_controlled.py", "record-authorization",
            "--package", str(package_path), "--decision", "preserve_deny",
            "--reviewer", "chat_user", "--reason", "Record a stale review as denied.",
            "--reviewed-package-sha256", "0" * 64,
        ],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )

    assert result.returncode == 0, result.stdout
    receipt = json.loads(package_path.read_text(encoding="utf-8"))["receipt"]
    assert receipt["decision"] == "deny"
    assert "authorization_request_stale_package_digest" in receipt["reasons"]
    assert receipt["dispatch_token"] is None


def test_record_authorization_interrupted_write_leaves_existing_package_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deny receipt publication uses replacement, so a failed replacement is not durable."""
    package_path = tmp_path / "authorization.json"
    original = (ROOT / "data/results/phase11-production-authorization.json").read_bytes()
    package_path.write_bytes(original)
    module = _api()

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated replacement interruption")

    monkeypatch.setattr(module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated replacement interruption"):
        module.materialize_phase11_authorization_receipt(
            ROOT, package_path, decision="preserve_deny", reviewer="chat_user",
            reason="Exercise atomic failure handling.",
            reviewed_package_sha256=json.loads(original)["package_sha256"],
            confirmed_ceilings_sha256=None, account=None, partition=None,
            approved_manifest_sha256s=(),
        )

    assert package_path.read_bytes() == original
    assert not list(tmp_path.glob(".phase11-authorization-*"))


def test_exact_digest_allow_subset_requires_every_gate_and_keeps_other_campaigns_denied() -> None:
    """The receipt validator accepts only a reviewed subset of an eligible package."""
    module = _api()
    package = module.build_phase11_dispatch_package(ROOT)
    package["requested_campaigns"] = [
        {**campaign, "source_eligible": True} for campaign in package["requested_campaigns"]
    ]
    package["site_capability"] = {
        "installed_slurm_clients": False,
        "max_cpu_time_ns": 10, "max_wall_time_ns": 10, "max_storage_bytes": 10,
        "max_shard_bytes": 10, "max_replay_time_ns": 10, "max_peak_memory_bytes": 10,
        "max_scheduler_cost_ns": 10,
    }
    package["accounting_partition"] = {"status": "available", "account": "research", "partition": "cpu"}
    package["quota_cost"] = {"status": "available", "allocation": 10, "cost_estimate": 10}
    package["forecast"] = {
        "status": "available", "predicted_memory_bytes": 1,
        "predicted_wall_time_ns": 1, "predicted_typed_work": 1,
    }
    package["receipt"] = {"decision": "deny", "dispatch_token": None, "reasons": []}
    chosen = package["calibrations"][0]["manifest_sha256"]
    denied = [
        campaign["campaign_id"] for campaign in package["requested_campaigns"]
        if campaign["code_id"] != package["calibrations"][0]["code_id"]
    ]
    receipt = {
        "schema": "phase11_authorization_receipt_v1", "decision": "allow", "reviewer": "chat_user",
        "reason": "Exact reviewed subset.", "recorded_at": "2026-10-14T22:44:29Z",
        "reviewed_package_sha256": package["package_sha256"],
        "confirmed_ceilings_sha256": module._digest(package["site_capability"]),
        "account": "research", "partition": "cpu", "approved_manifest_sha256s": [chosen],
        "denied_campaign_ids": denied, "reasons": ["human_reviewed_exact_manifest_allow"],
        "dispatch_token": None,
    }
    receipt["receipt_sha256"] = module._digest({key: value for key, value in receipt.items() if key != "receipt_sha256"})

    module._validate_phase11_authorization_receipt(package, receipt)

    receipt["approved_manifest_sha256s"].append("0" * 64)
    receipt["receipt_sha256"] = module._digest({key: value for key, value in receipt.items() if key != "receipt_sha256"})
    with pytest.raises(ValueError, match="unknown manifest"):
        module._validate_phase11_authorization_receipt(package, receipt)
