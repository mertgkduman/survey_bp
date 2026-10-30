"""Parallel fixed-shot iid shards for the rare B1 T=1, p=0.04 point."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from run_point import run

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULTS = ROOT / "results"
PLAN = RESULTS / "completion-rare-shards-plan.json"
SHARDS = 16
SHOTS_PER_SHARD = 500_000


def write_plan() -> list[dict]:
    if PLAN.exists():
        raise FileExistsError(PLAN)
    jobs = []
    for index in range(SHARDS):
        output = RESULTS / f"completion-rare-shard-b1-bpgd_t1-p040-seed20261044-s{index+1:02d}"
        jobs.append({"code": "b1", "method": "bpgd_t1", "p": 0.04,
                     "seed": 20261044, "start_shot": index * SHOTS_PER_SHARD,
                     "max_shots": SHOTS_PER_SHARD, "target_failures": None,
                     "output": str(output.relative_to(REPO))})
    body = {"schema": "yao-completion-rare-shards-plan-v1", "jobs": jobs,
            "total_fixed_shots": SHARDS * SHOTS_PER_SHARD,
            "source_rate": 2.9e-5,
            "expected_failures_at_source_rate": SHARDS * SHOTS_PER_SHARD * 2.9e-5,
            "runner_sha256": sha256((ROOT / "run_point.py").read_bytes()).hexdigest()}
    PLAN.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
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
        max_shots=job["max_shots"], target_failures=None, output=output)


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
        command = ["sbatch", "--parsable", "-J", "yao-b1-rare-iid", "-p", "common",
                   "--account=pfisterlab", "-c", "1", "--mem=4G", "-t", "12:00:00",
                   "-o", str(RESULTS / "completion-rare-shard-%A_%a.log"),
                   f"--array=0-{len(jobs)-1}%16", "--wrap",
                   f"PYTHONPATH={REPO/'src'} {sys.executable} {Path(__file__).resolve()} "
                   "--run-index $SLURM_ARRAY_TASK_ID"]
        print(json.dumps({"jobs": len(jobs),
                          "slurm_job_id": subprocess.check_output(command, text=True).strip()}))
    else:
        parser.error("choose --plan, --submit, or --run-index")
