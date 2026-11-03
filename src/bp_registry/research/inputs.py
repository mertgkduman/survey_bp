"""Machine-readable shared registry of research code and circuit inputs."""
from __future__ import annotations

import json
from pathlib import Path


def input_registry(repository=None):
    root = Path(repository) if repository is not None else Path(__file__).resolve().parents[3]
    result = json.loads((root / "research/catalog/inputs.json").read_text())
    if result.get("schema") != "research-input-registry-v1":
        raise ValueError("unsupported research input registry")
    for collection, field in (("codes", "code_id"), ("circuits", "circuit_id")):
        identifiers = [row[field] for row in result[collection]]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("duplicate research input identifier")
    return result


def input_catalog(repository, asset):
    registry = input_registry(repository)
    codes = [{**row, "asset": asset(repository, row["artifact_path"],
              label=row["asset_label"], kind=row["asset_kind"])} for row in registry["codes"]]
    circuits = []
    for row in registry["circuits"]:
        manifest = json.loads((repository / row["manifest_path"]).read_text())
        circuits.append({**row, "asset": asset(repository, row["path"], label=row["asset_label"], kind="stim"),
            "source": {key: manifest.get(key) for key in ("upstream_repository", "upstream_commit", "upstream_tag", "license")},
            "source_manifest": asset(repository, row["manifest_path"], label="Pinned circuit source manifest", kind="manifest"),
            "license_assets": [asset(repository, path, label=Path(path).name, kind="license") for path in row["license_paths"]]})
    return codes, circuits
