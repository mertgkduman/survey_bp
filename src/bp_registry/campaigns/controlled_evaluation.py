"""Fail-closed consumer for Phase 11 controlled-evaluation authorization.

The checked-in Phase 11 authorization is an explicit denial.  This module
still consumes it through the same identity and receipt boundary that a future
reviewed allow would use: any missing or changed prerequisite seals a durable,
zero-dispatch receipt.  Calibration output remains resource-forecast
provenance and is never admitted as an evaluation pair ledger.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .controlled_execution import _publish_exact, preflight_phase11_controlled_design
from .contracts import canonical_json_bytes
from .profiling_gate import validate_phase11_dispatch_package


_SCHEMA = "phase11_controlled_evaluation_receipt_v1"
_VERIFICATION_SCHEMA = "phase11_controlled_evaluation_verification_v1"
_CONTROLLED_CAMPAIGNS = {"GB46": "gb46-controlled", "BB72": "bb72-controlled"}


def canonical_receipt_bytes(value: object) -> bytes:
    """Serialize receipts using the project-wide canonical JSON grammar."""
    return canonical_json_bytes(value)


def receipt_digest(receipt: Mapping[str, object]) -> str:
    """Return a content digest without trusting a supplied receipt digest."""
    return sha256(canonical_receipt_bytes({
        key: value for key, value in receipt.items() if key != "receipt_sha256"
    })).hexdigest()


def _read_regular_json(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    try:
        value = json.loads(path.read_bytes())
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} must be valid JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _inside(root: Path, path: Path, *, label: str) -> Path:
    resolved = path.resolve(strict=True)
    if root not in (resolved, *resolved.parents) or resolved.is_symlink() or not resolved.is_file():
        raise ValueError(f"{label} must be a regular file beneath the project root")
    return resolved


def _package_context(*, root: Path, package_path: Path) -> dict[str, Any]:
    package = _read_regular_json(package_path, label="authorization package")
    validate_phase11_dispatch_package(root, package)
    receipt = package.get("receipt")
    if not isinstance(receipt, dict) or receipt.get("schema") != "phase11_authorization_receipt_v1":
        raise ValueError("authorization package lacks a sealed Phase 11 receipt")
    return package


def _design_context(*, root: Path, package: Mapping[str, object], design_path: Path) -> dict[str, Any]:
    resolved = _inside(root, design_path, label="controlled design")
    preflight = preflight_phase11_controlled_design(root=root, design_path=resolved)
    code_id = preflight.get("code_id")
    if code_id not in _CONTROLLED_CAMPAIGNS:
        raise ValueError("controlled design has an unsupported code identity")
    raw = resolved.read_bytes()
    manifest_sha256 = sha256(raw).hexdigest()
    calibrations = package.get("calibrations")
    requested = package.get("requested_campaigns")
    if not isinstance(calibrations, list) or not isinstance(requested, list):
        raise ValueError("authorization package has incomplete controlled campaign evidence")
    calibration = next((row for row in calibrations if isinstance(row, dict) and row.get("code_id") == code_id), None)
    campaign = next((row for row in requested if isinstance(row, dict) and row.get("campaign_id") == _CONTROLLED_CAMPAIGNS[code_id]), None)
    if calibration is None or campaign is None:
        raise ValueError("authorization package has no exact controlled campaign entry")
    if calibration.get("manifest_sha256") != manifest_sha256:
        raise ValueError("controlled manifest digest differs from the authorized package")
    if calibration.get("code_artifact_sha256") != preflight.get("code_artifact_sha256"):
        raise ValueError("controlled artifact digest differs from the authorized package")
    qualification = {
        "run_fidelity": "canonical_adaptation",
        "code_artifact_sha256": preflight["code_artifact_sha256"],
        "code_provenance_sha256": preflight.get("code_provenance_sha256"),
    }
    for field in ("distance_qualification", "logical_operator_qualification"):
        if field in preflight:
            qualification[field] = preflight[field]
    return {
        "code_id": code_id,
        "campaign_id": _CONTROLLED_CAMPAIGNS[code_id],
        "design_path": str(resolved.relative_to(root)),
        "manifest_sha256": manifest_sha256,
        "preflight": preflight,
        "campaign": campaign,
        "code_qualification": qualification,
    }


def _zero_dispatch_receipt(
    *, package: Mapping[str, object], context: Mapping[str, object], status: str, reason: str,
) -> dict[str, object]:
    sealed = package["receipt"]
    assert isinstance(sealed, Mapping)
    receipt: dict[str, object] = {
        "schema": _SCHEMA,
        "code_id": context["code_id"],
        "campaign_id": context["campaign_id"],
        "manifest": {
            "path": context["design_path"],
            "sha256": context["manifest_sha256"],
            "fixed_marginal_design_sha256": context["preflight"]["fixed_marginal_design_sha256"],
        },
        "code_qualification": context["code_qualification"],
        "authorization": {
            "package_sha256": package["package_sha256"],
            "sealed_receipt_sha256": sealed["receipt_sha256"],
            "decision": sealed["decision"],
            "approved_manifest_sha256s": sealed["approved_manifest_sha256s"],
            "account": sealed["account"],
            "partition": sealed["partition"],
        },
        "approved_envelope": {
            "manifest_sha256": context["manifest_sha256"],
            "requested_pairs_per_point": context["campaign"]["pairs_per_point"],
            "pairs_per_point": None,
            "max_workers": None,
            "max_wall_time_ns": None,
            "max_peak_memory_bytes": None,
            "max_typed_work": None,
            "status": "not_approved",
        },
        "terminal_status": status,
        "terminal_reason": reason,
        "dispatch": {"state": "zero_dispatch", "scheduler_submissions": [], "scheduler_transitions": []},
        "attempted_pairs": [],
        "complete_pairs": [],
        "typed_work": {},
        "interruptions": [],
        "calibration_provenance": {
            "status": "forecast_provenance_only",
            "manifest_sha256": context["manifest_sha256"],
            "forbidden_as_evaluation_evidence": True,
        },
        "evidence_scope": {
            "assessment_ready_ledger_refs": [],
            "complete_pair_count": 0,
            "calibration_reuse_prohibited": True,
        },
    }
    receipt["receipt_sha256"] = receipt_digest(receipt)
    return receipt


def _stale_zero_dispatch_receipt(*, package_path: Path, design_path: Path, error: ValueError) -> dict[str, object]:
    """Make identity failures terminal without pretending their evidence is valid."""
    guessed = "BB72" if "bb72" in design_path.name.lower() else "GB46"
    receipt: dict[str, object] = {
        "schema": _SCHEMA,
        "code_id": guessed,
        "campaign_id": _CONTROLLED_CAMPAIGNS[guessed],
        "manifest": {"path": str(design_path), "sha256": None, "fixed_marginal_design_sha256": None},
        "code_qualification": {"status": "unverified"},
        "authorization": {"package_path": str(package_path), "decision": "unverified"},
        "approved_envelope": {"status": "not_approved"},
        "terminal_status": "stale_identity",
        "terminal_reason": str(error),
        "dispatch": {"state": "zero_dispatch", "scheduler_submissions": [], "scheduler_transitions": []},
        "attempted_pairs": [], "complete_pairs": [], "typed_work": {}, "interruptions": [],
        "calibration_provenance": {"status": "not_admitted", "forbidden_as_evaluation_evidence": True},
        "evidence_scope": {"assessment_ready_ledger_refs": [], "complete_pair_count": 0,
                           "calibration_reuse_prohibited": True},
    }
    receipt["receipt_sha256"] = receipt_digest(receipt)
    return receipt


def preflight_controlled_manifest(*, root: Path, package_path: Path, design_path: Path) -> dict[str, object]:
    """Validate the exact package and controlled manifest without dispatching work."""
    root = root.resolve(strict=True)
    package = _package_context(root=root, package_path=package_path)
    context = _design_context(root=root, package=package, design_path=design_path)
    sealed = package["receipt"]
    assert isinstance(sealed, Mapping)
    return {
        "schema": "phase11_controlled_evaluation_preflight_v1",
        "code_id": context["code_id"],
        "campaign_id": context["campaign_id"],
        "manifest_sha256": context["manifest_sha256"],
        "authorization_decision": sealed["decision"],
        "dispatch_permitted": False,
        "reason": "sealed authorization remains deny" if sealed["decision"] == "deny" else "allow requires a qualified dispatcher",
    }


def execute_authorized_controlled_manifest(
    *, root: Path, package_path: Path, design_path: Path, receipt_path: Path,
) -> dict[str, object]:
    """Consume exactly one controlled entry, writing an immutable terminal receipt.

    No dispatch implementation is reachable from a package that currently fails
    any authorization gate.  A hypothetical sealed allow also fails closed here
    until a separately qualified dispatcher can preserve all pair and scheduler
    evidence required by this receipt schema.
    """
    root = root.resolve(strict=True)
    try:
        package = _package_context(root=root, package_path=package_path)
        context = _design_context(root=root, package=package, design_path=design_path)
        sealed = package["receipt"]
        assert isinstance(sealed, Mapping)
        if sealed["decision"] == "deny":
            reason = "sealed_authorization_deny:" + ",".join(sorted(str(value) for value in sealed["reasons"]))
            receipt = _zero_dispatch_receipt(package=package, context=context, status="denied", reason=reason)
        else:
            receipt = _zero_dispatch_receipt(
                package=package, context=context, status="ineligible",
                reason="allow_requires_qualified_dispatcher_with_complete_pair_and_scheduler_evidence",
            )
    except ValueError as error:
        receipt = _stale_zero_dispatch_receipt(package_path=package_path, design_path=design_path, error=error)
    _publish_exact(receipt_path, canonical_receipt_bytes(receipt))
    return receipt


def verify_controlled_evaluation_receipt(
    *, root: Path, package_path: Path, design_path: Path, receipt_path: Path,
) -> dict[str, object]:
    """Verify one terminal receipt against the current exact package and design."""
    root = root.resolve(strict=True)
    package = _package_context(root=root, package_path=package_path)
    context = _design_context(root=root, package=package, design_path=design_path)
    receipt = _read_regular_json(receipt_path, label="controlled evaluation receipt")
    if receipt.get("schema") != _SCHEMA or receipt.get("receipt_sha256") != receipt_digest(receipt):
        raise ValueError("controlled evaluation receipt digest differs from its evidence")
    if receipt.get("code_id") != context["code_id"] or receipt.get("campaign_id") != context["campaign_id"]:
        raise ValueError("controlled evaluation receipt code or campaign differs from its design")
    if receipt.get("manifest", {}).get("sha256") != context["manifest_sha256"]:
        raise ValueError("controlled evaluation receipt manifest differs from the authorized design")
    if receipt.get("code_qualification") != context["code_qualification"]:
        raise ValueError("controlled evaluation receipt loses code qualification evidence")
    sealed = package["receipt"]
    assert isinstance(sealed, Mapping)
    authorization = receipt.get("authorization")
    dispatch = receipt.get("dispatch")
    if not isinstance(authorization, Mapping) or not isinstance(dispatch, Mapping):
        raise ValueError("controlled evaluation receipt lacks authorization or dispatch evidence")
    if authorization.get("decision") != sealed["decision"]:
        raise ValueError("controlled evaluation receipt decision differs from sealed authorization")
    if receipt.get("attempted_pairs") != [] or receipt.get("complete_pairs") != []:
        raise ValueError("zero-dispatch closure cannot contain attempted or complete pairs")
    if receipt.get("evidence_scope", {}).get("assessment_ready_ledger_refs") != []:
        raise ValueError("calibration or closure evidence cannot become assessment ready")
    if receipt.get("calibration_provenance", {}).get("forbidden_as_evaluation_evidence") is not True:
        raise ValueError("controlled evaluation receipt must prohibit calibration evidence reuse")
    if sealed["decision"] == "deny":
        if receipt.get("terminal_status") != "denied" or dispatch.get("state") != "zero_dispatch":
            raise ValueError("denied authorization must produce a zero-dispatch denial closure")
    elif dispatch.get("state") == "zero_dispatch":
        raise ValueError("allow authorization cannot be represented as an unqualified zero-dispatch receipt")
    else:
        raise ValueError("allow receipt requires a separately qualified controlled dispatcher")
    return receipt


def verify_all_controlled_evaluations(
    *, root: Path, package_path: Path, receipt_paths: Mapping[str, Path],
) -> dict[str, object]:
    """Verify exact two-code terminal coverage and assessment-ready boundaries."""
    root = root.resolve(strict=True)
    package = _package_context(root=root, package_path=package_path)
    if set(receipt_paths) != set(_CONTROLLED_CAMPAIGNS):
        raise ValueError("two-code verification requires exactly GB46 and BB72 receipt paths")
    rows = {row["code_id"]: row for row in package["calibrations"] if isinstance(row, Mapping)}
    receipts: dict[str, dict[str, object]] = {}
    for code_id in sorted(_CONTROLLED_CAMPAIGNS):
        relative = rows.get(code_id, {}).get("manifest_path")
        if not isinstance(relative, str):
            raise ValueError("authorization package has no manifest for a controlled code")
        receipt = verify_controlled_evaluation_receipt(
            root=root, package_path=package_path, design_path=root / relative, receipt_path=receipt_paths[code_id],
        )
        receipts[code_id] = receipt
    verification: dict[str, object] = {
        "schema": _VERIFICATION_SCHEMA,
        "authorization_package_sha256": package["package_sha256"],
        "authorization_receipt_sha256": package["receipt"]["receipt_sha256"],
        "terminal_coverage": {code: receipts[code]["terminal_status"] for code in sorted(receipts)},
        "receipt_sha256_by_code": {code: receipts[code]["receipt_sha256"] for code in sorted(receipts)},
        "assessment_ready": {
            "complete_pair_count_by_code": {code: 0 for code in sorted(receipts)},
            "ledger_refs": [],
            "complete_pair_only": True,
        },
        "calibration_scope": "forecast_provenance_only",
    }
    verification["receipt_sha256"] = receipt_digest(verification)
    return verification


def write_controlled_evaluation_verification(
    *, root: Path, package_path: Path, receipt_paths: Mapping[str, Path], verification_path: Path,
) -> dict[str, object]:
    """Seal the independent two-code verification receipt with immutable bytes."""
    verification = verify_all_controlled_evaluations(
        root=root, package_path=package_path, receipt_paths=receipt_paths,
    )
    _publish_exact(verification_path, canonical_receipt_bytes(verification))
    return verification
