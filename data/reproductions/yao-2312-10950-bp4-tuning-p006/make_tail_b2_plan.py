"""Freeze a fresh B2 prior/cap-tail comparison after the followup."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEED = 620311128
SHOTS = 50_000
IDS = (
    "sp_f64_v2_d01_p012_t1000", "sp_f64_v2_d01_p012_t2000",
    "sp_f64_v2_d01_p012_t5000", "sp_f64_v2_d01_p012_t10000",
    "sp_f64_v2_d01_p006_t5000", "sp_f64_v2_d01_p006_t10000",
    "sp_f64_v2_d01_p015_t2000", "sp_f64_v2_d01_p015_t5000",
)


def _profile(name: str, p0: float, iterations: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": p0,
            "damping": .1, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": iterations}


def main() -> None:
    registry_path = ROOT / "decoders/tail_b2_candidates.json"
    plan_path = ROOT / "tail_b2_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("B2 tail comparison already frozen")
    followup_bytes = (ROOT / "results/followup_results.json").read_bytes()
    followup = json.loads(followup_bytes)
    if not followup["complete"] or followup["completed_tasks"] != 14:
        raise ValueError("complete audited followup required")
    _, originals, _ = load_registry(ROOT / "decoders/followup_candidates.json")
    additions = {
        "sp_f64_v2_d01_p012_t2000": _profile("sp_f64_v2_d01_p012_t2000", .12, 2000),
        "sp_f64_v2_d01_p012_t5000": _profile("sp_f64_v2_d01_p012_t5000", .12, 5000),
        "sp_f64_v2_d01_p012_t10000": _profile("sp_f64_v2_d01_p012_t10000", .12, 10000),
        "sp_f64_v2_d01_p006_t10000": _profile("sp_f64_v2_d01_p006_t10000", .06, 10000),
        "sp_f64_v2_d01_p015_t5000": _profile("sp_f64_v2_d01_p015_t5000", .15, 5000),
    }
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": IDS[0], "selection_status": "prior_and_cap_tail_new_seed",
                "source_followup_results_sha256": sha256(followup_bytes).hexdigest(),
                "candidates": [originals[name] if name in originals else additions[name]
                               for name in IDS]}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, _, registry_sha = load_registry(registry_path)
    tasks = [{"index": i, "code": "b2", "candidate_id": name,
              "seed": SEED, "shots": SHOTS,
              "output": f"results/tail_b2/b2/{name}"}
             for i, name in enumerate(IDS)]
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "tail_b2",
            "physical_p": .06, "design": "new fixed paired seed for p0=.06,.12,.15 and T=1000..10000",
            "source_followup_results_sha256": sha256(followup_bytes).hexdigest(),
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_tail_task_sha256": sha256((ROOT / "run_tail_task.py").read_bytes()).hexdigest(),
            "points": {"b2": {"seed": SEED, "shots": SHOTS, "candidate_ids": list(IDS)}},
            "incumbents": {"b2": IDS[0]}, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} B2 prior/cap-tail tasks")


if __name__ == "__main__":
    main()
