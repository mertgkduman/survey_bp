#!/usr/bin/env python3
"""Publish only the verified, compressed BB72 study package to origin/main."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/results/bb72-css-bp-v1"
REMOTE = "origin"
BRANCH = "main"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def publish() -> str:
    package = _read(EVIDENCE / "publication-manifest.json")
    result = _read(EVIDENCE / "result.json")
    if (package["design_sha256"] != result["design_sha256"]
            or package["result_sha256"] != _digest(EVIDENCE / "result.json")
            or package["report_sha256"] != _digest(EVIDENCE / "REPORT.md")
            or package["html_sha256"] != _digest(EVIDENCE / "study.html")
            or result["selection_lock_sha256"] != _digest(EVIDENCE / "selection-lock.json")):
        raise ValueError("publication package differs from the verified study result")
    expected = [EVIDENCE / name for name in (
        "README.md", "REPORT.md", "study.html", "result.json", "selection-lock.json", "seal.json", "publication-manifest.json",
    )]
    for relative, hashes in package["ledgers"].items():
        root = EVIDENCE / relative
        if not root.resolve().is_relative_to(EVIDENCE.resolve()):
            raise ValueError(f"arm path escapes study directory: {relative}")
        compressed = root / "events.jsonl.gz"
        if _digest(compressed) != hashes["compressed_sha256"]:
            raise ValueError(f"compressed ledger differs from verified package: {relative}")
        if (_digest(root / "manifest.json") != hashes["manifest_sha256"]
                or _digest(root / "result.json") != hashes["arm_result_sha256"]):
            raise ValueError(f"arm metadata differs from verified package: {relative}")
        expected.extend((root / "manifest.json", root / "result.json", compressed))
    if len(expected) != len({path.resolve() for path in expected}) or any(not path.is_file() for path in expected):
        raise ValueError("publication file set is incomplete or duplicated")
    if _git("diff", "--cached", "--name-only"):
        raise ValueError("unrelated files are already staged; refusing automated publication")
    head = _git("rev-parse", "HEAD")
    remote = _git("ls-remote", REMOTE, f"refs/heads/{BRANCH}").split()[0]
    if head != remote:
        raise ValueError("origin/main advanced or local HEAD changed; refusing automated publication")
    relative_paths = [str(path.relative_to(ROOT)) for path in expected]
    subprocess.run(["git", "add", "-f", "--", *relative_paths], cwd=ROOT, check=True)
    staged = set(_git("diff", "--cached", "--name-only").splitlines())
    if staged != set(relative_paths):
        raise ValueError("staged publication paths differ from the verified file set")
    subprocess.run(["git", "diff", "--cached", "--check"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "Publish verified BB72 CSS BP study v1"], cwd=ROOT, check=True)
    subprocess.run(["git", "push", REMOTE, f"HEAD:{BRANCH}"], cwd=ROOT, check=True)
    return _git("rev-parse", "HEAD")


if __name__ == "__main__":
    print(json.dumps({"status": "published", "commit": publish()}))
