#!/usr/bin/env python3
"""Run the frozen BB-144 p=.05 LER rate with four independent arm workers.

This is a compute-only amendment to the frozen two-rate design. The p=.06
rate remains owned by the original serial job. Each arm retains its own
append-only journal and public shot/verification commands.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

import run_phase4_low_noise_ler as original


ROOT = Path(__file__).resolve().parents[1]
RATE = 0.05
RATE_KEY = "p0050"


def run(*, design_path: Path, output_root: Path) -> dict[str, Any]:
    design_path, output_root = design_path.resolve(), output_root.resolve()
    design = original._read(design_path)
    original.validate_design(design)
    for commit in original.CORE_COMMITS:
        if subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                          cwd=ROOT, check=False).returncode:
            raise RuntimeError(f"required active-memory core commit missing: {commit}")
    design_digest = sha256(design_path.read_bytes()).hexdigest()
    script_digest = sha256(Path(__file__).read_bytes()).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    identity_path = output_root / "identity.json"
    result_path = output_root / "result.json"
    progress_path = output_root / "progress.json"
    if result_path.exists():
        raise FileExistsError("p=.05 parallel result is terminal")
    if identity_path.exists():
        identity = original._read(identity_path)
        if identity.get("design_byte_sha256") != design_digest or identity.get("script_byte_sha256") != script_digest:
            raise ValueError("retained parallel-run identity differs from this script or frozen design")
    else:
        identity = {
            "schema_version": 1,
            "rate": RATE,
            "design_byte_sha256": design_digest,
            "script_byte_sha256": script_digest,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "compute_amendment": "four independent arm workers; unchanged sample identities, looks, denominators, intervals, and stop rule",
        }
        original._atomic(identity_path, identity)
    started_at = datetime.fromisoformat(identity["started_at"])
    helper = original._helper()
    base = original._read(ROOT / "data/manifests/phase4-memory-relay-bb144.json")
    looks = design["precision"]["looks"]
    max_shots = looks[-1]
    alpha = (1.0 - design["precision"]["confidence"]) / (len(looks) * 2)
    paths: dict[str, tuple[Path, Path]] = {}
    rows: dict[str, dict[int, dict[str, Any]]] = {}
    for arm_name, preset, arm in original.ARMS:
        arm_root = output_root / RATE_KEY / arm_name
        manifest_path, journal_path = arm_root / "manifest.json", arm_root / "attempts.jsonl"
        manifest = original._manifest(helper, base, arm_name=arm_name, preset=preset, arm=arm,
                                      rate=RATE, design_digest=design_digest, max_shots=max_shots)
        expected = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
        if manifest_path.exists():
            if manifest_path.read_text(encoding="utf-8") != expected:
                raise ValueError(f"retained manifest drifted: {arm_name}")
        else:
            original._atomic(manifest_path, manifest)
        preflight_path = arm_root / "preflight.json"
        if not preflight_path.exists():
            original._atomic(preflight_path, helper._command(ROOT, "preflight", str(manifest_path)))
        paths[arm_name] = manifest_path, journal_path
        rows[arm_name] = original._journal(journal_path)
        for shot_id, prior in list(rows[arm_name].items()):
            if prior.get("status") == "started":
                output = arm_root / "batches" / f"{shot_id // 64:04d}" / "run"
                rows[arm_name][shot_id] = original._recover_started(
                    helper, manifest_path=manifest_path, output=output,
                    shot_id=shot_id, journal_path=journal_path, prior=prior)

    def attempt(arm_name: str, shot_id: int) -> dict[str, Any]:
        manifest_path, journal_path = paths[arm_name]
        output = output_root / RATE_KEY / arm_name / "batches" / f"{shot_id // 64:04d}" / "run"
        return original._public_attempt(
            helper, manifest_path=manifest_path, output=output,
            shot_id=shot_id, journal_path=journal_path,
            boundary_seconds=design["public_shot_boundary_seconds"])

    stop_at = None
    wall_exhausted = False
    snapshot: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=len(original.ARMS)) as pool:
        for shot_id in range(max_shots):
            if ((datetime.now(timezone.utc) - started_at).total_seconds()
                    + 4 * design["public_shot_boundary_seconds"] > design["max_campaign_wall_seconds"]):
                wall_exhausted = True
                break
            futures = {arm_name: pool.submit(attempt, arm_name, shot_id)
                       for arm_name, _preset, _arm in original.ARMS if shot_id not in rows[arm_name]}
            for arm_name, future in futures.items():
                rows[arm_name][shot_id] = future.result()
            sample_ids = {rows[arm_name][shot_id].get("sample_identity")
                          for arm_name, _preset, _arm in original.ARMS}
            if None in sample_ids or len(sample_ids) != 1:
                raise ValueError(f"matched physical samples diverged or are missing at shot {shot_id}")
            n = shot_id + 1
            if n in looks:
                snapshot = {
                    arm_name: original.summarize(
                        rows[arm_name], planned_shots=n, alpha=alpha,
                        min_failures=design["precision"]["minimum_failures"],
                        max_relative_half_width=design["precision"]["maximum_relative_half_width"],
                        no_recovery_policy=design["precision"]["no_recovery_policy"])
                    for arm_name, _preset, _arm in original.ARMS
                }
                precise = all(value["precision_met"] for value in snapshot.values())
                original._atomic(progress_path, {
                    "status": "running", "rate": RATE, "look_shots": n,
                    "design_byte_sha256": design_digest, "arms": snapshot,
                    "precision_met": precise, "updated_at": datetime.now(timezone.utc).isoformat(),
                })
                if precise:
                    stop_at = n
                    break
    if stop_at is None:
        n = min(max_shots, max((max(arm_rows, default=-1) for arm_rows in rows.values()), default=-1) + 1)
        snapshot = {
            arm_name: original.summarize(
                rows[arm_name], planned_shots=n, alpha=alpha,
                min_failures=design["precision"]["minimum_failures"],
                max_relative_half_width=design["precision"]["maximum_relative_half_width"],
                no_recovery_policy=design["precision"]["no_recovery_policy"])
            for arm_name, _preset, _arm in original.ARMS
        }
    result = {
        "schema_version": 1,
        "status": "completed_precision" if stop_at is not None else "completed_with_inconclusive",
        "rate": RATE, "look_shots": stop_at if stop_at is not None else n,
        "precision_met": stop_at is not None,
        "reason": None if stop_at is not None else "campaign_wall_cap" if wall_exhausted else "shot_cap_or_incomplete",
        "arms": snapshot, "design_byte_sha256": design_digest,
        "script_byte_sha256": script_digest, "started_at": identity["started_at"],
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "interval_alpha_per_look_and_precision_metric": alpha,
        "compute_amendment": identity["compute_amendment"],
    }
    result["result_digest"] = original._sha(result)
    original._atomic(result_path, result)
    print(json.dumps({"status": result["status"], "rate": RATE,
                      "look_shots": result["look_shots"], "result_digest": result["result_digest"]},
                     sort_keys=True), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=Path("data/evidence/phase4-low-noise-ler-design-v1.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        parser.error("--run is required")
    run(design_path=args.design, output_root=args.output)
