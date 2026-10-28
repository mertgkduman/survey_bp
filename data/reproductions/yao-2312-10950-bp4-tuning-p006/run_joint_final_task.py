"""Run one frozen final damping/prior interaction check on a paired seed."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os

from runner import ROOT, REPO, load_registry, run_one, source_hashes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, default=os.environ.get("SLURM_ARRAY_TASK_ID"))
    args = parser.parse_args()
    raw = (ROOT / "joint_final_plan.json").read_bytes()
    plan = json.loads(raw)
    if plan.get("schema") != "yao-bp4-tuning-fixed-plan-v1" or plan.get("stage") != "joint_final":
        raise ValueError("unsupported joint final plan")
    registry_path = REPO / plan["candidate_registry"]
    _, items, registry_sha = load_registry(registry_path)
    if (source_hashes() != plan["source_files_sha256"]
            or registry_sha != plan["candidate_registry_sha256"]
            or sha256((ROOT / "run_joint_final_task.py").read_bytes()).hexdigest()
            != plan["run_joint_final_task_sha256"]):
        raise ValueError("implementation or decoder file differs from frozen plan")
    if args.index is None or not 0 <= args.index < len(plan["tasks"]):
        parser.error("valid final-grid task index required")
    task = plan["tasks"][args.index]
    code = task["code"]
    if (task["index"] != args.index or code not in {"a5", "b2"}
            or task["candidate_id"] not in items
            or task["seed"] != plan["points"][code]["seed"]
            or task["shots"] != plan["points"][code]["shots"]):
        raise ValueError("task differs from frozen paired design")
    output = (ROOT / task["output"]).resolve()
    if not output.is_relative_to((ROOT / "results/joint_final").resolve()):
        raise ValueError("task output escapes final-grid directory")
    run_one(code_name=code, candidate_id=task["candidate_id"],
            registry_path=registry_path, seed=task["seed"],
            max_shots=task["shots"], target_failures=None, output=output,
            plan_sha256=sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
