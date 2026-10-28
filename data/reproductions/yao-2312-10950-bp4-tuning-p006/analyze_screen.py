"""Audit every paired exploratory screen ledger and rank BP4 candidates."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from runner import ROOT, REPO, load_registry, source_hashes, vanilla


def _task_events(task: dict[str, object], plan: dict[str, object], plan_sha: str):
    folder = ROOT / task["output"]
    summary_bytes = (folder / "summary.json").read_bytes()
    summary = json.loads(summary_bytes)
    manifest_bytes = (folder / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (sha256(manifest_bytes).hexdigest() != summary["manifest_sha256"]
            or manifest["plan_sha256"] != plan_sha
            or manifest["candidate_registry_sha256"] != plan["candidate_registry_sha256"]
            or manifest["source_files_sha256"] != plan["source_files_sha256"]
            or (manifest["code"], manifest["candidate_id"], manifest["seed"], manifest["planned_max_shots"])
            != (task["code"], task["candidate_id"], task["seed"], task["shots"])
            or summary["stop_reason"] != "fixed_shots" or summary["shots"] != task["shots"]):
        raise ValueError(f"manifest or summary mismatch: {folder}")
    digest = sha256()
    counts = {key: 0 for key in ("type_i", "type_ii", "exact_success",
                                 "stabilizer_success", "iterations", "elapsed_ns")}
    failures: list[bool] = []
    error_hashes: list[str] = []
    with (folder / "events.jsonl").open("rb") as handle:
        for shot, raw in enumerate(handle):
            digest.update(raw)
            event = json.loads(raw)
            if event["schema"] != "yao-bp4-tuning-shot-v1" or event["shot"] != shot:
                raise ValueError(f"shot index or schema mismatch: {folder}")
            record = event["outcome"]
            if sum(bool(record[key]) for key in ("type_i", "type_ii", "exact_success", "stabilizer_success")) != 1:
                raise ValueError(f"outcome partition mismatch: {folder}")
            for key in ("type_i", "type_ii", "exact_success", "stabilizer_success"):
                counts[key] += int(record[key])
            counts["iterations"] += record["iterations"][0]
            counts["elapsed_ns"] += record["elapsed_ns"]
            failures.append(bool(record["type_i"] or record["type_ii"]))
            error_hashes.append(event["error_sha256"])
    if (len(failures) != task["shots"] or counts != summary["counts"]
            or digest.hexdigest() != summary["events_sha256"]):
        raise ValueError(f"ledger hash or counts mismatch: {folder}")
    return summary, failures, error_hashes


def analyze(*, partial: bool = False) -> dict[str, object]:
    raw = (ROOT / "screen_plan.json").read_bytes()
    plan = json.loads(raw)
    plan_sha = sha256(raw).hexdigest()
    if (source_hashes() != plan["source_files_sha256"]
            or sha256((ROOT / "run_task.py").read_bytes()).hexdigest() != plan["run_task_sha256"]):
        raise ValueError("screen implementation differs from frozen plan")
    registry_path = REPO / plan["candidate_registry"]
    registry, items, registry_sha = load_registry(registry_path)
    if registry_sha != plan["candidate_registry_sha256"]:
        raise ValueError("screen decoder registry differs from frozen plan")
    completed = {}
    missing = []
    for task in plan["tasks"]:
        folder = ROOT / task["output"]
        if not (folder / "summary.json").exists():
            missing.append(task["index"])
            continue
        manifest = json.loads((folder / "manifest.json").read_text())
        if manifest["candidate"] != items[task["candidate_id"]]:
            raise ValueError(f"effective decoder spec differs from frozen registry: {folder}")
        completed[(task["code"], task["candidate_id"])] = _task_events(task, plan, plan_sha)
    if missing and not partial:
        raise RuntimeError(f"{len(missing)} screen tasks incomplete: {missing[:12]}")
    rows = []
    for code_name in ("a5", "b2"):
        base_key = (code_name, registry["baseline_id"])
        if base_key not in completed:
            continue
        _, base_failures, base_hashes = completed[base_key]
        code = vanilla._load_code(code_name)
        rng = np.random.Generator(np.random.PCG64(plan["pilots"][code_name]["seed"]))
        for shot, observed in enumerate(base_hashes):
            expected = sha256(vanilla._sample(rng, code.n, .06).tobytes()).hexdigest()
            if observed != expected:
                raise ValueError(f"sample stream mismatch: {code_name} shot {shot}")
        for candidate_id, item in items.items():
            key = (code_name, candidate_id)
            if key not in completed:
                continue
            summary, failures, hashes = completed[key]
            if hashes != base_hashes:
                raise ValueError(f"candidate did not decode the paired errors: {key}")
            rescues = sum(old and not new for old, new in zip(base_failures, failures, strict=True))
            losses = sum(new and not old for old, new in zip(base_failures, failures, strict=True))
            n = len(failures)
            rows.append({"code": code_name, "candidate_id": candidate_id,
                         "kernel": item["kernel"], "shots": n,
                         "failures": sum(failures), "type_i": summary["counts"]["type_i"],
                         "type_ii": summary["counts"]["type_ii"],
                         "rescues_vs_baseline": rescues, "losses_vs_baseline": losses,
                         "mean_iterations": summary["counts"]["iterations"] / n,
                         "mean_decode_ms": summary["counts"]["elapsed_ns"] / n / 1e6})
    result = {"schema": "yao-bp4-tuning-screen-assessment-v1", "complete": not missing,
              "completed_tasks": len(completed), "total_tasks": len(plan["tasks"]),
              "missing_task_indices": missing, "plan_sha256": plan_sha,
              "baseline_id": registry["baseline_id"], "rows": rows,
              "interpretation": "exploratory; N was selected by baseline failures on these same errors"}
    out = ROOT / "results"
    prefix = "screen" if not missing else "screen_partial"
    (out / f"{prefix}_results.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    with (out / f"{prefix}_results.csv").open("w", newline="") as handle:
        fields = ("code", "candidate_id", "kernel", "shots", "failures", "type_i", "type_ii",
                  "rescues_vs_baseline", "losses_vs_baseline", "mean_iterations", "mean_decode_ms")
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# BP4 p=.06 exploratory screen", "",
             "N is chosen by stopping the v2 baseline after six block failures.",
             "These counts rank candidates only; they are not unbiased rate estimates.",
             f"Audited {len(completed)}/{len(plan['tasks'])} tasks.", ""]
    for code_name in ("a5", "b2"):
        subset = sorted((row for row in rows if row["code"] == code_name),
                        key=lambda row: (row["failures"], row["mean_iterations"]))
        lines.extend([f"## {code_name.upper()}", "",
                      "| Candidate | Failures / N | Rescues | Losses | Mean iterations |",
                      "|---|---:|---:|---:|---:|"])
        for row in subset[:15]:
            lines.append(f"| {row['candidate_id']} | {row['failures']}/{row['shots']} | "
                         f"{row['rescues_vs_baseline']} | {row['losses_vs_baseline']} | "
                         f"{row['mean_iterations']:.2f} |")
        lines.extend(["", f"All {len(subset)} completed candidates are in `{prefix}_results.csv`.", ""])
    (out / f"{prefix}_report.md").write_text("\n".join(lines))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    result = analyze(partial=args.partial)
    print(f"audited {result['completed_tasks']}/{result['total_tasks']} tasks; complete={result['complete']}")
