"""Execute one immutable campaign shard by its array index."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

from run import ROOT, run_point


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, default=os.environ.get("SLURM_ARRAY_TASK_ID"))
    args = parser.parse_args()
    campaign_bytes = (ROOT / "campaign.json").read_bytes()
    campaign = json.loads(campaign_bytes)
    if sha256((ROOT / "source_points.json").read_bytes()).hexdigest() != campaign["source_points_sha256"]:
        raise ValueError("published source points changed after campaign planning")
    repo = ROOT.parents[2]
    for name, expected in campaign["implementation_files_sha256"].items():
        if sha256((repo / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"implementation or decoder policy changed after campaign planning: {name}")
    if args.index is None or not 0 <= args.index < len(campaign["tasks"]):
        parser.error("valid campaign task index required")
    task = campaign["tasks"][args.index]
    if task["index"] != args.index:
        raise ValueError("campaign task ordering changed")
    output = (ROOT / task["output"]).resolve()
    if not output.is_relative_to((ROOT / "results/shards").resolve()):
        raise ValueError("campaign task output escapes result directory")
    run_point(task["code"], task["p"], target_failures=100,
              max_shots=task["shots"], seed=task["seed"], output=output,
              start_shot=task["start_shot"], fixed_shots=task["shots"],
              campaign_sha256=sha256(campaign_bytes).hexdigest())


if __name__ == "__main__":
    main()
