"""Longer ordinary-iid runs for selected low-rate BP/BPGD points."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

from run_point import SOURCE, run

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULTS = ROOT / "results"
PLAN = RESULTS / "completion-low-direct-plan.json"

# These are feasible on one CPU within an 18-hour wall, based on measured
# per-shot timing. More expensive rare B1/C2 targets use the IS tier.
TARGETS = (
    ("a5", "bpgd_t10", .04), ("a5", "bpgd_t10", .05), ("a5", "bpgd_t10", .07),
    ("b2", "bpgd_t10", .04), ("b2", "bpgd_t10", .05), ("b2", "bpgd_t10", .07),
    ("b2", "bpgd_t10", .08), ("b2", "bpgd_t10", .09), ("b2", "bpgd_t10", .10),
    ("b1", "bpgd_t1", .05), ("b1", "bpgd_t10", .05),
    ("b1", "bpgd_t100_r5", .04), ("b1", "bpgd_t100_r10", .05),
    ("c2", "bpgd_t10", .05),
)


def source_rate(code: str, method: str, p: float) -> float:
    key = f"{p:.5f}"
    rates = {float(body["curves"][method][key]) for body in SOURCE["figures"].values()
             if body["code"] == code and key in body["curves"].get(method, {})}
    if not rates:
        raise ValueError(f"missing source rate: {code} {method} {p}")
    # Figures 3 and 4 disagree on B1 T=10; the lower value gives the
    # more conservative shot ceiling while both targets remain reported.
    return min(rates)


def write_plan() -> list[dict]:
    if PLAN.exists():
        raise FileExistsError(PLAN)
    jobs = []
    for code, method, p in TARGETS:
        rate = source_rate(code, method, p)
        output = RESULTS / f"completion-low-{code}-{method}-p{int(round(p*1000)):03d}-seed20261037"
        jobs.append({"code":code,"method":method,"p":p,"source_rate":rate,
                     "seed":20261037,"target_failures":100,
                     "max_shots":math.ceil(300/rate),
                     "output":str(output.relative_to(REPO))})
    PLAN.write_text(json.dumps({"schema":"yao-completion-low-direct-plan-v1",
                                "jobs":jobs,"target_failures":100,
                                "max_shots_rule":"ceil(300/source_rate)",
                                "runner_sha256":sha256((ROOT/"run_point.py").read_bytes()).hexdigest()},
                               indent=2,sort_keys=True)+"\n")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--run-index", type=int)
    args = parser.parse_args()
    if args.run_index is not None:
        run_index(args.run_index)
    elif args.plan:
        print(json.dumps({"jobs":len(write_plan())}))
    elif args.submit:
        jobs=json.loads(PLAN.read_text())["jobs"]
        command=["sbatch","--parsable","-J","yao-bp-bpgd-low","-p","common",
                 "--account=pfisterlab","-c","1","--mem=4G","-t","18:00:00",
                 "-o",str(RESULTS/"completion-low-%A_%a.log"),
                 f"--array=0-{len(jobs)-1}%14", "--wrap",
                 f"{sys.executable} {Path(__file__).resolve()} --run-index $SLURM_ARRAY_TASK_ID"]
        print(json.dumps({"jobs":len(jobs),"slurm_job_id":subprocess.check_output(command,text=True).strip()}))
    else:
        parser.error("choose --plan, --submit, or --run-index")
