"""Run one frozen paired BP4 fairness-control task."""

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
    parser.add_argument("--stage", choices=("pilot", "evaluation"), required=True)
    parser.add_argument("--index", type=int, default=os.environ.get("SLURM_ARRAY_TASK_ID"))
    args = parser.parse_args()
    raw = (FAIR / f"{args.stage}_plan.json").read_bytes()
    plan = json.loads(raw)
    if (plan["schema"] != "yao-bp4-fairness-plan-v1"
            or plan["stage"] != args.stage
            or plan["source_files_sha256"] != source_hashes()
            or plan["run_task_sha256"] != sha256(Path(__file__).read_bytes()).hexdigest()):
        raise ValueError("frozen fairness plan or implementation mismatch")
    registry_path = REPO / plan["candidate_registry"]
    _, candidates, registry_sha = load_registry(registry_path)
    if registry_sha != plan["candidate_registry_sha256"]:
        raise ValueError("candidate registry differs from frozen plan")
    if args.index is None or not 0 <= args.index < len(plan["tasks"]):
        parser.error("valid task index required")
    task = plan["tasks"][args.index]
    if (task["index"] != args.index or task["candidate_id"] not in candidates
            or task["seed"] != plan["points"][task["code"]]["seed"]
            or task["shots"] != plan["points"][task["code"]]["shots"]
            or task["candidate_id"] not in plan["points"][task["code"]]["candidate_ids"]):
        raise ValueError("task differs from frozen paired design")
    output = (ROOT / task["output"]).resolve()
    if not output.is_relative_to((ROOT / "results/fairness_t100" / args.stage).resolve()):
        raise ValueError("output escapes stage directory")
    run_one(code_name=task["code"], candidate_id=task["candidate_id"],
            registry_path=registry_path, seed=task["seed"],
            max_shots=task["shots"], target_failures=None, output=output,
            plan_sha256=sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
