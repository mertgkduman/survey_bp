"""Commands for validated Phase 1 pilot evidence and inspection."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import socket
from time import perf_counter
from typing import Any

import numpy as np

from . import evaluator, evidence, sampling
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


def _ledger_events(ledger_path: Path) -> list[dict[str, Any]]:
    if not ledger_path.exists():
        return []
    return [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line]


def _validate_pilot_ledger(manifest_path: Path, ledger_path: Path, rows: list[dict[str, Any]]) -> None:
    """Validate immutable manifest identity and begin-to-terminal lineage."""
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    if not isinstance(manifest, ManifestV1):
        raise ValueError("pilot ledger requires a complete manifest")
    digest = manifest_digest(manifest)
    expected_common = {
        "manifest_sha256": digest,
        "source_uri": manifest.implementation.repository_uri,
        "source_revision": manifest.implementation.revision,
        "source_anchor": manifest.implementation.source_path,
        "paper_uri": manifest.paper.uri,
        "paper_revision": manifest.paper.revision,
        "paper_anchor": manifest.paper.experiment_anchor,
        "implementation_source_artifact_sha256": manifest.implementation.source_artifact_sha256,
        "code_id": manifest.artifact.code_id,
        "experiment_relation": manifest.paper.relation,
        "expected_output_status": manifest.expected_output.status,
        "decoder_config": {
            "bp_method": manifest.decoder.bp_method,
            "schedule": manifest.decoder.schedule,
            "input_vector_type": manifest.decoder.input_vector_type,
            "error_rate": manifest.noise.x_error_rates[0],
            "max_iter": manifest.budget.max_iter,
        },
        "decoder_version": manifest.decoder.version,
        "artifact_raw_sha256": manifest.artifact.raw_sha256,
        "artifact_semantic_sha256": manifest.artifact.semantic_sha256,
        "artifact_path": str((Path(manifest.artifact.root) / manifest.artifact.path).resolve()),
    }
    events = _ledger_events(ledger_path)
    begins = {
        (event.get("run_id"), event.get("shot_id")): event
        for event in events if event.get("kind") == "begin"
    }
    terminals = {
        (event.get("run_id"), event.get("shot_id")): event
        for event in events if event.get("kind") == "terminal"
    }
    for row in rows:
        key = (row.get("run_id"), row.get("shot_id"))
        begin, terminal = begins.get(key), terminals.get(key)
        if begin is None or terminal is None or terminal != row:
            raise ValueError("pilot terminal row lacks an unmodified begin-to-terminal lineage")
        shot_id = row["shot_id"]
        if type(shot_id) is not int or not 0 <= shot_id < manifest.budget.max_shots:
            raise ValueError("pilot ledger shot ID is outside the manifest budget")
        identity = sha256(f"bp-registry-sample-v1\0{digest}\0{shot_id}".encode()).hexdigest()
        for event in (begin, terminal):
            if any(event.get(key) != value for key, value in expected_common.items()):
                raise ValueError("pilot ledger provenance differs from the resolved manifest")
            if event.get("sample_seed_identity") != identity:
                raise ValueError("pilot ledger sample identity is not deterministic for its manifest and shot")
        if terminal.get("termination") != "completed":
            raise ValueError("pilot ledger contains a non-completed terminal row")
        sample = sampling.sample_shot(
            resolved.code, manifest_identity=digest, seed=manifest.seed_policy.root_seed,
            shot_id=shot_id, x_error_rate=manifest.noise.x_error_rates[0],
        )
        if (terminal.get("sample_identity") != sample.sample_identity
                or terminal.get("syndrome") != sample.observation.syndrome.tolist()
                or terminal.get("hidden_x") != sample.hidden.x.tolist()
                or terminal.get("hidden_z") != sample.hidden.z.tolist()):
            raise ValueError("pilot ledger sample fields do not reproduce from the manifest")
        candidate = np.asarray(terminal.get("candidate"), dtype=np.uint8)
        if terminal.get("selected_output") != terminal.get("candidate"):
            raise ValueError("pilot ledger selected output is not linked to its native candidate")
        evaluation = evaluator.evaluate_candidate(
            resolved.code, true_x=sample.hidden.x, true_z=sample.hidden.z, candidate_x=candidate,
        )
        if (terminal.get("outcome") != evaluation.outcome
                or terminal.get("logical_action_agrees") != evaluation.logical_action_agrees):
            raise ValueError("pilot ledger outcome is not linked to its independently evaluated candidate")


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
    _validate_pilot_ledger(manifest_path, ledger_path, rows)
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
    _validate_pilot_ledger(manifest_path, output / "events.jsonl", rows)
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
