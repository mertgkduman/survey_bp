"""Run one frozen A5 work-calibration extension task."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STUDY))

from runner import REPO, ROOT, load_registry, run_one, source_hashes  # noqa: E402


FAIR = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, default=os.environ.get("SLURM_ARRAY_TASK_ID"))
    args = parser.parse_args()
    raw = (FAIR / "pilot_extension_plan.json").read_bytes()
    plan = json.loads(raw)
    if (plan["schema"] != "yao-bp4-fairness-plan-v1"
            or plan["stage"] != "pilot_extension"
            or plan["source_files_sha256"] != source_hashes()
            or plan["run_extension_sha256"] != sha256(Path(__file__).read_bytes()).hexdigest()):
        raise ValueError("frozen pilot extension differs from source")
    registry_path = REPO / plan["candidate_registry"]
    _, items, registry_sha = load_registry(registry_path)
    if registry_sha != plan["candidate_registry_sha256"]:
        raise ValueError("candidate registry differs from plan")
    if args.index is None or not 0 <= args.index < len(plan["tasks"]):
        parser.error("valid task index required")
    task = plan["tasks"][args.index]
    if (task["index"] != args.index or task["code"] != "a5"
            or task["candidate_id"] not in items
            or task["seed"] != plan["points"]["a5"]["seed"]
            or task["shots"] != plan["points"]["a5"]["shots"]):
        raise ValueError("task differs from frozen pilot extension")
    output = (ROOT / task["output"]).resolve()
    if not output.is_relative_to((ROOT / "results/fairness_t100/pilot_extension").resolve()):
        raise ValueError("output escapes extension directory")
    run_one(code_name="a5", candidate_id=task["candidate_id"],
            registry_path=registry_path, seed=task["seed"],
            max_shots=task["shots"], target_failures=None, output=output,
            plan_sha256=sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
