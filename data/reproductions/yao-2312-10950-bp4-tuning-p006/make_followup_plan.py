"""Freeze final fresh-seed neighborhoods from completed leading holdout arms."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEEDS = {"a5": 620301028, "b2": 620301128}
SHOTS = {"a5": 50_000, "b2": 50_000}
A5 = (
    "sp_f64_v2_d01_p006_t5000", "sp_f64_v2_d01_p006_t10000",
    "sp_f64_v2_d02_p006_t5000", "sp_f64_v2_d03_p006_t5000",
    "sp_f64_v2_d01_p0075_t5000", "sp_f64_v2_d02_p0075_t5000",
)
B2 = (
    "sp_f64_v2_d01_p006_t1000", "sp_f64_v2_d01_p006_t2000",
    "sp_f64_v2_d01_p006_t5000", "sp_f64_v2_d01_p015_t300",
    "sp_f64_v2_d01_p015_t1000", "sp_f64_v2_d01_p015_t2000",
    "sp_f64_v2_d01_p012_t1000", "sp_f64_v2_d02_p006_t1000",
)


def _profile(name: str, damping: float, p0: float, iterations: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": p0,
            "damping": damping, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": iterations}


def main() -> None:
    registry_path = ROOT / "decoders/followup_candidates.json"
    plan_path = ROOT / "followup_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("followup already frozen; do not overwrite")
    validation_plan = (ROOT / "validate_plan.json").read_bytes()
    extension_results = (ROOT / "results/extend_results.json").read_bytes()
    if not json.loads(extension_results)["complete"]:
        raise ValueError("complete audited A5 extension required")
    leading_b2 = ("sp_f64_v2_d01_p006_t1000", "sp_f64_v2_d01_p015_t300")
    receipts = {}
    for name in leading_b2:
        path = ROOT / "results/validate/b2" / name / "summary.json"
        receipts[name] = sha256(path.read_bytes()).hexdigest()
    _, from_validate, _ = load_registry(ROOT / "decoders/validate_candidates.json")
    _, from_extend, _ = load_registry(ROOT / "decoders/extend_candidates.json")
    original = dict(from_validate)
    for name, item in from_extend.items():
        if name in original and original[name] != item:
            raise ValueError(f"decoder identity collision: {name}")
        original[name] = item
    additions = {
        "sp_f64_v2_d02_p006_t5000": _profile("sp_f64_v2_d02_p006_t5000", .2, .06, 5000),
        "sp_f64_v2_d03_p006_t5000": _profile("sp_f64_v2_d03_p006_t5000", .3, .06, 5000),
        "sp_f64_v2_d01_p0075_t5000": _profile("sp_f64_v2_d01_p0075_t5000", .1, .075, 5000),
        "sp_f64_v2_d02_p0075_t5000": _profile("sp_f64_v2_d02_p0075_t5000", .2, .075, 5000),
        "sp_f64_v2_d01_p006_t2000": _profile("sp_f64_v2_d01_p006_t2000", .1, .06, 2000),
        "sp_f64_v2_d01_p006_t5000": _profile("sp_f64_v2_d01_p006_t5000", .1, .06, 5000),
        "sp_f64_v2_d01_p015_t1000": _profile("sp_f64_v2_d01_p015_t1000", .1, .15, 1000),
        "sp_f64_v2_d01_p015_t2000": _profile("sp_f64_v2_d01_p015_t2000", .1, .15, 2000),
        "sp_f64_v2_d01_p012_t1000": _profile("sp_f64_v2_d01_p012_t1000", .1, .12, 1000),
        "sp_f64_v2_d02_p006_t1000": _profile("sp_f64_v2_d02_p006_t1000", .2, .06, 1000),
    }
    ids = list(dict.fromkeys(A5 + B2))
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "sp_f64_v2_d01_p006_t5000",
                "selection_status": "independent_followup_to_resolved_iteration_cap_signal",
                "source_validate_plan_sha256": sha256(validation_plan).hexdigest(),
                "source_a5_extension_results_sha256": sha256(extension_results).hexdigest(),
                "source_b2_leader_summary_sha256": receipts,
                "candidates": [original[name] if name in original else additions[name]
                               for name in ids]}
    # The generic study loader requires a registry baseline present. The A5
    # incumbent is used for that field; B2's incumbent is recorded per code.
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, bound, registry_sha = load_registry(registry_path)
    tasks = []
    for code, selected in (("a5", A5), ("b2", B2)):
        for candidate_id in selected:
            if candidate_id not in bound:
                raise AssertionError("candidate missing")
            tasks.append({"index": len(tasks), "code": code, "candidate_id": candidate_id,
                          "seed": SEEDS[code], "shots": SHOTS[code],
                          "output": f"results/followup/{code}/{candidate_id}"})
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "followup",
            "physical_p": .06,
            "design": "fresh fixed paired seed after holdout/extension; finite damping-prior-cap neighborhood",
            "source_validate_plan_sha256": sha256(validation_plan).hexdigest(),
            "source_a5_extension_results_sha256": sha256(extension_results).hexdigest(),
            "source_b2_leader_summary_sha256": receipts,
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_followup_task_sha256": sha256((ROOT / "run_followup_task.py").read_bytes()).hexdigest(),
            "points": {code: {"seed": SEEDS[code], "shots": SHOTS[code],
                              "candidate_ids": list(selected)}
                       for code, selected in (("a5", A5), ("b2", B2))},
            "incumbents": {"a5": "sp_f64_v2_d01_p006_t5000",
                           "b2": "sp_f64_v2_d01_p006_t1000"},
            "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} fresh-seed followup tasks: A5 {len(A5)}, B2 {len(B2)}")


if __name__ == "__main__":
    main()
