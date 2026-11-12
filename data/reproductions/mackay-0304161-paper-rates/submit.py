"""Submit bounded independent-shot workers and a dependent paper-rate audit."""

import argparse
import fcntl
import json
import shlex
import subprocess
import sys

from run import REPO, RESULTS, ROOT, jobs, load_plan, write_json


def submit(check_only=False):
    plan = load_plan()
    RESULTS.mkdir(exist_ok=True)
    base = ["sbatch", "--parsable", "--partition=common,scavenger", "--account=pfisterlab",
            "--nodes=1", "--ntasks=1", "--requeue", "--time=4-00:00:00", f"--chdir={REPO}",
            f"--export=ALL,PYTHONPATH={REPO / 'src'},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1"]
    if check_only:
        base.append("--test-only")
    command = shlex.join([sys.executable, str(ROOT / "run.py")])
    receipt_path = RESULTS / "dispatch.json"
    with (RESULTS / "dispatch.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}

        def queue(name, options):
            if name in receipt and not check_only:
                return
            argv = [*base, *options]
            result = subprocess.run(argv, check=True, capture_output=True, text=True)
            if check_only:
                print(result.stdout + result.stderr, end="")
                return
            job_id = result.stdout.strip().split(";")[0]
            if not job_id.isdigit():
                raise ValueError(f"invalid Slurm receipt: {result.stdout!r}")
            receipt[name] = {"id": job_id, "argv": argv}
            write_json(receipt_path, receipt)
            print(name, job_id, flush=True)

        names = []
        for workers, concurrency, memory in ((16, 4, "8G"), (4, 12, "6G"), (1, 14, "4G")):
            indexes = [str(i) for i, job in enumerate(jobs(plan)) if job["workers"] == workers]
            if not indexes:
                continue
            name = f"workers_{workers}"
            names.append(name)
            queue(name, [f"--job-name=mackay-paper-{workers}c", f"--cpus-per-task={workers}", f"--mem={memory}",
                         f"--array={','.join(indexes)}%{concurrency}",
                         f"--output={RESULTS / 'slurm-%A_%a.log'}",
                         f'--wrap=exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        if not check_only:
            dependency = ":".join(receipt[name]["id"] for name in names)
            publish = shlex.join([sys.executable, str(ROOT / "publish.py")])
            refresh = shlex.join([sys.executable, str(ROOT / "refresh_catalog.py")])
            queue("collect", ["--job-name=mackay-paper-audit", "--cpus-per-task=1", "--mem=4G",
                              f"--dependency=afterany:{dependency}", f"--output={RESULTS / 'collect-%j.log'}",
                              f"--wrap={command} --collect && {publish} && {refresh}"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-only", action="store_true")
    submit(parser.parse_args().test_only)
