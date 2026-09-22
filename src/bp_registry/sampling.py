"""Deterministic CSS samples with decoder-visible observations kept separate."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from types import MappingProxyType
from typing import Mapping

import numpy as np

from .css import CssCode


@dataclass(frozen=True)
class DecoderObservation:
    """A syndrome identified by the type of check that measured it."""

    check_type: str
    syndrome: np.ndarray


@dataclass(frozen=True)
class HiddenTruth:
    """Physical errors retained for independent evaluation, never native decoding."""

    x: np.ndarray
    z: np.ndarray


@dataclass(frozen=True)
class ShotSample:
    """A replayable sample whose adapter input is explicitly ``observation``."""

    shot_id: int
    sample_identity: str
    hidden: HiddenTruth
    observation: DecoderObservation
    observations: Mapping[str, DecoderObservation]

    @property
    def hidden_x(self) -> np.ndarray:
        return self.hidden.x

    @property
    def hidden_z(self) -> np.ndarray:
        return self.hidden.z


def _rate(value: float, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite rate in [0, 1]")
    rate = float(value)
    if not math.isfinite(rate) or not 0 <= rate <= 1:
        raise ValueError(f"{name} must be a finite rate in [0, 1]")
    return rate


def _identity(manifest_identity: str | None, seed: int) -> str:
    if manifest_identity is not None:
        if not isinstance(manifest_identity, str) or not manifest_identity:
            raise ValueError("manifest_identity must be a nonempty string")
        return manifest_identity
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    return f"legacy-seed:{seed}"


def _rng(identity: str, shot_id: int) -> np.random.Generator:
    material = hashlib.sha256(f"bp-registry-sample-v1\0{identity}\0{shot_id}".encode()).digest()
    words = np.frombuffer(material, dtype="<u4").astype(np.uint32, copy=False)
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(words)))


def sample_shot(
    code: CssCode,
    *,
    shot_id: int,
    seed: int,
    x_error_rate: float,
    z_error_rate: float = 0.0,
    manifest_identity: str | None = None,
) -> ShotSample:
    """Generate a deterministic separate-X/Z code-capacity sample.

    ``manifest_identity`` is the preferred reproducibility anchor.  It is
    combined with ``shot_id`` for physical randomness; decoder-local random
    state is neither consumed nor represented here.
    """
    if type(shot_id) is not int or shot_id < 0:
        raise ValueError("shot_id must be a nonnegative integer")
    x_rate, z_rate = _rate(x_error_rate, "x_error_rate"), _rate(z_error_rate, "z_error_rate")
    anchor = _identity(manifest_identity, seed)
    validated = code.validate()
    generator = _rng(anchor, shot_id)
    hidden_x = np.zeros(validated.n, dtype=np.uint8) if x_rate == 0 else (
        np.ones(validated.n, dtype=np.uint8) if x_rate == 1 else
        np.asarray(generator.random(validated.n) < x_rate, dtype=np.uint8)
    )
    hidden_z = np.zeros(validated.n, dtype=np.uint8) if z_rate == 0 else (
        np.ones(validated.n, dtype=np.uint8) if z_rate == 1 else
        np.asarray(generator.random(validated.n) < z_rate, dtype=np.uint8)
    )
    z_check = DecoderObservation(
        "Z", np.asarray((validated.hz.astype(np.int64) @ hidden_x) % 2, dtype=np.uint8)
    )
    x_check = DecoderObservation(
        "X", np.asarray((validated.hx.astype(np.int64) @ hidden_z) % 2, dtype=np.uint8)
    )
    sample_identity = hashlib.sha256(
        f"bp-registry-sample-v1\0{anchor}\0{shot_id}".encode()
    ).hexdigest()
    observations = MappingProxyType({"Z": z_check, "X": x_check})
    return ShotSample(
        shot_id=shot_id, sample_identity=sample_identity,
        hidden=HiddenTruth(hidden_x, hidden_z), observation=z_check, observations=observations,
    )
