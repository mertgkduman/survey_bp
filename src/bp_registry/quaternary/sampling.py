"""Strict physical joint-Pauli channels and decoder-only prior smoothing.

The physical channel is always a four-state categorical distribution in the
persisted ``I,X,Y,Z`` order.  It deliberately has no binary X/Z sampling
surface: a Y is one physical event that derives both symplectic bits later in
the shot boundary.  Numerical accommodation for a decoder is represented by a
separate object so exact physical zeros remain part of the experiment identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import json
import math
from types import MappingProxyType
from typing import Literal

import numpy as np
from bp_registry.compiled_contracts import immutable_snapshot

from .algebra import Pauli, to_symplectic
from .problems import QuaternaryOriginalProblem


PAULI_ORDER = "I,X,Y,Z"
ROW_SUM_TOLERANCE = 1e-12


def _readonly_f64(value: object) -> np.ndarray:
    result = immutable_snapshot(value, dtype=np.float64)
    return result


def _positive_n(n: int) -> int:
    if type(n) is not int or n <= 0:
        raise ValueError("n must be a positive integer")
    return n


def _finite_probability(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{name} must be a finite float64 probability in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be a finite float64 probability in [0, 1]")
    return result


def _rows(value: object, *, n: int) -> tuple[np.ndarray, Literal["explicit_shared", "explicit_per_qubit"], tuple[tuple[float, ...], ...]]:
    try:
        raw = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError("probability table must be float64-compatible") from error
    if raw.ndim == 1:
        if raw.shape != (4,):
            raise ValueError("shared probability table must have shape (4,)")
        kind: Literal["explicit_shared", "explicit_per_qubit"] = "explicit_shared"
        rows = np.repeat(raw[np.newaxis, :], n, axis=0)
        declaration = (tuple(float(item) for item in raw),)
    elif raw.ndim == 2:
        if raw.shape != (n, 4):
            raise ValueError("per-qubit probability table must have shape (n, 4)")
        kind = "explicit_per_qubit"
        rows = raw
        declaration = tuple(tuple(float(item) for item in row) for row in raw)
    else:
        raise ValueError("probability table must have shape (4,) or (n, 4)")
    if not np.all(np.isfinite(rows)):
        raise ValueError("probability table entries must be finite")
    if np.any((rows < 0.0) | (rows > 1.0)):
        raise ValueError("probability table entries must lie in [0, 1]")
    if np.any(np.abs(rows.sum(axis=1) - 1.0) > ROW_SUM_TOLERANCE):
        raise ValueError(f"probability table rows must sum to one within {ROW_SUM_TOLERANCE:g}")
    return _readonly_f64(rows), kind, declaration


def _identity(*, kind: str, raw_declaration: tuple[tuple[float, ...], ...], probabilities: np.ndarray, scalar_p: float | None) -> str:
    payload = {
        "version": 1,
        "kind": kind,
        "pauli_order": PAULI_ORDER,
        "row_sum_tolerance": ROW_SUM_TOLERANCE,
        "raw_declaration": raw_declaration,
        "resolved_probabilities": probabilities.tolist(),
        "scalar_physical_p": scalar_p,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return f"joint-pauli-channel-v1:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True, slots=True)
class JointPauliChannel:
    """A resolved immutable categorical physical channel in ``I,X,Y,Z`` order."""

    kind: Literal["depolarizing", "explicit_shared", "explicit_per_qubit"]
    raw_declaration: tuple[tuple[float, ...], ...]
    resolved_probabilities: np.ndarray
    scalar_physical_p: float | None
    identity: str
    pauli_order: str = PAULI_ORDER
    row_sum_tolerance: float = ROW_SUM_TOLERANCE
    _physical_nonidentity_rates: np.ndarray = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.pauli_order != PAULI_ORDER:
            raise ValueError("joint Pauli channels require I,X,Y,Z ordering")
        rows, _, _ = _rows(self.resolved_probabilities, n=int(np.asarray(self.resolved_probabilities).shape[0]))
        object.__setattr__(self, "resolved_probabilities", rows)
        rates = _readonly_f64(1.0 - rows[:, 0])
        object.__setattr__(self, "_physical_nonidentity_rates", rates)

    @classmethod
    def depolarizing(cls, p: object, *, n: int) -> "JointPauliChannel":
        """Resolve a named uniform depolarizing channel, including both endpoints."""
        count = _positive_n(n)
        rate = _finite_probability(p, name="p")
        row = np.asarray((1.0 - rate, rate / 3.0, rate / 3.0, rate / 3.0), dtype=np.float64)
        rows = _readonly_f64(np.repeat(row[np.newaxis, :], count, axis=0))
        declaration = (tuple(float(item) for item in row),)
        return cls(
            kind="depolarizing",
            raw_declaration=declaration,
            resolved_probabilities=rows,
            scalar_physical_p=rate,
            identity=_identity(kind="depolarizing", raw_declaration=declaration, probabilities=rows, scalar_p=rate),
        )

    @classmethod
    def explicit(cls, probabilities: object, *, n: int) -> "JointPauliChannel":
        """Resolve a shared or per-qubit user table without normalizing it."""
        count = _positive_n(n)
        rows, kind, declaration = _rows(probabilities, n=count)
        return cls(
            kind=kind,
            raw_declaration=declaration,
            resolved_probabilities=rows,
            scalar_physical_p=None,
            identity=_identity(kind=kind, raw_declaration=declaration, probabilities=rows, scalar_p=None),
        )

    @property
    def n(self) -> int:
        return int(self.resolved_probabilities.shape[0])

    @property
    def physical_nonidentity_rates(self) -> np.ndarray:
        """Per-qubit ``1-P(I)`` rates; no heterogeneous scalar is manufactured."""
        return self._physical_nonidentity_rates

    def x_rate(self, qubit: int) -> float:
        self._qubit(qubit)
        return float(self.resolved_probabilities[qubit, 1] + self.resolved_probabilities[qubit, 2])

    def z_rate(self, qubit: int) -> float:
        self._qubit(qubit)
        return float(self.resolved_probabilities[qubit, 2] + self.resolved_probabilities[qubit, 3])

    def xz_covariance(self, qubit: int) -> float:
        """Return covariance of symplectic X and Z bits for one joint row."""
        self._qubit(qubit)
        return float(self.resolved_probabilities[qubit, 2] - self.x_rate(qubit) * self.z_rate(qubit))

    def _qubit(self, qubit: int) -> None:
        if type(qubit) is not int or not 0 <= qubit < self.n:
            raise ValueError("qubit must identify a resolved channel row")

    def as_evidence(self) -> dict[str, object]:
        """Return complete immutable physical-channel evidence for ledgers/manifests."""
        return {
            "identity": self.identity,
            "kind": self.kind,
            "pauli_order": self.pauli_order,
            "row_sum_tolerance": self.row_sum_tolerance,
            "raw_declaration": [list(row) for row in self.raw_declaration],
            "resolved_probabilities": self.resolved_probabilities.tolist(),
            "physical_nonidentity_rates": self.physical_nonidentity_rates.tolist(),
            "scalar_physical_p": self.scalar_physical_p,
        }


@dataclass(frozen=True, slots=True)
class DecoderPriorSmoothing:
    """An explicitly identified decoder-only zero-prior accommodation rule."""

    floor: float
    identity: str = ""

    def __post_init__(self) -> None:
        floor = _finite_probability(self.floor, name="decoder smoothing floor")
        if floor == 0.0:
            raise ValueError("decoder smoothing floor must be positive")
        if floor > 0.25:
            raise ValueError("decoder smoothing floor must not exceed 0.25")
        object.__setattr__(self, "floor", floor)
        if not self.identity:
            payload = json.dumps({"version": 1, "kind": "replace_zero_prior", "floor": floor}, sort_keys=True, separators=(",", ":"))
            object.__setattr__(self, "identity", f"decoder-prior-smoothing-v1:{hashlib.sha256(payload.encode()).hexdigest()}")
        elif not isinstance(self.identity, str):
            raise ValueError("decoder smoothing identity must be a string")

    def apply(self, probabilities: object) -> np.ndarray:
        """Return decoder priors with zero entries raised, leaving physical data untouched."""
        rows = np.asarray(probabilities, dtype=np.float64)
        if rows.ndim != 2 or rows.shape[1] != 4 or not np.all(np.isfinite(rows)):
            raise ValueError("decoder smoothing requires finite (n, 4) probabilities")
        return _readonly_f64(np.where(rows == 0.0, self.floor, rows))

    def as_evidence(self) -> dict[str, object]:
        return {"identity": self.identity, "kind": "replace_zero_prior", "floor": self.floor}


def _rng(manifest_identity: str, shot_id: int) -> np.random.Generator:
    material = hashlib.sha256(
        f"bp-registry-joint-pauli-sample-v1\0{manifest_identity}\0{shot_id}".encode("utf-8")
    ).digest()
    words = np.frombuffer(material, dtype="<u4").astype(np.uint32, copy=False)
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(words)))


def _sample_identity(manifest_identity: str, channel_identity: str, shot_id: int) -> str:
    payload = f"joint-pauli-sample-v1\0{manifest_identity}\0{channel_identity}\0{shot_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_shot(shot_id: int, manifest_identity: str) -> None:
    if type(shot_id) is not int or shot_id < 0:
        raise ValueError("shot_id must be a nonnegative integer")
    if not isinstance(manifest_identity, str) or not manifest_identity:
        raise ValueError("manifest_identity must be a nonempty string")


def _categorical(row: np.ndarray, draw: float) -> Pauli:
    """Map one uniform draw using right-owned exact cumulative boundaries.

    ``searchsorted(..., side='right')`` gives I the interval beginning at zero
    and each later Pauli the exact preceding cumulative boundary: e.g. a draw
    exactly at ``P(I)`` belongs to X.  This is the recorded stable I<X<Y<Z
    convention.  A row sum allowed by the persisted tolerance may finish just
    below one, so only a final-tolerance tail is assigned to Z.
    """
    if not math.isfinite(draw) or draw < 0.0 or draw > 1.0:
        raise ValueError("categorical RNG draw must be finite in [0, 1]")
    # Decimal(str(...)) fixes the CDF convention at the persisted float text,
    # avoiding platform-dependent binary accumulation at user-declared ties
    # such as 0.1 + 0.2 = 0.3.
    threshold = Decimal(str(draw))
    cumulative = Decimal("0")
    for index, probability in enumerate(row):
        cumulative += Decimal(str(float(probability)))
        if threshold < cumulative:
            return Pauli(index)
    if threshold <= cumulative + Decimal(str(ROW_SUM_TOLERANCE)):
        return Pauli.Z
    raise RuntimeError("categorical draw exceeded probability row beyond tolerance")


@dataclass(frozen=True, slots=True)
class PauliHiddenTruth:
    """Immutable categorical physical truth, withheld from decoder-visible input."""

    paulis: np.ndarray
    x: np.ndarray
    z: np.ndarray

    def __post_init__(self) -> None:
        values = np.asarray(self.paulis)
        if values.ndim != 1 or not np.issubdtype(values.dtype, np.integer) or np.any((values < Pauli.I) | (values > Pauli.Z)):
            raise ValueError("hidden Pauli truth must be a one-dimensional I,X,Y,Z vector")
        labels = np.array(values, dtype=np.uint8, copy=True)
        symplectic = to_symplectic(labels)
        expected_x, expected_z = symplectic[:, 0], symplectic[:, 1]
        supplied_x = np.asarray(self.x)
        supplied_z = np.asarray(self.z)
        if supplied_x.shape != labels.shape or supplied_z.shape != labels.shape or not np.array_equal(supplied_x, expected_x) or not np.array_equal(supplied_z, expected_z):
            raise ValueError("hidden symplectic bits must derive from the categorical Pauli values")
        labels = immutable_snapshot(labels)
        frozen_x = np.array(expected_x, dtype=np.uint8, copy=True)
        frozen_z = np.array(expected_z, dtype=np.uint8, copy=True)
        frozen_x = immutable_snapshot(frozen_x)
        frozen_z = immutable_snapshot(frozen_z)
        object.__setattr__(self, "paulis", labels)
        object.__setattr__(self, "x", frozen_x)
        object.__setattr__(self, "z", frozen_z)


@dataclass(frozen=True, slots=True)
class PauliShotSample:
    """Replayable sample exposing only the full syndrome to decoding code."""

    shot_id: int
    sample_identity: str
    hidden: PauliHiddenTruth
    observation: QuaternaryOriginalProblem
    ledger: MappingProxyType
    decoder_smoothing_identity: str | None = None

    def __post_init__(self) -> None:
        if type(self.shot_id) is not int or self.shot_id < 0:
            raise ValueError("shot_id must be a nonnegative integer")
        if not isinstance(self.sample_identity, str) or len(self.sample_identity) != 64:
            raise ValueError("sample_identity must be a sha256 hex string")
        if self.hidden.paulis.shape != (self.observation.code.n,):
            raise ValueError("hidden truth and decoder observation must share qubit count")
        object.__setattr__(self, "ledger", MappingProxyType(dict(self.ledger)))


def sample_joint_pauli(
    problem: QuaternaryOriginalProblem,
    *,
    channel: JointPauliChannel,
    shot_id: int,
    manifest_identity: str,
    decoder_smoothing: DecoderPriorSmoothing | None = None,
) -> PauliShotSample:
    """Sample exactly one categorical Pauli per qubit and derive a full syndrome.

    The returned ``observation`` is a new immutable original problem for the
    sampled measurement.  It contains the declared code and syndrome only;
    hidden Pauli labels and symplectic bits stay in ``hidden`` for independent
    evaluation after decoding.
    """
    if not isinstance(problem, QuaternaryOriginalProblem):
        raise ValueError("problem must be an immutable quaternary original problem")
    if not isinstance(channel, JointPauliChannel):
        raise ValueError("channel must be a JointPauliChannel")
    if decoder_smoothing is not None and not isinstance(decoder_smoothing, DecoderPriorSmoothing):
        raise ValueError("decoder_smoothing must be a DecoderPriorSmoothing or None")
    _validate_shot(shot_id, manifest_identity)
    if channel.n != problem.code.n:
        raise ValueError("channel row count must match the original problem qubit count")

    generator = _rng(manifest_identity, shot_id)
    labels = np.asarray(
        [_categorical(channel.resolved_probabilities[index], float(generator.random())) for index in range(channel.n)],
        dtype=np.uint8,
    )
    bits = to_symplectic(labels)
    hidden = PauliHiddenTruth(labels, bits[:, 0], bits[:, 1])
    sample_identity = _sample_identity(manifest_identity, channel.identity, shot_id)
    observed_syndrome = problem.code.syndrome(hidden.paulis)
    observation = QuaternaryOriginalProblem(
        f"original-sample-{sample_identity[:16]}", problem.code, observed_syndrome
    )
    ledger = {
        "sample_identity": sample_identity,
        "manifest_identity": manifest_identity,
        "shot_id": shot_id,
        "channel_identity": channel.identity,
        "channel_kind": channel.kind,
        "pauli_order": PAULI_ORDER,
        "row_sum_tolerance": ROW_SUM_TOLERANCE,
        "resolved_physical_probabilities": channel.resolved_probabilities.tolist(),
        "physical_nonidentity_rates": channel.physical_nonidentity_rates.tolist(),
        "scalar_physical_p": channel.scalar_physical_p,
        "decoder_smoothing_identity": None if decoder_smoothing is None else decoder_smoothing.identity,
        "observation_syndrome": observed_syndrome.tolist(),
    }
    return PauliShotSample(
        shot_id=shot_id,
        sample_identity=sample_identity,
        hidden=hidden,
        observation=observation,
        ledger=ledger,
        decoder_smoothing_identity=None if decoder_smoothing is None else decoder_smoothing.identity,
    )


__all__ = [
    "DecoderPriorSmoothing",
    "JointPauliChannel",
    "PAULI_ORDER",
    "PauliHiddenTruth",
    "PauliShotSample",
    "ROW_SUM_TOLERANCE",
    "sample_joint_pauli",
]
