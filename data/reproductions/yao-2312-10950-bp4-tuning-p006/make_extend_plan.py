"""Freeze a fresh-seed A5 iteration-cap neighborhood after the holdout signal."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEED = 620291028
SHOTS = 50_000
IDS = (
    "sp_f64_v2_d01_p006_t1000", "sp_f64_v2_d01_p006_t2000",
    "sp_f64_v2_d01_p006_t5000", "sp_f64_v2_d01_p006_t10000",
    "sp_f64_v2_d02_p006_t1000", "sp_f64_v2_d02_p006_t2000",
)


def _profile(name: str, damping: float, iterations: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": .06,
            "damping": damping, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": iterations}


def main() -> None:
    registry_path = ROOT / "decoders/extend_candidates.json"
    plan_path = ROOT / "extend_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("extension already frozen; do not overwrite")
    validate_bytes = (ROOT / "validate_plan.json").read_bytes()
    validate = json.loads(validate_bytes)
    for task in validate["tasks"]:
        if task["code"] != "a5":
            continue
        if not (ROOT / task["output"] / "summary.json").exists():
            raise ValueError("complete A5 holdout required")
    _, original, _ = load_registry(ROOT / "decoders/validate_candidates.json")
    additions = {
        "sp_f64_v2_d01_p006_t5000": _profile("sp_f64_v2_d01_p006_t5000", .1, 5000),
        "sp_f64_v2_d01_p006_t10000": _profile("sp_f64_v2_d01_p006_t10000", .1, 10000),
        "sp_f64_v2_d02_p006_t2000": _profile("sp_f64_v2_d02_p006_t2000", .2, 2000),
    }
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "sp_f64_v2_d01_p006_t2000",
                "selection_status": "post_holdout_iteration_cap_check_on_new_seed",
                "source_validate_plan_sha256": sha256(validate_bytes).hexdigest(),
                "candidates": [original[name] if name in original else additions[name]
                               for name in IDS]}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, bound, registry_sha = load_registry(registry_path)
    tasks = []
    for name in IDS:
        if name not in bound:
            raise AssertionError("candidate missing")
        tasks.append({"index": len(tasks), "code": "a5", "candidate_id": name,
                      "seed": SEED, "shots": SHOTS,
                      "output": f"results/extend/a5/{name}"})
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "extend",
            "physical_p": .06,
            "design": "post-holdout A5 iteration-cap and damping neighborhood on a new fixed paired seed",
            "source_validate_plan_sha256": sha256(validate_bytes).hexdigest(),
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_extend_task_sha256": sha256((ROOT / "run_extend_task.py").read_bytes()).hexdigest(),
            "points": {"a5": {"seed": SEED, "shots": SHOTS, "candidate_ids": list(IDS)}},
            "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} fresh-seed A5 extension tasks")


if __name__ == "__main__":
    main()
