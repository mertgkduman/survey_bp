#!/usr/bin/env python3
"""Run or replay a matched CSS BeamSearch/RelayBP controlled adaptation."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from time import perf_counter_ns

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_FILES = ("src/bp_registry/canonical/fair_legs.py", "scripts/run_fair_beam_relay_css.py")
sys.path.insert(0, str(ROOT / "src"))

from bp_registry.artifacts import load_artifact  # noqa: E402
from bp_registry.canonical.fair_legs import FairLegConfig, FairLegController  # noqa: E402
from bp_registry.evaluator import evaluate_candidate  # noqa: E402
from bp_registry.sampling import sample_shot  # noqa: E402


def _bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _design(path: Path) -> tuple[dict, FairLegConfig, object]:
    spec = _read(path)
    if spec.get("schema_version") != 1 or spec.get("study_id") != "fair-beam-relay-css-v1":
        raise ValueError("unexpected controlled-study identity")
    if spec.get("assessment_status") != "not_assessed" or spec.get("source_status") != "controlled_css_adaptation":
        raise ValueError("development study cannot claim source reproduction")
    if type(spec.get("shots")) is not int or not 1 <= spec["shots"] <= 100_000:
        raise ValueError("fixed shot denominator must be positive and bounded")
    if type(spec.get("sample_seed")) is not int or spec["sample_seed"] < 0:
        raise ValueError("sample seed must be a nonnegative integer")
    if not isinstance(spec.get("physical_sample_identity"), str) or not spec["physical_sample_identity"]:
        raise ValueError("physical sample identity is required")
    controls = FairLegConfig(**spec["controls"])
    if spec.get("damping_gammas") != [1.0, 0.5] or controls.v2c_gamma != 0.5:
        raise ValueError("matched study requires damping off (1.0) and on (0.5)")
    artifact = load_artifact(
        ROOT, spec["artifact_path"], expected_raw_sha256=spec["artifact_raw_sha256"],
        expected_semantic_sha256=spec["artifact_semantic_sha256"],
    )
    return spec, controls, artifact.code


def _outcome(code: object, hidden_x: np.ndarray, candidate: np.ndarray | None) -> str:
    if candidate is None:
        return "no_valid_candidate"
    result = evaluate_candidate(
        code, true_x=hidden_x, true_z=np.zeros_like(hidden_x),
        candidate_x=candidate, candidate_z=np.zeros_like(hidden_x),
    )
    if result.outcome == "invalid_syndrome":
        raise ValueError("decoder emitted a candidate invalid on the original CSS problem")
    return result.outcome


def _shot(spec: dict, controls: FairLegConfig, code: object, shot_id: int) -> dict:
    sample = sample_shot(
        code, shot_id=shot_id, seed=spec["sample_seed"], x_error_rate=spec["error_rate"],
        manifest_identity=spec["physical_sample_identity"],
    )
    arms = {}
    for gamma in spec["damping_gammas"]:
        label = f"g{int(round(gamma * 1000)):04d}"
        controller = FairLegController(
            code.hz, sample.observation.syndrome, error_rate=spec["error_rate"],
            config=replace(controls, v2c_gamma=gamma),
        )
        start = perf_counter_ns()
        initial = controller.initial_bp()
        initial_ns = perf_counter_ns() - start
        start = perf_counter_ns()
        beam = controller.run_beam(initial)
        beam_ns = perf_counter_ns() - start
        start = perf_counter_ns()
        relay = controller.run_relay(initial, sample_seed_identity=sample.sample_identity)
        relay_ns = perf_counter_ns() - start
        assert beam.initial is relay.initial is initial
        arms[label] = {
            "v2c_gamma": gamma,
            "initial": initial.as_evidence(), "beam": beam.as_evidence(), "relay": relay.as_evidence(),
            "outcomes": {
                "initial": _outcome(code, sample.hidden.x, initial.candidate) if initial.converged else "no_valid_candidate",
                "beam": _outcome(code, sample.hidden.x, beam.candidate),
                "relay": _outcome(code, sample.hidden.x, relay.candidate),
            },
            "runtime_ns": {"method": "time.perf_counter_ns:serial_same_process_v1",
                           "initial": initial_ns, "beam_extra": beam_ns, "relay_extra": relay_ns},
        }
    return {
        "kind": "matched_shot", "study_id": spec["study_id"], "shot_id": shot_id,
        "sample_identity": sample.sample_identity,
        "syndrome": sample.observation.syndrome.tolist(), "arms": arms,
    }


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("rb") as handle:
        for line in handle:
            if not line.endswith(b"\n"):
                raise ValueError("ledger has a partial event")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("ledger event must be an object")
            arms = value.get("arms")
            if not isinstance(arms, dict) or set(arms) != {"g1000", "g0500"}:
                raise ValueError("ledger is missing a matched damping arm")
            for arm in arms.values():
                runtime = arm.get("runtime_ns")
                if (not isinstance(runtime, dict) or runtime.get("method") != "time.perf_counter_ns:serial_same_process_v1"
                        or any(type(runtime.get(name)) is not int or runtime[name] < 0
                               for name in ("initial", "beam_extra", "relay_extra"))):
                    raise ValueError("observed runtime evidence is malformed")
            rows.append(value)
    return rows


def _deterministic(row: dict) -> dict:
    return {**row, "arms": {label: {key: value for key, value in arm.items() if key != "runtime_ns"}
                            for label, arm in row["arms"].items()}}


def execute(design_path: Path, output: Path, *, check_only: bool = False) -> dict:
    spec, controls, code = _design(design_path)
    output.mkdir(parents=True, exist_ok=True)
    frozen_design = output / "design.json"
    design_bytes = design_path.read_bytes()
    if frozen_design.exists() and frozen_design.read_bytes() != design_bytes:
        raise ValueError("study design changed after evidence began")
    if not frozen_design.exists():
        if check_only:
            raise ValueError("no frozen design to check")
        frozen_design.write_bytes(design_bytes)
    ledger = output / "events.jsonl"
    existing = _rows(ledger)
    if [row.get("shot_id") for row in existing] != list(range(len(existing))) or len(existing) > spec["shots"]:
        raise ValueError("ledger has duplicate, reordered, or out-of-range shots")
    if check_only and len(existing) != spec["shots"]:
        raise ValueError("study has not reached its fixed denominator")
    for shot_id in range(spec["shots"]):
        expected = _shot(spec, controls, code, shot_id)
        if shot_id < len(existing):
            if _deterministic(existing[shot_id]) != _deterministic(expected):
                raise ValueError(f"shot {shot_id} differs from deterministic replay")
        elif not check_only:
            with ledger.open("ab") as handle:
                handle.write(_bytes(expected))
                handle.flush()
                os.fsync(handle.fileno())
            existing.append(expected)
    if len(existing) != spec["shots"]:
        raise ValueError("study denominator is incomplete")
    result = {
        "schema_version": 1, "study_id": spec["study_id"], "assessment_status": "not_assessed",
        "implementation_sha256": {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in IMPLEMENTATION_FILES},
        "source_status": "controlled_css_adaptation", "design_sha256": sha256(design_bytes).hexdigest(),
        "ledger_sha256": sha256(ledger.read_bytes()).hexdigest(), "shots": len(existing),
        "outcomes": {label: {mode: dict(Counter(row["arms"][label]["outcomes"][mode] for row in existing))
                             for mode in ("initial", "beam", "relay")}
                     for label in ("g1000", "g0500")},
        "total_initial_c2v_updates": {
            label: sum(row["arms"][label]["initial"]["work"]["check_to_variable_updates"] for row in existing)
            for label in ("g1000", "g0500")
        },
        "total_extra_c2v_updates": {
            label: {mode: sum(row["arms"][label][mode]["extra_work"]["check_to_variable_updates"]
                              for row in existing) for mode in ("beam", "relay")}
            for label in ("g1000", "g0500")
        },
        "claim": "development fixture only; no statistical decoder ranking or source-curve reproduction",
    }
    target = output / "result.json"
    if target.exists() and _read(target) != result:
        raise ValueError("existing result differs from replayed evidence")
    if not target.exists() and not check_only:
        target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if check_only and not target.exists():
        raise ValueError("result file is missing")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--design", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(execute(args.design, args.output, check_only=args.command == "verify"), sort_keys=True))
