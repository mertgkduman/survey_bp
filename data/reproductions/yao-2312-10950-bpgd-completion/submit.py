"""Submit the frozen campaign and a dependent Slurm verification job."""

from __future__ import annotations

import argparse
import fcntl
import json
import shlex
import subprocess
import sys

from run import REPO, RESULTS, ROOT, jobs, load_plan, write_json


def submit(*, check_only: bool) -> None:
    plan = load_plan()
    RESULTS.mkdir(exist_ok=True)
    base = ["sbatch", "--parsable", "--partition=common,scavenger", "--account=pfisterlab",
            "--nodes=1", "--ntasks=1", "--requeue", f"--chdir={REPO}",
            f"--export=ALL,PYTHONPATH={REPO / 'src'},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1"]
    if check_only:
        base.append("--test-only")
    command = shlex.join([sys.executable, str(ROOT / "run.py")])
    receipt_path = RESULTS / "dispatch.json"
    with (RESULTS / "dispatch.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}

        def queue(name: str, options: list[str]) -> None:
            if name in receipt and not check_only:
                return
            argv = [*base, *options]
            result = subprocess.run(argv, check=True, capture_output=True, text=True)
            if check_only:
                print(result.stdout + result.stderr, end="")
                return
            job_id = result.stdout.strip().split(";")[0]
            if not job_id.isdigit():
                raise ValueError(f"invalid Slurm job receipt: {result.stdout!r}")
            receipt[name] = {"id": job_id, "argv": argv}
            write_json(receipt_path, receipt)
            print(name, job_id, flush=True)

        for workers, concurrent, memory, time_limit in (
            (16, 4, "12G", "4-00:00:00"), (4, 14, "6G", "2-00:00:00"), (1, 32, "4G", "12:00:00"),
        ):
            indexes = ",".join(str(index) for index, job in enumerate(jobs(plan)) if job["workers"] == workers)
            queue(f"workers_{workers}", [
                f"--job-name=yao-complete-{workers}c", f"--cpus-per-task={workers}", f"--mem={memory}",
                f"--time={time_limit}", f"--array={indexes}%{concurrent}",
                f"--output={RESULTS / 'slurm-%A_%a.log'}",
                f"--wrap=exec {command} --index \"$SLURM_ARRAY_TASK_ID\"",
            ])
        if not check_only:
            dependencies = ":".join(receipt[f"workers_{n}"]["id"] for n in (16, 4, 1))
            queue("collect", [
                "--job-name=yao-complete-collect", "--cpus-per-task=1", "--mem=4G", "--time=2-00:00:00",
                f"--dependency=afterany:{dependencies}", f"--output={RESULTS / 'collect-%j.log'}",
                f"--wrap={command} --collect && {shlex.join([sys.executable, str(ROOT / 'refresh_catalog.py')])}",
            ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-only", action="store_true")
    submit(check_only=parser.parse_args().test_only)
