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
import subprocess
import sys
from typing import Any, Mapping


AUTHOR_REPOSITORY = "https://github.com/trmue/relay.git"
AUTHOR_COMMIT = "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
AUTHOR_TREE = "5f6f112429e62112ba71fbff45f4e16247725fbc"
STAGES = frozenset({"benchmark", "calibration", "evaluation", "factorial", "native", "trace"})
ARMS = ("source_procedure", "canonical_default", "native_v022")
_NATIVE_TIMEOUT_SECONDS = 90


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _json_command(repository_root: Path, *arguments: str) -> dict[str, Any]:
    """Invoke the public CLI only; no canonical execution internals are imported here."""
    completed = subprocess.run(
        [sys.executable, "-m", "bp_registry.cli", *arguments], cwd=repository_root,
        text=True, capture_output=True, timeout=300,
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
payload = json.loads(os.environ["RELAY_V022_PAYLOAD"])
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
    completed = subprocess.run(
        [str(environment / "bin/python"), "-c", program], cwd=source, text=True, capture_output=True,
        timeout=_NATIVE_TIMEOUT_SECONDS, env={**os.environ, "PYTHONNOUSERSITE": "1", "RELAY_V022_SOURCE": str(source), "RELAY_V022_PAYLOAD": _canonical_json(serializable)},
    )
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
            "pre_iter": 1, "num_sets": 1, "set_max_iter": 1, "stopping_criterion": "pre_iter", "logging": False,
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
        if existing.get("identity") == {"stage_identity": overall_identity, "arms": identities} and existing.get("status") == "completed":
            return {**existing, "reused": True, "stage_record": str(stage_record)}
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
    args = parser.parse_args()
    print(json.dumps(run_stage(repository_root=Path(__file__).resolve().parents[1], manifest_path=args.manifest, stage=args.stage, output_root=args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
