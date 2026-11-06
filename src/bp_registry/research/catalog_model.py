"""Shared catalog relationships and additive, data-only catalog extensions."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
from typing import Any


ENTITY_IDS = {"papers": "paper_id", "decoders": "decoder_id", "codes": "code_id",
              "circuits": "circuit_id", "channels": "channel_id", "experiments": "experiment_id", "datasets": "dataset_id"}


def validate_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    """Reject unresolved/ambiguous relationships before publishing the static file."""
    indexes = {}
    for kind, field in ENTITY_IDS.items():
        records = catalog.get(kind, [])
        if not isinstance(records, list):
            raise ValueError(f"catalog.{kind} must be an array")
        index = {}
        for record in records:
            identifier = record.get(field)
            if not isinstance(identifier, str) or not identifier or identifier in index:
                raise ValueError(f"catalog.{kind} has a missing or duplicate {field}: {identifier}")
            index[identifier] = record
        indexes[kind] = index
    for dataset in catalog["datasets"]:
        for paper in dataset.get("paper_ids", [dataset.get("paper_id")]):
            if paper not in indexes["papers"]:
                raise ValueError(f"dataset {dataset['dataset_id']} has an unresolved paper {paper}")
    for experiment in catalog["experiments"]:
        for paper in experiment.get("paper_ids", []):
            if paper not in indexes["papers"]:
                raise ValueError(f"experiment has an unresolved paper {paper}")
        for dataset in experiment.get("dataset_ids", [experiment.get("dataset_id")]):
            if dataset is not None and dataset not in indexes["datasets"]:
                raise ValueError(f"experiment has an unresolved dataset {dataset}")
    series_ids = set()
    explicit_series_ids = set()
    for series in catalog.get("result_series", []):
        key = (series["dataset_id"], series["code_id"], series["decoder_id"])
        if key in series_ids:
            raise ValueError(f"duplicate result series {key}; group its points or assign a distinct experiment/decoder")
        series_ids.add(key)
        for kind, value in zip(("datasets", "codes", "decoders"), key, strict=True):
            # The shared Code/circuit selector deliberately uses the same
            # result-series slot. A circuit performance record therefore
            # resolves its middle identity through ``circuits`` rather than
            # manufacturing a fictitious CSS code record.
            if kind == "codes" and value in indexes["circuits"]:
                continue
            if value not in indexes[kind]:
                raise ValueError(f"result series has an unresolved {kind} relationship: {value}")
        for point in series["points"]:
            for field in ("x", "y", "n", "failures", "ci_low", "ci_high", "mean_work", "mean_seconds"):
                value = point.get(field)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                    raise ValueError(f"nonfinite/nonnumeric result value {field} in {key}")
            n, failures = point.get("n"), point.get("failures")
            if n is not None and (n < 0 or int(n) != n):
                raise ValueError(f"invalid sample count in {key}")
            if failures is not None and (failures < 0 or int(failures) != failures or n is not None and failures > n):
                raise ValueError(f"invalid failure count in {key}")
            if point.get("y") is not None and not 0 <= point["y"] <= 1:
                raise ValueError(f"failure probability outside [0,1] in {key}")
        series.setdefault("series_id", ":".join(key))
        if not isinstance(series["series_id"], str) or not series["series_id"] or series["series_id"] in explicit_series_ids:
            raise ValueError("missing or duplicate series_id")
        explicit_series_ids.add(series["series_id"])
    return catalog


def extend_catalog(catalog: dict[str, Any], registry: dict[str, Any], repository: Path) -> dict[str, Any]:
    """Merge normalized evidence files without an interface or Python adapter edit.

    Existing legacy studies retain their format-specific adapters. A new study
    can emit this normalized format directly and register its file in the source
    index's ``normalized_catalogs`` array.
    """
    root = repository.resolve()
    result = deepcopy(catalog)
    result.setdefault("extension_sources", [])
    tracked = None

    def asset(value: dict[str, Any]) -> dict[str, Any]:
        nonlocal tracked
        if tracked is None:
            tracked = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0"))
        if "storage_path" in value:
            storage = value["storage_path"]
            digest = value.get("sha256")
            if not isinstance(storage, str) or not storage or not isinstance(value.get("storage_instructions"), str):
                raise ValueError("external assets need storage_path and storage_instructions")
            if digest is not None and (not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
                raise ValueError("external asset sha256 must be lowercase hexadecimal")
            # A storage declaration does not establish a public download or verify
            # a potentially large external object during a static catalog build.
            return {**value, "url": None, "availability": "external_unverified",
                    "local_storage_path": storage, "checksum_status": "declared_unverified" if digest else "not_supplied"}
        relative = value.get("path")
        if not isinstance(relative, str):
            raise ValueError("extension assets need a repository-relative path")
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("extension asset escapes repository")
        available = relative in tracked and path.is_file()
        return {**value, "url": relative if available else None,
                "availability": "tracked" if available else "local_only" if path.is_file() else "unavailable",
                "local_storage_path": None if available else str(path) if path.exists() else None,
                "sha256": sha256(path.read_bytes()).hexdigest() if path.is_file() else None}

    for relative in registry.get("normalized_catalogs", []):
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"normalized catalog is unavailable within repository: {relative}")
        extension = json.loads(path.read_text())
        if extension.get("schema") != "research-catalog-extension-v1":
            raise ValueError("unsupported normalized catalog extension schema")
        for kind in (*ENTITY_IDS, "result_series"):
            records = extension.get(kind, [])
            if not isinstance(records, list):
                raise ValueError(f"extension.{kind} must be an array")
            for record in records:
                item = deepcopy(record)
                if "asset" in item:
                    item["asset"] = asset(item["asset"])
                if "assets" in item:
                    item["assets"] = [asset(a) for a in item["assets"]]
                result.setdefault(kind, []).append(item)
        result["extension_sources"].append({"path": relative, "sha256": sha256(path.read_bytes()).hexdigest()})
    return validate_catalog(result)
