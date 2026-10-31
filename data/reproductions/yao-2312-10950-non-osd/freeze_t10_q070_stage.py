"""Audit the completed T=10 proposal screens and dispatch an independent stage."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from assess_proposals import assess
from extend_importance import submit

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULTS = ROOT / "results"
KEY = ("b1", "bpgd_t10", 0.04)
STAGE = "stage9"
REFRESH_JOB_ID = "60650712"


def add_refresh_dependency(stage_job_id: str) -> None:
    """Keep the deferred report refresh behind the newly dispatched array."""
    shown = subprocess.run(["scontrol", "show", "job", "-o", REFRESH_JOB_ID],
                           check=True, capture_output=True, text=True).stdout
    match = re.search(r"(?:^|\s)Dependency=([^\s]+)", shown)
    if match is None or match.group(1) == "(null)":
        raise ValueError("refresh job has no preserved dependency chain")
    current = re.sub(r"\((?:unfulfilled|fulfilled)\)", "", match.group(1))
    added = f"afterany:{stage_job_id}_*"
    if added not in current.split(","):
        subprocess.run(["scontrol", "update", f"jobid={REFRESH_JOB_ID}",
                        f"dependency={current},{added}"], check=True)


def freeze() -> tuple[Path, Path]:
    stage_path = RESULTS / "completion-importance-extension-stage9.json"
    receipt_path = RESULTS / "proposal-tuning-b1-t10-p040-assessment-three-arm.json"
    if stage_path.exists() or receipt_path.exists():
        raise FileExistsError("stage 9 or its selection receipt already exists")
    two = assess(RESULTS / "proposal-tuning-b1-t10-p040-plan.json")
    third = assess(RESULTS / "proposal-tuning-b1-t10-p040-q070-plan.json")
    candidates = two["rows"] + third["rows"]
    if {row["proposal_p"] for row in candidates} != {0.05, 0.055, 0.07}:
        raise ValueError("proposal screen arms differ from the frozen comparison")
    selected = min(candidates, key=lambda row: (-row["failure_ess_per_shot"], row["proposal_p"]))
    old_stage = json.loads((RESULTS / "completion-importance-extension-stage8.json").read_text())
    if len(old_stage["jobs"]) != 10 or any(not (REPO / job["output"] / "summary.json").exists()
                                             for job in old_stage["jobs"]):
        raise ValueError("the independent stage 8 must finish before stage 9 is frozen")
    intervals = []
    for name in ["completion-importance-plan.json"] + [
            f"completion-importance-extension-stage{stage}.json" for stage in range(1, 9)]:
        body = json.loads((RESULTS / name).read_text())
        for job in body["jobs"]:
            if (job["code"], job["method"], job["p"]) == KEY:
                count = job.get("shots", job.get("max_shots"))
                if count is None:
                    raise ValueError("prior importance stage lacks a fixed shot count")
                intervals.append((job["start_shot"], job["start_shot"] + count))
    intervals.sort()
    if not intervals or intervals[0][0] != 0 or any(a[1] > b[0] for a, b in zip(intervals, intervals[1:])):
        raise ValueError("prior importance shots overlap or have no origin")
    next_shot = intervals[-1][1]
    receipt = {
        "schema": "yao-importance-proposal-screen-comparison-v1",
        "rule": "maximum independently audited weighted failure ESS per shot; lower q breaks ties",
        "rows": candidates,
        "selected_proposal_p": selected["proposal_p"],
        "two_arm_plan_sha256": two["plan_sha256"],
        "third_arm_plan_sha256": third["plan_sha256"],
        "screen_shots_excluded_from_final_estimate": True,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    jobs = []
    for shard in range(10):
        output = RESULTS / (f"completion-importance-b1-bpgd_t10-p040-"
                            f"q{int(round(selected['proposal_p']*1000)):03d}-seed20261035-"
                            f"stage9-s{shard+1:02d}")
        jobs.append({"code": "b1", "method": "bpgd_t10", "p": 0.04,
                     "proposal_p": selected["proposal_p"], "defensive_fraction": 0.1,
                     "seed": 20261035, "start_shot": next_shot + 50000*shard,
                     "shots": 50000, "output": str(output.relative_to(REPO)),
                     "proposal_selection_sha256": sha256(receipt_path.read_bytes()).hexdigest()})
    stage = {"schema": "yao-importance-extension-plan-v1", "stage": STAGE,
             "precision_target_failure_ess": 100,
             "max_additional_shots_per_point_this_stage": 500000,
             "max_shots_per_shard": 50000,
             "runner_sha256": sha256((ROOT / "run_importance.py").read_bytes()).hexdigest(),
             "proposal_selection": str(receipt_path.relative_to(REPO)), "jobs": jobs}
    stage_path.write_text(json.dumps(stage, indent=2, sort_keys=True) + "\n")
    return stage_path, receipt_path


if __name__ == "__main__":
    stage_path, receipt_path = freeze()
    job_id = submit(STAGE, 10)
    add_refresh_dependency(job_id)
    dispatch_path = RESULTS / "completion-dispatch.json"
    dispatch = json.loads(dispatch_path.read_text())
    dispatch["dispatches"].append({
        "job_id": job_id,
        "description": "Independent B1 guided T=10, p=0.04 stage selected by three audited proposal screens",
        "plan": stage_path.name, "selection_receipt": receipt_path.name,
        "tasks": 10, "max_simultaneous_tasks": 10,
        "cpus_per_task": 1, "memory_gib_per_task": 4,
        "wall_limit_hours_per_task": 12,
    })
    dispatch["worst_case_core_hours_if_every_task_hits_its_wall_limit"] += 120
    dispatch_path.write_text(json.dumps(dispatch, indent=2) + "\n")
    print(json.dumps({"stage": STAGE, "slurm_job_id": job_id,
                      "selected_proposal_p": json.loads(receipt_path.read_text())["selected_proposal_p"]}))
