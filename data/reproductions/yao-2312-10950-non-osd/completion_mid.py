"""Direct 100-failure follow-up for moderate-rate BP/BPGD points.

This tier covers published rates in [0.003,0.01), where ordinary iid
sampling is feasible but the first bounded campaign had too few failures.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

from run_point import run

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULTS = ROOT / "results"
PLAN = RESULTS / "completion-mid-plan.json"


def write_plan() -> list[dict]:
    if PLAN.exists():
        raise FileExistsError(PLAN)
    chosen = {}
    with (RESULTS / "comparison.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["curve"] == "bp_si_external":
                continue
            method = "bpgd_t100" if row["curve"] == "bpgd_t100_r882" else row["curve"]
            code, p, rate = row["code"], float(row["p"]), float(row["published_rate"])
            key = (code, method, p)
            if key in chosen or not .003 <= rate < .01:
                continue
            if row["assessment"] not in {"pending", "pilot_only", "low_count_unresolved", "low_count_tension", "importance_preliminary"}:
                continue
            output = RESULTS / f"completion-mid-{code}-{method}-p{int(round(p*1000)):03d}-seed20261036"
            chosen[key] = {"code": code, "method": method, "p": p, "seed": 20261036,
                           "max_shots": math.ceil(300/rate), "target_failures": 100,
                           "output": str(output.relative_to(REPO)), "source_rate": rate}
    jobs = sorted(chosen.values(), key=lambda item:(item["code"],item["method"],item["p"]))
    PLAN.write_text(json.dumps({"schema":"yao-completion-mid-plan-v1", "jobs":jobs,
                                "runner_sha256":sha256((ROOT/"run_point.py").read_bytes()).hexdigest(),
                                "max_shots_rule":"ceil(300/source_rate)",
                                "target_failures":100},indent=2,sort_keys=True)+"\n")
    return jobs


def run_index(index: int) -> None:
    body = json.loads(PLAN.read_text())
    if sha256((ROOT/"run_point.py").read_bytes()).hexdigest() != body["runner_sha256"]:
        raise ValueError("runner changed after plan freeze")
    job = body["jobs"][index]
    output = REPO / job["output"]
    if (output/"summary.json").exists():
        return
    if output.exists():
        raise FileExistsError(output)
    run(code_name=job["code"],method=job["method"],p=job["p"],seed=job["seed"],
        start_shot=0,max_shots=job["max_shots"],target_failures=100,output=output)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",action="store_true")
    parser.add_argument("--submit",action="store_true")
    parser.add_argument("--run-index",type=int)
    args=parser.parse_args()
    if args.run_index is not None:
        run_index(args.run_index)
    elif args.plan:
        print(json.dumps({"jobs":len(write_plan())}))
    elif args.submit:
        jobs=json.loads(PLAN.read_text())["jobs"]
        if not jobs:
            print(json.dumps({"jobs":0,"slurm_job_id":None}))
        else:
            command=["sbatch","--parsable","-J","yao-bp-bpgd-mid","-p","common",
                     "--account=pfisterlab","-c","1","--mem=4G","-t","08:00:00",
                     "-o",str(RESULTS/"completion-mid-%A_%a.log"),
                     f"--array=0-{len(jobs)-1}%9", "--wrap",
                     f"{sys.executable} {Path(__file__).resolve()} --run-index $SLURM_ARRAY_TASK_ID"]
            print(json.dumps({"jobs":len(jobs),"slurm_job_id":subprocess.check_output(command,text=True).strip()}))
    else:
        parser.error("choose --plan, --submit, or --run-index")
