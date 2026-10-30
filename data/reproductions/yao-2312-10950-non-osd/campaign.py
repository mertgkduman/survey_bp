"""Run explicit bounded subsets of the Yao non-OSD source grid.

This development runner does not authorize Phase 11 publication campaigns.
Each point has a fixed shot ceiling and keeps its own manifest and ledger.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = json.loads((ROOT / "source_points.json").read_text())


def planned_jobs(tier: str) -> list[tuple[str, str, float, int, int]]:
    jobs = []
    for figure, body in SOURCE["figures"].items():
        for method, curve in body["curves"].items():
            if method in {"qbp", "bp_si_external"}:
                continue
            normalized = "bpgd_t100" if method == "bpgd_t100_r882" else method
            for p_str, rate in curve.items():
                p = float(p_str)
                if tier == "bp_grid" and not (normalized == "bp" and p != .06):
                    continue
                if tier == "guided_grid" and not (normalized == "bpgd_t10" and .07 <= p <= .1 and body["code"] in {"b1", "c2"}):
                    continue
                if tier == "quaternary_grid" and not (normalized == "bpgd_t10" and body["code"] in {"a5", "b2"} and p != .06):
                    continue
                if tier == "ablation_p008" and not (body["code"] == "b1" and normalized in {"bpgd_t1", "bpgd_t100_r2", "bpgd_t100_r5", "bpgd_t100_r10", "bpgd_t100_r50"} and p == .08):
                    continue
                if tier == "full_bounded" and (normalized == "bp" or body["code"] in {"a5", "b2"}):
                    continue
                if tier in {"bp_grid", "guided_grid", "quaternary_grid"}:
                    ceiling = 5000
                elif tier == "ablation_p008":
                    ceiling = 200 if normalized == "bpgd_t100_r50" else 500
                else:
                    ceiling = 1000
                target = 100
                jobs.append((body["code"], normalized, p, ceiling, target))
    return sorted(set(jobs))


def execute(job: tuple[str, str, float, int, int], tier: str, seed: int) -> dict:
    code, method, p, ceiling, target = job
    output = ROOT / "results" / f"{tier}-{code}-{method}-p{int(round(p * 1000)):03d}-seed{seed}"
    if (output / "summary.json").exists():
        return {"job": job, "status": "already_complete", "output": str(output)}
    if output.exists():
        return {"job": job, "status": "partial_evidence_requires_review", "output": str(output)}
    environment = dict(os.environ, PYTHONPATH=str(ROOT.parents[2] / "src"))
    command = [sys.executable, str(ROOT / "run_point.py"), "--code", code, "--method", method,
               "--p", str(p), "--seed", str(seed), "--max-shots", str(ceiling),
               "--target-failures", str(target), "--output", str(output)]
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    (ROOT / "results" / f"{output.name}.log").write_text(result.stdout + result.stderr)
    return {"job": job, "status": "complete" if result.returncode == 0 else "failed",
            "returncode": result.returncode, "output": str(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=("bp_grid", "guided_grid", "quaternary_grid", "ablation_p008", "full_bounded"), required=True)
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        raise ValueError("development campaign has a four-worker ceiling")
    jobs = planned_jobs(args.tier)
    print(json.dumps({"tier": args.tier, "jobs": jobs, "workers": args.workers}), flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(execute, job, args.tier, args.seed): job for job in jobs}
        for future in as_completed(futures):
            print(json.dumps(future.result(), sort_keys=True), flush=True)
