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
