"""Run bounded Phase 3 policy pilots only through the public CLI boundary."""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable


DEFAULT_MANIFESTS = (
    "phase3-pilot-bb144.json",
    "phase3-pilot-b1.json",
    "phase3-pilot-hgp-gallager.json",
)


def _json_command(repository_root: Path, *arguments: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "bp_registry.cli", *arguments],
        cwd=repository_root, text=True, capture_output=True,
        env={**__import__("os").environ, "PYTHONPATH": str(repository_root / "src"), "OMP_NUM_THREADS": "1"},
    )
    if completed.returncode:
        raise RuntimeError(f"public CLI {' '.join(arguments)} failed: {completed.stderr or completed.stdout}")
    return json.loads(completed.stdout)


_LOCAL_GRAPH = {
    "b1-ghp-882": (441, "e679f44025e5afd7688339c765740bfca34edf36d3a6e595f1296bbceb4188c6"),
    "hgp-gallager-3-4-seed-20260923": (108, "1b3fe1fa3a814444c7ac52a72e599127a215d1704ae7f33ef92a9de5a7bb1a78"),
}


def _variant_manifest(base: dict[str, Any], name: str) -> dict[str, Any]:
    value = deepcopy(base)
    value["run_id"] = f"{base['run_id']}-{name}"
    update = value["policies"]["update"]
    if name == "spa":
        return value
    value["numerical_profile"] = "cpu-float64-min-sum-v1"
    if name == "ms":
        update.update({"kind": "min_sum", "binding_id": "update-min-sum-v1"})
    elif name == "nms":
        update.update({"kind": "normalized_min_sum", "binding_id": "update-normalized-min-sum-v1", "parameter_assignment": {"shape": "scalar", "value": 0.8}})
    elif name == "oms":
        update.update({"kind": "offset_min_sum", "binding_id": "update-offset-min-sum-v1", "parameter_assignment": {"shape": "scalar", "value": 0.2}})
    else:
        raise ValueError(f"unknown focused pilot update variant {name!r}")
    return value


def _schedule_variant(base: dict[str, Any], name: str) -> dict[str, Any]:
    value = deepcopy(base)
    value["run_id"] = f"{base['run_id']}-{name}"
    count, graph_sha256 = _LOCAL_GRAPH[base["artifact"]["code_id"]]
    schedule = value["policies"]["schedule"]
    if name == "spa":
        return value
    if name in {"layered", "randomized"}:
        schedule.update({"kind": name, "binding_id": f"schedule-{name}-v1", "partitions": [[index] for index in range(count)], "provenance": "explicit"})
        if name == "randomized":
            schedule.update({"base_schedule": "layered", "refresh_scope": "attempt", "root_identity": "a" * 64})
    elif name == "cn":
        schedule.update({"kind": "check_node_serial", "binding_id": "schedule-check-node-serial-v1"})
    elif name == "vn":
        schedule.update({"kind": "variable_node_serial", "binding_id": "schedule-variable-node-serial-v1"})
    elif name == "residual":
        schedule.update({"kind": "residual", "binding_id": "schedule-residual-v1"})
    elif name == "nms-check":
        value["numerical_profile"] = "cpu-float64-min-sum-v1"
        value["policies"]["update"].update({"kind": "normalized_min_sum", "binding_id": "update-normalized-min-sum-v1", "parameter_assignment": {"shape": "check", "graph_sha256": graph_sha256, "values": [0.7 if index % 2 else 0.9 for index in range(count)]}})
    elif name == "nms-seeded":
        value["numerical_profile"] = "cpu-float64-min-sum-v1"
        generator = {
            "shape": "check", "graph_sha256": graph_sha256,
            "distribution": "uniform", "low": 0.7, "high": 0.9,
            "root_seed_identity": "b" * 64, "provenance": "exploratory",
        }
        value["policies"]["update"].update({
            "kind": "normalized_min_sum", "binding_id": "update-normalized-min-sum-v1",
            "parameter_generator": generator,
            "parameter_refresh": {"scope": "configuration", "generator": generator},
        })
    else:
        raise ValueError(f"unknown focused pilot schedule variant {name!r}")
    return value


def _variants(base: dict[str, Any]) -> tuple[str, ...]:
    if base["artifact"]["code_id"] == "gross-bb-144":
        return ("spa", "ms", "nms", "oms")
    variants = ("spa", "layered", "cn", "vn", "randomized", "residual", "nms-check")
    return variants + (("nms-seeded",) if base["artifact"]["code_id"] == "hgp-gallager-3-4-seed-20260923" else ())


def _terminal_summary(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    events = list(events)
    samples = {(event["run_id"], event["shot_id"]): event["sample_seed_identity"] for event in events if event["kind"] == "shot_begin"}
    terminals: list[dict[str, Any]] = []
    for event in events:
        if event["kind"] != "termination":
            continue
        data = event["data"]
        terminals.append({
            "run_id": event["run_id"], "shot_id": event["shot_id"], "termination": event["termination"],
            "sample_identity": samples[(event["run_id"], event["shot_id"])], "code_id": data["code_id"],
            "artifact_raw_sha256": data["artifact_raw_sha256"],
            "artifact_semantic_sha256": data["artifact_semantic_sha256"],
            "canonical_identity": data["canonical_identity"],
            "composition_identity": data["composition_identity"],
            "relation": data["evidence_relation"], "assessment_status": data["assessment_status"],
            "outcome": data.get("outcome"), "converged": data.get("converged"),
            "qualified_iterations": data.get("schedule_terminal", {}).get("source_iteration", {"count": data.get("iterations", 0), "schedule": "flooding"}),
            "work_vector": data["work_vector"], "schedule_terminal": data.get("schedule_terminal"),
            "profile": data.get("profile"), "policy_effects": data["policy_effects"],
        })
    return terminals


def run_pilots(*, repository_root: Path, output_root: Path, manifest_names: tuple[str, ...] = DEFAULT_MANIFESTS, reuse_verified_runs: bool = False) -> dict[str, Any]:
    """Preflight, run, and independently verify every retained pilot terminal."""
    repository_root = repository_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    generated = output_root / "manifests"
    generated.mkdir(exist_ok=True)
    all_events: list[str] = []
    terminals: list[dict[str, Any]] = []
    verified: list[dict[str, Any]] = []
    for manifest_name in manifest_names:
        base_path = repository_root / "data" / "manifests" / manifest_name
        base = json.loads(base_path.read_text(encoding="utf-8"))
        for variant in _variants(base):
            manifest = _variant_manifest(base, variant) if base["artifact"]["code_id"] == "gross-bb-144" else _schedule_variant(base, variant)
            manifest_path = generated / f"{manifest['run_id']}.json"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            run_output = output_root / "runs" / manifest["run_id"]
            if not reuse_verified_runs or not (run_output / "result.json").is_file():
                _json_command(repository_root, "preflight", str(manifest_path))
                _json_command(repository_root, "canonical", str(manifest_path), "--output", str(run_output))
            verified.append(_json_command(repository_root, "verify-run", str(run_output)))
            text = (run_output / "events.jsonl").read_text(encoding="utf-8")
            all_events.extend(line for line in text.splitlines() if line)
            for terminal in _terminal_summary(json.loads(line) for line in text.splitlines() if line):
                terminal["matrix_hashes"] = manifest["artifact"]["matrix_hashes"]
                terminal["budget_views"] = {
                    "common_c2v_cap": manifest["budgets"]["shot"]["work_limits"]["check_to_variable_updates"],
                    "qualified_iteration_limit": manifest["budgets"]["shot"]["max_iterations"],
                    "budget_scope": "shot",
                    "equal_total_cost_claim": False,
                }
                terminals.append(terminal)
    by_code: dict[str, list[str]] = defaultdict(list)
    by_code_shot: dict[tuple[str, int], list[str]] = defaultdict(list)
    for terminal in terminals:
        by_code[terminal["code_id"]].append(terminal["sample_identity"])
        by_code_shot[(terminal["code_id"], terminal["shot_id"])].append(terminal["sample_identity"])
    matched = all(len(set(values)) == 1 for values in by_code_shot.values())
    if not matched or any(item["relation"] != "pilot_adaptation" or item["assessment_status"] != "not_assessed" for item in terminals):
        raise ValueError("pilot terminal identity or transparent assessment label drifted")
    (output_root / "events.jsonl").write_text("\n".join(all_events) + "\n", encoding="utf-8")
    undefined = deepcopy(json.loads((repository_root / "data" / "manifests" / "phase3-pilot-b1.json").read_text(encoding="utf-8")))
    undefined["policies"]["schedule"].update({"kind": "randomized", "binding_id": "schedule-randomized-v1"})
    undefined_path = generated / "undefined-randomized-without-controls.json"
    undefined_path.write_text(json.dumps(undefined, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rejected_undefined = False
    try:
        _json_command(repository_root, "preflight", str(undefined_path))
    except RuntimeError:
        rejected_undefined = True
    if not rejected_undefined:
        raise ValueError("undefined randomized schedule unexpectedly passed public preflight")
    result = {
        "schema_version": 1,
        "title": "Phase 3 bounded matched pilot adaptations — not_assessed",
        "relation": "pilot_adaptation",
        "assessment_status": "not_assessed",
        "statistical_claim": "not_assessed; bounded pilots are not statistical curve reproductions, performance rankings, or superiority claims",
        "code_ids": sorted(by_code), "matched_sample_identities": matched,
        "verified_terminals": terminals, "public_verify_reports": verified, "rejected_undefined": rejected_undefined,
    }
    (output_root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"code_ids": result["code_ids"], "labels": {"relation": result["relation"], "assessment_status": result["assessment_status"]}, "matched_sample_identities": matched, "verified_terminals": terminals, "rejected_undefined": rejected_undefined}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/results/phase3-pilots"))
    parser.add_argument("--manifest", action="append", dest="manifests")
    parser.add_argument("--reuse-verified-runs", action="store_true", help="rebuild the aggregate after public verification of existing complete run directories")
    args = parser.parse_args()
    report = run_pilots(repository_root=Path(__file__).resolve().parents[1], output_root=args.output, manifest_names=tuple(args.manifests or DEFAULT_MANIFESTS), reuse_verified_runs=args.reuse_verified_runs)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
