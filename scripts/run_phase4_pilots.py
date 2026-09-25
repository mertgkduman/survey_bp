#!/usr/bin/env python3
"""Run finite Phase 4 Relay/memory stages through public evidence boundaries.

This command intentionally owns no decoder kernel.  Canonical arms invoke only
the public CLI; the native arm receives the same public, decoder-visible CSS
observation and invokes the approved Relay v0.2.2 source in a stage-local,
commit-verified environment.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import socket
import subprocess
import sys
import tempfile
from time import perf_counter
from typing import Any, Mapping


AUTHOR_REPOSITORY = "https://github.com/trmue/relay.git"
AUTHOR_COMMIT = "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
AUTHOR_TREE = "5f6f112429e62112ba71fbff45f4e16247725fbc"
STAGES = frozenset({"benchmark", "calibration", "evaluation", "factorial", "native", "trace"})
ARMS = ("source_procedure", "canonical_default", "native_v022")
_NATIVE_TIMEOUT_SECONDS = 900
_BENCHMARK_SHOTS = 32
_BENCHMARK_CENTRAL_ERROR_RATE = 0.03
# The B1 p=.07 scan retained four external timeouts before any full 31-leg
# path completed.  This common internal ceiling is a deliberately smaller,
# measured adaptation: first leg 80 sweeps plus two later legs of 60 sweeps.
# It is expressed in the public ledger's per-field units, not as an inferred
# decoder runtime.  A separate 32-shot cohort measures its wall-time tail.
_B1_P07_BOUNDED_THREE_LEG_WORK_LIMITS = {
    "belief_assemblies": 176_400,
    "candidate_checks": 176_400,
    "check_to_variable_updates": 529_200,
    "variable_to_check_updates": 529_200,
    "residual_priority_evaluations": 0,
    "bp_calls": 3,
    "relay_transfers": 2,
    "branch_expansions": 0,
    "branch_prunes": 0,
    "fallback_calls": 0,
    "intervention_actions": 0,
}
_BENCHMARK_ARMS = ("baseline", "canonical_relay_31", "native_v022")
_BENCHMARK_MANIFESTS = {
    "gross-bb-144": Path("data/manifests/phase4-memory-relay-bb144.json"),
    "b1-ghp-882": Path("data/manifests/phase4-memory-relay-b1.json"),
    "hgp-gallager-3-4-seed-20260923": Path("data/manifests/phase4-memory-relay-hgp.json"),
}


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json_atomic(path: Path, value: object) -> None:
    """Durably replace an evidence journal without a partial JSON window."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


_CALIBRATION_PRESETS: tuple[tuple[str, str, str], ...] = (
    ("source_procedure", "relay-source-internal-bp-v0.2.2", "source_internal_bp"),
    ("canonical_default", "relay-canonical-css-default-v1", "canonical_internal_bp"),
)


def calibration_plan(repository_root: Path, caps: Mapping[str, Any]) -> dict[str, object]:
    """Expand the frozen D-22 surface without reading any calibration outcome.

    The result is a pure projection of the cap record.  Keeping this separate
    from execution makes an accidental outcome-dependent new cell observable
    as a digest change before a public command can start.
    """
    if caps.get("status") != "frozen_pre_calibration":
        raise ValueError("calibration requires the frozen pre-calibration cap record")
    amendment = caps.get("design_amendment")
    if not isinstance(amendment, Mapping) or not isinstance(amendment.get("path"), str):
        raise ValueError("calibration caps omit the versioned design amendment")
    amendment_path = repository_root / str(amendment["path"])
    if not amendment_path.is_file() or sha256(amendment_path.read_bytes()).hexdigest() != amendment.get("sha256"):
        raise ValueError("calibration design amendment is missing or has drifted")
    amendment_value = _read_json(amendment_path)
    if amendment_value.get("calibration_outcomes_inspected") is not False:
        raise ValueError("calibration amendment must predate every calibration outcome")

    cells: list[dict[str, object]] = []
    calibration_namespaces: list[str] = []
    evaluation_namespaces: list[str] = []
    for code_id in sorted(caps.get("codes", {})):
        code = caps["codes"][code_id]
        if not isinstance(code, Mapping):
            raise ValueError(f"calibration caps for {code_id} are invalid")
        controls = code.get("fixed_relay_controls")
        if not isinstance(controls, Mapping) or controls != {
            "total_leg_limit": 31, "first_leg_iteration_limit": 80,
            "later_leg_iteration_limit": 60, "solution_limit": 1,
        }:
            raise ValueError(f"calibration controls drifted for {code_id}")
        calibration_namespace = code.get("calibration_namespace")
        evaluation_namespace = code.get("evaluation_namespace")
        if not isinstance(calibration_namespace, str) or not isinstance(evaluation_namespace, str):
            raise ValueError(f"calibration/evaluation namespaces missing for {code_id}")
        calibration_namespaces.append(calibration_namespace)
        evaluation_namespaces.append(evaluation_namespace)
        candidates = [("coarse", item) for item in code.get("coarse_candidates", [])]
        candidates.extend(("refinement", item) for item in code.get("refinement_candidates", []))
        if len(candidates) != int(code.get("coarse_candidate_count", -1)) + int(code.get("refinement_candidate_count_per_preset", -1)):
            raise ValueError(f"frozen candidate count drifted for {code_id}")
        for preset_key, preset_name, procedure in _CALIBRATION_PRESETS:
            for tier, candidate in candidates:
                if not isinstance(candidate, Mapping):
                    raise ValueError(f"invalid frozen {tier} candidate for {code_id}")
                candidate_copy = dict(candidate)
                candidate_id = candidate_copy.get("id")
                if not isinstance(candidate_id, str):
                    raise ValueError(f"candidate id missing for {code_id}")
                relay = {
                    "preset_name": preset_name,
                    "procedure": procedure,
                    # The amendment fixes 31/80/60 controls for both names;
                    # neither arm is source-faithful in this calibration.
                    "fidelity_status": "controlled_component_adaptation",
                    **dict(controls),
                    "first_leg_memory": "uniform",
                    "later_leg_memory": "disordered" if preset_key == "source_procedure" else "uniform",
                }
                cells.append({
                    "configuration_id": f"{code_id}:{preset_key}:{tier}:{candidate_id}",
                    "code_id": code_id, "preset_key": preset_key,
                    "tier": tier, "candidate": candidate_copy, "relay": relay,
                    "calibration_namespace": calibration_namespace,
                    "calibration_shots": int(code["calibration_shots_per_configuration"]),
                    "central_error_rate": float(code["central_error_rate"]),
                    "per_shot_work_cap": dict(code["per_shot_work_cap"]),
                    "public_boundary_seconds": int(code["canonical_public_boundary_seconds"]),
                })
    if len(set(calibration_namespaces)) != len(calibration_namespaces) or set(calibration_namespaces) & set(evaluation_namespaces):
        raise ValueError("calibration and evaluation namespaces must be globally disjoint")
    calibration_input: dict[str, object] = {
        "caps_digest": caps.get("caps_digest"), "amendment_sha256": amendment.get("sha256"),
        "cells": cells, "calibration_namespaces": sorted(calibration_namespaces),
        "evaluation_namespaces": sorted(evaluation_namespaces),
        "selection_rule": "lowest_failure_then_overlapping_interval_c2v_total_lexicographic",
    }
    return {
        "calibration_input": calibration_input,
        "calibration_digest": _digest(calibration_input), "cells": cells,
        "calibration_namespaces": sorted(calibration_namespaces),
        "evaluation_namespaces": sorted(evaluation_namespaces),
    }


def select_calibration_settings(calibration: Mapping[str, Any]) -> dict[str, object]:
    """Freeze only deterministic selections supported by retained calibration rows."""
    digest = calibration.get("calibration_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("selection requires a bound calibration digest")
    codes = calibration.get("codes")
    if not isinstance(codes, Mapping):
        raise ValueError("selection requires per-code calibration evidence")
    selections: dict[str, object] = {}
    for code_id in sorted(codes):
        code = codes[code_id]
        presets = code.get("presets") if isinstance(code, Mapping) else None
        if not isinstance(presets, Mapping):
            raise ValueError(f"calibration presets missing for {code_id}")
        selected_presets: dict[str, object] = {}
        for preset_key in sorted(presets):
            values = presets[preset_key]
            configurations = values.get("configurations") if isinstance(values, Mapping) else None
            if not isinstance(configurations, list):
                raise ValueError(f"calibration configurations missing for {code_id}/{preset_key}")
            eligible: list[Mapping[str, Any]] = []
            for configuration in configurations:
                logical = configuration.get("logical_failure", {}) if isinstance(configuration, Mapping) else {}
                if isinstance(logical, Mapping) and logical.get("eligible") is True and isinstance(logical.get("estimate"), (int, float)):
                    eligible.append(configuration)
            if not eligible:
                selected_presets[preset_key] = {
                    "status": "inconclusive", "reason": "no eligible complete calibration configuration",
                    "configuration_id": None,
                }
                continue
            def key(item: Mapping[str, Any]) -> tuple[float, float, float, str]:
                logical = item["logical_failure"]
                work = item.get("work", {})
                # 95% overlap does not support a precision claim; it only
                # activates the fixed resource and lexicographic tie sequence.
                return (
                    float(logical["estimate"]),
                    float(work.get("mean_c2v") if work.get("mean_c2v") is not None else float("inf")),
                    float(work.get("mean_total") if work.get("mean_total") is not None else float("inf")),
                    str(item.get("configuration_id", "")),
                )
            winner = min(eligible, key=key)
            selected_presets[preset_key] = {
                "status": "selected_finite_precision_limited", "configuration_id": winner["configuration_id"],
                "candidate": winner.get("candidate"), "logical_failure": winner["logical_failure"],
                "work": winner.get("work"),
            }
        selections[code_id] = {"presets": selected_presets}
    return {
        "schema_version": 1, "status": "frozen_from_calibration_only",
        "calibration_digest": digest, "selection_input_fields": ["calibration.codes"],
        "selection_rule": "eligible lowest estimated logical-failure; overlapping 95% intervals then lower mean C2V, lower total work, lexicographic configuration id; no eligible configuration is inconclusive",
        "codes": selections,
    }


def _calibration_manifest(base: Mapping[str, Any], cell: Mapping[str, Any], *, amendment_sha256: str) -> dict[str, Any]:
    """Materialize one frozen calibration cell for the public canonical CLI."""
    value = deepcopy(dict(base))
    candidate = cell["candidate"]
    relay = dict(cell["relay"])
    configuration_id = str(cell["configuration_id"])
    seed_identity = _digest({
        "purpose": "phase4-relay-calibration-memory", "configuration_id": configuration_id,
        "calibration_namespace": cell["calibration_namespace"],
    })
    relay["legs"] = [{"max_iterations": relay["first_leg_iteration_limit"]}] + [
        {"max_iterations": relay["later_leg_iteration_limit"]}
        for _ in range(int(relay["total_leg_limit"]) - 1)
    ]
    relay["memory_tuning"] = {
        "semantics": "relay_v022_dynamic_affine_prior_css_adaptation",
        "first_leg_gamma": float(candidate["gamma0"]),
        "later_leg_center": float(candidate["later_center"]),
        "later_leg_width": float(candidate["later_width"]),
        "seed_identity": seed_identity,
        "rng_algorithm": "numpy.PCG64",
        "refresh": "per_later_leg",
    }
    value["relay"] = relay
    value["run_id"] = "phase4-calibration-" + _digest({"configuration_id": configuration_id, "amendment": amendment_sha256})[:24]
    value["error_rate"] = float(cell["central_error_rate"])
    randomness = dict(value["randomness"])
    randomness["physical_sample_identity"] = str(cell["calibration_namespace"])
    randomness["decoder_seed_identity"] = seed_identity
    value["randomness"] = randomness
    budgets = dict(value["budgets"])
    for scope_name in ("shot", "search", "attempt"):
        scope = dict(budgets[scope_name])
        scope["max_iterations"] = int(relay["first_leg_iteration_limit"])
        scope["work_limits"] = dict(cell["per_shot_work_cap"])
        budgets[scope_name] = scope
    budgets["max_shots"] = int(cell["calibration_shots"])
    value["budgets"] = budgets
    bindings = deepcopy(value["memory"]["bindings"])
    # The active V4 Relay path consumes the explicit memory_tuning declaration.
    # Keep the base binding's alpha aligned with gamma0 as a manifest-level
    # cross-check rather than relying on an unrecorded runner-side value.
    bindings[0]["parameters"]["alpha"] = float(candidate["gamma0"])
    value["memory"] = {"bindings": bindings}
    evidence = dict(value["evidence"])
    evidence["procedure"] = (
        f"{evidence['procedure']} D-22 calibration cell={configuration_id}; "
        "both named presets use controlled 31/80/60/one-solution CSS adaptation."
    )
    evidence["sources"] = list(evidence.get("sources", [])) + [
        f"phase4-pilot-design-amendment-v3.json#sha256:{amendment_sha256}",
    ]
    evidence["discrepancies"] = list(evidence.get("discrepancies", [])) + [
        "This finite controlled calibration is neither the source 301-leg procedure nor a source-faithful curve reproduction.",
    ]
    value["evidence"] = evidence
    return value


def _wilson_95(failures: int, denominator: int) -> list[float] | None:
    if denominator <= 0:
        return None
    z = 1.959963984540054
    p = failures / denominator
    denominator_z = 1.0 + z * z / denominator
    center = (p + z * z / (2.0 * denominator)) / denominator_z
    half = z * ((p * (1.0 - p) / denominator + z * z / (4.0 * denominator * denominator)) ** 0.5) / denominator_z
    return [max(0.0, center - half), min(1.0, center + half)]


def _append_event_subset(source: Path, destination: Path, *, shot_id: int) -> None:
    """Append one public shot's ledger events exactly once to the calibration ledger."""
    if not source.is_file():
        return
    selected = [line for line in source.read_text(encoding="utf-8").splitlines() if line and json.loads(line).get("shot_id") == shot_id]
    if not selected:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(selected) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _attempt_terminal(run_output: Path, shot_id: int) -> tuple[dict[str, Any] | None, str | None]:
    events_path = run_output / "events.jsonl"
    if not events_path.is_file():
        return None, None
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    terminal = next((event for event in reversed(events) if event.get("kind") == "termination" and event.get("shot_id") == shot_id), None)
    sample = next((event.get("sample_seed_identity") for event in events if event.get("kind") == "shot_begin" and event.get("shot_id") == shot_id), None)
    return terminal, sample if isinstance(sample, str) else None


def _configuration_evidence(cell: Mapping[str, Any], attempts: list[Mapping[str, Any]]) -> dict[str, object]:
    completed = [attempt for attempt in attempts if attempt.get("status") == "completed"]
    logical = [attempt for attempt in completed if attempt.get("outcome") in {"exact", "stabilizer_equivalent", "logical_failure"}]
    failures = sum(attempt.get("outcome") == "logical_failure" for attempt in logical)
    work_rows = [attempt.get("work_vector") for attempt in completed if isinstance(attempt.get("work_vector"), Mapping)]
    mean_c2v = (sum(int(row.get("check_to_variable_updates", 0)) for row in work_rows) / len(work_rows)) if work_rows else None
    mean_total = (sum(sum(int(value) for value in row.values() if isinstance(value, int)) for row in work_rows) / len(work_rows)) if work_rows else None
    complete = len(completed) == int(cell["calibration_shots"])
    eligible = complete and len(logical) == len(completed)
    return {
        "configuration_id": cell["configuration_id"], "candidate": cell["candidate"], "relay": cell["relay"],
        "attempts": list(attempts), "status": "completed" if eligible else "inconclusive",
        "logical_failure": {
            "failures": failures, "denominator": len(logical),
            "estimate": failures / len(logical) if logical else None,
            "wilson_95": _wilson_95(failures, len(logical)), "eligible": eligible,
            "precision_status": "finite_precision_limited_wilson_95_percent" if eligible else "insufficient_precision_or_nonterminal",
        },
        "work": {"mean_c2v": mean_c2v, "mean_total": mean_total},
        "termination_counts": {name: sum(attempt.get("termination") == name for attempt in attempts) for name in sorted({str(attempt.get("termination")) for attempt in attempts if attempt.get("termination") is not None})},
    }


def run_calibration(*, repository_root: Path, caps_path: Path, output_root: Path) -> dict[str, object]:
    """Run or resume the finite D-22 calibration surface through public boundaries."""
    repository_root, caps_path, output_root = repository_root.resolve(), caps_path.resolve(), output_root.resolve()
    caps = _read_json(caps_path)
    plan = calibration_plan(repository_root, caps)
    amendment_sha256 = str(caps["design_amendment"]["sha256"])
    category = caps["allocation"]["categories"]["calibration"]
    category_cap = float(category["wall_seconds_max"])
    result_path = output_root / "result.json"
    events_path = output_root / "events.jsonl"
    output_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema_version": 1, "status": "running", "calibration_digest": plan["calibration_digest"],
        "calibration_input": plan["calibration_input"], "caps_path": str(caps_path.relative_to(repository_root)),
        "caps_sha256": sha256(caps_path.read_bytes()).hexdigest(), "amendment_sha256": amendment_sha256,
        "allocation": {"category": "calibration", "wall_seconds_max": category_cap, "public_boundary_accounting": "decode plus mandatory verify elapsed per identified shot"},
        "codes": {}, "selection_rule": plan["calibration_input"]["selection_rule"],
        "evaluation_namespace_accessed": False,
    }
    if result_path.exists():
        existing = _read_json(result_path)
        if existing.get("calibration_digest") != plan["calibration_digest"]:
            raise ValueError("refusing to mix a different calibration plan into retained evidence")
        result.update(existing)
    cells_by_code: dict[str, dict[str, list[Mapping[str, Any]]]] = {}
    for cell in plan["cells"]:
        cells_by_code.setdefault(str(cell["code_id"]), {}).setdefault(str(cell["preset_key"]), []).append(cell)
    used_wall = sum(
        float(attempt.get("public_boundary", {}).get("elapsed_seconds") or 0.0)
        for code in result["codes"].values() for preset in code.get("presets", {}).values()
        for configuration in preset.get("configurations", []) for attempt in configuration.get("attempts", [])
    )
    cap_reached = False
    for code_id, preset_cells in cells_by_code.items():
        code_record = result["codes"].setdefault(code_id, {"presets": {}})
        base = _read_json(repository_root / _BENCHMARK_MANIFESTS[code_id])
        for preset_key, cells in preset_cells.items():
            preset_record = code_record["presets"].setdefault(preset_key, {"configurations": []})
            existing_by_id = {entry.get("configuration_id"): entry for entry in preset_record["configurations"]}
            for cell in cells:
                configuration_id = str(cell["configuration_id"])
                configuration = existing_by_id.get(configuration_id)
                if configuration is None:
                    configuration = _configuration_evidence(cell, [])
                    preset_record["configurations"].append(configuration)
                attempts = configuration["attempts"]
                manifest = _calibration_manifest(base, cell, amendment_sha256=amendment_sha256)
                cell_root = output_root / "runs" / code_id / preset_key / _digest(configuration_id)[:16]
                manifest_path = cell_root / "manifest.json"
                cell_root.mkdir(parents=True, exist_ok=True)
                if not manifest_path.exists():
                    _write_json_atomic(manifest_path, manifest)
                    _write_json_atomic(cell_root / "preflight.json", _json_command(repository_root, "preflight", str(manifest_path)))
                elif manifest_path.read_bytes() != (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"):
                    raise ValueError(f"retained calibration manifest drifted: {configuration_id}")
                retained = {int(attempt["shot_id"]) for attempt in attempts}
                for shot_id in range(int(cell["calibration_shots"])):
                    if shot_id in retained:
                        continue
                    if used_wall + float(cell["public_boundary_seconds"]) > category_cap:
                        cap_reached = True
                        attempts.append({"shot_id": shot_id, "status": "cap_reached", "termination": None, "failure": "calibration category wall ceiling would be exceeded before launch", "public_boundary": {"elapsed_seconds": 0.0}})
                        retained.add(shot_id)
                        continue
                    started = perf_counter()
                    attempts.append({"shot_id": shot_id, "status": "incomplete_public_boundary", "termination": None, "failure": "public canonical command interrupted before retained terminal", "public_boundary": {"elapsed_seconds": None}})
                    _write_json_atomic(result_path, result)
                    run_output = cell_root / "run"
                    run = verified = None
                    error = None
                    try:
                        run = _json_command(repository_root, "canonical", str(manifest_path), "--output", str(run_output), "--shot", str(shot_id), timeout_seconds=float(cell["public_boundary_seconds"]))
                        verified = _json_command(repository_root, "verify-canonical-shot", str(manifest_path), str(run_output), "--shot", str(shot_id), timeout_seconds=max(0.001, float(cell["public_boundary_seconds"]) - (perf_counter() - started)))
                    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as caught:
                        error = str(caught)
                    elapsed = perf_counter() - started
                    terminal, sample_identity = _attempt_terminal(run_output, shot_id)
                    if terminal is not None:
                        _append_event_subset(run_output / "events.jsonl", events_path, shot_id=shot_id)
                    terminal_data = terminal.get("data", {}) if isinstance(terminal, Mapping) else {}
                    status = "completed" if error is None and terminal is not None and terminal.get("termination") == "completed" else ("budget_exhausted" if terminal is not None and terminal.get("termination") == "budget_exhausted" else "incomplete_public_boundary")
                    attempts[-1] = {
                        "shot_id": shot_id, "status": status,
                        "termination": terminal.get("termination") if terminal else None,
                        "outcome": terminal_data.get("outcome") if isinstance(terminal_data, Mapping) else None,
                        "work_vector": terminal_data.get("work_vector") if isinstance(terminal_data, Mapping) else None,
                        "sample_identity": sample_identity, "failure": error,
                        "public_boundary": {"elapsed_seconds": elapsed, "run": run, "verify": verified},
                    }
                    used_wall += elapsed
                    configuration.update(_configuration_evidence(cell, attempts))
                    result["allocation"]["retained_public_boundary_seconds"] = used_wall
                    _write_json_atomic(result_path, result)
                configuration.update(_configuration_evidence(cell, attempts))
                _write_json_atomic(result_path, result)
    result["allocation"]["retained_public_boundary_seconds"] = used_wall
    result["status"] = "cap_reached" if cap_reached else "completed"
    result["calibration_digest"] = plan["calibration_digest"]
    result["result_digest"] = _digest({key: value for key, value in result.items() if key != "result_digest"})
    _write_json_atomic(result_path, result)
    return result


def _json_command(repository_root: Path, *arguments: str, timeout_seconds: float = 900) -> dict[str, Any]:
    """Invoke the public CLI only; no canonical execution internals are imported here."""
    completed = subprocess.run(
        [sys.executable, "-m", "bp_registry.cli", *arguments], cwd=repository_root,
        text=True, capture_output=True, timeout=timeout_seconds,
        env={**os.environ, "PYTHONPATH": str(repository_root / "src"), "OMP_NUM_THREADS": "1"},
    )
    if completed.returncode:
        raise RuntimeError(f"public CLI {' '.join(arguments)} failed: {completed.stderr or completed.stdout}")
    result = json.loads(completed.stdout)
    if not isinstance(result, dict):
        raise ValueError("public CLI did not return a JSON object")
    return result


def _source_record(repository_root: Path) -> dict[str, Any]:
    record = _read_json(repository_root / "data/evidence/relay-v0.2.2-source.json")
    if (
        record.get("author_repository") != AUTHOR_REPOSITORY
        or record.get("author_commit") != AUTHOR_COMMIT
        or record.get("author_tree") != AUTHOR_TREE
        or record.get("qualification", {}).get("passed") is not True
    ):
        raise ValueError("Relay v0.2.2 source record is not the approved qualified author identity")
    return record


def _environment_identity(manifest: Mapping[str, Any]) -> dict[str, object]:
    environment = manifest.get("environment")
    if not isinstance(environment, Mapping):
        raise ValueError("manifest omits execution environment")
    return {"canonical_environment": dict(environment), "runner_python": sys.version.split()[0]}


def stage_identity(*, repository_root: Path, manifest_path: Path, stage: str, arm: str) -> dict[str, object]:
    """Bind every reusable stage to source, code, environment, sample, and arm facts."""
    if stage not in STAGES:
        raise ValueError(f"unknown finite Phase 4 stage: {stage}")
    if arm not in ARMS:
        raise ValueError(f"unknown Phase 4 arm: {arm}")
    manifest = _read_json(manifest_path)
    randomness = manifest.get("randomness")
    artifact = manifest.get("artifact")
    if not isinstance(randomness, Mapping) or not isinstance(artifact, Mapping):
        raise ValueError("manifest omits artifact or matched sample identity")
    sample_identity = randomness.get("physical_sample_identity")
    if not isinstance(sample_identity, str) or not sample_identity:
        raise ValueError("Phase 4 stages require a physical sample namespace")
    source_identity: dict[str, object]
    if arm == "native_v022":
        record = _source_record(repository_root)
        source_identity = {
            "kind": "approved_author_native", "repository": AUTHOR_REPOSITORY,
            "author_commit": AUTHOR_COMMIT, "author_tree": AUTHOR_TREE,
            "source_record_sha256": sha256((repository_root / "data/evidence/relay-v0.2.2-source.json").read_bytes()).hexdigest(),
            "qualification": record["qualification"],
        }
        translation_identity: dict[str, object] = {
            "kind": "relay-v022-decoder-visible-css-translation-v1", "numerical_profile": "f64",
            "hidden_truth": "not_transferred", "native_fields": "terminal_only",
        }
    else:
        relay = manifest.get("relay")
        if not isinstance(relay, Mapping):
            raise ValueError("canonical Relay arm requires a persisted relay specification")
        source_identity = {
            "kind": "canonical_relay", "procedure": "source_internal_bp" if arm == "source_procedure" else "canonical_internal_bp",
            "relay_preset": "relay-source-internal-bp-v0.2.2" if arm == "source_procedure" else "relay-canonical-css-default-v1",
        }
        translation_identity = {
            "kind": "canonical-public-v4", "relay": dict(relay), "arm": arm,
        }
    identity: dict[str, object] = {
        "identity_version": 1, "stage": stage, "arm": arm,
        "manifest_path": str(manifest_path), "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
        "policy_identity": _digest({"policies": manifest.get("policies"), "memory": manifest.get("memory"), "arm": arm}),
        "code_identity": {"code_id": artifact.get("code_id"), "raw_sha256": artifact.get("raw_sha256"), "semantic_sha256": artifact.get("semantic_sha256"), "matrix_hashes": artifact.get("matrix_hashes")},
        "environment_identity": _environment_identity(manifest), "sample_identity": sample_identity,
        "source_identity": source_identity, "translation_identity": _digest(translation_identity),
    }
    identity["stage_identity"] = _digest(identity)
    return identity


def _arm_manifest(base: Mapping[str, Any], *, stage: str, arm: str) -> dict[str, Any]:
    """Produce an immutable arm manifest with explicit bounded Relay controls."""
    value = deepcopy(dict(base))
    value["run_id"] = f"{base['run_id']}-{stage}-{arm}"
    relay = dict(value["relay"])
    if arm == "source_procedure":
        relay.update({
            "preset_name": "relay-source-internal-bp-v0.2.2", "procedure": "source_internal_bp",
            "fidelity_status": "source_procedure_css_adaptation", "later_leg_memory": "disordered",
        })
    elif arm == "canonical_default":
        relay.update({
            "preset_name": "relay-canonical-css-default-v1", "procedure": "canonical_internal_bp",
            "fidelity_status": "canonical_css_adaptation", "later_leg_memory": "uniform",
        })
    else:
        raise ValueError("native arms do not create a canonical manifest")
    value["relay"] = relay
    evidence = dict(value["evidence"])
    evidence["procedure"] = (
        f"{evidence['procedure']} Stage={stage}; arm={arm}; finite controls are a CSS adaptation."
    )
    value["evidence"] = evidence
    return value


def _run(command: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)


def _git_exact_source(stage_root: Path) -> tuple[Path, Path]:
    """Provision a durable stage-local author checkout and isolated environment."""
    native_root = stage_root / "native-v0.2.2"
    source = native_root / "source"
    environment = native_root / "venv"
    native_root.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        cloned = _run(["git", "clone", "--quiet", AUTHOR_REPOSITORY, str(source)], cwd=native_root, timeout=300)
        if cloned.returncode:
            raise RuntimeError(f"exact author clone failed: {cloned.stderr[-1000:]}")
    for args, expected in ((["git", "config", "--get", "remote.origin.url"], AUTHOR_REPOSITORY), (["git", "rev-parse", "HEAD"], AUTHOR_COMMIT), (["git", "rev-parse", "HEAD^{tree}"], AUTHOR_TREE)):
        check = _run(args, cwd=source, timeout=30)
        if check.returncode or check.stdout.strip() != expected:
            if args[1:3] == ["rev-parse", "HEAD"]:
                checkout = _run(["git", "checkout", "--quiet", "--detach", AUTHOR_COMMIT], cwd=source, timeout=60)
                if checkout.returncode:
                    raise RuntimeError(f"exact author checkout failed: {checkout.stderr[-1000:]}")
                check = _run(args, cwd=source, timeout=30)
            if check.returncode or check.stdout.strip() != expected:
                raise RuntimeError("stage-local native source does not match the approved author identity")
    # A prior interrupted build can leave only Cargo.lock changed. It is a
    # generated resolver byproduct, never source evidence; restore it before
    # admitting the exact checkout, while rejecting any other tracked change.
    changed = _run(["git", "diff", "--name-only"], cwd=source, timeout=30)
    changed_paths = [line for line in changed.stdout.splitlines() if line]
    if changed_paths == ["Cargo.lock"]:
        restored = _run(["git", "checkout", "--", "Cargo.lock"], cwd=source, timeout=30)
        if restored.returncode:
            raise RuntimeError("could not restore generated Cargo.lock in stage-local native source")
    elif changed_paths:
        raise RuntimeError("stage-local native source has non-lock tracked modifications")
    clean = _run(["git", "status", "--porcelain"], cwd=source, timeout=30)
    if clean.returncode or clean.stdout.strip():
        raise RuntimeError("stage-local native source must remain unmodified")
    if not environment.exists():
        created = _run([sys.executable, "-m", "venv", "--system-site-packages", str(environment)], cwd=native_root, timeout=120)
        if created.returncode:
            raise RuntimeError(f"native environment creation failed: {created.stderr[-1000:]}")
        installed = _run([str(environment / "bin/python"), "-m", "pip", "install", "--no-deps", str(source)], cwd=native_root, timeout=300)
        if installed.returncode:
            raise RuntimeError(f"exact author binding install failed: {installed.stderr[-1000:]}")
        # The source's build backend may refresh Cargo.lock.  That build byproduct
        # must never become a source modification used by an exact-author run.
        dirty_after_install = _run(["git", "diff", "--name-only"], cwd=source, timeout=30)
        if [line for line in dirty_after_install.stdout.splitlines() if line] == ["Cargo.lock"]:
            restored = _run(["git", "checkout", "--", "Cargo.lock"], cwd=source, timeout=30)
            if restored.returncode:
                raise RuntimeError("could not restore generated Cargo.lock in stage-local native source")
        clean_after_install = _run(["git", "status", "--porcelain"], cwd=source, timeout=30)
        if clean_after_install.returncode or clean_after_install.stdout.strip():
            raise RuntimeError("native build left the exact author source modified")
    return source, environment


def _native_runner(*, source: Path, environment: Path, payload: Mapping[str, object]) -> dict[str, object]:
    """Run the exact-author binding in its isolated stage environment."""
    program = r'''
import json, os
from pathlib import Path
import numpy as np
import relay_bp
from relay_bp.bp import RelayDecoderF32, RelayDecoderF64
source = Path(os.environ["RELAY_V022_SOURCE"]).resolve()
module = Path(relay_bp.__file__).resolve()
if "mg551/storage/relay" in str(module):
    raise RuntimeError("refusing installed fork module")
payload = json.loads(Path(os.environ["RELAY_V022_PAYLOAD_PATH"]).read_text(encoding="utf-8"))
classes = {"RelayDecoderF32": RelayDecoderF32, "RelayDecoderF64": RelayDecoderF64}
decoder = classes[payload["decoder_class"]](
    np.asarray(payload["check_matrix"], dtype=np.uint8),
    np.asarray(payload["error_priors"], dtype=np.float64), **payload["relay_settings"],
)
result = decoder.decode_detailed(np.asarray(payload["syndrome"], dtype=np.uint8))
posterior = np.asarray(result.posterior_ratios, dtype=np.float64)
print(json.dumps({
    "candidate": np.asarray(result.decoding, dtype=np.uint8).tolist(),
    "success": bool(result.success), "score": None,
    "aggregate_iterations": int(result.iterations), "final_posterior": posterior.tolist(),
    "log_output": "", "module_origin": str(module), "source_root": str(source),
}))
'''
    serializable = {
        **payload,
        "check_matrix": getattr(payload["check_matrix"], "tolist", lambda: payload["check_matrix"])(),
        "syndrome": getattr(payload["syndrome"], "tolist", lambda: payload["syndrome"])(),
        "error_priors": getattr(payload["error_priors"], "tolist", lambda: payload["error_priors"])(),
    }
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False) as payload_file:
        payload_file.write(_canonical_json(serializable))
        payload_path = Path(payload_file.name)
    try:
        completed = subprocess.run(
            [str(environment / "bin/python"), "-c", program], cwd=source, text=True, capture_output=True,
            timeout=_NATIVE_TIMEOUT_SECONDS, env={**os.environ, "PYTHONNOUSERSITE": "1", "RELAY_V022_SOURCE": str(source), "RELAY_V022_PAYLOAD_PATH": str(payload_path)},
        )
    finally:
        payload_path.unlink(missing_ok=True)
    if completed.returncode:
        raise RuntimeError(f"exact author native execution failed: {completed.stderr[-1000:]}")
    result = json.loads(completed.stdout)
    if not isinstance(result, dict):
        raise ValueError("exact author native execution returned invalid JSON")
    return result


def _run_native(*, repository_root: Path, stage_root: Path, observation: Mapping[str, object]) -> dict[str, object]:
    """Translate only public decoder-visible observation fields through RelayV022Adapter."""
    from bp_registry.native.relay_v022 import RelayV022Adapter, unavailable_native_facts

    source, environment = _git_exact_source(stage_root)
    adapter = RelayV022Adapter(native_runner=lambda payload: _native_runner(source=source, environment=environment, payload=payload))
    result = adapter.run(
        check_matrix=observation["check_matrix"], syndrome=observation["syndrome"],
        error_priors=observation["error_priors"], relay_settings={
            "pre_iter": 80, "num_sets": 30, "set_max_iter": 60, "stopping_criterion": "nconv", "stop_nconv": 1, "logging": False,
        }, seed=int(observation["decoder_seed"]), numerical_profile="f64",
    )
    return {
        "status": "completed", "candidate": result.candidate.tolist(), "success": result.success,
        "aggregate_iterations": result.aggregate_iterations,
        "final_posterior": None if result.final_posterior is None else result.final_posterior.tolist(),
        "unavailable_native_facts": unavailable_native_facts(),
        "source_path": str(source), "environment_path": str(environment),
    }


def _archive_mismatch(stage_dir: Path, existing: Mapping[str, object]) -> None:
    archive = stage_dir / f"mismatch-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{_digest(existing)[:12]}.json"
    archive.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _slurm_entitlement(job_id: str) -> dict[str, object]:
    """Read the scheduler allocation without consulting node-wide capacity."""
    shown = subprocess.run(
        ["scontrol", "show", "job", "-o", job_id], text=True, capture_output=True, timeout=30, check=False,
    )
    if shown.returncode:
        raise RuntimeError(f"cannot read SLURM entitlement for {job_id}: {shown.stderr[-1000:]}")
    fields = dict(
        token.split("=", 1) for token in shown.stdout.strip().split() if "=" in token
    )
    required = ("Account", "Partition", "NumCPUs", "NumTasks", "CPUs/Task", "AllocTRES", "NumNodes", "TimeLimit")
    missing = [name for name in required if not fields.get(name)]
    if missing:
        raise RuntimeError(f"SLURM allocation record omits {', '.join(missing)}")
    alloc_tres = dict(
        item.split("=", 1) for item in fields["AllocTRES"].split(",") if "=" in item
    )
    memory = alloc_tres.get("mem")
    if memory is None:
        raise RuntimeError("SLURM AllocTRES does not declare allocated memory")
    return {
        "scheduler": "slurm",
        "job_id": job_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "scontrol_show_job_o": shown.stdout.strip(),
        "allocation": {
            "account": fields["Account"], "partition": fields["Partition"],
            "cpus": int(fields["NumCPUs"]), "tasks": int(fields["NumTasks"]),
            "cpus_per_task": int(fields["CPUs/Task"]), "memory": memory,
            "nodes": int(fields["NumNodes"]), "time_limit": fields["TimeLimit"],
        },
        "concurrency_limit": 1,
        "environment": {
            "host": socket.gethostname(), "python": sys.version.split()[0],
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS", "unset"),
        },
    }


def _benchmark_manifest(
    base: Mapping[str, object], *, arm: str, central_error_rate: float = _BENCHMARK_CENTRAL_ERROR_RATE,
    work_limit_override: Mapping[str, int] | None = None, namespace_suffix: str = "",
    sample_namespace_suffix: str | None = None,
) -> dict[str, object]:
    """Build one bounded, identified benchmark arm from a qualified V4 manifest."""
    value = deepcopy(dict(base))
    value["run_id"] = f"{base['run_id']}-benchmark-{arm}{namespace_suffix}"
    value["error_rate"] = central_error_rate
    randomness = dict(value["randomness"])
    # A rate amendment must never share a sample namespace with the retained
    # central-rate cohort.  Canonical and native arms below receive these exact
    # generated bytes, so matching within the amended cohort remains public.
    rate_tag = f"p{central_error_rate:.3f}".replace(".", "")
    if sample_namespace_suffix is None:
        sample_namespace_suffix = namespace_suffix
    randomness["physical_sample_identity"] = f"{randomness['physical_sample_identity']}-benchmark-{rate_tag}{sample_namespace_suffix}"
    value["randomness"] = randomness
    budgets = dict(value["budgets"])
    budgets["max_shots"] = _BENCHMARK_SHOTS
    multiplier = 1 if arm == "baseline" else 31
    for scope_name in ("shot", "search", "attempt"):
        scope = dict(budgets[scope_name])
        scope["max_iterations"] = 80
        limits = {name: amount * multiplier * 80 for name, amount in dict(scope["work_limits"]).items()}
        limits["bp_calls"] = multiplier
        limits["relay_transfers"] = max(0, multiplier - 1)
        if work_limit_override is not None:
            limits = dict(work_limit_override)
        scope["work_limits"] = limits
        budgets[scope_name] = scope
    value["budgets"] = budgets
    relay = dict(value["relay"])
    relay["total_leg_limit"] = multiplier
    relay["legs"] = [{"max_iterations": 80}] + [{"max_iterations": 60} for _ in range(multiplier - 1)]
    relay["first_leg_iteration_limit"] = 80
    relay["later_leg_iteration_limit"] = 60
    relay["solution_limit"] = 1
    relay["preset_name"] = "phase4-benchmark-baseline-v1" if arm == "baseline" else "phase4-benchmark-canonical-relay-31-v1"
    relay["procedure"] = "canonical_internal_bp"
    relay["fidelity_status"] = "canonical_css_adaptation"
    value["relay"] = relay
    evidence = dict(value["evidence"])
    evidence["procedure"] = (
        f"{evidence['procedure']} Bounded D-23 benchmark arm={arm}; "
        f"shots={_BENCHMARK_SHOTS}; central_error_rate={central_error_rate}."
    )
    value["evidence"] = evidence
    return value


def _distribution(values: list[float | None]) -> dict[str, object]:
    observed = sorted(value for value in values if value is not None)
    result: dict[str, object] = {"count": len(values), "observed_count": len(observed), "values": values}
    if observed:
        result.update({
            "min": observed[0], "max": observed[-1], "mean": sum(observed) / len(observed),
            "p95": observed[min(len(observed) - 1, int((len(observed) - 1) * 0.95))],
        })
    return result


def _canonical_attempts(output: Path, *, expected_shots: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Extract terminal facts and relay leaves from the public structural ledger."""
    events_path = output / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line] if events_path.exists() else []
    terminals = {event["shot_id"]: event for event in events if event.get("kind") == "termination"}
    begins = {event["shot_id"]: event for event in events if event.get("kind") == "shot_begin"}
    runtimes: dict[int, float] = {}
    per_leg_totals: dict[str, dict[str, int]] = {}
    for event in events:
        data = event.get("data", {})
        if event.get("kind") == "runtime":
            profile = data.get("profile", {})
            value = profile.get("wall_seconds") or profile.get("elapsed_seconds")
            if isinstance(value, (int, float)):
                runtimes[event["shot_id"]] = runtimes.get(event["shot_id"], 0.0) + float(value)
        if event.get("kind") == "work":
            for leaf in data.get("relay_work_leaves", []):
                if leaf.get("kind") != "leg":
                    continue
                key = str(leaf["leg_index"])
                total = per_leg_totals.setdefault(key, {})
                for name, amount in leaf.get("work_vector", {}).items():
                    if isinstance(amount, int):
                        total[name] = total.get(name, 0) + amount
    attempts = []
    for shot_id in range(expected_shots):
        terminal = terminals.get(shot_id)
        attempts.append({
            "shot_id": shot_id,
            "status": "completed" if terminal is not None else "incomplete_no_terminal",
            "termination": None if terminal is None else terminal["termination"],
            "runtime_seconds": runtimes.get(shot_id),
            "sample_identity": begins.get(shot_id, {}).get("sample_seed_identity"),
            "terminal": {} if terminal is None else terminal.get("data", {}),
        })
    return attempts, {"availability": "observed", "per_leg_totals": per_leg_totals}


def _run_canonical_benchmark_arm(*, repository_root: Path, base: Mapping[str, object], arm: str, output: Path, central_error_rate: float = _BENCHMARK_CENTRAL_ERROR_RATE,
                                 work_limit_override: Mapping[str, int] | None = None, namespace_suffix: str = "",
                                 sample_namespace_suffix: str | None = None) -> dict[str, object]:
    """Use one bounded public CLI invocation per identified shot."""
    manifest = _benchmark_manifest(
        base, arm=arm, central_error_rate=central_error_rate,
        work_limit_override=work_limit_override, namespace_suffix=namespace_suffix,
        sample_namespace_suffix=sample_namespace_suffix,
    )
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    preflight = _json_command(repository_root, "preflight", str(manifest_path))
    _write_json_atomic(output / "preflight.json", preflight)
    run_path = output / "run"
    journal_path = output / "canonical-attempts.json"
    attempts: list[dict[str, object]] = json.loads(journal_path.read_text(encoding="utf-8")) if journal_path.exists() else []
    if not isinstance(attempts, list):
        raise ValueError("canonical benchmark attempt journal is not a list")
    retained = {entry["shot_id"] for entry in attempts}
    for shot_id in range(_BENCHMARK_SHOTS):
        if shot_id in retained:
            continue
        started = perf_counter()
        # Persist the identified attempt before launching the child.  A job
        # interruption can then be reported as incomplete rather than being
        # silently absent from the 32-shot public ledger.
        attempts.append({
            "shot_id": shot_id, "status": "incomplete_canonical_interrupted",
            "manifest_sha256": _digest(manifest), "sample_identity": None,
            "failure": "public canonical command did not reach a retained terminal record",
            "public_boundary": {"decode_wall_seconds": None, "verify_wall_seconds": None},
        })
        _write_json_atomic(journal_path, attempts)
        run: dict[str, object] | None = None
        verified: dict[str, object] | None = None
        error: str | None = None
        decode_started = perf_counter()
        deadline = decode_started + 900
        decode_wall_seconds: float | None = None
        verify_wall_seconds: float | None = None
        try:
            run = _json_command(repository_root, "canonical", str(manifest_path), "--output", str(run_path), "--shot", str(shot_id), timeout_seconds=max(0.001, deadline - perf_counter()))
            decode_wall_seconds = perf_counter() - decode_started
            verify_started = perf_counter()
            verified = _json_command(repository_root, "verify-canonical-shot", str(manifest_path), str(run_path), "--shot", str(shot_id), timeout_seconds=max(0.001, deadline - perf_counter()))
            verify_wall_seconds = perf_counter() - verify_started
        except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as caught:
            if decode_wall_seconds is None:
                decode_wall_seconds = perf_counter() - decode_started
            error = str(caught)
        all_attempts, shot_work = _canonical_attempts(run_path, expected_shots=_BENCHMARK_SHOTS)
        terminal = all_attempts[shot_id]
        attempts[-1] = {
            "shot_id": shot_id,
            "status": "completed" if error is None and terminal["status"] == "completed" else "incomplete_canonical_shot",
            "termination": terminal["termination"], "runtime_seconds": terminal["runtime_seconds"], "sample_identity": terminal["sample_identity"], "terminal": terminal["terminal"],
            "manifest_sha256": _digest(manifest), "failure": error,
            "public_boundary": {"run": run, "verify": verified, "decode_wall_seconds": decode_wall_seconds, "verify_wall_seconds": verify_wall_seconds, "elapsed_seconds": perf_counter() - started},
        }
        _write_json_atomic(journal_path, attempts)
    # The ledger contains all retained shots.  Aggregate it once after any
    # resume, so skipped journal entries still contribute exactly once.
    _, retained_work = _canonical_attempts(run_path, expected_shots=_BENCHMARK_SHOTS)
    raw_work = {"availability": "observed", "per_leg_totals": retained_work["per_leg_totals"]}
    completed = all(attempt["status"] == "completed" for attempt in attempts)
    return {
        "shot_ids": list(range(_BENCHMARK_SHOTS)), "attempts": attempts,
        "sample_identities": [attempt["sample_identity"] for attempt in attempts],
        "runtime_seconds": _distribution([attempt["runtime_seconds"] for attempt in attempts]),
        "public_decode_wall_seconds": _distribution([attempt.get("public_boundary", {}).get("decode_wall_seconds") for attempt in attempts]),
        "public_command_wall_seconds": _distribution([attempt.get("public_boundary", {}).get("elapsed_seconds") for attempt in attempts]),
        "resource_measurements": {"scope": "attempt", "method": "canonical_public_ledger", "status": "runtime facts retained per terminal"},
        "raw_work": raw_work, "relay": manifest["relay"], "manifest_sha256": _digest(manifest),
        "status": "completed" if completed else "incomplete_canonical_arm",
        "failure": None if completed else "one or more identified canonical shots did not complete within the public CLI boundary",
        "public_boundary": {"mode": "one public preflight/canonical/verify-canonical-shot invocation per identified shot"},
    }


def _reuse_exact_canonical_benchmark_arm(*, repository_root: Path, base: Mapping[str, object], arm: str, output: Path, central_error_rate: float = _BENCHMARK_CENTRAL_ERROR_RATE) -> dict[str, object] | None:
    """Reuse only a complete old arm whose generated manifest bytes are identical."""
    manifest_path = output / "manifest.json"
    run_path = output / "run"
    if not manifest_path.is_file() or not (run_path / "events.jsonl").is_file():
        return None
    expected = _benchmark_manifest(base, arm=arm, central_error_rate=central_error_rate)
    if manifest_path.read_bytes() != (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode("utf-8"):
        return None
    try:
        verified = [
            _json_command(repository_root, "verify-canonical-shot", str(manifest_path), str(run_path), "--shot", str(shot_id))
            for shot_id in range(_BENCHMARK_SHOTS)
        ]
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError):
        return None
    attempts, raw_work = _canonical_attempts(run_path, expected_shots=_BENCHMARK_SHOTS)
    if not all(attempt["status"] == "completed" for attempt in attempts):
        return None
    return {
        "shot_ids": list(range(_BENCHMARK_SHOTS)), "attempts": attempts,
        "sample_identities": [attempt["sample_identity"] for attempt in attempts],
        "runtime_seconds": _distribution([attempt["runtime_seconds"] for attempt in attempts]),
        "resource_measurements": {"scope": "attempt", "method": "canonical_public_ledger", "status": "runtime facts retained per terminal"},
        "raw_work": raw_work, "relay": expected["relay"], "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
        "status": "completed", "failure": None, "reused_exact_identity": True,
        "public_boundary": {"run": {"output": str(run_path)}, "verify": verified, "elapsed_seconds_whole_arm": None},
    }


def _run_native_benchmark_arm(*, repository_root: Path, base: Mapping[str, object], output: Path, central_error_rate: float = _BENCHMARK_CENTRAL_ERROR_RATE) -> dict[str, object]:
    """Run each author-native shot separately so failures remain terminal benchmark facts."""
    output.mkdir(parents=True, exist_ok=True)
    source_record = _source_record(repository_root)
    relay_manifest = _benchmark_manifest(base, arm="canonical_relay_31", central_error_rate=central_error_rate)
    relay_manifest_path = output / "observation-manifest.json"
    relay_manifest_path.write_text(json.dumps(relay_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    attempts_path = output / "attempts.json"
    attempts: list[dict[str, object]] = json.loads(attempts_path.read_text(encoding="utf-8")) if attempts_path.exists() else []
    if not isinstance(attempts, list):
        raise ValueError("native benchmark attempts record is not a list")
    retained = {attempt["shot_id"] for attempt in attempts}
    try:
        # Validate exact source once per arm. Repeating an expensive status scan
        # is not a per-shot measurement and must not consume the shot budget.
        _git_exact_source(output / "native-stage")
        setup_error: str | None = None
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        setup_error = str(error)
    for shot_id in range(_BENCHMARK_SHOTS):
        if shot_id in retained:
            continue
        started = perf_counter()
        attempts.append({"shot_id": shot_id, "status": "incomplete_native_interrupted", "runtime_seconds": None,
                         "sample_identity": None, "children_maxrss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                         "result": {"reason": "native command did not reach a retained terminal record"}})
        _write_json_atomic(attempts_path, attempts)
        try:
            observation = _json_command(repository_root, "canonical-observation", str(relay_manifest_path), "--shot", str(shot_id))
        except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as error:
            attempts[-1] = {
                "shot_id": shot_id, "status": "incomplete_native_observation_unavailable",
                "runtime_seconds": perf_counter() - started, "sample_identity": None,
                "children_maxrss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                "result": {"reason": str(error)},
            }
            _write_json_atomic(attempts_path, attempts)
            continue
        if setup_error is not None:
            result, status = {"reason": setup_error}, "incomplete_native_unavailable"
        else:
            try:
                result = _run_native(repository_root=repository_root, stage_root=output / "native-stage", observation=observation)
                status = result["status"]
            except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as error:
                result, status = {"reason": str(error)}, "incomplete_native_unavailable"
        attempts[-1] = {
            "shot_id": shot_id, "status": status, "runtime_seconds": perf_counter() - started,
            "sample_identity": observation["sample_identity"],
            "children_maxrss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            "result": result,
        }
        _write_json_atomic(attempts_path, attempts)
    completed = len(attempts) == _BENCHMARK_SHOTS and all(attempt["status"] == "completed" for attempt in attempts)
    return {
        "shot_ids": list(range(_BENCHMARK_SHOTS)), "attempts": attempts,
        "sample_identities": [attempt["sample_identity"] for attempt in attempts],
        "runtime_seconds": _distribution([float(attempt["runtime_seconds"]) for attempt in attempts]),
        "resource_measurements": {
            "scope": "all_children_to_date", "method": "resource.getrusage(RUSAGE_CHILDREN).ru_maxrss",
            "interpretation": "cumulative child-process high-water mark, not independent per-shot RSS",
            "cumulative_maxrss_kib": [attempt["children_maxrss_kib"] for attempt in attempts],
        },
        "raw_work": {
            "availability": "unavailable", "reason": "unmodified exact-author Relay v0.2.2 does not expose edge or per-leg work facts",
            "per_leg_totals": None,
        },
        "source_identity": {
            "author_repository": AUTHOR_REPOSITORY, "author_commit": AUTHOR_COMMIT, "author_tree": AUTHOR_TREE,
            "source_record_sha256": sha256((repository_root / "data/evidence/relay-v0.2.2-source.json").read_bytes()).hexdigest(),
            "qualification": source_record["qualification"],
        },
        "status": "completed" if completed else "incomplete_native_arm",
        "failure": None if completed else "one or more identified native shots did not complete within the retained benchmark boundary",
    }


def run_benchmark(*, repository_root: Path, output_path: Path, job_id: str, artifact_run_id: str | None = None,
                  central_error_rate: float = _BENCHMARK_CENTRAL_ERROR_RATE,
                  code_ids: tuple[str, ...] | None = None,
                  purpose: str = "D-23 measured finite Phase 4 pilot benchmark") -> dict[str, object]:
    """Retain the bounded D-23 benchmark once; an existing record is never silently replaced."""
    repository_root, output_path = repository_root.resolve(), output_path.resolve()
    if output_path.exists():
        raise FileExistsError(f"refusing to replace retained benchmark evidence: {output_path}")
    entitlement = _slurm_entitlement(job_id)
    selected_codes = tuple(_BENCHMARK_MANIFESTS) if code_ids is None else code_ids
    unknown_codes = set(selected_codes) - set(_BENCHMARK_MANIFESTS)
    if not selected_codes or unknown_codes:
        raise ValueError(f"benchmark code selection is invalid: {sorted(unknown_codes) if unknown_codes else 'empty'}")
    prior_root = output_path.parent / "benchmark-artifacts"
    prior_incomplete_evidence = []
    if prior_root.is_dir():
        for ledger in sorted(prior_root.rglob("run/events.jsonl")):
            terminal_count = sum(1 for line in ledger.read_text(encoding="utf-8").splitlines() if line and json.loads(line).get("kind") == "termination")
            prior_incomplete_evidence.append({
                "ledger_path": str(ledger.relative_to(repository_root)), "ledger_sha256": sha256(ledger.read_bytes()).hexdigest(),
                "terminal_count": terminal_count, "status": "retained_interrupted_prior_attempt",
            })
    benchmark_run_id = artifact_run_id or _digest({
        "entitlement": entitlement, "manifests": {
            code_id: sha256((repository_root / path).read_bytes()).hexdigest()
            for code_id, path in _BENCHMARK_MANIFESTS.items() if code_id in selected_codes
        },
        "central_error_rate": central_error_rate,
        "code_ids": selected_codes,
    })[:16]
    root = output_path.parent / "benchmark-artifacts" / benchmark_run_id
    codes: dict[str, object] = {}
    for code_id in selected_codes:
        relative_manifest = _BENCHMARK_MANIFESTS[code_id]
        base = _read_json(repository_root / relative_manifest)
        if base["artifact"]["code_id"] != code_id:
            raise ValueError(f"benchmark manifest code identity drifted for {code_id}")
        code_root = root / code_id
        codes[code_id] = {
            "central_error_rate": central_error_rate,
            "manifest_sha256": sha256((repository_root / relative_manifest).read_bytes()).hexdigest(),
            "sample_namespace": _benchmark_manifest(base, arm="canonical_relay_31", central_error_rate=central_error_rate)["randomness"]["physical_sample_identity"],
            "arms": {
                "baseline": _reuse_exact_canonical_benchmark_arm(repository_root=repository_root, base=base, arm="baseline", output=code_root / "baseline", central_error_rate=central_error_rate) or _run_canonical_benchmark_arm(repository_root=repository_root, base=base, arm="baseline", output=code_root / "baseline", central_error_rate=central_error_rate),
                "canonical_relay_31": _reuse_exact_canonical_benchmark_arm(repository_root=repository_root, base=base, arm="canonical_relay_31", output=code_root / "canonical-relay-31", central_error_rate=central_error_rate) or _run_canonical_benchmark_arm(repository_root=repository_root, base=base, arm="canonical_relay_31", output=code_root / "canonical-relay-31", central_error_rate=central_error_rate),
                "native_v022": _run_native_benchmark_arm(repository_root=repository_root, base=base, output=code_root / "native-v022", central_error_rate=central_error_rate),
            },
        }
    complete_current = all(
        arm.get("status") == "completed"
        for code in codes.values() for arm in code["arms"].values()
    )
    result: dict[str, object] = {
        "schema_version": 1, "status": "completed" if complete_current else "incomplete_current_attempts", "purpose": purpose,
        "benchmark_run_id": benchmark_run_id, "artifact_root": str(root.relative_to(repository_root)),
        "prior_incomplete_evidence": prior_incomplete_evidence,
        "sample_count_per_arm": _BENCHMARK_SHOTS, "entitlement": entitlement, "entitlement_digest": _digest(entitlement),
        "codes": codes,
        "command_boundaries": {
            "canonical": [sys.executable, "-m", "bp_registry.cli", "preflight|canonical|verify-run"],
            "native": ["approved exact author Relay v0.2.2", "per-shot timeout", _NATIVE_TIMEOUT_SECONDS],
        },
        "no_retry_policy": "Every failed or incomplete identified native attempt is retained; this benchmark does not retry it.",
        "runtime_measurement_note": "Canonical ledger runtime_seconds may be unavailable; public_decode_wall_seconds and public_command_wall_seconds are measured per-shot public command timings, with decode and verification scopes retained separately.",
    }
    result["benchmark_digest"] = _digest(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_bounded_b1_p07_relay_probe(*, repository_root: Path, output_path: Path, job_id: str,
                                    artifact_run_id: str) -> dict[str, object]:
    """Measure the B1 p=.07 bounded Relay adaptation without replacing its timeout scan."""
    repository_root, output_path = repository_root.resolve(), output_path.resolve()
    if output_path.exists():
        raise FileExistsError(f"refusing to replace retained bounded-probe evidence: {output_path}")
    if not artifact_run_id:
        raise ValueError("bounded Relay probe requires a fresh explicit artifact identity")
    entitlement = _slurm_entitlement(job_id)
    code_id = "b1-ghp-882"
    base = _read_json(repository_root / _BENCHMARK_MANIFESTS[code_id])
    root = output_path.parent / "benchmark-artifacts" / artifact_run_id
    namespace_suffix = "-bounded-three-leg-v1"
    arm = _run_canonical_benchmark_arm(
        repository_root=repository_root, base=base, arm="canonical_relay_31",
        output=root / code_id / "canonical-relay-31-bounded-three-leg",
        central_error_rate=0.07, work_limit_override=_B1_P07_BOUNDED_THREE_LEG_WORK_LIMITS,
        namespace_suffix=namespace_suffix, sample_namespace_suffix="",
    )
    complete_current = arm["status"] == "completed"
    prior_scan = repository_root / "data/results/phase4-memory-relay/benchmark-v3-p07-bb-b1-amendment.json"
    if not prior_scan.is_file():
        raise FileNotFoundError("bounded B1 p=.07 probe requires retained unbounded p=.07 scan evidence")
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "completed" if complete_current else "incomplete_current_attempts",
        "purpose": "D-23 B1 p=.07 bounded Relay-work calibration adaptation probe",
        "benchmark_run_id": artifact_run_id,
        "artifact_root": str(root.relative_to(repository_root)),
        "sample_count_per_arm": _BENCHMARK_SHOTS,
        "entitlement": entitlement,
        "entitlement_digest": _digest(entitlement),
        "unbounded_rate_probe": {
            "path": str(prior_scan.relative_to(repository_root)),
            "sha256": sha256(prior_scan.read_bytes()).hexdigest(),
            "status": "incomplete_current_attempts",
            "reason": "four B1 p=.07 canonical public-boundary timeouts; retained as rate-scan evidence only",
        },
        "adaptation": {
            "name": "b1-p007-bounded-three-leg-equivalent-v1",
            "central_error_rate": 0.07,
            "declared_relay_controls": {
                "total_leg_limit": 31, "first_leg_iteration_limit": 80,
                "later_leg_iteration_limit": 60, "solution_limit": 1,
            },
            "work_limit_scope": "identical shot/search/attempt work vector for every bounded probe shot and later B1 p=.07 calibration candidate",
            "work_limits": _B1_P07_BOUNDED_THREE_LEG_WORK_LIMITS,
            "derivation": {
                "per_sweep_belief_and_candidate": 882,
                "per_sweep_message_updates_each_direction": 2646,
                "sweep_envelope": 200,
                "equivalent_leg_envelope": "first 80 sweeps plus two 60-sweep later legs",
            },
            "qualification": "bounded adaptation measures up to a three-leg-equivalent work envelope; it does not claim measured unbounded 31-leg B1 p=.07 runtime",
        },
        "code": {
            "code_id": code_id,
            "manifest_sha256": sha256((repository_root / _BENCHMARK_MANIFESTS[code_id]).read_bytes()).hexdigest(),
            "sample_namespace": _benchmark_manifest(
                base, arm="canonical_relay_31", central_error_rate=0.07,
                work_limit_override=_B1_P07_BOUNDED_THREE_LEG_WORK_LIMITS,
                namespace_suffix=namespace_suffix, sample_namespace_suffix="",
            )["randomness"]["physical_sample_identity"],
            "arm": arm,
        },
        "command_boundaries": {
            "canonical_total_public_boundary_seconds": 900,
            "canonical": [sys.executable, "-m", "bp_registry.cli", "preflight|canonical|verify-canonical-shot"],
        },
        "no_retry_policy": "Every started bounded canonical attempt is durably retained and never silently retried.",
        "runtime_measurement_note": "Canonical ledger runtime_seconds may be unavailable; public_decode_wall_seconds and public_command_wall_seconds are measured per-shot public timings with decode and verification scopes retained separately.",
    }
    result["benchmark_digest"] = _digest(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_stage(*, repository_root: Path, manifest_path: Path, stage: str, output_root: Path) -> dict[str, object]:
    """Preflight, execute, and verify a finite identified stage without unsafe reuse."""
    repository_root, manifest_path, output_root = repository_root.resolve(), manifest_path.resolve(), output_root.resolve()
    base = _read_json(manifest_path)
    identities = [stage_identity(repository_root=repository_root, manifest_path=manifest_path, stage=stage, arm=arm) for arm in ARMS]
    overall_identity = _digest({"stage": stage, "identities": identities})
    stage_dir = output_root / f"{base['artifact']['code_id']}-{stage}-{overall_identity[:16]}"
    stage_dir.mkdir(parents=True, exist_ok=True)
    stage_record = stage_dir / "stage.json"
    if stage_record.exists():
        existing = _read_json(stage_record)
        if existing.get("identity") == {"stage_identity": overall_identity, "arms": identities}:
            if existing.get("status") == "completed":
                return {**existing, "reused": True, "stage_record": str(stage_record)}
            # A finite interruption is evidence, not permission to repeat the same
            # workload. A caller must create a new stage identity explicitly.
            return {
                **existing, "reused": False, "stage_record": str(stage_record),
                "retry_requires_new_stage_identity": True,
            }
        _archive_mismatch(stage_dir, existing)
    manifests = stage_dir / "manifests"
    manifests.mkdir(exist_ok=True)
    arms: list[dict[str, object]] = []
    for arm, identity in zip(ARMS[:2], identities[:2], strict=True):
        arm_path = manifests / f"{arm}.json"
        arm_path.write_text(json.dumps(_arm_manifest(base, stage=stage, arm=arm), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # Public preflight/run/verify must all pass before a stage can be reusable.
        preflight = _json_command(repository_root, "preflight", str(arm_path))
        output = stage_dir / "canonical" / arm
        run = _json_command(repository_root, "canonical", str(arm_path), "--output", str(output))
        verified = _json_command(repository_root, "verify-run", str(output))
        arms.append({"arm": arm, "identity": identity, "status": "completed", "preflight": preflight, "run": run, "verify": verified})
    # The observation is emitted by the public CLI and contains no hidden truth.
    observation = _json_command(repository_root, "canonical-observation", str(manifests / "source_procedure.json"), "--shot", "0")
    if observation.get("sample_namespace") != identities[2]["sample_identity"]:
        raise ValueError("native observation does not use the declared matched physical sample namespace")
    try:
        native = _run_native(repository_root=repository_root, stage_root=stage_dir, observation=observation)
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        native = {"status": "native_unavailable", "reason": str(error), "unavailable_native_facts": "native result retained without replacement"}
    arms.append({"arm": "native_v022", "identity": identities[2], **native})
    status = "completed" if native.get("status") == "completed" else "incomplete_native_unavailable"
    record: dict[str, object] = {
        "schema_version": 1, "status": status, "identity": {"stage_identity": overall_identity, "arms": identities},
        "sample_identity": observation["sample_identity"], "sample_namespace": identities[0]["sample_identity"],
        "arms": arms, "stage": stage,
        "finite_caps": {"canonical_shots": base["budgets"]["max_shots"], "native_timeout_seconds": _NATIVE_TIMEOUT_SECONDS},
        "stage_record": str(stage_record), "reused": False,
    }
    stage_record.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/phase4-memory-relay-bb144.json"))
    parser.add_argument("--stage", choices=sorted(STAGES), default="trace")
    parser.add_argument("--output", type=Path, default=Path("data/results/phase4-pilots"))
    parser.add_argument("--benchmark", action="store_true", help="run the retained D-23 32-shot benchmark for all qualified Phase 4 codes")
    parser.add_argument("--benchmark-output", type=Path, default=Path("data/results/phase4-memory-relay/benchmark-v2.json"), help="new versioned benchmark report; refuses to overwrite historical evidence")
    parser.add_argument("--slurm-job-id", default=os.environ.get("SLURM_JOB_ID"), help="concrete SLURM allocation used for a D-23 benchmark")
    parser.add_argument("--benchmark-artifact-run-id", help="resume only the named retained benchmark artifact identity")
    parser.add_argument("--benchmark-error-rate", type=float, default=_BENCHMARK_CENTRAL_ERROR_RATE, help="explicit rate for a fresh, rate-namespaced benchmark cohort")
    parser.add_argument("--benchmark-code", action="append", choices=sorted(_BENCHMARK_MANIFESTS), help="repeat to select a bounded subset of qualified codes")
    parser.add_argument("--bounded-b1-p07-relay-probe", action="store_true", help="run the fresh 32-shot B1 p=.07 three-leg-equivalent Relay adaptation probe")
    parser.add_argument("--bounded-probe-output", type=Path, default=Path("data/results/phase4-memory-relay/benchmark-v3-b1-p07-bounded-three-leg.json"), help="new immutable report for the bounded B1 p=.07 probe")
    parser.add_argument("--bounded-probe-artifact-run-id", help="fresh artifact identity for the bounded B1 p=.07 probe")
    args = parser.parse_args()
    repository_root = Path(__file__).resolve().parents[1]
    if args.benchmark and args.bounded_b1_p07_relay_probe:
        raise SystemExit("choose one benchmark mode per invocation")
    if args.bounded_b1_p07_relay_probe:
        if not args.slurm_job_id or not args.bounded_probe_artifact_run_id:
            raise SystemExit("bounded B1 p=.07 probe requires --slurm-job-id and --bounded-probe-artifact-run-id")
        print(json.dumps(run_bounded_b1_p07_relay_probe(
            repository_root=repository_root, output_path=args.bounded_probe_output,
            job_id=args.slurm_job_id, artifact_run_id=args.bounded_probe_artifact_run_id,
        ), indent=2, sort_keys=True))
        return
    if args.benchmark:
        if not args.slurm_job_id:
            raise SystemExit("--benchmark requires --slurm-job-id or SLURM_JOB_ID")
        print(json.dumps(run_benchmark(
            repository_root=repository_root,
            output_path=args.benchmark_output,
            job_id=args.slurm_job_id,
            artifact_run_id=args.benchmark_artifact_run_id,
            central_error_rate=args.benchmark_error_rate,
            code_ids=None if args.benchmark_code is None else tuple(args.benchmark_code),
        ), indent=2, sort_keys=True))
        return
    print(json.dumps(run_stage(repository_root=repository_root, manifest_path=args.manifest, stage=args.stage, output_root=args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
