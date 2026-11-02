#!/usr/bin/env python3
"""Run a finite, matched BB-144 low-noise LER precision campaign.

The design is frozen before sampling. Every shot uses the public canonical and
verification commands, and append-only journals make interruption visible.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any, Mapping

import numpy as np
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[1]
AUTHOR_PIN = "relay-v0.2.2@14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
CORE_COMMITS = ("6e6ad03", "660049a", "1f8f1c2")
ARMS = (
    ("canonical_baseline", "canonical_default", "baseline"),
    ("canonical_relay", "canonical_default", "canonical_relay_31"),
    ("source_baseline", "source_procedure", "baseline"),
    ("source_relay", "source_procedure", "canonical_relay_31"),
)


def _helper():
    path = Path(__file__).with_name("run_phase4_active_benchmark.py")
    spec = importlib.util.spec_from_file_location("phase4_active_benchmark", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _sha(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


def _atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _append(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _journal(path: Path) -> dict[int, dict[str, Any]]:
    latest: dict[int, dict[str, Any]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line:
                row = json.loads(line)
                latest[int(row["shot_id"])] = row
    return latest


def exact_interval(failures: int, denominator: int, *, alpha: float) -> list[float] | None:
    """Clopper-Pearson interval at one of the prespecified sequential looks."""
    if denominator <= 0 or failures < 0 or failures > denominator or not 0 < alpha < 1:
        return None
    lower = 0.0 if failures == 0 else float(beta.ppf(alpha / 2, failures, denominator - failures + 1))
    upper = 1.0 if failures == denominator else float(beta.ppf(1 - alpha / 2, failures + 1, denominator - failures))
    return [lower, upper]


def summarize(rows: Mapping[int, Mapping[str, Any]], *, planned_shots: int, alpha: float,
              min_failures: int, max_relative_half_width: float,
              no_recovery_policy: str) -> dict[str, Any]:
    complete = [row for shot, row in rows.items() if shot < planned_shots and row.get("status") == "completed"]
    cells = Counter(row.get("diagnostic_cell") for row in complete)
    expected_cells = {"valid_correct", "valid_wrong_logical", "invalid_correct", "invalid_wrong_logical", "no_proposal"}
    if set(cells) - expected_cells:
        raise ValueError("completed LER shot lacks an independently classified diagnostic proposal")
    selected = [row for row in complete if row.get("selection_status") == "frozen_decoder_visible_candidate"]
    if any(row.get("diagnostic_cell") not in {"valid_correct", "valid_wrong_logical"} for row in selected):
        raise ValueError("selected recovery has an invalid syndrome or missing diagnostic proposal")
    selected_valid_correct = sum(row.get("diagnostic_cell") == "valid_correct" for row in selected)
    selected_valid_wrong = sum(row.get("diagnostic_cell") == "valid_wrong_logical" for row in selected)
    no_recovery = cells["no_proposal"]
    if no_recovery_policy == "count_as_failure":
        primary_failures, primary_denominator = len(complete) - selected_valid_correct, len(complete)
    elif no_recovery_policy == "conditional_ler":
        primary_failures, primary_denominator = selected_valid_wrong, len(selected)
    else:
        raise ValueError("unknown no-recovery policy")
    interval = exact_interval(primary_failures, primary_denominator, alpha=alpha)
    estimate = primary_failures / primary_denominator if primary_denominator else None
    relative_half_width = ((interval[1] - interval[0]) / (2 * estimate)
                           if interval and estimate and estimate > 0 else None)
    strict_interval = exact_interval(selected_valid_wrong, len(selected), alpha=alpha)
    strict_estimate = selected_valid_wrong / len(selected) if selected else None
    strict_relative_half_width = ((strict_interval[1] - strict_interval[0]) / (2 * strict_estimate)
                                  if strict_interval and strict_estimate and strict_estimate > 0 else None)
    all_identified_complete = len(complete) == planned_shots and all(
        shot in rows and rows[shot].get("status") == "completed" for shot in range(planned_shots)
    )
    primary_precise = bool(all_identified_complete and primary_failures >= min_failures
                           and relative_half_width is not None and relative_half_width <= max_relative_half_width)
    strict_precise = bool(all_identified_complete and selected_valid_wrong >= min_failures
                          and strict_relative_half_width is not None and strict_relative_half_width <= max_relative_half_width)
    return {
        "planned_shots": planned_shots, "complete_shots": len(complete),
        "incomplete_shots": planned_shots - len(complete),
        "diagnostic_cells": {cell: cells[cell] for cell in ("valid_correct", "valid_wrong_logical", "invalid_correct", "invalid_wrong_logical", "no_proposal")},
        "diagnostic_cell_estimates": {
            cell: {"count": cells[cell], "denominator": len(complete),
                   "estimate": cells[cell] / len(complete) if complete else None,
                   "exact_interval_simultaneous_over_cells_and_looks": exact_interval(cells[cell], len(complete), alpha=2 * alpha / 5)}
            for cell in ("valid_correct", "valid_wrong_logical", "invalid_correct", "invalid_wrong_logical", "no_proposal")
        },
        "selection": {"selected_recoveries": len(selected), "no_selected_recovery": len(complete) - len(selected),
                      "valid_correct_selected": selected_valid_correct},
        "primary": {"metric": "all_shot_decoder_failure" if no_recovery_policy == "count_as_failure" else "conditional_logical_error",
                    "failures": primary_failures, "denominator": primary_denominator,
                    "estimate": estimate, "simultaneous_over_looks_exact_interval": interval,
                    "relative_half_width": relative_half_width, "precision_met": primary_precise},
        "strict_logical_error": {"failures": selected_valid_wrong, "valid_syndrome_selected_denominator": len(selected),
                                 "estimate": strict_estimate, "simultaneous_over_looks_exact_interval": strict_interval,
                                 "relative_half_width": strict_relative_half_width,
                                 "precision_met": strict_precise,
                                 "no_proposal_reported_separately": no_recovery},
        "precision_met": primary_precise and strict_precise,
    }


def validate_design(design: Mapping[str, Any]) -> None:
    if design.get("status") != "frozen_before_sampling" or design.get("schema_version") != 1:
        raise ValueError("LER design must be frozen before sampling")
    if design.get("code_id") != "gross-bb-144" or design.get("error_rates") != [0.06, 0.05]:
        raise ValueError("LER design must use the frozen BB-144 lower-rate grid")
    if design.get("author_source_pin") != AUTHOR_PIN or design.get("active_core_commits") != list(CORE_COMMITS):
        raise ValueError("LER design lacks the approved author/core identity")
    if design.get("arms") != [name for name, _preset, _arm in ARMS]:
        raise ValueError("LER design four-arm comparison drifted")
    if design.get("controls") != {
        "first_leg_gamma": 0.125, "later_leg_center": 0.25, "later_leg_width": 1.25,
        "relay_total_leg_limit": 31, "baseline_total_leg_limit": 1,
        "first_leg_iteration_limit": 80, "later_leg_iteration_limit": 60,
        "solution_limit": 1, "work_profile": "full31",
        "source_numerical_profile": "cpu-float64-min-sum-v1",
        "canonical_numerical_profile": "cpu-float64-spa-v1",
    }:
        raise ValueError("LER design controlled parameters drifted")
    precision = design.get("precision", {})
    if precision.get("looks") != [256, 512, 1024, 2048, 4096, 8192]:
        raise ValueError("LER design must use the frozen finite look schedule")
    if precision.get("confidence") != 0.95 or precision.get("minimum_failures") != 50:
        raise ValueError("LER design precision target drifted")
    if precision.get("maximum_relative_half_width") != 0.35:
        raise ValueError("LER design interval width target drifted")
    if precision.get("no_recovery_policy") != "count_as_failure":
        raise ValueError("LER design must count no-recovery shots as primary failures")
    if design.get("reporting_axes") != {
        "syndrome": ["valid", "invalid"], "logical_projection": ["correct", "wrong"],
        "cells": ["valid_correct", "valid_wrong_logical", "invalid_correct", "invalid_wrong_logical"],
        "missing_proposal": "no_proposal counted as primary failure but reported separately",
        "invalid_logical_note": "logical projection against pinned LZ is computed for diagnostics even when residual syndrome is nonzero; it is not a code-space logical coset",
    }:
        raise ValueError("LER design four-cell reporting contract drifted")


def classify_diagnostic_candidate(manifest_path: Path, *, shot_id: int,
                                  candidate: object) -> dict[str, Any]:
    """Evaluate both axes independently after decoding, never inside a policy."""
    if candidate is None:
        return {"diagnostic_cell": "no_proposal", "syndrome_valid": None,
                "logical_projection_correct": None, "diagnostic_candidate_sha256": None}
    from bp_registry.runner import canonical_public_shot_context
    context = canonical_public_shot_context(manifest_path, shot_id=shot_id)
    if context.code is None or context.hidden_truth is None:
        raise ValueError("public shot context lacks independent original-problem evaluation data")
    code = context.code.validate()
    if code.lz is None:
        raise ValueError("BB-144 logical projection requires its pinned LZ basis")
    proposed = np.asarray(candidate)
    if proposed.shape != (code.n,) or not np.issubdtype(proposed.dtype, np.integer) or np.any((proposed != 0) & (proposed != 1)):
        raise ValueError("diagnostic proposal must be a pinned-length binary X vector")
    proposed = proposed.astype(np.uint8, copy=True)
    hidden = context.hidden_truth.x.astype(np.uint8)
    syndrome_valid = bool(np.array_equal(
        (code.hz.astype(np.int64) @ proposed.astype(np.int64)) % 2,
        np.asarray(context.syndrome, dtype=np.uint8),
    ))
    residual = hidden ^ proposed
    logical_correct = not bool(np.any((residual.astype(np.int64) @ code.lz.astype(np.int64).T) % 2))
    cell = ("valid_" if syndrome_valid else "invalid_") + ("correct" if logical_correct else "wrong_logical")
    return {"diagnostic_cell": cell, "syndrome_valid": syndrome_valid,
            "logical_projection_correct": logical_correct,
            "diagnostic_candidate_sha256": sha256(proposed.tobytes()).hexdigest()}
    if design.get("public_shot_boundary_seconds") != 900 or design.get("max_campaign_wall_seconds") != 5 * 86400:
        raise ValueError("LER design lacks finite shot/campaign wall bounds")


def _manifest(helper: Any, base: Mapping[str, Any], *, arm_name: str, preset: str,
              arm: str, rate: float, design_digest: str, max_shots: int) -> dict[str, Any]:
    value = helper.build_active_manifest(
        base, arm=arm, preset=preset, error_rate=rate,
        first_leg_gamma=0.125, later_center=0.25, later_width=1.25,
        seed_identity=f"phase4-low-noise-ler-v1-bb144-p{rate:.3f}", work_profile="full31",
    )
    value["run_id"] = f"phase4-low-noise-ler-v1-bb144-{arm_name}-p{rate:.3f}".replace(".", "")
    value["randomness"]["physical_sample_identity"] = f"phase4-low-noise-ler-v1-bb144-matched-p{rate:.3f}".replace(".", "")
    value["budgets"]["max_shots"] = max_shots
    value["evidence"]["procedure"] += f" Separate prespecified lower-noise LER precision campaign design sha256:{design_digest}."
    value["evidence"]["discrepancies"].append(
        "Uncalibrated controlled CSS pilot; this is not a source-faithful reproduction or publication ranking."
    )
    return value


def _public_attempt(helper: Any, *, manifest_path: Path, output: Path, shot_id: int,
                    journal_path: Path, boundary_seconds: int) -> dict[str, Any]:
    _append(journal_path, {"shot_id": shot_id, "status": "started", "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest()})
    began = perf_counter()
    run = verify = None
    error = None
    try:
        run = helper._command(ROOT, "canonical", str(manifest_path), "--output", str(output), "--shot", str(shot_id),
                              timeout=max(0.001, boundary_seconds - (perf_counter() - began)))
        verify = helper._command(ROOT, "verify-canonical-shot", str(manifest_path), str(output), "--shot", str(shot_id),
                                 timeout=max(0.001, boundary_seconds - (perf_counter() - began)))
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as caught:
        error = str(caught)
    fact = helper._attempt_from_events(helper._events(output), shot_id)
    classification = classify_diagnostic_candidate(
        manifest_path, shot_id=shot_id, candidate=fact["terminal"].get("diagnostic_candidate"))
    if fact["termination"] is not None and error is None:
        cell, outcome = classification["diagnostic_cell"], fact["terminal"].get("outcome")
        selected = fact["terminal"].get("selection_status") == "frozen_decoder_visible_candidate"
        if ((outcome is not None and cell == "valid_correct" and outcome not in {"exact", "stabilizer_equivalent"})
                or (outcome is not None and cell == "valid_wrong_logical" and outcome != "logical_failure")
                or (cell.startswith("invalid_") and outcome is not None)
                or (selected and (outcome is None or cell not in {"valid_correct", "valid_wrong_logical"}))):
            raise ValueError("diagnostic axes disagree with the independently evaluated public terminal")
    row = {"shot_id": shot_id,
           "status": "completed" if error is None and fact["termination"] is not None and verify is not None else "incomplete_public_boundary",
           "termination": fact["termination"], "outcome": fact["terminal"].get("outcome"),
           "selection_status": fact["terminal"].get("selection_status"),
           "diagnostic_candidate_origin": fact["terminal"].get("diagnostic_candidate_origin"),
           **classification,
           "sample_identity": fact["sample_identity"], "work_vector": fact["work_vector"],
           "distinct_leg_indices": fact["distinct_leg_indices"],
           "active_memory_verified": helper._active_memory_proven({**fact, "status": "completed"}) if fact["termination"] else False,
           "public_boundary": {"elapsed_seconds": perf_counter() - began, "run": run, "verify": verify},
           "failure": error, "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest()}
    _append(journal_path, row)
    return row


def _recover_started(helper: Any, *, manifest_path: Path, output: Path, shot_id: int,
                     journal_path: Path, prior: Mapping[str, Any]) -> dict[str, Any]:
    fact = helper._attempt_from_events(helper._events(output), shot_id)
    verified = None
    error = None
    if fact["termination"]:
        try:
            verified = helper._command(ROOT, "verify-canonical-shot", str(manifest_path), str(output), "--shot", str(shot_id))
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as caught:
            error = str(caught)
    completed = fact["termination"] is not None and verified is not None
    classification = classify_diagnostic_candidate(
        manifest_path, shot_id=shot_id, candidate=fact["terminal"].get("diagnostic_candidate"))
    row = {"shot_id": shot_id,
           "status": "completed" if completed else "incomplete_interrupted",
           "termination": fact["termination"], "outcome": fact["terminal"].get("outcome"),
           "selection_status": fact["terminal"].get("selection_status"),
           "diagnostic_candidate_origin": fact["terminal"].get("diagnostic_candidate_origin"),
           **classification,
           "sample_identity": fact["sample_identity"], "work_vector": fact["work_vector"],
           "distinct_leg_indices": fact["distinct_leg_indices"],
           "active_memory_verified": helper._active_memory_proven(fact) if verified is not None else False,
           "public_boundary": {"elapsed_seconds": None, "charged_seconds": 900, "verify": verified},
           "failure": None if completed else (error or "started command had no retained verified terminal"),
           "manifest_sha256": prior["manifest_sha256"]}
    _append(journal_path, row)
    return row


def run_campaign(*, design_path: Path, output_root: Path) -> dict[str, Any]:
    design_path, output_root = design_path.resolve(), output_root.resolve()
    design = _read(design_path)
    validate_design(design)
    for commit in CORE_COMMITS:
        check = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=False)
        if check.returncode:
            raise RuntimeError(f"LER campaign requires committed active-memory core repair {commit}")
    design_bytes = design_path.read_bytes()
    design_digest = sha256(design_bytes).hexdigest()
    script_digest = sha256(Path(__file__).read_bytes()).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    terminal_path, progress_path, identity_path = (output_root / name for name in ("result.json", "progress.json", "identity.json"))
    if terminal_path.exists():
        raise FileExistsError("LER result is terminal; refusing to overwrite or extend it")
    if identity_path.exists():
        identity = _read(identity_path)
        if identity.get("design_byte_sha256") != design_digest or identity.get("script_byte_sha256") != script_digest:
            raise ValueError("retained LER campaign design or runner differs from requested execution")
    else:
        identity = {"schema_version": 1, "design_path": str(design_path.relative_to(ROOT)),
                    "design_byte_sha256": design_digest, "started_at": datetime.now(timezone.utc).isoformat(),
                    "script_byte_sha256": script_digest, "author_source_pin": design["author_source_pin"]}
        _atomic(identity_path, identity)
    started_at = datetime.fromisoformat(identity["started_at"])
    helper = _helper()
    base = _read(ROOT / "data/manifests/phase4-memory-relay-bb144.json")
    looks = design["precision"]["looks"]
    max_shots = looks[-1]
    alpha = (1.0 - design["precision"]["confidence"]) / (len(looks) * 2)
    summaries: dict[str, Any] = {}
    all_precise = True
    wall_exhausted = False
    for rate in design["error_rates"]:
        rate_key = f"p{rate:.3f}".replace(".", "")
        paths: dict[str, tuple[Path, Path]] = {}
        rows: dict[str, dict[int, dict[str, Any]]] = {}
        for arm_name, preset, arm in ARMS:
            arm_root = output_root / rate_key / arm_name
            manifest_path, journal_path = arm_root / "manifest.json", arm_root / "attempts.jsonl"
            manifest = _manifest(helper, base, arm_name=arm_name, preset=preset, arm=arm,
                                 rate=rate, design_digest=design_digest, max_shots=max_shots)
            expected = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
            if manifest_path.exists():
                if manifest_path.read_text(encoding="utf-8") != expected:
                    raise ValueError(f"retained LER manifest drifted: {rate_key}/{arm_name}")
            else:
                _atomic(manifest_path, manifest)
            preflight_path = arm_root / "preflight.json"
            if not preflight_path.exists():
                _atomic(preflight_path, helper._command(ROOT, "preflight", str(manifest_path)))
            paths[arm_name] = manifest_path, journal_path
            rows[arm_name] = _journal(journal_path)
            for shot_id, prior in list(rows[arm_name].items()):
                if prior.get("status") == "started":
                    output = arm_root / "batches" / f"{shot_id // 64:04d}" / "run"
                    rows[arm_name][shot_id] = _recover_started(
                        helper, manifest_path=manifest_path, output=output,
                        shot_id=shot_id, journal_path=journal_path, prior=prior)
        stop_at = None
        for shot_id in range(max_shots):
            if (datetime.now(timezone.utc) - started_at).total_seconds() + 4 * design["public_shot_boundary_seconds"] > design["max_campaign_wall_seconds"]:
                wall_exhausted = True
                break
            sample_ids = set()
            for arm_name, _preset, _arm in ARMS:
                manifest_path, journal_path = paths[arm_name]
                prior = rows[arm_name].get(shot_id)
                if prior is None:
                    output = output_root / rate_key / arm_name / "batches" / f"{shot_id // 64:04d}" / "run"
                    row = _public_attempt(helper, manifest_path=manifest_path, output=output,
                                          shot_id=shot_id, journal_path=journal_path,
                                          boundary_seconds=design["public_shot_boundary_seconds"])
                    rows[arm_name][shot_id] = row
                else:
                    row = prior
                if row.get("sample_identity") is not None:
                    sample_ids.add(row["sample_identity"])
            if len(sample_ids) > 1:
                raise ValueError(f"matched physical samples diverged at {rate_key}/shot-{shot_id}")
            n = shot_id + 1
            if n in looks:
                snapshot = {arm_name: summarize(rows[arm_name], planned_shots=n, alpha=alpha,
                    min_failures=design["precision"]["minimum_failures"],
                    max_relative_half_width=design["precision"]["maximum_relative_half_width"],
                    no_recovery_policy=design["precision"]["no_recovery_policy"])
                    for arm_name, _preset, _arm in ARMS}
                summaries[rate_key] = {"error_rate": rate, "look_shots": n, "arms": snapshot,
                                       "precision_met": all(x["precision_met"] for x in snapshot.values())}
                _atomic(progress_path, {"status": "running", "design_byte_sha256": design_digest,
                                        "rates": summaries, "updated_at": datetime.now(timezone.utc).isoformat()})
                if summaries[rate_key]["precision_met"]:
                    stop_at = n
                    break
        if stop_at is None:
            n = min(max_shots, max((max(arm_rows, default=-1) for arm_rows in rows.values()), default=-1) + 1)
            snapshot = {arm_name: summarize(rows[arm_name], planned_shots=n, alpha=alpha,
                min_failures=design["precision"]["minimum_failures"],
                max_relative_half_width=design["precision"]["maximum_relative_half_width"],
                no_recovery_policy=design["precision"]["no_recovery_policy"])
                for arm_name, _preset, _arm in ARMS}
            summaries[rate_key] = {"error_rate": rate, "look_shots": n, "arms": snapshot,
                                   "precision_met": False,
                                   "reason": "campaign_wall_cap" if wall_exhausted else "shot_cap_or_incomplete"}
            all_precise = False
        if wall_exhausted:
            break
    result = {"schema_version": 1, "status": "completed_precision" if all_precise and len(summaries) == len(design["error_rates"]) else "completed_with_inconclusive",
              "design_path": identity["design_path"], "design_byte_sha256": design_digest,
              "script_byte_sha256": script_digest,
              "started_at": identity["started_at"], "finished_at": datetime.now(timezone.utc).isoformat(),
              "rates": summaries, "stopping_rule": design["precision"],
              "interval_alpha_per_look_and_precision_metric": alpha,
              "interval_scope": "each arm/rate individually, simultaneous across six prespecified looks and two precision metrics; cell intervals cover five cells across six looks; no cross-arm hypothesis test",
              "sample_matching": "same physical sample identity at each code/rate/shot across four arms",
              "claim_limit": "uncalibrated controlled CSS adaptation; no source-faithful or universal ranking claim"}
    result["result_digest"] = _sha(result)
    _atomic(terminal_path, result)
    print(json.dumps({"status": result["status"], "result_digest": result["result_digest"],
                      "rates": {key: {"look_shots": value["look_shots"], "precision_met": value["precision_met"]}
                                for key, value in summaries.items()}}, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=Path("data/evidence/phase4-low-noise-ler-design-v1.json"))
    parser.add_argument("--output", type=Path, default=Path("data/results/phase4-memory-relay/low-noise-ler-v1"))
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        parser.error("--run is required; the finite design must be reviewed before launch")
    run_campaign(design_path=args.design, output_root=args.output)


if __name__ == "__main__":
    main()
