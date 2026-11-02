#!/usr/bin/env python3
"""Stop p=.05 duplicate work and reconcile the two frozen LER rate jobs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import run_phase4_low_noise_ler as original


def _job_present(job_id: str) -> bool:
    result = subprocess.run(["squeue", "-h", "-j", job_id], capture_output=True, text=True, check=True)
    return bool(result.stdout.strip())


def _completed_p0060(serial_root: Path) -> tuple[dict[str, Any] | None, Path | None]:
    terminal = serial_root / "result.json"
    if terminal.exists():
        report = original._read(terminal)
        rate = report.get("rates", {}).get("p0060")
        if rate is not None:
            return rate, terminal
    progress = serial_root / "progress.json"
    if progress.exists():
        report = original._read(progress)
        rate = report.get("rates", {}).get("p0060")
        if rate is not None and (rate.get("precision_met") or rate.get("look_shots") == 8192):
            return rate, progress
    return None, None


def run(*, serial_root: Path, parallel_root: Path, output_root: Path,
        serial_job_id: str, parallel_job_id: str) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "result.json"
    if report_path.exists():
        return original._read(report_path)
    handoff_path = output_root / "handoff.json"
    p0060 = None
    p0060_source = None
    while p0060 is None:
        p0060, p0060_source = _completed_p0060(serial_root)
        if p0060 is not None:
            break
        if not _job_present(parallel_job_id) and not (parallel_root / "result.json").exists():
            raise RuntimeError("parallel p=.05 job ended without a terminal report; preserving serial fallback")
        if not _job_present(serial_job_id):
            raise RuntimeError("serial p=.06 job ended without a terminal rate snapshot")
        time.sleep(15)
    assert p0060_source is not None

    # The original script proceeds directly to p=.05 after this rate. Stop it
    # now; p=.06's prespecified look snapshot already contains all four arms.
    was_present = _job_present(serial_job_id)
    if was_present:
        subprocess.run(["scancel", serial_job_id], check=True)
    original._atomic(handoff_path, {
        "serial_job_id": serial_job_id, "parallel_job_id": parallel_job_id,
        "serial_job_cancelled_after_p0060_snapshot": was_present,
        "p0060_source": str(p0060_source),
        "p0060_source_sha256": sha256(p0060_source.read_bytes()).hexdigest(),
        "p0060_look_shots": p0060["look_shots"],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })
    while not (parallel_root / "result.json").exists():
        if not _job_present(parallel_job_id):
            raise RuntimeError("parallel p=.05 job ended without a terminal report after serial handoff")
        time.sleep(15)
    p0050_path = parallel_root / "result.json"
    p0050 = original._read(p0050_path)
    serial_identity = original._read(serial_root / "identity.json")
    parallel_identity = original._read(parallel_root / "identity.json")
    if serial_identity["design_byte_sha256"] != p0050["design_byte_sha256"] or parallel_identity["design_byte_sha256"] != p0050["design_byte_sha256"]:
        raise ValueError("rate jobs disagree on the frozen design bytes")
    if p0050.get("rate") != 0.05 or set(p0050.get("arms", {})) != {name for name, _, _ in original.ARMS}:
        raise ValueError("parallel p=.05 terminal lacks its four declared arms")
    if p0060.get("error_rate") != 0.06 or set(p0060.get("arms", {})) != {name for name, _, _ in original.ARMS}:
        raise ValueError("serial p=.06 snapshot lacks its four declared arms")
    p0050_rate = {"error_rate": 0.05, "look_shots": p0050["look_shots"],
                  "arms": p0050["arms"], "precision_met": p0050["precision_met"]}
    if not p0050["precision_met"]:
        p0050_rate["reason"] = p0050["reason"]
    report = {
        "schema_version": 1,
        "status": "completed_precision" if p0060["precision_met"] and p0050["precision_met"] else "completed_with_inconclusive",
        "design_byte_sha256": p0050["design_byte_sha256"],
        "rates": {"p0060": p0060, "p0050": p0050_rate},
        "rate_sources": {
            "p0060": {"path": str(p0060_source), "byte_sha256": sha256(p0060_source.read_bytes()).hexdigest(),
                      "job_id": serial_job_id},
            "p0050": {"path": str(p0050_path), "byte_sha256": sha256(p0050_path.read_bytes()).hexdigest(),
                      "job_id": parallel_job_id},
        },
        "compute_amendment": "p=.06 serial and p=.05 four-arm parallel execution; unchanged frozen scientific design",
        "sample_matching": "same physical sample identity at each code/rate/shot across four arms",
        "claim_limit": "uncalibrated controlled CSS adaptation; no source-faithful or universal ranking claim",
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    report["result_digest"] = original._sha(report)
    original._atomic(report_path, report)
    print(json.dumps({"status": report["status"], "result_digest": report["result_digest"],
                      "looks": {key: value["look_shots"] for key, value in report["rates"].items()}},
                     sort_keys=True), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial-root", type=Path, required=True)
    parser.add_argument("--parallel-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--serial-job-id", required=True)
    parser.add_argument("--parallel-job-id", required=True)
    args = parser.parse_args()
    run(serial_root=args.serial_root.resolve(), parallel_root=args.parallel_root.resolve(),
        output_root=args.output.resolve(), serial_job_id=args.serial_job_id,
        parallel_job_id=args.parallel_job_id)
