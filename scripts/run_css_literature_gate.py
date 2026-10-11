"""Bounded, matched B1 mechanism gate for three source-qualified CSS policies.

The public `ensure_study` path does every computation. This module freezes the
source inventory and verifies that the installed command reuses those results.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tomllib
from typing import Any

from bp_registry.artifacts import load_artifact
from bp_registry.cli import verify_run
from bp_registry.ledger import read_canonical_events
from bp_registry.literature import (
    parse_literature_policy, qualify_bhatnagar_source_records,
    qualify_rabeti_source_record, qualify_yao_source_records,
)
from bp_registry.study import ensure_study


ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION = ROOT / "literature_policies/qualification-v1.json"
SELECTED = (
    ("yao", "yao-2024-guided-decimation", "bpgd-t100-r002"),
    ("bhatnagar", "bhatnagar-2026-impulse-decoding", "first-convergence-0"),
    ("rabeti", "rabeti-2026-multiple-bases-bp-list-decoding", "mbbp-ld"),
)
VOTE_POLICY = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld-vote.toml"


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_once(path: Path, value: Any) -> None:
    content = _json_bytes(value)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"frozen gate file differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _study(study: Path) -> dict[str, Any]:
    value = json.loads(study.read_text())
    expected_work_limits = {
        "check_to_variable_updates": 100000000, "variable_to_check_updates": 100000000,
        "belief_assemblies": 100000000, "residual_priority_evaluations": 100000000,
        "bp_calls": 1000000, "candidate_checks": 100000000, "intervention_actions": 2000,
        "branch_expansions": 0, "branch_prunes": 0, "relay_transfers": 0, "fallback_calls": 0,
    }
    if (value.get("schema_version") != 8 or value.get("run_id") != "css-literature-b1-gate-v1"
            or value.get("error_rate") != 0.000001 or value.get("budgets", {}).get("max_shots") != 2
            or value.get("budgets", {}).get("denominator_rule") != "all_terminal_shots"
            or value.get("numerical_profiles") != {"binary_spa": "cpu-float64-spa-v1",
                                                    "normalized_min_sum": "cpu-float64-min-sum-v1"}
            or value.get("randomness", {}).get("physical_sample_identity") != "css-literature-b1-gate-v1-matched"
            or value.get("evidence", {}).get("assessment_status") != "not_assessed"
            or value.get("evidence", {}).get("relation") != "pilot_adaptation"):
        raise ValueError("B1 gate study differs from its prespecified bounded design")
    artifact = value.get("artifact", {})
    if (artifact.get("code_id") != "b1-ghp-882"
            or artifact.get("raw_sha256") != "3b3fb669daf18cb294049c2c20a457a2da997ad1a7da9f0667171d3b48eb38a6"
            or artifact.get("semantic_sha256") != "ea1200028ace4a446dc04fe40c9eb9607903b31e3772c2921835ed6e20430548"):
        raise ValueError("B1 gate artifact identity differs from the project-qualified candidate")
    for scope in ("shot", "search", "attempt"):
        if (value["budgets"][scope]["max_iterations"] != 100
                or value["budgets"][scope]["work_limits"] != expected_work_limits):
            raise ValueError("B1 gate work or iteration cap differs from the frozen study")
    root = (study.parent / artifact["root"]).resolve()
    loaded = load_artifact(root, artifact["path"], expected_raw_sha256=artifact["raw_sha256"],
                           expected_semantic_sha256=artifact["semantic_sha256"])
    if loaded.code.n != 882 or loaded.code.hz.shape[0] != 441:
        raise ValueError("B1 gate artifact dimensions differ from the qualified candidate")
    return value


def qualification_inventory(study: Path) -> dict[str, Any]:
    """Bind all fourteen source records to the parser and local artifact."""
    value = _study(study)
    _ = value
    folders = {name: ROOT / "literature_policies" / folder for name, folder, _selected in SELECTED}
    groups = {
        "yao": qualify_yao_source_records(folders["yao"], code_block_length=882),
        "bhatnagar": qualify_bhatnagar_source_records(folders["bhatnagar"], code_block_length=882),
        "rabeti": (qualify_rabeti_source_record(folders["rabeti"]),),
    }
    if {family: len(rows) for family, rows in groups.items()} != {"yao": 10, "bhatnagar": 3, "rabeti": 1}:
        raise ValueError("CSS literature gate must account for exactly ten, three, and one source records")
    records = []
    for family, rows in groups.items():
        for row in rows:
            source = row.source_path
            document = tomllib.loads(source.read_text())
            if document.get("execution_status") != "not_runnable":
                raise ValueError("a source transcription cannot be directly executable")
            parsed_source = parse_literature_policy(source)
            if parsed_source.disposition != "non_runnable":
                raise ValueError("source transcription bypassed its non-runnable parser boundary")
            counterpart = source.with_name(f"{row.variant_id}.toml")
            runnable = None
            if counterpart.is_file():
                policy = parse_literature_policy(counterpart)
                projection = policy.decoder_projection(code_block_length=882, code_check_count=441)
                if (policy.disposition != "runnable" or policy.provenance["variant_id"] != row.variant_id
                        or policy.provenance["source"]["revision"] != document["source"]["revision"]
                        or policy.provenance["qualification"] != row.qualification
                        or any(projection[role] != row.executable[role] for role in (
                            "update", "schedule", "state_memory", "intervention", "stopping", "selection", "postprocessing"
                        ))):
                    raise ValueError(f"runnable counterpart is not the qualified source mapping: {counterpart}")
                runnable = {
                    "path": str(counterpart.relative_to(ROOT)),
                    "raw_sha256": policy.raw_document_identity,
                    "execution_sha256": policy.execution_identity_for(code_block_length=882, code_check_count=441),
                }
            records.append({
                "family": family, "variant_id": row.variant_id,
                "source_spec": str(source.relative_to(ROOT)), "source_sha256": _sha(source),
                "source_revision": document["source"]["revision"],
                "source_execution_status": "not_runnable",
                "execution_status": "runnable_canonical_adaptation" if runnable else "source_spec_only",
                "compiler_disposition": row.disposition,
                "qualification": row.qualification,
                "source_faithful": False,
                "blockers": sorted(set(parsed_source.blocking_features) | set(row.unresolved)),
                "runnable_counterpart": runnable,
            })
    return {"schema_version": 1, "study_sha256": _sha(study),
            "artifact_raw_sha256": value["artifact"]["raw_sha256"], "records": records}


def _selected_policy(family: str, folder: str, variant: str) -> Path:
    path = ROOT / "literature_policies" / folder / f"{variant}.toml"
    policy = parse_literature_policy(path)
    if policy.disposition != "runnable" or policy.provenance["variant_id"] != variant:
        raise ValueError(f"selected policy is not a qualified runnable variant: {family}/{variant}")
    return path


def _snapshot(response: dict[str, Any], *, policy: Path, output: Path, shots: int) -> dict[str, Any]:
    run = Path(response["output"]).resolve()
    if not run.is_relative_to((output / "cache").resolve()):
        raise ValueError("study result escaped the gate cache")
    result = json.loads((run / "result.json").read_text())
    events = read_canonical_events(run / "events.jsonl")
    terminals = [event for event in events if event["kind"] == "termination"]
    if (result["denominators"]["all_terminal_shots"] != shots
            or len(terminals) != shots or {event["shot_id"] for event in terminals} != set(range(shots))):
        raise ValueError("gate result omits a terminal or changes the all-shot denominator")
    if result["assessment_status"] != "not_assessed":
        raise ValueError("bounded B1 gate cannot claim a paper-curve assessment")
    receipt = run / "request-receipts" / f'{response["request_receipt"]}.json'
    if not receipt.is_file() or not (run / "cache-receipt.json").is_file():
        raise ValueError("gate result lacks request or computation provenance")
    for event in events:
        if event["kind"] == "original_check":
            payload = event["data"].get("payload", event["data"])
            if payload.get("valid") is False:
                raise ValueError("gate ledger contains an invalid original correction")
    return {
        "policy": str(policy.relative_to(ROOT)), "policy_sha256": _sha(policy),
        "cache_key": response["cache_key"], "output": str(run.relative_to(output.resolve())),
        "manifest_sha256": _sha(run / "manifest.json"),
        "ledger_sha256": _sha(run / "events.jsonl"), "result_sha256": _sha(run / "result.json"),
        "computation_receipt_sha256": _sha(run / "cache-receipt.json"),
        "request_receipt": response["request_receipt"], "request_receipt_sha256": _sha(receipt),
        "shot_denominator": shots, "terminations": result["terminations"],
    }


def prepare(study: Path) -> dict[str, Any]:
    inventory = qualification_inventory(study)
    _write_once(QUALIFICATION, inventory)
    return {"status": "prepared", "source_records": len(inventory["records"])}


def run(study: Path, output: Path) -> dict[str, Any]:
    prepare(study)
    shots = _study(study)["budgets"]["max_shots"]
    entries = {}
    statuses = {}
    for family, folder, variant in SELECTED:
        policy = _selected_policy(family, folder, variant)
        response = ensure_study(study, policy, results_root=output / "cache")
        if response["status"] not in {"computed", "reused"}:
            raise ValueError(f"{family} did not compute or verify through the public study API")
        entries[family] = _snapshot(response, policy=policy, output=output, shots=shots)
        statuses[family] = response["status"]
    index = {"schema_version": 1, "study": str(study.relative_to(ROOT)),
             "study_sha256": _sha(study), "qualification_sha256": _sha(QUALIFICATION),
             "assessment_status": "not_assessed", "entries": entries}
    _write_once(output / "evidence-index.json", index)
    _write_once(output / "verification-summary.json", {
        "schema_version": 1, "study_sha256": _sha(study),
        "entries": {family: {"public_replay": "passed", "manifest_sha256": row["manifest_sha256"],
                             "ledger_sha256": row["ledger_sha256"], "result_sha256": row["result_sha256"],
                             "final_row_count": row["shot_denominator"]}
                    for family, row in entries.items()},
    })
    return {"status": "verified", "requests": statuses, "index": str(output / "evidence-index.json")}


def run_vote(study: Path, output: Path) -> dict[str, Any]:
    """Run and replay the separately declared Rabeti vote policy in caller-owned cache."""
    policy = parse_literature_policy(VOTE_POLICY)
    if (policy.disposition != "runnable" or policy.provenance.get("qualification") != "canonical_adaptation_not_assessed"
            or policy.executable.get("vote") != {
                "object": "correction_bits", "electorate_rule": "admitted_members",
                "aggregation": "coordinate_majority", "tie_bit": 1,
            }):
        raise ValueError("vote policy is not the closed canonical adaptation")
    response = ensure_study(study, VOTE_POLICY, results_root=output / "cache")
    if response["status"] not in {"computed", "reused"}:
        raise ValueError("vote policy did not compute through the public study API")
    run = Path(response["output"])
    result = json.loads((run / "result.json").read_text())
    events = read_canonical_events(run / "events.jsonl")
    if (result.get("assessment_status") != "not_assessed"
            or not any(event["kind"] == "vote_electorate" for event in events)
            or not any(event["kind"] == "termination" and event["termination"] in {
                "vote_selected_original_valid_candidate", "vote_aggregate_original_invalid", "no_eligible_vote_candidate",
            } for event in events)
            or not all(event["data"].get("identity", {}).get("source_status") == "canonical_adaptation"
                       for event in events)):
        raise ValueError("vote output lacks canonical-adaptation labels or complete terminal evidence")
    verification = verify_run(run)
    return {
        "status": verification["status"] if "status" in verification else "verified",
        "policy": str(VOTE_POLICY.relative_to(ROOT)),
        "policy_sha256": _sha(VOTE_POLICY),
        "cache_key": response["cache_key"],
        "output": str(run),
        "final_row_count": verification["final_row_count"],
        "assessment_status": "not_assessed",
    }


def _index(study: Path, output: Path) -> dict[str, Any]:
    index = json.loads((output / "evidence-index.json").read_text())
    if (index.get("schema_version") != 1 or index.get("study_sha256") != _sha(study)
            or index.get("qualification_sha256") != _sha(QUALIFICATION)
            or set(index.get("entries", {})) != {family for family, _folder, _variant in SELECTED}):
        raise ValueError("gate evidence index differs from its frozen inputs")
    return index


def cli_smoke(study: Path, output: Path, command: Path) -> dict[str, Any]:
    index = _index(study, output)
    shots = _study(study)["budgets"]["max_shots"]
    receipts = {}
    for family, folder, variant in SELECTED:
        policy = _selected_policy(family, folder, variant)
        prior = index["entries"][family]
        completed = subprocess.run(
            [str(command), str(study), "--decoder", str(policy), "--results-root", str(output / "cache")],
            cwd=ROOT, check=True, capture_output=True, text=True,
            env={**os.environ, "OMP_NUM_THREADS": "1"},
        )
        answer = json.loads(completed.stdout)
        if answer.get("status") != "reused":
            raise ValueError(f"installed CLI did not reuse {family} evidence")
        actual = _snapshot(answer, policy=policy, output=output, shots=shots)
        if actual != prior:
            raise ValueError(f"installed CLI changed {family} result identity or denominator")
        receipts[family] = {"status": "reused", "cache_key": actual["cache_key"],
                            "ledger_sha256": actual["ledger_sha256"], "result_sha256": actual["result_sha256"],
                            "shot_denominator": shots}
    document = {"schema_version": 1, "study_sha256": _sha(study),
                "evidence_index_sha256": _sha(output / "evidence-index.json"), "entries": receipts}
    _write_once(output / "cli-smoke.json", document)
    return {"status": "reused", "entries": list(receipts)}


def verify(study: Path, output: Path) -> dict[str, Any]:
    if qualification_inventory(study) != json.loads(QUALIFICATION.read_text()):
        raise ValueError("source qualification changed after the gate was frozen")
    index = _index(study, output)
    shots = _study(study)["budgets"]["max_shots"]
    for family, folder, variant in SELECTED:
        prior = index["entries"][family]
        run = (output / prior["output"]).resolve()
        verification = verify_run(run)
        if verification["final_row_count"] != shots:
            raise ValueError(f"{family} public replay changed the shot denominator")
        response = {"output": str(run), "cache_key": prior["cache_key"],
                    "request_receipt": prior["request_receipt"]}
        if _snapshot(response, policy=_selected_policy(family, folder, variant), output=output, shots=shots) != prior:
            raise ValueError(f"{family} packaged evidence changed")
    cli = json.loads((output / "cli-smoke.json").read_text())
    summary = json.loads((output / "verification-summary.json").read_text())
    expected_summary = {"schema_version": 1, "study_sha256": _sha(study),
                        "entries": {family: {"public_replay": "passed",
                                             "manifest_sha256": row["manifest_sha256"],
                                             "ledger_sha256": row["ledger_sha256"],
                                             "result_sha256": row["result_sha256"],
                                             "final_row_count": row["shot_denominator"]}
                                    for family, row in index["entries"].items()}}
    if summary != expected_summary:
        raise ValueError("gate public replay summary is absent or stale")
    expected_cli_entries = {family: {
        "status": "reused", "cache_key": row["cache_key"],
        "ledger_sha256": row["ledger_sha256"], "result_sha256": row["result_sha256"],
        "shot_denominator": shots,
    } for family, row in index["entries"].items()}
    if (cli.get("study_sha256") != _sha(study)
            or cli.get("evidence_index_sha256") != _sha(output / "evidence-index.json")
            or cli.get("entries") != expected_cli_entries):
        raise ValueError("CLI reuse receipt is absent or stale")
    return {"status": "verified", "source_records": 14, "paper_families": 3,
            "shot_denominator_per_policy": shots, "assessment_status": "not_assessed"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "vote", "cli-smoke", "verify"))
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data/results/css-literature-gate-v1")
    parser.add_argument("--bp-registry", type=Path, default=ROOT / ".venv/bin/bp-registry")
    args = parser.parse_args()
    study = args.study.resolve()
    output = args.output.resolve()
    if args.command == "prepare":
        result = prepare(study)
    elif args.command == "run":
        result = run(study, output)
    elif args.command == "vote":
        result = run_vote(study, output)
    elif args.command == "cli-smoke":
        result = cli_smoke(study, output, args.bp_registry.resolve())
    else:
        result = verify(study, output)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
