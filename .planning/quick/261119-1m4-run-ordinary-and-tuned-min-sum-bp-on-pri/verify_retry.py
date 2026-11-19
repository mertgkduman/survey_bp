"""Verify the replacement launch against the frozen evaluation grid."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "data/reproductions/priortilt-2611-13373-bp"))
import run

plan = run.load()
receipt = run.read_json(run.ROOT / "dispatch.json")
assert receipt["plan_sha256"] == run.sha(run.ROOT / "plan.json")
assert plan["schema"] == "circuit-bp-ordered-v2"
assert plan["workers"] == 20 and plan["protocol"]["iterations"] == 18080
counts = Counter((j["mode"], j["method"]) for j in plan["jobs"])
assert counts == {("xz", "bp"): 13, ("xz", "tuned-bp"): 13, ("xyz", "bp"): 1, ("xyz", "tuned-bp"): 1}

evaluations = {}
for name, entry in receipt["jobs"].items():
    args = entry["argv"]
    assert f'--cpus-per-task={1 if name == "collect" else 20}' in args
    array = next((arg.split("=", 1)[1] for arg in args if arg.startswith("--array=")), None)
    if array:
        for index in map(int, array.split(",")):
            job = plan["jobs"][index]
            assert name == ("baseline" if job["method"] == "bp" else f'eval-{job["group"]}')
            evaluations[f'{entry["id"]}_{index}'] = job["id"]
        if name != "baseline":
            tune = receipt["jobs"]["tune-" + name.removeprefix("eval-")]["id"]
            assert "--dependency=afterok:" + tune in args
assert len(evaluations) == 28 and set(evaluations.values()) == {job["id"] for job in plan["jobs"]}
ids = ",".join(v["id"] for v in receipt["jobs"].values())
output = subprocess.check_output(
    ["squeue", "-r", "-h", "-j", ids + ",62102101", "-o", "%i|%j|%T|%C|%M|%R"], text=True)
(HERE / "scheduler.txt").write_text(output)
active = {}
for line in output.splitlines():
    jid, name, state, cpus, elapsed, reason = line.split("|")
    active[jid] = {"name": name, "state": state, "cpus": int(cpus),
                   "elapsed": elapsed, "reason_or_node": reason}
for jid in evaluations:
    if jid not in active:
        text = subprocess.check_output(["scontrol", "show", "job", "-o", jid], text=True)
        fields = dict(entry.split("=", 1) for entry in text.split() if "=" in entry)
        active[jid] = {"state": fields["JobState"], "cpus": int(fields["NumCPUs"])}
    assert active[jid]["cpus"] == 20
    assert active[jid]["state"] not in {"FAILED", "OUT_OF_MEMORY", "CANCELLED"}
progress = {}
for job in plan["jobs"]:
    folder = run.ROOT / "results" / job["id"]
    path = folder / "progress.json"
    if path.exists():
        progress[job["id"]] = {
            b: {k: values[k] for k in ("shots", "errors", "rescaled_shots", "llr_rescales")}
            for b, values in run.read_json(path)["bases"].items()
        }
verification = {
    "timestamp": datetime.now(timezone.utc).isoformat(), "plan_sha256": receipt["plan_sha256"],
    "frozen_files": len(plan["implementation_sha256"]), "allocated_cpus_per_evaluation": 20,
    "evaluation_jobs": evaluations, "scheduler": active, "committed_progress": progress,
    "complete_audits": sum((run.ROOT / "results" / j["id"] / "audit.json").exists() for j in plan["jobs"]),
}
(HERE / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
print("Verified", len(evaluations), "20-CPU evaluations,", len(progress), "with committed progress")
