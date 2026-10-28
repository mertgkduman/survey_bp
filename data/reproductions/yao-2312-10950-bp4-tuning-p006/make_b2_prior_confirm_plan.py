"""Freeze an independent B2 prior confirmation around p0=.16."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEED = 620351128
SHOTS = 100_000
IDS = (
    "sp_f64_v2_d01_p014_t5000", "sp_f64_v2_d01_p015_t5000",
    "sp_f64_v2_d01_p016_t5000", "sp_f64_v2_d01_p017_t5000",
    "sp_f64_v2_d01_p016_t10000",
)


def main() -> None:
    registry_path = ROOT / "decoders/b2_prior_confirm_candidates.json"
    plan_path = ROOT / "b2_prior_confirm_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("B2 prior confirmation already frozen")
    joint_raw = (ROOT / "results/joint_final_results.json").read_bytes()
    joint = json.loads(joint_raw)
    if not joint["complete"]:
        raise ValueError("complete audited joint grid required")
    _, original, _ = load_registry(ROOT / "decoders/joint_final_candidates.json")
    _, sweet, _ = load_registry(ROOT / "decoders/sweet_b2_candidates.json")
    for name, item in sweet.items():
        if name in original and original[name] != item:
            raise ValueError(f"decoder identity collision: {name}")
        original[name] = item
    additions = {
        "sp_f64_v2_d01_p017_t5000": {"id": "sp_f64_v2_d01_p017_t5000",
                                          "kernel": "profile_v2", "p0": .17,
                                          "damping": .1, "check_cap": None,
                                          "product_epsilon": 1e-10, "max_iterations": 5000},
    }
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "sp_f64_v2_d01_p016_t5000",
                "selection_status": "independent_prior_confirmation_after_joint_grid",
                "source_joint_final_results_sha256": sha256(joint_raw).hexdigest(),
                "candidates": [original[name] if name in original else additions[name]
                               for name in IDS]}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, _, registry_sha = load_registry(registry_path)
    tasks = [{"index": i, "code": "b2", "candidate_id": name,
              "seed": SEED, "shots": SHOTS,
              "output": f"results/b2_prior_confirm/b2/{name}"}
             for i, name in enumerate(IDS)]
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "b2_prior_confirm",
            "physical_p": .06,
            "design": "new fixed paired seed for p0=.14-.17 at d=.1,T=5000; cap check at .16",
            "source_joint_final_results_sha256": sha256(joint_raw).hexdigest(),
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_b2_prior_task_sha256": sha256((ROOT / "run_b2_prior_task.py").read_bytes()).hexdigest(),
            "points": {"b2": {"seed": SEED, "shots": SHOTS, "candidate_ids": list(IDS)}},
            "incumbents": {"b2": "sp_f64_v2_d01_p016_t5000"}, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} B2 confirmation tasks at N={SHOTS:,}")


if __name__ == "__main__":
    main()
