"""Commands for validated Phase 1 pilot evidence and inspection."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
from time import perf_counter
from typing import Any

from . import evidence
from .ledger import reconcile
from .manifests import ManifestV1, manifest_digest, preflight
from .runner import preflight_pilot, run_one


def _dump(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _terminal_rows(ledger_path: Path, run_id: str) -> list[dict[str, Any]]:
    return sorted(
        (row for row in reconcile(ledger_path) if row["run_id"] == run_id),
        key=lambda row: row["shot_id"],
    )


def _result_from_final_rows(
    manifest_path: Path, output: Path, rows: list[dict[str, Any]], elapsed_seconds: float
) -> dict[str, Any]:
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    if not isinstance(manifest, ManifestV1):
        raise ValueError("pilot result requires a complete manifest")
    outcomes = Counter(row.get("outcome") or "outcome_unavailable" for row in rows)
    terminations = Counter(row["termination"] for row in rows)
    return {
        "schema_version": 1,
        "title": "gross-bb-144 pilot_adaptation — not_assessed",
        "run_id": manifest.run_id,
        "paper_experiment_id": "bhatnagar-impulse:Figure 6",
        "relation": "pilot_adaptation",
        "assessment_status": "not_assessed",
        "assessment_reason": manifest.expected_output.reason,
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_digest(manifest),
        "artifact": {
            "code_id": manifest.artifact.code_id,
            "raw_sha256": manifest.artifact.raw_sha256,
            "semantic_sha256": manifest.artifact.semantic_sha256,
        },
        "ledger_path": str(output / "events.jsonl"),
        "final_row_count": len(rows),
        "shot_ids": [row["shot_id"] for row in rows],
        "denominators": {
            "all_terminal_shots": len(rows),
            "exact": outcomes["exact"],
            "stabilizer_equivalent": outcomes["stabilizer_equivalent"],
            "logical_failure": outcomes["logical_failure"],
            "invalid_syndrome": outcomes["invalid_syndrome"],
            "outcome_unavailable": outcomes["outcome_unavailable"],
            "nonconverged": sum(row.get("native_converged") is False for row in rows),
            "interrupted": terminations["interrupted"],
            "postselected": sum(row.get("postselection") not in {None, "none", "unavailable"} for row in rows),
        },
        "terminations": dict(sorted(terminations.items())),
        "resource_context": {
            "omp_num_threads": manifest.environment.omp_num_threads,
            "host": socket.gethostname(),
            "elapsed_seconds_this_invocation": elapsed_seconds,
            "native_internals": "edge-update counts unavailable; each final row records the reason",
        },
        "statistical_claim": "not_assessed; this fixed 32-shot local smoke budget is not a curve comparison",
    }


def run_pilot(manifest_path: str | Path, output: str | Path) -> dict[str, Any]:
    """Run only missing declared shot IDs, then reconstruct the result from finals."""

    manifest_path, output = Path(manifest_path), Path(output)
    report = preflight_pilot(manifest_path)
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    assert isinstance(manifest, ManifestV1)
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "events.jsonl"
    started = perf_counter()
    existing = {row["shot_id"] for row in _terminal_rows(ledger_path, manifest.run_id)}
    missing = [shot_id for shot_id in range(manifest.budget.max_shots) if shot_id not in existing]
    for shot_id in missing:
        run_one(manifest_path, shot_id=shot_id, ledger_path=ledger_path)
    rows = _terminal_rows(ledger_path, manifest.run_id)
    expected = list(range(manifest.budget.max_shots))
    if [row["shot_id"] for row in rows] != expected:
        raise ValueError("pilot ledger does not contain exactly the pinned final shot IDs")
    result_path = output / "result.json"
    if missing or not result_path.exists():
        result = _result_from_final_rows(manifest_path, output, rows, perf_counter() - started)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**report, "output": str(output), "final_row_count": len(rows)}


def verify_run(output: str | Path) -> dict[str, Any]:
    """Reject incomplete, tampered, mislabeled, or non-reconstructed pilot output."""

    output = Path(output)
    result = _read_json(output / "result.json")
    if (
        "pilot_adaptation" not in str(result.get("title", ""))
        or "not_assessed" not in str(result.get("title", ""))
        or result.get("relation") != "pilot_adaptation"
        or result.get("assessment_status") != "not_assessed"
    ):
        raise ValueError("pilot result is missing pilot_adaptation/not_assessed labels")
    manifest_path = Path(result["manifest_path"])
    report = preflight_pilot(manifest_path)
    rows = _terminal_rows(output / "events.jsonl", report["run_id"])
    expected_result = _result_from_final_rows(manifest_path, output, rows, 0.0)
    comparable = {
        key: value for key, value in result.items() if key != "resource_context"
    }
    expected_comparable = {
        key: value for key, value in expected_result.items() if key != "resource_context"
    }
    for value in (result.get("resource_context"), expected_result.get("resource_context")):
        if not isinstance(value, dict):
            raise ValueError("result resource context is missing")
    actual_resource = dict(result["resource_context"])
    expected_resource = dict(expected_result["resource_context"])
    for key in ("elapsed_seconds_this_invocation", "host"):
        actual_resource.pop(key, None)
        expected_resource.pop(key, None)
    if actual_resource != expected_resource:
        raise ValueError("result resource context does not match the manifest requirement")
    if comparable != expected_comparable:
        raise ValueError("result JSON does not equal counts reconstructed from final ledger rows")
    if len(rows) != report["shot_budget"]:
        raise ValueError("pilot final-row count differs from the pinned shot budget")
    return {**report, "output": str(output), "final_row_count": len(rows), "verified_at": datetime.now(timezone.utc).isoformat()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    evidence_command = commands.add_parser("validate-evidence")
    evidence_command.add_argument("records", type=Path, nargs="?", default=Path("data/evidence/seed-records.json"))
    preflight_command = commands.add_parser("preflight")
    preflight_command.add_argument("manifest", type=Path)
    pilot_command = commands.add_parser("pilot")
    pilot_command.add_argument("manifest", type=Path)
    pilot_command.add_argument("--output", type=Path, required=True)
    reconcile_command = commands.add_parser("reconcile")
    reconcile_command.add_argument("ledger", type=Path)
    verify_command = commands.add_parser("verify-run")
    verify_command.add_argument("output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "validate-evidence":
        records = evidence.load_seed_records(args.records)
        _dump({"records": str(args.records), "paper_experiments": sorted(records["paper_experiments"]), "status": "valid"})
    elif args.command == "preflight":
        _dump(preflight_pilot(args.manifest))
    elif args.command == "pilot":
        _dump(run_pilot(args.manifest, args.output))
    elif args.command == "reconcile":
        _dump({"ledger": str(args.ledger), "final_rows": reconcile(args.ledger)})
    elif args.command == "verify-run":
        _dump(verify_run(args.output))


if __name__ == "__main__":
    main()
