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
            "relation": data["evidence_relation"], "assessment_status": data["assessment_status"],
            "outcome": data.get("outcome"), "converged": data.get("converged"),
            "qualified_iterations": data.get("schedule_terminal", {}).get("source_iteration", {"count": data.get("iterations", 0), "schedule": "flooding"}),
            "work_vector": data["work_vector"], "schedule_terminal": data.get("schedule_terminal"),
            "profile": data.get("profile"), "policy_effects": data["policy_effects"],
        })
    return terminals


def run_pilots(*, repository_root: Path, output_root: Path, manifest_names: tuple[str, ...] = DEFAULT_MANIFESTS) -> dict[str, Any]:
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
        for variant in ("spa", "ms", "nms", "oms"):
            manifest = _variant_manifest(base, variant)
            manifest_path = generated / f"{manifest['run_id']}.json"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            _json_command(repository_root, "preflight", str(manifest_path))
            run_output = output_root / "runs" / manifest["run_id"]
            _json_command(repository_root, "canonical", str(manifest_path), "--output", str(run_output))
            verified.append(_json_command(repository_root, "verify-run", str(run_output)))
            text = (run_output / "events.jsonl").read_text(encoding="utf-8")
            all_events.extend(line for line in text.splitlines() if line)
            terminals.extend(_terminal_summary(json.loads(line) for line in text.splitlines() if line))
    by_code: dict[str, list[str]] = defaultdict(list)
    for terminal in terminals:
        by_code[terminal["code_id"]].append(terminal["sample_identity"])
    matched = all(len(set(values)) == 1 for values in by_code.values())
    if not matched or any(item["relation"] != "pilot_adaptation" or item["assessment_status"] != "not_assessed" for item in terminals):
        raise ValueError("pilot terminal identity or transparent assessment label drifted")
    (output_root / "events.jsonl").write_text("\n".join(all_events) + "\n", encoding="utf-8")
    result = {
        "schema_version": 1,
        "title": "Phase 3 bounded matched pilot adaptations — not_assessed",
        "relation": "pilot_adaptation",
        "assessment_status": "not_assessed",
        "statistical_claim": "not_assessed; bounded pilots are not statistical curve reproductions, performance rankings, or superiority claims",
        "code_ids": sorted(by_code), "matched_sample_identities": matched,
        "verified_terminals": terminals, "public_verify_reports": verified,
    }
    (output_root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"code_ids": result["code_ids"], "labels": {"relation": result["relation"], "assessment_status": result["assessment_status"]}, "matched_sample_identities": matched, "verified_terminals": terminals}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/results/phase3-pilots"))
    parser.add_argument("--manifest", action="append", dest="manifests")
    args = parser.parse_args()
    report = run_pilots(repository_root=Path(__file__).resolve().parents[1], output_root=args.output, manifest_names=tuple(args.manifests or DEFAULT_MANIFESTS))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
