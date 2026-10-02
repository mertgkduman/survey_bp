#!/usr/bin/env python3
"""Freeze the commented [[72,12,6]] variant in pinned Bravyi source.

The author's executable default is BB144.  This reads the explicitly listed
BB72 parameter block without executing the source's circuit-building script.
Logical operators use this project's deterministic paired GF(2) basis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from bp_registry.code_constructions import derive_css_logicals
from bp_registry.css import CssCode, gf2_rank, semantic_sha256
from tools.freeze_css_source import (
    BRAVYI_REVISION, SOURCE_FILE, SourceGateError, _assert_construction_shape, _git,
)


def source_parameters(source_text: str) -> dict[str, int]:
    """Require the single author-commented BB72 block with its exact values."""
    pattern = (
        r"(?m)^#\s*\[\[72,12,6\]\]\s*$\n"
        r"^#\s*ell\s*,\s*m\s*=\s*(\d+)\s*,\s*(\d+)\s*$\n"
        r"^#\s*a1\s*,\s*a2\s*,\s*a3\s*=\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$\n"
        r"^#\s*b1\s*,\s*b2\s*,\s*b3\s*=\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$"
    )
    matches = list(re.finditer(pattern, source_text))
    if len(matches) != 1:
        raise SourceGateError("pinned source must contain exactly one BB72 parameter block")
    values = tuple(int(value) for value in matches[0].groups())
    if values != (6, 6, 3, 1, 2, 3, 1, 2):
        raise SourceGateError("pinned BB72 parameter block differs from reviewed [[72,12,6]] variant")
    return dict(zip(("ell", "m", "a1", "a2", "a3", "b1", "b2", "b3"), values, strict=True))


def construct(source_dir: Path) -> tuple[CssCode, dict[str, object]]:
    root = source_dir.resolve(strict=True)
    revision = _git(root, "rev-parse", "HEAD")
    if revision != BRAVYI_REVISION or _git(root, "status", "--porcelain"):
        raise SourceGateError("Bravyi source checkout must be clean at the pinned revision")
    source_bytes = (root / SOURCE_FILE).read_bytes()
    source_text = source_bytes.decode("utf-8")
    _assert_construction_shape(source_text)
    p = source_parameters(source_text)
    ell, m = p["ell"], p["m"]
    i_ell, i_m = np.eye(ell, dtype=np.uint8), np.eye(m, dtype=np.uint8)
    x = {i: np.kron(np.roll(i_ell, i, axis=1), i_m) for i in range(ell)}
    y = {i: np.kron(i_ell, np.roll(i_m, i, axis=1)) for i in range(m)}
    a = (x[p["a1"]] + y[p["a2"]] + y[p["a3"]]) % 2
    b = (y[p["b1"]] + x[p["b2"]] + x[p["b3"]]) % 2
    hx = np.hstack((a, b)).astype(np.uint8)
    hz = np.hstack((b.T, a.T)).astype(np.uint8)
    lx, lz = derive_css_logicals(hx, hz)
    code = CssCode(hx, hz, lx, lz).validate()
    if code.n != 72 or code.k != 12 or hx.shape != (36, 72) or hz.shape != (36, 72):
        raise SourceGateError("constructed BB72 has unexpected dimensions")
    if gf2_rank(hx) != 30 or gf2_rank(hz) != 30:
        raise SourceGateError("constructed BB72 has unexpected GF(2) rank")
    source = {
        "repository": "https://github.com/sbravyi/BivariateBicycleCodes",
        "revision": revision,
        "source_file": SOURCE_FILE,
        "source_file_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "parameter_location": "commented [[72,12,6]] block",
        "parameters": p,
        "matrix_ordering": "Hx=[A|B], Hz=[B^T|A^T], columns=left block then right block",
    }
    return code, source


def matrix_hashes(code: CssCode) -> dict[str, str]:
    """Use the public manifest's V1 matrix byte conventions without Pydantic."""
    hashes: dict[str, str] = {}
    for name, role in (("hx", "Hx"), ("hz", "Hz"), ("lx", "Lx"), ("lz", "Lz")):
        matrix = getattr(code, name)
        raw = json.dumps(matrix.tolist(), separators=(",", ":")).encode("utf-8")
        semantic = (b"BPREG-MATRIX-V1\0" + role.encode("ascii") + b"\0"
                    + f"{matrix.shape[0]}x{matrix.shape[1]}\0".encode("ascii")
                    + np.packbits(matrix.reshape(-1), bitorder="little").tobytes())
        hashes[f"{name}_raw_sha256"] = hashlib.sha256(raw).hexdigest()
        hashes[f"{name}_semantic_sha256"] = hashlib.sha256(semantic).hexdigest()
    return hashes


def freeze(source_dir: Path, artifact_output: Path, provenance_output: Path) -> dict[str, object]:
    code, source = construct(source_dir)
    artifact = {
        "format_version": 1,
        "hx": code.hx.tolist(), "hz": code.hz.tolist(),
        "lx": code.lx.tolist(), "lz": code.lz.tolist(),
    }
    artifact_bytes = (json.dumps(artifact, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
    artifact_output.parent.mkdir(parents=True, exist_ok=True)
    provenance_output.parent.mkdir(parents=True, exist_ok=True)
    artifact_output.write_bytes(artifact_bytes)
    provenance: dict[str, object] = {
        "format_version": 1,
        "code_id": "bravyi-bb-72",
        "artifact": {
            "path": str(artifact_output),
            "raw_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
            "semantic_sha256": semantic_sha256(code),
            "matrix_hashes": matrix_hashes(code),
            "shapes": {name: list(getattr(code, name).shape) for name in ("hx", "hz", "lx", "lz")},
        },
        "source": source,
        "logical_provider": {
            "status": "project_derived",
            "method": "deterministic free-column quotient basis and GF(2) pairing normalization",
            "source_logical_equivalence": "not_assessed",
        },
        "independent_validation": {
            "commutator_nonzero_entries": int(np.count_nonzero((code.hx.astype(np.int64) @ code.hz.astype(np.int64).T) % 2)),
            "hx_rank_gf2": gf2_rank(code.hx), "hz_rank_gf2": gf2_rank(code.hz),
            "k_gf2": code.k,
        },
        "distance": {"status": "source_reported", "value": 6, "independently_verified": False},
        "assessment_status": "not_assessed",
        "recipe": {
            "tool": "tools/freeze_bb72_source.py",
            "command": "PYTHONPATH=src:. python tools/freeze_bb72_source.py --source-dir <clean-pinned-checkout> --artifact-output data/artifacts/bb72-css.json --provenance-output data/artifacts/bb72-css.provenance.json",
        },
    }
    provenance_output.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--artifact-output", type=Path, required=True)
    parser.add_argument("--provenance-output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.source_dir, args.artifact_output, args.provenance_output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
