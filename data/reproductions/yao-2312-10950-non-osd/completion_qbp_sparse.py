"""Run two frozen fixed-shot vanilla BP follow-ups without changing the original runner."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PLAN = ROOT / "results/completion-qbp-sparse-plan.json"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: completion_qbp_sparse.py INDEX")
    body = json.loads(PLAN.read_text())
    if body["schema"] != "yao-completion-qbp-sparse-plan-v1":
        raise ValueError("unexpected QBP follow-up plan schema")
    runner = REPO / body["runner"]
    if sha256(runner.read_bytes()).hexdigest() != body["runner_sha256"]:
        raise ValueError("vanilla runner drift since follow-up freeze")
    job = body["jobs"][int(sys.argv[1])]
    output = REPO / job["output"]
    if output.exists():
        raise FileExistsError(output)
    subprocess.run([sys.executable, str(runner), "--code", job["code"],
                    "--p", str(job["p"]), "--seed", str(job["seed"]),
                    "--start-shot", str(job["start_shot"]),
                    "--shots", str(job["fixed_shots"]),
                    "--output", str(output)], check=True)
