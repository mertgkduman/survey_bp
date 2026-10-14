"""Immutable general-stabilizer problems for the canonical quaternary kernel."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Literal

import numpy as np

from ..canonical.lineage import LineageEdge, LineageId
from ..code_constructions import derive_css_logicals
from ..css import CssCode, gf2_rank, semantic_sha256 as css_semantic_sha256
from .algebra import Pauli, syndrome, to_symplectic


RowRole = Literal["general", "x", "z"]


def _readonly(value: object, *, name: str, ndim: int) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != ndim or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be a {ndim}D integer Pauli array")
    if np.any((array < Pauli.I) | (array > Pauli.Z)):
        raise ValueError(f"{name} must use I=0, X=1, Y=2, Z=3 labels")
    copied = np.array(array, dtype=np.uint8, copy=True)
    copied.setflags(write=False)
    return copied


def _binary(value: object, *, name: str, length: int) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != (length,) or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary vector matching the ordered checks")
    copied = np.array(array, dtype=np.uint8, copy=True)
    copied.setflags(write=False)
    return copied


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _commutation_matrix(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left_bits, right_bits = to_symplectic(left), to_symplectic(right)
    return np.asarray(
        (left_bits[:, None, :, 0].astype(np.int64) * right_bits[None, :, :, 1].astype(np.int64)
         + left_bits[:, None, :, 1].astype(np.int64) * right_bits[None, :, :, 0].astype(np.int64)).sum(axis=2) % 2,
        dtype=np.uint8,
    )


@dataclass(frozen=True, slots=True)
class PauliCode:
    """Ordered immutable stabilizer checks and an optional paired logical basis."""

    checks: np.ndarray
    row_roles: tuple[RowRole, ...] | list[RowRole] | None = None
    row_original_indices: tuple[int, ...] | list[int] | None = None
    logical_x: np.ndarray | None = None
    logical_z: np.ndarray | None = None
    source_artifact_identity: str | None = None
    pauli_order: str = "I,X,Y,Z"

    def __post_init__(self) -> None:
        checks = _readonly(self.checks, name="checks", ndim=2)
        if checks.shape[0] == 0 or checks.shape[1] == 0:
            raise ValueError("Pauli code requires at least one check and one qubit")
        if np.any(np.all(checks == Pauli.I, axis=1)):
            raise ValueError("Pauli code checks must not contain identity-only rows")
        if np.any(_commutation_matrix(checks, checks)):
            raise ValueError("Pauli stabilizer checks must commute")
        roles = tuple("general" for _ in range(checks.shape[0])) if self.row_roles is None else tuple(self.row_roles)
        if len(roles) != checks.shape[0] or any(role not in {"general", "x", "z"} for role in roles):
            raise ValueError("row roles must name every check as general, x, or z")
        indices = tuple(range(checks.shape[0])) if self.row_original_indices is None else tuple(self.row_original_indices)
        if len(indices) != checks.shape[0] or any(type(index) is not int or index < 0 for index in indices):
            raise ValueError("row original indices must be nonnegative integers for every check")
        if self.pauli_order != "I,X,Y,Z":
            raise ValueError("Pauli code requires the persisted I,X,Y,Z ordering")
        source = self.source_artifact_identity
        if source is not None and (not isinstance(source, str) or not source):
            raise ValueError("source artifact identity must be a nonempty string when supplied")

        if (self.logical_x is None) != (self.logical_z is None):
            raise ValueError("logical basis needs both logical_x and logical_z or neither")
        logical_x: np.ndarray | None = None
        logical_z: np.ndarray | None = None
        rank_input = np.concatenate((to_symplectic(checks)[..., 0], to_symplectic(checks)[..., 1]), axis=1)
        logical_count = checks.shape[1] - gf2_rank(rank_input)
        if self.logical_x is not None and self.logical_z is not None:
            logical_x = _readonly(self.logical_x, name="logical_x", ndim=2)
            logical_z = _readonly(self.logical_z, name="logical_z", ndim=2)
            if logical_x.shape != (logical_count, checks.shape[1]) or logical_z.shape != logical_x.shape:
                raise ValueError("logical basis must contain the complete paired logical rows")
            if np.any(_commutation_matrix(checks, logical_x)) or np.any(_commutation_matrix(checks, logical_z)):
                raise ValueError("logical basis must commute with every stabilizer check")
            if np.any(_commutation_matrix(logical_x, logical_x)) or np.any(_commutation_matrix(logical_z, logical_z)):
                raise ValueError("same-type logical rows must commute")
            if not np.array_equal(_commutation_matrix(logical_x, logical_z), np.eye(logical_count, dtype=np.uint8)):
                raise ValueError("logical basis pairing or order is invalid")

        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "row_roles", roles)
        object.__setattr__(self, "row_original_indices", indices)
        object.__setattr__(self, "logical_x", logical_x)
        object.__setattr__(self, "logical_z", logical_z)

    @property
    def n(self) -> int:
        return int(self.checks.shape[1])

    @property
    def logical_basis_available(self) -> bool:
        return self.logical_x is not None

    def syndrome(self, error: object) -> np.ndarray:
        """Compute the declared full syndrome in this code's immutable row order."""
        return syndrome(self.checks, error)

    def semantic_bytes(self) -> bytes:
        """Canonical bytes for ordered checks, labels, logical availability, and source identity."""
        return _canonical_bytes({
            "version": 1,
            "pauli_order": self.pauli_order,
            "checks": self.checks.tolist(),
            "row_roles": list(self.row_roles),
            "row_original_indices": list(self.row_original_indices),
            "logical_basis": None if self.logical_x is None else {"x": self.logical_x.tolist(), "z": self.logical_z.tolist()},
            "source_artifact_identity": self.source_artifact_identity,
        })

    @property
    def semantic_sha256(self) -> str:
        return sha256(self.semantic_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class QuaternaryOriginalProblem:
    """Immutable original Pauli graph and observed full syndrome."""

    lineage_id: str
    code: PauliCode
    syndrome: np.ndarray

    def __post_init__(self) -> None:
        if not isinstance(self.lineage_id, str) or not self.lineage_id.startswith("original-"):
            raise ValueError("original problem needs an original-prefixed lineage ID")
        observed = _binary(self.syndrome, name="syndrome", length=self.code.checks.shape[0])
        object.__setattr__(self, "syndrome", observed)

    def semantic_bytes(self) -> bytes:
        return _canonical_bytes({"version": 1, "code": self.code.semantic_sha256, "syndrome": self.syndrome.tolist()})

    @property
    def semantic_sha256(self) -> str:
        return sha256(self.semantic_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class QuaternaryWorkingProblem:
    """An original problem or a derived graph with explicit certified witnesses."""

    lineage_id: str
    original: QuaternaryOriginalProblem
    parent_edge: LineageEdge
    code: PauliCode | None = None
    syndrome: np.ndarray | None = None
    transform_identity: str | None = None
    lift_identity: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.lineage_id, str) or not self.lineage_id.startswith("working-"):
            raise ValueError("working problem needs a working-prefixed lineage ID")
        expected_parent = LineageId("original", self.original.lineage_id)
        expected_child = LineageId("working", self.lineage_id)
        if self.parent_edge.parent != expected_parent or self.parent_edge.child != expected_child or self.parent_edge.relation not in {"identity", "transform"}:
            raise ValueError("working problem requires an identity or certified transform edge from its original")
        code = self.original.code if self.code is None else self.code
        observed = _binary(self.original.syndrome if self.syndrome is None else self.syndrome, name="working syndrome", length=code.checks.shape[0])
        if self.parent_edge.relation == "identity":
            if code.semantic_bytes() != self.original.code.semantic_bytes() or not np.array_equal(observed, self.original.syndrome):
                raise ValueError("identity working problem cannot change graph or syndrome")
            if self.transform_identity not in {None, "identity"} or self.lift_identity not in {None, "identity"}:
                raise ValueError("identity working problem cannot carry transform or lift witnesses")
            transform, lift = "identity", "identity"
        else:
            if not isinstance(self.transform_identity, str) or not self.transform_identity or not isinstance(self.lift_identity, str) or not self.lift_identity:
                raise ValueError("transformed working problem requires explicit transform and lift identities")
            transform, lift = self.transform_identity, self.lift_identity
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "syndrome", observed)
        object.__setattr__(self, "transform_identity", transform)
        object.__setattr__(self, "lift_identity", lift)


@dataclass(frozen=True, slots=True)
class PauliCandidate:
    """A frozen candidate in original Pauli coordinates from one working path."""

    lineage_id: str
    working: QuaternaryWorkingProblem
    candidate: np.ndarray
    local_order: int

    def __post_init__(self) -> None:
        if not isinstance(self.lineage_id, str) or not self.lineage_id.startswith("candidate-"):
            raise ValueError("Pauli candidate needs a candidate-prefixed lineage ID")
        if type(self.local_order) is not int or self.local_order < 0:
            raise ValueError("candidate local order must be nonnegative")
        candidate = _readonly(self.candidate, name="candidate", ndim=1)
        if candidate.shape != (self.working.original.code.n,):
            raise ValueError("candidate must be expressed in original Pauli coordinates")
        object.__setattr__(self, "candidate", candidate)


def compile_css_artifact(code: CssCode, *, source_artifact_identity: str | None = None) -> PauliCode:
    """Losslessly compile validated CSS rows as X checks followed by Z checks.

    This fixes the shared convention ``[s_X, s_Z] = [H_x z, H_z x]`` by using
    X labels for the stored ``H_x`` rows and Z labels for the stored ``H_z`` rows.
    """
    validated = code.validate()
    identity = source_artifact_identity or f"css_semantic_sha256:{css_semantic_sha256(validated)}"
    if not isinstance(identity, str) or not identity:
        raise ValueError("source artifact identity must be a nonempty string")
    x_checks = np.where(validated.hx == 1, Pauli.X, Pauli.I).astype(np.uint8)
    z_checks = np.where(validated.hz == 1, Pauli.Z, Pauli.I).astype(np.uint8)
    checks = np.vstack((x_checks, z_checks))
    logical_x = None if validated.lx is None else np.where(validated.lx == 1, Pauli.X, Pauli.I).astype(np.uint8)
    logical_z = None if validated.lz is None else np.where(validated.lz == 1, Pauli.Z, Pauli.I).astype(np.uint8)
    return PauliCode(
        checks=checks,
        row_roles=("x",) * validated.hx.shape[0] + ("z",) * validated.hz.shape[0],
        row_original_indices=tuple(range(validated.hx.shape[0])) + tuple(range(validated.hz.shape[0])),
        logical_x=logical_x,
        logical_z=logical_z,
        source_artifact_identity=identity,
    )


def build_qbpgd_a5_css_artifact() -> tuple[CssCode, dict[str, object]]:
    """Rebuild the A5 generalized-bicycle code from its published polynomials.

    The source reports the distance interval; this constructor only certifies
    the binary matrix algebra and the resulting ``[[180, 10]]`` dimensions.
    """
    l = 90
    a_exponents = (0, 28, 80, 89)
    b_exponents = (0, 2, 21, 25)
    identity = np.eye(l, dtype=np.uint8)

    def circulant(exponents: tuple[int, ...]) -> np.ndarray:
        result = np.zeros((l, l), dtype=np.uint8)
        for exponent in exponents:
            result ^= np.roll(identity, exponent, axis=1)
        return result

    a, b = circulant(a_exponents), circulant(b_exponents)
    hx = np.hstack((a, b))
    hz = np.hstack((b.T, a.T))
    lx, lz = derive_css_logicals(hx, hz)
    css = CssCode(hx, hz, lx, lz).validate()
    hx_rank, hz_rank = gf2_rank(css.hx), gf2_rank(css.hz)
    receipt: dict[str, object] = {
        "construction": {
            "l": l,
            "a_exponents": list(a_exponents),
            "b_exponents": list(b_exponents),
            "circulant_convention": "row_i_column_(i+exponent)_mod_l",
        },
        "checks": {
            "hx_rank": hx_rank,
            "hz_rank": hz_rank,
            "commutes": not bool(np.any((css.hx.astype(np.int64) @ css.hz.astype(np.int64).T) % 2)),
            "claimed_parameters": {"n": css.n, "k": css.k},
        },
        "distance": {
            "status": "source_reported_bounds",
            "source_reported": "15<=d<=18",
            "independently_verified": False,
        },
        "artifact": {
            "semantic_sha256": css_semantic_sha256(css),
            "matrix_sha256": {
                "hx": sha256(css.hx.tobytes()).hexdigest(),
                "hz": sha256(css.hz.tobytes()).hexdigest(),
            },
        },
    }
    return css, receipt


def construct_qbpgd_a5_css() -> tuple[PauliCode, dict[str, object]]:
    """Compile the checked A5 CSS artifact for the quaternary execution path."""
    css, receipt = build_qbpgd_a5_css_artifact()
    code = compile_css_artifact(css, source_artifact_identity="yao-2023-a5-polynomial-circulant-v1")
    receipt["artifact"]["pauli_semantic_sha256"] = code.semantic_sha256  # type: ignore[index]
    return code, receipt


__all__ = [
    "PauliCandidate",
    "PauliCode",
    "QuaternaryOriginalProblem",
    "QuaternaryWorkingProblem",
    "compile_css_artifact",
    "build_qbpgd_a5_css_artifact",
    "construct_qbpgd_a5_css",
]
