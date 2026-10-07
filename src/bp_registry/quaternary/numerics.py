"""Finite numerical conventions for the scalar log-domain quaternary BP4 kernel.

The production state for a qubit is three identity-referenced LLRs in the
persisted ``I, X, Y, Z`` order.  Edges carry only one commute/anticommute LLR;
they never collapse the node posterior to a binary state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import numbers

import numpy as np

from .algebra import Pauli, anticommutes


class QuaternaryNumericalFailure(RuntimeError):
    """A nonfinite numerical result which must terminate a decoder attempt."""


@dataclass(frozen=True, slots=True)
class QuaternaryNumericalProfile:
    """All persisted numerical choices for one frozen scalar BP4 meaning."""

    profile_id: str = "quaternary-bp4-f64-v1"
    backend: str = "cpu-numpy"
    dtype: str = "float64"
    llr_orientation: str = "log(P(I)/P(W)) for W=X,Y,Z"
    pauli_order: str = "I,X,Y,Z"
    message_representation: str = "scalar_commute_over_anticommute_edge_llr"
    saturation: float = 25.0
    saturation_boundary: str = "symmetric_after_every_public_message_or_belief_primitive"
    reduction_order: str = "declared_edge_order_pairwise_left_fold"
    normalization: str = "four_state_logsumexp"
    candidate_tie_break: str = "I<X<Y<Z; I only when all nonidentity LLRs are strictly positive"
    zero_rule: str = "exact_zero_is_not_positive"
    smoothing_requirement: str = "decoder_priors_are_strictly_positive_or_explicitly_smoothed"
    nonfinite_policy: str = "reject_input_and_raise_terminal_numerical_failure"
    oracle_gate: str = "vector_and_exact_tree_fixtures_required_before_public_manifest"

    def as_evidence(self) -> dict[str, str | float]:
        """Return the complete immutable numerical contract for durable evidence."""
        return asdict(self)


QBP4_F64_V1 = QuaternaryNumericalProfile()


def _float64(value: object, *, name: str) -> np.ndarray:
    try:
        result = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be float64-compatible") from error
    if not np.all(np.isfinite(result)):
        raise QuaternaryNumericalFailure(f"nonfinite arithmetic at {name}")
    return result


def _edge_label(value: int | np.integer) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral) or int(value) not in (1, 2, 3):
        raise ValueError("edge label must be a nonidentity I,X,Y,Z Pauli label")
    return int(value)


def _syndrome(value: int | np.integer) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral) or int(value) not in (0, 1):
        raise ValueError("syndrome must be a binary integer")
    return int(value)


def finite_saturate(
    value: object,
    *,
    boundary: str,
    profile: QuaternaryNumericalProfile = QBP4_F64_V1,
) -> np.ndarray:
    """Reject nonfinite values and symmetrically clip a public numerical result."""
    if not isinstance(profile, QuaternaryNumericalProfile):
        raise ValueError("profile must be a QuaternaryNumericalProfile")
    return np.clip(_float64(value, name=boundary), -profile.saturation, profile.saturation)


def ordered_logsumexp(values: object, *, profile: QuaternaryNumericalProfile = QBP4_F64_V1) -> float:
    """Fold log masses with NumPy ``logaddexp`` in their declared order."""
    vector = _float64(values, name="ordered_logsumexp_input")
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError("ordered_logsumexp requires a nonempty one-dimensional vector")
    result = float(vector[0])
    for value in vector[1:]:
        result = float(np.logaddexp(result, float(value)))
    return float(finite_saturate(result, boundary="ordered_logsumexp_output", profile=profile))


def _boxplus_pair(left: float, right: float, *, profile: QuaternaryNumericalProfile) -> float:
    pair = finite_saturate((left, right), boundary="boxplus_pair_input", profile=profile)
    smaller, larger = sorted((abs(float(pair[0])), abs(float(pair[1]))))
    sign = -1.0 if float(pair[0]) * float(pair[1]) < 0.0 else 1.0
    try:
        correction = np.log1p(np.exp(-(smaller + larger))) - np.log1p(np.exp(-(larger - smaller)))
    except FloatingPointError as error:
        raise QuaternaryNumericalFailure("nonfinite arithmetic at boxplus_pair_intermediate") from error
    return float(finite_saturate(sign * (smaller + float(correction)), boundary="boxplus_pair_output", profile=profile))


def ordered_boxplus(values: object, *, profile: QuaternaryNumericalProfile = QBP4_F64_V1) -> float:
    """Apply the exact excluded-neighbor box-plus reduction in edge order.

    An empty reduction represents the degree-one check convention and therefore
    returns positive saturation before the separate syndrome sign is applied.
    """
    vector = finite_saturate(values, boundary="ordered_boxplus_input", profile=profile)
    if vector.ndim != 1:
        raise ValueError("ordered_boxplus requires a one-dimensional LLR vector")
    if vector.size == 0:
        return float(profile.saturation)
    result = float(vector[0])
    for value in vector[1:]:
        result = _boxplus_pair(result, float(value), profile=profile)
    return float(finite_saturate(result, boundary="ordered_boxplus_output", profile=profile))


def check_message(
    incoming: object,
    *,
    syndrome: int | np.integer,
    profile: QuaternaryNumericalProfile = QBP4_F64_V1,
) -> float:
    """Return the source-defined signed scalar C2V message for one excluded edge."""
    message = ordered_boxplus(incoming, profile=profile)
    signed = -message if _syndrome(syndrome) else message
    return float(finite_saturate(signed, boundary="check_message_output", profile=profile))


def llrs_to_probabilities(
    llrs: object,
    *,
    profile: QuaternaryNumericalProfile = QBP4_F64_V1,
) -> np.ndarray:
    """Normalize three identity-referenced LLRs to an ``I/X/Y/Z`` posterior."""
    belief = finite_saturate(llrs, boundary="llrs_to_probabilities_input", profile=profile)
    if belief.shape != (3,):
        raise ValueError("three identity-referenced X/Y/Z LLRs are required")
    log_weights = np.concatenate((np.asarray((0.0,), dtype=np.float64), -belief))
    log_normalizer = ordered_logsumexp(log_weights, profile=profile)
    # The normalizer is bounded only for public LLR output; use the stable raw
    # maximum shift here so four-state mass remains exactly normalized.
    shifted = log_weights - float(np.max(log_weights))
    probabilities = np.exp(shifted)
    probabilities /= float(probabilities.sum())
    if not np.all(np.isfinite(probabilities)):
        raise QuaternaryNumericalFailure("nonfinite arithmetic at llrs_to_probabilities_output")
    # Retain the named normalization operation in the public contract.
    del log_normalizer
    return np.array(probabilities, dtype=np.float64, copy=True)


def probabilities_to_llrs(
    probabilities: object,
    *,
    profile: QuaternaryNumericalProfile = QBP4_F64_V1,
) -> np.ndarray:
    """Encode a strictly positive normalized ``I/X/Y/Z`` prior as X/Y/Z LLRs."""
    values = _float64(probabilities, name="probabilities_to_llrs_input")
    if values.shape != (4,) or np.any(values <= 0.0) or not np.isclose(float(values.sum()), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("decoder probabilities must be a strictly positive normalized I/X/Y/Z vector")
    llrs = np.log(values[0]) - np.log(values[1:])
    return finite_saturate(llrs, boundary="probabilities_to_llrs_output", profile=profile)


def commutation_llr(
    llrs: object,
    edge_label: int | np.integer,
    *,
    profile: QuaternaryNumericalProfile = QBP4_F64_V1,
) -> float:
    """Quantize a four-state belief to log commute mass over anticommute mass."""
    label = _edge_label(edge_label)
    belief = finite_saturate(llrs, boundary="commutation_llr_input", profile=profile)
    if belief.shape != (3,):
        raise ValueError("commutation_llr requires three X/Y/Z LLRs")
    log_weights = np.concatenate((np.asarray((0.0,), dtype=np.float64), -belief))
    mask = np.asarray(anticommutes(np.full(4, label, dtype=np.uint8), _STATES), dtype=bool)
    commute = ordered_logsumexp(log_weights[~mask], profile=profile)
    anticommute = ordered_logsumexp(log_weights[mask], profile=profile)
    return float(finite_saturate(commute - anticommute, boundary="commutation_llr_output", profile=profile))


def pauli_hard_decision(
    llrs: object,
    *,
    profile: QuaternaryNumericalProfile = QBP4_F64_V1,
) -> Pauli:
    """Choose I only for strictly positive LLRs, then use the persisted I<X<Y<Z tie order."""
    belief = finite_saturate(llrs, boundary="pauli_hard_decision_input", profile=profile)
    if belief.shape != (3,):
        raise ValueError("pauli_hard_decision requires three X/Y/Z LLRs")
    if bool(np.all(belief > 0.0)):
        return Pauli.I
    return Pauli(1 + int(np.argmin(belief)))


_STATES = np.arange(4, dtype=np.uint8)


__all__ = [
    "QBP4_F64_V1",
    "QuaternaryNumericalFailure",
    "QuaternaryNumericalProfile",
    "check_message",
    "commutation_llr",
    "finite_saturate",
    "llrs_to_probabilities",
    "ordered_boxplus",
    "ordered_logsumexp",
    "pauli_hard_decision",
    "probabilities_to_llrs",
]
