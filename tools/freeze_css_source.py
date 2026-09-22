#!/usr/bin/env python3
"""Probe a pinned Bravyi source tree before freezing a CSS artifact.

The script intentionally does not import ``decoder_setup.py``: that program
also builds circuit data and writes files.  Instead it reads its pinned source,
checks the committed construction statement, and reproduces only the published
matrix construction.  A freeze is permitted only when independent GF(2)
checks and the requested bposd logical basis agree.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

from bp_registry.css import CssCode, gf2_rank, semantic_sha256


BRAVYI_REVISION = "fa77e3333d3ec44c79d8f914dd24c040d1da471b"
SOURCE_FILE = "decoder_setup.py"


class SourceGateError(ValueError):
    """Raised when a source tree cannot establish a safe frozen artifact."""


def _git(source_dir: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(source_dir), *args], text=True, stderr=subprocess.STDOUT
    ).strip()


def _source_assignments(source_bytes: bytes) -> dict[str, int]:
    """Read only the active literal parameter assignments from the source file."""
    tree = ast.parse(source_bytes.decode("utf-8"), filename=SOURCE_FILE)
    values: dict[str, int] = {}
    required = {"ell", "m", "a1", "a2", "a3", "b1", "b2", "b3"}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (TypeError, ValueError):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in required:
                values[target.id] = value
            elif isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (tuple, list)):
                for name, item in zip(target.elts, value, strict=True):
                    if isinstance(name, ast.Name) and name.id in required:
                        values[name.id] = item
    if set(values) != required or any(type(item) is not int for item in values.values()):
        raise SourceGateError("pinned source does not expose all literal BB construction parameters")
    return values


def _assert_construction_shape(source_text: str) -> None:
    """Reject a same-parameter source whose matrix assembly has changed."""
    normalized = "".join(source_text.split())
    required_fragments = (
        "A=(x[a1]+y[a2]+y[a3])%2",
        "B=(y[b1]+x[b2]+x[b3])%2",
        "hx=np.hstack((A,B))",
        "hz=np.hstack((BT,AT))",
    )
    if any(fragment not in normalized for fragment in required_fragments):
        raise SourceGateError("pinned source matrix construction no longer matches the reviewed BB recipe")


def construct_from_pinned_source(source_dir: str | Path) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    """Return source metadata and its Hx/Hz rows without executing source code."""
    root = Path(source_dir).resolve(strict=True)
    revision = _git(root, "rev-parse", "HEAD")
    if revision != BRAVYI_REVISION:
        raise SourceGateError(f"source revision is {revision}, expected {BRAVYI_REVISION}")
    if _git(root, "status", "--porcelain"):
        raise SourceGateError("source checkout has uncommitted changes")
    source_path = root / SOURCE_FILE
    source_bytes = source_path.read_bytes()
    source_text = source_bytes.decode("utf-8")
    _assert_construction_shape(source_text)
    p = _source_assignments(source_bytes)
    ell, m = p["ell"], p["m"]
    identity_ell = np.identity(ell, dtype=np.uint8)
    identity_m = np.identity(m, dtype=np.uint8)
    x = {index: np.kron(np.roll(identity_ell, index, axis=1), identity_m).astype(np.uint8)
         for index in range(ell)}
    y = {index: np.kron(identity_ell, np.roll(identity_m, index, axis=1)).astype(np.uint8)
         for index in range(m)}
    a = (x[p["a1"]] + y[p["a2"]] + y[p["a3"]]) % 2
    b = (y[p["b1"]] + x[p["b2"]] + x[p["b3"]]) % 2
    hx = np.hstack((a, b)).astype(np.uint8)
    hz = np.hstack((b.T, a.T)).astype(np.uint8)
    metadata: dict[str, Any] = {
        "repository": "https://github.com/sbravyi/BivariateBicycleCodes",
        "revision": revision,
        "source_file": SOURCE_FILE,
        "source_file_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "parameters": p,
        "matrix_ordering": "Hx=[A|B], Hz=[B^T|A^T], columns=left block then right block",
    }
    return metadata, hx, hz


def probe(source_dir: str | Path) -> dict[str, Any]:
    """Report independent source facts and every failing artifact gate."""
    metadata, hx, hz = construct_from_pinned_source(source_dir)
    commutator = (hx.astype(np.int64) @ hz.astype(np.int64).T) % 2
    independent = {
        "hx_shape": list(hx.shape),
        "hz_shape": list(hz.shape),
        "hx_rank_gf2": gf2_rank(hx),
        "hz_rank_gf2": gf2_rank(hz),
        "k_gf2": int(hx.shape[1] - gf2_rank(hx) - gf2_rank(hz)),
        "commutator_nonzero_entries": int(np.count_nonzero(commutator)),
    }
    gates: list[str] = []
    if independent["commutator_nonzero_entries"]:
        gates.append("reconstructed Hx and Hz do not commute over GF(2)")
    logical_provider: dict[str, Any]
    try:
        from bposd.css import css_code

        code = css_code(hx, hz)
        css_path = Path(inspect.getfile(css_code))
        logical_provider = {
            "package": "bposd",
            "version": importlib.metadata.version("bposd"),
            "module_sha256": hashlib.sha256(css_path.read_bytes()).hexdigest(),
            "reported_k": int(code.K),
            "lx_rows": int(code.lx.shape[0]),
            "lz_rows": int(code.lz.shape[0]),
        }
        if code.K != code.lx.shape[0] or code.K != code.lz.shape[0]:
            gates.append("bposd reported K does not equal emitted logical-row count")
    except Exception as exc:  # pragma: no cover - only environment failure paths
        logical_provider = {"error": f"{type(exc).__name__}: {exc}"}
        gates.append("bposd logical extraction did not complete")
    return {"source": metadata, "independent": independent,
            "logical_provider": logical_provider, "gates": gates,
            "eligible_for_freeze": not gates}


def _matrix_sha256(matrix: np.ndarray) -> str:
    """Fingerprint exact row-major binary rows with their dimensions."""
    packed_shape = np.asarray(matrix.shape, dtype="<u8").tobytes()
    return hashlib.sha256(packed_shape + np.asarray(matrix, dtype=np.uint8).tobytes()).hexdigest()


def _gf2_inverse(matrix: np.ndarray) -> np.ndarray:
    """Invert a square GF(2) matrix, rejecting a non-paired logical basis."""
    size = matrix.shape[0]
    if matrix.shape != (size, size):
        raise SourceGateError("logical pairing matrix is not square")
    work = np.concatenate((matrix.copy().astype(np.uint8) % 2, np.eye(size, dtype=np.uint8)), axis=1)
    for column in range(size):
        pivots = np.flatnonzero(work[column:, column])
        if not pivots.size:
            raise SourceGateError("source logical pairing matrix is singular over GF(2)")
        pivot = column + int(pivots[0])
        if pivot != column:
            work[[column, pivot]] = work[[pivot, column]]
        for row in range(size):
            if row != column and work[row, column]:
                work[row] ^= work[column]
    return work[:, size:]


def freeze(source_dir: str | Path, artifact_output: str | Path, provenance_output: str | Path) -> dict[str, Any]:
    """Materialize a validated project artifact and its source/provenance ledger."""
    result = probe(source_dir)
    if not result["eligible_for_freeze"]:
        raise SourceGateError("; ".join(result["gates"]))
    metadata, hx, hz = construct_from_pinned_source(source_dir)
    from bposd.css import css_code

    provided = css_code(hx, hz)
    source_lx = np.asarray(provided.lx.toarray(), dtype=np.uint8)
    source_lz = np.asarray(provided.lz.toarray(), dtype=np.uint8)
    pairing = (source_lx.astype(np.int64) @ source_lz.astype(np.int64).T % 2).astype(np.uint8)
    # Preserve bposd's Lx row order and explicitly pair its Lz rows.
    paired_lz = (_gf2_inverse(pairing).T @ source_lz % 2).astype(np.uint8)
    code = CssCode(hx=hx, hz=hz, lx=source_lx, lz=paired_lz).validate()
    artifact = {"format_version": 1, "hx": code.hx.tolist(), "hz": code.hz.tolist(),
                "lx": code.lx.tolist(), "lz": code.lz.tolist()}
    artifact_path, provenance_path = Path(artifact_output), Path(provenance_output)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_bytes = (json.dumps(artifact, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
    artifact_path.write_bytes(artifact_bytes)
    provenance = {
        "format_version": 1, "code_id": "gross-bb-144",
        "artifact": {"path": str(artifact_path), "raw_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
                     "semantic_sha256": semantic_sha256(code),
                     "shapes": {"hx": list(code.hx.shape), "hz": list(code.hz.shape), "lx": list(code.lx.shape), "lz": list(code.lz.shape)}},
        "source": metadata,
        "logical_provider": {**result["logical_provider"], "source_lx_row_sha256": _matrix_sha256(source_lx),
                             "source_lz_row_sha256": _matrix_sha256(source_lz), "source_pairing_sha256": _matrix_sha256(pairing),
                             "paired_lz_row_sha256": _matrix_sha256(paired_lz),
                             "pairing_normalization": "Lx order retained; Lz <- (Lx Lz^T)^(-T) Lz over GF(2)"},
        "independent_validation": result["independent"],
        "recipe": {"command": "python tools/freeze_css_source.py --source-dir <clean-pinned-checkout> --artifact-output data/artifacts/selected-css.json --provenance-output data/artifacts/selected-css.provenance.json", "tool": "tools/freeze_css_source.py"},
    }
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="write the probe JSON to this path")
    parser.add_argument("--artifact-output", type=Path, help="freeze validated CSS rows to this JSON path")
    parser.add_argument("--provenance-output", type=Path, help="write the corresponding provenance JSON")
    args = parser.parse_args()
    if (args.artifact_output is None) != (args.provenance_output is None):
        parser.error("--artifact-output and --provenance-output must be used together")
    if args.artifact_output:
        print(json.dumps(freeze(args.source_dir, args.artifact_output, args.provenance_output), indent=2, sort_keys=True))
        return 0
    result = probe(args.source_dir)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["eligible_for_freeze"] else 2


if __name__ == "__main__":
    sys.exit(main())
