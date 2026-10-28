"""Freeze final damping/prior neighborhoods at the selected cap per code."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEEDS = {"a5": 620331028, "b2": 620331128}
SHOTS = {"a5": 60_000, "b2": 60_000}
A5 = (
    "sp_f64_v2_d01_p006_t10000", "sp_f64_v2_d02_p006_t10000",
    "sp_f64_v2_d03_p006_t10000", "sp_f64_v2_d01_p0045_t10000",
    "sp_f64_v2_d01_p0075_t10000",
)
B2 = (
    "sp_f64_v2_d01_p015_t5000", "sp_f64_v2_d005_p015_t5000",
    "sp_f64_v2_d015_p015_t5000", "sp_f64_v2_d02_p015_t5000",
    "sp_f64_v2_d01_p014_t5000", "sp_f64_v2_d01_p016_t5000",
    "sp_f64_v2_d01_p018_t5000",
)


def _profile(name: str, damping: float, p0: float, iterations: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": p0,
            "damping": damping, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": iterations}


def main() -> None:
    registry_path = ROOT / "decoders/joint_final_candidates.json"
    plan_path = ROOT / "joint_final_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("final interaction check already frozen")
    sources = {}
    for stage in ("tail_a5", "sweet_b2"):
        raw = (ROOT / "results" / f"{stage}_results.json").read_bytes()
        data = json.loads(raw)
        if not data["complete"]:
            raise ValueError(f"{stage} audit incomplete")
        sources[stage] = sha256(raw).hexdigest()
    original = {}
    for stage in ("tail_a5", "sweet_b2"):
        _, items, _ = load_registry(ROOT / "decoders" / f"{stage}_candidates.json")
        for name, item in items.items():
            if name in original and original[name] != item:
                raise ValueError(f"decoder identity collision: {name}")
            original[name] = item
    additions = {
        "sp_f64_v2_d02_p006_t10000": _profile("sp_f64_v2_d02_p006_t10000", .2, .06, 10000),
        "sp_f64_v2_d03_p006_t10000": _profile("sp_f64_v2_d03_p006_t10000", .3, .06, 10000),
        "sp_f64_v2_d01_p0045_t10000": _profile("sp_f64_v2_d01_p0045_t10000", .1, .045, 10000),
        "sp_f64_v2_d01_p0075_t10000": _profile("sp_f64_v2_d01_p0075_t10000", .1, .075, 10000),
        "sp_f64_v2_d005_p015_t5000": _profile("sp_f64_v2_d005_p015_t5000", .05, .15, 5000),
        "sp_f64_v2_d015_p015_t5000": _profile("sp_f64_v2_d015_p015_t5000", .15, .15, 5000),
        "sp_f64_v2_d02_p015_t5000": _profile("sp_f64_v2_d02_p015_t5000", .2, .15, 5000),
    }
    ids = list(dict.fromkeys(A5 + B2))
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": A5[0],
                "selection_status": "independent_joint_damping_prior_check_at_selected_caps",
                "source_audited_results_sha256": sources,
                "candidates": [original[name] if name in original else additions[name]
                               for name in ids]}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, bound, registry_sha = load_registry(registry_path)
    tasks = []
    for code, selected in (("a5", A5), ("b2", B2)):
        for candidate_id in selected:
            if candidate_id not in bound:
                raise AssertionError("candidate missing")
            tasks.append({"index": len(tasks), "code": code, "candidate_id": candidate_id,
                          "seed": SEEDS[code], "shots": SHOTS[code],
                          "output": f"results/joint_final/{code}/{candidate_id}"})
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "joint_final",
            "physical_p": .06,
            "design": "fresh fixed paired seed; final damping and prior changes at selected caps",
            "source_audited_results_sha256": sources,
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_joint_final_task_sha256": sha256((ROOT / "run_joint_final_task.py").read_bytes()).hexdigest(),
            "points": {code: {"seed": SEEDS[code], "shots": SHOTS[code],
                              "candidate_ids": list(selected)}
                       for code, selected in (("a5", A5), ("b2", B2))},
            "incumbents": {"a5": A5[0], "b2": B2[0]}, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} final interaction tasks")


if __name__ == "__main__":
    main()
