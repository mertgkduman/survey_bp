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


def _json_command(repository_root: Path, *arguments: str) -> dict[str, Any]:
    """Invoke the public CLI only; no canonical execution internals are imported here."""
    completed = subprocess.run(
        [sys.executable, "-m", "bp_registry.cli", *arguments], cwd=repository_root,
        text=True, capture_output=True, timeout=900,
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
            "pre_iter": 80, "num_sets": 30, "set_max_iter": 60, "stopping_criterion": "pre_iter", "logging": False,
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


def _benchmark_manifest(base: Mapping[str, object], *, arm: str) -> dict[str, object]:
    """Build one bounded, identified benchmark arm from a qualified V4 manifest."""
    value = deepcopy(dict(base))
    value["run_id"] = f"{base['run_id']}-benchmark-{arm}"
    value["error_rate"] = _BENCHMARK_CENTRAL_ERROR_RATE
    budgets = dict(value["budgets"])
    budgets["max_shots"] = _BENCHMARK_SHOTS
    multiplier = 1 if arm == "baseline" else 31
    for scope_name in ("shot", "search", "attempt"):
        scope = dict(budgets[scope_name])
        scope["max_iterations"] = 80
        limits = {name: amount * multiplier * 80 for name, amount in dict(scope["work_limits"]).items()}
        limits["bp_calls"] = multiplier
        limits["relay_transfers"] = max(0, multiplier - 1)
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
        f"shots={_BENCHMARK_SHOTS}; central_error_rate={_BENCHMARK_CENTRAL_ERROR_RATE}."
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


def _run_canonical_benchmark_arm(*, repository_root: Path, base: Mapping[str, object], arm: str, output: Path) -> dict[str, object]:
    """Use one bounded public CLI invocation per identified shot."""
    manifest = _benchmark_manifest(base, arm=arm)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _json_command(repository_root, "preflight", str(manifest_path))
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
        decode_wall_seconds: float | None = None
        verify_wall_seconds: float | None = None
        try:
            run = _json_command(repository_root, "canonical", str(manifest_path), "--output", str(run_path), "--shot", str(shot_id))
            decode_wall_seconds = perf_counter() - decode_started
            verify_started = perf_counter()
            verified = _json_command(repository_root, "verify-canonical-shot", str(manifest_path), str(run_path), "--shot", str(shot_id))
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


def _reuse_exact_canonical_benchmark_arm(*, repository_root: Path, base: Mapping[str, object], arm: str, output: Path) -> dict[str, object] | None:
    """Reuse only a complete old arm whose generated manifest bytes are identical."""
    manifest_path = output / "manifest.json"
    run_path = output / "run"
    if not manifest_path.is_file() or not (run_path / "events.jsonl").is_file():
        return None
    expected = _benchmark_manifest(base, arm=arm)
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


def _run_native_benchmark_arm(*, repository_root: Path, base: Mapping[str, object], output: Path) -> dict[str, object]:
    """Run each author-native shot separately so failures remain terminal benchmark facts."""
    output.mkdir(parents=True, exist_ok=True)
    source_record = _source_record(repository_root)
    relay_manifest = _benchmark_manifest(base, arm="canonical_relay_31")
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
    }


def run_benchmark(*, repository_root: Path, output_path: Path, job_id: str, artifact_run_id: str | None = None) -> dict[str, object]:
    """Retain the bounded D-23 benchmark once; an existing record is never silently replaced."""
    repository_root, output_path = repository_root.resolve(), output_path.resolve()
    if output_path.exists():
        raise FileExistsError(f"refusing to replace retained benchmark evidence: {output_path}")
    entitlement = _slurm_entitlement(job_id)
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
            for code_id, path in _BENCHMARK_MANIFESTS.items()
        },
    })[:16]
    root = output_path.parent / "benchmark-artifacts" / benchmark_run_id
    codes: dict[str, object] = {}
    for code_id, relative_manifest in _BENCHMARK_MANIFESTS.items():
        base = _read_json(repository_root / relative_manifest)
        if base["artifact"]["code_id"] != code_id:
            raise ValueError(f"benchmark manifest code identity drifted for {code_id}")
        code_root = root / code_id
        codes[code_id] = {
            "central_error_rate": _BENCHMARK_CENTRAL_ERROR_RATE,
            "manifest_sha256": sha256((repository_root / relative_manifest).read_bytes()).hexdigest(),
            "sample_namespace": base["randomness"]["physical_sample_identity"],
            "arms": {
                "baseline": _reuse_exact_canonical_benchmark_arm(repository_root=repository_root, base=base, arm="baseline", output=code_root / "baseline") or _run_canonical_benchmark_arm(repository_root=repository_root, base=base, arm="baseline", output=code_root / "baseline"),
                "canonical_relay_31": _reuse_exact_canonical_benchmark_arm(repository_root=repository_root, base=base, arm="canonical_relay_31", output=code_root / "canonical-relay-31") or _run_canonical_benchmark_arm(repository_root=repository_root, base=base, arm="canonical_relay_31", output=code_root / "canonical-relay-31"),
                "native_v022": _run_native_benchmark_arm(repository_root=repository_root, base=base, output=code_root / "native-v022"),
            },
        }
    result: dict[str, object] = {
        "schema_version": 1, "status": "completed_with_retained_incompletes", "purpose": "D-23 measured finite Phase 4 pilot benchmark",
        "benchmark_run_id": benchmark_run_id, "artifact_root": str(root.relative_to(repository_root)),
        "prior_incomplete_evidence": prior_incomplete_evidence,
        "sample_count_per_arm": _BENCHMARK_SHOTS, "entitlement": entitlement, "entitlement_digest": _digest(entitlement),
        "codes": codes,
        "command_boundaries": {
            "canonical": [sys.executable, "-m", "bp_registry.cli", "preflight|canonical|verify-run"],
            "native": ["approved exact author Relay v0.2.2", "per-shot timeout", _NATIVE_TIMEOUT_SECONDS],
        },
        "no_retry_policy": "Every failed or incomplete identified native attempt is retained; this benchmark does not retry it.",
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
    args = parser.parse_args()
    repository_root = Path(__file__).resolve().parents[1]
    if args.benchmark:
        if not args.slurm_job_id:
            raise SystemExit("--benchmark requires --slurm-job-id or SLURM_JOB_ID")
        print(json.dumps(run_benchmark(
            repository_root=repository_root,
            output_path=args.benchmark_output,
            job_id=args.slurm_job_id,
            artifact_run_id=args.benchmark_artifact_run_id,
        ), indent=2, sort_keys=True))
        return
    print(json.dumps(run_stage(repository_root=repository_root, manifest_path=args.manifest, stage=args.stage, output_root=args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
