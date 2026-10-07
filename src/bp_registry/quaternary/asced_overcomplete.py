"""Qualified, deterministic overcomplete aSCED check maps.

The paper's supplied matrices remain comparison data.  Canonical execution
constructs its own map from the receipt-bound ``[H_X, T_X, H_Z, T_Z]`` graph,
then carries the same GF(2) map from the extended syndrome to the overcomplete
syndrome.  Nothing in this module observes or mutates a physical syndrome.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from typing import Literal

import numpy as np

from ..css import gf2_rank
from .asced import QualifiedAscedBatch, _verify_qualified_batch


RunFidelity = Literal["canonical_adaptation", "source_comparison"]
_ROW_ORDER = ("H_X", "T_X", "H_Z", "T_Z")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _digest(value: object) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _binary_matrix(value: object, *, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2 or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a two-dimensional binary integer matrix")
    result = np.array(array, dtype=np.uint8, copy=True)
    result.setflags(write=False)
    return result


def _binary_vector(value: object, *, name: str, length: int) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != (length,) or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary vector of length {length}")
    result = np.array(array, dtype=np.uint8, copy=True)
    result.setflags(write=False)
    return result


def _normalise_row_map(row_map: object, *, rows: int) -> tuple[tuple[str, str, int], ...]:
    try:
        normalised = tuple((str(role), str(origin), int(index)) for role, origin, index in row_map)  # type: ignore[misc]
    except (TypeError, ValueError) as error:
        raise ValueError("extended row map must contain typed (role, origin, index) entries") from error
    if len(normalised) != rows:
        raise ValueError("extended row map length must equal H_ext rows")
    expected_blocks = (("x", "original"), ("x", "splitter"), ("z", "original"), ("z", "splitter"))
    block_index = 0
    last_index = -1
    for role, origin, index in normalised:
        if index < 0:
            raise ValueError("extended row-map indices must be nonnegative")
        while block_index < len(expected_blocks) and (role, origin) != expected_blocks[block_index]:
            block_index += 1
            last_index = -1
        if block_index == len(expected_blocks) or index <= last_index:
            raise ValueError("extended row map must preserve [H_X,T_X,H_Z,T_Z] block order")
        last_index = index
    return normalised


def _validate_row_order(row_order: object) -> tuple[str, str, str, str]:
    result = tuple(row_order)  # type: ignore[arg-type]
    if result != _ROW_ORDER:
        raise ValueError("aSCED overcomplete maps require row order [H_X,T_X,H_Z,T_Z]")
    return _ROW_ORDER


def _pauli_support_matrix(value: object, *, row_map: tuple[tuple[str, str, int], ...]) -> tuple[np.ndarray, np.ndarray]:
    """Return canonical raw Pauli rows and their GF(2) support matrix."""
    raw = np.asarray(value)
    if raw.ndim != 2 or not np.issubdtype(raw.dtype, np.integer) or np.any(~np.isin(raw, (0, 1, 3))):
        raise ValueError("constructed H_ext must be a two-dimensional I/X/Z integer matrix")
    if raw.shape[0] != len(row_map):
        raise ValueError("constructed H_ext and row map lengths must agree")
    expected_value = {"x": 1, "z": 3}
    for row, (role, _origin, _index) in zip(raw, row_map):
        if np.any((row != 0) & (row != expected_value[role])):
            raise ValueError("constructed H_ext row Pauli type disagrees with its typed row map")
    copied = np.array(raw, dtype=np.uint8, copy=True)
    copied.setflags(write=False)
    support = np.asarray(copied != 0, dtype=np.uint8)
    support.setflags(write=False)
    return copied, support


@dataclass(frozen=True, slots=True)
class OvercompleteSearchReceipt:
    """One bounded, ordered same-type pair search witness."""

    role: Literal["x", "z"]
    pair_cap: int
    pairs_examined: int
    accepted_pair: tuple[int, int] | None
    accepted_image: tuple[int, ...] | None
    rejected_zero: int
    rejected_existing: int
    terminal_status: Literal["accepted", "exhausted"]


@dataclass(frozen=True, slots=True)
class OvercompleteSearchExhausted:
    """Non-runnable terminal produced when either required extra row is absent."""

    role: Literal["x", "z"]
    pair_cap: int
    receipts: tuple[OvercompleteSearchReceipt, ...]
    terminal_status: Literal["exhausted"] = "exhausted"


@dataclass(frozen=True, slots=True)
class AscedOvercompleteMap:
    """Immutable qualified GF(2) transform from extended to overcomplete checks."""

    h_ext: np.ndarray
    mapping: np.ndarray
    h_oc: np.ndarray
    row_order: tuple[str, str, str, str]
    row_origin_map: tuple[tuple[str, str, int], ...]
    fidelity: RunFidelity
    h_ext_sha256: str
    row_origin_sha256: str
    mapping_sha256: str
    h_oc_sha256: str
    qualification_sha256: str
    comparison_only: bool

    def __post_init__(self) -> None:
        h_ext = _binary_matrix(self.h_ext, name="H_ext")
        mapping = _binary_matrix(self.mapping, name="M")
        h_oc = _binary_matrix(self.h_oc, name="H_oc")
        row_order = _validate_row_order(self.row_order)
        row_map = _normalise_row_map(self.row_origin_map, rows=h_ext.shape[0])
        if mapping.shape[1] != h_ext.shape[0] or h_oc.shape != (mapping.shape[0], h_ext.shape[1]):
            raise ValueError("overcomplete matrix shapes are incompatible")
        if gf2_rank(mapping) != h_ext.shape[0]:
            raise ValueError("M must retain every extended syndrome bit")
        if not np.array_equal((mapping.astype(np.int64) @ h_ext.astype(np.int64)) % 2, h_oc):
            raise ValueError("overcomplete checks must satisfy H_oc=M H_ext over GF(2)")
        if self.comparison_only != (self.fidelity == "source_comparison"):
            raise ValueError("only source-comparison maps may be marked comparison-only")
        expected = {
            "h_ext": h_ext.tolist(), "mapping": mapping.tolist(), "h_oc": h_oc.tolist(),
            "row_order": list(row_order), "row_origin_map": [list(item) for item in row_map],
            "fidelity": self.fidelity, "comparison_only": self.comparison_only,
        }
        if (
            self.h_ext_sha256 != _digest(h_ext.tolist())
            or self.row_origin_sha256 != _digest([list(item) for item in row_map])
            or self.mapping_sha256 != _digest(mapping.tolist())
            or self.h_oc_sha256 != _digest(h_oc.tolist())
            or self.qualification_sha256 != _digest(expected)
        ):
            raise ValueError("overcomplete map receipt digest does not match its content")
        object.__setattr__(self, "h_ext", h_ext)
        object.__setattr__(self, "mapping", mapping)
        object.__setattr__(self, "h_oc", h_oc)
        object.__setattr__(self, "row_order", row_order)
        object.__setattr__(self, "row_origin_map", row_map)


@dataclass(frozen=True, slots=True)
class ConstructedOvercompleteReceipt:
    """Content-addressed canonical map bound to one constructed splitter receipt."""

    run_fidelity: Literal["canonical_adaptation"]
    constructed_splitter_receipt_sha256: str
    h_ext_sha256: str
    h_ext_row_map_sha256: str
    construction_profile_sha256: str
    mapping_sha256: str
    h_oc_sha256: str
    row_order_sha256: str
    qualification_sha256: str
    receipt_sha256: str


def qualify_overcomplete_map(
    *,
    h_ext: object,
    h_oc: object,
    mapping: object,
    row_order: object,
    row_origin_map: object,
    fidelity: RunFidelity = "canonical_adaptation",
) -> AscedOvercompleteMap:
    """Validate a generic frozen map before any decoder path may consume it."""
    extended = _binary_matrix(h_ext, name="H_ext")
    matrix = _binary_matrix(mapping, name="M")
    overcomplete = _binary_matrix(h_oc, name="H_oc")
    order = _validate_row_order(row_order)
    origins = _normalise_row_map(row_origin_map, rows=extended.shape[0])
    comparison_only = fidelity == "source_comparison"
    payload = {
        "h_ext": extended.tolist(), "mapping": matrix.tolist(), "h_oc": overcomplete.tolist(),
        "row_order": list(order), "row_origin_map": [list(item) for item in origins],
        "fidelity": fidelity, "comparison_only": comparison_only,
    }
    return AscedOvercompleteMap(
        extended, matrix, overcomplete, order, origins, fidelity,
        _digest(extended.tolist()), _digest([list(item) for item in origins]),
        _digest(matrix.tolist()), _digest(overcomplete.tolist()), _digest(payload), comparison_only,
    )


def map_overcomplete_syndrome(overcomplete: AscedOvercompleteMap, z_ext: object) -> np.ndarray:
    """Apply the already-qualified ``M`` to immutable ordered extended bits."""
    if not isinstance(overcomplete, AscedOvercompleteMap):
        raise ValueError("overcomplete syndrome mapping requires a qualified AscedOvercompleteMap")
    if overcomplete.comparison_only:
        raise ValueError("pinned source comparison maps cannot be applied in canonical execution")
    syndrome = _binary_vector(z_ext, name="z_ext", length=overcomplete.h_ext.shape[0])
    mapped = np.asarray((overcomplete.mapping.astype(np.int64) @ syndrome.astype(np.int64)) % 2, dtype=np.uint8)
    mapped.setflags(write=False)
    return mapped


def assemble_extended_syndrome(
    overcomplete: AscedOvercompleteMap,
    *,
    s_x: object,
    g_x: object,
    s_z: object,
    g_z: object,
) -> np.ndarray:
    """Build the only admitted typed order: ``[s_X, g_X, s_Z, g_Z]``.

    Callers pass each semantic segment by name so equal-sized X/Z or
    original/splitter blocks cannot be silently swapped before ``M`` applies.
    """
    if not isinstance(overcomplete, AscedOvercompleteMap):
        raise ValueError("extended syndrome assembly requires a qualified AscedOvercompleteMap")
    groups = tuple(
        sum(1 for item in overcomplete.row_origin_map if item[:2] == block)
        for block in (("x", "original"), ("x", "splitter"), ("z", "original"), ("z", "splitter"))
    )
    parts = tuple(
        _binary_vector(value, name=name, length=length)
        for value, name, length in zip((s_x, g_x, s_z, g_z), ("s_X", "g_X", "s_Z", "g_Z"), groups)
    )
    result = np.concatenate(parts).astype(np.uint8, copy=False)
    result.setflags(write=False)
    return result


def _search_extra_row(
    h_ext: np.ndarray,
    indices: tuple[int, ...],
    *,
    role: Literal["x", "z"],
    pair_cap: int,
    forbidden_images: tuple[tuple[int, ...], ...] = (),
) -> tuple[np.ndarray, OvercompleteSearchReceipt] | OvercompleteSearchExhausted:
    existing = {tuple(row.tolist()) for row in h_ext} | set(forbidden_images)
    zero = duplicate = examined = 0
    for left, right in combinations(indices, 2):
        if examined >= pair_cap:
            break
        examined += 1
        image = h_ext[left] ^ h_ext[right]
        image_key = tuple(image.tolist())
        if not image.any():
            zero += 1
            continue
        if image_key in existing:
            duplicate += 1
            continue
        return image, OvercompleteSearchReceipt(role, pair_cap, examined, (left, right), image_key, zero, duplicate, "accepted")
    receipt = OvercompleteSearchReceipt(role, pair_cap, examined, None, None, zero, duplicate, "exhausted")
    return OvercompleteSearchExhausted(role, pair_cap, (receipt,))


def construct_overcomplete_map(
    batch: QualifiedAscedBatch,
    *,
    pair_cap: int = 1000,
) -> tuple[AscedOvercompleteMap, ConstructedOvercompleteReceipt, tuple[OvercompleteSearchReceipt, ...]] | OvercompleteSearchExhausted:
    """Build the selected deterministic two-extra-row canonical map.

    Only a complete :class:`QualifiedAscedBatch` crosses this boundary.  The
    Plan 10-10 verifier replays every splitter witness and receipt before its
    immutable ``H_ext`` and typed row map become construction inputs.  Search
    works on binary supports, with one lexicographically first new XOR image
    from each same-type block. An exhausted terminal has no runnable map.
    """
    if not isinstance(batch, QualifiedAscedBatch):
        raise ValueError("canonical overcomplete construction requires a complete QualifiedAscedBatch")
    if type(pair_cap) is not int or not 1 <= pair_cap <= 1000:
        raise ValueError("overcomplete pair cap must be an integer in [1, 1000]")
    _verify_qualified_batch(batch)
    row_map = _normalise_row_map(batch.h_ext_row_map, rows=batch.h_ext.shape[0])
    raw, extended = _pauli_support_matrix(batch.h_ext, row_map=row_map)
    source_h_ext_digest = _digest({"rows": raw.tolist(), "row_map": [list(item) for item in row_map]})
    if source_h_ext_digest != batch.receipt.h_ext_sha256:
        raise ValueError("canonical overcomplete construction rejected an H_ext/constructed-splitter receipt mismatch")
    x_indices = tuple(index for index, (role, _origin, _local) in enumerate(row_map) if role == "x")
    z_indices = tuple(index for index, (role, _origin, _local) in enumerate(row_map) if role == "z")
    x_result = _search_extra_row(extended, x_indices, role="x", pair_cap=pair_cap)
    if isinstance(x_result, OvercompleteSearchExhausted):
        return x_result
    x_image, x_receipt = x_result
    z_result = _search_extra_row(
        extended, z_indices, role="z", pair_cap=pair_cap,
        forbidden_images=(tuple(x_image.tolist()),),
    )
    if isinstance(z_result, OvercompleteSearchExhausted):
        return OvercompleteSearchExhausted("z", pair_cap, (x_receipt, *z_result.receipts))
    z_image, z_receipt = z_result
    identity = np.eye(extended.shape[0], dtype=np.uint8)
    x_pair = x_receipt.accepted_pair
    z_pair = z_receipt.accepted_pair
    assert x_pair is not None and z_pair is not None
    x_coefficients = identity[x_pair[0]] ^ identity[x_pair[1]]
    z_coefficients = identity[z_pair[0]] ^ identity[z_pair[1]]
    mapping = np.vstack((identity, x_coefficients, z_coefficients))
    h_oc = np.vstack((extended, x_image, z_image))
    qualified = qualify_overcomplete_map(
        h_ext=extended, h_oc=h_oc, mapping=mapping, row_order=_ROW_ORDER,
        row_origin_map=row_map, fidelity="canonical_adaptation",
    )
    profile = {"pair_cap_per_type": pair_cap, "search": "lexicographic_first_same_type_xor", "extras": "one_x_then_one_z"}
    receipt_payload = {
        "run_fidelity": "canonical_adaptation",
        "constructed_splitter_receipt_sha256": batch.receipt.receipt_sha256,
        "h_ext_sha256": source_h_ext_digest,
        "h_ext_row_map_sha256": _digest([list(item) for item in row_map]),
        "construction_profile_sha256": _digest(profile),
        "mapping_sha256": qualified.mapping_sha256,
        "h_oc_sha256": qualified.h_oc_sha256,
        "row_order_sha256": _digest(list(_ROW_ORDER)),
        "qualification_sha256": qualified.qualification_sha256,
    }
    receipt = ConstructedOvercompleteReceipt(**receipt_payload, receipt_sha256=_digest(receipt_payload))
    return qualified, receipt, (x_receipt, z_receipt)


__all__ = [
    "AscedOvercompleteMap", "ConstructedOvercompleteReceipt", "OvercompleteSearchExhausted",
    "OvercompleteSearchReceipt", "assemble_extended_syndrome", "construct_overcomplete_map", "map_overcomplete_syndrome",
    "qualify_overcomplete_map",
]
