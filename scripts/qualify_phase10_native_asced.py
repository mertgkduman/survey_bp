#!/usr/bin/env python3
"""Build, run, and verify the approved isolated native aSCED reference."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import venv
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "data" / "native" / "phase10-asced-source-spec.json"
APPROVED_SPEC_SHA256 = "55359962431c055cf971171f81d75997282beb29e8928a8d82e023fbb6c1f24e"
APPROVAL_SIGNAL = f"approved phase10 native spec {APPROVED_SPEC_SHA256}"
COMMIT_LENGTH = 40


class QualificationError(RuntimeError):
    """A failed native step whose diagnostics must become receipt evidence."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_spec(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("aSCED specification must be a JSON object")
    return data


def _download(url: str) -> bytes:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "bp-registry-native-qualification"})
    with urlopen(request, timeout=60) as response:  # nosec B310: URLs are exact spec inputs.
        return response.read()


def _require_source(spec: dict[str, Any]) -> dict[str, Any]:
    source = spec.get("source")
    if not isinstance(source, dict):
        raise ValueError("specification is missing source")
    commit = source.get("commit")
    if not isinstance(commit, str) or len(commit) != COMMIT_LENGTH:
        raise ValueError("source commit must be an exact full 40-character commit")
    if source.get("repository") != "https://github.com/kit-cel/quantum_asced.git":
        raise ValueError("only kit-cel/quantum_asced is an allowed native source")
    digests, algorithms = source.get("source_digests"), source.get("algorithm_files")
    if not isinstance(digests, dict) or not digests or not isinstance(algorithms, list) or not algorithms:
        raise ValueError("source digests and algorithm-file guard are required")
    if any(not isinstance(item, str) or item not in digests for item in algorithms):
        raise ValueError("every guarded algorithm file must have a source digest")
    return source


def verify_source_spec(spec: dict[str, Any]) -> None:
    """Validate immutable source-spec structure without changing its bytes."""
    if spec.get("schema") != "phase10-asced-source-spec-v1":
        raise ValueError("unsupported aSCED source-spec schema")
    source = _require_source(spec)
    if source["commit"] != "816772071486615dfc7d71d1e15df597edc58a26":
        raise ValueError("native source must remain pinned to the audited exact commit")
    discrepancies = spec.get("discrepancies")
    required = {"pybind11_gitlink", "demo_path", "license", "pauli_translation", "selection", "channel", "instrumentation"}
    if not isinstance(discrepancies, dict) or set(discrepancies) != required:
        raise ValueError("every audited discrepancy must remain explicit")
    translation = discrepancies["pauli_translation"]
    if not isinstance(translation, dict) or translation.get("native") != ["I", "X", "Z", "Y"]:
        raise ValueError("native Pauli order must remain explicitly translated")
    verify_build_proposal(spec)


def verify_build_proposal(spec: dict[str, Any]) -> None:
    proposal = spec.get("build_proposal")
    if not isinstance(proposal, dict):
        raise ValueError("build proposal is required")
    root = proposal.get("disposable_root")
    if not isinstance(root, str) or root != "/tmp/phase10-asced-native":
        raise ValueError("build proposal requires the approved absolute disposable root")
    if proposal.get("primary_environment_access") != "forbidden":
        raise ValueError("build proposal must not reach the primary environment")
    packages = proposal.get("python_packages")
    expected = {"numpy", "galois", "matplotlib", "scikit-build-core", "pybind11"}
    if not isinstance(packages, dict) or set(packages) != expected:
        raise ValueError("proposal requires exactly the five reviewed Python packages")
    for name, locked in packages.items():
        if not isinstance(locked, dict) or locked.get("classification") != "SUS":
            raise ValueError(f"{name} must remain a SUS package input")
        if not isinstance(locked.get("artifact_url"), str) or not isinstance(locked.get("sha256"), str) or len(locked["sha256"]) != 64:
            raise ValueError(f"{name} artifact must have a SHA-256 digest")
    overlay, cmake, driver = proposal.get("pybind11_overlay"), proposal.get("cmake"), proposal.get("driver")
    if not isinstance(overlay, dict) or overlay.get("classification") != "human_reviewed_build_input":
        raise ValueError("pybind11 overlay must remain a separately reviewed build input")
    if not isinstance(cmake, dict) or cmake.get("classification") != "human_reviewed_build_input":
        raise ValueError("CMake must remain a separately reviewed build input")
    if not isinstance(cmake.get("executable"), str) or not cmake["executable"].startswith(root + "/") or cmake.get("ambient_path_fallback") != "forbidden":
        raise ValueError("only the recorded disposable-root CMake executable may be used")
    if not isinstance(driver, dict) or any(not isinstance(driver.get(k), str) or not driver[k].startswith(root + "/") for k in ("path", "source_checkout", "build_directory", "install_prefix")):
        raise ValueError("driver and build paths must be out-of-tree under the disposable root")
    guard = proposal.get("algorithm_guard")
    if not isinstance(guard, dict) or guard.get("allow_algorithm_modification") is not False:
        raise ValueError("algorithm-file guard must prohibit modification")


def audit_source(spec: dict[str, Any]) -> dict[str, Any]:
    verify_source_spec(spec)
    source = _require_source(spec)
    remote_commit = json.loads(_download(str(source["commit_api"])).decode("utf-8"))
    if not isinstance(remote_commit, dict) or remote_commit.get("sha") != source["commit"]:
        raise ValueError("remote did not resolve the exact audited commit")
    observed: dict[str, str] = {}
    for relative, expected in source["source_digests"].items():
        actual = _sha256(_download(f"https://raw.githubusercontent.com/kit-cel/quantum_asced/{source['commit']}/{relative}"))
        if actual != expected:
            raise ValueError(f"source digest mismatch for {relative}")
        observed[relative] = actual
    return {"commit": source["commit"], "source_digests": observed, "mode": "read_only"}


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, timeout: int = 600) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False, timeout=timeout)
    record = {"command": command, "cwd": str(cwd) if cwd else None, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    if result.returncode:
        raise QualificationError("command", json.dumps(record, sort_keys=True))
    return record


def _approval(spec_path: Path, summary: Path) -> str:
    digest = _file_sha256(spec_path)
    if digest != APPROVED_SPEC_SHA256:
        raise QualificationError("approval", "source-spec SHA-256 does not match the approved exact identity")
    if not summary.is_file() or APPROVAL_SIGNAL not in summary.read_text(encoding="utf-8"):
        raise QualificationError("approval", "approval summary lacks the exact approved phase10 native spec signal")
    return digest


def _algorithm_digests(source_dir: Path, spec: dict[str, Any]) -> dict[str, str]:
    source = _require_source(spec)
    actual: dict[str, str] = {}
    for relative, expected in source["source_digests"].items():
        path = source_dir / relative
        if not path.is_file():
            raise QualificationError("source", f"missing pinned source file {relative}")
        digest = _file_sha256(path)
        if digest != expected:
            raise QualificationError("source", f"source digest mismatch for {relative}")
        actual[relative] = digest
    return actual


def _write_receipt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prepare_source(spec: dict[str, Any], commands: list[dict[str, Any]]) -> Path:
    proposal, source = spec["build_proposal"], _require_source(spec)
    assert isinstance(proposal, dict)
    checkout = Path(str(proposal["driver"]["source_checkout"]))
    if checkout.exists():
        shutil.rmtree(checkout)
    checkout.parent.mkdir(parents=True, exist_ok=True)
    commands.append(_run(["git", "clone", "--no-checkout", str(source["repository"]), str(checkout)], timeout=180))
    commands.append(_run(["git", "fetch", "--depth", "1", "origin", str(source["commit"])], cwd=checkout, timeout=180))
    commands.append(_run(["git", "checkout", "--detach", str(source["commit"])], cwd=checkout))
    head = _run(["git", "rev-parse", "HEAD"], cwd=checkout)["stdout"].strip()
    tree = _run(["git", "rev-parse", "HEAD^{tree}"], cwd=checkout)["stdout"].strip()
    if head != source["commit"] or tree != source["tree"]:
        raise QualificationError("source", "checked out source commit/tree differs from the approved identity")
    return checkout


def _download_exact(url: str, destination: Path, expected: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(_download(url))
    if _file_sha256(destination) != expected:
        raise QualificationError("download", f"SHA-256 mismatch for {destination.name}")


def _build(spec_path: Path, summary: Path, receipt_path: Path) -> dict[str, Any]:
    spec = _load_spec(spec_path)
    verify_source_spec(spec)
    approval_digest = _approval(spec_path, summary)
    proposal = spec["build_proposal"]
    assert isinstance(proposal, dict)
    root = Path(str(proposal["disposable_root"]))
    commands: list[dict[str, Any]] = []
    receipt: dict[str, Any] = {"schema": "phase10-asced-build-receipt-v1", "source_spec_sha256": approval_digest, "approval_summary": str(summary), "disposable_root": str(root), "started_at": time.time(), "commands": commands}
    try:
        root.mkdir(parents=True, exist_ok=True)
        primary = ROOT / str(proposal["primary_environment"])
        receipt["primary_environment_sha256_before"] = _file_sha256(primary)
        source_dir = _prepare_source(spec, commands)
        receipt["source_digests_before"] = _algorithm_digests(source_dir, spec)
        downloads = root / "downloads"
        venv_dir = root / "venv"
        if venv_dir.exists():
            shutil.rmtree(venv_dir)
        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
        python = venv_dir / "bin" / "python"
        packages: dict[str, Any] = {}
        for project, locked in proposal["python_packages"].items():
            artifact = downloads / str(locked["artifact"])
            _download_exact(str(locked["artifact_url"]), artifact, str(locked["sha256"]))
            commands.append(_run([str(python), "-m", "pip", "install", "--no-deps", str(artifact)], timeout=300))
            packages[project] = {"artifact": str(artifact), "sha256": _file_sha256(artifact)}
        overlay = proposal["pybind11_overlay"]
        overlay_archive = downloads / "pybind11-v3.1.0.tar.gz"
        _download_exact(str(overlay["archive_url"]), overlay_archive, str(overlay["archive_sha256"]))
        mount = Path(str(overlay["mount"]))
        if mount.exists():
            shutil.rmtree(mount)
        with tarfile.open(overlay_archive, "r:gz") as archive:
            archive.extractall(mount.parent, filter="data")
        extracted = next(mount.parent.glob("pybind11-*"))
        extracted.rename(mount)
        cmake = proposal["cmake"]
        cmake_archive = downloads / str(cmake["artifact"])
        _download_exact(str(cmake["artifact_url"]), cmake_archive, str(cmake["artifact_sha256"]))
        tools_dir = root / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(cmake_archive, "r:gz") as archive:
            archive.extractall(tools_dir, filter="data")
        cmake_path = Path(str(cmake["executable"]))
        if not cmake_path.is_file() or _file_sha256(cmake_path) != cmake["executable_sha256"]:
            raise QualificationError("cmake", "approved CMake executable is absent or has a mismatched SHA-256")
        receipt["packages"] = packages
        receipt["cmake"] = {"path": str(cmake_path), "executable_sha256": _file_sha256(cmake_path), "version": _run([str(cmake_path), "--version"])["stdout"]}
        build_dir, prefix = Path(str(proposal["driver"]["build_directory"])), Path(str(proposal["driver"]["install_prefix"]))
        build_env = {"PATH": f"{venv_dir / 'bin'}:{os.environ.get('PATH', '')}", "HOME": str(root), "PYTHONNOUSERSITE": "1", "OMP_NUM_THREADS": "1"}
        commands.append(_run([str(cmake_path), "-S", str(source_dir), "-B", str(build_dir), f"-DCMAKE_INSTALL_PREFIX={prefix}", "-DCMAKE_BUILD_TYPE=Release"], env=build_env, timeout=600))
        commands.append(_run([str(cmake_path), "--build", str(build_dir), "--parallel", "1"], env=build_env, timeout=900))
        commands.append(_run([str(cmake_path), "--install", str(build_dir)], env=build_env, timeout=180))
        probe = "import sys; sys.path.insert(0, sys.argv[1]); import QEC; assert hasattr(QEC, 'Simulation_Env'); print(QEC.__file__)"
        commands.append(_run([str(python), "-c", probe, str(prefix)], env=build_env, timeout=60))
        receipt["source_digests_after"] = _algorithm_digests(source_dir, spec)
        receipt["primary_environment_sha256_after"] = _file_sha256(primary)
        if receipt["primary_environment_sha256_before"] != receipt["primary_environment_sha256_after"]:
            raise QualificationError("isolation", "primary environment freeze changed during isolated native build")
        receipt["terminal"] = "build_success"
    except Exception as error:
        receipt["terminal"] = f"native_unavailable_build_{getattr(error, 'stage', 'unexpected')}"
        receipt["error"] = str(error)
        _write_receipt(receipt_path, receipt)
        raise QualificationError("build", str(error)) from error
    receipt["completed_at"] = time.time()
    _write_receipt(receipt_path, receipt)
    return receipt


def verify_receipt(spec_path: Path, receipt_path: Path, required_terminal: str) -> dict[str, Any]:
    spec = _load_spec(spec_path)
    verify_source_spec(spec)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    if payload.get("source_spec_sha256") != _file_sha256(spec_path):
        raise ValueError("receipt does not bind the exact source specification")
    if payload.get("terminal") != required_terminal:
        raise ValueError(f"receipt terminal must be {required_terminal}")
    if required_terminal == "build_success":
        source = _require_source(spec)
        if payload.get("source_digests_before") != source["source_digests"] or payload.get("source_digests_after") != source["source_digests"]:
            raise ValueError("build receipt algorithm guard is incomplete or mismatched")
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    commands = parser.add_subparsers(dest="command", required=True)
    def command(name: str) -> argparse.ArgumentParser:
        child = commands.add_parser(name)
        child.add_argument("--spec", type=Path, dest="spec", default=argparse.SUPPRESS)
        return child
    command("audit-source")
    command("verify-proposal")
    command("propose-lock")
    build = command("build")
    build.add_argument("--approval-summary", type=Path, required=True)
    build.add_argument("--receipt", type=Path, required=True)
    verify = command("verify-receipt")
    verify.add_argument("--receipt", type=Path, required=True)
    verify.add_argument("--require-terminal", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    spec = _load_spec(args.spec)
    if args.command == "audit-source":
        print(json.dumps(audit_source(spec), sort_keys=True))
        return 0
    if args.command == "verify-proposal":
        verify_source_spec(spec)
        print(json.dumps({"status": "verified", "mode": "read_only"}, sort_keys=True))
        return 0
    if args.command == "propose-lock":
        verify_source_spec(spec)
        print(json.dumps(spec["build_proposal"], sort_keys=True))
        return 0
    if args.command == "build":
        print(json.dumps(_build(args.spec, args.approval_summary, args.receipt), sort_keys=True))
        return 0
    if args.command == "verify-receipt":
        print(json.dumps(verify_receipt(args.spec, args.receipt, args.require_terminal), sort_keys=True))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, PermissionError, QualificationError, subprocess.SubprocessError) as error:
        print(f"qualification failed: {error}", file=sys.stderr)
        raise SystemExit(2)
