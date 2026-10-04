#!/usr/bin/env python3
"""Independently reduce the matched BB72 v1 SPA/BP-SF terminal ledgers."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/results/bb72-css-bp-v1"
OUTPUT = ROOT / "docs/evidence/bb72-v1-bpsf-audit.json"
VALID = {"exact", "stabilizer_equivalent"}


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _shots(path: Path, expected_digest: str) -> dict[int, dict]:
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_digest:
        raise ValueError(f"ledger digest differs from published result: {path}")
    shots: dict[int, dict] = {}
    for line in raw.splitlines():
        event = json.loads(line)
        shot = shots.setdefault(event["shot_id"], {})
        if event["kind"] == "shot_begin":
            if "sample_identity" in shot:
                raise ValueError("duplicate shot beginning")
            shot["sample_identity"] = event["sample_seed_identity"]
        elif event["kind"] == "termination":
            if "terminal" in shot:
                raise ValueError("duplicate terminal")
            data = event["data"]
            shot["terminal"] = data.get("payload", data)
            shot["termination"] = event["termination"]
    if any(set(shot) != {"sample_identity", "terminal", "termination"} for shot in shots.values()):
        raise ValueError("incomplete shot evidence")
    return shots


def audit() -> dict:
    report = _read(EVIDENCE / "result.json")
    output = {"schema_version": 1, "study_id": report["study_id"],
              "design_sha256": report["design_sha256"], "rates": {}}
    for rate in ("p030", "p050", "p080"):
        root = EVIDENCE / "evaluation" / rate
        reference = _shots(root / "spa-g1000/events.jsonl", report["evaluation_ledger_sha256"][f"{rate}/spa-g1000"])
        bpsf = _shots(root / "bpsf-g1000/events.jsonl", report["evaluation_ledger_sha256"][f"{rate}/bpsf-g1000"])
        if set(reference) != set(bpsf) or len(reference) != 512:
            raise ValueError(f"paired denominator differs: {rate}")
        transitions: Counter[str] = Counter()
        gained_terms: Counter[str] = Counter()
        gained_calls: Counter[str] = Counter()
        gained_actions: Counter[str] = Counter()
        runtime_available = {"spa": 0, "bpsf": 0}
        for shot_id in sorted(reference):
            before, after = reference[shot_id], bpsf[shot_id]
            if before["sample_identity"] != after["sample_identity"]:
                raise ValueError(f"unmatched physical sample: {rate}/{shot_id}")
            a = before["terminal"]["outcome"]
            b = after["terminal"]["outcome"]
            transitions[f"{a or 'unavailable'}=>{b or 'unavailable'}"] += 1
            for name, shot in (("spa", before), ("bpsf", after)):
                measurement = shot["terminal"].get("decode_runtime")
                if isinstance(measurement, dict) and measurement.get("value") is not None:
                    runtime_available[name] += 1
            if a not in VALID and b in VALID:
                gained_terms[f"{before['termination']}=>{after['termination']}"] += 1
                gained_calls[str(after["terminal"]["work_vector"]["bp_calls"])] += 1
                gained_actions[str(after["terminal"]["work_vector"]["intervention_actions"])] += 1
        newly_valid = sum(count for pair, count in transitions.items()
                          if pair.split("=>")[0] not in VALID and pair.split("=>")[1] in VALID)
        lost_valid = sum(count for pair, count in transitions.items()
                         if pair.split("=>")[0] in VALID and pair.split("=>")[1] not in VALID)
        published = report["shared_work_view"]["contrasts"][f"{rate}/bpsf"]
        if (newly_valid, lost_valid) != (published["newly_valid"], published["lost_valid"]):
            raise ValueError(f"independent matched counts disagree: {rate}")
        output["rates"][rate] = {
            "matched_shots": len(reference), "newly_valid": newly_valid, "lost_valid": lost_valid,
            "outcome_transitions": dict(sorted(transitions.items())),
            "gained_termination_pairs": dict(sorted(gained_terms.items())),
            "gained_bp_calls": dict(sorted(gained_calls.items())),
            "gained_intervention_actions": dict(sorted(gained_actions.items())),
            "runtime_available_shots": runtime_available,
            "reported_holm_adjusted_p": published["holm_adjusted_p"],
        }
    return output


if __name__ == "__main__":
    payload = (json.dumps(audit(), indent=2, sort_keys=True) + "\n").encode()
    if OUTPUT.exists() and OUTPUT.read_bytes() != payload:
        raise ValueError("existing audit differs from verified ledgers")
    OUTPUT.write_bytes(payload)
    print(OUTPUT)
