#!/usr/bin/env python3
"""Read-only qualification tools for the pinned native aSCED reference.

This module intentionally never installs packages, creates an environment,
configures CMake, compiles code, imports the native extension, or runs it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "data" / "native" / "phase10-asced-source-spec.json"
COMMIT_LENGTH = 40


def _load_spec(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("aSCED specification must be a JSON object")
    return data


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _download(url: str) -> bytes:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "bp-registry-source-audit"})
    with urlopen(request, timeout=30) as response:  # nosec B310: URLs are pinned by the checked specification.
        return response.read()


def _require_source(spec: dict[str, object]) -> dict[str, object]:
    source = spec.get("source")
    if not isinstance(source, dict):
        raise ValueError("specification is missing source")
    commit = source.get("commit")
    if not isinstance(commit, str) or len(commit) != COMMIT_LENGTH:
        raise ValueError("source commit must be an exact full 40-character commit")
    if source.get("repository") != "https://github.com/kit-cel/quantum_asced.git":
        raise ValueError("only kit-cel/quantum_asced is an allowed native source")
    digests = source.get("source_digests")
    algorithms = source.get("algorithm_files")
    if not isinstance(digests, dict) or not digests or not isinstance(algorithms, list) or not algorithms:
        raise ValueError("source digests and algorithm-file guard are required")
    if any(not isinstance(path, str) or path not in digests for path in algorithms):
        raise ValueError("every guarded algorithm file must have a source digest")
    return source


def verify_source_spec(spec: dict[str, object]) -> None:
    """Validate local invariants without contacting a network or executable input."""
    if spec.get("schema") != "phase10-asced-source-spec-v1":
        raise ValueError("unsupported aSCED source-spec schema")
    if spec.get("status") != "pending_human":
        raise ValueError("unapproved native proposal must remain pending_human")
    source = _require_source(spec)
    expected = "816772071486615dfc7d71d1e15df597edc58a26"
    if source["commit"] != expected:
        raise ValueError("native source must remain pinned to the audited exact commit")
    discrepancies = spec.get("discrepancies")
    if not isinstance(discrepancies, dict):
        raise ValueError("audited discrepancies are required")
    required = {"pybind11_gitlink", "demo_path", "license", "pauli_translation", "selection", "channel", "instrumentation"}
    if set(discrepancies) != required:
        raise ValueError("every audited discrepancy must remain explicit")
    license_fact = discrepancies["license"]
    if not isinstance(license_fact, dict) or license_fact.get("status") != "unresolved":
        raise ValueError("license must remain an unresolved fact until human review")
    translation = discrepancies["pauli_translation"]
    if not isinstance(translation, dict) or translation.get("native") != ["I", "X", "Z", "Y"]:
        raise ValueError("native Pauli order must remain explicitly translated")
    proposal = spec.get("build_proposal")
    if proposal is not None:
        verify_build_proposal(spec)


def verify_build_proposal(spec: dict[str, object]) -> None:
    """Reject floating or ambient-build inputs without installing anything."""
    proposal = spec.get("build_proposal")
    if not isinstance(proposal, dict) or proposal.get("status") != "pending_human":
        raise ValueError("build proposal must remain pending_human")
    root = proposal.get("disposable_root")
    if not isinstance(root, str) or not root.startswith("/"):
        raise ValueError("build proposal requires an absolute disposable root")
    if proposal.get("primary_environment_access") != "forbidden":
        raise ValueError("build proposal must not reach the primary environment")
    packages = proposal.get("python_packages")
    expected_projects = {"numpy", "galois", "matplotlib", "scikit-build-core", "pybind11"}
    if not isinstance(packages, dict) or set(packages) != expected_projects:
        raise ValueError("proposal requires exactly the five reviewed Python packages")
    for project, lock in packages.items():
        if not isinstance(lock, dict) or lock.get("classification") != "SUS":
            raise ValueError(f"{project} must remain a SUS package input")
        if not isinstance(lock.get("registry_url"), str) or not lock["registry_url"].startswith("https://pypi.org/pypi/"):
            raise ValueError(f"{project} must use an official PyPI registry URL")
        if not isinstance(lock.get("version"), str) or not isinstance(lock.get("artifact"), str):
            raise ValueError(f"{project} must pin a version and artifact")
        digest = lock.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"{project} artifact must have a SHA-256 digest")
    overlay = proposal.get("pybind11_overlay")
    if not isinstance(overlay, dict) or overlay.get("classification") != "human_reviewed_build_input":
        raise ValueError("pybind11 overlay must remain a separately reviewed build input")
    if not isinstance(overlay.get("commit"), str) or len(overlay["commit"]) != COMMIT_LENGTH:
        raise ValueError("pybind11 overlay requires an exact commit")
    if not isinstance(overlay.get("archive_sha256"), str) or len(overlay["archive_sha256"]) != 64:
        raise ValueError("pybind11 overlay archive requires a SHA-256 digest")
    cmake = proposal.get("cmake")
    if not isinstance(cmake, dict) or cmake.get("classification") != "human_reviewed_build_input":
        raise ValueError("CMake must remain a separately reviewed build input")
    required_cmake = {"provider", "release_page", "version", "artifact", "artifact_url", "artifact_sha256", "acquisition_command", "executable", "executable_sha256"}
    if any(not isinstance(cmake.get(key), str) or not cmake[key] for key in required_cmake):
        raise ValueError("CMake provider, artifact, acquisition, and executable identity are required")
    if not cmake["executable"].startswith(root + "/") or cmake.get("ambient_path_fallback") != "forbidden":
        raise ValueError("only the recorded disposable-root CMake executable may be used")
    if len(cmake["artifact_sha256"]) != 64 or len(cmake["executable_sha256"]) != 64:
        raise ValueError("CMake artifact and executable require SHA-256 digests")
    driver = proposal.get("driver")
    if not isinstance(driver, dict) or any(not isinstance(driver.get(key), str) or not driver[key].startswith(root + "/") for key in ("path", "source_checkout", "build_directory", "install_prefix")):
        raise ValueError("driver and build paths must be out-of-tree under the disposable root")
    forbidden = driver.get("forbidden_changes")
    if not isinstance(forbidden, list) or {"algorithm source", "Pauli semantics", "candidate selection", "channel code"} - set(forbidden):
        raise ValueError("driver must forbid native algorithm and semantic changes")
    guard = proposal.get("algorithm_guard")
    if not isinstance(guard, dict) or guard.get("allow_algorithm_modification") is not False:
        raise ValueError("algorithm-file guard must prohibit modification")


def propose_lock(spec: dict[str, object]) -> dict[str, object]:
    """Query official PyPI metadata and return the already-inert frozen proposal.

    The command does not install, download artifacts, or write a lock.  A human
    approval records whether the checked proposal may later be used for bytes.
    """
    verify_source_spec(spec)
    policy = spec.get("package_resolution_policy")
    if not isinstance(policy, dict) or not isinstance(policy.get("projects"), list):
        raise ValueError("package resolution policy is required")
    for project in policy["projects"]:
        if not isinstance(project, str):
            raise ValueError("package project names must be strings")
        _download(f"https://pypi.org/pypi/{project}/json")
    proposal = spec["build_proposal"]
    assert isinstance(proposal, dict)
    return proposal


def audit_source(spec: dict[str, object]) -> dict[str, object]:
    """Resolve the exact remote commit and hash each selected source input."""
    verify_source_spec(spec)
    source = _require_source(spec)
    commit = str(source["commit"])
    remote = str(source["repository"])
    listed = subprocess.run(["git", "ls-remote", remote, commit], check=False, capture_output=True, text=True)
    if listed.returncode != 0 or not any(line.startswith(commit) for line in listed.stdout.splitlines()):
        raise ValueError("remote did not resolve the exact audited commit")
    digests = source["source_digests"]
    assert isinstance(digests, dict)
    observed: dict[str, str] = {}
    for relative, expected in digests.items():
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError("source digest entries must be strings")
        raw_url = f"https://raw.githubusercontent.com/kit-cel/quantum_asced/{commit}/{relative}"
        actual = _sha256(_download(raw_url))
        if actual != expected:
            raise ValueError(f"source digest mismatch for {relative}")
        observed[relative] = actual
    return {"commit": commit, "source_digests": observed, "mode": "read_only"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("audit-source", help="resolve only the exact remote source and its hashes")
    subcommands.add_parser("verify-proposal", help="verify local source/proposal invariants without network or builds")
    subcommands.add_parser("propose-lock", help="reserved for the inert package/build proposal generator")
    subcommands.add_parser("build-run", help="always refuse unapproved native execution")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    spec = _load_spec(args.spec)
    if args.command == "audit-source":
        print(json.dumps(audit_source(spec), sort_keys=True))
        return 0
    if args.command == "verify-proposal":
        verify_source_spec(spec)
        print(json.dumps({"status": "verified_pending_human", "mode": "read_only"}, sort_keys=True))
        return 0
    if args.command == "propose-lock":
        print(json.dumps(propose_lock(spec), sort_keys=True))
        return 0
    if args.command == "build-run":
        verify_source_spec(spec)
        raise PermissionError("native build-run is blocked: proposal status is pending_human")
    raise AssertionError("unreachable")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, PermissionError, subprocess.SubprocessError) as error:
        print(f"qualification failed: {error}", file=sys.stderr)
        raise SystemExit(2)
