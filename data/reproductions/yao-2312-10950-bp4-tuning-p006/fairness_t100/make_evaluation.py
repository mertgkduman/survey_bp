"""Freeze fresh paired equal-cap and approximately equal-work BP4 arms."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STUDY))

from runner import REPO, ROOT, load_registry, source_hashes  # noqa: E402


FAIR = Path(__file__).resolve().parent
SEEDS = {"a5": 2026102911, "b2": 2026102912}
SHOTS = 100_000


def _audited_stage(stage: str) -> tuple[dict[str, object], dict[str, object], str, str]:
    plan_raw = (FAIR / f"{stage}_plan.json").read_bytes()
    result_raw = (FAIR / f"{stage}_results.json").read_bytes()
    plan, result = json.loads(plan_raw), json.loads(result_raw)
    if (not result["complete"] or result["stage"] != stage
            or result["plan_sha256"] != sha256(plan_raw).hexdigest()
            or result["completed_tasks"] != result["total_tasks"]):
        raise ValueError(f"complete audited {stage} required")
    return plan, result, sha256(plan_raw).hexdigest(), sha256(result_raw).hexdigest()


def main() -> None:
    registry_path = FAIR / "evaluation_candidates.json"
    plan_path = FAIR / "evaluation_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("fairness evaluation already frozen")
    pilot_plan, pilot, pilot_plan_sha, pilot_sha = _audited_stage("pilot")
    ext_plan, extension, ext_plan_sha, ext_sha = _audited_stage("pilot_extension")
    _, pilot_items, _ = load_registry(FAIR / "pilot_candidates.json")
    _, extension_items, _ = load_registry(FAIR / "pilot_extension_candidates.json")
    pilot_rows = {(r["code"], r["candidate_id"]): r for r in pilot["rows"]}
    extension_rows = {(r["code"], r["candidate_id"]): r for r in extension["rows"]}
    candidates = [pilot_items["vanilla_t100"]]
    work_caps = {}
    pilot_work = {}
    points = {}
    selected_results_hashes = {}
    for code in ("a5", "b2"):
        tuned_id = f"tuned_selected_{code}"
        selected_path = ROOT / "decoders" / f"{code}_tuned.json"
        selected_registry, selected_items, _ = load_registry(selected_path)
        selected_id = selected_registry["selected_candidate_id"]
        selected_item = dict(selected_items[selected_id], id=tuned_id)
        if selected_item != pilot_items[tuned_id]:
            raise ValueError("pilot tuned policy differs from selected decoder")
        source_stage = "a5_d02_neighborhood" if code == "a5" else "b2_prior_confirm"
        source_raw = (ROOT / "results" / f"{source_stage}_results.json").read_bytes()
        source = json.loads(source_raw)
        if not source["complete"]:
            raise ValueError("selected 100,000-shot source result is incomplete")
        selected_row = next(r for r in source["rows"] if r["code"] == code and r["candidate_id"] == selected_id)
        if selected_row["shots"] != 100_000:
            raise ValueError("selected work target lacks 100,000 shots")
        selected_results_hashes[code] = sha256(source_raw).hexdigest()
        target = selected_row["mean_iterations"]
        cap_rows = [(int(name.removeprefix("vanilla_t")), pilot_rows[(code, name)]["mean_iterations"],
                     pilot_items[name])
                    for name in pilot_plan["points"][code]["candidate_ids"]
                    if name.startswith("vanilla_t")]
        if code == "a5":
            cap_rows.extend((int(name.removeprefix("vanilla_t")), extension_rows[(code, name)]["mean_iterations"],
                             extension_items[name])
                            for name in ext_plan["points"][code]["candidate_ids"]
                            if name.startswith("vanilla_t") and name != "vanilla_t100")
        cap, observed, work_item = min(cap_rows, key=lambda x: (abs(x[1] - target), x[0]))
        mismatch = abs(observed - target) / target
        if cap <= 100 or mismatch > .10:
            raise ValueError(f"{code} pilot cap grid does not match tuned mean work within 10%")
        work_caps[code] = cap
        pilot_work[code] = {"tuned_selected_100k_mean_iterations": target,
                            "tuned_selected_pilot_mean_iterations": pilot_rows[(code, tuned_id)]["mean_iterations"],
                            "vanilla_selected_cap": cap,
                            "vanilla_mean_iterations_at_cap": observed,
                            "relative_mismatch": mismatch}
        work = dict(work_item, id=f"vanilla_work_{code}")
        tuned = dict(pilot_items[tuned_id])
        tuned_t100 = dict(tuned, id=f"tuned_t100_{code}", max_iterations=100)
        candidates.extend((work, tuned_t100, tuned))
        points[code] = {"seed": SEEDS[code], "shots": SHOTS,
                        "candidate_ids": ["vanilla_t100", f"tuned_t100_{code}",
                                          f"vanilla_work_{code}", tuned_id]}
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "vanilla_t100",
                "design": "fresh paired equal-T100 and pilot-matched mean-iteration controls",
                "pilot_plan_sha256": pilot_plan_sha, "pilot_results_sha256": pilot_sha,
                "pilot_extension_plan_sha256": ext_plan_sha,
                "pilot_extension_results_sha256": ext_sha,
                "source_selected_stage_results_sha256": selected_results_hashes,
                "candidates": candidates}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, items, registry_sha = load_registry(registry_path)
    tasks = []
    for code, point in points.items():
        for name in point["candidate_ids"]:
            if name not in items:
                raise AssertionError("candidate missing")
            tasks.append({"index": len(tasks), "code": code, "candidate_id": name,
                          "seed": point["seed"], "shots": point["shots"],
                          "output": f"results/fairness_t100/evaluation/{code}/{name}"})
    plan = {"schema": "yao-bp4-fairness-plan-v1", "stage": "evaluation",
            "physical_p": .06,
            "purpose": "fixed-shot paired equal-cap and approximately equal-mean-iteration comparison",
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_task_sha256": sha256((FAIR / "run_task.py").read_bytes()).hexdigest(),
            "pilot_plan_sha256": pilot_plan_sha, "pilot_results_sha256": pilot_sha,
            "pilot_extension_plan_sha256": ext_plan_sha,
            "pilot_extension_results_sha256": ext_sha,
            "source_selected_stage_results_sha256": selected_results_hashes,
            "pilot_work_selection": pilot_work,
            "work_caps": work_caps,
            "points": points, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"froze {len(tasks)} evaluation tasks; vanilla work caps {work_caps}")


if __name__ == "__main__":
    main()
