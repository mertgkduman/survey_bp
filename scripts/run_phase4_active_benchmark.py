#!/usr/bin/env python3
"""Build and retain v4 active-memory Phase 4 benchmark evidence.

This runner deliberately does not import the canonical kernel.  Each shot is
preflighted, run, and verified through the public CLI; journals are written
before a child starts so an interruption remains an identified outcome.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any, Mapping


SHOTS = 32
PUBLIC_BOUNDARY_SECONDS = 900
CODE_MANIFESTS = {
    "gross-bb-144": Path("data/manifests/phase4-memory-relay-bb144.json"),
    "b1-ghp-882": Path("data/manifests/phase4-memory-relay-b1.json"),
    "hgp-gallager-3-4-seed-20260923": Path("data/manifests/phase4-memory-relay-hgp.json"),
}
PRESETS = {
    "source_procedure": ("relay-source-internal-bp-v0.2.2", "source_internal_bp"),
    "canonical_default": ("relay-canonical-css-default-v1", "canonical_internal_bp"),
}
ACTIVE_SEMANTICS = "relay_v022_dynamic_affine_prior_css_adaptation"
FULL_WORK = {
    "gross-bb-144": {"belief_assemblies": 270720, "candidate_checks": 270720, "check_to_variable_updates": 812160, "variable_to_check_updates": 812160, "residual_priority_evaluations": 0, "bp_calls": 31, "intervention_actions": 0, "branch_expansions": 0, "branch_prunes": 0, "relay_transfers": 30, "fallback_calls": 0},
    "b1-ghp-882": {"belief_assemblies": 1658160, "candidate_checks": 1658160, "check_to_variable_updates": 4974480, "variable_to_check_updates": 4974480, "residual_priority_evaluations": 0, "bp_calls": 31, "intervention_actions": 0, "branch_expansions": 0, "branch_prunes": 0, "relay_transfers": 30, "fallback_calls": 0},
    "hgp-gallager-3-4-seed-20260923": {"belief_assemblies": 423000, "candidate_checks": 423000, "check_to_variable_updates": 1421280, "variable_to_check_updates": 1421280, "residual_priority_evaluations": 0, "bp_calls": 31, "intervention_actions": 0, "branch_expansions": 0, "branch_prunes": 0, "relay_transfers": 30, "fallback_calls": 0},
}
B1_THREE_LEG_WORK = {"belief_assemblies": 176400, "candidate_checks": 176400, "check_to_variable_updates": 529200, "variable_to_check_updates": 529200, "residual_priority_evaluations": 0, "bp_calls": 3, "intervention_actions": 0, "branch_expansions": 0, "branch_prunes": 0, "relay_transfers": 2, "fallback_calls": 0}


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return sha256(_canonical(value).encode()).hexdigest()


def _atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _command(root: Path, *args: str, timeout: float = PUBLIC_BOUNDARY_SECONDS) -> dict[str, Any]:
    run = subprocess.run(
        [sys.executable, "-m", "bp_registry.cli", *args], cwd=root, text=True,
        capture_output=True, timeout=timeout,
        env={**os.environ, "PYTHONPATH": str(root / "src"), "OMP_NUM_THREADS": "1"},
    )
    if run.returncode:
        raise RuntimeError(run.stderr or run.stdout)
    decoded = json.loads(run.stdout)
    if not isinstance(decoded, dict):
        raise ValueError("public CLI did not return an object")
    return decoded


def active_scan_plan() -> dict[str, object]:
    """Predeclare scans before outcomes: advance only on retained activation facts."""
    return {
        "schema_version": 1,
        "start_rate": 0.03,
        "conditional_rates": [0.05, 0.07],
        "codes": {
            "gross-bb-144": {"rates": [0.03, 0.05, 0.07]},
            "b1-ghp-882": {"rates": [0.03, 0.05, 0.07]},
            "hgp-gallager-3-4-seed-20260923": {"rates": [0.03]},
        },
        "trigger": {
            "advance_when": "all 32 retained Relay attempts at the current rate have fewer than 2 attempts with a later-leg activation",
            "select_when": "at least 2 of 32 retained Relay attempts have a later-leg activation",
            "terminal_when": "rate 0.07 is exhausted; retain the scan as precision-limited/inconclusive if activation remains sparse",
        },
        "no_outcome_dependent_retries": True,
    }


def build_active_manifest(base: Mapping[str, Any], *, arm: str, preset: str,
                          error_rate: float, first_leg_gamma: float,
                          later_center: float, later_width: float,
                          seed_identity: str, work_profile: str = "full31") -> dict[str, Any]:
    """Create a versioned 31/80/60 active-memory CSS adaptation manifest."""
    if arm not in {"baseline", "canonical_relay_31"}:
        raise ValueError("active benchmark arm must be baseline or canonical_relay_31")
    if preset not in PRESETS:
        raise ValueError("unknown active benchmark preset")
    value = deepcopy(dict(base))
    legs = 1 if arm == "baseline" else 31
    relay = dict(value["relay"])
    relay.update({
        "preset_name": PRESETS[preset][0], "procedure": PRESETS[preset][1],
        "fidelity_status": "controlled_component_adaptation",
        "total_leg_limit": legs, "first_leg_iteration_limit": 80,
        "later_leg_iteration_limit": 60, "solution_limit": 1,
        "legs": [{"max_iterations": 80}] + [{"max_iterations": 60} for _ in range(legs - 1)],
        "later_leg_memory": "disordered",
        "memory_tuning": {
            "semantics": ACTIVE_SEMANTICS, "first_leg_gamma": first_leg_gamma,
            "later_center": later_center, "later_width": later_width,
            "seed_identity": seed_identity, "rng_algorithm": "numpy.PCG64",
            "refresh": "per_later_leg",
        },
    })
    value["relay"] = relay
    if preset == "source_procedure":
        update = {"kind": "min_sum", "binding_id": "update-min-sum-v1", "state_lifetime": "message",
                  "owned_state": [], "requires": [], "provides": []}
        policies = dict(value["policies"])
        policies["update"] = update
        value["policies"] = policies
        value["numerical_profile"] = "cpu-float64-min-sum-v1"
        relay["numerical_profile"] = "cpu-float64-min-sum-v1"
    memory = dict(value["memory"])
    bindings = []
    for binding in memory.get("bindings", []):
        copied = dict(binding)
        if copied.get("kind") == "affine_prior":
            parameters = dict(copied.get("parameters", {}))
            parameters["alpha"] = first_leg_gamma
            copied["parameters"] = parameters
        bindings.append(copied)
    memory["bindings"] = bindings
    value["memory"] = memory
    code_id = value["artifact"]["code_id"]
    if work_profile == "b1_three_leg" and code_id == "b1-ghp-882":
        work = B1_THREE_LEG_WORK
    elif work_profile == "full31":
        work = FULL_WORK[code_id]
    else:
        raise ValueError("unknown active benchmark work profile")
    budgets = dict(value["budgets"])
    budgets["max_shots"] = SHOTS
    for scope in ("shot", "search", "attempt"):
        item = dict(budgets[scope])
        item["max_iterations"] = 80
        item["work_limits"] = dict(work)
        budgets[scope] = item
    value["budgets"] = budgets
    value["run_id"] = f"{base['run_id']}-active-v4-{preset}-{arm}-p{error_rate:.3f}".replace(".", "")
    value["error_rate"] = error_rate
    randomness = dict(value["randomness"])
    randomness["physical_sample_identity"] = f"{randomness['physical_sample_identity']}-active-v4-p{error_rate:.3f}".replace(".", "")
    value["randomness"] = randomness
    return value


def _events(path: Path) -> list[dict[str, Any]]:
    events = path / "events.jsonl"
    return [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines() if line] if events.exists() else []


def _active_facts(events: list[Mapping[str, Any]], shot_id: int) -> list[dict[str, Any]]:
    facts = []
    for event in events:
        if event.get("shot_id") != shot_id:
            continue
        data = event.get("data")
        if isinstance(data, Mapping) and (data.get("relay_memory_mode") == "dynamic_affine_prior_each_source_iteration" or data.get("relay_legs") is not None):
            facts.append(dict(data))
    return facts


def _active_memory_proven(attempt: Mapping[str, Any]) -> bool:
    """Require core's explicit dynamic mode and applied memory for every executed leg."""
    facts = attempt.get("active_memory_facts", [])
    if not isinstance(facts, list) or not any(fact.get("relay_memory_mode") == "dynamic_affine_prior_each_source_iteration" for fact in facts if isinstance(fact, Mapping)):
        return False
    memory_legs = [leg for fact in facts if isinstance(fact, Mapping) for leg in fact.get("relay_legs", []) if isinstance(leg, Mapping)]
    executed = attempt.get("distinct_leg_indices", [])
    return bool(executed) and len(memory_legs) >= len(executed) and all(
        isinstance(leg.get("memory"), Mapping) and leg["memory"].get("applied_each_source_iteration") is True
        for leg in memory_legs
    )


def _attempt_from_events(events: list[Mapping[str, Any]], shot_id: int) -> dict[str, object]:
    terminal = next((event for event in reversed(events) if event.get("shot_id") == shot_id and event.get("kind") == "termination"), None)
    begin = next((event for event in events if event.get("shot_id") == shot_id and event.get("kind") == "shot_begin"), None)
    work: dict[str, int] = {}
    legs: set[int] = set()
    for event in events:
        if event.get("shot_id") != shot_id or event.get("kind") != "work":
            continue
        for leaf in event.get("data", {}).get("relay_work_leaves", []):
            if leaf.get("kind") == "leg":
                legs.add(int(leaf["leg_index"]))
                for name, amount in leaf.get("work_vector", {}).items():
                    if isinstance(amount, int):
                        work[name] = work.get(name, 0) + amount
    return {"termination": None if terminal is None else terminal.get("termination"),
            "terminal": {} if terminal is None else terminal.get("data", {}),
            "sample_identity": None if begin is None else begin.get("sample_seed_identity"),
            "work_vector": work, "distinct_leg_indices": sorted(legs),
            "active_memory_facts": _active_facts(events, shot_id)}


def _distribution(values: list[float | None]) -> dict[str, object]:
    seen = sorted(value for value in values if isinstance(value, float))
    result: dict[str, object] = {"count": len(values), "observed_count": len(seen), "values": values}
    if seen:
        result.update({"min": seen[0], "max": seen[-1], "mean": sum(seen) / len(seen),
                       "p95": seen[min(len(seen) - 1, int(.95 * (len(seen) - 1)))]})
    return result


def run_canonical_arm(*, root: Path, manifest: Mapping[str, Any], output: Path) -> dict[str, object]:
    """Run 32 durable public canonical attempts and verify every terminal."""
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    expected_manifest = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != expected_manifest:
        raise FileExistsError("refusing to overwrite a retained active benchmark manifest with different bytes")
    if not manifest_path.exists():
        _atomic(manifest_path, manifest)
    _atomic(output / "preflight.json", _command(root, "preflight", str(manifest_path)))
    journal_path, run_path = output / "attempts.json", output / "run"
    attempts: list[dict[str, Any]] = json.loads(journal_path.read_text()) if journal_path.exists() else []
    retained = {item["shot_id"] for item in attempts}
    for shot in range(SHOTS):
        if shot in retained:
            continue
        attempts.append({"shot_id": shot, "status": "incomplete_interrupted", "manifest_sha256": _digest(manifest)})
        _atomic(journal_path, attempts)
        began, error, run, verify = perf_counter(), None, None, None
        deadline = began + PUBLIC_BOUNDARY_SECONDS
        try:
            run = _command(root, "canonical", str(manifest_path), "--output", str(run_path), "--shot", str(shot), timeout=max(.001, deadline - perf_counter()))
            verify = _command(root, "verify-canonical-shot", str(manifest_path), str(run_path), "--shot", str(shot), timeout=max(.001, deadline - perf_counter()))
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as caught:
            error = str(caught)
        fact = _attempt_from_events(_events(run_path), shot)
        attempts[-1] = {"shot_id": shot, "status": "completed" if error is None and fact["termination"] is not None else "incomplete_public_boundary",
                        "manifest_sha256": _digest(manifest), "failure": error, **fact,
                        "public_boundary": {"run": run, "verify": verify, "elapsed_seconds": perf_counter() - began}}
        _atomic(journal_path, attempts)
    complete = len(attempts) == SHOTS and all(x["status"] == "completed" for x in attempts)
    leg_counts = [len(x["distinct_leg_indices"]) for x in attempts]
    work_totals: dict[str, int] = {}
    for attempt in attempts:
        for name, amount in attempt["work_vector"].items():
            work_totals[name] = work_totals.get(name, 0) + amount
    return {"attempts": attempts, "status": "completed" if complete else "incomplete_canonical_arm",
            "manifest_sha256": _digest(manifest), "sample_namespace": manifest["randomness"]["physical_sample_identity"],
            "active_memory_verified": complete and all(_active_memory_proven(x) for x in attempts),
            "public_command_wall_seconds": _distribution([x.get("public_boundary", {}).get("elapsed_seconds") for x in attempts]),
            "distinct_leg_count_distribution": _distribution([float(count) for count in leg_counts]),
            "raw_work": {"availability": "observed", "total": work_totals,
                         "per_shot": [x["work_vector"] for x in attempts]},
            "termination_counts": {key: sum(x.get("termination") == key for x in attempts) for key in sorted({x.get("termination") for x in attempts if x.get("termination")})}}


def native_reuse_evidence(*, root: Path, active_manifest_path: Path, retained_observations_path: Path) -> dict[str, object]:
    """Prove exact public observation reuse before accepting old native outcomes."""
    retained = json.loads(retained_observations_path.read_text(encoding="utf-8"))
    if not isinstance(retained, list) or any(not isinstance(item, Mapping) or "observation_sha256" not in item for item in retained):
        return {"status": "native_rerun_required", "reason": "retained native evidence lacks byte-exact public observation digests", "retained_observations_path": str(retained_observations_path)}
    by_shot = {item["shot_id"]: item["observation_sha256"] for item in retained}
    observed = [_command(root, "canonical-observation", str(active_manifest_path), "--shot", str(shot)) for shot in range(SHOTS)]
    observation_digests = [_digest(item) for item in observed]
    matches = [digest == by_shot.get(shot) for shot, digest in enumerate(observation_digests)]
    return {"status": "reusable_exact_observations" if all(matches) else "native_rerun_required",
            "retained_observations_path": str(retained_observations_path), "sample_identities": [item.get("sample_identity") for item in observed], "observation_sha256": observation_digests,
            "matching_shots": matches, "matched_count": sum(matches), "expected_count": SHOTS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-plan", action="store_true")
    args = parser.parse_args()
    if args.scan_plan:
        print(json.dumps(active_scan_plan(), indent=2, sort_keys=True))
        return
    parser.error("this reusable module is invoked by the v4 campaign orchestrator; use --scan-plan for its prespecified scan contract")


if __name__ == "__main__":
    main()
