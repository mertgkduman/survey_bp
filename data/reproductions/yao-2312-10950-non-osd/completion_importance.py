"""Plan and dispatch initial rare-event BP/BPGD mixture samples.

Each planned point gets a fixed 10,000-shot pilot. A later assessment
checks the weighted failure effective sample size and can request
additional disjoint shards; no pilot is promoted merely because it ran.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PLAN = ROOT / "results" / "completion-importance-plan.json"
RESULTS = ROOT / "results"


def _proposal(code: str, p: float) -> float:
    if code == "b2":
        return round(p + (0.03 if p <= 0.07 else 0.02), 5)
    return round(p + (0.02 if p <= 0.05 else 0.01), 5)


def planned_jobs() -> list[dict]:
    chosen = {}
    with (RESULTS / "comparison.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["curve"] == "bp_si_external":
                continue
            method = "bpgd_t100" if row["curve"] == "bpgd_t100_r882" else row["curve"]
            code, p = row["code"], float(row["p"])
            key = (code, method, p)
            if key in chosen:
                continue
            if row["assessment"] not in {"pending", "pilot_only", "low_count_unresolved", "low_count_tension"}:
                continue
            rate = float(row["published_rate"])
            if rate >= 0.01:
                continue
            # A separate long direct run was submitted for this exact point.
            if code in {"a5", "b2"} and method == "bpgd_t10" and p == 0.06:
                continue
            q = _proposal(code, p)
            output = RESULTS / f"completion-importance-{code}-{method}-p{int(round(p*1000)):03d}-q{int(round(q*1000)):03d}-seed20261035"
            chosen[key] = {"code": code, "method": method, "p": p,
                           "proposal_p": q, "defensive_fraction": 0.1,
                           "seed": 20261035, "start_shot": 0, "shots": 10000,
                           "output": str(output.relative_to(REPO)),
                           "source_rate": rate}
    return sorted(chosen.values(), key=lambda item: (item["code"], item["method"], item["p"]))


def write_plan() -> list[dict]:
    if PLAN.exists():
        raise FileExistsError(f"refusing to overwrite {PLAN}")
    jobs = planned_jobs()
    body = {"schema": "yao-completion-importance-plan-v1", "fixed_shots_per_point": 10000,
            "source_rate_ceiling": 0.01, "defensive_fraction": 0.1,
            "interpretation": "pilot only; subsequent ESS-gated shards needed for final interval",
            "runner_sha256": sha256((ROOT / "run_importance.py").read_bytes()).hexdigest(),
            "jobs": jobs}
    PLAN.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    return jobs


def run_index(index: int) -> None:
    plan = json.loads(PLAN.read_text())
    if sha256((ROOT / "run_importance.py").read_bytes()).hexdigest() != plan["runner_sha256"]:
        raise ValueError("importance runner changed after plan freeze")
    job = plan["jobs"][index]
    output = REPO / job["output"]
    if (output / "summary.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"partial task requires review: {output}")
    environment = dict(os.environ, PYTHONPATH=str(REPO / "src"))
    command = [sys.executable, str(ROOT / "run_importance.py"), "--code", job["code"],
               "--method", job["method"], "--p", str(job["p"]),
               "--proposal-p", str(job["proposal_p"]),
               "--defensive-fraction", str(job["defensive_fraction"]),
               "--seed", str(job["seed"]), "--start-shot", str(job["start_shot"]),
               "--shots", str(job["shots"]), "--output", str(output)]
    subprocess.run(command, env=environment, check=True)


def submit(jobs: list[dict], max_parallel: int) -> str:
    if not jobs:
        return "no_jobs"
    command = ["sbatch", "--parsable", "-J", "yao-bp-bpgd-rare", "-p", "common",
               "--account=pfisterlab", "-c", "1", "--mem=4G", "-t", "12:00:00",
               "-o", str(RESULTS / "completion-importance-%A_%a.log"),
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
