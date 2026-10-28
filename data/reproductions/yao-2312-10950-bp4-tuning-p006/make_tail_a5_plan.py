"""Freeze a fresh A5 cap-tail check after repeated late BP4 rescues."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEED = 620311028
SHOTS = 50_000
IDS = ("sp_f64_v2_d01_p006_t10000", "sp_f64_v2_d01_p006_t20000",
       "sp_f64_v2_d01_p006_t50000")


def _profile(name: str, iterations: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": .06,
            "damping": .1, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": iterations}


def main() -> None:
    registry_path = ROOT / "decoders/tail_a5_candidates.json"
    plan_path = ROOT / "tail_a5_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("A5 tail check already frozen")
    followup_bytes = (ROOT / "followup_plan.json").read_bytes()
    summary_hashes = {}
    for name in ("sp_f64_v2_d01_p006_t5000", "sp_f64_v2_d01_p006_t10000"):
        path = ROOT / "results/followup/a5" / name / "summary.json"
        summary_hashes[name] = sha256(path.read_bytes()).hexdigest()
    _, originals, _ = load_registry(ROOT / "decoders/followup_candidates.json")
    items = [originals[IDS[0]], _profile(IDS[1], 20_000), _profile(IDS[2], 50_000)]
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": IDS[0], "selection_status": "late_convergence_cap_tail_new_seed",
                "source_followup_plan_sha256": sha256(followup_bytes).hexdigest(),
                "source_followup_a5_summary_sha256": summary_hashes, "candidates": items}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, _, registry_sha = load_registry(registry_path)
    tasks = [{"index": i, "code": "a5", "candidate_id": name,
              "seed": SEED, "shots": SHOTS,
              "output": f"results/tail_a5/a5/{name}"}
             for i, name in enumerate(IDS)]
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "tail_a5",
            "physical_p": .06, "design": "new fixed paired seed for T=10000,20000,50000",
            "source_followup_plan_sha256": sha256(followup_bytes).hexdigest(),
            "source_followup_a5_summary_sha256": summary_hashes,
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_tail_task_sha256": sha256((ROOT / "run_tail_task.py").read_bytes()).hexdigest(),
            "points": {"a5": {"seed": SEED, "shots": SHOTS, "candidate_ids": list(IDS)}},
            "incumbents": {"a5": IDS[0]}, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} A5 cap-tail tasks")


if __name__ == "__main__":
    main()
