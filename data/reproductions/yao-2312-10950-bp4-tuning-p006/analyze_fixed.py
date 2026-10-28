"""Audit paired fixed-shot tuning runs and report exact 90% rate intervals."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json

import numpy as np
from scipy.stats import beta, binomtest

from analyze_screen import _task_events
from runner import ROOT, REPO, load_registry, source_hashes, vanilla


def rate_interval(failures: int, shots: int) -> tuple[float, float]:
    """Two-sided 90% Clopper-Pearson interval for a fixed shot count."""
    if shots <= 0 or not 0 <= failures <= shots:
        raise ValueError("invalid binomial count")
    lower = 0.0 if failures == 0 else float(beta.ppf(.05, failures, shots - failures + 1))
    upper = 1.0 if failures == shots else float(beta.ppf(.95, failures + 1, shots - failures))
    return lower, upper


def paired_p(rescues: int, losses: int) -> float:
    """One-sided exact McNemar probability for an improvement under equal discordance."""
    if rescues < 0 or losses < 0:
        raise ValueError("negative discordant count")
    if rescues + losses == 0:
        return 1.0
    return float(binomtest(rescues, rescues + losses, .5, alternative="greater").pvalue)


def analyze(stage: str, *, partial: bool = False) -> dict[str, object]:
    if stage not in {"refine", "validate", "extend", "followup", "tail_a5", "tail_b2", "sweet_b2", "joint_final", "a5_prior", "b2_prior_confirm", "a5_low_prior", "a5_tiny_prior", "a5_final_neighborhood", "a5_d02_neighborhood"}:
        raise ValueError("unknown fixed-shot stage")
    raw = (ROOT / f"{stage}_plan.json").read_bytes()
    plan = json.loads(raw)
    plan_sha = sha256(raw).hexdigest()
    task_runner = {"extend": "run_extend_task.py", "followup": "run_followup_task.py",
                   "tail_a5": "run_tail_task.py", "tail_b2": "run_tail_task.py",
                   "sweet_b2": "run_sweet_task.py", "joint_final": "run_joint_final_task.py",
                   "a5_prior": "run_a5_prior_task.py",
                   "b2_prior_confirm": "run_b2_prior_task.py",
                   "a5_low_prior": "run_new_stage.py", "a5_tiny_prior": "run_new_stage.py",
                   "a5_final_neighborhood": "run_new_stage.py",
                   "a5_d02_neighborhood": "run_new_stage.py"}.get(
        stage, "run_fixed_task.py")
    task_runner_hash_key = f"{task_runner.removesuffix('.py')}_sha256"
    if (plan["schema"] != "yao-bp4-tuning-fixed-plan-v1" or plan["stage"] != stage
            or source_hashes() != plan["source_files_sha256"]
            or sha256((ROOT / task_runner).read_bytes()).hexdigest()
            != plan[task_runner_hash_key]):
        raise ValueError("fixed-shot implementation differs from frozen plan")
    registry_path = REPO / plan["candidate_registry"]
    registry, items, registry_sha = load_registry(registry_path)
    if registry_sha != plan["candidate_registry_sha256"]:
        raise ValueError("decoder registry differs from frozen plan")
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
        raise RuntimeError(f"{len(missing)} fixed-shot tasks incomplete: {missing[:12]}")
    rows = []
    baseline_by_code = {code: registry["baseline_id"] for code in ("a5", "b2")}
    baseline_by_code.update(plan.get("incumbents", {}))
    for code_name in ("a5", "b2"):
        base_key = (code_name, baseline_by_code[code_name])
        if base_key not in completed:
            continue
        _, base_failures, base_hashes = completed[base_key]
        code = vanilla._load_code(code_name)
        rng = np.random.Generator(np.random.PCG64(plan["points"][code_name]["seed"]))
        for shot, observed in enumerate(base_hashes):
            expected = sha256(vanilla._sample(rng, code.n, .06).tobytes()).hexdigest()
            if observed != expected:
                raise ValueError(f"sample stream mismatch: {code_name} shot {shot}")
        for candidate_id in plan["points"][code_name]["candidate_ids"]:
            key = (code_name, candidate_id)
            if key not in completed:
                continue
            summary, failures, hashes = completed[key]
            if hashes != base_hashes:
                raise ValueError(f"candidate did not decode the paired errors: {key}")
            rescues = sum(old and not new for old, new in zip(base_failures, failures, strict=True))
            losses = sum(new and not old for old, new in zip(base_failures, failures, strict=True))
            n = len(failures)
            k = sum(failures)
            lo, hi = rate_interval(k, n)
            rows.append({"code": code_name, "candidate_id": candidate_id,
                         "kernel": items[candidate_id]["kernel"], "shots": n,
                         "failures": k, "ler": k / n, "ci90_lower": lo,
                         "ci90_upper": hi, "type_i": summary["counts"]["type_i"],
                         "type_ii": summary["counts"]["type_ii"],
                         "rescues_vs_baseline": rescues, "losses_vs_baseline": losses,
                         "paired_improvement_p_vs_baseline": paired_p(rescues, losses),
                         "mean_iterations": summary["counts"]["iterations"] / n,
                         "mean_decode_ms": summary["counts"]["elapsed_ns"] / n / 1e6})
    result = {"schema": "yao-bp4-tuning-fixed-assessment-v1", "stage": stage,
              "complete": not missing, "completed_tasks": len(completed),
              "total_tasks": len(plan["tasks"]), "missing_task_indices": missing,
              "plan_sha256": plan_sha, "baseline_id": registry["baseline_id"],
              "confidence": .90, "interval_method": "two-sided exact Clopper-Pearson",
              "paired_test": "one-sided exact McNemar, unadjusted exploratory p-value",
              "rows": rows}
    if stage in {"followup", "tail_a5", "tail_b2", "sweet_b2", "joint_final", "a5_prior", "b2_prior_confirm", "a5_low_prior", "a5_tiny_prior", "a5_final_neighborhood", "a5_d02_neighborhood"}:
        result["baseline_by_code"] = baseline_by_code
    prefix = stage if not missing else f"{stage}_partial"
    out = ROOT / "results"
    (out / f"{prefix}_results.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    with (out / f"{prefix}_results.csv").open("w", newline="") as handle:
        if rows:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    paired_description = ("Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;"
                          if stage not in {"refine", "validate"} else
                          "Paired p-values are one-sided exact McNemar tests versus the undamped v2 baseline;")
    pvalue_note = ("P-values are unadjusted after policy search; treat them as exploratory."
                   if stage not in {"refine", "validate"} else
                   "refinement p-values are exploratory because many settings were screened.")
    lines = [f"# BP4 p=.06 {stage} results", "", f"Audited {len(completed)}/{len(plan['tasks'])} tasks.",
             "All rates use fixed N and exact two-sided 90% binomial intervals.",
             paired_description,
             pvalue_note, ""]
    for code_name in ("a5", "b2"):
        subset = sorted((r for r in rows if r["code"] == code_name),
                        key=lambda r: (r["failures"], r["mean_iterations"]))
        if not subset:
            continue
        lines.extend([f"## {code_name.upper()}", ""])
        if stage not in {"refine", "validate"}:
            lines.extend([f"Paired reference: `{baseline_by_code[code_name]}`.", ""])
        lines.extend(["| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |",
                      "|---|---:|---:|---:|---:|---:|"])
        for r in subset:
            lines.append(f"| {r['candidate_id']} | {r['failures']}/{r['shots']} | "
                         f"{r['ler']:.5g} [{r['ci90_lower']:.5g}, {r['ci90_upper']:.5g}] | "
                         f"{r['rescues_vs_baseline']}/{r['losses_vs_baseline']} | "
                         f"{r['paired_improvement_p_vs_baseline']:.4g} | {r['mean_iterations']:.2f} |")
        lines.append("")
    (out / f"{prefix}_report.md").write_text("\n".join(lines))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("refine", "validate", "extend", "followup", "tail_a5", "tail_b2", "sweet_b2", "joint_final", "a5_prior", "b2_prior_confirm", "a5_low_prior", "a5_tiny_prior", "a5_final_neighborhood", "a5_d02_neighborhood"))
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    result = analyze(args.stage, partial=args.partial)
    print(f"audited {result['completed_tasks']}/{result['total_tasks']} tasks; complete={result['complete']}")
