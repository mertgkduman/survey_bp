"""Check Slurm task coverage, CPU requests and the dependency mapping."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[2] / "data/reproductions/priortilt-2611-13373-advanced-tuning"
sys.path.insert(0, str(STUDY))
import run

plan = run.load()
receipt = run.read_json(STUDY/"dispatch.json")
assert receipt["plan_sha256"] == run.sha(STUDY/"plan.json")
entries = receipt["jobs"]
assert len(entries) == 20
harness = {}
for group in plan["groups"]:
    screen = entries[f"screen-{group}"]
    assert "--cpus-per-task=20" in screen["argv"]
    training = entries[f"tune-{group}"]
    assert "--cpus-per-task=20" in training["argv"]
    assert f'--dependency=afterok:{screen["id"]}' in training["argv"]
    subset = []
    for i, job in enumerate(plan["jobs"]):
        if job["group"] == group:
            subset.append(i)
            confirmation = entries[f"confirm-{i}"]
            assert "--cpus-per-task=20" in confirmation["argv"] and f"--array={i}" in confirmation["argv"]
            assert f'--dependency=afterok:{training["id"]}_{i}' in confirmation["argv"]
            harness[job["id"]] = {"p": job["p"], "training": f'{training["id"]}_{i}',
                                  "confirmation": f'{confirmation["id"]}_{i}', "cpus": 20}
    assert "--array=" + ",".join(map(str, subset)) in training["argv"]
assert len(harness) == 11
ids = ",".join(e["id"] for e in entries.values())
raw = subprocess.check_output(["squeue","-r","-h","-j",ids,"-o","%i|%j|%T|%C|%M|%R"], text=True)
(HERE/"scheduler.txt").write_text(raw)
states = {}
for row in raw.splitlines():
    jid, name, state, cpus, elapsed, loc = row.split("|")
    if "collect" not in name:
        assert int(cpus) == 20
    states[jid] = {"name": name, "state": state, "cpus": int(cpus), "elapsed": elapsed, "node_or_reason": loc}
(HERE/"verification.json").write_text(json.dumps({
    "plan_sha256": receipt["plan_sha256"], "frozen_files": len(plan["implementation_sha256"]),
    "scheduler": states, "points": harness,
    "screen_groups": list(plan["groups"]), "collector": entries["collect"]["id"]
}, indent=2)+"\n")
print("Verified 11 tuning and 11 confirmation allocations at 20 CPUs each.",
      dict(Counter((s["name"].split("-")[1],s["state"]) for s in states.values())))
