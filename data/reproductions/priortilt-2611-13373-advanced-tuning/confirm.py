"""Use the established ordered executor for each fixed tuned controller."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import json
import multiprocessing as mp
import os
import platform
import sys

import numpy as np

import run

# The frozen parallel module imports this study's run adapter. Its scheduling,
# prefix commits, work reconciliation and endpoint audit are reused verbatim.
sys.path.append(str(run.PARENTS["xyz"]))
import parallel

parallel.VERSION = run.VERSION


def run_point(plan, job, audit, workers):
    plan = run.effective_plan(plan, job)
    root = run.ROOT / "results" / job["id"]
    root.mkdir(parents=True, exist_ok=True)
    plan_hash = run.sha(run.ROOT / "plan.json")
    # PriorTiltSpec stores schedule tuples. Compare their JSON representation
    # on both executions so the fresh audit accepts the same sealed manifest.
    manifest = json.loads(json.dumps({"plan_sha256": plan_hash, "job": job,
                                     "resolved_policy": asdict(run.spec_for(job)), "workers": workers}))
    with run.lock(root / "run.lock", True):
        path = root / "manifest.json"
        if path.exists() and run.read_json(path) != manifest:
            raise ValueError("advanced point manifest changed")
        if not path.exists():
            run.write_json(path, manifest)
        audit_path = root / "audit.json"
        complete_path = root / "complete.json"
        if not audit and complete_path.exists():
            return
        models = {b: run.case_model(job, b) for b in run.BASES}
        expected = {b: m.execution_sha256 for b, (_, m) in models.items()}
        for b, (_, model) in models.items():
            run.prepared(plan, job, b, model).decode(np.zeros(model.table.check_count, np.uint8), shot=0)
        with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn"),
                                 initializer=parallel.initialize,
                                 initargs=(plan, job, expected, str(run.ROOT))) as pool:
            summaries = parallel.scan(pool, plan, job)
            if not audit:
                run.write_json(root / "hardware.json",
                               {"host": platform.node(), "workers": workers,
                                "cpus": os.environ.get("SLURM_CPUS_PER_TASK"),
                                "affinity": sorted(os.sched_getaffinity(0))})
                parallel.continue_point(pool, plan, job, summaries, models, plan_hash, workers)
            else:
                stages = (root / "parallel-stages" / run.VERSION).glob("*.json")
                for _ in pool.map(parallel.audit_task, [(p.name[0], str(p)) for p in stages], chunksize=8):
                    pass
        cost = parallel.expenditure(plan, job, summaries)
        receipt = {**manifest, "manifest_sha256": run.sha(path),
                   "bases": {b: run.terminal(s, plan) for b, s in summaries.items()},
                   "work_sha256": run.identity(cost)}
        work_path = root / "parallel-work.json"
        if audit:
            if run.read_json(complete_path) != receipt or run.read_json(work_path) != cost:
                raise ValueError("fresh advanced audit differs from terminal receipt")
            run.write_json(audit_path, receipt)
            print("Audited", job["id"], flush=True)
        else:
            run.write_json(work_path, cost)
            run.write_json(complete_path, receipt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    plan = run.load()
    workers = plan["workers"]
    if int(os.environ.get("SLURM_CPUS_PER_TASK", 0)) != workers or len(os.sched_getaffinity(0)) < workers:
        raise ValueError(f"expected {workers} Slurm CPUs and corresponding affinity")
    run_point(plan, run.resolve_job(plan, args.index), args.audit, workers)


if __name__ == "__main__":
    main()
