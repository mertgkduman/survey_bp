"""Finalize only complete, flushed shot rows after an external process termination."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


def recover(directory: Path) -> dict:
    manifest_path = directory / "manifest.json"
    ledger_path = directory / "events.jsonl"
    summary_path = directory / "summary.json"
    if summary_path.exists():
        raise FileExistsError("refusing to replace a completed summary")
    manifest = json.loads(manifest_path.read_text())
    if manifest["schema"] != "yao-non-osd-run-v1":
        raise ValueError("unsupported manifest")
    ledger = ledger_path.read_bytes()
    if not ledger or not ledger.endswith(b"\n"):
        raise ValueError("no complete flushed shot prefix")
    events = [json.loads(line) for line in ledger.splitlines()]
    if len(events) > manifest["max_shots"]:
        raise ValueError("shot ceiling exceeded")
    if [row["shot"] for row in events] != list(range(manifest["start_shot"], manifest["start_shot"] + len(events))):
        raise ValueError("shot prefix is not contiguous")
    names = ("type_i", "type_ii", "exact_success", "stabilizer_success",
             "iterations", "rounds", "fixations", "elapsed_ns")
    counts = {name: sum(int(row["outcome"][name]) for row in events) for name in names}
    if sum(counts[name] for name in names[:4]) != len(events):
        raise ValueError("shot outcomes do not partition")
    failures = counts["type_i"] + counts["type_ii"]
    if manifest["target_failures"] is not None and failures >= manifest["target_failures"]:
        raise ValueError("prefix already hit target; investigate missing normal summary")
    result = {"schema": "yao-non-osd-summary-v1", "code": manifest["code"],
              "method": manifest["method"], "physical_p": manifest["physical_p"],
              "seed": manifest["seed"], "start_shot": manifest["start_shot"],
              "shots": len(events), "failures": failures,
              "stop_reason": "externally_interrupted_complete_prefix", "counts": counts,
              "source_targets": manifest["source_targets"],
              "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
              "events_sha256": sha256(ledger).hexdigest(), "wall_seconds": None,
              "recovery_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    summary_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(recover(args.directory), sort_keys=True))
