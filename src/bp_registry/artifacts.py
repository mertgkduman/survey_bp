"""Confined, version-dispatched CSS artifact loading."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .css import CssCode, semantic_sha256


MAX_ARTIFACT_BYTES = 1_000_000
MAX_MATRIX_DIMENSION = 10_000
MAX_MATRIX_CELLS = 2_000_000


@dataclass(frozen=True)
class LoadedArtifact:
    """A parsed artifact with independent raw and semantic identities."""

    code: CssCode
    format_version: int
    raw_sha256: str
    semantic_sha256: str


def _require_digest(value: str, name: str) -> str:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hexadecimal digest")
    return value


def _matrix(value: Any, name: str) -> np.ndarray:
    if not isinstance(value, list) or len(value) > MAX_MATRIX_DIMENSION:
        raise ValueError(f"{name} has invalid row dimensions")
    columns: int | None = None
    cells = 0
    for row in value:
        if not isinstance(row, list) or len(row) > MAX_MATRIX_DIMENSION:
            raise ValueError(f"{name} has invalid column dimensions")
        if columns is None:
            columns = len(row)
        elif len(row) != columns:
            raise ValueError(f"{name} rows have inconsistent lengths")
        cells += len(row)
        if cells > MAX_MATRIX_CELLS:
            raise ValueError(f"{name} exceeds matrix cell limit")
        if any(type(entry) is not int or entry not in (0, 1) for entry in row):
            raise ValueError(f"{name} must be binary integers")
    return np.asarray(value, dtype=np.uint8)


def _decode_v1(payload: dict[str, Any]) -> CssCode:
    required = {"format_version", "hx", "hz", "lx", "lz"}
    if set(payload) != required or payload.get("format_version") != 1:
        raise ValueError("v1 CSS artifact has an invalid schema")
    return CssCode(
        hx=_matrix(payload["hx"], "Hx"), hz=_matrix(payload["hz"], "Hz"),
        lx=_matrix(payload["lx"], "Lx"), lz=_matrix(payload["lz"], "Lz"),
    ).validate()


_DECODERS: dict[int, Callable[[dict[str, Any]], CssCode]] = {1: _decode_v1}


def _confined_file(root: str | Path, relative_path: str | Path) -> Path:
    approved_root = Path(root).resolve(strict=True)
    if not approved_root.is_dir():
        raise ValueError("approved root must be a directory")
    requested = Path(relative_path)
    if requested.is_absolute() or ".." in requested.parts:
        raise ValueError("artifact path escapes approved root")
    candidate = approved_root / requested
    cursor = approved_root
    for part in requested.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("artifact path may not traverse a symlink")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(candidate) from exc
    if not resolved.is_relative_to(approved_root):
        raise ValueError("artifact path escapes approved root")
    if not resolved.is_file():
        raise ValueError("artifact path must identify a regular file")
    return resolved


def load_artifact(
    root: str | Path,
    relative_path: str | Path,
    *,
    expected_raw_sha256: str | None = None,
    expected_semantic_sha256: str | None = None,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> LoadedArtifact:
    """Load an immutable CSS artifact without filesystem escape or blind trust.

    The reader dispatches on a stored version.  Future codecs must use a new
    version, allowing this v1 decoder to continue reading saved artifacts.
    """
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_ARTIFACT_BYTES:
        raise ValueError("max_bytes must be a positive bounded integer")
    artifact = _confined_file(root, relative_path)
    if artifact.suffix == ".npz":
        # Phase 3 frozen B1/HGP artifacts use the bounded, pickle-free archive
        # contract established by the code-construction boundary.  Reuse that
        # validator rather than treating a metadata JSON sidecar as decoder input.
        from .code_constructions import load_frozen_css_npz

        code = load_frozen_css_npz(
            root, relative_path,
            expected_raw_sha256=expected_raw_sha256,
            expected_semantic_sha256=expected_semantic_sha256,
        )
        return LoadedArtifact(
            code=code,
            format_version=1,
            raw_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
            semantic_sha256=semantic_sha256(code),
        )
    if artifact.suffix != ".json":
        raise ValueError("unsupported CSS artifact format")
    if artifact.stat().st_size > max_bytes:
        raise ValueError("artifact exceeds size limit")
    raw_bytes = artifact.read_bytes()
    if len(raw_bytes) > max_bytes:
        raise ValueError("artifact exceeds size limit")
    raw_digest = hashlib.sha256(raw_bytes).hexdigest()
    if expected_raw_sha256 is not None:
        if raw_digest != _require_digest(expected_raw_sha256, "expected raw SHA-256"):
            raise ValueError("raw SHA-256 does not match artifact bytes")
    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("artifact is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict) or type(decoded.get("format_version")) is not int:
        raise ValueError("artifact needs an integer format_version")
    version = decoded["format_version"]
    decoder = _DECODERS.get(version)
    if decoder is None:
        raise ValueError(f"unsupported CSS artifact format version {version}")
    code = decoder(decoded)
    semantic_digest = semantic_sha256(code)
    if expected_semantic_sha256 is not None:
        if semantic_digest != _require_digest(expected_semantic_sha256, "expected semantic SHA-256"):
            raise ValueError("semantic SHA-256 does not match CSS content")
    return LoadedArtifact(code, version, raw_digest, semantic_digest)
