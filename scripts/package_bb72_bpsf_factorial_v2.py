#!/usr/bin/env python3
"""Package verified BB72 BP-SF v2 ledgers for GitHub without raw copies."""

from __future__ import annotations

import gzip
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "data/studies/bb72-bpsf-factorial-v2.json"
EVIDENCE = ROOT / "data/results/bb72-bpsf-factorial-v2"


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _hash(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _write_once(path: Path, payload: bytes) -> None:
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"publication artifact differs: {path}")
        return
    path.write_bytes(payload)


def package() -> dict:
    result = _read(EVIDENCE / "result.json")
    if result["design_sha256"] != _hash(DESIGN.read_bytes()) or result["source_reproduction_assessment"] != "not_applicable":
        raise ValueError("study report is not bound to the frozen controlled design")
    if not (EVIDENCE / "REPORT.md").is_file() or not (EVIDENCE / "study.html").is_file():
        raise ValueError("report and offline view are required")
    ledgers = result["evaluation_ledger_sha256"]
    if len(ledgers) != 24:
        raise ValueError("factorial result must bind all 24 arms")
    packaged: dict[str, dict[str, str | int]] = {}
    for relative, expected in sorted(ledgers.items()):
        arm = EVIDENCE / relative
        if not arm.resolve().is_relative_to(EVIDENCE.resolve()):
            raise ValueError("arm path escapes study directory")
        manifest = _read(arm / "manifest.json")
        arm_result = _read(arm / "result.json")
        raw = (arm / "events.jsonl").read_bytes()
        if (_hash(raw) != expected or arm_result["ledger_sha256"] != expected
                or arm_result["run_id"] != manifest["run_id"]
                or arm_result["final_row_count"] != manifest["budgets"]["max_shots"]):
            raise ValueError(f"unverified arm package input: {relative}")
        compressed = gzip.compress(raw, compresslevel=9, mtime=0)
        if gzip.decompress(compressed) != raw:
            raise ValueError(f"compressed ledger does not roundtrip: {relative}")
        _write_once(arm / "events.jsonl.gz", compressed)
        packaged[relative] = {
            "raw_sha256": expected, "compressed_sha256": _hash(compressed),
            "manifest_sha256": _hash((arm / "manifest.json").read_bytes()),
            "arm_result_sha256": _hash((arm / "result.json").read_bytes()),
            "raw_bytes": len(raw), "compressed_bytes": len(compressed),
        }
    publication = {
        "schema_version": 1, "study_id": result["study_id"], "design_sha256": result["design_sha256"],
        "result_sha256": _hash((EVIDENCE / "result.json").read_bytes()),
        "report_sha256": _hash((EVIDENCE / "REPORT.md").read_bytes()),
        "html_sha256": _hash((EVIDENCE / "study.html").read_bytes()),
        "seal_sha256": _hash((EVIDENCE / "seal.json").read_bytes()),
        "ledgers": packaged,
    }
    _write_once(EVIDENCE / "publication-manifest.json", (json.dumps(publication, indent=2, sort_keys=True) + "\n").encode())
    readme = """# BB72 BP-SF factorial v2 evidence

This independent X-only CSS study compares SPA and min-sum updates, damping off/on, and BP-only 20/40-sweep controls against deterministic BP-SF. It does not reproduce the source's parallel execution or the Bravyi circuit-level BP-OSD experiment.

Open `study.html` for the offline interactive view and `REPORT.md` for the primary statistical assessment. `result.json` contains all 24 arm summaries, secondary descriptive contrasts, typed work, and runtime method/scope. Runtime is observed serial execution and is not a normalized source parallel-latency benchmark.

Each arm has a compressed `events.jsonl.gz` beside its manifest and result. Uncompressed ledgers and Slurm logs remain on the HPC filesystem. Restore a ledger with `gzip -dc events.jsonl.gz > events.jsonl` and compare its SHA-256 with `raw_sha256` in `publication-manifest.json`.
"""
    _write_once(EVIDENCE / "README.md", readme.encode())
    return publication


if __name__ == "__main__":
    result = package()
    print(json.dumps({"status": "packaged", "ledgers": len(result["ledgers"]),
                      "bytes": sum(row["compressed_bytes"] for row in result["ledgers"].values())}))
