"""Freeze pilot caps for matching untuned mean iterations to tuned BP4."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STUDY))

from bp_registry.css import semantic_sha256  # noqa: E402
from runner import REPO, ROOT, load_registry, source_hashes, vanilla  # noqa: E402


FAIR = Path(__file__).resolve().parent
CAPS = (100, 300, 600, 1000, 1600, 2400)
SEEDS = {"a5": 2026102901, "b2": 2026102902}
SHOTS = 20_000


def _profile(name: str, cap: int) -> dict[str, object]:
    return {"id": name, "kernel": "profile_v2", "p0": .06,
            "damping": 0.0, "check_cap": None,
            "product_epsilon": 1e-10, "max_iterations": cap}


def main() -> None:
    registry_path = FAIR / "pilot_candidates.json"
    plan_path = FAIR / "pilot_plan.json"
    if registry_path.exists() or plan_path.exists():
        raise FileExistsError("fairness pilot already frozen")
    selected = {}
    selected_hashes = {}
    for code in ("a5", "b2"):
        path = ROOT / "decoders" / f"{code}_tuned.json"
        raw = path.read_bytes()
        registry, items, _ = load_registry(path)
        if registry["code"] != code or registry["code_semantic_sha256"] != semantic_sha256(vanilla._load_code(code)):
            raise ValueError("selected decoder code identity differs")
        candidate = dict(items[registry["selected_candidate_id"]])
        candidate["id"] = f"tuned_selected_{code}"
        selected[code] = candidate
        selected_hashes[code] = sha256(raw).hexdigest()
    candidates = [_profile(f"vanilla_t{cap}", cap) for cap in CAPS]
    candidates.extend(selected[code] for code in ("a5", "b2"))
    registry = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "baseline_id": "vanilla_t100",
                "design": "independent mean-iteration calibration pilot; no rate claims",
                "source_selected_sha256": selected_hashes,
                "candidates": candidates}
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    _, items, registry_sha = load_registry(registry_path)
    points = {code: {"seed": SEEDS[code], "shots": SHOTS,
                     "candidate_ids": [f"vanilla_t{cap}" for cap in CAPS]
                     + [f"tuned_selected_{code}"]}
              for code in ("a5", "b2")}
    tasks = []
    for code, point in points.items():
        for name in point["candidate_ids"]:
            if name not in items:
                raise AssertionError("candidate missing")
            tasks.append({"index": len(tasks), "code": code, "candidate_id": name,
                          "seed": point["seed"], "shots": point["shots"],
                          "output": f"results/fairness_t100/pilot/{code}/{name}"})
    plan = {"schema": "yao-bp4-fairness-plan-v1", "stage": "pilot",
            "physical_p": .06,
            "purpose": "choose vanilla cap nearest tuned selected mean iterations on paired pilot",
            "candidate_registry": str(registry_path.relative_to(REPO)),
            "candidate_registry_sha256": registry_sha,
            "source_selected_sha256": selected_hashes,
            "source_files_sha256": source_hashes(),
            "run_task_sha256": sha256((FAIR / "run_task.py").read_bytes()).hexdigest(),
            "points": points, "tasks": tasks}
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"froze {len(tasks)} paired pilot tasks")


if __name__ == "__main__":
    main()
