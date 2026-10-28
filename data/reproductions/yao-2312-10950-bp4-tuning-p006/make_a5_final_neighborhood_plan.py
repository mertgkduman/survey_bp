"""Freeze a fresh A5 damping/cap neighborhood around the selected prior."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEED = 720371028
SHOTS = 100_000
IDS = (
    "sp_f64_v2_d01_p0005_t10000",
    "sp_f64_v2_d005_p0005_t10000",
    "sp_f64_v2_d015_p0005_t10000",
    "sp_f64_v2_d02_p0005_t10000",
    "sp_f64_v2_d01_p0005_t5000",
    "sp_f64_v2_d01_p0005_t20000",
)


def _profile(name: str, damping: float, cap: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": .005,
            "damping": damping, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": cap}


def main() -> None:
    registry_path = ROOT / "decoders/a5_final_neighborhood_candidates.json"
    plan_path = ROOT / "a5_final_neighborhood_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("A5 final neighborhood already frozen")
    source_raw = (ROOT / "a5_tiny_prior_plan.json").read_bytes()
    source_result_raw = (ROOT / "results/a5_tiny_prior_results.json").read_bytes()
    source_result = json.loads(source_result_raw)
    if not source_result["complete"] or source_result["plan_sha256"] != sha256(source_raw).hexdigest():
        raise ValueError("A5 tiny-prior audit missing or mismatched")
    _, original, _ = load_registry(ROOT / "decoders/a5_tiny_prior_candidates.json")
    additions = {
        "sp_f64_v2_d005_p0005_t10000": _profile("sp_f64_v2_d005_p0005_t10000", .05, 10000),
        "sp_f64_v2_d015_p0005_t10000": _profile("sp_f64_v2_d015_p0005_t10000", .15, 10000),
        "sp_f64_v2_d02_p0005_t10000": _profile("sp_f64_v2_d02_p0005_t10000", .2, 10000),
        "sp_f64_v2_d01_p0005_t5000": _profile("sp_f64_v2_d01_p0005_t5000", .1, 5000),
        "sp_f64_v2_d01_p0005_t20000": _profile("sp_f64_v2_d01_p0005_t20000", .1, 20000),
    }
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": IDS[0], "selection_status": "independent_a5_final_neighborhood",
                "source_a5_tiny_prior_plan_sha256": sha256(source_raw).hexdigest(),
                "source_a5_tiny_prior_results_sha256": sha256(source_result_raw).hexdigest(),
                "candidates": [original[name] if name in original else additions[name]
                               for name in IDS]}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, _, registry_sha = load_registry(registry_path)
    tasks = [{"index": i, "code": "a5", "candidate_id": name,
              "seed": SEED, "shots": SHOTS,
              "output": f"results/a5_final_neighborhood/a5/{name}"}
             for i, name in enumerate(IDS)]
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "a5_final_neighborhood",
            "physical_p": .06,
            "design": "fresh paired seed; local damping and iteration cap at selected p0=.005",
            "source_a5_tiny_prior_plan_sha256": sha256(source_raw).hexdigest(),
            "source_a5_tiny_prior_results_sha256": sha256(source_result_raw).hexdigest(),
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_new_stage_sha256": sha256((ROOT / "run_new_stage.py").read_bytes()).hexdigest(),
            "points": {"a5": {"seed": SEED, "shots": SHOTS, "candidate_ids": list(IDS)}},
            "incumbents": {"a5": IDS[0]}, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} A5 final-neighborhood tasks at N={SHOTS:,}")


if __name__ == "__main__":
    main()
