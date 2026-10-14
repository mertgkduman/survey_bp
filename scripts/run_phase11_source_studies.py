#!/usr/bin/env python3
"""Preflight and preserve aSCED source-study evidence without dispatching compute."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

from bp_registry.campaigns.targets import QuaternarySourceTargetV1


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _load(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON input {path}: {error}") from error
    if not isinstance(loaded, dict):
        raise ValueError(f"JSON input {path} must be an object")
    return loaded


def _validated(target_path: Path, manifest_path: Path | None) -> tuple[QuaternarySourceTargetV1, dict[str, Any] | None, str]:
    target_bytes = target_path.read_bytes()
    target = QuaternarySourceTargetV1.model_validate_json(target_bytes)
    if manifest_path is None:
        return target, None, sha256(target_bytes).hexdigest()
    manifest = _load(manifest_path)
    if manifest.get("schema") != "phase11-asced-source-manifest-v1":
        raise ValueError("source manifest schema is not admitted")
    if manifest.get("target_document_sha256") != sha256(target_bytes).hexdigest():
        raise ValueError("target document digest differs from the frozen source manifest")
    if manifest.get("target_receipt_sha256") != target.digest():
        raise ValueError("target receipt digest differs from the frozen source manifest")
    if manifest.get("source_only") is not True or manifest.get("controlled_comparison") is not False:
        raise ValueError("source manifest cannot be reused for a controlled comparison")
    if manifest.get("run_fidelity") != "canonical_adaptation":
        raise ValueError("source target cannot promote canonical adaptation fidelity")
    return target, manifest, sha256(target_bytes).hexdigest()


def _blocked_assessment(target: QuaternarySourceTargetV1, target_document_sha256: str) -> dict[str, Any]:
    members = []
    for member in target.members:
        if member.eligibility != "blocked_metadata":
            raise ValueError("non-blocked execution is not authorized by this source-study entry point")
        members.append({
            "member_id": member.member_id,
            "target_slot": member.target_slot,
            "status": "blocked_metadata",
            "admitted_shots": 0,
            "blockers": list(member.blockers),
            "discrepancy": "not_assessed_due_to_blocked_source_metadata",
        })
    payload = {
        "schema": "phase11-asced-source-assessment-v1",
        "status": "blocked_metadata",
        "target_receipt_sha256": target.digest(),
        "target_document_sha256": target_document_sha256,
        "run_fidelity": "canonical_adaptation",
        "source_fidelity": "not_promoted",
        "admitted_shots": 0,
        "members": members,
    }
    payload["assessment_sha256"] = sha256(_canonical_bytes(payload)).hexdigest()
    return payload


def preflight(target_path: Path, manifest_path: Path | None, assessment_path: Path) -> dict[str, Any]:
    target, _manifest, document_digest = _validated(target_path, manifest_path)
    assessment = _blocked_assessment(target, document_digest)
    assessment_path.parent.mkdir(parents=True, exist_ok=True)
    assessment_path.write_bytes(_canonical_bytes(assessment) + b"\n")
    return assessment


def verify(target_path: Path, manifest_path: Path | None, assessment_path: Path) -> dict[str, Any]:
    target, _manifest, document_digest = _validated(target_path, manifest_path)
    assessment = _load(assessment_path)
    expected = _blocked_assessment(target, document_digest)
    if assessment != expected:
        raise ValueError("assessment digest or blocked source evidence drifted")
    return assessment


def run(target_path: Path, manifest_path: Path | None, assessment_path: Path) -> dict[str, Any]:
    target, _manifest, document_digest = _validated(target_path, manifest_path)
    assessment = _blocked_assessment(target, document_digest)
    if assessment["status"] == "blocked_metadata":
        raise ValueError("source assessment is blocked_metadata; sampling is not admitted")
    raise ValueError("unreachable source-study execution state")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "assess", "verify"))
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--assessment", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command in {"preflight", "assess"}:
            result = preflight(args.target, args.manifest, args.assessment)
        elif args.command == "verify":
            result = verify(args.target, args.manifest, args.assessment)
        else:
            result = run(args.target, args.manifest, args.assessment)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error
    print(json.dumps({"status": result["status"], "admitted_shots": result["admitted_shots"]}, sort_keys=True))


if __name__ == "__main__":
    main()
