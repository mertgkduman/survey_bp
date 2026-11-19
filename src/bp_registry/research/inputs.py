"""Machine-readable shared registry of research code and circuit inputs."""
from __future__ import annotations

import json
from pathlib import Path


def input_registry(repository=None):
    root = Path(repository) if repository is not None else Path(__file__).resolve().parents[3]
    result = json.loads((root / "research/catalog/inputs.json").read_text())
    if result.get("schema") != "research-input-registry-v1":
        raise ValueError("unsupported research input registry")
    source_path = "data/reproductions/priortilt-2611-13373/source.json"
    if (root / source_path).is_file():
        source = json.loads((root / source_path).read_text())
        for item in source["circuits"]:
            if item["p"] != 0.001 or item["basis"] not in {"x", "z"}:
                continue
            code, basis = item["code"], item["basis"]
            result["circuits"].append({
                "circuit_id": f"priortilt-{code.lower()}-memory-{basis}",
                "label": f"{code} memory {basis.upper()} · p=0.001",
                "comparison_label": f"{code} X/Z circuit memories",
                "path": item["path"],
                "asset_label": f"{code} memory {basis.upper()} circuit",
                "manifest_path": source_path,
                "license_paths": ["data/reproductions/priortilt-2611-13373/SOURCE-LICENSE"],
                "source_probability": 0.001,
                "source_paper_id": "priortilt-2611-13373-v1",
            })
    for collection, field in (("codes", "code_id"), ("circuits", "circuit_id")):
        identifiers = [row[field] for row in result[collection]]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("duplicate research input identifier")
    return result


def input_catalog(repository, asset):
    registry = input_registry(repository)
    codes = [{**row, "asset": asset(repository, row["artifact_path"],
              label=row["asset_label"], kind=row["asset_kind"])} for row in registry["codes"]]
    for code in codes:
        if code["code_id"].startswith("unicycle"):
            code["label"] = code["label"].replace("MacKay ", "")
            code["source_paper_ids"] = ["mackay-0304161-v3"]
        elif code["code_id"].startswith("toric"):
            code["label"] = code["label"].replace("Roffe ", "")
            code["source_paper_ids"] = ["roffe-2005-07016-v2"]
    circuits = []
    for row in registry["circuits"]:
        manifest = json.loads((repository / row["manifest_path"]).read_text())
        circuits.append({**row, "asset": asset(repository, row["path"], label=row["asset_label"], kind="stim"),
            "source": {key: manifest.get(key) for key in ("upstream_repository", "upstream_commit", "upstream_tag", "license")},
            "source_manifest": asset(repository, row["manifest_path"], label="Pinned circuit source manifest", kind="manifest"),
            "license_assets": [asset(repository, path, label=Path(path).name, kind="license") for path in row["license_paths"]]})
    return codes, circuits
