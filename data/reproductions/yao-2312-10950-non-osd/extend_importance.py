"""Freeze disjoint rare-event shards from completed pilot ESS measurements."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

from importance_assess import verified_importance_runs
from run_importance import run

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULTS = ROOT / "results"


def _plan_path(stage: str) -> Path:
    if not stage.startswith("stage") or not stage[5:].isdigit() or not 1 <= int(stage[5:]) <= 99:
        raise ValueError("stage must be stage1 through stage99")
    return RESULTS / f"completion-importance-extension-{stage}.json"


def _direct_keys() -> set[tuple[str, str, str]]:
    keys = set()
    for name in ("completion-direct-plan.json", "completion-mid-plan.json",
                 "completion-low-direct-plan.json"):
        for item in json.loads((RESULTS / name).read_text())["jobs"]:
            keys.add((item["code"], item["method"], f'{item["p"]:.5f}'))
    keys.update({("a5", "bpgd_t10", "0.06000"), ("b2", "bpgd_t10", "0.06000")})
    return keys


def write_plan(stage: str) -> list[dict]:
    path = _plan_path(stage)
    stage_number = int(stage[5:])
    if path.exists():
        raise FileExistsError(path)
    pilot_jobs = json.loads((RESULTS / "completion-importance-plan.json").read_text())["jobs"]
    runs = verified_importance_runs()
    direct_keys = _direct_keys()
    prior_jobs_by_key = {}
    for prior_stage in range(1, stage_number):
        prior_path = _plan_path(f"stage{prior_stage}")
        if prior_path.exists():
            for prior in json.loads(prior_path.read_text())["jobs"]:
                prior_key = (prior["code"], prior["method"], f'{prior["p"]:.5f}')
                prior_jobs_by_key.setdefault(prior_key, []).append(prior)
    jobs = []
    skipped = []
    for item in pilot_jobs:
        code, method, p = item["code"], item["method"], item["p"]
        key = (code, method, f"{p:.5f}")
        if key in direct_keys:
            skipped.append({"key": key, "reason": "ordinary_iid_run_planned"})
            continue
        estimate = runs.get(key)
        if estimate is None:
            skipped.append({"key": key, "reason": "initial_pilot_incomplete"})
            continue
        prior_jobs = prior_jobs_by_key.get(key, [])
        if any(not (REPO / job["output"] / "summary.json").exists() for job in prior_jobs):
            skipped.append({"key": key, "reason": "prior_extension_stage_incomplete"})
            continue
        if estimate["analysis_stage"] >= stage_number:
            skipped.append({"key": key, "reason": "stage_already_exists"})
            continue
        ess = estimate["failure_ess"]
        halfwidth = math.inf if estimate["rate"] == 0 else (
            estimate["ci95_high"] - estimate["ci95_low"]) / (2*estimate["rate"])
        if ess >= 100 and halfwidth <= .25:
            skipped.append({"key": key, "reason": "precision_gate_met"})
            continue
        needed = math.ceil(120*estimate["shots"]/ess - estimate["shots"]) if ess > 0 else 500000
        additional = min(500000, max(50000, needed))
        shard_count = math.ceil(additional/50000)
        for shard in range(shard_count):
            count = min(50000, additional-50000*shard)
            start = estimate["next_start_shot"] + 50000*shard
            output = RESULTS / (f"completion-importance-{code}-{method}-p{int(round(p*1000)):03d}"
                                f"-q{int(round(item['proposal_p']*1000)):03d}-seed{item['seed']}"
                                f"-{stage}-s{shard+1:02d}")
            jobs.append({"code": code, "method": method, "p": p,
                         "proposal_p": item["proposal_p"],
                         "defensive_fraction": item["defensive_fraction"],
                         "seed": item["seed"], "start_shot": start, "shots": count,
                         "output": str(output.relative_to(REPO)),
                         "pilot_ess": ess, "pilot_rate": estimate["rate"]})
    body = {"schema": "yao-importance-extension-plan-v1", "stage": stage,
            "precision_target_failure_ess": 100,
            "planning_ess_target": 120,
            "max_additional_shots_per_point_this_stage": 500000,
            "max_shots_per_shard": 50000,
            "runner_sha256": sha256((ROOT/"run_importance.py").read_bytes()).hexdigest(),
            "jobs": jobs, "skipped": skipped}
    path.write_text(json.dumps(body, indent=2, sort_keys=True)+"\n")
    return jobs


def run_index(stage: str, index: int) -> None:
    body = json.loads(_plan_path(stage).read_text())
    if sha256((ROOT/"run_importance.py").read_bytes()).hexdigest() != body["runner_sha256"]:
        raise ValueError("importance runner changed after plan freeze")
    job = body["jobs"][index]
    output = REPO / job["output"]
    if (output/"summary.json").exists():
        return
    if output.exists():
        raise FileExistsError(output)
    run(code_name=job["code"], method=job["method"], p=job["p"],
        proposal_p=job["proposal_p"], defensive_fraction=job["defensive_fraction"],
        seed=job["seed"], start_shot=job["start_shot"], shots=job["shots"], output=output)


def submit(stage: str, max_parallel: int) -> str | None:
    body = json.loads(_plan_path(stage).read_text())
    jobs = body["jobs"]
    if not jobs:
        return None
    command = ["sbatch", "--parsable", "-J", "yao-bp-bpgd-rare-ext", "-p", "common",
               "--account=pfisterlab", "-c", "1", "--mem=4G", "-t", "12:00:00",
               "-o", str(RESULTS / f"completion-importance-{stage}-%A_%a.log"),
               f"--array=0-{len(jobs)-1}%{max_parallel}", "--wrap",
               f"{sys.executable} {Path(__file__).resolve()} --stage {stage} --run-index $SLURM_ARRAY_TASK_ID"]
    return subprocess.check_output(command, text=True).strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--run-index", type=int)
    parser.add_argument("--max-parallel", type=int, default=32)
    args = parser.parse_args()
    if args.run_index is not None:
        run_index(args.stage, args.run_index)
    elif args.plan:
        print(json.dumps({"jobs": len(write_plan(args.stage))}))
    elif args.submit:
        if not 1 <= args.max_parallel <= 64:
            raise ValueError("max_parallel must be in [1,64]")
        body = json.loads(_plan_path(args.stage).read_text())
        print(json.dumps({"jobs":len(body["jobs"]),"slurm_job_id":submit(args.stage,args.max_parallel)}))
    else:
        parser.error("choose --plan, --submit, or --run-index")
