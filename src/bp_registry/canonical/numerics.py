"""Named, finite numerical conventions for deterministic binary LLR SPA."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import numbers

import numpy as np


class NumericalFailure(RuntimeError):
    """A nonfinite numerical result that must become terminal evidence."""


@dataclass(frozen=True, slots=True)
class NumericalProfile:
    """All effective conventions for one durable canonical numerical meaning."""

    profile_id: str = "binary-spa-flooding-f64-v1"
    backend: str = "cpu-numpy"
    dtype: str = "float64"
    llr_encoding: str = "natural_log_odds"
    syndrome_convention: str = "one_negates_check_to_variable"
    saturation: float = 25.0
    prior_initialization: str = "log((1-p)/p)"
    normalization: str = "none"
    degree_one_rule: str = "positive_saturation_before_syndrome_sign"
    exact_zero_decision: int = 0
    tie_break: str = "ascending_canonical_id"

    def as_evidence(self) -> dict[str, str | float | int]:
        """Return the complete resolved profile for manifests and ledgers."""
        return asdict(self)


REFERENCE_CPU_F64 = NumericalProfile()
SATURATION = REFERENCE_CPU_F64.saturation


def _float64(value: np.ndarray | float, *, name: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be float64-compatible") from error
    return array


def finite_saturate(
    value: np.ndarray | float,
    *,
    boundary: str,
    profile: NumericalProfile = REFERENCE_CPU_F64,
) -> np.ndarray:
    """Reject nonfinite input and apply the profile's symmetric finite clip."""
    array = _float64(value, name=boundary)
    if not np.all(np.isfinite(array)):
        raise NumericalFailure(f"nonfinite arithmetic at {boundary}")
    return np.clip(array, -profile.saturation, profile.saturation)


def probability_to_llr(
    probability: np.ndarray | float,
    *,
    profile: NumericalProfile = REFERENCE_CPU_F64,
) -> np.ndarray:
    """Encode bit-one probabilities as natural-log odds, with explicit bounds."""
    values = _float64(probability, name="probability")
    if not np.all(np.isfinite(values)):
        raise NumericalFailure("nonfinite arithmetic at probability_to_llr_input")
    if np.any((values <= 0.0) | (values >= 1.0)):
        raise ValueError("probability must lie strictly between zero and one")
    with np.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
        try:
            llr = np.log1p(-values) - np.log(values)
        except FloatingPointError as error:
            raise NumericalFailure("nonfinite arithmetic at probability_to_llr_intermediate") from error
    return finite_saturate(llr, boundary="probability_to_llr_output", profile=profile)


def prior_llr(error_rate: float, *, profile: NumericalProfile = REFERENCE_CPU_F64) -> float:
    """Return the profile-clipped independent bit prior for a binary channel."""
    return float(probability_to_llr(error_rate, profile=profile))


def _syndrome_bit(value: int | np.integer) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral) or int(value) not in (0, 1):
        raise ValueError("syndrome must be a binary integer")
    return int(value)


def boxplus_pair(
    left: float,
    right: float,
    *,
    profile: NumericalProfile = REFERENCE_CPU_F64,
) -> float:
    """Stable two-input LLR box-plus, clipped at named calculation boundaries."""
    pair = finite_saturate(np.asarray([left, right]), boundary="boxplus_pair_input", profile=profile)
    magnitudes = np.abs(pair)
    smaller = float(np.min(magnitudes))
    larger = float(np.max(magnitudes))
    sign = -1.0 if float(pair[0]) * float(pair[1]) < 0.0 else 1.0
    with np.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
        try:
            correction = np.log1p(np.exp(-(smaller + larger))) - np.log1p(np.exp(-(larger - smaller)))
            result = sign * (smaller + float(correction))
        except FloatingPointError as error:
            raise NumericalFailure("nonfinite arithmetic at boxplus_pair_intermediate") from error
    return float(finite_saturate(result, boundary="boxplus_pair_output", profile=profile))


def boxplus(values: np.ndarray, *, profile: NumericalProfile = REFERENCE_CPU_F64) -> float:
    """Fold incoming LLRs in their supplied canonical order; empty means degree one."""
    vector = finite_saturate(values, boundary="boxplus_input", profile=profile)
    if vector.ndim != 1:
        raise ValueError("boxplus_input must be a one-dimensional LLR array")
    if vector.size == 0:
        return profile.saturation
    result = float(vector[0])
    for value in vector[1:]:
        result = boxplus_pair(result, float(value), profile=profile)
    return float(finite_saturate(result, boundary="boxplus_output", profile=profile))


def check_to_variable(
    incoming: np.ndarray,
    *,
    syndrome: int | np.integer = 0,
    profile: NumericalProfile = REFERENCE_CPU_F64,
) -> float:
    """Apply the declared degree-one and syndrome-sign convention to a check update."""
    message = boxplus(incoming, profile=profile)
    signed = -message if _syndrome_bit(syndrome) else message
    return float(finite_saturate(signed, boundary="check_to_variable_output", profile=profile))


def hard_decision(llrs: np.ndarray, *, profile: NumericalProfile = REFERENCE_CPU_F64) -> np.ndarray:
    """Decode negative LLRs as one; exact zero deterministically decodes as bit zero."""
    beliefs = finite_saturate(llrs, boundary="hard_decision_input", profile=profile)
    if beliefs.ndim != 1:
        raise ValueError("hard_decision_input must be a one-dimensional LLR array")
    return np.asarray(beliefs < 0.0, dtype=np.uint8)


def canonical_min_index(values: np.ndarray, canonical_ids: np.ndarray) -> int:
    """Choose the minimum score, resolving equal scores by ascending canonical ID."""
    scores = finite_saturate(values, boundary="canonical_tie_input")
    identifiers = np.asarray(canonical_ids)
    if scores.ndim != 1 or identifiers.ndim != 1 or scores.shape != identifiers.shape or scores.size == 0:
        raise ValueError("scores and canonical_ids must be nonempty matching one-dimensional arrays")
    if not np.issubdtype(identifiers.dtype, np.integer) or len(np.unique(identifiers)) != identifiers.size:
        raise ValueError("canonical_ids must be unique integers")
    return int(np.lexsort((identifiers, scores))[0])
