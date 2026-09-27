#!/usr/bin/env python3
"""Prepare and run capped fresh Phase 4 canonical evaluation after calibration.

The selection gate is deliberately ahead of every fresh-sample operation.
Only the three arms admitted by the frozen V4 cap can be materialized.  A
terminal calibration with inconclusive presets leaves those arms unavailable.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import os
import subprocess
from time import perf_counter
from typing import Any, Mapping

import numpy as np

import run_phase4_active_benchmark as active
import run_phase4_pilots as pilot
from bp_registry.phase4_analysis import CELLS, summarize_matched_cohort, wilson_interval
from bp_registry.canonical.memory import MemoryAssignmentSpec
from bp_registry.canonical.schedules import EdgeTable
from bp_registry.native.relay_v022 import RelayV022Adapter, unavailable_native_facts


ROOT = Path(__file__).resolve().parents[1]
CAPS_PATH = ROOT / "data/manifests/phase4-pilot-caps.json"
CALIBRATION_PATH = ROOT / "data/results/phase4-memory-relay/calibration/result.json"
SELECTION_PATH = ROOT / "data/results/phase4-memory-relay/selected-settings.json"
OUTPUT = ROOT / "data/results/phase4-memory-relay/evaluation"
ARMS = ("baseline", "selected_source_procedure", "selected_canonical_procedure")
TERMINAL_CALIBRATION = frozenset({"completed", "completed_with_inconclusive", "cap_reached"})


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _digest(value: object) -> str:
    return pilot._digest(value)


def _byte_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verified_calibration_inputs(*, root: Path = ROOT, caps_path: Path = CAPS_PATH,
                                calibration_path: Path = CALIBRATION_PATH) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify terminal calibration provenance without requiring a frozen selection."""
    root, caps_path, calibration_path = (path.resolve() for path in (root, caps_path, calibration_path))
    caps = _read(caps_path)
    if caps.get("schema_version") != 4 or caps.get("caps_digest") != _digest({k: v for k, v in caps.items() if k != "caps_digest"}):
        raise ValueError("frozen V4 cap digest does not verify")
    plan = pilot.calibration_plan(root, caps)
    calibration = _read(calibration_path)
    if calibration.get("status") not in TERMINAL_CALIBRATION:
        raise ValueError("fresh evaluation is gated on terminal calibration evidence")
    if calibration.get("caps_sha256") != _byte_sha(caps_path) or calibration.get("calibration_digest") != plan["calibration_digest"]:
        raise ValueError("calibration is not bound to the frozen cap and plan")
    if calibration.get("calibration_input") != plan["calibration_input"] or calibration.get("evaluation_namespace_accessed") is not False:
        raise ValueError("calibration input drifted or fresh evaluation samples were already accessed")
    if calibration.get("result_digest") != _digest({k: v for k, v in calibration.items() if k != "result_digest"}):
        raise ValueError("terminal calibration result digest does not verify")
    return caps, calibration


def verified_inputs(*, root: Path = ROOT, caps_path: Path = CAPS_PATH,
                    calibration_path: Path = CALIBRATION_PATH,
                    selection_path: Path = SELECTION_PATH,
                    freeze_selection: bool = False) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Reject any selection or cap drift before writing/reading evaluation samples."""
    root, caps_path, calibration_path, selection_path = (
        path.resolve() for path in (root, caps_path, calibration_path, selection_path)
    )
    caps, calibration = verified_calibration_inputs(root=root, caps_path=caps_path, calibration_path=calibration_path)
    expected = pilot.select_calibration_settings(calibration)
    if set(expected["codes"]) != set(caps["codes"]):
        raise ValueError("terminal calibration does not cover every qualified code")
    if selection_path.exists():
        selection = _read(selection_path)
        if selection != expected:
            raise ValueError("frozen selected settings differ from deterministic calibration selection")
    elif freeze_selection:
        pilot._write_canonical_json_atomic(selection_path, expected)
        selection = _read(selection_path)
    else:
        raise FileNotFoundError("selected-settings.json is absent; freeze only from terminal calibration")
    return caps, calibration, selection


def _selected_candidate(selection: Mapping[str, Any], code_id: str, arm: str,
                        caps: Mapping[str, Any]) -> Mapping[str, Any] | None:
    if arm == "baseline":
        return {"id": "neutral-one-leg-baseline", "gamma0": 0.0, "later_center": 0.0, "later_width": 0.0}
    preset = "source_procedure" if arm == "selected_source_procedure" else "canonical_default"
    selected = selection["codes"][code_id]["presets"][preset]
    if selected.get("status") != "selected_finite_precision_limited":
        return None
    candidate = selected.get("candidate")
    admitted = list(caps["codes"][code_id]["coarse_candidates"]) + list(caps["codes"][code_id]["refinement_candidates"])
    if not isinstance(candidate, Mapping) or not any(candidate == frozen for frozen in admitted):
        raise ValueError(f"selected candidate is outside frozen calibration surface: {code_id}/{arm}")
    if not str(selected.get("configuration_id", "")).startswith(f"{code_id}:{preset}:"):
        raise ValueError(f"selected configuration identity does not match {code_id}/{preset}")
    return candidate


def evaluation_plan(caps: Mapping[str, Any], selection: Mapping[str, Any]) -> dict[str, Any]:
    """Expand exactly the admitted arms and per-code shot counts."""
    if tuple(caps.get("evaluation", {}).get("arms_per_code", ())) != ARMS:
        raise ValueError("evaluation arm cap drifted; shared-settings arms need a new freeze")
    cells = []
    namespaces = set()
    for code_id in sorted(caps["codes"]):
        code = caps["codes"][code_id]
        namespace = code["evaluation_namespace"]
        if not isinstance(namespace, str) or not namespace or namespace in namespaces or namespace == code["calibration_namespace"]:
            raise ValueError("fresh evaluation namespaces must be distinct from each other and calibration")
        namespaces.add(namespace)
        shots = int(code["evaluation_shots_per_arm"])
        if shots <= 0 or shots != int(caps["evaluation"]["fresh_matched_samples_per_arm_by_code"][code_id]):
            raise ValueError("evaluation shot count drifted")
        work = code["per_shot_work_cap"]
        if code_id == "b1-ghp-882" and (work["bp_calls"] != 3 or work["relay_transfers"] != 2):
            raise ValueError("B1 evaluation must retain the bounded three-leg work envelope")
        for arm in ARMS:
            candidate = _selected_candidate(selection, code_id, arm, caps)
            cells.append({"code_id": code_id, "arm": arm,
                          "status": "ready" if candidate is not None else "unavailable_inconclusive_selection",
                          "candidate": None if candidate is None else dict(candidate),
                          "sample_namespace": namespace, "shots": shots,
                          "error_rate": float(code["central_error_rate"]),
                          "public_boundary_seconds": int(code["canonical_public_boundary_seconds"]),
                          "work_cap": dict(work)})
    return {"schema_version": 1, "status": "frozen_selection_ready",
            "caps_digest": caps["caps_digest"], "selected_settings_digest": _digest(selection),
            "cells": cells,
            "shared_settings_view": {"status": "not_admitted_by_current_v4_evaluation_arm_cap",
                                     "candidate_selection_retained": True,
                                     "required_action": "versioned presampling cap amendment before any shared-settings fresh shot"}}


def build_manifest(*, base: Mapping[str, Any], cell: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    if cell.get("status") != "ready" or cell.get("arm") not in ARMS:
        raise ValueError("cannot materialize an unavailable or undeclared evaluation arm")
    arm = str(cell["arm"])
    preset = "source_procedure" if arm == "selected_source_procedure" else "canonical_default"
    candidate = cell["candidate"]
    seed_identity = _digest({"purpose": "phase4-evaluation-matched-draw-stream-v1",
                             "namespace": cell["sample_namespace"]})
    value = active.build_active_manifest(
        base, arm="baseline" if arm == "baseline" else "canonical_relay_31",
        preset=preset, error_rate=float(cell["error_rate"]),
        first_leg_gamma=float(candidate["gamma0"]), later_center=float(candidate["later_center"]),
        later_width=float(candidate["later_width"]), seed_identity=seed_identity,
        work_profile="b1_three_leg" if cell["code_id"] == "b1-ghp-882" else "full31",
    )
    if value["artifact"]["code_id"] != cell["code_id"]:
        raise ValueError("base code and evaluation cell differ")
    value["run_id"] = "phase4-evaluation-" + _digest({"cell": cell, "selection": plan["selected_settings_digest"]})[:24]
    value["randomness"]["physical_sample_identity"] = cell["sample_namespace"]
    value["randomness"]["decoder_seed_identity"] = seed_identity
    value["budgets"]["max_shots"] = int(cell["shots"])
    for scope in ("shot", "search", "attempt"):
        value["budgets"][scope]["work_limits"] = dict(cell["work_cap"])
    if arm == "baseline":
        # A zero affine coefficient is neutral; one leg prevents transfer.
        value["relay"]["memory_tuning"]["first_leg_gamma"] = 0.0
    value["evidence"]["procedure"] += (
        f" Fresh Phase 4 evaluation arm={arm}; frozen selection digest={plan['selected_settings_digest']};"
        f" frozen cap digest={plan['caps_digest']}."
    )
    value["evidence"]["discrepancies"].append(
        "Finite controlled CSS adaptation; no circuit reproduction, publication curve, or universal ranking claim."
    )
    return value


def classify_candidate(manifest_path: Path, *, shot_id: int, candidate: object) -> dict[str, Any]:
    """Evaluate syndrome and logical projection from original hidden truth after decoding."""
    if candidate is None:
        return {"diagnostic_cell": "no_proposal", "syndrome_valid": None,
                "logical_projection_correct": None, "candidate_sha256": None}
    from bp_registry.runner import canonical_public_shot_context
    context = canonical_public_shot_context(manifest_path, shot_id=shot_id)
    if context.code is None or context.hidden_truth is None:
        raise ValueError("independent CSS truth is absent")
    code = context.code.validate()
    if code.lz is None:
        raise ValueError("qualified CSS code lacks pinned LZ")
    proposed = np.asarray(candidate)
    if proposed.shape != (code.n,) or not np.issubdtype(proposed.dtype, np.integer) or np.any((proposed != 0) & (proposed != 1)):
        raise ValueError("candidate must be a pinned-length binary X vector")
    proposed = proposed.astype(np.uint8, copy=True)
    syndrome_valid = bool(np.array_equal((code.hz.astype(np.int64) @ proposed.astype(np.int64)) % 2,
                                         np.asarray(context.syndrome, dtype=np.uint8)))
    residual = context.hidden_truth.x.astype(np.uint8) ^ proposed
    logical_correct = not bool(np.any((residual.astype(np.int64) @ code.lz.astype(np.int64).T) % 2))
    return {"diagnostic_cell": ("valid_" if syndrome_valid else "invalid_") +
            ("correct" if logical_correct else "wrong_logical"),
            "syndrome_valid": syndrome_valid, "logical_projection_correct": logical_correct,
            "candidate_sha256": sha256(proposed.tobytes()).hexdigest()}


def terminal_candidate_for_diagnosis(terminal: Mapping[str, Any], *, termination: str | None) -> tuple[object, object]:
    """Choose the producer-visible candidate appropriate to the terminal kind."""
    if termination == "completed":
        return terminal.get("candidate"), terminal.get("candidate_lineage_id")
    return terminal.get("diagnostic_candidate"), terminal.get("diagnostic_candidate_origin")


def summarize_rows(rows: list[Mapping[str, Any]], *, planned: int) -> dict[str, Any]:
    if len(rows) > planned or len({row.get("shot_id") for row in rows}) != len(rows):
        raise ValueError("duplicate or excess evaluation attempts")
    complete = [row for row in rows if row.get("status") == "completed"]
    cells = Counter(row.get("diagnostic_cell") for row in complete)
    if set(cells) - set(CELLS):
        raise ValueError("completed shot has an unknown diagnostic cell")
    success = sum(row.get("selected") is True and row.get("diagnostic_cell") == "valid_correct" for row in complete)
    valid_wrong = sum(row.get("selected") is True and row.get("diagnostic_cell") == "valid_wrong_logical" for row in complete)
    selected_valid = sum(row.get("selected") is True for row in complete)
    failures = len(complete) - success
    return {"planned": planned, "attempted": len(rows), "completed": len(complete),
            "incomplete_or_unstarted": planned - len(complete),
            "diagnostic_cells": {cell: cells[cell] for cell in CELLS},
            "all_shot_failure": {"failures": failures, "denominator": len(complete),
                                 "estimate": failures / len(complete) if complete else None,
                                 "wilson_95": wilson_interval(failures, len(complete)),
                                 "no_proposal_counted_as_failure": True},
            "selected_valid_syndrome_logical_error": {
                "failures": valid_wrong, "denominator": selected_valid,
                "estimate": valid_wrong / selected_valid if selected_valid else None,
                "wilson_95": wilson_interval(valid_wrong, selected_valid)},
            "termination_counts": dict(Counter(row.get("termination") for row in rows if row.get("termination"))),
            "work_vectors": [row.get("work_vector") for row in rows],
            "public_elapsed_seconds": [row.get("public_boundary", {}).get("elapsed_seconds") for row in rows]}


def retained_category_wall(output: Path) -> float:
    """Rebuild category spending from durable shot journals on every resume."""
    total = 0.0
    for timing in output.glob("*/baseline/preflight-timing.json"):
        total += float(_read(timing)["elapsed_seconds"])
    for timing in output.glob("*/selected_*/preflight-timing.json"):
        total += float(_read(timing)["elapsed_seconds"])
    for journal in output.glob("*/selected_*/attempts.json"):
        for row in json.loads(journal.read_text(encoding="utf-8")):
            elapsed = row.get("public_boundary", {}).get("elapsed_seconds")
            if elapsed is None:
                # A started shot with no retained elapsed may have spent its
                # entire hard boundary before interruption.
                total += 900.0
            else:
                total += float(elapsed)
    for journal in output.glob("*/baseline/attempts.json"):
        for row in json.loads(journal.read_text(encoding="utf-8")):
            elapsed = row.get("public_boundary", {}).get("elapsed_seconds")
            total += 900.0 if elapsed is None else float(elapsed)
    return total


def native_cell(caps: Mapping[str, Any], selection: Mapping[str, Any], code_id: str,
                plan: Mapping[str, Any]) -> dict[str, Any]:
    """Reserve the separate frozen native namespace and shot cap for a pair."""
    source = next(cell for cell in plan["cells"] if cell["code_id"] == code_id and cell["arm"] == "selected_source_procedure")
    code = caps["codes"][code_id]
    count = int(code["native_shots_per_code"])
    if count != int(caps["native"]["shots_per_code"][code_id]) or count <= 0:
        raise ValueError("native shot count drifted")
    namespace = code["native_namespace"]
    if namespace in {code["calibration_namespace"], code["evaluation_namespace"]}:
        raise ValueError("native matched-pair namespace is not disjoint")
    return {**source, "arm": "selected_source_procedure", "sample_namespace": namespace,
            "shots": count, "native_pair_namespace": namespace,
            "native_boundary_seconds": int(caps["native"]["planning_cost_per_shot_seconds"])}


def explicit_native_gammas(manifest: Mapping[str, Any], observation: Mapping[str, Any],
                           *, later_legs: int) -> tuple[np.ndarray, list[str]]:
    """Translate the canonical common random variates to explicit native F64 gammas."""
    matrix = np.asarray(observation["check_matrix"], dtype=np.uint8)
    graph_sha256 = EdgeTable.from_check_matrix(matrix).graph_sha256
    seed_identity = manifest["relay"]["memory_tuning"]["seed_identity"]
    assignment = MemoryAssignmentSpec(
        mode="uniform", graph_sha256=graph_sha256,
        root_seed_identity=sha256(seed_identity.encode("utf-8")).hexdigest(),
        refresh_boundary="leg_start", retain_history=False, low=0.0, high=1.0)
    state = assignment.initial_state(
        configuration_identity=sha256(b"relay-v022-dynamic-memory-common-draw-stream-v1").hexdigest(),
        decoder_identity=seed_identity)
    tuning = manifest["relay"]["memory_tuning"]
    lower = float(tuning["later_leg_center"]) - float(tuning["later_leg_width"]) / 2
    width = float(tuning["later_leg_width"])
    gammas, digests = [], []
    for leg_index in range(1, later_legs + 1):
        replay_identity = f"relay-memory-v022:{observation['sample_identity']}:leg:{leg_index}"
        derived = sha256(f"{state.derived_identity}:memory_assignment:{replay_identity}".encode()).hexdigest()
        rng = np.random.Generator(np.random.PCG64(int(derived[:32], 16)))
        gamma = lower + width * rng.uniform(0.0, 1.0, size=matrix.shape[1])
        gammas.append(gamma)
        digests.append(sha256(np.asarray(gamma, dtype="<f8").tobytes()).hexdigest())
    return np.asarray(gammas, dtype=np.float64), digests


def _author_runner(source: Path, environment: Path, payload: Mapping[str, Any],
                   payload_path: Path, *, timeout: float) -> dict[str, Any]:
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
    pilot._write_json_atomic(payload_path, serializable)
    payload_digest = _byte_sha(payload_path)
    program = r'''
import json, os
from pathlib import Path
import numpy as np
import relay_bp
from relay_bp.bp import RelayDecoderF64
from time import perf_counter
p = json.loads(Path(os.environ["RELAY_V022_PAYLOAD_PATH"]).read_text(encoding="utf-8"))
settings = dict(p["relay_settings"])
settings["explicit_gammas"] = np.ascontiguousarray(settings["explicit_gammas"], dtype=np.float64)
settings["gamma_dist_interval"] = tuple(settings["gamma_dist_interval"])
d = RelayDecoderF64(np.asarray(p["check_matrix"], dtype=np.uint8),
                    np.asarray(p["error_priors"], dtype=np.float64), **settings)
began = perf_counter()
r = d.decode_detailed(np.asarray(p["syndrome"], dtype=np.uint8))
decode_seconds = perf_counter() - began
print(json.dumps({"candidate": np.asarray(r.decoding, dtype=np.uint8).tolist(),
                  "success": bool(r.success), "aggregate_iterations": int(r.iterations),
                  "native_decode_seconds": decode_seconds,
                  "module_origin": str(Path(relay_bp.__file__).resolve())}))
'''
    process = subprocess.run(
        [str(environment / "bin/python"), "-c", program], cwd=source,
        text=True, capture_output=True, timeout=timeout,
        env={**os.environ, "PYTHONNOUSERSITE": "1", "PYTHONPATH": "",
             "RELAY_V022_PAYLOAD_PATH": str(payload_path)})
    if process.returncode:
        raise RuntimeError(f"pinned author native command failed: {(process.stderr or process.stdout)[-1200:]}")
    result = json.loads(process.stdout)
    if not Path(result["module_origin"]).resolve().is_relative_to(environment.resolve()):
        raise RuntimeError("native module resolved outside the isolated exact-author environment")
    result["payload_sha256"] = payload_digest
    return result


def _checked_gamma_digests(events: list[Mapping[str, Any]], shot_id: int,
                           expected: list[str]) -> int:
    checked = 0
    for event in events:
        if event.get("kind") != "work" or event.get("shot_id") != shot_id:
            continue
        for leg in event.get("data", {}).get("relay_legs", []):
            index = leg.get("index")
            if isinstance(index, int) and index > 0:
                if index > len(expected) or leg.get("memory", {}).get("gamma_sha256") != expected[index - 1]:
                    raise ValueError("native gamma translation disagrees with canonical executed leg")
                checked += 1
    return checked


def run_native_pairs(*, root: Path, caps: Mapping[str, Any], selection: Mapping[str, Any],
                     plan: Mapping[str, Any], output: Path) -> dict[str, Any]:
    """Run source-policy canonical and pinned Rust on one fresh native cohort."""
    output.mkdir(parents=True, exist_ok=True)
    category_cap = float(caps["allocation"]["categories"]["native"]["wall_seconds_max"])
    if category_cap <= 0:
        raise ValueError("native category has no finite wall cap")
    native_cells = {code_id: native_cell(caps, selection, code_id, plan) for code_id in sorted(caps["codes"])}
    source = environment = None
    if any(cell["status"] == "ready" for cell in native_cells.values()):
        started = perf_counter()
        source, environment = pilot._git_exact_source(output / "exact-author")
        pilot._source_record(root)
        setup_path = output / "setup-timing.json"
        prior = _read(setup_path) if setup_path.exists() else {"elapsed_seconds": 0.0, "invocations": 0}
        pilot._write_json_atomic(setup_path, {
            "elapsed_seconds": float(prior["elapsed_seconds"]) + perf_counter() - started,
            "invocations": int(prior["invocations"]) + 1,
            "scope": "exact author source qualification and isolated environment provisioning"})
    codes: dict[str, Any] = {}
    for code_id in sorted(caps["codes"]):
        cell = native_cells[code_id]
        if cell["status"] != "ready":
            codes[code_id] = {"status": "unavailable_inconclusive_selection"}
            continue
        base = _read(root / active.CODE_MANIFESTS[code_id])
        manifest = build_manifest(base=base, cell=cell, plan=plan)
        manifest["run_id"] = "phase4-native-matched-" + _digest({"cell": cell, "selection": plan["selected_settings_digest"]})[:24]
        pair_root = output / code_id
        canonical_root = pair_root / "canonical"
        pair_root.mkdir(parents=True, exist_ok=True)
        native_journal = pair_root / "native-attempts.json"
        native_rows: list[dict[str, Any]] = _read(native_journal)["attempts"] if native_journal.exists() else []
        expected_manifest_sha = sha256((json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")).hexdigest()
        if any(row.get("manifest_sha256") != expected_manifest_sha for row in native_rows):
            raise ValueError("retained native pair has a different frozen source manifest")
        if len({int(row["shot_id"]) for row in native_rows}) != len(native_rows):
            raise ValueError("retained native pair journal contains duplicate shot IDs")
        retained_native = {int(row["shot_id"]) for row in native_rows}
        cap_reached = False
        for shot_id in range(int(cell["shots"])):
            if shot_id in retained_native:
                continue
            used = native_category_wall(output)
            # The canonical call is charged by observed elapsed; the native
            # call gets its full declared boundary reserved before launch.
            if used + float(cell["public_boundary_seconds"]) > category_cap:
                cap_reached = True
                break
            one_shot = {**cell, "shots": shot_id + 1}
            canonical = run_cell(root=root, cell=one_shot, manifest=manifest, output=canonical_root,
                                 category_wall_seconds_max=category_cap,
                                 category_wall_seconds_used=used)
            canonical_rows = json.loads((canonical_root / "attempts.json").read_text(encoding="utf-8")) if (canonical_root / "attempts.json").exists() else []
            canonical_row = next((row for row in canonical_rows if row["shot_id"] == shot_id), None)
            if canonical_row is None or canonical_row["status"] != "completed":
                if canonical["status"] == "category_cap_reached":
                    cap_reached = True
                    break
                native_rows.append({"shot_id": shot_id, "status": "incomplete_canonical_pair",
                                    "sample_identity": None, "manifest_sha256": expected_manifest_sha,
                                    "failure": "canonical source arm did not complete"})
                pilot._write_json_atomic(native_journal, {"attempts": native_rows})
                continue
            if native_category_wall(output) + float(cell["native_boundary_seconds"]) > category_cap:
                cap_reached = True
                break
            manifest_path = canonical_root / "manifest.json"
            started = perf_counter()
            native_rows.append({"shot_id": shot_id, "status": "incomplete_interrupted",
                                "sample_identity": canonical_row["sample_identity"],
                                "manifest_sha256": _byte_sha(manifest_path)})
            pilot._write_json_atomic(native_journal, {"attempts": native_rows})
            try:
                observation = active._command(root, "canonical-observation", str(manifest_path),
                                              "--shot", str(shot_id), timeout=float(cell["native_boundary_seconds"]))
                if observation.get("sample_identity") != canonical_row["sample_identity"]:
                    raise ValueError("native and canonical public physical sample differ")
                later_legs = 2 if code_id == "b1-ghp-882" else 30
                gammas, digests = explicit_native_gammas(manifest, observation, later_legs=later_legs)
                checked = _checked_gamma_digests(active._events(canonical_root / "run"), shot_id, digests)
                settings = {"gamma0": float(cell["candidate"]["gamma0"]), "pre_iter": 80,
                            "num_sets": later_legs, "set_max_iter": 60,
                            "gamma_dist_interval": (
                                float(cell["candidate"]["later_center"]) - float(cell["candidate"]["later_width"]) / 2,
                                float(cell["candidate"]["later_center"]) + float(cell["candidate"]["later_width"]) / 2),
                            "explicit_gammas": gammas, "stop_nconv": 1,
                            "stopping_criterion": "nconv", "logging": False}
                metadata: dict[str, Any] = {}
                def call_author(payload: Mapping[str, Any]) -> dict[str, Any]:
                    raw = _author_runner(source, environment, payload, pair_root / f"shot-{shot_id:04d}-payload.json",
                                         timeout=max(.001, float(cell["native_boundary_seconds"]) - (perf_counter() - started)))
                    result_path = pair_root / f"shot-{shot_id:04d}-native-result.json"
                    pilot._write_json_atomic(result_path, raw)
                    metadata.update({"module_origin": raw["module_origin"], "payload_sha256": raw["payload_sha256"],
                                     "native_decode_seconds": raw["native_decode_seconds"],
                                     "payload_path": str(pair_root / f"shot-{shot_id:04d}-payload.json"),
                                     "result_path": str(result_path), "result_sha256": _byte_sha(result_path)})
                    return raw
                result = RelayV022Adapter(native_runner=call_author).run(
                    check_matrix=observation["check_matrix"], syndrome=observation["syndrome"],
                    error_priors=observation["error_priors"], relay_settings=settings,
                    seed=int(observation["decoder_seed"]), numerical_profile="f64")
                diagnosis = classify_candidate(manifest_path, shot_id=shot_id, candidate=result.candidate)
                native_rows[-1] = {"shot_id": shot_id, "status": "completed",
                    "sample_identity": observation["sample_identity"], "success_flag": result.success,
                    "selected": bool(result.success and diagnosis["syndrome_valid"]),
                    "candidate": None if result.candidate is None else np.asarray(result.candidate, dtype=np.uint8).tolist(),
                    "aggregate_iterations": result.aggregate_iterations,
                    "gamma_digests": digests, "executed_gamma_digests_checked": checked,
                    "unavailable_native_facts": unavailable_native_facts(),
                    "native_module_origin": metadata["module_origin"],
                    "native_payload_sha256": metadata["payload_sha256"],
                    "native_payload_path": metadata["payload_path"],
                    "native_result_path": metadata["result_path"], "native_result_sha256": metadata["result_sha256"],
                    "native_decode_seconds": metadata["native_decode_seconds"],
                    "manifest_sha256": _byte_sha(manifest_path), **diagnosis,
                    "public_boundary": {"elapsed_seconds": perf_counter() - started}}
            except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as caught:
                native_rows[-1] = {"shot_id": shot_id, "status": "incomplete_native_unavailable",
                    "sample_identity": canonical_row["sample_identity"],
                    "manifest_sha256": _byte_sha(manifest_path), "failure": str(caught),
                    "public_boundary": {"elapsed_seconds": perf_counter() - started}}
            pilot._write_json_atomic(native_journal, {"attempts": native_rows})
        source_rows = json.loads((canonical_root / "attempts.json").read_text(encoding="utf-8")) if (canonical_root / "attempts.json").exists() else []
        complete = []
        by_source = {int(row["shot_id"]): row for row in source_rows}
        for native in native_rows:
            canonical = by_source.get(int(native["shot_id"]))
            if canonical is None or canonical.get("status") != "completed" or native["status"] != "completed":
                continue
            if canonical["sample_identity"] != native["sample_identity"]:
                raise ValueError("matched native pair identity drifted")
            complete.append({"shot_id": native["shot_id"], "sample_identity": native["sample_identity"],
                             "arms": {"canonical_source": canonical, "author_native": native}})
        codes[code_id] = {"status": "category_cap_reached" if cap_reached else
                          "completed" if len(complete) == int(cell["shots"]) else "incomplete_retained",
                          "planned_pairs": int(cell["shots"]), "complete_pairs": len(complete),
                          "namespace": cell["native_pair_namespace"],
                          "paired": summarize_matched_cohort(complete, arm_names=("canonical_source", "author_native")) if complete else None,
                          "native_summary": summarize_rows(native_rows, planned=int(cell["shots"]))}
        pilot._write_json_atomic(output / "progress.json", {"status": "running", "codes": codes,
                                                           "selected_settings_digest": plan["selected_settings_digest"]})
    report = {"schema_version": 1, "status": "completed" if all(c["status"] == "completed" for c in codes.values()) else "incomplete_or_inconclusive",
              "codes": codes, "author_pin": pilot._ACTIVE_V4_AUTHOR_PIN,
              "selected_settings_digest": plan["selected_settings_digest"],
              "native_category_wall_seconds_max": category_cap,
              "native_category_wall_seconds_used": native_category_wall(output),
              "comparison_scope": "matched fresh native-namespace CSS observations; min-sum canonical source procedure versus exact author F64",
              "runtime_scope": "separate public canonical boundary and exact author native call; setup excluded from per-shot time"}
    pilot._write_json_atomic(output / "result.json", report)
    return report


def native_category_wall(output: Path) -> float:
    setup = output / "setup-timing.json"
    total = float(_read(setup)["elapsed_seconds"]) if setup.exists() else 0.0
    for timing in output.glob("*/canonical/preflight-timing.json"):
        total += float(_read(timing)["elapsed_seconds"])
    for journal in output.glob("*/canonical/attempts.json"):
        for row in json.loads(journal.read_text(encoding="utf-8")):
            elapsed = row.get("public_boundary", {}).get("elapsed_seconds")
            total += 900.0 if elapsed is None else float(elapsed)
    for journal in output.glob("*/native-attempts.json"):
        for row in _read(journal)["attempts"]:
            if row.get("status") == "incomplete_canonical_pair":
                continue
            elapsed = row.get("public_boundary", {}).get("elapsed_seconds")
            total += 900.0 if elapsed is None else float(elapsed)
    return total


def run_cell(*, root: Path, cell: Mapping[str, Any], manifest: Mapping[str, Any], output: Path,
             category_wall_seconds_max: float, category_wall_seconds_used: float) -> dict[str, Any]:
    """Run bounded public shots with a durable no-retry journal and verification."""
    if cell.get("status") != "ready":
        return {"status": "unavailable_inconclusive_selection", "summary": None}
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    expected = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != expected:
        raise ValueError("retained fresh evaluation manifest drifted")
    if not manifest_path.exists():
        pilot._write_json_atomic(manifest_path, manifest)
    preflight_path = output / "preflight.json"
    if not preflight_path.exists():
        began = perf_counter()
        pilot._write_json_atomic(preflight_path, active._command(root, "preflight", str(manifest_path)))
        preflight_elapsed = perf_counter() - began
        pilot._write_json_atomic(output / "preflight-timing.json", {"elapsed_seconds": preflight_elapsed})
        category_wall_seconds_used += preflight_elapsed
    journal = output / "attempts.json"
    rows: list[dict[str, Any]] = json.loads(journal.read_text(encoding="utf-8")) if journal.exists() else []
    if any(row.get("manifest_sha256") != _byte_sha(manifest_path) for row in rows):
        raise ValueError("retained evaluation attempt has a different manifest")
    retained = {int(row["shot_id"]) for row in rows}
    category_cap_reached = False
    for shot_id in range(int(cell["shots"])):
        if shot_id in retained:
            continue
        boundary = float(cell["public_boundary_seconds"])
        if category_wall_seconds_used + boundary > category_wall_seconds_max:
            category_cap_reached = True
            break
        started = perf_counter()
        row: dict[str, Any] = {"shot_id": shot_id, "status": "incomplete_interrupted",
                               "manifest_sha256": _byte_sha(manifest_path)}
        rows.append(row)
        pilot._write_json_atomic(journal, rows)
        run = verify = None
        decode_command_seconds = verify_command_seconds = None
        error = None
        try:
            decode_started = perf_counter()
            run = active._command(root, "canonical", str(manifest_path), "--output", str(output / "run"),
                                  "--shot", str(shot_id), timeout=max(.001, boundary - (perf_counter() - started)))
            decode_command_seconds = perf_counter() - decode_started
            verify_started = perf_counter()
            verify = active._command(root, "verify-canonical-shot", str(manifest_path), str(output / "run"),
                                     "--shot", str(shot_id), timeout=max(.001, boundary - (perf_counter() - started)))
            verify_command_seconds = perf_counter() - verify_started
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as caught:
            error = str(caught)
        facts = active._attempt_from_events(active._events(output / "run"), shot_id)
        terminal = facts["terminal"]
        classification: dict[str, Any] = {}
        if facts["termination"] is not None:
            candidate, candidate_origin = terminal_candidate_for_diagnosis(
                terminal, termination=facts["termination"])
            classification = classify_candidate(manifest_path, shot_id=shot_id, candidate=candidate)
        selected = terminal.get("selection_status") == "frozen_decoder_visible_candidate"
        if selected and classification.get("diagnostic_cell") not in {"valid_correct", "valid_wrong_logical"}:
            raise ValueError("selected recovery fails independent syndrome evaluation")
        rows[-1] = {**row, **facts, **classification,
                    "status": "completed" if error is None and verify is not None and facts["termination"] is not None else "incomplete_public_boundary",
                    "outcome": terminal.get("outcome"), "selection_status": terminal.get("selection_status"),
                    "candidate_origin": candidate_origin, "selected": selected,
                    "failure": error,
                    "public_boundary": {"elapsed_seconds": perf_counter() - started,
                                        "decode_command_seconds": decode_command_seconds,
                                        "verify_command_seconds": verify_command_seconds,
                                        "run": run, "verify": verify}}
        category_wall_seconds_used += float(rows[-1]["public_boundary"]["elapsed_seconds"])
        pilot._write_json_atomic(journal, rows)
    return {"status": "completed" if len(rows) == int(cell["shots"]) and all(row["status"] == "completed" for row in rows)
            else "category_cap_reached" if category_cap_reached else "incomplete_retained",
            "summary": summarize_rows(rows, planned=int(cell["shots"])),
            "attempts_path": str(journal)}


def matched_summary(*, output: Path, code_id: str, first: str, second: str) -> dict[str, Any]:
    a_path = output / code_id / first / "attempts.json"
    b_path = output / code_id / second / "attempts.json"
    if not a_path.exists() or not b_path.exists():
        return {"status": "unavailable_missing_arm"}
    a = {int(row["shot_id"]): row for row in json.loads(a_path.read_text(encoding="utf-8"))}
    b = {int(row["shot_id"]): row for row in json.loads(b_path.read_text(encoding="utf-8"))}
    matched = []
    for shot_id in sorted(a.keys() & b.keys()):
        left, right = a[shot_id], b[shot_id]
        if left.get("status") != "completed" or right.get("status") != "completed":
            continue
        if left.get("sample_identity") != right.get("sample_identity"):
            raise ValueError(f"fresh evaluation sample mismatch: {code_id}/{shot_id}")
        matched.append({"shot_id": shot_id, "sample_identity": left["sample_identity"],
                        "arms": {first: left, second: right}})
    if not matched:
        return {"status": "inconclusive_no_complete_pairs", "complete_pairs": 0}
    return {"status": "partial" if len(matched) != len(a) or len(matched) != len(b) else "completed",
            "complete_pairs": len(matched),
            "analysis": summarize_matched_cohort(matched, arm_names=(first, second))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="freeze terminal selection and preflight admitted manifests")
    parser.add_argument("--run", action="store_true", help="run all admitted canonical evaluation shots")
    parser.add_argument("--run-native", action="store_true", help="run capped matched source-policy and exact-author shots in the frozen native namespace")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if sum((args.prepare, args.run, args.run_native)) != 1:
        parser.error("choose exactly one of --prepare, --run, or --run-native")
    caps, _, selection = verified_inputs(freeze_selection=True)
    plan = evaluation_plan(caps, selection)
    output = args.output.resolve()
    if args.run_native:
        print(json.dumps(run_native_pairs(root=ROOT, caps=caps, selection=selection, plan=plan,
                                          output=output / "native-pairs"), indent=2, sort_keys=True))
        return
    plan_path = output / "plan.json"
    if plan_path.exists() and _read(plan_path) != plan:
        raise ValueError("retained evaluation plan drifted")
    if not plan_path.exists():
        pilot._write_json_atomic(plan_path, plan)
    cells = {}
    for cell in plan["cells"]:
        code_id, arm = cell["code_id"], cell["arm"]
        if cell["status"] != "ready":
            cells.setdefault(code_id, {})[arm] = {"status": cell["status"]}
            continue
        base = _read(ROOT / active.CODE_MANIFESTS[code_id])
        manifest = build_manifest(base=base, cell=cell, plan=plan)
        cell_output = output / code_id / arm
        if args.prepare:
            cell_output.mkdir(parents=True, exist_ok=True)
            manifest_path = cell_output / "manifest.json"
            expected = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != expected:
                raise ValueError("retained evaluation manifest drifted")
            if not manifest_path.exists():
                pilot._write_json_atomic(manifest_path, manifest)
            preflight_path = cell_output / "preflight.json"
            if not preflight_path.exists():
                began = perf_counter()
                pilot._write_json_atomic(preflight_path, active._command(ROOT, "preflight", str(manifest_path)))
                pilot._write_json_atomic(cell_output / "preflight-timing.json", {"elapsed_seconds": perf_counter() - began})
            cells.setdefault(code_id, {})[arm] = {"status": "prepared", "manifest_sha256": _byte_sha(manifest_path)}
        else:
            cells.setdefault(code_id, {})[arm] = run_cell(
                root=ROOT, cell=cell, manifest=manifest, output=cell_output,
                category_wall_seconds_max=float(caps["allocation"]["categories"]["evaluation"]["wall_seconds_max"]),
                category_wall_seconds_used=retained_category_wall(output))
        if args.run:
            pilot._write_json_atomic(output / "progress.json", {"status": "running", "plan_digest": _digest(plan), "codes": cells})
    result: dict[str, Any] = {"schema_version": 1,
        "status": "prepared" if args.prepare else "completed" if all(
            arm.get("status") == "completed" for code in cells.values() for arm in code.values()) else "incomplete_or_inconclusive",
        "plan_digest": _digest(plan), "caps_digest": plan["caps_digest"],
        "selected_settings_digest": plan["selected_settings_digest"], "codes": cells,
        "evaluation_category_wall_seconds_max": caps["allocation"]["categories"]["evaluation"]["wall_seconds_max"],
        "evaluation_category_wall_seconds_used": retained_category_wall(output),
        "shared_settings_view": plan["shared_settings_view"],
        "claim_scope": "finite CSS pilot adaptation; not_assessed for circuit curves or universal ranking"}
    if args.run:
        result["paired"] = {code_id: {
            arm: matched_summary(output=output, code_id=code_id, first="baseline", second=arm)
            for arm in ARMS[1:]} for code_id in caps["codes"]}
        pilot._write_json_atomic(output / "result.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
