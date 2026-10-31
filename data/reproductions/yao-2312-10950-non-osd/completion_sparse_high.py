"""Execute the frozen high-rate direct 100-failure follow-up array."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

from run_point import run

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PLAN = ROOT / "results/completion-sparse-high-plan.json"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: completion_sparse_high.py INDEX")
    body = json.loads(PLAN.read_text())
    if body["schema"] != "yao-completion-sparse-high-plan-v1":
        raise ValueError("unexpected frozen sparse-plan schema")
    if sha256((ROOT / "run_point.py").read_bytes()).hexdigest() != body["runner_sha256"]:
        raise ValueError("runner drift since sparse-plan freeze")
    job = body["jobs"][int(sys.argv[1])]
    output = REPO / job["output"]
    if output.exists():
        raise FileExistsError(output)
    run(code_name=job["code"], method=job["method"], p=job["p"],
        seed=job["seed"], start_shot=job["start_shot"],
        max_shots=job["max_shots"], target_failures=job["target_failures"],
        output=output)
