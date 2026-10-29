"""Bracket the A5 vanilla work cap beyond the initial pilot grid."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STUDY))

from runner import REPO, ROOT, load_registry, source_hashes  # noqa: E402


FAIR = Path(__file__).resolve().parent
CAPS = (100, 3000, 3600, 4200)


def main() -> None:
    registry_path = FAIR / "pilot_extension_candidates.json"
    plan_path = FAIR / "pilot_extension_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("pilot extension already frozen")
    pilot_raw = (FAIR / "pilot_plan.json").read_bytes()
    pilot = json.loads(pilot_raw)
    _, old, _ = load_registry(FAIR / "pilot_candidates.json")
    receipts = {}
    for name in pilot["points"]["a5"]["candidate_ids"]:
        path = ROOT / f"results/fairness_t100/pilot/a5/{name}/summary.json"
        receipts[name] = sha256(path.read_bytes()).hexdigest()
    candidates = [old["vanilla_t100"]]
    for cap in CAPS[1:]:
        candidates.append({"id": f"vanilla_t{cap}", "kernel": "profile_v2",
                           "p0": .06, "damping": 0.0,
                           "check_cap": None, "product_epsilon": 1e-10,
                           "max_iterations": cap})
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "vanilla_t100", "design": "A5 pilot extension; rates not assessed",
                "source_pilot_plan_sha256": sha256(pilot_raw).hexdigest(),
                "source_a5_summary_sha256": receipts,
                "candidates": candidates}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, _, registry_sha = load_registry(registry_path)
    seed = pilot["points"]["a5"]["seed"]
    shots = pilot["points"]["a5"]["shots"]
    names = [c["id"] for c in candidates]
    tasks = [{"index": i, "code": "a5", "candidate_id": name,
              "seed": seed, "shots": shots,
              "output": f"results/fairness_t100/pilot_extension/a5/{name}"}
             for i, name in enumerate(names)]
    plan = {"schema": "yao-bp4-fairness-plan-v1", "stage": "pilot_extension",
            "physical_p": .06,
            "purpose": "bracket A5 selected mean work above initial cap 2400",
            "source_pilot_plan_sha256": sha256(pilot_raw).hexdigest(),
            "source_a5_summary_sha256": receipts,
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_files_sha256": source_hashes(),
            "run_extension_sha256": sha256((FAIR / "run_extension.py").read_bytes()).hexdigest(),
            "points": {"a5": {"seed": seed, "shots": shots, "candidate_ids": names}},
            "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"froze {len(tasks)} A5 pilot-extension tasks")


if __name__ == "__main__":
    main()
