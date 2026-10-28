"""Freeze a narrow B2 p0 and cap neighborhood around the long-cap leader."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEED = 620321128
SHOTS = 80_000
IDS = (
    "sp_f64_v2_d01_p014_t5000", "sp_f64_v2_d01_p015_t5000",
    "sp_f64_v2_d01_p016_t5000", "sp_f64_v2_d01_p018_t5000",
    "sp_f64_v2_d01_p020_t5000", "sp_f64_v2_d01_p015_t10000",
    "sp_f64_v2_d01_p015_t20000", "sp_f64_v2_d01_p016_t10000",
)


def _profile(name: str, p0: float, iterations: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": p0,
            "damping": .1, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": iterations}


def main() -> None:
    registry_path = ROOT / "decoders/sweet_b2_candidates.json"
    plan_path = ROOT / "sweet_b2_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("B2 neighborhood already frozen")
    tail_bytes = (ROOT / "results/tail_b2_results.json").read_bytes()
    tail = json.loads(tail_bytes)
    if not tail["complete"] or tail["completed_tasks"] != 8:
        raise ValueError("complete audited B2 tail required")
    _, originals, _ = load_registry(ROOT / "decoders/tail_b2_candidates.json")
    additions = {
        "sp_f64_v2_d01_p014_t5000": _profile("sp_f64_v2_d01_p014_t5000", .14, 5000),
        "sp_f64_v2_d01_p016_t5000": _profile("sp_f64_v2_d01_p016_t5000", .16, 5000),
        "sp_f64_v2_d01_p018_t5000": _profile("sp_f64_v2_d01_p018_t5000", .18, 5000),
        "sp_f64_v2_d01_p020_t5000": _profile("sp_f64_v2_d01_p020_t5000", .20, 5000),
        "sp_f64_v2_d01_p015_t10000": _profile("sp_f64_v2_d01_p015_t10000", .15, 10000),
        "sp_f64_v2_d01_p015_t20000": _profile("sp_f64_v2_d01_p015_t20000", .15, 20000),
        "sp_f64_v2_d01_p016_t10000": _profile("sp_f64_v2_d01_p016_t10000", .16, 10000),
    }
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "sp_f64_v2_d01_p015_t5000",
                "selection_status": "fresh_seed_local_prior_and_cap_neighborhood",
                "source_tail_b2_results_sha256": sha256(tail_bytes).hexdigest(),
                "candidates": [originals[name] if name in originals else additions[name]
                               for name in IDS]}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, _, registry_sha = load_registry(registry_path)
    tasks = [{"index": i, "code": "b2", "candidate_id": name,
              "seed": SEED, "shots": SHOTS,
              "output": f"results/sweet_b2/b2/{name}"}
             for i, name in enumerate(IDS)]
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "sweet_b2",
            "physical_p": .06,
            "design": "new fixed paired seed for p0=.14-.20 at T5000 and p0=.15/.16 cap check",
            "source_tail_b2_results_sha256": sha256(tail_bytes).hexdigest(),
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_sweet_task_sha256": sha256((ROOT / "run_sweet_task.py").read_bytes()).hexdigest(),
            "points": {"b2": {"seed": SEED, "shots": SHOTS, "candidate_ids": list(IDS)}},
            "incumbents": {"b2": "sp_f64_v2_d01_p015_t5000"}, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} B2 neighborhood tasks at N={SHOTS:,}")


if __name__ == "__main__":
    main()
