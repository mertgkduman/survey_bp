"""Audit paired fairness ledgers and summarize rates, work, and rescues."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import binomtest

STUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STUDY))

from bp_registry.css import semantic_sha256  # noqa: E402
from analyze_fixed import paired_p, rate_interval  # noqa: E402
from analyze_screen import _task_events  # noqa: E402
from runner import REPO, ROOT, load_registry, source_hashes, vanilla  # noqa: E402


FAIR = Path(__file__).resolve().parent


def analyze(stage: str, *, partial: bool = False) -> dict[str, object]:
    if stage not in {"pilot", "pilot_extension", "evaluation"}:
        raise ValueError("unknown fairness stage")
    raw = (FAIR / f"{stage}_plan.json").read_bytes()
    plan = json.loads(raw)
    plan_sha = sha256(raw).hexdigest()
    runner_file = "run_extension.py" if stage == "pilot_extension" else "run_task.py"
    runner_hash_key = "run_extension_sha256" if stage == "pilot_extension" else "run_task_sha256"
    if (plan["schema"] != "yao-bp4-fairness-plan-v1"
            or plan["stage"] != stage
            or plan["source_files_sha256"] != source_hashes()
            or plan[runner_hash_key] != sha256((FAIR / runner_file).read_bytes()).hexdigest()):
        raise ValueError("frozen fairness plan differs from source")
    if stage == "evaluation":
        for key, path in (
            ("pilot_plan_sha256", FAIR / "pilot_plan.json"),
            ("pilot_results_sha256", FAIR / "pilot_results.json"),
            ("pilot_extension_plan_sha256", FAIR / "pilot_extension_plan.json"),
            ("pilot_extension_results_sha256", FAIR / "pilot_extension_results.json"),
        ):
            if plan[key] != sha256(path.read_bytes()).hexdigest():
                raise ValueError(f"evaluation source receipt changed: {key}")
        for code, source_stage in (("a5", "a5_d02_neighborhood"),
                                   ("b2", "b2_prior_confirm")):
            path = ROOT / "results" / f"{source_stage}_results.json"
            if (plan["source_selected_stage_results_sha256"][code]
                    != sha256(path.read_bytes()).hexdigest()):
                raise ValueError(f"selected {code} work-target source changed")
    registry_path = REPO / plan["candidate_registry"]
    _, items, registry_sha = load_registry(registry_path)
    if registry_sha != plan["candidate_registry_sha256"]:
        raise ValueError("candidate registry differs from plan")
    completed = {}
    missing = []
    for task in plan["tasks"]:
        folder = ROOT / task["output"]
        if not (folder / "summary.json").exists():
            missing.append(task["index"])
            continue
        manifest = json.loads((folder / "manifest.json").read_text())
        if (manifest["candidate"] != items[task["candidate_id"]]
                or manifest["code_semantic_sha256"] != semantic_sha256(vanilla._load_code(task["code"]))
                or manifest["physical_p"] != .06
                or task["seed"] != plan["points"][task["code"]]["seed"]
                or task["shots"] != plan["points"][task["code"]]["shots"]):
            raise ValueError(f"task policy, code, or point differs: {folder}")
        completed[(task["code"], task["candidate_id"])] = _task_events(task, plan, plan_sha)
    if missing and not partial:
        raise RuntimeError(f"{len(missing)} fairness tasks incomplete: {missing}")
    rows = []
    comparisons = []
    for code_name, point in plan["points"].items():
        baseline_key = (code_name, "vanilla_t100")
        if baseline_key not in completed:
            continue
        _, _, base_hashes = completed[baseline_key]
        code = vanilla._load_code(code_name)
        rng = np.random.Generator(np.random.PCG64(point["seed"]))
        for shot, observed in enumerate(base_hashes):
            expected = sha256(vanilla._sample(rng, code.n, .06).tobytes()).hexdigest()
            if observed != expected:
                raise ValueError(f"physical error stream mismatch: {code_name}, shot {shot}")
        for candidate_id in point["candidate_ids"]:
            key = (code_name, candidate_id)
            if key not in completed:
                continue
            summary, failures, hashes = completed[key]
            if hashes != base_hashes:
                raise ValueError(f"candidate errors are not paired: {key}")
            n = len(failures)
            k = sum(failures)
            lo, hi = rate_interval(k, n)
            rows.append({"code": code_name, "candidate_id": candidate_id,
                         "shots": n, "failures": k, "ler": k / n,
                         "ci90_lower": lo, "ci90_upper": hi,
                         "type_i": summary["counts"]["type_i"],
                         "type_ii": summary["counts"]["type_ii"],
                         "mean_iterations": summary["counts"]["iterations"] / n,
                         "mean_decode_ms": summary["counts"]["elapsed_ns"] / n / 1e6})
        if stage == "evaluation":
            pairs = (("vanilla_t100", f"tuned_t100_{code_name}"),
                     (f"vanilla_work_{code_name}", f"tuned_selected_{code_name}"),
                     ("vanilla_t100", f"tuned_selected_{code_name}"),
                     (f"tuned_t100_{code_name}", f"tuned_selected_{code_name}"))
            for left, right in pairs:
                if (code_name, left) not in completed or (code_name, right) not in completed:
                    continue
                old = completed[(code_name, left)][1]
                new = completed[(code_name, right)][1]
                rescues = sum(o and not n for o, n in zip(old, new, strict=True))
                losses = sum(n and not o for o, n in zip(old, new, strict=True))
                comparisons.append({"code": code_name, "left": left, "right": right,
                                    "shots": len(old), "rescues": rescues, "losses": losses,
                                    "rate_reduction": (sum(old) - sum(new)) / len(old),
                                    "paired_improvement_p": paired_p(rescues, losses),
                                    "paired_reverse_p": paired_p(losses, rescues),
                                    "paired_two_sided_p":
                                    float(binomtest(rescues, rescues + losses, .5).pvalue)
                                    if rescues + losses else 1.0})
    result = {"schema": "yao-bp4-fairness-assessment-v1", "stage": stage,
              "complete": not missing, "completed_tasks": len(completed),
              "total_tasks": len(plan["tasks"]), "missing_task_indices": missing,
              "plan_sha256": plan_sha, "rows": rows, "comparisons": comparisons,
              "interval": "exact two-sided Clopper-Pearson 90%",
              "paired_test": "exact one-sided and two-sided McNemar; selected policies fixed before this evaluation"}
    stem = stage if not missing else f"{stage}_partial"
    (FAIR / f"{stem}_results.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    with (FAIR / f"{stem}_results.csv").open("w", newline="") as handle:
        if rows:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    if comparisons:
        with (FAIR / f"{stem}_comparisons.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(comparisons)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("pilot", "pilot_extension", "evaluation"))
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    result = analyze(args.stage, partial=args.partial)
    print(f"audited {result['completed_tasks']}/{result['total_tasks']} tasks; complete={result['complete']}")
