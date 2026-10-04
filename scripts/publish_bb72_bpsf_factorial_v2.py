#!/usr/bin/env python3
"""Push only the verified BB72 BP-SF v2 package to origin/main."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/results/bb72-bpsf-factorial-v2"
DESIGN = ROOT / "data/studies/bb72-bpsf-factorial-v2.json"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def publish() -> str:
    package = _read(EVIDENCE / "publication-manifest.json")
    report = _read(EVIDENCE / "result.json")
    if (package["design_sha256"] != report["design_sha256"]
            or package["design_sha256"] != _digest(DESIGN)
            or package["result_sha256"] != _digest(EVIDENCE / "result.json")
            or package["report_sha256"] != _digest(EVIDENCE / "REPORT.md")
            or package["html_sha256"] != _digest(EVIDENCE / "study.html")
            or package["seal_sha256"] != _digest(EVIDENCE / "seal.json")):
        raise ValueError("publication package differs from the verified study result")
    expected = [EVIDENCE / name for name in (
        "README.md", "REPORT.md", "study.html", "result.json", "seal.json", "publication-manifest.json",
    )]
    if len(package["ledgers"]) != 24:
        raise ValueError("publication package does not contain all 24 arms")
    for relative, hashes in package["ledgers"].items():
        root = EVIDENCE / relative
        if not root.resolve().is_relative_to(EVIDENCE.resolve()):
            raise ValueError(f"arm path escapes study directory: {relative}")
        compressed = root / "events.jsonl.gz"
        if (_digest(compressed) != hashes["compressed_sha256"]
                or _digest(root / "manifest.json") != hashes["manifest_sha256"]
                or _digest(root / "result.json") != hashes["arm_result_sha256"]):
            raise ValueError(f"arm differs from verified package: {relative}")
        expected.extend((root / "manifest.json", root / "result.json", compressed))
    if len(expected) != len({path.resolve() for path in expected}) or any(not path.is_file() for path in expected):
        raise ValueError("publication file set is incomplete or duplicated")
    if _git("diff", "--cached", "--name-only"):
        raise ValueError("unrelated files are already staged")
    head = _git("rev-parse", "HEAD")
    remote = _git("ls-remote", "origin", "refs/heads/main").split()[0]
    if head != remote:
        raise ValueError("origin/main advanced or local HEAD changed")
    paths = [str(path.relative_to(ROOT)) for path in expected]
    subprocess.run(["git", "add", "-f", "--", *paths], cwd=ROOT, check=True)
    if set(_git("diff", "--cached", "--name-only").splitlines()) != set(paths):
        raise ValueError("staged paths differ from verified package")
    subprocess.run(["git", "diff", "--cached", "--check", "--", ".",
                    ":(exclude)data/results/bb72-bpsf-factorial-v2/study.html"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "Publish verified BB72 BP-SF factorial v2"], cwd=ROOT, check=True)
    subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, check=True)
    return _git("rev-parse", "HEAD")


if __name__ == "__main__":
    print(json.dumps({"status": "published", "commit": publish()}))
