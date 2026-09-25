#!/usr/bin/env python3
"""Run or resume the immutable v4 active-memory Relay benchmark campaign."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


AUTHOR_PIN = "relay-v0.2.2@14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
REQUIRED_CORE_COMMITS = ("6e6ad03", "660049a")


def _helper():
    path = Path(__file__).with_name("run_phase4_active_benchmark.py")
    spec = importlib.util.spec_from_file_location("phase4_active_benchmark", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object at {path}")
    return value


def _entitlement(job_id: str) -> dict[str, object]:
    result = subprocess.run(["scontrol", "show", "job", "-o", job_id], text=True, capture_output=True, check=True)
    fields = dict(item.split("=", 1) for item in result.stdout.split() if "=" in item)
    return {"job_id": job_id, "observed_at": datetime.now(timezone.utc).isoformat(),
            "account": fields.get("Account"), "partition": fields.get("Partition"),
            "num_cpus": int(fields["NumCPUs"]), "num_tasks": int(fields["NumTasks"]),
            "cpus_per_task": int(fields["CPUs/Task"]), "alloc_tres": fields["AllocTRES"],
            "time_limit": fields["TimeLimit"], "one_worker": {"omp_num_threads": 1, "workers": 1}}


def _core_identity(root: Path) -> dict[str, object]:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
    present = []
    for commit in REQUIRED_CORE_COMMITS:
        check = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=root)
        if check.returncode == 0:
            present.append(commit)
    if tuple(present) != REQUIRED_CORE_COMMITS:
        raise RuntimeError("active campaign requires both committed active-memory core repairs")
    return {"head": head, "required_core_commits": list(REQUIRED_CORE_COMMITS)}


def _later_activations(arm: Mapping[str, Any]) -> int:
    return sum(len(attempt.get("distinct_leg_indices", [])) > 1 for attempt in arm.get("attempts", []))


def _arm_record(helper: Any, *, root: Path, base: Mapping[str, Any], output: Path,
                rate: float, preset: str, arm: str, work_profile: str = "full31") -> dict[str, object]:
    manifest = helper.build_active_manifest(base, arm="baseline" if arm == "baseline" else "canonical_relay_31",
                                            preset=preset, error_rate=rate, first_leg_gamma=.125,
                                            later_center=.25, later_width=1.25,
                                            seed_identity=f"phase4-active-v4-{base['artifact']['code_id']}-{preset}-p{rate:.3f}",
                                            work_profile=work_profile)
    try:
        record = helper.run_canonical_arm(root=root, manifest=manifest, output=output)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        record = {"status": "incomplete_preflight_or_setup", "failure": str(error),
                  "attempts": [], "manifest_sha256": helper._digest(manifest),
                  "sample_namespace": manifest["randomness"]["physical_sample_identity"],
                  "active_memory_verified": False}
    record["arm"] = arm
    record["active_tuning"] = manifest["relay"]["memory_tuning"]
    record["relay_controls"] = {key: manifest["relay"][key] for key in ("total_leg_limit", "first_leg_iteration_limit", "later_leg_iteration_limit", "solution_limit", "fidelity_status", "later_leg_memory")}
    record["observed_later_leg_activations"] = _later_activations(record)
    return record


def run_campaign(*, root: Path, output_path: Path, job_id: str, campaign_id: str) -> dict[str, object]:
    """Execute only the prespecified scan branches, retaining every arm journal."""
    root, output_path = root.resolve(), output_path.resolve()
    if output_path.exists():
        raise FileExistsError("refusing to overwrite a retained active campaign report")
    helper, scan_plan = _helper(), _helper().active_scan_plan()
    artifact_root = output_path.parent / "benchmark-artifacts" / campaign_id
    report: dict[str, object] = {"schema_version": 1, "status": "incomplete", "campaign_id": campaign_id,
        "core_commits": list(REQUIRED_CORE_COMMITS), "core_identity": _core_identity(root), "author_source_pin": AUTHOR_PIN,
        "entitlement": _entitlement(job_id), "scan_plan": scan_plan, "scan_plan_digest": _digest(scan_plan),
        "artifact_root": str(artifact_root.relative_to(root)), "codes": {},
        "native": {"status": "native_rerun_required", "reason": "no retained byte-exact public observation digests were supplied"},
        "no_retry_policy": "Started shots remain terminal/incomplete evidence; resume never replaces an identified attempt."}
    for code_id, relative in helper.CODE_MANIFESTS.items():
        base = _read(root / relative)
        code: dict[str, object] = {"rates": {}, "selected_rate": None, "selection_status": "inconclusive"}
        selected: float | None = None
        for rate in scan_plan["codes"][code_id]["rates"]:
            rate_key = f"p{rate:.3f}".replace(".", "")
            scan = _arm_record(helper, root=root, base=base, output=artifact_root / code_id / rate_key / "canonical_default" / "controlled-relay-31",
                               rate=rate, preset="canonical_default", arm="controlled_relay_31")
            decision = "incomplete_scan" if scan["status"] != "completed" or not scan.get("active_memory_verified") else (
                "selected" if scan["observed_later_leg_activations"] >= 2 else "advance")
            code["rates"][rate_key] = {"error_rate": rate, "presets": {"canonical_default": {"controlled_relay_31": scan}}, "trigger_decision": decision}
            if decision == "selected":
                selected = rate
                break
            if decision == "incomplete_scan":
                break
        if selected is not None:
            selected_key = f"p{selected:.3f}".replace(".", "")
            selected_entry = code["rates"][selected_key]
            for preset in helper.PRESETS:
                for arm in ("baseline", "controlled_relay_31"):
                    if preset == "canonical_default" and arm == "controlled_relay_31":
                        continue
                    profile = "b1_three_leg" if code_id == "b1-ghp-882" and selected == .07 and arm == "controlled_relay_31" else "full31"
                    selected_entry["presets"].setdefault(preset, {})[arm] = _arm_record(
                        helper, root=root, base=base, output=artifact_root / code_id / selected_key / preset / arm,
                        rate=selected, preset=preset, arm=arm, work_profile=profile)
            code.update({"selected_rate": selected, "selection_status": "selected"})
        report["codes"][code_id] = code
    report["status"] = "completed" if all(code["selection_status"] == "selected" for code in report["codes"].values()) else "incomplete_or_inconclusive"
    report["report_digest"] = _digest(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("data/results/phase4-memory-relay/benchmark-v4-active.json"))
    parser.add_argument("--slurm-job-id")
    parser.add_argument("--campaign-id")
    args = parser.parse_args()
    if not args.run or not args.slurm_job_id or not args.campaign_id:
        parser.error("--run, --slurm-job-id, and --campaign-id are required")
    print(json.dumps(run_campaign(root=Path(__file__).resolve().parents[1], output_path=args.output,
                                  job_id=args.slurm_job_id, campaign_id=args.campaign_id), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
