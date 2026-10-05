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
from .manifests import CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4, parse_manifest, preflight


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
    allowed = required | ({"memory", "relay"} if schema_version == 4 else set())
    if not required <= set(decoder) or not set(decoder) <= allowed:
        raise ValueError("canonical decoder must declare engine, schema_version, and all seven policy roles")
    if schema_version == 4 and "memory" not in decoder:
        raise ValueError("schema v4 decoder must declare its ordered memory bindings")
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
        expanded[role] = {
            "binding_id": f"research-{role.replace('_', '-')}-{kind.replace('_', '-')}",
            "state_lifetime": _LIFETIMES[role],
            **value,
        }
    return expanded


def _ensure_canonical(study_path: Path, decoder: dict[str, Any], results_root: Path) -> dict[str, Any]:
    study = _read_object(study_path)
    if "policies" in study or study.get("schema_version") not in (2, 3, 4):
        raise ValueError("canonical study must be a schema v2/v3/v4 experiment without policies")
    if study["schema_version"] == 4 and ("memory" in study or "relay" in study):
        raise ValueError("schema v4 memory and Relay controls belong in the decoder file")
    if not isinstance(study.get("randomness"), dict) or not study["randomness"].get("physical_sample_identity"):
        raise ValueError("study must explicitly pin physical_sample_identity for matched comparisons")
    artifact = study.get("artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("root"), str):
        raise ValueError("study artifact must declare a root")
    study["artifact"] = {**artifact, "root": str((study_path.parent / artifact["root"]).resolve())
                         if not Path(artifact["root"]).is_absolute() else artifact["root"]}
    policies = _expanded_policies(decoder, schema_version=study["schema_version"])
    policy_payload = {"policies": policies}
    if study["schema_version"] == 4:
        policy_payload["memory"] = decoder["memory"]
        policy_payload["relay"] = decoder.get("relay")
        study["memory"] = decoder["memory"]
        study["relay"] = decoder.get("relay")
    policy_identity = sha256(_json_bytes(policy_payload)).hexdigest()
    study["run_id"] = f"{study['run_id']}-{policy_identity[:12]}"
    study["policies"] = policies
    parsed = parse_manifest(study)
    if not isinstance(parsed, (CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4)):
        raise ValueError("this public study runner supports canonical CSS schema v2/v3/v4")
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
            return {"status": "reused", "output": str(output), "cache_key": key,
                    "result": json.loads((output / "result.json").read_text()), "verification": verified}
        run_canonical(manifest_path, output)
        verified = verify_run(output)
        _write_once(receipt_path, _json_bytes(receipt))
        return {"status": "computed", "output": str(output), "cache_key": key,
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
    decoder = _read_object(Path(decoder_file).resolve())
    study = _read_object(study_path)
    if study.get("study_id") == "fair-beam-relay-css-v2":
        default_root = study_path.parents[2] / "data/results"
        return _ensure_campaign(study_path, decoder, Path(results_root or default_root), workers)
    default_root = Path.cwd() / "bp-registry-results"
    return _ensure_canonical(study_path, decoder, Path(results_root or default_root))
