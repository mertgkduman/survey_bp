"""Direct 100-failure cross-check for a feasible rare B1 guided point."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

from completion_low_direct import source_rate
from run_point import run

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULTS = ROOT / "results"
PLAN = RESULTS / "completion-rare-direct-plan.json"
TARGET = ("b1", "bpgd_t100_r10", 0.04)


def write_plan() -> list[dict]:
    if PLAN.exists():
        raise FileExistsError(PLAN)
    code, method, p = TARGET
    rate = source_rate(code, method, p)
    output = RESULTS / "completion-rare-direct-b1-bpgd_t100_r10-p040-seed20261043"
    jobs = [{"code": code, "method": method, "p": p, "source_rate": rate,
             "seed": 20261043, "start_shot": 0, "target_failures": 100,
             "max_shots": math.ceil(400 / rate), "output": str(output.relative_to(REPO))}]
    PLAN.write_text(json.dumps({"schema": "yao-completion-rare-direct-plan-v1",
                                "target_failures": 100,
                                "max_shots_rule": "ceil(400/source_rate)",
                                "runner_sha256": sha256((ROOT / "run_point.py").read_bytes()).hexdigest(),
                                "jobs": jobs}, indent=2, sort_keys=True) + "\n")
    return jobs


def run_index(index: int) -> None:
    body = json.loads(PLAN.read_text())
    if sha256((ROOT / "run_point.py").read_bytes()).hexdigest() != body["runner_sha256"]:
        raise ValueError("runner changed after plan freeze")
    job = body["jobs"][index]
    output = REPO / job["output"]
    if (output / "summary.json").exists():
        return
    if output.exists():
        raise FileExistsError(output)
    run(code_name=job["code"], method=job["method"], p=job["p"],
        seed=job["seed"], start_shot=job["start_shot"],
        max_shots=job["max_shots"], target_failures=100, output=output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--run-index", type=int)
    args = parser.parse_args()
    if args.run_index is not None:
        run_index(args.run_index)
    elif args.plan:
        print(json.dumps({"jobs": len(write_plan())}))
    elif args.submit:
        jobs = json.loads(PLAN.read_text())["jobs"]
        command = ["sbatch", "--parsable", "-J", "yao-b1-rare-direct", "-p", "common",
                   "--account=pfisterlab", "-c", "1", "--mem=4G", "-t", "48:00:00",
                   "-o", str(RESULTS / "completion-rare-direct-%A_%a.log"),
                   f"--array=0-{len(jobs)-1}", "--wrap",
                   f"PYTHONPATH={REPO/'src'} {sys.executable} {Path(__file__).resolve()} "
                   "--run-index $SLURM_ARRAY_TASK_ID"]
        print(json.dumps({"jobs": len(jobs),
                          "slurm_job_id": subprocess.check_output(command, text=True).strip()}))
    else:
        parser.error("choose --plan, --submit, or --run-index")
