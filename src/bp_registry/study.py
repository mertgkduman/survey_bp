"""One entry point for verified cached results or canonical CSS execution."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
from typing import Any

from .cli import run_canonical, verify_run
from .artifacts import load_artifact
from .literature import LiteraturePolicy, parse_literature_policy
from .manifests import (
    CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4,
    CanonicalExperimentV5, CanonicalExperimentV6, CanonicalExperimentV7, parse_manifest, preflight,
)


_ROLES = (
    "update", "schedule", "state_memory", "intervention", "stopping", "selection", "postprocessing",
)
_LIFETIMES = {
    "update": "message", "schedule": "iteration", "state_memory": "attempt",
    "intervention": "search", "stopping": "iteration", "selection": "attempt",
    "postprocessing": "attempt",
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _read_object(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".toml":
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("policy/study files must be .json or .toml")
    if not isinstance(value, dict):
        raise ValueError(f"expected an object in {path}")
    return value


def _source_identity() -> str:
    root = Path(__file__).resolve().parent
    identities = {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
                  for path in sorted(root.rglob("*.py"))}
    return sha256(_json_bytes(identities)).hexdigest()


def _write_once(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"frozen study file differs: {path}")
    else:
        path.write_bytes(content)


@contextmanager
def _study_lock(path: Path):
    """Serialize writes for one evidence identity on the shared HPC filesystem."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _expanded_policies(decoder: dict[str, Any], *, schema_version: int) -> dict[str, Any]:
    required = {"schema_version", "engine", *_ROLES}
    extension = (
        {"memory", "relay"} if schema_version == 4 else
        {"intervention", "intervention_limits"} if schema_version == 5 else
        {"memory", "intervention", "intervention_limits"} if schema_version == 6 else
        {"ensemble", "list_selection", "vote"} if schema_version == 7 else set()
    )
    allowed = required | extension
    if not required <= set(decoder) or not set(decoder) <= allowed:
        raise ValueError("canonical decoder must declare engine, schema_version, and all seven policy roles")
    if schema_version == 4 and "memory" not in decoder:
        raise ValueError("schema v4 decoder must declare its ordered memory bindings")
    if schema_version in (5, 6) and not {"intervention", "intervention_limits"} <= set(decoder):
        raise ValueError("schema v5/v6 decoder must declare intervention controls and limits")
    if schema_version == 6 and "memory" not in decoder:
        raise ValueError("schema v6 decoder must declare its ordered memory bindings")
    if schema_version == 7 and not {"ensemble", "list_selection"} <= set(decoder):
        raise ValueError("schema v7 decoder must declare its complete ensemble and list selection")
    if decoder["schema_version"] != 1 or decoder["engine"] != "canonical_css":
        raise ValueError("unsupported canonical decoder file version or engine")
    expanded = {}
    for role in _ROLES:
        value = decoder[role]
        if isinstance(value, str):
            value = {"kind": value}
        if not isinstance(value, dict) or not isinstance(value.get("kind"), str):
            raise ValueError(f"{role} requires a registered policy kind")
        kind = value["kind"]
        binding_controls = {name: control for name, control in value.items()
                            if name in {"kind", "parameter_assignment"}}
        expanded[role] = {
            "binding_id": f"research-{role.replace('_', '-')}-{kind.replace('_', '-')}",
            "state_lifetime": _LIFETIMES[role],
            **binding_controls,
        }
    return expanded


def _apply_decoder_stopping_cap(study: dict[str, Any], decoder: dict[str, Any]) -> None:
    """Make a decoder-owned sweep cap explicit in each public manifest budget."""
    control = decoder["stopping"].get("max_iterations")
    if control is None:
        return
    if type(control) is not int or control < 1:
        raise ValueError("stopping.max_iterations must be a positive integer")
    budgets = study.get("budgets")
    if not isinstance(budgets, dict):
        raise ValueError("canonical study must declare explicit budgets")
    for scope in ("attempt", "search", "shot"):
        budget = budgets.get(scope)
        if not isinstance(budget, dict) or budget.get("max_iterations") != control:
            raise ValueError("study budgets must equal the decoder stopping.max_iterations cap")


def _validated_artifact_dimensions(study: dict[str, Any]) -> tuple[int, int]:
    """Return ``(n, m_z)`` only after validating pinned artifact bytes."""
    artifact = study.get("artifact")
    if not isinstance(artifact, dict):
        raise ValueError("canonical study must declare an artifact before symbolic policy resolution")
    required = {"root", "path", "raw_sha256", "semantic_sha256"}
    if not required <= set(artifact):
        raise ValueError("canonical study artifact is incomplete for symbolic policy resolution")
    loaded = load_artifact(
        artifact["root"], artifact["path"], expected_raw_sha256=artifact["raw_sha256"],
        expected_semantic_sha256=artifact["semantic_sha256"],
    )
    return int(loaded.code.hz.shape[1]), int(loaded.code.hz.shape[0])


def _validated_artifact_block_length(study: dict[str, Any]) -> int:
    """Preserve the public test seam for source R=n resolution."""
    return _validated_artifact_dimensions(study)[0]


def _request_receipt(policy: LiteraturePolicy | None, decoder_path: Path, *, computation_key: str,
                     execution_identity: str, verification: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Bind an immutable source document to verified shared computation evidence."""
    if policy is None:
        raw_identity = sha256(decoder_path.read_bytes()).hexdigest()
        provenance_identity = sha256(_json_bytes({"legacy_decoder": str(decoder_path)})).hexdigest()
        source_path = str(decoder_path)
    else:
        raw_identity = policy.raw_document_identity
        provenance_identity = policy.provenance_identity
        source_path = str(policy.source_path)
    request = {
        "schema_version": 1,
        "computation_key": computation_key,
        "executable_policy_sha256": execution_identity,
        "provenance_sha256": provenance_identity,
        "raw_document_sha256": raw_identity,
        "source_path": source_path,
    }
    request_id = sha256(_json_bytes(request)).hexdigest()
    # Verification timestamps are observations, not the identity of a stable
    # computation receipt.  Preserve the replay-relevant verification facts.
    request["verification"] = {name: value for name, value in verification.items() if name != "verified_at"}
    return request_id, request


def _ensure_canonical(study_path: Path, decoder: dict[str, Any], results_root: Path,
                      *, policy: LiteraturePolicy | None = None, decoder_path: Path | None = None) -> dict[str, Any]:
    study = _read_object(study_path)
    if "policies" in study or study.get("schema_version") not in (2, 3, 4, 5, 6, 7):
        raise ValueError("canonical study must be a schema v2-v7 experiment without policies")
    if study["schema_version"] == 4 and ("memory" in study or "relay" in study):
        raise ValueError("schema v4 memory and Relay controls belong in the decoder file")
    if study["schema_version"] in (5, 6) and ({"intervention", "intervention_limits", "memory"} & set(study)):
        raise ValueError("schema v5/v6 intervention and memory controls belong in the decoder file")
    if study["schema_version"] == 7 and ({"ensemble", "list_selection", "vote"} & set(study)):
        raise ValueError("schema v7 ensemble, list selection, and vote controls belong in the decoder file")
    if not isinstance(study.get("randomness"), dict) or not study["randomness"].get("physical_sample_identity"):
        raise ValueError("study must explicitly pin physical_sample_identity for matched comparisons")
    artifact = study.get("artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("root"), str):
        raise ValueError("study artifact must declare a root")
    study["artifact"] = {**artifact, "root": str((study_path.parent / artifact["root"]).resolve())
                         if not Path(artifact["root"]).is_absolute() else artifact["root"]}
    if policy is not None and policy.requires_artifact_block_length():
        # R=n is source data, not a default.  Resolve only after byte and
        # semantic validation, before executable/cache identities are made.
        code_block_length, code_check_count = _validated_artifact_dimensions(study)
        decoder = policy.decoder_projection(
            code_block_length=code_block_length, code_check_count=code_check_count,
        )
    policies = _expanded_policies(decoder, schema_version=study["schema_version"])
    _apply_decoder_stopping_cap(study, decoder)
    policy_payload = {"decoder": decoder, "policies": policies}
    if study["schema_version"] == 4:
        policy_payload["memory"] = decoder["memory"]
        policy_payload["relay"] = decoder.get("relay")
        study["memory"] = decoder["memory"]
        study["relay"] = decoder.get("relay")
    if study["schema_version"] in (5, 6):
        study["intervention"] = decoder["intervention"]
        study["intervention_limits"] = decoder["intervention_limits"]
    if study["schema_version"] == 6:
        study["memory"] = decoder["memory"]
    if study["schema_version"] == 7:
        study["ensemble"] = decoder["ensemble"]
        study["list_selection"] = decoder["list_selection"]
        if "vote" in decoder:
            study["vote"] = decoder["vote"]
    policy_identity = sha256(_json_bytes(policy_payload)).hexdigest()
    study["run_id"] = f"{study['run_id']}-{policy_identity[:12]}"
    study["policies"] = policies
    parsed = parse_manifest(study)
    if not isinstance(parsed, (CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4, CanonicalExperimentV5, CanonicalExperimentV6, CanonicalExperimentV7)):
        raise ValueError("this public study runner supports canonical CSS schema v2-v7")
    preflight(study)
    manifest_bytes = _json_bytes(study)
    source_identity = _source_identity()
    key = sha256(manifest_bytes + source_identity.encode()).hexdigest()
    output = (results_root / key).resolve()
    receipt = {"schema_version": 1, "engine": "canonical_css", "cache_key": key,
               "manifest_sha256": sha256(manifest_bytes).hexdigest(),
               "policy_sha256": policy_identity, "source_sha256": source_identity}
    with _study_lock(results_root / ".locks" / f"{key}.lock"):
        manifest_path = output / "manifest.json"
        _write_once(manifest_path, manifest_bytes)
        receipt_path = output / "cache-receipt.json"
        if (output / "result.json").exists():
            if not receipt_path.is_file() or json.loads(receipt_path.read_text()) != receipt:
                raise ValueError("cached result is missing or conflicts with its source receipt")
            verified = verify_run(output)
            status = "reused"
        else:
            run_canonical(manifest_path, output)
            verified = verify_run(output)
            _write_once(receipt_path, _json_bytes(receipt))
            status = "computed"
        request_id, request = _request_receipt(
            policy, decoder_path or Path("<in-memory-decoder>"), computation_key=key,
            execution_identity=policy_identity, verification=verified,
        )
        _write_once(output / "request-receipts" / f"{request_id}.json", _json_bytes(request))
        return {"status": status, "output": str(output), "cache_key": key,
                "request_receipt": request_id,
                "result": json.loads((output / "result.json").read_text()), "verification": verified}


def _verify_campaign(output: Path, design_path: Path) -> dict[str, Any]:
    design = _read_object(design_path)
    manifest = json.loads((output / "publication-manifest.json").read_text())
    expected = {"design.json", "seal.json", "selection-lock.json", "result.json", "REPORT.md", "study.html"}
    expected |= {f"{cohort}/{rate}/{profile}/{name}"
                 for cohort in design["cohorts"] for rate in design["rates"]
                 for profile in design["profiles"]
                 for name in ("manifest.json", "result.json", "events.jsonl.gz")}
    if (manifest.get("study_id") != "fair-beam-relay-css-v2"
            or manifest.get("assessment_status") != "controlled_evaluation_complete"
            or set(manifest.get("files", {})) != expected):
        raise ValueError("campaign publication manifest is missing or incomplete")
    if (output / "design.json").read_bytes() != design_path.read_bytes():
        raise ValueError("published campaign design differs from requested study")
    for name, identity in manifest["files"].items():
        path = output / name
        if not path.resolve().is_relative_to(output.resolve()) or not path.is_file():
            raise ValueError(f"campaign package file is missing: {name}")
        if path.stat().st_size != identity["bytes"] or sha256(path.read_bytes()).hexdigest() != identity["sha256"]:
            raise ValueError(f"campaign package file differs: {name}")
    result = json.loads((output / "result.json").read_text())
    if (result.get("assessment_status") != "controlled_evaluation_complete"
            or result.get("design_sha256") != sha256(design_path.read_bytes()).hexdigest()
            or result.get("seal_sha256") != sha256((output / "seal.json").read_bytes()).hexdigest()
            or result.get("selection_lock_sha256") != sha256((output / "selection-lock.json").read_bytes()).hexdigest()):
        raise ValueError("campaign result does not match requested study")
    lock = json.loads((output / "selection-lock.json").read_text())
    for cohort in design["cohorts"]:
        for rate in design["rates"]:
            for profile in design["profiles"]:
                shard = output / cohort / rate / profile
                arm = json.loads((shard / "result.json").read_text())
                expected_digest = (lock["selection_ledger_sha256"][rate][profile]
                                   if cohort == "selection" else result["evaluation_ledger_sha256"][rate][profile])
                if arm.get("ledger_sha256") != expected_digest:
                    raise ValueError("campaign ledger hash differs from lock/report")
                actual = sha256()
                with gzip.open(shard / "events.jsonl.gz", "rb") as source:
                    while block := source.read(1024 * 1024):
                        actual.update(block)
                if actual.hexdigest() != expected_digest:
                    raise ValueError("campaign compressed ledger differs from verified evidence")
    return result


def _ensure_campaign(study_path: Path, decoder: dict[str, Any], results_root: Path, workers: int) -> dict[str, Any]:
    if set(decoder) != {"schema_version", "engine", "method", "damping", "profile"}:
        raise ValueError("fair-leg decoder requires schema_version, engine, method, damping, profile")
    if (decoder["schema_version"] != 1 or decoder["engine"] != "fair_beam_relay_css_v2"
            or decoder["method"] not in ("beam", "relay")
            or type(decoder["damping"]) not in (int, float)
            or decoder["damping"] not in (1.0, 0.5)
            or decoder["profile"] not in ("selected", "i05", "i10", "i20")):
        raise ValueError("unsupported fair-leg decoder configuration")
    root = study_path.resolve().parents[2]
    runner = root / "scripts/run_fair_beam_relay_campaign.py"
    publisher = root / "scripts/package_fair_beam_relay_campaign_v2.py"
    if not runner.is_file() or not publisher.is_file():
        raise ValueError("producing this registered campaign requires its repository scripts")
    output = (results_root / "fair-beam-relay-css-v2").resolve()
    with _study_lock(results_root / ".locks" / "fair-beam-relay-css-v2.lock"):
        existed = (output / "publication-manifest.json").is_file()
        if not existed:
            if output.exists() and any(output.iterdir()):
                raise ValueError("incomplete campaign output exists; inspect or resume its shard runner explicitly")
            common = ["--design", str(study_path), "--output", str(output)]
            def execute(command: str, *extra: str) -> None:
                env = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
                subprocess.run([sys.executable, str(runner), command, *common, *extra],
                               cwd=root, env=env, stdout=subprocess.DEVNULL, check=True)
            execute("prepare")
            design = _read_object(study_path)
            for cohort in ("selection", "evaluation"):
                if cohort == "evaluation":
                    execute("select", "--workers", str(workers))
                for rate in design["rates"]:
                    for profile in design["profiles"]:
                        execute("run", "--cohort", cohort, "--rate", rate, "--profile", profile,
                                "--workers", str(workers))
            execute("report", "--workers", str(workers))
            # The packaging module has a reusable function while its published CLI
            # intentionally keeps its original, source-bound default paths.
            import importlib.util
            sys.path.insert(0, str(root / "scripts"))
            spec = importlib.util.spec_from_file_location("_fair_campaign_package", publisher)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module._package(study_path, output)
        result = _verify_campaign(output, study_path)
        key = f"g{int(decoder['damping'] * 1000):04d}"
        arm = {rate: (result["selected_summaries"][rate][key][decoder["method"]]
                      if decoder["profile"] == "selected" else
                      result["parameter_grid"][rate][key][decoder["profile"]][decoder["method"]])
               for rate in result["selected_summaries"]}
        return {"status": "reused" if existed else "computed", "output": str(output),
                "study_id": "fair-beam-relay-css-v2", "method": decoder["method"],
                "damping": decoder["damping"], "profile": decoder["profile"], "result": arm,
                "verification": {"package_files": 43, "assessment_status": result["assessment_status"]}}


def ensure_study(study_file: str | Path, decoder_file: str | Path, *,
                 results_root: str | Path | None = None, workers: int = 1) -> dict[str, Any]:
    """Verify and reuse a result, or run the requested decoder and verify it.

    Canonical CSS policies are declarative. The registered BB72 fair-leg campaign
    exposes published BeamSearch/RelayBP settings through the same entry point.
    """
    if type(workers) is not int or workers < 1:
        raise ValueError("workers must be a positive integer")
    study_path = Path(study_file).resolve()
    decoder_path = Path(decoder_file).resolve()
    raw_decoder = _read_object(decoder_path)
    policy: LiteraturePolicy | None = None
    if raw_decoder.get("record_kind") in {"literature_policy", "literature_policy_spec"} or decoder_path.name.endswith(".spec.toml"):
        policy = parse_literature_policy(decoder_path)
        if policy.disposition != "runnable":
            return {"status": "non_runnable", "disposition": policy.disposition,
                    "source_path": str(policy.source_path), "blocking_features": list(policy.blocking_features)}
        # Symbolic source controls are resolved inside ``_ensure_canonical``
        # after the selected artifact is byte/semantically validated.
        decoder = {} if policy.requires_artifact_block_length() else policy.decoder_projection()
    else:
        decoder = raw_decoder
    study = _read_object(study_path)
    if study.get("study_id") == "fair-beam-relay-css-v2":
        default_root = study_path.parents[2] / "data/results"
        return _ensure_campaign(study_path, decoder, Path(results_root or default_root), workers)
    default_root = Path.cwd() / "bp-registry-results"
    return _ensure_canonical(study_path, decoder, Path(results_root or default_root),
                             policy=policy, decoder_path=decoder_path)
