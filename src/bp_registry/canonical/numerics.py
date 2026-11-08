"""Named, finite numerical conventions for deterministic binary LLR SPA."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from bp_registry.check_numerics import stabilized_log_ratio
from bp_registry.profile_contracts import finite_real, validate_fixed_fields
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

    def __post_init__(self) -> None:
        overrides = ({"profile_id": "binary-min-sum-flooding-f64-v1", "normalization": "min_sum"}
                     if self.normalization == "min_sum" else {})
        validate_fixed_fields(self, NumericalProfile, parameters={"saturation"}, overrides=overrides)
        if not finite_real(self.saturation) or self.saturation <= 0:
            raise ValueError("saturation must be finite and positive")

    def as_evidence(self) -> dict[str, str | float | int | None]:
        """Return the complete resolved profile for manifests and ledgers."""
        return asdict(self)


REFERENCE_CPU_F64 = NumericalProfile()


@dataclass(frozen=True, slots=True)
class BinaryNumericalProfileV2(NumericalProfile):
    """SPA with unbounded beliefs and a product-bounded check message."""

    profile_id: str = "binary-spa-flooding-f64-v2"
    degree_one_rule: str = "product_clamp_epsilon_before_atanh"
    prior_initialization: str = "log((1-p)/p)_single_ratio"
    check_rule: str = "tanh_product"
    check_cap: float | None = None
    product_epsilon: float = 1e-10
    v2c_damping: float = 0.1
    saturation_boundary: str = "legacy_saturation_field_inactive; optional_final_check_cap_and_product_unity_safeguard"

    def __post_init__(self) -> None:
        if self.profile_id == "binary-spa-flooding-f64-v2-undamped":
            # Frozen identity used by the existing vanilla reproduction study.
            validate_fixed_fields(self, BinaryNumericalProfileV2,
                                  overrides={"profile_id": self.profile_id, "v2c_damping": 0.0})
        else:
            validate_fixed_fields(self, BinaryNumericalProfileV2,
                                  parameters={"check_cap", "product_epsilon", "v2c_damping"})
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        if self.check_rule != "tanh_product" or not (
            (self.check_cap is None or finite_real(self.check_cap) and self.check_cap > 0)
            and finite_real(self.product_epsilon) and 0 < self.product_epsilon < .5 and 1.0 - self.product_epsilon < 1.0
            and finite_real(self.v2c_damping) and 0 <= self.v2c_damping < 1
        ):
            raise ValueError("invalid binary SPA v2 numerical profile")


BINARY_SPA_F64_V2 = BinaryNumericalProfileV2()
@dataclass(frozen=True, slots=True)
class BinaryNumericalProfileV3(BinaryNumericalProfileV2):
    """Stable log odds and prior-based boundary decisions."""

    profile_id: str = "binary-spa-flooding-f64-v3"
    prior_initialization: str = "log1p(-p)-log(p)"
    initial_candidate: str = "prior_decision; no_initial_shortcut; convergence_reports_candidate_validity"
    check_stabilization: str = "exact_unity"

    def __post_init__(self) -> None:
        validate_fixed_fields(self, BinaryNumericalProfileV3,
                              parameters={"check_cap", "product_epsilon", "v2c_damping"})
        self._validate_parameters()


BINARY_SPA_F64_V3 = BinaryNumericalProfileV3()
DEFAULT_BINARY_SPA_F64 = BINARY_SPA_F64_V3
MIN_SUM_CPU_F64 = NumericalProfile(
    profile_id="binary-min-sum-flooding-f64-v1",
    normalization="min_sum",
)
# Compatibility constant for the frozen v1 profile; v2 has no global clip.
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
    profile: NumericalProfile = DEFAULT_BINARY_SPA_F64,
) -> np.ndarray:
    """Reject nonfinite input and apply the profile's symmetric finite clip."""
    array = _float64(value, name=boundary)
    if not np.all(np.isfinite(array)):
        raise NumericalFailure(f"nonfinite arithmetic at {boundary}")
    if isinstance(profile, BinaryNumericalProfileV2):
        return np.array(array, copy=True)
    return np.clip(array, -profile.saturation, profile.saturation)


def probability_to_llr(
    probability: np.ndarray | float,
    *,
    profile: NumericalProfile = DEFAULT_BINARY_SPA_F64,
) -> np.ndarray:
    """Encode bit-one probabilities as natural-log odds, with explicit bounds."""
    values = _float64(probability, name="probability")
    if not np.all(np.isfinite(values)):
        raise NumericalFailure("nonfinite arithmetic at probability_to_llr_input")
    if np.any((values <= 0.0) | (values >= 1.0)):
        raise ValueError("probability must lie strictly between zero and one")
    with np.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
        try:
            llr = (np.log((1.0 - values) / values) if isinstance(profile, BinaryNumericalProfileV2) and not isinstance(profile, BinaryNumericalProfileV3)
                   else np.log1p(-values) - np.log(values))
        except FloatingPointError as error:
            raise NumericalFailure("nonfinite arithmetic at probability_to_llr_intermediate") from error
    return finite_saturate(llr, boundary="probability_to_llr_output", profile=profile)


def prior_llr(error_rate: float, *, profile: NumericalProfile = DEFAULT_BINARY_SPA_F64) -> float:
    """Return the independent bit prior using the selected profile's boundary rule."""
    if isinstance(profile, BinaryNumericalProfileV2) and not isinstance(profile, BinaryNumericalProfileV3):
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 1.0:
            raise ValueError("probability must lie strictly between zero and one")
        return float(finite_saturate(math.log((1.0 - error_rate) / error_rate),
                                     boundary="binary_spa_v2_prior", profile=profile))
    return float(probability_to_llr(error_rate, profile=profile))


def _syndrome_bit(value: int | np.integer) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral) or int(value) not in (0, 1):
        raise ValueError("syndrome must be a binary integer")
    return int(value)


def boxplus_pair(
    left: float,
    right: float,
    *,
    profile: NumericalProfile = DEFAULT_BINARY_SPA_F64,
) -> float:
    """Stable two-input LLR box-plus under the selected numerical profile."""
    try:
        left_value, right_value = float(left), float(right)
    except (TypeError, ValueError) as error:
        raise ValueError("boxplus_pair_input must be float64-compatible") from error
    if not math.isfinite(left_value) or not math.isfinite(right_value):
        raise NumericalFailure("nonfinite arithmetic at boxplus_pair_input")
    limit = math.inf if isinstance(profile, BinaryNumericalProfileV2) else profile.saturation
    left_value = min(limit, max(-limit, left_value))
    right_value = min(limit, max(-limit, right_value))
    smaller = min(abs(left_value), abs(right_value))
    larger = max(abs(left_value), abs(right_value))
    sign = -1.0 if left_value * right_value < 0.0 else 1.0
    with np.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
        try:
            correction = np.log1p(np.exp(-(smaller + larger))) - np.log1p(np.exp(-(larger - smaller)))
            result = sign * (smaller + float(correction))
        except FloatingPointError as error:
            raise NumericalFailure("nonfinite arithmetic at boxplus_pair_intermediate") from error
    if not math.isfinite(result):
        raise NumericalFailure("nonfinite arithmetic at boxplus_pair_output")
    return min(limit, max(-limit, result))


def boxplus(values: np.ndarray, *, profile: NumericalProfile = DEFAULT_BINARY_SPA_F64) -> float:
    """Fold incoming LLRs in their supplied canonical order; empty means degree one."""
    vector = finite_saturate(values, boundary="boxplus_input", profile=profile)
    if vector.ndim != 1:
        raise ValueError("boxplus_input must be a one-dimensional LLR array")
    if vector.size == 0:
        if isinstance(profile, BinaryNumericalProfileV2):
            return math.log1p(1-profile.product_epsilon) - math.log(profile.product_epsilon)
        return profile.saturation
    result = float(vector[0])
    for value in vector[1:]:
        result = boxplus_pair(result, float(value), profile=profile)
    return float(finite_saturate(result, boundary="boxplus_output", profile=profile))


def check_to_variable(
    incoming: np.ndarray,
    *,
    syndrome: int | np.integer = 0,
    profile: NumericalProfile = DEFAULT_BINARY_SPA_F64,
) -> float:
    """Apply the declared degree-one and syndrome-sign convention to a check update."""
    if isinstance(profile, BinaryNumericalProfileV2):
        vector = finite_saturate(incoming, boundary="tanh_product_input", profile=profile)
        if vector.ndim != 1:
            raise ValueError("tanh_product requires a one-dimensional LLR vector")
        product = -1.0 if _syndrome_bit(syndrome) else 1.0
        for value in vector:
            scalar = float(value)
            product *= (1.0 if scalar > 40.0 else -1.0 if scalar < -40.0 else math.tanh(scalar / 2.0))
        result = stabilized_log_ratio(product, profile.product_epsilon)
        checked = float(finite_saturate(result, boundary="check_to_variable_output", profile=profile))
        return checked if profile.check_cap is None else float(np.clip(checked, -profile.check_cap, profile.check_cap))
    message = boxplus(incoming, profile=profile)
    signed = -message if _syndrome_bit(syndrome) else message
    return float(finite_saturate(signed, boundary="check_to_variable_output", profile=profile))


def hard_decision(llrs: np.ndarray, *, profile: NumericalProfile = DEFAULT_BINARY_SPA_F64) -> np.ndarray:
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
