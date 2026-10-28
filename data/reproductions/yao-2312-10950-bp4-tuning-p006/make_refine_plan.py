"""Freeze an independent, code-specific refinement neighborhood after screen."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEEDS = {"a5": 620271028, "b2": 620271128}
SHOTS = {"a5": 12_000, "b2": 15_000}
A5_EXISTING = (
    "sp_f64_v2_d0_p006_t100",
    "sp_f64_v2_d005_p006_t100", "sp_f64_v2_d01_p006_t100",
    "sp_f64_v2_d02_p006_t100", "sp_f64_v2_d03_p006_t100",
    "sp_f64_v2_d05_p006_t100",
    "sp_f64_v2_d01_p003_t100", "sp_f64_v2_d01_p0045_t100",
    "sp_f64_v2_d01_p0075_t100", "sp_f64_v2_d01_p009_t100",
    "sp_f64_v2_d01_p006_t300", "sp_f64_v2_d01_p006_t1000",
    "sp_q8_s4_edge_d02", "sp_q8_s8_edge_d02", "sp_policy_f64_d02",
)
B2_EXISTING = (
    "sp_f64_v2_d0_p006_t100", "sp_f64_v2_d01_p006_t100",
    "sp_f64_v2_d02_p006_t100", "sp_f64_v2_d03_p006_t100",
    "sp_f64_v2_d05_p006_t100",
    "sp_f64_v2_d01_p003_t100", "sp_f64_v2_d01_p009_t100",
    "sp_f64_v2_d01_p012_t100", "sp_f64_v2_d01_p006_eps1e8",
    "sp_f64_v2_d01_p006_cap20", "sp_f64_v2_d01_p006_t300",
    "sp_q8_s4_edge_d0", "sp_q8_s4_edge_d02", "sp_q8_s8_edge_d02",
    "sp_policy_f64_d02",
)


def _profile(name: str, *, damping: float, p0: float) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": p0,
            "damping": damping, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": 100}


def main() -> None:
    registry_path = ROOT / "decoders/refine_candidates.json"
    plan_path = ROOT / "refine_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("refinement already frozen; do not overwrite")
    screen_bytes = (ROOT / "results/screen_results.json").read_bytes()
    screen = json.loads(screen_bytes)
    if not screen["complete"] or screen["completed_tasks"] != 94:
        raise ValueError("screen audit must be complete before refinement")
    _, original, _ = load_registry(ROOT / "decoders/screen_candidates.json")
    selection = {"a5": list(A5_EXISTING), "b2": list(B2_EXISTING)}
    additions = {}
    for d, dname in ((.2, "02"), (.3, "03")):
        for p0, pname in ((.03, "003"), (.045, "0045"), (.075, "0075"),
                          (.09, "009"), (.12, "012")):
            name = f"sp_f64_v2_d{dname}_p{pname}_t100"
            additions[name] = _profile(name, damping=d, p0=p0)
            if p0 in (.03, .045, .075, .09):
                selection["a5"].append(name)
            if p0 in (.03, .09, .12):
                selection["b2"].append(name)
    for p0, pname in ((.02, "002"), (.15, "015")):
        name = f"sp_f64_v2_d01_p{pname}_t100"
        additions[name] = _profile(name, damping=.1, p0=p0)
        selection["a5"].append(name)
        selection["b2"].append(name)
    name = "sp_f64_v2_d04_p006_t100"
    additions[name] = _profile(name, damping=.4, p0=.06)
    selection["a5"].append(name)
    selection["b2"].append(name)
    ordered_ids = list(dict.fromkeys(selection["a5"] + selection["b2"]))
    items = [original[name] if name in original else additions[name] for name in ordered_ids]
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "sp_f64_v2_d0_p006_t100",
                "selection_status": "independent_fixed_refinement",
                "source_screen_results_sha256": sha256(screen_bytes).hexdigest(),
                "candidates": items}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, bound, registry_sha = load_registry(registry_path)
    tasks = []
    for code in ("a5", "b2"):
        for candidate_id in selection[code]:
            if candidate_id not in bound:
                raise AssertionError("refinement candidate missing")
            tasks.append({"index": len(tasks), "code": code, "candidate_id": candidate_id,
                          "seed": SEEDS[code], "shots": SHOTS[code],
                          "output": f"results/refine/{code}/{candidate_id}"})
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "refine",
            "physical_p": .06, "design": "fixed paired N on fresh seed after six-failure screen",
            "source_screen_results_sha256": sha256(screen_bytes).hexdigest(),
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_fixed_task_sha256": sha256((ROOT / "run_fixed_task.py").read_bytes()).hexdigest(),
            "points": {code: {"seed": SEEDS[code], "shots": SHOTS[code],
                              "candidate_ids": selection[code]} for code in ("a5", "b2")},
            "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} fixed-shot refinement tasks: "
          f"A5 {len(selection['a5'])}, B2 {len(selection['b2'])}")


if __name__ == "__main__":
    main()
