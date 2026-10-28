"""Freeze an independent holdout and nearby BP4 settings after refinement."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEEDS = {"a5": 620281028, "b2": 620281128}
SHOTS = {"a5": 50_000, "b2": 50_000}
A5 = (
    "sp_f64_v2_d0_p006_t100", "sp_f64_v2_d01_p006_t1000",
    "sp_f64_v2_d01_p006_t300", "sp_f64_v2_d01_p006_t2000",
    "sp_f64_v2_d02_p006_t1000", "sp_f64_v2_d03_p0075_t100",
    "sp_f64_v2_d03_p0075_t1000", "sp_f64_v2_d03_p006_t100",
    "sp_f64_v2_d05_p006_t100", "sp_q8_s4_edge_d02",
)
B2 = (
    "sp_f64_v2_d0_p006_t100", "sp_f64_v2_d01_p015_t100",
    "sp_f64_v2_d01_p015_t300", "sp_f64_v2_d01_p018_t100",
    "sp_f64_v2_d01_p024_t100", "sp_f64_v2_d01_p030_t100",
    "sp_f64_v2_d01_p006_t300", "sp_f64_v2_d01_p006_t1000",
    "sp_f64_v2_d01_p012_t100", "sp_f64_v2_d02_p012_t100",
)


def _profile(name: str, damping: float, p0: float, iterations: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": p0,
            "damping": damping, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": iterations}


def main() -> None:
    registry_path = ROOT / "decoders/validate_candidates.json"
    plan_path = ROOT / "validate_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("validation already frozen; do not overwrite")
    refine_bytes = (ROOT / "results/refine_results.json").read_bytes()
    refine = json.loads(refine_bytes)
    if not refine["complete"] or refine["completed_tasks"] != 50:
        raise ValueError("complete audited refinement required")
    _, original, _ = load_registry(ROOT / "decoders/refine_candidates.json")
    additions = {
        "sp_f64_v2_d01_p006_t2000": _profile("sp_f64_v2_d01_p006_t2000", .1, .06, 2000),
        "sp_f64_v2_d02_p006_t1000": _profile("sp_f64_v2_d02_p006_t1000", .2, .06, 1000),
        "sp_f64_v2_d03_p0075_t1000": _profile("sp_f64_v2_d03_p0075_t1000", .3, .075, 1000),
        "sp_f64_v2_d01_p015_t300": _profile("sp_f64_v2_d01_p015_t300", .1, .15, 300),
        "sp_f64_v2_d01_p018_t100": _profile("sp_f64_v2_d01_p018_t100", .1, .18, 100),
        "sp_f64_v2_d01_p024_t100": _profile("sp_f64_v2_d01_p024_t100", .1, .24, 100),
        "sp_f64_v2_d01_p030_t100": _profile("sp_f64_v2_d01_p030_t100", .1, .30, 100),
        "sp_f64_v2_d01_p006_t1000": _profile("sp_f64_v2_d01_p006_t1000", .1, .06, 1000),
    }
    ids = list(dict.fromkeys(A5 + B2))
    items = [original[name] if name in original else additions[name] for name in ids]
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "sp_f64_v2_d0_p006_t100",
                "selection_status": "independent_holdout_and_finite_neighborhood",
                "source_refine_results_sha256": sha256(refine_bytes).hexdigest(),
                "candidates": items}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, bound, registry_sha = load_registry(registry_path)
    tasks = []
    for code, selected in (("a5", A5), ("b2", B2)):
        for candidate_id in selected:
            if candidate_id not in bound:
                raise AssertionError("candidate missing")
            tasks.append({"index": len(tasks), "code": code, "candidate_id": candidate_id,
                          "seed": SEEDS[code], "shots": SHOTS[code],
                          "output": f"results/validate/{code}/{candidate_id}"})
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "validate",
            "physical_p": .06, "design": "independent fixed paired N after refinement; finite neighboring policies",
            "source_refine_results_sha256": sha256(refine_bytes).hexdigest(),
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_fixed_task_sha256": sha256((ROOT / "run_fixed_task.py").read_bytes()).hexdigest(),
            "points": {code: {"seed": SEEDS[code], "shots": SHOTS[code],
                              "candidate_ids": list(selected)}
                       for code, selected in (("a5", A5), ("b2", B2))},
            "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} holdout tasks; 10 settings on each code")


if __name__ == "__main__":
    main()
