#!/usr/bin/env python3
"""Matched active-memory CSS agreement benchmark against exact author v0.2.2."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any, Mapping

import numpy as np
from scipy.stats import beta

import run_phase4_low_noise_ler as low
import run_phase4_pilots as pilot

from bp_registry.canonical.memory import MemoryAssignmentSpec
from bp_registry.canonical.schedules import EdgeTable
from bp_registry.native.relay_v022 import RelayV022Adapter


ROOT = Path(__file__).resolve().parents[1]
LOOKS = (32, 64, 128)
AUTHOR_PIN = "relay-v0.2.2@14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
PUBLIC_BOUNDARY = 900
METRICS = ("all_shot_success", "diagnostic_cell", "exact_candidate", "syndrome_validity")


def validate_design(design: Mapping[str, Any]) -> None:
    if design.get("schema_version") != 1 or design.get("status") != "frozen_before_sampling":
        raise ValueError("agreement design must be frozen before sampling")
    if design.get("author_source_pin") != AUTHOR_PIN:
        raise ValueError("agreement design lacks the approved author pin")
    expected = [
        {"code_id": "gross-bb-144", "error_rate": .07, "work_profile": "full31", "total_legs": 31},
        {"code_id": "b1-ghp-882", "error_rate": .07, "work_profile": "b1_three_leg", "total_legs": 3},
        {"code_id": "hgp-gallager-3-4-seed-20260923", "error_rate": .03, "work_profile": "full31", "total_legs": 31},
    ]
    if design.get("code_rates") != expected or design.get("sampling", {}).get("looks") != list(LOOKS):
        raise ValueError("agreement design code/rate grid or finite look schedule drifted")
    controls = design.get("controls", {})
    if (controls.get("canonical_preset") != "source_procedure"
            or controls.get("native_decoder_class") != "RelayDecoderF64"
            or controls.get("first_leg_gamma") != .125
            or controls.get("later_leg_gamma_interval") != [-.375, .875]
            or controls.get("first_leg_iterations") != 80
            or controls.get("later_leg_iterations") != 60
            or controls.get("solution_limit") != 1
            or controls.get("stopping_criterion") != "nconv"):
        raise ValueError("agreement design controlled settings drifted")
    resources = design.get("resources", {})
    if (resources.get("workers") != 8 or resources.get("public_canonical_boundary_seconds") != PUBLIC_BOUNDARY
            or resources.get("native_boundary_seconds") != PUBLIC_BOUNDARY
            or resources.get("campaign_wall_seconds") != 432000):
        raise ValueError("agreement design compute boundary drifted")


def manifest_for_cell(helper: Any, cell: Mapping[str, Any], design_digest: str) -> dict[str, Any]:
    code_id, rate = cell["code_id"], cell["error_rate"]
    base = low._read(ROOT / helper.CODE_MANIFESTS[code_id])
    value = helper.build_active_manifest(
        base, arm="canonical_relay_31", preset="source_procedure", error_rate=rate,
        first_leg_gamma=.125, later_center=.25, later_width=1.25,
        seed_identity=f"phase4-active-v4-{code_id}-source_procedure-p{rate:.3f}",
        work_profile=cell["work_profile"],
    )
    value["budgets"]["max_shots"] = LOOKS[-1]
    value["run_id"] += "-author-v022-agreement-v1"
    value["evidence"]["procedure"] += f" Matched exact-author agreement design sha256:{design_digest}."
    value["evidence"]["discrepancies"].append(
        "The exact author native F64 backend and canonical source-policy backend can differ numerically; this is a controlled CSS adaptation."
    )
    return value


def explicit_gammas(manifest: Mapping[str, Any], observation: Mapping[str, Any], *, later_legs: int) -> tuple[np.ndarray, list[str]]:
    """Reconstruct canonical PCG64 assignments without hidden error data."""
    check = np.asarray(observation["check_matrix"], dtype=np.uint8)
    graph_sha256 = EdgeTable.from_check_matrix(check).graph_sha256
    seed_identity = manifest["relay"]["memory_tuning"]["seed_identity"]
    assignment = MemoryAssignmentSpec(
        mode="uniform", graph_sha256=graph_sha256,
        root_seed_identity=sha256(seed_identity.encode("utf-8")).hexdigest(),
        refresh_boundary="leg_start", retain_history=False, low=0.0, high=1.0,
    )
    state = assignment.initial_state(
        configuration_identity=sha256(b"relay-v022-dynamic-memory-common-draw-stream-v1").hexdigest(),
        decoder_identity=seed_identity,
    )
    sample_identity = observation["sample_identity"]
    tuning = manifest["relay"]["memory_tuning"]
    low_gamma = tuning["later_leg_center"] - tuning["later_leg_width"] / 2
    gammas, digests = [], []
    for leg_index in range(1, later_legs + 1):
        replay_identity = f"relay-memory-v022:{sample_identity}:leg:{leg_index}"
        derived = sha256(f"{state.derived_identity}:memory_assignment:{replay_identity}".encode()).hexdigest()
        rng = np.random.Generator(np.random.PCG64(int(derived[:32], 16)))
        gamma = low_gamma + tuning["later_leg_width"] * rng.uniform(0.0, 1.0, size=check.shape[1])
        gammas.append(gamma)
        digests.append(sha256(np.asarray(gamma, dtype="<f8").tobytes()).hexdigest())
    return np.asarray(gammas, dtype=np.float64), digests


def _native_runner(source: Path, environment: Path, shot_root: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Call only the isolated, commit-verified author binding; retain input digest."""
    serializable = {
        **payload,
        "check_matrix": np.asarray(payload["check_matrix"], dtype=np.uint8).tolist(),
        "syndrome": np.asarray(payload["syndrome"], dtype=np.uint8).tolist(),
        "error_priors": np.asarray(payload["error_priors"], dtype=np.float64).tolist(),
        "relay_settings": {
            **payload["relay_settings"],
            "explicit_gammas": np.asarray(payload["relay_settings"]["explicit_gammas"], dtype=np.float64).tolist(),
        },
    }
    payload_path = shot_root / "native-payload.json"
    low._atomic(payload_path, serializable)
    payload_digest = sha256(payload_path.read_bytes()).hexdigest()
    program = r'''
import json, os
from pathlib import Path
import numpy as np
import relay_bp
from relay_bp.bp import RelayDecoderF64
payload = json.loads(Path(os.environ["RELAY_V022_PAYLOAD_PATH"]).read_text(encoding="utf-8"))
settings = dict(payload["relay_settings"])
settings["explicit_gammas"] = np.ascontiguousarray(settings["explicit_gammas"], dtype=np.float64)
settings["gamma_dist_interval"] = tuple(settings["gamma_dist_interval"])
decoder = RelayDecoderF64(
    np.asarray(payload["check_matrix"], dtype=np.uint8),
    np.asarray(payload["error_priors"], dtype=np.float64), **settings,
)
result = decoder.decode_detailed(np.asarray(payload["syndrome"], dtype=np.uint8))
print(json.dumps({
    "candidate": np.asarray(result.decoding, dtype=np.uint8).tolist(),
    "success": bool(result.success),
    "aggregate_iterations": int(result.iterations),
    "module_origin": str(Path(relay_bp.__file__).resolve()),
}))
'''
    try:
        command = subprocess.run(
            [str(environment / "bin/python"), "-c", program], cwd=source, text=True,
            capture_output=True, timeout=PUBLIC_BOUNDARY,
            env={**os.environ, "PYTHONNOUSERSITE": "1", "RELAY_V022_PAYLOAD_PATH": str(payload_path)},
        )
    finally:
        payload_path.unlink(missing_ok=True)
    if command.returncode:
        raise RuntimeError(f"exact author command failed: {(command.stderr or command.stdout)[-1200:]}")
    result = json.loads(command.stdout)
    module_origin = Path(result["module_origin"]).resolve()
    if not module_origin.is_relative_to(environment.resolve()):
        raise RuntimeError(f"exact author module escaped isolated environment: {module_origin}")
    result["payload_sha256"] = payload_digest
    return result


def ensure_exact_author_environment(stage_root: Path) -> tuple[Path, Path, str]:
    """Reject an inherited editable fork even if a stage-local venv exists."""
    source, environment = pilot._git_exact_source(stage_root)

    def origin() -> Path:
        command = subprocess.run(
            [str(environment / "bin/python"), "-c", "import relay_bp; print(relay_bp.__file__)"],
            cwd=source, capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONNOUSERSITE": "1", "PYTHONPATH": ""},
        )
        if command.returncode:
            raise RuntimeError(f"cannot import exact author binding: {command.stderr[-1000:]}")
        return Path(command.stdout.strip()).resolve()

    module_origin = origin()
    if not module_origin.is_relative_to(environment.resolve()):
        installed = subprocess.run(
            [str(environment / "bin/python"), "-m", "pip", "install", "--force-reinstall", "--no-deps", str(source)],
            cwd=stage_root, capture_output=True, text=True, timeout=1200,
            env={**os.environ, "PYTHONNOUSERSITE": "1", "PYTHONPATH": ""},
        )
        if installed.returncode:
            raise RuntimeError(f"exact author binding install failed: {(installed.stderr or installed.stdout)[-1200:]}")
        source, environment = pilot._git_exact_source(stage_root)
        module_origin = origin()
    if not module_origin.is_relative_to(environment.resolve()):
        raise RuntimeError(f"isolated native environment still resolves outside exact author install: {module_origin}")
    return source, environment, str(module_origin)


def _check_executed_gamma_digests(events: list[Mapping[str, Any]], shot_id: int, expected: list[str]) -> int:
    work = next((event for event in events if event.get("kind") == "work" and event.get("shot_id") == shot_id), None)
    if work is None:
        return 0
    checked = 0
    for leg in work.get("data", {}).get("relay_legs", []):
        index = leg.get("index")
        if isinstance(index, int) and index > 0:
            if index > len(expected) or leg.get("memory", {}).get("gamma_sha256") != expected[index - 1]:
                raise ValueError(f"canonical later-leg gamma digest disagrees at shot {shot_id}, leg {index}")
            checked += 1
    return checked


def _pair(*, helper: Any, manifest_path: Path, manifest: Mapping[str, Any],
          cell: Mapping[str, Any], shot_id: int, output_root: Path,
          source: Path, environment: Path, design_digest: str, script_digest: str) -> dict[str, Any]:
    shot_root = output_root / cell["code_id"] / f"shot-{shot_id:04d}"
    shot_root.mkdir(parents=True, exist_ok=True)
    result_path = shot_root / "result.json"
    if result_path.exists():
        result = low._read(result_path)
        if result.get("design_byte_sha256") != design_digest or result.get("script_byte_sha256") != script_digest:
            raise ValueError(f"retained pair identity drifted: {result_path}")
        return result
    started_path = shot_root / "started.json"
    if started_path.exists():
        started = low._read(started_path)
        if started.get("design_byte_sha256") != design_digest or started.get("script_byte_sha256") != script_digest:
            raise ValueError(f"retained interrupted pair identity drifted: {started_path}")
        result = {"schema_version": 1, "code_id": cell["code_id"], "error_rate": cell["error_rate"],
                  "shot_id": shot_id, "design_byte_sha256": design_digest,
                  "script_byte_sha256": script_digest,
                  "canonical": {"status": "incomplete_interrupted"},
                  "native": {"status": "incomplete_interrupted"},
                  "executed_gamma_digests_checked": 0,
                  "completed_at": datetime.now(timezone.utc).isoformat()}
        low._atomic(result_path, result)
        return result
    low._atomic(started_path, {
        "code_id": cell["code_id"], "error_rate": cell["error_rate"], "shot_id": shot_id,
        "design_byte_sha256": design_digest, "script_byte_sha256": script_digest,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })
    canonical: dict[str, Any]
    canonical_output = shot_root / "canonical" / "run"
    try:
        canonical = low._public_attempt(
            helper, manifest_path=manifest_path, output=canonical_output, shot_id=shot_id,
            journal_path=shot_root / "canonical-attempts.jsonl", boundary_seconds=PUBLIC_BOUNDARY)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        canonical = {"status": "incomplete_public_boundary", "failure": str(error),
                     "diagnostic_cell": "no_proposal", "selection_status": None,
                     "sample_identity": None, "diagnostic_candidate_sha256": None}
    events = helper._events(canonical_output)
    checked_gamma_digests = 0
    native: dict[str, Any]
    began = perf_counter()
    try:
        observation = helper._command(ROOT, "canonical-observation", str(manifest_path), "--shot", str(shot_id))
        if canonical.get("sample_identity") is not None and canonical["sample_identity"] != observation["sample_identity"]:
            raise ValueError("canonical and native physical sample identity diverged")
        later_legs = cell["total_legs"] - 1
        gamma_matrix, gamma_digests = explicit_gammas(manifest, observation, later_legs=later_legs)
        checked_gamma_digests = _check_executed_gamma_digests(events, shot_id, gamma_digests)
        settings = {
            "gamma0": .125, "pre_iter": 80, "num_sets": later_legs,
            "set_max_iter": 60, "gamma_dist_interval": (-.375, .875),
            "explicit_gammas": gamma_matrix, "stop_nconv": 1,
            "stopping_criterion": "nconv", "logging": False,
        }
        native_metadata: dict[str, str] = {}

        def call_author(payload: Mapping[str, Any]) -> dict[str, Any]:
            raw = _native_runner(source, environment, shot_root, payload)
            native_metadata["module_origin"] = raw["module_origin"]
            native_metadata["payload_sha256"] = raw["payload_sha256"]
            return raw

        adapter = RelayV022Adapter(
            native_runner=call_author)
        result = adapter.run(
            check_matrix=observation["check_matrix"], syndrome=observation["syndrome"],
            error_priors=observation["error_priors"], relay_settings=settings,
            seed=int(observation["decoder_seed"]), numerical_profile="f64",
        )
        candidate = result.candidate.tolist()
        classification = low.classify_diagnostic_candidate(manifest_path, shot_id=shot_id, candidate=candidate)
        native = {"status": "completed", "candidate": candidate, "success": result.success,
                  "aggregate_iterations": result.aggregate_iterations,
                  "sample_identity": observation["sample_identity"], **classification,
                  "gamma_digests": gamma_digests,
                  "native_module_origin": native_metadata["module_origin"],
                  "native_payload_sha256": native_metadata["payload_sha256"],
                  "runtime_seconds": perf_counter() - began}
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        native = {"status": "incomplete_native_unavailable", "failure": str(error),
                  "runtime_seconds": perf_counter() - began}
    result = {"schema_version": 1, "code_id": cell["code_id"], "error_rate": cell["error_rate"],
              "shot_id": shot_id, "design_byte_sha256": design_digest,
              "script_byte_sha256": script_digest, "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
              "canonical": canonical, "native": native,
              "executed_gamma_digests_checked": checked_gamma_digests,
              "completed_at": datetime.now(timezone.utc).isoformat()}
    low._atomic(result_path, result)
    return result


def _interval(disagreements: int, denominator: int, alpha: float) -> list[float] | None:
    if denominator <= 0:
        return None
    lower = 0.0 if disagreements == 0 else float(beta.ppf(alpha / 2, disagreements, denominator - disagreements + 1))
    upper = 1.0 if disagreements == denominator else float(beta.ppf(1 - alpha / 2, disagreements + 1, denominator - disagreements))
    return [lower, upper]


def summarize(pairs: list[Mapping[str, Any]], *, look: int, alpha: float) -> dict[str, Any]:
    complete = [p for p in pairs if p["canonical"].get("status") == "completed" and p["native"].get("status") == "completed"]
    missing = [p["shot_id"] for p in pairs if p not in complete]
    disagreements = Counter()
    outcomes = Counter()
    cells = {"canonical": Counter(), "native": Counter()}
    for pair in complete:
        canonical, native = pair["canonical"], pair["native"]
        c_cell, n_cell = canonical["diagnostic_cell"], native["diagnostic_cell"]
        c_success = canonical["selection_status"] == "frozen_decoder_visible_candidate" and c_cell == "valid_correct"
        n_success = native["success"] is True and n_cell == "valid_correct"
        outcomes[(c_success, n_success)] += 1
        cells["canonical"][c_cell] += 1
        cells["native"][n_cell] += 1
        disagreements["all_shot_success"] += c_success != n_success
        disagreements["diagnostic_cell"] += c_cell != n_cell
        disagreements["exact_candidate"] += canonical["diagnostic_candidate_sha256"] != native["diagnostic_candidate_sha256"]
        disagreements["syndrome_validity"] += canonical["syndrome_valid"] != native["syndrome_valid"]
    n = len(complete)
    return {
        "look_shots": look, "complete_pairs": n, "incomplete_pair_shot_ids": missing,
        "paired_success_table": {f"canonical_{int(c)}_native_{int(v)}": outcomes[(c, v)]
                                 for c in (False, True) for v in (False, True)},
        "proposal_cells": {arm: dict(counts) for arm, counts in cells.items()},
        "disagreement": {name: {"count": disagreements[name], "denominator": n,
                                "estimate": disagreements[name] / n if n else None,
                                "simultaneous_exact_interval": _interval(disagreements[name], n, alpha)}
                         for name in METRICS},
        "native_failures_or_timeouts": sum(p["native"].get("status") != "completed" for p in pairs),
        "canonical_failures_or_timeouts": sum(p["canonical"].get("status") != "completed" for p in pairs),
        "native_success_flag_with_invalid_syndrome": sum(
            p["native"].get("success") is True and p["native"].get("syndrome_valid") is False
            for p in complete),
        "executed_gamma_digests_checked": sum(p["executed_gamma_digests_checked"] for p in pairs),
    }


def run(*, design_path: Path, output_root: Path) -> dict[str, Any]:
    design_path, output_root = design_path.resolve(), output_root.resolve()
    design = low._read(design_path)
    validate_design(design)
    design_digest = sha256(design_path.read_bytes()).hexdigest()
    script_digest = sha256(Path(__file__).read_bytes()).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    identity_path = output_root / "identity.json"
    if (output_root / "result.json").exists():
        raise FileExistsError("author agreement result is terminal")
    if identity_path.exists():
        identity = low._read(identity_path)
        if identity.get("design_byte_sha256") != design_digest or identity.get("script_byte_sha256") != script_digest:
            raise ValueError("retained agreement campaign identity drifted")
    else:
        identity = {"schema_version": 1, "design_byte_sha256": design_digest,
                    "script_byte_sha256": script_digest, "author_source_pin": AUTHOR_PIN,
                    "started_at": datetime.now(timezone.utc).isoformat()}
        low._atomic(identity_path, identity)
    helper = low._helper()
    manifests: dict[str, tuple[dict[str, Any], Path]] = {}
    for cell in design["code_rates"]:
        code_id = cell["code_id"]
        manifest = manifest_for_cell(helper, cell, design_digest)
        manifest_path = output_root / code_id / "manifest.json"
        expected = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
        if manifest_path.exists():
            if manifest_path.read_text(encoding="utf-8") != expected:
                raise ValueError(f"retained agreement manifest drifted for {code_id}")
        else:
            low._atomic(manifest_path, manifest)
        preflight_path = output_root / code_id / "preflight.json"
        if not preflight_path.exists():
            low._atomic(preflight_path, helper._command(ROOT, "preflight", str(manifest_path)))
        manifests[code_id] = manifest, manifest_path
    source, environment, module_origin = ensure_exact_author_environment(output_root / "native-stage")
    source_record = pilot._source_record(ROOT)
    started = datetime.fromisoformat(identity["started_at"])
    alpha = .05 / (len(design["code_rates"]) * len(METRICS) * len(LOOKS))
    final_look = 0
    wall_exhausted = False
    with ThreadPoolExecutor(max_workers=design["resources"]["workers"]) as pool:
        for look in LOOKS:
            if (datetime.now(timezone.utc) - started).total_seconds() + 2 * PUBLIC_BOUNDARY > design["resources"]["campaign_wall_seconds"]:
                wall_exhausted = True
                break
            tasks = []
            for cell in design["code_rates"]:
                code_id = cell["code_id"]
                manifest, manifest_path = manifests[code_id]
                for shot_id in range(final_look, look):
                    tasks.append(pool.submit(
                        _pair, helper=helper, manifest_path=manifest_path, manifest=manifest,
                        cell=cell, shot_id=shot_id, output_root=output_root,
                        source=source, environment=environment,
                        design_digest=design_digest, script_digest=script_digest,
                    ))
            for task in tasks:
                task.result()
            final_look = look
            summary = {}
            for cell in design["code_rates"]:
                code_id = cell["code_id"]
                pairs = [low._read(output_root / code_id / f"shot-{shot_id:04d}" / "result.json")
                         for shot_id in range(look)]
                summary[code_id] = summarize(pairs, look=look, alpha=alpha)
            low._atomic(output_root / "progress.json", {"status": "running", "look_shots": look,
                        "codes": summary, "design_byte_sha256": design_digest,
                        "updated_at": datetime.now(timezone.utc).isoformat()})
    report = {"schema_version": 1,
              "status": "completed" if final_look == LOOKS[-1] else "inconclusive_wall_cap",
              "look_shots": final_look, "wall_exhausted": wall_exhausted,
              "design_byte_sha256": design_digest, "script_byte_sha256": script_digest,
              "author_source_pin": AUTHOR_PIN, "author_source_record_sha256": sha256((ROOT / "data/evidence/relay-v0.2.2-source.json").read_bytes()).hexdigest(),
              "author_qualification": source_record["qualification"],
              "native_source_path": str(source), "native_environment_path": str(environment),
              "native_module_origin": module_origin,
              "codes": {} if final_look == 0 else low._read(output_root / "progress.json")["codes"],
              "interval_alpha_per_code_metric_look": alpha,
              "claim_limit": design["claim_limit"],
              "finished_at": datetime.now(timezone.utc).isoformat()}
    report["result_digest"] = low._sha(report)
    low._atomic(output_root / "result.json", report)
    print(json.dumps({"status": report["status"], "look_shots": final_look,
                      "result_digest": report["result_digest"]}, sort_keys=True), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        parser.error("--run is required")
    run(design_path=args.design, output_root=args.output)
