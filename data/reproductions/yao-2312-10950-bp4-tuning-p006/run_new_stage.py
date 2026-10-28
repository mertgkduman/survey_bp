"""Run one frozen study extension stage without changing earlier task runners."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
import re

from runner import ROOT, REPO, load_registry, run_one, source_hashes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--index", type=int, default=os.environ.get("SLURM_ARRAY_TASK_ID"))
    args = parser.parse_args()
    stage = args.stage
    if not re.fullmatch(r"(?:a5|b2)_[a-z0-9_]+", stage):
        raise ValueError("invalid study extension stage")
    raw = (ROOT / f"{stage}_plan.json").read_bytes()
    plan = json.loads(raw)
    if plan.get("schema") != "yao-bp4-tuning-fixed-plan-v1" or plan.get("stage") != stage:
        raise ValueError("unsupported study extension plan")
    registry_path = REPO / plan["candidate_registry"]
    _, items, registry_sha = load_registry(registry_path)
    if (source_hashes() != plan["source_files_sha256"]
            or registry_sha != plan["candidate_registry_sha256"]
            or sha256((ROOT / "run_new_stage.py").read_bytes()).hexdigest()
            != plan["run_new_stage_sha256"]):
        raise ValueError("implementation or decoder file differs from frozen plan")
    if args.index is None or not 0 <= args.index < len(plan["tasks"]):
        parser.error("valid extension task index required")
    task = plan["tasks"][args.index]
    code = stage.split("_")[0]
    if (task["index"] != args.index or task["code"] != code
            or task["candidate_id"] not in items
            or task["seed"] != plan["points"][code]["seed"]
            or task["shots"] != plan["points"][code]["shots"]):
        raise ValueError("task differs from frozen paired design")
    output = (ROOT / task["output"]).resolve()
    if not output.is_relative_to((ROOT / "results" / stage).resolve()):
        raise ValueError("task output escapes extension directory")
    run_one(code_name=code, candidate_id=task["candidate_id"],
            registry_path=registry_path, seed=task["seed"],
            max_shots=task["shots"], target_failures=None, output=output,
            plan_sha256=sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
