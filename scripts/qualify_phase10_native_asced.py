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
    if spec.get("build_proposal") is not None:
        raise ValueError("Task 1 source audit cannot contain a build proposal")


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
        print(json.dumps({"status": "verified_source_only", "mode": "read_only"}, sort_keys=True))
        return 0
    if args.command == "propose-lock":
        raise ValueError("package/build proposal is not present until the second qualification task")
    if args.command == "build-run":
        raise PermissionError("native build-run is blocked: proposal status is pending_human")
    raise AssertionError("unreachable")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, PermissionError, subprocess.SubprocessError) as error:
        print(f"qualification failed: {error}", file=sys.stderr)
        raise SystemExit(2)
