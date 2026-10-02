#!/usr/bin/env python3
"""Replay and summarize the corrected Phase 5 p=0.05 paired pilot v2."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from run_phase5_damping_pilot_v2 import ARMS, BASE_ARMS, OUTPUT, SHOTS, verify


def _save(path: Path, text: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise ValueError(f"existing report differs: {path}")
        return
    path.write_text(text, encoding="utf-8")


def summarize() -> tuple[dict, str]:
    verification = verify()
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
                    outcomes[shot_id] = event["data"]["payload"]["outcome"]
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
