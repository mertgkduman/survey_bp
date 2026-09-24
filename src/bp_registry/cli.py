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
from .ledger import read_canonical_events, reconcile, summarize
from .manifests import CanonicalExperimentV2, CanonicalExperimentV3, ManifestV1, manifest_digest, preflight, qualify_cluster_artifact
from .canonical.verification import validate_canonical_shot
from .runner import (
    canonical_public_shot_context, canonical_terminal_rows, preflight_canonical,
    preflight_pilot, run_canonical_one, run_one,
)


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


def _reconcile_report(ledger_path: Path) -> dict[str, Any]:
    """Report final rows for either durable ledger version without weakening validation."""
    events = _ledger_events(ledger_path)
    if events and events[0].get("ledger_version") == 2:
        canonical_events = read_canonical_events(ledger_path)
        return {
            "ledger": str(ledger_path),
            "final_rows": sum(event["kind"] == "termination" for event in canonical_events),
            "ledger_version": 2,
            "mode": "canonical_query",
        }
    return {"ledger": str(ledger_path), "final_rows": reconcile(ledger_path), "ledger_version": 1}


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
        "artifact_path": str(Path(manifest.artifact.root) / manifest.artifact.path),
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
        termination = terminal.get("termination")
        if termination in {"interrupted", "exception"}:
            if (terminal.get("outcome") is not None
                    or not terminal.get("outcome_unavailable_reason")
                    or terminal.get("selected_output") is not None
                    or terminal.get("native_converged") is not None
                    or terminal.get("native_iterations") is not None
                    or terminal.get("native_edge_updates") is not None
                    or not terminal.get("native_internals_unavailable_reason")
                    or any(terminal.get(field) is not None for field in (
                        "candidate", "syndrome", "hidden_x", "hidden_z",
                        "sample_identity", "logical_action_agrees", "observation_check_type",
                        "native_edge_updates_missing_reason",
                    ))
                    or terminal.get("postselection") != "unavailable"):
                raise ValueError("pilot unsuccessful terminal lacks explicit unavailable fields")
            if termination == "interrupted":
                if (terminal.get("termination_inference") != "reconciled_after_owner_release"
                        or terminal.get("observed_termination") is not False
                        or terminal.get("selection_status") != "unavailable"
                        or any(terminal.get(field) is not None for field in (
                            "exception_stage", "exception_type", "exception_message",
                        ))):
                    raise ValueError("pilot interruption lacks reconciliation provenance")
            elif (terminal.get("exception_stage") not in {"sampling", "decoding", "evaluation"}
                    or not terminal.get("exception_type")
                    or terminal.get("observed_termination") is not True
                    or terminal.get("selection_status") != "unavailable_due_to_exception"
                    or terminal.get("termination_inference") is not None):
                raise ValueError("pilot exception lacks stage and type provenance")
            continue
        if termination != "completed":
            raise ValueError("pilot ledger has an unknown termination status")
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
    metric_summary = summarize(output / "events.jsonl")
    result = {
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
    if metric_summary["native_metric_availability"]:
        result["native_metric_availability"] = metric_summary["native_metric_availability"]
    return result


def _canonical_result_from_terminal_events(manifest_path: Path, output: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    report = preflight_canonical(manifest_path)
    manifest = preflight(manifest_path).manifest
    assert isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3))
    digest = manifest_digest(manifest)
    outcomes = Counter((row["data"].get("outcome") or "outcome_unavailable") for row in rows)
    terminations = Counter(row["termination"] for row in rows)
    ledger_path = output / "events.jsonl"
    events = read_canonical_events(ledger_path)
    for row in rows:
        validate_canonical_shot(events, canonical_public_shot_context(manifest_path, shot_id=row["shot_id"]))
    return {
        "schema_version": 2,
        "title": f"{report['run_id']} — {manifest.evidence.relation} {manifest.evidence.fixture} {manifest.evidence.assessment_status}",
        "run_id": report["run_id"],
        "relation": manifest.evidence.relation,
        "fixture": manifest.evidence.fixture,
        "assessment_status": manifest.evidence.assessment_status,
        "manifest_path": str(manifest_path),
        "manifest_sha256": digest,
        "ledger_path": str(ledger_path),
        "ledger_sha256": sha256(ledger_path.read_bytes()).hexdigest(),
        "final_row_count": len(rows),
        "shot_ids": [row["shot_id"] for row in rows],
        "policy_identity": report["policy_identity"],
        "denominators": {"all_terminal_shots": len(rows), **dict(sorted(outcomes.items()))},
        "terminations": dict(sorted(terminations.items())),
        "statistical_claim": (
            "not_assessed; canonical development fixture, not a source-faithful or statistical reproduction"
            if manifest.evidence.relation == "canonical_implemented"
            else "not_assessed; bounded pilot adaptation, not a statistical reproduction, performance ranking, or superiority claim"
        ),
    }


def run_canonical(manifest_path: str | Path, output: str | Path) -> dict[str, Any]:
    """Run only missing canonical shots and reconstruct result solely from v2 terminals."""
    manifest_path, output = Path(manifest_path), Path(output)
    report = preflight_canonical(manifest_path)
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "events.jsonl"
    for shot_id in range(report["shot_budget"]):
        run_canonical_one(manifest_path, shot_id=shot_id, ledger_path=ledger_path)
    rows = canonical_terminal_rows(ledger_path, report["run_id"])
    expected = list(range(report["shot_budget"]))
    if [row["shot_id"] for row in rows] != expected:
        raise ValueError("canonical ledger does not contain exactly the pinned terminal shot IDs")
    result_path = output / "result.json"
    result = _canonical_result_from_terminal_events(manifest_path, output, rows)
    if result_path.exists() and _read_json(result_path) != result:
        raise ValueError("canonical result conflicts with terminal evidence")
    if not result_path.exists():
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**report, "output": str(output), "final_row_count": len(rows)}


def _verify_canonical_run(output: Path, result: dict[str, Any]) -> dict[str, Any]:
    if result.get("assessment_status") != "not_assessed":
        raise ValueError("canonical result is missing the not_assessed label")
    relation_fixture = (result.get("relation"), result.get("fixture"))
    if relation_fixture not in {("canonical_implemented", "development_fixture"), ("pilot_adaptation", "pilot_adaptation")}:
        raise ValueError("canonical result has an invalid transparent evidence label")
    manifest_path = Path(result["manifest_path"])
    report = preflight_canonical(manifest_path)
    ledger_path = output / "events.jsonl"
    if result.get("ledger_sha256") != sha256(ledger_path.read_bytes()).hexdigest():
        raise ValueError("canonical result ledger hash does not match durable evidence")
    rows = canonical_terminal_rows(ledger_path, report["run_id"])
    if [row["shot_id"] for row in rows] != list(range(report["shot_budget"])):
        raise ValueError("canonical terminal rows differ from the manifest shot budget")
    events = read_canonical_events(ledger_path)
    for row in rows:
        validate_canonical_shot(events, canonical_public_shot_context(manifest_path, shot_id=row["shot_id"]))
    expected = _canonical_result_from_terminal_events(manifest_path, output, rows)
    if result != expected:
        raise ValueError("canonical result JSON does not equal terminal structural evidence")
    return {**report, "output": str(output), "final_row_count": len(rows), "verified_at": datetime.now(timezone.utc).isoformat()}


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
        try:
            run_one(manifest_path, shot_id=shot_id, ledger_path=ledger_path)
        except Exception:
            # A recorded per-shot exception is a terminal observation and belongs
            # in the denominator. Unrecorded failures still abort this invocation.
            if shot_id not in {row["shot_id"] for row in _terminal_rows(ledger_path, manifest.run_id)}:
                raise
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
    if result.get("relation") in {"canonical_implemented", "pilot_adaptation"} and result.get("ledger_sha256") is not None:
        return _verify_canonical_run(output, result)
    if result.get("title") == "Phase 3 bounded matched pilot adaptations — not_assessed":
        terminals = result.get("verified_terminals")
        reports = result.get("public_verify_reports")
        if (
            result.get("relation") != "pilot_adaptation"
            or result.get("assessment_status") != "not_assessed"
            or result.get("matched_sample_identities") is not True
            or result.get("rejected_undefined") is not True
            or result.get("statistical_claim") != "not_assessed; bounded pilots are not statistical curve reproductions, performance rankings, or superiority claims"
            or not isinstance(terminals, list)
            or not terminals
            or not isinstance(reports, list)
            or not reports
        ):
            raise ValueError("Phase 3 pilot aggregate is missing transparent matched-pilot evidence")
        expected_events: list[dict[str, Any]] = []
        expected_terminals: list[dict[str, Any]] = []
        matched: dict[tuple[str, int], set[str]] = {}
        for report in reports:
            if not isinstance(report, dict) or not isinstance(report.get("output"), str):
                raise ValueError("Phase 3 pilot aggregate has an invalid public verification report")
            run_output = Path(report["output"])
            if not run_output.resolve().is_relative_to((output / "runs").resolve()):
                raise ValueError("Phase 3 pilot run path escapes the aggregate")
            actual_report = verify_run(run_output)
            if {key: value for key, value in actual_report.items() if key != "verified_at"} != {
                key: value for key, value in report.items() if key != "verified_at"
            }:
                raise ValueError("Phase 3 pilot verification report differs from public replay")
            run_result = _read_json(run_output / "result.json")
            manifest_path = Path(run_result["manifest_path"])
            if not manifest_path.resolve().is_relative_to((output / "manifests").resolve()):
                raise ValueError("Phase 3 pilot manifest path escapes the aggregate")
            manifest = _read_json(manifest_path)
            events = read_canonical_events(run_output / "events.jsonl")
            expected_events.extend(events)
            samples = {
                (event["run_id"], event["shot_id"]): event["sample_seed_identity"]
                for event in events if event.get("kind") == "shot_begin"
            }
            for event in events:
                if event.get("kind") != "termination":
                    continue
                data = event["data"]
                sample = samples[(event["run_id"], event["shot_id"])]
                matched.setdefault((data["code_id"], event["shot_id"]), set()).add(sample)
                expected_terminals.append({
                    "run_id": event["run_id"], "shot_id": event["shot_id"],
                    "termination": event["termination"], "sample_identity": sample,
                    "code_id": data["code_id"],
                    "artifact_raw_sha256": data["artifact_raw_sha256"],
                    "artifact_semantic_sha256": data["artifact_semantic_sha256"],
                    "canonical_identity": data["canonical_identity"],
                    "composition_identity": data["composition_identity"],
                    "relation": data["evidence_relation"],
                    "assessment_status": data["assessment_status"],
                    "outcome": data.get("outcome"), "converged": data.get("converged"),
                    "qualified_iterations": data.get("schedule_terminal", {}).get(
                        "source_iteration", {"count": data.get("iterations", 0), "schedule": "flooding"}
                    ),
                    "work_vector": data["work_vector"],
                    "schedule_terminal": data.get("schedule_terminal"),
                    "profile": data.get("profile"),
                    "setup_runtime": data["setup_runtime"],
                    "decode_runtime": data["decode_runtime"],
                    "policy_effects": data["policy_effects"],
                    "matrix_hashes": manifest["artifact"]["matrix_hashes"],
                    "budget_views": {
                        "common_c2v_cap": manifest["budgets"]["shot"]["work_limits"]["check_to_variable_updates"],
                        "qualified_iteration_limit": manifest["budgets"]["shot"]["max_iterations"],
                        "budget_scope": "shot", "equal_total_cost_claim": False,
                    },
                })
        aggregate_events = read_canonical_events(output / "events.jsonl")
        if aggregate_events != expected_events or terminals != expected_terminals:
            raise ValueError("Phase 3 pilot aggregate differs from its publicly verified run evidence")
        if result.get("code_ids") != sorted({item["code_id"] for item in expected_terminals}):
            raise ValueError("Phase 3 pilot code identities differ from verified terminals")
        if not matched or any(len(values) != 1 for values in matched.values()):
            raise ValueError("Phase 3 pilot physical samples are not matched by code and shot")
        if any(
            terminal.get("relation") != "pilot_adaptation"
            or terminal.get("assessment_status") != "not_assessed"
            for terminal in terminals
        ):
            raise ValueError("Phase 3 pilot aggregate terminal labels are not transparent")
        return {
            "output": str(output),
            "verified_terminals": len(terminals),
            "matched_sample_identities": True,
        }
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
    canonical_command = commands.add_parser("canonical")
    canonical_command.add_argument("manifest", type=Path)
    canonical_command.add_argument("--output", type=Path, required=True)
    reconcile_command = commands.add_parser("reconcile")
    reconcile_command.add_argument("ledger", type=Path)
    verify_command = commands.add_parser("verify-run")
    verify_command.add_argument("output", type=Path)
    cluster_command = commands.add_parser("qualify-cluster-artifact")
    cluster_command.add_argument("specification", type=Path)
    cluster_command.add_argument("--approved-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "validate-evidence":
        records = evidence.load_seed_records(args.records)
        _dump({"records": str(args.records), "paper_experiments": sorted(records["paper_experiments"]), "status": "valid"})
    elif args.command == "preflight":
        _dump(preflight_canonical(args.manifest) if isinstance(preflight(args.manifest).manifest, (CanonicalExperimentV2, CanonicalExperimentV3)) else preflight_pilot(args.manifest))
    elif args.command == "pilot":
        _dump(run_pilot(args.manifest, args.output))
    elif args.command == "canonical":
        _dump(run_canonical(args.manifest, args.output))
    elif args.command == "reconcile":
        _dump(_reconcile_report(args.ledger))
    elif args.command == "verify-run":
        _dump(verify_run(args.output))
    elif args.command == "qualify-cluster-artifact":
        qualification = qualify_cluster_artifact(args.specification, approved_root=args.approved_root)
        _dump(qualification.report())
        if not qualification.qualified:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
