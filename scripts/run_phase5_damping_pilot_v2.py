#!/usr/bin/env python3
"""Corrected matched p=0.05 B1 pilot in a new immutable v2 namespace."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bp_registry.cli import run_canonical, verify_run  # noqa: E402
from bp_registry.ledger import read_canonical_events  # noqa: E402
from bp_registry.manifests import preflight  # noqa: E402


SOURCE = ROOT / "data/manifests/phase5-b1-mechanism-pilot.json"
CAP_FREEZE = ROOT / "docs/evidence/phase5-b1-cap-freeze.json"
DESIGN = ROOT / "data/manifests/phase5-b1-p005-damping-pilot-v2.json"
OUTPUT = ROOT / "data/results/phase5-interventions/b1-p005-damping-pilot-v2"
BASE_ARMS = ("identity", "guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief")
ARMS = tuple(name for arm in BASE_ARMS for name in (arm, f"{arm}__damped"))
SHOTS = 128
GAMMA = 0.5
SAMPLE_SEED = 5012129
PHYSICAL_ID = "phase5-b1-p005-damping-physical-v2"
DECODER_ID = "phase5-b1-p005-damping-decoder-v2"
CODE_FILES = (
    "src/bp_registry/canonical/contracts.py",
    "src/bp_registry/canonical/execution.py",
    "src/bp_registry/canonical/impulse.py",
    "src/bp_registry/canonical/intervention_session.py",
    "src/bp_registry/canonical/interventions.py",
    "src/bp_registry/canonical/memory.py",
    "src/bp_registry/canonical/phase5.py",
    "src/bp_registry/canonical/restarting.py",
    "src/bp_registry/canonical/verification.py",
    "src/bp_registry/ledger.py",
    "src/bp_registry/manifests.py",
    "src/bp_registry/runner.py",
    "scripts/run_phase5_damping_pilot_v2.py",
)


def _digest_bytes(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _write_once(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"sealed artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _memory() -> dict[str, Any]:
    return {"bindings": [{
        "binding_id": "v2c-damping", "kind": "v2c_damping", "target": "v2c",
        "parameters": {"gamma": GAMMA}, "order": 0,
        "history_owner": "attempt:v2c-damping", "state_lifetime": "attempt",
        "advance_boundary": "source_iteration", "refresh_boundary": "attempt_start",
        "source_status": "canonical_adaptation", "retain_history": False,
    }]}


def build_design() -> dict[str, Any]:
    source = _read(SOURCE)
    if (source.get("error_rate") != 0.07 or source.get("assessment_status") != "not_assessed"
            or tuple(source.get("arm_order", ())) != BASE_ARMS or _read(CAP_FREEZE).get("status") != "frozen_before_evaluation"):
        raise ValueError("source pilot or objective cap freeze is not the expected retained evidence")
    manifests: dict[str, Any] = {}
    for arm in BASE_ARMS:
        for damped in (False, True):
            key = f"{arm}__damped" if damped else arm
            manifest = deepcopy(source["arm_manifests"][arm])
            manifest["schema_version"] = 6 if damped else 5
            manifest["memory"] = _memory() if damped else None
            manifest["run_id"] = f"phase5-b1-p005-{key}-v2"
            manifest["error_rate"] = 0.05
            manifest["budgets"]["max_shots"] = SHOTS
            manifest["randomness"].update({
                "sample_seed": SAMPLE_SEED, "physical_sample_identity": PHYSICAL_ID,
                "decoder_seed_identity": DECODER_ID,
            })
            if manifest["intervention"].get("root_seed") is not None:
                manifest["intervention"]["root_seed"] = DECODER_ID
            manifest["evidence"]["procedure"] = (
                f"Corrected matched p=0.05 B1 mechanism pilot v2; {arm}; "
                f"V2C damping gamma={GAMMA} at each fresh BP attempt." if damped else
                f"Corrected matched p=0.05 B1 mechanism pilot v2; {arm}; memory disabled."
            )
            manifest["evidence"]["discrepancies"].append(
                "The p=0.05 paired damping pilot is a controlled composition adaptation, not source-curve reproduction."
            )
            parsed = preflight(manifest).manifest
            if parsed.intervention.kind != arm or parsed.budgets.max_shots != SHOTS or parsed.error_rate != 0.05:
                raise ValueError(f"invalid paired manifest for {key}")
            manifests[key] = manifest
    return {
        "schema_version": 1, "stage": "matched_mechanism_pilot", "code_id": "b1-ghp-882",
        "error_rate": 0.05, "assessment_status": "not_assessed",
        "relation": "pilot_adaptation", "question": "Which bounded Phase 5 mechanisms remain available at p=0.05, and how do their attempts and typed work change under V2C damping?",
        "claim_limit": "No decoder ranking, statistical reproduction, or source-curve agreement claim.",
        "stop_rule": "fixed 128 matched physical samples; retain every terminal class",
        "shot_ids": list(range(SHOTS)), "sample_seed": SAMPLE_SEED,
        "physical_sample_identity": PHYSICAL_ID, "decoder_seed_identity": DECODER_ID,
        "damping_gamma": GAMMA, "damping_equation": "v2c=(1-gamma)*previous_committed_damped+gamma*current_fresh; reset to channel prior per attempt",
        "supersedes_invalid_run": "phase5-b1-p005-damping-pilot-v1; incorrect damping history and BP-SF/Restart source semantics",
        "arm_order": list(ARMS), "arm_manifests": manifests,
        "source_design_sha256": _digest_bytes(SOURCE),
        "source_cap_freeze_sha256": _digest_bytes(CAP_FREEZE),
        "implementation_sha256": {name: _digest_bytes(ROOT / name) for name in CODE_FILES},
    }


@lru_cache(maxsize=1)
def sealed_design() -> dict[str, Any]:
    saved = _read(DESIGN)
    if saved != build_design():
        raise ValueError("saved design differs from the prespecified source projection")
    return saved


def run_arm(key: str) -> tuple[str, list[str], dict[int, str]]:
    if os.environ.get("OMP_NUM_THREADS") != "1":
        raise ValueError("paired intervention pilot requires OMP_NUM_THREADS=1")
    design = sealed_design()
    arm_root = OUTPUT / key
    manifest_path = arm_root / "manifest.json"
    _write_once(manifest_path, _json_bytes(design["arm_manifests"][key]))
    # run_canonical resumes completed durable shots and writes a result only
    # after every shot has been replayed by the public structural verifier.
    run_canonical(manifest_path, arm_root)
    events = read_canonical_events(arm_root / "events.jsonl")
    starts = {event["shot_id"]: event["sample_seed_identity"] for event in events if event["kind"] == "shot_begin"}
    if sorted(starts) != design["shot_ids"]:
        raise ValueError(f"{key} has an incomplete or duplicate physical sample set")
    print(f"completed {key}: {len(starts)} replayed shots", flush=True)
    return key, (arm_root / "events.jsonl").read_text(encoding="utf-8").splitlines(), starts


def run() -> dict[str, Any]:
    design = sealed_design()
    if os.environ.get("OMP_NUM_THREADS") != "1":
        raise ValueError("paired intervention pilot requires OMP_NUM_THREADS=1")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    available = int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1))
    with ProcessPoolExecutor(max_workers=min(len(ARMS), available)) as pool:
        completed = dict((key, (lines, starts)) for key, lines, starts in pool.map(run_arm, ARMS))
    samples: dict[int, str] = {}
    aggregate: list[str] = []
    arm_results: dict[str, Any] = {}
    for key in ARMS:
        lines, starts = completed[key]
        for shot_id, sample_id in starts.items():
            if samples.setdefault(shot_id, sample_id) != sample_id:
                raise ValueError("paired arms used different physical samples")
        aggregate.extend(lines)
        arm_result = _read(OUTPUT / key / "result.json")
        arm_results[key] = {
            "manifest_sha256": arm_result["manifest_sha256"],
            "ledger_sha256": arm_result["ledger_sha256"],
            "denominators": arm_result["denominators"],
            "terminations": arm_result["terminations"],
        }
    ledger = OUTPUT / "events.jsonl"
    _write_once(ledger, ("\n".join(aggregate) + "\n").encode("utf-8"))
    result = {
        "schema_version": 1, "design_sha256": _digest_bytes(DESIGN),
        "ledger_sha256": _digest_bytes(ledger), "code_id": "b1-ghp-882",
        "error_rate": 0.05, "assessment_status": "not_assessed",
        "relation": "pilot_adaptation", "shot_ids": design["shot_ids"],
        "arm_order": design["arm_order"], "physical_sample_identities": {str(k): samples[k] for k in sorted(samples)},
        "arm_results": arm_results,
        "statistical_claim": "not_assessed; fixed matched mechanism pilot only",
    }
    _write_once(OUTPUT / "result.json", _json_bytes(result))
    return result


def verify() -> dict[str, Any]:
    design = sealed_design()
    result = _read(OUTPUT / "result.json")
    if result["design_sha256"] != _digest_bytes(DESIGN) or result["ledger_sha256"] != _digest_bytes(OUTPUT / "events.jsonl"):
        raise ValueError("paired result design or aggregate ledger digest differs")
    aggregate: list[str] = []
    samples: dict[int, str] = {}
    for key in ARMS:
        arm_root = OUTPUT / key
        if _read(arm_root / "manifest.json") != design["arm_manifests"][key]:
            raise ValueError(f"{key} saved manifest drifted")
        verify_run(arm_root)
        arm_result = _read(arm_root / "result.json")
        if arm_result["ledger_sha256"] != result["arm_results"][key]["ledger_sha256"]:
            raise ValueError(f"{key} public result digest drifted")
        lines = (arm_root / "events.jsonl").read_text(encoding="utf-8").splitlines()
        aggregate.extend(lines)
        for event in (json.loads(line) for line in lines if line):
            if event["kind"] == "shot_begin":
                shot_id, sample_id = event["shot_id"], event["sample_seed_identity"]
                if samples.setdefault(shot_id, sample_id) != sample_id:
                    raise ValueError("paired physical sample mismatch")
    if ("\n".join(aggregate) + "\n").encode("utf-8") != (OUTPUT / "events.jsonl").read_bytes():
        raise ValueError("aggregate ledger differs from its arm evidence")
    if sorted(samples) != design["shot_ids"] or {str(k): v for k, v in samples.items()} != result["physical_sample_identities"]:
        raise ValueError("paired sample identity set is incomplete")
    return {"status": "passed", "shots": len(samples), "arms": len(ARMS), "ledger_sha256": result["ledger_sha256"]}


def report() -> str:
    result = _read(OUTPUT / "result.json")
    rows = []
    for key in ARMS:
        d = Counter(result["arm_results"][key]["denominators"])
        rows.append(f"| {key} | {d['exact']} | {d['stabilizer_equivalent']} | {d['logical_failure']} | {d['outcome_unavailable']} |")
    return "\n".join([
        "# Corrected v2 matched B1 p=0.05 intervention and damping pilot", "",
        "Fixed 128 physical samples per arm; 14 arms; V2C damping gamma=0.5. All outcomes include all terminal shots.",
        "This is a `pilot_adaptation` with assessment `not_assessed`. Counts are descriptive and do not rank decoders or reproduce a source curve.",
        "", "| Arm | Exact | Stabilizer equivalent | Logical failure | Unavailable |",
        "| --- | ---: | ---: | ---: | ---: |", *rows, "",
        "See `result.json`, each arm's `manifest.json` and `events.jsonl`, and the aggregate ledger for complete attempts and typed work.", "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--prepare", action="store_true")
    choices.add_argument("--run", action="store_true")
    choices.add_argument("--verify", action="store_true")
    choices.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        _write_once(DESIGN, _json_bytes(build_design()))
        print(json.dumps({"status": "prepared", "design": str(DESIGN), "sha256": _digest_bytes(DESIGN)}, sort_keys=True))
    elif args.run:
        print(json.dumps(run(), sort_keys=True))
    elif args.verify:
        print(json.dumps(verify(), sort_keys=True))
    else:
        print(report())


if __name__ == "__main__":
    main()
