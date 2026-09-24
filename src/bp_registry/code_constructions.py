"""Deterministic, source-traced CSS pilot-code constructions.

The functions here construct immutable inputs for Phase 3 experiments.  They
deliberately distinguish source-specified check matrices from the ordered
logical bases derived by this project over GF(2).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
from pathlib import Path
import zipfile

import numpy as np

from .css import CssCode, semantic_sha256


_B1_ELL = 63
_B1_BLOCKS = 7
_B1_A_EXPONENTS: tuple[tuple[int | None, ...], ...] = (
    (27, None, None, None, None, 0, 54),
    (54, 27, None, None, None, None, 0),
    (0, 54, 27, None, None, None, None),
    (None, 0, 54, 27, None, None, None),
    (None, None, 0, 54, 27, None, None),
    (None, None, None, 0, 54, 27, None),
    (None, None, None, None, 0, 54, 27),
)
_B1_B_EXPONENTS = (0, 1, 6)
_MAX_MATRIX_DIMENSION = 10_000
_MAX_MATRIX_CELLS = 2_000_000
_MAX_NPZ_BYTES = 1_000_000
_MAX_NPZ_UNCOMPRESSED_BYTES = 2_000_000


@dataclass(frozen=True)
class GallagerConstituent:
    """A frozen classical (3,4)-regular constituent and its exact draws."""

    matrix: np.ndarray
    seed: int
    permutations: tuple[tuple[int, ...], tuple[int, ...]]


def _bits(value: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2 or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be a two-dimensional integer matrix")
    if array.size > _MAX_MATRIX_CELLS or any(size > _MAX_MATRIX_DIMENSION for size in array.shape):
        raise ValueError(f"{name} exceeds bounded artifact dimensions")
    if np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be binary")
    return np.array(array, dtype=np.uint8, copy=True)


def _rref(matrix: np.ndarray) -> tuple[np.ndarray, tuple[int, ...]]:
    """Return deterministic reduced row echelon form over GF(2)."""
    reduced = _bits(matrix, "matrix")
    row = 0
    pivots: list[int] = []
    for column in range(reduced.shape[1]):
        candidates = np.flatnonzero(reduced[row:, column])
        if candidates.size == 0:
            continue
        pivot = row + int(candidates[0])
        if pivot != row:
            reduced[[row, pivot]] = reduced[[pivot, row]]
        for other in range(reduced.shape[0]):
            if other != row and reduced[other, column]:
                reduced[other] ^= reduced[row]
        pivots.append(column)
        row += 1
        if row == reduced.shape[0]:
            break
    return reduced[:row], tuple(pivots)


def _nullspace(matrix: np.ndarray) -> np.ndarray:
    """Return a free-column-ordered row basis for a GF(2) nullspace."""
    reduced, pivots = _rref(matrix)
    pivot_set = set(pivots)
    free = [column for column in range(reduced.shape[1]) if column not in pivot_set]
    basis = np.zeros((len(free), reduced.shape[1]), dtype=np.uint8)
    for index, column in enumerate(free):
        basis[index, column] = 1
        for pivot_row, pivot_column in enumerate(pivots):
            basis[index, pivot_column] = reduced[pivot_row, column]
    return basis


def _quotient_basis(kernel: np.ndarray, stabilizers: np.ndarray, dimension: int) -> np.ndarray:
    """Choose the first deterministic independent quotient representatives."""
    echelon, pivots = _rref(stabilizers)
    pivot_rows = {column: echelon[index].copy() for index, column in enumerate(pivots)}
    selected: list[np.ndarray] = []
    for candidate in kernel:
        reduced = candidate.copy()
        while True:
            nonzero = np.flatnonzero(reduced)
            if nonzero.size == 0:
                break
            pivot = int(nonzero[0])
            previous = pivot_rows.get(pivot)
            if previous is None:
                pivot_rows[pivot] = reduced
                selected.append(candidate.copy())
                break
            reduced ^= previous
        if len(selected) == dimension:
            return np.asarray(selected, dtype=np.uint8)
    raise ValueError("kernel does not contain the requested quotient basis")


def _inverse(matrix: np.ndarray) -> np.ndarray:
    """Invert a square GF(2) matrix or reject a degenerate pairing."""
    value = _bits(matrix, "pairing")
    if value.shape[0] != value.shape[1]:
        raise ValueError("pairing must be square")
    width = value.shape[0]
    augmented = np.concatenate((value, np.eye(width, dtype=np.uint8)), axis=1)
    reduced, pivots = _rref(augmented)
    if pivots[:width] != tuple(range(width)) or reduced.shape[0] != width:
        raise ValueError("logical pairing is singular")
    return reduced[:, width:]


def derive_css_logicals(hx: np.ndarray, hz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Derive a deterministic ordered paired logical basis over GF(2).

    This is a project convention: free columns and quotient representatives are
    selected in increasing canonical column order, then the Z representatives
    are normalized so that ``Lx @ Lz.T == I`` over GF(2).
    """
    provisional = CssCode(hx=_bits(hx, "Hx"), hz=_bits(hz, "Hz")).validate()
    dimension = provisional.k
    if dimension == 0:
        empty = np.zeros((0, provisional.n), dtype=np.uint8)
        return empty, empty
    lx = _quotient_basis(_nullspace(provisional.hz), provisional.hx, dimension)
    lz_unpaired = _quotient_basis(_nullspace(provisional.hx), provisional.hz, dimension)
    pairing = (lx.astype(np.int64) @ lz_unpaired.astype(np.int64).T % 2).astype(np.uint8)
    lz = (_inverse(pairing).T.astype(np.int64) @ lz_unpaired.astype(np.int64) % 2).astype(np.uint8)
    return lx, lz


def _circulant(length: int, exponents: tuple[int, ...]) -> np.ndarray:
    """Row-major polynomial circulant: x**e has a one at column ``e`` in row 0."""
    matrix = np.zeros((length, length), dtype=np.uint8)
    for exponent in exponents:
        if not 0 <= exponent < length:
            raise ValueError("circulant exponent is outside the declared modulus")
        matrix ^= np.roll(np.eye(length, dtype=np.uint8), exponent, axis=1)
    return matrix


def build_b1_ghp() -> CssCode:
    """Expand Panteleev--Kalachev v3 Appendix-B B1 in a frozen convention.

    Block rows and columns follow the displayed 7-by-7 matrix order.  Each
    polynomial is expanded in R=GF(2)[x]/(x**63-1) using the row-major
    circulant convention documented by :func:`_circulant`.
    """
    blocks = [
        [np.zeros((_B1_ELL, _B1_ELL), dtype=np.uint8) if exponent is None else _circulant(_B1_ELL, (exponent,))
         for exponent in row]
        for row in _B1_A_EXPONENTS
    ]
    a = np.block(blocks)
    b = np.kron(np.eye(_B1_BLOCKS, dtype=np.uint8), _circulant(_B1_ELL, _B1_B_EXPONENTS))
    hx = np.hstack((a, b))
    # For binary circulants the source involution/star expands as transpose.
    hz = np.hstack((b.T, a.T))
    lx, lz = derive_css_logicals(hx, hz)
    return CssCode(hx=hx, hz=hz, lx=lx, lz=lz).validate()


def build_gallager_constituent(*, seed: int = 20260923) -> GallagerConstituent:
    """Build one 9-by-12 Gallager-family (3,4)-regular classical matrix."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    base = np.tile(np.eye(3, dtype=np.uint8), (1, 4))
    generator = np.random.Generator(np.random.PCG64(seed))
    permutations = tuple(tuple(int(item) for item in generator.permutation(12)) for _ in range(2))
    matrix = np.vstack((base, base[:, permutations[0]], base[:, permutations[1]])).astype(np.uint8)
    return GallagerConstituent(matrix=matrix, seed=seed, permutations=permutations)


def build_hgp(constituent: np.ndarray) -> CssCode:
    """Build the standard self-product CSS code from a binary m-by-n matrix."""
    check = _bits(constituent, "constituent")
    checks, variables = check.shape
    hx = np.hstack((np.kron(np.eye(variables, dtype=np.uint8), check),
                    np.kron(check.T, np.eye(checks, dtype=np.uint8))))
    hz = np.hstack((np.kron(check, np.eye(variables, dtype=np.uint8)),
                    np.kron(np.eye(checks, dtype=np.uint8), check.T)))
    lx, lz = derive_css_logicals(hx, hz)
    return CssCode(hx=hx, hz=hz, lx=lx, lz=lz).validate()


def _write_npz_arrays(arrays: dict[str, np.ndarray], artifact_path: Path) -> None:
    """Write named primitive arrays with fixed ZIP metadata for byte replay."""
    with zipfile.ZipFile(artifact_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, array in arrays.items():
            buffer = io.BytesIO()
            np.lib.format.write_array(buffer, np.asarray(array, dtype=np.uint8), allow_pickle=False)
            member = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o600 << 16
            archive.writestr(member, buffer.getvalue(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def write_css_npz(code: CssCode, artifact_path: Path) -> None:
    """Write primitive CSS arrays as a reproducible, pickle-free NPZ archive."""
    validated = code.validate()
    if validated.lx is None or validated.lz is None:
        raise ValueError("frozen CSS artifacts require an ordered logical basis")
    _write_npz_arrays(
        {"hx": validated.hx, "hz": validated.hz, "lx": validated.lx, "lz": validated.lz}, artifact_path
    )


def write_hgp_npz(constituent: GallagerConstituent, code: CssCode, artifact_path: Path) -> None:
    """Freeze a generated Gallager constituent and its derived self-product."""
    validated = code.validate()
    if validated.lx is None or validated.lz is None:
        raise ValueError("frozen CSS artifacts require an ordered logical basis")
    _write_npz_arrays(
        {
            "constituent": _bits(constituent.matrix, "constituent"),
            "permutations": np.asarray(constituent.permutations, dtype=np.uint8),
            "hx": validated.hx,
            "hz": validated.hz,
            "lx": validated.lx,
            "lz": validated.lz,
        },
        artifact_path,
    )


def _confined_artifact(root: str | Path, relative_path: str | Path) -> Path:
    approved_root = Path(root).resolve(strict=True)
    if not approved_root.is_dir():
        raise ValueError("approved artifact root must be a directory")
    requested = Path(relative_path)
    if requested.is_absolute() or ".." in requested.parts:
        raise ValueError("artifact path escapes approved root")
    candidate = approved_root / requested
    cursor = approved_root
    for part in requested.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("artifact path may not traverse a symlink")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(approved_root) or not resolved.is_file():
        raise ValueError("artifact path must identify a regular file under the approved root")
    return resolved


def load_frozen_css_npz(
    root: str | Path,
    relative_path: str | Path,
    *,
    expected_raw_sha256: str | None = None,
    expected_semantic_sha256: str | None = None,
) -> CssCode:
    """Load a bounded, confined primitive-array CSS archive without pickle."""
    artifact = _confined_artifact(root, relative_path)
    if artifact.stat().st_size > _MAX_NPZ_BYTES:
        raise ValueError("NPZ artifact exceeds compressed size limit")
    raw = artifact.read_bytes()
    if expected_raw_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_raw_sha256:
        raise ValueError("raw SHA-256 does not match NPZ artifact bytes")
    allowed = {"hx.npy", "hz.npy", "lx.npy", "lz.npy", "constituent.npy", "permutations.npy"}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if not members or any(member.filename not in allowed for member in members):
            raise ValueError("NPZ artifact has unexpected members")
        if sum(member.file_size for member in members) > _MAX_NPZ_UNCOMPRESSED_BYTES:
            raise ValueError("NPZ artifact exceeds uncompressed size limit")
    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        if not {"hx", "hz", "lx", "lz"}.issubset(archive.files):
            raise ValueError("NPZ artifact lacks required CSS arrays")
        arrays = {name: archive[name] for name in archive.files}
    if any(array.dtype != np.uint8 for array in arrays.values()):
        raise ValueError("NPZ artifact arrays must be primitive uint8")
    code = CssCode(hx=arrays["hx"], hz=arrays["hz"], lx=arrays["lx"], lz=arrays["lz"]).validate()
    if expected_semantic_sha256 is not None and semantic_sha256(code) != expected_semantic_sha256:
        raise ValueError("semantic SHA-256 does not match CSS content")
    return code


def artifact_metadata(code: CssCode, artifact_path: Path) -> dict[str, str]:
    """Return the two identities that bind a frozen primitive-array artifact."""
    return {
        "raw_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        "semantic_sha256": semantic_sha256(code),
    }
