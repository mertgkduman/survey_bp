#!/usr/bin/env python3
"""Create deterministic GitHub-sized copies of verified BB72 study ledgers."""

from __future__ import annotations

import gzip
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "data/studies/bb72-css-bp-v1.json"
EVIDENCE = ROOT / "data/results/bb72-css-bp-v1"


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
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
    report = _read(EVIDENCE / "result.json")
    lock = _read(EVIDENCE / "selection-lock.json")
    design_sha = _hash(DESIGN.read_bytes())
    if (report["design_sha256"] != design_sha or lock["design_sha256"] != design_sha
            or report["selection_lock_sha256"] != _hash((EVIDENCE / "selection-lock.json").read_bytes())):
        raise ValueError("study report and selection lock are not bound to the frozen design")
    if not (EVIDENCE / "REPORT.md").is_file() or not (EVIDENCE / "study.html").is_file():
        raise ValueError("verified report and offline study view are required before packaging")
    ledger_map = {
        **{f"selection/{relative}": digest for relative, digest in lock["selection_ledger_sha256"].items()},
        **{f"evaluation/{relative}": digest for relative, digest in report["evaluation_ledger_sha256"].items()},
    }
    if len(ledger_map) != len(lock["selection_ledger_sha256"]) + len(report["evaluation_ledger_sha256"]):
        raise ValueError("duplicate ledger identity between study cohorts")
    packaged: dict[str, dict[str, str | int]] = {}
    for relative, expected in sorted(ledger_map.items()):
        root = EVIDENCE / relative
        manifest = _read(root / "manifest.json")
        result = _read(root / "result.json")
        raw = (root / "events.jsonl").read_bytes()
        if (_hash(raw) != expected or result["ledger_sha256"] != expected
                or result["run_id"] != manifest["run_id"]
                or result["final_row_count"] != manifest["budgets"]["max_shots"]):
            raise ValueError(f"unverified arm package input: {relative}")
        compressed = gzip.compress(raw, compresslevel=9, mtime=0)
        if gzip.decompress(compressed) != raw:
            raise ValueError(f"compressed ledger does not roundtrip: {relative}")
        _write_once(root / "events.jsonl.gz", compressed)
        packaged[relative] = {
            "raw_sha256": expected, "compressed_sha256": _hash(compressed),
            "manifest_sha256": _hash((root / "manifest.json").read_bytes()),
            "arm_result_sha256": _hash((root / "result.json").read_bytes()),
            "raw_bytes": len(raw), "compressed_bytes": len(compressed),
        }
    manifest = {
        "schema_version": 1, "study_id": report["study_id"], "design_sha256": design_sha,
        "result_sha256": _hash((EVIDENCE / "result.json").read_bytes()),
        "report_sha256": _hash((EVIDENCE / "REPORT.md").read_bytes()),
        "html_sha256": _hash((EVIDENCE / "study.html").read_bytes()),
        "ledgers": packaged,
    }
    _write_once(EVIDENCE / "publication-manifest.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
    readme = """# BB72 CSS BP study v1 evidence

This directory contains the frozen, verified controlled CSS study on the source-pinned [[72,12,6]] BB72 code. Open `study.html` for the offline interactive view and `REPORT.md` for the statistical readout. The original paper's circuit-level BP-OSD experiment is not reproduced here. The BP-SF arm uses canonical SPA messages and deterministic test order, unlike the source paper's min-sum and parallel selection.

Each arm's uncompressed ledger remains on the HPC filesystem. GitHub stores a deterministic `events.jsonl.gz` beside the arm's manifest and result. To restore one ledger, run `gzip -dc events.jsonl.gz > events.jsonl`; its SHA-256 must equal that arm's `raw_sha256` in `publication-manifest.json` and `ledger_sha256` in its `result.json`.

`selection-lock.json` binds the independently sampled parameter-selection cohort. `result.json` binds the evaluation arm ledgers and their matched sample identities. Operational Slurm logs are local-only and are not outcome evidence.
"""
    _write_once(EVIDENCE / "README.md", readme.encode())
    return manifest


if __name__ == "__main__":
    result = package()
    print(json.dumps({"status": "packaged", "ledgers": len(result["ledgers"]), "bytes": sum(row["compressed_bytes"] for row in result["ledgers"].values())}))
