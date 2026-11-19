"""Submit resumable BP jobs with separate dependencies for each tuned group."""
import argparse
from datetime import datetime, timezone
import subprocess

import run


def submit(plan):
    state = run.ROOT / "dispatch.json"
    (run.ROOT / "results").mkdir(exist_ok=True)
    digest = run.sha(run.ROOT / "plan.json")
    with run.lock(run.ROOT / "dispatch.lock", True):
        record = (run.read_json(state) if state.exists() else
                  {"plan_sha256": digest, "created_utc": datetime.now(timezone.utc).isoformat(), "jobs": {}})
        if record["plan_sha256"] != digest:
            raise ValueError("BP dispatch plan changed")

        def launch(key, options, args, cpu=20, memory=32, limit="4-00:00:00"):
            if key not in record["jobs"]:
                argv = ["sbatch", "--parsable", "--partition=common,scavenger", "--account=pfisterlab",
                        "--nodes=1", "--ntasks=1", f"--cpus-per-task={cpu}", f"--mem={memory}G",
                        f"--time={limit}", f"--chdir={run.REPO}", "--requeue", "--signal=B:USR1@180",
                        f"--job-name=ptbp-{key}", f"--output={run.ROOT}/results/{key}-%A_%a.log",
                        *options, str(run.ROOT / "worker.sh"), *args]
                job = subprocess.check_output(argv, text=True).strip().split(";")[0]
                if not job.isdigit():
                    raise ValueError("unexpected sbatch job ID")
                record["jobs"][key] = {"id": job, "argv": argv}
                run.write_json(state, record)
                print(key, job, flush=True)
            return record["jobs"][key]["id"]

        baseline = [i for i, j in enumerate(plan["jobs"]) if j["method"] == "bp"]
        collectors = [launch("baseline", ["--array=" + ",".join(map(str, baseline))], ["evaluate"])]
        for group in plan["training_points"]:
            training = launch(f"tune-{group}", [], ["tune", group])
            points = [i for i, j in enumerate(plan["jobs"]) if j["group"] == group and j["method"] == "tuned-bp"]
            collectors.append(launch(f"eval-{group}",
                                     [f"--dependency=afterok:{training}", "--kill-on-invalid-dep=yes",
                                      "--array=" + ",".join(map(str, points))], ["evaluate"]))
        launch("collect", ["--dependency=afterany:" + ":".join(collectors)], ["collect"], cpu=1, memory=10)
        return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("freeze", "submit"))
    args = parser.parse_args()
    if args.action == "freeze":
        import report
        report.collect(run.freeze())
    else:
        submit(run.load())
