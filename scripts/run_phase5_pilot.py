#!/usr/bin/env python3
"""Prespecified matched B1 intervention pilot with a digest-bound evaluation gate."""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bp_registry.cli import run_canonical  # noqa: E402
from bp_registry.ledger import read_canonical_events  # noqa: E402
from bp_registry.manifests import manifest_digest, preflight  # noqa: E402


CALIBRATION = ROOT / "data/manifests/phase5-b1-calibration.json"
EVALUATION = ROOT / "data/manifests/phase5-b1-mechanism-pilot.json"
ENTITLEMENT = ROOT / "docs/evidence/phase5-compute-entitlement.json"
FREEZE = ROOT / "docs/evidence/phase5-b1-cap-freeze.json"
CALIBRATION_OUTPUT = ROOT / "data/results/phase5-interventions/b1-calibration"
EVALUATION_OUTPUT = ROOT / "data/results/phase5-interventions/b1-mechanism-pilot"
ARMS = ("identity", "guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief")
B1_RAW = "3b3fb669daf18cb294049c2c20a457a2da997ad1a7da9f0667171d3b48eb38a6"
B1_SEMANTIC = "ea1200028ace4a446dc04fe40c9eb9607903b31e3772c2921835ed6e20430548"


def _bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return sha256(_bytes(value)).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object at {path}")
    return value


def _write_once(path: Path, value: object) -> None:
    serialized = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != serialized:
            raise ValueError(f"sealed evidence differs at {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def _field(value: str | None) -> dict[str, Any]:
    return {"status": "available" if value else "not_available", "value": value if value else None}


def capture_entitlement() -> dict[str, Any]:
    """Capture exposed allocation facts without inventing scheduler values."""
    if os.environ.get("OMP_NUM_THREADS") != "1":
        raise ValueError("the Phase 5 pilot requires OMP_NUM_THREADS=1")
    job_id = os.environ.get("SLURM_JOB_ID")
    output = ""
    if job_id:
        completed = subprocess.run(["scontrol", "show", "job", job_id], capture_output=True, text=True, check=True)
        output = completed.stdout
    def token(name: str) -> str | None:
        match = re.search(rf"(?:^|\s){re.escape(name)}=([^\s]+)", output)
        return match.group(1) if match else None
    record = {
        "schema_version": 1,
        "scheduler": _field("slurm" if job_id else None),
        "job_id": _field(job_id),
        "account": _field(token("Account")),
        "partition": _field(token("Partition")),
        "qos": _field(token("QOS")),
        "node_list": _field(token("NodeList")),
        "allocated_cpus": _field(token("NumCPUs")),
        "allocated_memory": _field(token("AllocTRES")),
        "walltime": _field(token("TimeLimit")),
        "omp_num_threads": 1,
        "purpose": "bounded_phase5_b1_mechanism_pilot",
    }
    _write_once(ENTITLEMENT, record)
    return record


def _stage(path: Path, *, stage: str) -> dict[str, Any]:
    design = _read(path)
    if design.get("schema_version") != 1 or design.get("stage") != stage:
        raise ValueError("Phase 5 pilot stage schema or stage is wrong")
    if tuple(design.get("arm_order", ())) != ARMS or set(design.get("arm_manifests", {})) != set(ARMS):
        raise ValueError("Phase 5 pilot requires exactly the baseline and six single arms")
    expected_shots = list(range(4 if stage == "calibration" else 16))
    if design.get("shot_ids") != expected_shots or design.get("error_rate") != 0.07:
        raise ValueError("Phase 5 pilot has the wrong fixed sample design")
    if design.get("assessment_status") != "not_assessed":
        raise ValueError("Phase 5 pilot assessment status must remain not_assessed")
    for arm in ARMS:
        candidate = design["arm_manifests"][arm]
        parsed = preflight(candidate).manifest
        if (candidate["policies"]["intervention"]["kind"] != arm
                or parsed.intervention.kind != arm
                or parsed.artifact.code_id != "b1-ghp-882"
                or parsed.artifact.raw_sha256 != B1_RAW
                or parsed.artifact.semantic_sha256 != B1_SEMANTIC
                or parsed.evidence.relation != "pilot_adaptation"
                or parsed.evidence.assessment_status != "not_assessed"
                or parsed.randomness.physical_sample_identity != design["physical_sample_identity"]
                or parsed.randomness.sample_seed != design["sample_seed"]
                or parsed.budgets.max_shots != len(expected_shots)
                or parsed.error_rate != 0.07):
            raise ValueError(f"Phase 5 {arm} manifest is incompatible with the matched B1 design")
    return design


def _evaluation_projection(calibration: dict[str, Any]) -> dict[str, Any]:
    design = deepcopy(calibration)
    design["stage"] = "evaluation"
    design["shot_ids"] = list(range(16))
    design["physical_sample_identity"] = "phase5-b1-evaluation-physical-v1"
    design["design_status"] = "sealed_after_objective_calibration"
    for arm in ARMS:
        manifest = design["arm_manifests"][arm]
        manifest["run_id"] = f"phase5-b1-evaluation-{arm}"
        manifest["randomness"]["physical_sample_identity"] = design["physical_sample_identity"]
        manifest["randomness"]["decoder_seed_identity"] = "phase5-b1-evaluation-decoder-v1"
        manifest["budgets"]["max_shots"] = 16
        if manifest["intervention"].get("root_seed") is not None:
            manifest["intervention"]["root_seed"] = "phase5-b1-evaluation-decoder-v1"
        manifest["evidence"]["procedure"] = f"Prespecified Phase 5 B1 evaluation, {arm}; mechanism only."
    return design


def _run_stage(design: dict[str, Any], output: Path) -> dict[str, Any]:
    if os.environ.get("OMP_NUM_THREADS") != "1":
        raise ValueError("Phase 5 pilot requires one OpenMP thread")
    output.mkdir(parents=True, exist_ok=True)
    arm_rows: dict[str, Any] = {}
    all_events: list[str] = []
    sample_ids: dict[int, str] = {}
    for arm in ARMS:
        arm_root = output / arm
        arm_root.mkdir(exist_ok=True)
        manifest_path = arm_root / "manifest.json"
        _write_once(manifest_path, design["arm_manifests"][arm])
        run_canonical(manifest_path, arm_root)
        # run_canonical reconstructs its result through validate_canonical_shot
        # for every terminal.  A second verify_run here would replay the same
        # bounded B1 controller work without adding a distinct gate.
        events = read_canonical_events(arm_root / "events.jsonl")
        begins = {row["shot_id"]: row for row in events if row["kind"] == "shot_begin"}
        if sorted(begins) != design["shot_ids"]:
            raise ValueError(f"{arm} has an incomplete shot_begin set")
        for shot_id, event in begins.items():
            sample_id = event["sample_seed_identity"]
            previous = sample_ids.setdefault(shot_id, sample_id)
            if previous != sample_id:
                raise ValueError("matched arms do not share the same physical sample identity")
        arm_rows[arm] = {
            "manifest_sha256": manifest_digest(preflight(design["arm_manifests"][arm]).manifest),
            "shot_ids": sorted(begins),
            "terminal_count": sum(row["kind"] == "termination" for row in events),
            "work_event_count": sum(row["kind"] == "work" for row in events),
        }
        all_events.extend((arm_root / "events.jsonl").read_text(encoding="utf-8").splitlines())
    aggregate_ledger = output / "events.jsonl"
    ledger_text = "\n".join(all_events) + "\n"
    if aggregate_ledger.exists() and aggregate_ledger.read_text(encoding="utf-8") != ledger_text:
        raise ValueError("aggregate pilot ledger conflicts with verified arm evidence")
    aggregate_ledger.write_text(ledger_text, encoding="utf-8")
    result = {
        "schema_version": 1, "stage": design["stage"],
        "code_id": "b1-ghp-882", "relation": "pilot_adaptation",
        "assessment_status": "not_assessed", "error_rate": 0.07,
        "arm_order": list(ARMS), "shot_ids": design["shot_ids"],
        "physical_sample_identities": {str(k): sample_ids[k] for k in sorted(sample_ids)},
        "arm_evidence": arm_rows, "ledger_sha256": sha256(aggregate_ledger.read_bytes()).hexdigest(),
        "design_digest": _digest(design),
        "statistical_claim": "not_assessed; bounded mechanism pilot only",
    }
    _write_once(output / "result.json", result)
    return result


def calibrate() -> dict[str, Any]:
    if not ENTITLEMENT.exists():
        raise ValueError("calibration requires scheduler entitlement evidence")
    design = _stage(CALIBRATION, stage="calibration")
    return _run_stage(design, CALIBRATION_OUTPUT)


def freeze_caps() -> dict[str, Any]:
    if not ENTITLEMENT.exists() or not (CALIBRATION_OUTPUT / "result.json").exists():
        raise ValueError("cap freeze requires entitlement and four-shot calibration")
    design = _stage(CALIBRATION, stage="calibration")
    calibration_result = _read(CALIBRATION_OUTPUT / "result.json")
    if calibration_result.get("design_digest") != _digest(design) or calibration_result.get("shot_ids") != list(range(4)):
        raise ValueError("calibration result does not match the prespecified design")
    if EVALUATION_OUTPUT.exists():
        raise ValueError("evaluation evidence exists before the objective cap freeze")
    projection = _evaluation_projection(design)
    if projection["physical_sample_identity"] == design["physical_sample_identity"]:
        raise ValueError("calibration and evaluation sample namespaces overlap")
    for arm in ARMS:
        before = design["arm_manifests"][arm]
        after = projection["arm_manifests"][arm]
        if before["intervention_limits"] != after["intervention_limits"] or before["budgets"]["attempt"] != after["budgets"]["attempt"]:
            raise ValueError("evaluation controls changed after calibration")
    freeze = {
        "schema_version": 1, "status": "frozen_before_evaluation",
        "b1_raw_sha256": B1_RAW, "b1_semantic_sha256": B1_SEMANTIC,
        "calibration_design_digest": _digest(design),
        "calibration_result_sha256": sha256((CALIBRATION_OUTPUT / "result.json").read_bytes()).hexdigest(),
        "calibration_ledger_sha256": sha256((CALIBRATION_OUTPUT / "events.jsonl").read_bytes()).hexdigest(),
        "entitlement_sha256": sha256(ENTITLEMENT.read_bytes()).hexdigest(),
        "evaluation_design_digest": _digest(projection),
        "calibration_physical_sample_identity": design["physical_sample_identity"],
        "evaluation_physical_sample_identity": projection["physical_sample_identity"],
        "arm_order": list(ARMS), "calibration_shot_ids": list(range(4)),
        "evaluation_shot_ids": list(range(16)),
        "caps_source": "prespecified_calibration_manifest; no outcome-conditioned tuning",
        "assessment_status": "not_assessed",
    }
    _write_once(FREEZE, freeze)
    sealed = dict(projection)
    sealed["cap_freeze_digest"] = _digest(freeze)
    _write_once(EVALUATION, sealed)
    return freeze


def self_audit() -> dict[str, Any]:
    freeze = _read(FREEZE)
    calibration = _stage(CALIBRATION, stage="calibration")
    evaluation = _read(EVALUATION)
    digest = evaluation.pop("cap_freeze_digest", None)
    if digest != _digest(freeze) or _digest(evaluation) != freeze["evaluation_design_digest"]:
        raise ValueError("evaluation design and cap freeze digests do not agree")
    if sha256(ENTITLEMENT.read_bytes()).hexdigest() != freeze["entitlement_sha256"]:
        raise ValueError("scheduler entitlement changed after freeze")
    if sha256((CALIBRATION_OUTPUT / "result.json").read_bytes()).hexdigest() != freeze["calibration_result_sha256"]:
        raise ValueError("calibration result changed after freeze")
    if sha256((CALIBRATION_OUTPUT / "events.jsonl").read_bytes()).hexdigest() != freeze["calibration_ledger_sha256"]:
        raise ValueError("calibration event ledger changed after freeze")
    if calibration["physical_sample_identity"] == evaluation["physical_sample_identity"]:
        raise ValueError("calibration and evaluation sample identities overlap")
    _stage(EVALUATION, stage="evaluation")
    return {"status": "passed", "cap_freeze_digest": _digest(freeze),
            "calibration_shots": 4, "evaluation_shots": 16, "arms": list(ARMS)}


def evaluate() -> dict[str, Any]:
    self_audit()
    return _run_stage(_stage(EVALUATION, stage="evaluation"), EVALUATION_OUTPUT)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-entitlement", action="store_true")
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--freeze-caps", action="store_true")
    parser.add_argument("--self-audit", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error("choose at least one stage")
    result: dict[str, Any] = {}
    if args.preflight_entitlement:
        result["entitlement"] = capture_entitlement()
    if args.calibrate:
        result["calibration"] = calibrate()
    if args.freeze_caps:
        result["freeze"] = freeze_caps()
    if args.self_audit:
        result["self_audit"] = self_audit()
    if args.evaluate:
        result["evaluation"] = evaluate()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
