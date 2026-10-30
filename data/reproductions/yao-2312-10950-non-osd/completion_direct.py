"""Plan and dispatch bounded direct-Monte-Carlo BP/BPGD source points.

The plan is generated from the verified comparison table. Each task is an
ordinary 100-failure run with a source-rate-based ceiling; no old evidence
is overwritten. Only points with published rate at least 0.01 enter this
direct tier. Rarer targets use a separately labelled rare-event protocol.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PLAN = ROOT / "results" / "completion-direct-plan.json"
RESULTS = ROOT / "results"


def planned_jobs() -> list[dict]:
    chosen = {}
    with (RESULTS / "comparison.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["curve"] == "bp_si_external":
                continue
            method = "bpgd_t100" if row["curve"] == "bpgd_t100_r882" else row["curve"]
            key = (row["code"], method, row["p"])
            if key in chosen:
                continue
            if row["assessment"] not in {"pending", "pilot_only", "low_count_unresolved", "low_count_tension"}:
                continue
            rate = float(row["published_rate"])
            if rate < 0.01:
                continue
            code, _, p = key
            output = RESULTS / f"completion-direct-{code}-{method}-p{int(round(float(p)*1000)):03d}-seed20261034"
            chosen[key] = {"code": code, "method": method, "p": float(p),
                           "seed": 20261034, "max_shots": math.ceil(300 / rate),
                           "target_failures": 100,
                           "output": str(output.relative_to(REPO)),
                           "source_rate": rate}
    return sorted(chosen.values(), key=lambda item: (item["code"], item["method"], item["p"]))


def write_plan() -> list[dict]:
    if PLAN.exists():
        raise FileExistsError(f"refusing to overwrite {PLAN}")
    jobs = planned_jobs()
    body = {"schema": "yao-completion-direct-plan-v1", "target_failures": 100,
            "source_rate_floor": 0.01, "max_shots_rule": "ceil(300/source_rate)",
            "method": "ordinary iid code-capacity Monte Carlo, same decoder/source p",
            "runner_sha256": sha256((ROOT / "run_point.py").read_bytes()).hexdigest(),
            "jobs": jobs}
    PLAN.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    return jobs


def run_index(index: int) -> None:
    plan = json.loads(PLAN.read_text())
    if sha256((ROOT / "run_point.py").read_bytes()).hexdigest() != plan["runner_sha256"]:
        raise ValueError("runner changed after plan freeze")
    job = plan["jobs"][index]
    output = REPO / job["output"]
    if (output / "summary.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"partial task requires review: {output}")
    environment = dict(os.environ, PYTHONPATH=str(REPO / "src"))
    command = [sys.executable, str(ROOT / "run_point.py"), "--code", job["code"],
               "--method", job["method"], "--p", str(job["p"]), "--seed", str(job["seed"]),
               "--max-shots", str(job["max_shots"]), "--target-failures", "100",
               "--output", str(output)]
    subprocess.run(command, env=environment, check=True)


def submit(jobs: list[dict], max_parallel: int) -> str:
    if not jobs:
        return "no_jobs"
    command = ["sbatch", "--parsable", "-J", "yao-bp-bpgd-direct", "-p", "common",
               "--account=pfisterlab", "-c", "1", "--mem=4G", "-t", "08:00:00",
               "-o", str(RESULTS / "completion-direct-%A_%a.log"),
               f"--array=0-{len(jobs)-1}%{max_parallel}",
               "--wrap", f"{sys.executable} {Path(__file__).resolve()} --run-index $SLURM_ARRAY_TASK_ID"]
    return subprocess.check_output(command, text=True).strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--run-index", type=int)
    parser.add_argument("--max-parallel", type=int, default=16)
    args = parser.parse_args()
    if args.run_index is not None:
        run_index(args.run_index)
    elif args.plan:
        print(json.dumps({"jobs": len(write_plan())}))
    elif args.submit:
        if not 1 <= args.max_parallel <= 32:
            raise ValueError("parallel task count must be in [1,32]")
        jobs = json.loads(PLAN.read_text())["jobs"]
        print(json.dumps({"jobs": len(jobs), "slurm_job_id": submit(jobs, args.max_parallel)}))
    else:
        parser.error("choose --plan, --submit, or --run-index")
