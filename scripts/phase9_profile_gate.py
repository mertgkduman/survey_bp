"""Run or independently verify the bounded Phase 9 Yao profile tracer.

This is development evidence only.  It executes two preselected algebraic
shots through the installed public campaign command and records observed
local costs without inventing scheduler or site ceilings.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "data/studies/phase9-css-profile-tracer-v1.json"


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def _digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"profile evidence is not a regular file: {path}")
    return sha256(path.read_bytes()).hexdigest()


def _publish(path: Path, payload: object) -> None:
    raw = _json_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != raw:
            raise ValueError("profile evidence conflicts with immutable bytes")
        return
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def _campaign(*arguments: str) -> dict[str, Any]:
    environment = dict(os.environ, OMP_NUM_THREADS="1")
    process = subprocess.run(
        [sys.executable, "-m", "bp_registry.campaigns.cli", *arguments],
        cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
    )
    if process.returncode:
        raise ValueError(f"campaign command failed: {process.stdout.strip()} {process.stderr.strip()}")
    result = json.loads(process.stdout)
    if result.get("status") != "ok":
        raise ValueError("campaign command did not return a successful JSON envelope")
    return result


def _cpu_ns() -> int:
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return int((usage.ru_utime + usage.ru_stime) * 1_000_000_000)


def _measurement(value: int | None, unit: str, method: str, scope: str, support: str) -> dict[str, Any]:
    return {
        "value": value, "unit": unit, "method": method, "scope": scope,
        "producer": "scripts/phase9_profile_gate.py", "support_receipt_sha256": support,
        "status": "observed" if value is not None else "unavailable",
    }


def _artifact_index(output: Path) -> dict[str, dict[str, Any]]:
    return {
        str(path.relative_to(output)): {"sha256": _digest(path), "bytes": path.stat().st_size}
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "profile-gate.json" and not path.name.startswith(".")
    }


def run(output: Path) -> dict[str, Any]:
    if output.exists() and any(output.iterdir()):
        raise ValueError("profile output root must be empty before a measured run")
    output.mkdir(parents=True, exist_ok=True)
    design = json.loads(STUDY.read_text())
    if (design.get("label") != "development_fixture" or design.get("assessment_status") != "not_assessed"
            or design.get("preselected_sample_ids") != [0, 1]
            or design.get("publication_slurm_authorization") != "deny"):
        raise ValueError("profile design is not the frozen pre-outcome development fixture")
    manifest = ROOT / design["manifest_path"]
    policy = ROOT / design["policy_path"]
    target = ROOT / design["target_receipt_path"]
    for path, field in ((manifest, "manifest_sha256"), (policy, "policy_sha256"),
                        (target, "target_receipt_sha256")):
        if _digest(path) != design[field]:
            raise ValueError("profile source bytes differ from the frozen design")
    campaign_path = output / "campaign.json"
    _publish(campaign_path, design["campaign_document"])
    plan_root = output / "plan"
    run_root = output / "run"
    merge_root = output / "merge"
    assessment_root = output / "assessment"
    _campaign("preflight", "--campaign", str(campaign_path), "--campaign-root", str(ROOT),
              "--output-root", str(run_root))
    planned = _campaign("plan", "--campaign", str(campaign_path), "--campaign-root", str(ROOT),
                        "--output-root", str(plan_root))
    plan_path = Path(planned["artifact_path"])
    before_cpu = _cpu_ns()
    before_wall = time.monotonic_ns()
    first = _campaign("run-local", "--plan", str(plan_path), "--campaign-root", str(ROOT),
                      "--output-root", str(run_root))
    if first["campaign_state"] != "progress" or first["completed_shots"] != 1:
        raise ValueError("profile first run must retain exactly one progress shot")
    second = _campaign("run-local", "--plan", str(plan_path), "--campaign-root", str(ROOT),
                       "--output-root", str(run_root))
    execution_wall_ns = time.monotonic_ns() - before_wall
    execution_cpu_ns = _cpu_ns() - before_cpu
    if second["campaign_state"] != "cap_censored" or second["completed_shots"] != 2:
        raise ValueError("profile second run must seal the predeclared two-shot cap")
    merged = _campaign("merge", "--receipt", second["receipt_path"], "--plan", str(plan_path),
                       "--campaign-root", str(ROOT), "--output-root", str(merge_root))
    merge_path = Path(merged["artifact_path"])
    resumed = _campaign("resume", "--plan", str(plan_path), "--merge", str(merge_path),
                        "--campaign-root", str(ROOT))
    if not resumed["complete"] or resumed["exact_missing_set"]:
        raise ValueError("profile merge has incomplete frozen ordinal coverage")
    assessed = _campaign("assess", "--plan", str(plan_path), "--merge", str(merge_path),
                         "--campaign-root", str(ROOT), "--output-root", str(assessment_root))
    report_path = Path(assessed["artifact_path"])
    before_replay_cpu = _cpu_ns()
    before_replay_wall = time.monotonic_ns()
    verified = _campaign("verify", "--report", str(report_path), "--plan", str(plan_path),
                         "--merge", str(merge_path), "--campaign-root", str(ROOT))
    replay_wall_ns = time.monotonic_ns() - before_replay_wall
    replay_cpu_ns = _cpu_ns() - before_replay_cpu
    if not verified["verified"] or assessed["report"]["inverse_binomial_rate"] is not None:
        raise ValueError("profile replay does not preserve the censored no-curve assessment")
    report = assessed["report"]
    support = _digest(merge_path)
    peak_rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak_bytes = peak_rss * 1024 if sys.platform.startswith("linux") else None
    measurements = {
        "execution_wall_ns": _measurement(execution_wall_ns, "ns", "time.monotonic_ns", "two local bounded run-local commands", support),
        "execution_cpu_ns": _measurement(execution_cpu_ns, "ns", "resource.RUSAGE_CHILDREN user+system delta", "two local bounded run-local commands", support),
        "peak_rss_bytes": _measurement(peak_bytes, "bytes", "resource.RUSAGE_CHILDREN ru_maxrss (Linux KiB)", "maximum child process in fresh profile harness", support),
        "replay_wall_ns": _measurement(replay_wall_ns, "ns", "time.monotonic_ns", "independent public verify command", support),
        "replay_cpu_ns": _measurement(replay_cpu_ns, "ns", "resource.RUSAGE_CHILDREN user+system delta", "independent public verify command", support),
        "decoder_work": _measurement(report["actual_resources"]["decoder_work"], "work units", "verified canonical attempt observations", "two completed shots", support),
        "events": _measurement(report["actual_resources"]["events"], "events", "verified canonical ledgers", "two completed shots", support),
        "evidence_bytes": _measurement(report["actual_resources"]["evidence_bytes"], "bytes", "verified canonical ledgers", "two completed shots", support),
        "storage_bytes": _measurement(report["actual_resources"]["storage_bytes"], "bytes", "verified materialized sample, ledger, attempt and terminal receipts", "two completed shots", support),
    }
    unavailable = {"status": "unavailable", "reason": "No measured site ceiling or scheduler accounting supplied for this local fixture."}
    gate = {
        "schema": "phase9_css_profile_gate_v1",
        "label": "development_fixture", "assessment_status": "not_assessed",
        "study_sha256": _digest(STUDY), "manifest_sha256": _digest(manifest),
        "policy_sha256": _digest(policy), "target_receipt_sha256": _digest(target),
        "campaign_plan_sha256": _digest(plan_path),
        "merge_receipt_sha256": support, "assessment_receipt_sha256": _digest(report_path),
        "preselected_sample_ids": [0, 1], "max_local_workers": 1,
        "measurements": measurements,
        "replay": {"verified": True, "report_sha256": verified["report_sha256"],
                   "merge_content_sha256": verified["merge_receipt_sha256"]},
        "site": {name: unavailable for name in (
            "wall_ceiling", "core_ceiling", "memory_ceiling", "storage_ceiling",
            "scheduler_accounting", "scheduler_cost", "device_availability",
        )},
        "publication_slurm_authorization": "deny",
        "artifact_index": _artifact_index(output),
    }
    _publish(output / "profile-gate.json", gate)
    return gate


def verify(output: Path) -> dict[str, Any]:
    gate_path = output / "profile-gate.json"
    gate = json.loads(gate_path.read_text())
    if (gate.get("schema") != "phase9_css_profile_gate_v1"
            or gate.get("label") != "development_fixture"
            or gate.get("assessment_status") != "not_assessed"
            or gate.get("preselected_sample_ids") != [0, 1]
            or gate.get("max_local_workers") != 1
            or gate.get("publication_slurm_authorization") != "deny"):
        raise ValueError("retained profile gate has an invalid scope")
    if gate["artifact_index"] != _artifact_index(output):
        raise ValueError("retained profile artifact index differs from sealed bytes")
    if gate["study_sha256"] != _digest(STUDY):
        raise ValueError("retained profile study differs from the frozen design")
    design = json.loads(STUDY.read_text())
    for name in ("manifest", "policy", "target_receipt"):
        if gate[f"{name}_sha256"] != _digest(ROOT / design[f"{name}_path"]):
            raise ValueError("retained profile source differs from the frozen design")
    plan = output / "plan/failure-count-plan.json"
    merge = output / "merge/failure-count-merge.json"
    report = output / "assessment/failure-count-assessment.json"
    if (gate["campaign_plan_sha256"] != _digest(plan)
            or gate["merge_receipt_sha256"] != _digest(merge)
            or gate["assessment_receipt_sha256"] != _digest(report)):
        raise ValueError("retained profile receipts differ from their linked bytes")
    checked = _campaign("verify", "--report", str(report), "--plan", str(plan),
                        "--merge", str(merge), "--campaign-root", str(ROOT))
    if (not checked["verified"] or checked["report_sha256"] != gate["replay"]["report_sha256"]
            or checked["merge_receipt_sha256"] != gate["replay"]["merge_content_sha256"]):
        raise ValueError("retained profile replay differs from its measured gate")
    retained_report = json.loads(report.read_text())
    if (retained_report["assessment_status"] != "inconclusive_cap_censored"
            or retained_report["inverse_binomial_rate"] is not None
            or retained_report["total_completed_shots"] != 2):
        raise ValueError("retained profile gained an assessment or lost frozen shots")
    expected_measurements = {
        "execution_wall_ns", "execution_cpu_ns", "peak_rss_bytes",
        "replay_wall_ns", "replay_cpu_ns", "decoder_work", "events",
        "evidence_bytes", "storage_bytes",
    }
    measurements = gate["measurements"]
    if set(measurements) != expected_measurements:
        raise ValueError("retained profile measurements are incomplete")
    for name, value in measurements.items():
        if (not isinstance(value, dict) or value.get("producer") != "scripts/phase9_profile_gate.py"
                or value.get("support_receipt_sha256") != gate["merge_receipt_sha256"]
                or not isinstance(value.get("unit"), str) or not value["unit"]
                or not isinstance(value.get("method"), str) or not value["method"]
                or not isinstance(value.get("scope"), str) or not value["scope"]
                or value.get("status") not in {"observed", "unavailable"}):
            raise ValueError(f"retained profile {name} lacks source-qualified measurement metadata")
        amount = value.get("value")
        if (value["status"] == "observed" and (type(amount) is not int or amount < 0)
                or value["status"] == "unavailable" and amount is not None):
            raise ValueError(f"retained profile {name} has an invalid observed value")
    for name in ("decoder_work", "events", "evidence_bytes", "storage_bytes"):
        if measurements[name]["value"] != retained_report["actual_resources"][name]:
            raise ValueError(f"retained profile {name} differs from verified campaign costs")
    if any(measurements[name]["value"] <= 0 for name in ("execution_wall_ns", "replay_wall_ns")):
        raise ValueError("retained profile lacks positive local wall observations")
    required_site = {
        "wall_ceiling", "core_ceiling", "memory_ceiling", "storage_ceiling",
        "scheduler_accounting", "scheduler_cost", "device_availability",
    }
    if (set(gate["site"]) != required_site
            or any(not isinstance(value, dict) or value.get("status") != "unavailable"
                   or not value.get("reason") for value in gate["site"].values())):
        raise ValueError("retained profile invents a site ceiling or scheduler observation")
    return gate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    result = run(Path(args.output_root)) if args.mode == "run" else verify(Path(args.output_root))
    print(json.dumps({"status": "ok", "gate_sha256": sha256(_json_bytes(result)).hexdigest(),
                      "publication_slurm_authorization": result["publication_slurm_authorization"]}, sort_keys=True))


if __name__ == "__main__":
    main()
