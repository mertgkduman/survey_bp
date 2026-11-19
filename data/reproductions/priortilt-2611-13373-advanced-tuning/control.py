"""Submit screen jobs and independently dependent tuning/confirmation jobs."""
import argparse
from datetime import datetime, timezone
import subprocess

import run


def launch(plan):
    state = run.ROOT / "dispatch.json"
    (run.ROOT / "results").mkdir(exist_ok=True)
    digest = run.sha(run.ROOT / "plan.json")
    with run.lock(run.ROOT / "dispatch.lock", True):
        receipt = (run.read_json(state) if state.exists() else
                   {"plan_sha256": digest, "submitted_utc": datetime.now(timezone.utc).isoformat(), "jobs": {}})
        if receipt["plan_sha256"] != digest:
            raise ValueError("dispatch plan changed")

        def submit(key, args, *, dependency=None, indices=(), cpu=20, memory=32):
            if key not in receipt["jobs"]:
                options = ["--array="+",".join(map(str,indices))] if indices else []
                if dependency:
                    options += [f"--dependency={dependency}", "--kill-on-invalid-dep=yes"]
                argv = ["sbatch", "--parsable", "--partition=common,scavenger", "--account=pfisterlab",
                        "--nodes=1", "--ntasks=1", f"--cpus-per-task={cpu}", f"--mem={memory}G",
                        "--time=4-00:00:00", f"--chdir={run.REPO}", "--requeue", "--signal=B:USR1@180",
                        f"--job-name=ptadv-{key}", f"--output={run.ROOT}/results/{key}-%A_%a.log",
                        *options, str(run.ROOT/"worker.sh"), *args]
                job_id = subprocess.check_output(argv, text=True).strip().split(";")[0]
                if not job_id.isdigit():
                    raise ValueError("unexpected scheduler job id")
                receipt["jobs"][key] = {"id": job_id, "argv": argv}
                run.write_json(state, receipt)
                print(key, job_id, flush=True)
            return receipt["jobs"][key]["id"]

        screens = {g: submit(f"screen-{g}", ["screen",g]) for g in plan["groups"]}
        confirms = []
        for group, screen in screens.items():
            points = [i for i,j in enumerate(plan["jobs"]) if j["group"] == group]
            training = submit(f"tune-{group}", ["tune"], dependency=f"afterok:{screen}", indices=points)
            for i in points:
                confirms.append(submit(f"confirm-{i}", ["confirm"],
                                       dependency=f"afterok:{training}_{i}", indices=[i]))
        submit("collect", ["collect"], dependency="afterany:"+":".join(confirms), cpu=1, memory=10)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("freeze", "submit"))
    a = p.parse_args()
    if a.action == "freeze":
        run.freeze()
    else:
        launch(run.load())
