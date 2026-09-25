#!/usr/bin/env python3
"""Measure frozen CSS identities before Phase 4 admits a pilot artifact.

This command deliberately reconstructs B1 from the pinned Panteleev--Kalachev
construction rather than selecting a digest from any existing record.  It
reports the exact stale-record disposition and separately performs read-only
identity checks for the BB-144 and generated HGP support artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np

from bp_registry.artifacts import load_artifact
from bp_registry.code_constructions import (
    build_b1_ghp,
    load_frozen_css_npz,
    write_css_npz,
)
from bp_registry.css import CssCode, semantic_sha256
from bp_registry.manifests import matrix_hashes


_B1_SOURCE = {
    "paper": "Panteleev and Kalachev, arXiv:1904.02703v3",
    "revision": "v3",
    "archive_sha256": "5aa90578b1a93e18dedf505784d3b2836b2fd5a9bbe91bff2617e5fc6603975e",
    "archive_member": "matrices/ghpc_3_3_N882_K24.tex",
    "archive_member_sha256": "91be6649c066b88d46e1b232ac16c3e7cb94f8a928fd9f82834663b16e9d8e83",
    "ring": "GF(2)[x]/(x^63-1)",
    "circulant_convention": "row-major: polynomial x^e has one at column e in row 0",
    "hx": "[A, B]",
    "hz": "[B^T, A^T]",
    "a_rows": [[27, None, None, None, None, 0, 54], [54, 27, None, None, None, None, 0],
               [0, 54, 27, None, None, None, None], [None, 0, 54, 27, None, None, None],
               [None, None, 0, 54, 27, None, None], [None, None, None, 0, 54, 27, None],
               [None, None, None, None, 0, 54, 27]],
    "b_diagonal_exponents": [0, 1, 6],
}


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identity(code: CssCode, raw_sha256: str) -> dict[str, Any]:
    return {
        "raw_sha256": raw_sha256,
        "semantic_sha256": semantic_sha256(code),
        "matrix_hashes": matrix_hashes(code),
    }


def _same_arrays(left: CssCode, right: CssCode) -> bool:
    return all(
        np.array_equal(getattr(left, name), getattr(right, name))
        for name in ("hx", "hz", "lx", "lz")
    )


def _matches(identity: dict[str, Any], expected: dict[str, Any]) -> bool:
    return all(identity.get(key) == expected.get(key) for key in ("raw_sha256", "semantic_sha256", "matrix_hashes"))


def _basic_identity_matches(identity: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Compare the digest pair used by historical sidecars without matrix hashes."""
    return all(identity.get(key) == expected.get(key) for key in ("raw_sha256", "semantic_sha256"))


def _b1_report(root: Path, inventory: dict[str, Any]) -> dict[str, Any]:
    artifacts = root / "data" / "artifacts"
    manifests = root / "data" / "manifests"
    frozen_path = artifacts / "b1-panteleev-kalachev-v3.npz"
    metadata = _json(artifacts / "b1-panteleev-kalachev-v3.json")
    phase3 = _json(manifests / "phase3-pilot-b1.json")
    inventory_entry = next(item for item in inventory["candidates"] if item["code_id"] == "b1-ghp-882")

    reconstructed = build_b1_ghp()
    frozen = load_frozen_css_npz(artifacts, frozen_path.name)
    with TemporaryDirectory(prefix="phase4-b1-qualification-") as temporary:
        regenerated_path = Path(temporary) / frozen_path.name
        write_css_npz(reconstructed, regenerated_path)
        regenerated_raw = _sha256(regenerated_path)
        regenerated_bytes_match = regenerated_path.read_bytes() == frozen_path.read_bytes()

    measured = _identity(reconstructed, regenerated_raw)
    frozen_identity = _identity(frozen, _sha256(frozen_path))
    metadata_identity = metadata["artifact"]
    manifest_identity = phase3["artifact"]
    inventory_identity = inventory_entry["matrix_identity"]
    source_matches = (
        metadata["source"]["revision"] == _B1_SOURCE["revision"]
        and metadata["source"]["archive_sha256"] == _B1_SOURCE["archive_sha256"]
        and metadata["source"]["archive_member"] == _B1_SOURCE["archive_member"]
        and metadata["source"]["archive_member_sha256"] == _B1_SOURCE["archive_member_sha256"]
        and metadata["source"]["equations"]["hx"] == _B1_SOURCE["hx"]
        and metadata["source"]["equations"]["hz"] == _B1_SOURCE["hz"]
        and metadata["source"]["equations"]["a_rows"] == _B1_SOURCE["a_rows"]
        and metadata["source"]["equations"]["b_diagonal_exponents"] == _B1_SOURCE["b_diagonal_exponents"]
    )
    artifact_matches = _same_arrays(reconstructed, frozen) and measured == frozen_identity and regenerated_bytes_match
    metadata_matches = all(metadata_identity[key] == measured[key] for key in ("raw_sha256", "semantic_sha256"))
    manifest_matches = _matches(measured, manifest_identity)
    inventory_matches = (
        inventory_identity["artifact_raw_sha256"] == measured["raw_sha256"]
        and inventory_identity["artifact_semantic_sha256"] == measured["semantic_sha256"]
    )

    stale = []
    if not artifact_matches or not metadata_matches or not source_matches:
        stale.append("artifact_or_metadata_stale")
    if not manifest_matches:
        stale.append("phase3_manifest_stale")
    if not inventory_matches:
        stale.append("inventory_stale")
    previous_inventory: dict[str, Any] | None = None
    if stale:
        disposition = stale[0] if len(stale) == 1 else "multiple_records_stale"
    else:
        resolution_link = inventory_entry.get("identity_resolution", {})
        resolution_path = root / str(resolution_link.get("resolution_record", ""))
        if resolution_link.get("disposition") == "inventory_stale" and resolution_path.is_file():
            previous = _json(resolution_path).get("b1", {})
            prior_records = previous.get("records", {})
            previous_inventory = prior_records.get("inventory_before_repair") or prior_records.get("inventory")
            if (
                previous.get("disposition") == "inventory_stale"
                and previous.get("reconstructed") == measured
                and isinstance(previous_inventory, dict)
                and previous_inventory.get("semantic_sha256") != measured["semantic_sha256"]
            ):
                disposition = "inventory_stale"
            else:
                disposition = "unresolved"
        else:
            disposition = "unresolved"
    if disposition == "unresolved":
        raise ValueError("B1 qualification could not classify a stale record from measured evidence")

    return {
        "disposition": disposition,
        "source": _B1_SOURCE,
        "construction": {
            "serialization": "css-npz-v1 fixed ZIP metadata and DEFLATE level 9",
            "logical_basis": "deterministic GF(2) free-column quotient basis with paired Lz normalization",
        },
        "reconstructed": measured,
        "records": {
            "artifact_v3": frozen_identity,
            "metadata_v3": {"raw_sha256": metadata_identity["raw_sha256"], "semantic_sha256": metadata_identity["semantic_sha256"]},
            "phase3_manifest": manifest_identity,
            "inventory": {"raw_sha256": inventory_identity["artifact_raw_sha256"], "semantic_sha256": inventory_identity["artifact_semantic_sha256"]},
            "inventory_before_repair": previous_inventory,
        },
        "checks": {
            "source_construction_matches_pin": source_matches,
            "regenerated_npz_matches_frozen_v3_bytes": regenerated_bytes_match,
            "artifact_arrays_match_reconstruction": _same_arrays(reconstructed, frozen),
            "artifact_identity_matches_reconstruction": artifact_matches,
            "metadata_matches_reconstruction": metadata_matches,
            "phase3_manifest_matches_reconstruction": manifest_matches,
            "inventory_matches_reconstruction": inventory_matches,
        },
        "matrix_logical_identity_match": measured["matrix_hashes"] == frozen_identity["matrix_hashes"] == manifest_identity["matrix_hashes"],
    }


def _support_report(root: Path, inventory: dict[str, Any], *, code_id: str, artifact_name: str, metadata_name: str, manifest_name: str, author_instance: bool) -> dict[str, Any]:
    artifacts = root / "data" / "artifacts"
    entry = next(item for item in inventory["candidates"] if item["code_id"] == code_id)
    metadata = _json(artifacts / metadata_name)
    manifest = _json(root / "data" / "manifests" / manifest_name)
    artifact_path = artifacts / artifact_name
    if artifact_path.suffix == ".npz":
        code = load_frozen_css_npz(artifacts, artifact_name)
    else:
        code = load_artifact(artifacts, artifact_name).code
    identity = _identity(code, _sha256(artifact_path))
    metadata_identity = metadata["artifact"]
    manifest_identity = manifest["artifact"]
    inventory_identity = entry["matrix_identity"]
    metadata_matches = _basic_identity_matches(identity, metadata_identity)
    manifest_matches = _matches(identity, manifest_identity)
    inventory_matches = (
        identity["raw_sha256"] == inventory_identity["artifact_raw_sha256"]
        and identity["semantic_sha256"] == inventory_identity["artifact_semantic_sha256"]
    )
    matches = (
        metadata_matches
        and manifest_matches
        and inventory_matches
    )
    return {
        "artifact": identity,
        "metadata_path": str(Path("data/artifacts") / metadata_name),
        "manifest_path": str(Path("data/manifests") / manifest_name),
        "checks": {
            "metadata_matches": metadata_matches,
            "manifest_matches": manifest_matches,
            "inventory_matches": inventory_matches,
        },
        "all_identities_match": matches,
        "author_instance": author_instance,
    }


def qualify_phase4_artifacts(repository_root: Path, *, output_path: Path) -> dict[str, Any]:
    """Return and persist a measured, source-backed qualification report."""
    root = repository_root.resolve()
    inventory = _json(root / "data" / "evidence" / "code-inventory.json")
    report = {
        "schema_version": 1,
        "purpose": "Phase 4 exact CSS artifact qualification before dependent pilot design",
        "b1": _b1_report(root, inventory),
        "supporting_qualifications": {
            "gross-bb-144": _support_report(root, inventory, code_id="gross-bb-144", artifact_name="selected-css.json", metadata_name="selected-css.provenance.json", manifest_name="phase3-pilot-bb144.json", author_instance=True),
            "hgp-gallager-3-4-seed-20260923": _support_report(root, inventory, code_id="hgp-gallager-3-4-seed-20260923", artifact_name="hgp-gallager-3-4-seed-20260923.npz", metadata_name="hgp-gallager-3-4-seed-20260923.json", manifest_name="phase3-pilot-hgp-gallager.json", author_instance=False),
        },
    }
    if report["b1"]["disposition"] == "unresolved" or not all(
        item["all_identities_match"] for item in report["supporting_qualifications"].values()
    ):
        raise ValueError("Phase 4 artifact qualification failed closed")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("data/evidence/phase4-b1-identity-resolution.json"))
    args = parser.parse_args()
    root = args.repository_root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    print(json.dumps(qualify_phase4_artifacts(root, output_path=output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
