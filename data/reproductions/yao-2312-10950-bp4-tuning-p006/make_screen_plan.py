"""Freeze paired screen length from six-failure baseline pilots."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from runner import ROOT, REPO, load_registry, source_hashes


SEEDS = {"a5": 620261028, "b2": 620261128}


def main() -> None:
    destination = ROOT / "screen_plan.json"
    if destination.exists():
        raise FileExistsError("screen plan exists; preserve its launched identity")
    registry_path = ROOT / "decoders/screen_candidates.json"
    registry, items, registry_sha = load_registry(registry_path)
    hashes = source_hashes()
    pilot_receipts = {}
    tasks = []
    for code in ("a5", "b2"):
        folder = ROOT / "results/pilot" / code
        summary_bytes = (folder / "summary.json").read_bytes()
        summary = json.loads(summary_bytes)
        manifest_bytes = (folder / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        ledger_bytes = (folder / "events.jsonl").read_bytes()
        if (summary["candidate_id"] != registry["baseline_id"]
                or summary["seed"] != SEEDS[code] or summary["stop_reason"] != "target_block_failures"
                or summary["counts"]["type_i"] + summary["counts"]["type_ii"] != 6
                or summary["manifest_sha256"] != sha256(manifest_bytes).hexdigest()
                or summary["events_sha256"] != sha256(ledger_bytes).hexdigest()
                or manifest["candidate_registry_sha256"] != registry_sha
                or manifest["source_files_sha256"] != hashes):
            raise ValueError(f"pilot evidence does not match the frozen baseline: {code}")
        pilot_receipts[code] = {"shots": summary["shots"], "seed": SEEDS[code],
                                "summary_sha256": sha256(summary_bytes).hexdigest(),
                                "events_sha256": summary["events_sha256"]}
        for candidate_id in items:
            tasks.append({"index": len(tasks), "code": code, "candidate_id": candidate_id,
                          "shots": summary["shots"], "seed": SEEDS[code],
                          "output": f"results/screen/{code}/{candidate_id}"})
    plan = {
        "schema": "yao-bp4-tuning-screen-plan-v1", "physical_p": .06,
        "design": "fixed paired prefix from independent six-baseline-failure pilot per code; exploratory only",
        "candidate_registry": str(registry_path.relative_to(REPO)),
        "candidate_registry_sha256": registry_sha,
        "source_files_sha256": hashes,
        "run_task_sha256": sha256((ROOT / "run_task.py").read_bytes()).hexdigest(),
        "pilots": pilot_receipts, "tasks": tasks,
    }
    destination.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(tasks)} tasks; A5 N={pilot_receipts['a5']['shots']}, "
          f"B2 N={pilot_receipts['b2']['shots']}")


if __name__ == "__main__":
    main()
