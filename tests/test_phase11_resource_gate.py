"""Default-deny authorization package regressions for Phase 11."""

from __future__ import annotations

import json
import importlib
from pathlib import Path

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
