"""Freeze an A5 lower-prior scan after p0=.03 beat p0=.045."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, REPO, load_registry, source_hashes


SEED = 620361028
SHOTS = 100_000
IDS = (
    "sp_f64_v2_d01_p0005_t10000", "sp_f64_v2_d01_p001_t10000",
    "sp_f64_v2_d01_p0015_t10000", "sp_f64_v2_d01_p002_t10000",
    "sp_f64_v2_d01_p0025_t10000", "sp_f64_v2_d01_p003_t10000",
    "sp_f64_v2_d01_p004_t10000",
)


def _profile(name: str, p0: float) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": p0,
            "damping": .1, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": 10000}


def main() -> None:
    registry_path = ROOT / "decoders/a5_low_prior_candidates.json"
    plan_path = ROOT / "a5_low_prior_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("A5 lower-prior scan already frozen")
    source_raw = (ROOT / "a5_prior_plan.json").read_bytes()
    receipts = {}
    for name in ("sp_f64_v2_d01_p003_t10000", "sp_f64_v2_d01_p0045_t10000"):
        path = ROOT / "results/a5_prior/a5" / name / "summary.json"
        receipts[name] = sha256(path.read_bytes()).hexdigest()
    _, original, _ = load_registry(ROOT / "decoders/a5_prior_candidates.json")
    additions = {
        "sp_f64_v2_d01_p0005_t10000": _profile("sp_f64_v2_d01_p0005_t10000", .005),
        "sp_f64_v2_d01_p001_t10000": _profile("sp_f64_v2_d01_p001_t10000", .01),
        "sp_f64_v2_d01_p0015_t10000": _profile("sp_f64_v2_d01_p0015_t10000", .015),
        "sp_f64_v2_d01_p002_t10000": _profile("sp_f64_v2_d01_p002_t10000", .02),
        "sp_f64_v2_d01_p0025_t10000": _profile("sp_f64_v2_d01_p0025_t10000", .025),
    }
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "sp_f64_v2_d01_p003_t10000",
                "selection_status": "independent_lower_prior_scan_after_resolved_signal",
                "source_a5_prior_plan_sha256": sha256(source_raw).hexdigest(),
                "source_a5_prior_summary_sha256": receipts,
                "candidates": [original[name] if name in original else additions[name]
                               for name in IDS]}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, _, registry_sha = load_registry(registry_path)
    tasks = [{"index": i, "code": "a5", "candidate_id": name,
              "seed": SEED, "shots": SHOTS,
              "output": f"results/a5_low_prior/a5/{name}"}
             for i, name in enumerate(IDS)]
    plan = {"schema": "yao-bp4-tuning-fixed-plan-v1", "stage": "a5_low_prior",
            "physical_p": .06,
            "design": "new fixed paired seed for p0=.005-.04 at d=.1,T=10000",
            "source_a5_prior_plan_sha256": sha256(source_raw).hexdigest(),
            "source_a5_prior_summary_sha256": receipts,
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_new_stage_sha256": sha256((ROOT / "run_new_stage.py").read_bytes()).hexdigest(),
            "points": {"a5": {"seed": SEED, "shots": SHOTS, "candidate_ids": list(IDS)}},
            "incumbents": {"a5": "sp_f64_v2_d01_p003_t10000"}, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} A5 lower-prior tasks at N={SHOTS:,}")


if __name__ == "__main__":
    main()
