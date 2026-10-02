#!/usr/bin/env python3
"""Replay and summarize the corrected Phase 5 p=0.05 paired pilot v2."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path

from run_phase5_damping_pilot_v2 import (
    ARMS, BASE_ARMS, OUTPUT, SHOTS, _digest_bytes, _read, sealed_design,
)
from bp_registry.cli import verify_run


def _verify_arm(arm: str) -> str:
    verify_run(OUTPUT / arm)
    return arm


def _verify_aggregate(design: dict, result: dict, root: Path, *, design_path: Path | None = None) -> dict:
    """Apply the sealed verifier's aggregate and paired-sample checks once."""
    pinned_design = design_path or root.parents[2] / "manifests/phase5-b1-p005-damping-pilot-v2.json"
    if result["design_sha256"] != _digest_bytes(pinned_design):
        raise ValueError("paired result design digest differs")
    if result["ledger_sha256"] != _digest_bytes(root / "events.jsonl"):
        raise ValueError("paired result aggregate ledger digest differs")
    aggregate: list[str] = []
    samples: dict[int, str] = {}
    for arm in ARMS:
        arm_root = root / arm
        if _read(arm_root / "manifest.json") != design["arm_manifests"][arm]:
            raise ValueError(f"{arm} saved manifest drifted")
        arm_result = _read(arm_root / "result.json")
        if arm_result["ledger_sha256"] != result["arm_results"][arm]["ledger_sha256"]:
            raise ValueError(f"{arm} public result digest drifted")
        lines = (arm_root / "events.jsonl").read_text(encoding="utf-8").splitlines()
        aggregate.extend(lines)
        for event in (json.loads(line) for line in lines if line):
            if event["kind"] == "shot_begin":
                shot_id, sample_id = event["shot_id"], event["sample_seed_identity"]
                if samples.setdefault(shot_id, sample_id) != sample_id:
                    raise ValueError("paired physical sample mismatch")
    if ("\n".join(aggregate) + "\n").encode("utf-8") != (root / "events.jsonl").read_bytes():
        raise ValueError("aggregate ledger differs from its arm evidence")
    if sorted(samples) != design["shot_ids"] or {str(k): v for k, v in samples.items()} != result["physical_sample_identities"]:
        raise ValueError("paired sample identity set is incomplete")
    return {"status": "passed", "shots": len(samples), "arms": len(ARMS), "ledger_sha256": result["ledger_sha256"]}


def verify_parallel() -> dict:
    design = sealed_design()
    available = int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1))
    with ProcessPoolExecutor(max_workers=min(len(ARMS), available)) as pool:
        verified = tuple(pool.map(_verify_arm, ARMS))
    if verified != ARMS:
        raise ValueError("not every arm completed public replay verification")
    return _verify_aggregate(design, _read(OUTPUT / "result.json"), OUTPUT)


def _save(path: Path, text: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise ValueError(f"existing report differs: {path}")
        return
    path.write_text(text, encoding="utf-8")


def summarize() -> tuple[dict, str]:
    verification = verify_parallel()
    rows: dict[str, dict] = {}
    terminals: dict[str, dict[int, str]] = {}
    for arm in ARMS:
        result = json.loads((OUTPUT / arm / "result.json").read_text(encoding="utf-8"))
        outcomes: dict[int, str] = {}
        work: dict[int, dict] = {}
        with (OUTPUT / arm / "events.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                event = json.loads(line)
                shot_id = event["shot_id"]
                if event["kind"] == "termination":
                    if shot_id in outcomes:
                        raise ValueError(f"duplicate terminal: {arm} {shot_id}")
                    outcomes[shot_id] = event["data"]["payload"]["outcome"] or "outcome_unavailable"
                elif event["kind"] == "work":
                    if shot_id in work:
                        raise ValueError(f"duplicate work event: {arm} {shot_id}")
                    work[shot_id] = event["data"]["payload"]["work_vector"]
        if sorted(outcomes) != list(range(SHOTS)) or sorted(work) != list(range(SHOTS)):
            raise ValueError(f"incomplete outcome or work set: {arm}")
        counts = Counter(outcomes.values())
        if {key: counts[key] for key in result["denominators"] if key != "all_terminal_shots"} != {
            key: value for key, value in result["denominators"].items() if key != "all_terminal_shots"
        }:
            raise ValueError(f"outcome denominator mismatch: {arm}")
        if sum(counts.values()) != result["denominators"]["all_terminal_shots"]:
            raise ValueError(f"terminal denominator mismatch: {arm}")
        rows[arm] = {
            "outcomes": dict(sorted(counts.items())),
            "terminations": result["terminations"],
            "mean_bp_sweeps": sum(item["convergence_checks"] for item in work.values()) / SHOTS,
            "mean_intervention_actions": sum(item["intervention_actions"] for item in work.values()) / SHOTS,
            "mean_bp_calls": sum(item["bp_calls"] for item in work.values()) / SHOTS,
        }
        terminals[arm] = outcomes
    summary = {
        "schema_version": 1,
        "design_sha256": sha256((Path(__file__).resolve().parents[1] / "data/manifests/phase5-b1-p005-damping-pilot-v2.json").read_bytes()).hexdigest(),
        "verification": verification,
        "arms": rows,
    }
    valid = {"exact", "stabilizer_equivalent"}
    report = [
        "# Corrected B1 p=0.05 matched intervention and damping pilot v2", "",
        "128 matched physical samples per arm, 14 arms, V2C damping γ=0.5. Every terminal shot is retained.",
        "Verification: all 14 public runs replayed and the aggregate ledger and physical sample identities matched.",
        "Evidence relation: `pilot_adaptation`; assessment: `not_assessed`. These descriptive counts do not establish decoder ranking or source-curve agreement. The v1 run was invalidated by source-semantic defects.",
        "", "| Intervention | Valid off | Valid damped | Newly valid | Lost valid | Unavailable off | Unavailable damped | Mean BP sweeps off | Mean BP sweeps damped |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for arm in BASE_ARMS:
        damped = f"{arm}__damped"
        a, b = rows[arm], rows[damped]
        ao, bo = terminals[arm], terminals[damped]
        newly = sum(ao[i] not in valid and bo[i] in valid for i in range(SHOTS))
        lost = sum(ao[i] in valid and bo[i] not in valid for i in range(SHOTS))
        av = sum(a["outcomes"].get(x, 0) for x in valid)
        bv = sum(b["outcomes"].get(x, 0) for x in valid)
        report.append(
            f"| {arm} | {av} | {bv} | {newly} | {lost} | "
            f"{a['outcomes'].get('outcome_unavailable', 0)} | {b['outcomes'].get('outcome_unavailable', 0)} | "
            f"{a['mean_bp_sweeps']:.2f} | {b['mean_bp_sweeps']:.2f} |"
        )
    report.extend([
        "", "Valid means exact or stabilizer-equivalent recovery on the original CSS problem. Newly valid and lost valid compare the same physical sample under damping off and on.",
        "Mean BP sweeps counts admitted convergence checks per sample across all attempts and branches. `summary.json` also records intervention actions, BP calls, exact outcomes, logical failures, and termination counts.",
        "Each arm has its own `manifest.json`, `events.jsonl`, and `result.json`; the root `events.jsonl` and `result.json` bind the aggregate evidence.", "",
    ])
    return summary, "\n".join(report)


if __name__ == "__main__":
    summary, report = summarize()
    _save(OUTPUT / "summary.json", json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
    _save(OUTPUT / "REPORT.md", report)
    print(json.dumps({"status": "verified", "shots": SHOTS, "arms": len(ARMS), "report": str(OUTPUT / "REPORT.md")}, sort_keys=True))
