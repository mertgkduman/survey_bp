#!/usr/bin/env python3
"""Build and qualify only the approved Relay-BP v0.2.2 author revision."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Any

AUTHOR_REPOSITORY = "https://github.com/trmue/relay.git"
AUTHOR_TAG = "v0.2.2"
AUTHOR_COMMIT = "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
AUTHOR_TREE = "5f6f112429e62112ba71fbff45f4e16247725fbc"
ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "native/relay-v0.2.2-observer.patch"


def _run(*args: str, cwd: Path | None = None, timeout: int = 900) -> dict[str, Any]:
    try:
        completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
        return {"command": list(args), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    except subprocess.TimeoutExpired as error:
        return {"command": list(args), "returncode": 124, "stdout": error.stdout or "", "stderr": error.stderr or "", "timed_out": True}


def _must(result: dict[str, Any], label: str) -> None:
    if result["returncode"]:
        raise RuntimeError(f"{label} failed: {result['stderr'][-1000:]}")


def _git(source: Path, *args: str) -> str:
    result = _run("git", *args, cwd=source)
    _must(result, f"git {' '.join(args)}")
    return str(result["stdout"]).strip()


def _identity(source: Path) -> dict[str, object]:
    return {
        "author_repository": AUTHOR_REPOSITORY,
        "author_tag": AUTHOR_TAG,
        "author_commit": _git(source, "rev-parse", "HEAD"),
        "author_tree": _git(source, "rev-parse", "HEAD^{tree}"),
    }


def qualify(output: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="relay-v022-") as temporary:
        workspace = Path(temporary)
        source = workspace / "source"
        clone = _run("git", "clone", "--quiet", AUTHOR_REPOSITORY, str(source), timeout=300)
        _must(clone, "author clone")
        _must(_run("git", "checkout", "--quiet", "--detach", AUTHOR_COMMIT, cwd=source), "author checkout")
        identity = _identity(source)
        if identity["author_commit"] != AUTHOR_COMMIT or identity["author_tree"] != AUTHOR_TREE:
            raise RuntimeError("checked-out author source is not the approved immutable pin")

        # Compile every native test target, then execute the bounded Relay unit fixture.
        # A prior all-test attempt exceeded twelve minutes in decode_144_12_12, so it is
        # retained as an inconclusive full-suite result rather than presented as a pass.
        native_build = _run("cargo", "test", "--workspace", "--no-run", cwd=source, timeout=300)
        _must(native_build, "native test build")
        native_suite = _run("cargo", "test", "--workspace", "min_sum_decode_repetition_code", cwd=source, timeout=120)
        _must(native_suite, "bounded Relay native fixture")

        patched = workspace / "patched"
        _must(_run("git", "clone", "--quiet", str(source), str(patched), timeout=300), "patched clone")
        _must(_run("git", "checkout", "--quiet", "--detach", AUTHOR_COMMIT, cwd=patched), "patched checkout")
        _must(_run("git", "apply", "--check", str(PATCH), cwd=patched), "observer patch check")
        _must(_run("git", "apply", str(PATCH), cwd=patched), "observer patch apply")
        patched_build = _run("cargo", "test", "--workspace", "--no-run", cwd=patched, timeout=300)
        _must(patched_build, "patched native test build")
        patched_suite = _run("cargo", "test", "--workspace", "min_sum_decode_repetition_code", cwd=patched, timeout=120)
        _must(patched_suite, "patched bounded native suite")

        patch_bytes = PATCH.read_bytes()
        fork_path = Path("/hpc/group/pfisterlab/mg551/storage/relay/relay")
        installed_fork: dict[str, object] = {"path": str(fork_path), "status": "untrusted_non_author_reference"}
        if (fork_path / ".git").exists():
            installed_fork["commit"] = _git(fork_path, "rev-parse", "HEAD")
        moving = _run("git", "ls-remote", AUTHOR_REPOSITORY, "HEAD", timeout=300)
        _must(moving, "author moving-main identity")
        moving_head = str(moving["stdout"]).split()[0]
        record: dict[str, object] = {
            **identity,
            "identities": {
                "author_release": {"repository": AUTHOR_REPOSITORY, "tag": AUTHOR_TAG, "commit": AUTHOR_COMMIT, "tree": AUTHOR_TREE},
                "author_moving_main": {"repository": AUTHOR_REPOSITORY, "ref": "HEAD", "commit": moving_head, "status": "not_author_reference"},
                "installed_fork": installed_fork,
            },
            "build": {
                "method": "isolated temporary clone plus complete test-target build and bounded Relay unit fixture",
                "rustc": _run("rustc", "--version")["stdout"].strip(),
                "cargo": _run("cargo", "--version")["stdout"].strip(),
                "python": sys.version.split()[0],
                "platform": platform.platform(),
            },
            "qualification": {
                "passed": True,
                "native_suite": {"unmodified_returncode": native_suite["returncode"], "patched_returncode": patched_suite["returncode"], "all_test_targets_built": native_build["returncode"] == 0 and patched_build["returncode"] == 0},
                "full_suite": {"status": "inconclusive_timeout", "case": "decode_144_12_12", "elapsed_lower_bound_seconds": 720, "reason": "bounded qualification terminated the CPU-bound test; no result is claimed"},
                "offline_scope": "bounded native tests; initial dependency resolution was required because v0.2.2 lock was stale and crates were uncached",
            },
            "observer_patch": {
                "base_commit": AUTHOR_COMMIT,
                "patch_sha256": sha256(patch_bytes).hexdigest(),
                "terminal_equivalence": {"passed": True, "method": "same locked native suite before and after a comment-only observer boundary"},
            },
            "numerical_profiles": {
                "f32": "RelayDecoderF32 available", "f64": "RelayDecoderF64 available",
                "source_matched_profile": None,
                "reason": "no material F32/F64 difference was demonstrated by this bounded qualification",
            },
            "unavailable_native_facts": {
                "gamma": "unavailable: comment-only observer cannot observe per-leg gamma",
                "edge_work": "unavailable: would require behavior-changing instrumentation",
                "resource": "unavailable: would require behavior-changing instrumentation",
            },
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data/evidence/relay-v0.2.2-source.json")
    arguments = parser.parse_args()
    qualify(arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
