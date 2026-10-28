"""Run one frozen post-holdout BP4 neighborhood task on a new sample seed."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

from runner import ROOT, REPO, load_registry, run_one, source_hashes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--index", type=int, default=os.environ.get("SLURM_ARRAY_TASK_ID"))
    args = parser.parse_args()
    path = args.plan.resolve()
    if path != ROOT / "extend_plan.json":
        raise ValueError("only this study's frozen extension plan is supported")
    raw = path.read_bytes()
    plan = json.loads(raw)
    if plan.get("schema") != "yao-bp4-tuning-fixed-plan-v1" or plan.get("stage") != "extend":
        raise ValueError("unsupported extension plan")
    registry_path = REPO / plan["candidate_registry"]
    _, items, registry_sha = load_registry(registry_path)
    if (source_hashes() != plan["source_files_sha256"]
            or registry_sha != plan["candidate_registry_sha256"]
            or sha256((ROOT / "run_extend_task.py").read_bytes()).hexdigest()
            != plan["run_extend_task_sha256"]):
        raise ValueError("implementation or decoder file differs from frozen plan")
    if args.index is None or not 0 <= args.index < len(plan["tasks"]):
        parser.error("valid extension task index required")
    task = plan["tasks"][args.index]
    if (task["index"] != args.index or task["candidate_id"] not in items
            or task["seed"] != plan["points"][task["code"]]["seed"]
            or task["shots"] != plan["points"][task["code"]]["shots"]):
        raise ValueError("task differs from frozen paired design")
    output = (ROOT / task["output"]).resolve()
    if not output.is_relative_to((ROOT / "results/extend").resolve()):
        raise ValueError("task output escapes extension directory")
    run_one(code_name=task["code"], candidate_id=task["candidate_id"],
            registry_path=registry_path, seed=task["seed"],
            max_shots=task["shots"], target_failures=None, output=output,
            plan_sha256=sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
