#!/usr/bin/env python3
"""Package and verify terminal fair BeamSearch/RelayBP CSS evidence."""

from __future__ import annotations

import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_fair_beam_relay_campaign import _checked, _digest, _read, _shard_path, _write_once  # noqa: E402

DESIGN = ROOT / "data/studies/fair-beam-relay-css-v2.json"
OUTPUT = ROOT / "data/results/fair-beam-relay-css-v2"


def _package(design_path: Path = DESIGN, output: Path = OUTPUT) -> dict:
    design = _checked(design_path, output)
    result = _read(output / "result.json")
    if (result.get("assessment_status") != "controlled_evaluation_complete"
            or result.get("source_status") != "controlled_css_adaptation"
            or result.get("design_sha256") != _digest(output / "design.json")
            or result.get("seal_sha256") != _digest(output / "seal.json")
            or result.get("selection_lock_sha256") != _digest(output / "selection-lock.json")):
        raise ValueError("campaign report is absent or differs from frozen evidence")
    files = {}
    for name in ("design.json", "seal.json", "selection-lock.json", "result.json", "REPORT.md", "study.html"):
        path = output / name
        files[name] = {"sha256": _digest(path), "bytes": path.stat().st_size}
    for cohort in design["cohorts"]:
        for rate in design["rates"]:
            for profile in design["profiles"]:
                root = _shard_path(output, cohort, rate, profile)
                arm = _read(root / "result.json")
                ledger = root / "events.jsonl"
                if (arm.get("shots") != design["rates"][rate][f"{cohort}_shots"]
                        or arm.get("ledger_sha256") != _digest(ledger)
                        or arm.get("manifest_sha256") != _digest(root / "manifest.json")):
                    raise ValueError(f"shard is incomplete or differs: {cohort}/{rate}/{profile}")
                if cohort == "evaluation":
                    if result["evaluation_ledger_sha256"][rate][profile] != arm["ledger_sha256"]:
                        raise ValueError("evaluation ledger differs from verified report")
                else:
                    lock = _read(output / "selection-lock.json")
                    if lock["selection_ledger_sha256"][rate][profile] != arm["ledger_sha256"]:
                        raise ValueError("selection ledger differs from frozen lock")
                compressed = root / "events.jsonl.gz"
                if not compressed.exists():
                    with compressed.open("wb") as sink:
                        with gzip.GzipFile(filename="", mode="wb", fileobj=sink, mtime=0, compresslevel=6) as gz:
                            with ledger.open("rb") as source:
                                while block := source.read(1024 * 1024):
                                    gz.write(block)
                with gzip.open(compressed, "rb") as source:
                    if sha256(source.read()).hexdigest() != arm["ledger_sha256"]:
                        raise ValueError("compressed ledger does not decompress to verified evidence")
                prefix = f"{cohort}/{rate}/{profile}"
                for name in ("manifest.json", "result.json", "events.jsonl.gz"):
                    path = root / name
                    files[f"{prefix}/{name}"] = {"sha256": _digest(path), "bytes": path.stat().st_size}
    manifest = {
        "schema_version": 1,
        "study_id": design["study_id"],
        "assessment_status": "controlled_evaluation_complete",
        "source_status": "controlled_css_adaptation",
        "publisher_source_sha256": _digest(ROOT / "scripts/package_fair_beam_relay_campaign_v2.py"),
        "files": files,
    }
    _write_once(output / "publication-manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n")
    return manifest


def _verify_package(output: Path = OUTPUT) -> dict:
    manifest = _read(output / "publication-manifest.json")
    if (manifest.get("schema_version") != 1 or manifest.get("study_id") != "fair-beam-relay-css-v2"
            or manifest.get("publisher_source_sha256") != _digest(ROOT / "scripts/package_fair_beam_relay_campaign_v2.py")
            or len(manifest.get("files", {})) != 42):
        raise ValueError("publication manifest is malformed")
    for name, identity in manifest["files"].items():
        path = output / name
        if not path.resolve().is_relative_to(output.resolve()) or not path.is_file():
            raise ValueError(f"published path is missing or outside package: {name}")
        if _digest(path) != identity["sha256"] or path.stat().st_size != identity["bytes"]:
            raise ValueError(f"published file differs: {name}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("package", "verify-package"))
    args = parser.parse_args()
    print(json.dumps(_package() if args.command == "package" else _verify_package(), sort_keys=True))
