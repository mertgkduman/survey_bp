"""Composable numerical resolution for BP messages and coefficients.

Resolution constrains values at declared message boundaries. The compiled
prototype still carries those values in float64 arrays; it does not claim
bit-packed storage or native low-precision arithmetic. Check reductions and
log-sum-exp use float64 intermediates before boundary rounding.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import math
from typing import Mapping

import numpy as np
from numba import njit


_FORMATS = {"float16": 0, "float32": 1, "float64": 2, "int8": 3, "int16": 4, "int32": 5}
_INTEGER_BITS = {"int8": 8, "int16": 16, "int32": 32}


@njit(cache=True)
def round_message(value: float, format_code: int, scale: int) -> float:
    """Round one finite value; fixed point saturates symmetrically.

    Float16 uses exact binary bin widths with ties-to-even and finite
    saturation. Float32 uses the platform IEEE conversion after finite clamp.
    """
    if not math.isfinite(value):
        raise ValueError("nonfinite BP message or coefficient")
    if format_code == 2:
        return value
    if format_code == 1:
        bound = 3.4028234663852886e38
        return float(np.float32(min(bound, max(-bound, value))))
    if format_code == 0:
        clipped = min(65504.0, max(-65504.0, value))
        if clipped == 0.0:
            return clipped
        absolute = abs(clipped)
        step = 2.0 ** -24 if absolute < 2.0 ** -14 else math.ldexp(1.0, math.frexp(absolute)[1] - 11)
        return math.copysign(np.rint(absolute / step) * step, clipped)
    bits = 8 if format_code == 3 else 16 if format_code == 4 else 32
    bound = (2 ** (bits - 1) - 1) / scale
    return min(bound, max(-bound, np.rint(value * scale) / scale))


@dataclass(frozen=True, slots=True)
class ResolutionPolicy:
    """Named message format and exact quantization boundaries.

    ``scalar_edges`` preserves unbounded BP4 three-LLR V2C state and beliefs;
    only projected commute LLRs and C2V messages use the requested format.
    ``all_messages`` also rounds V2C state. ``all_state`` rounds beliefs too.
    Priors remain input probabilities and are converted in float64.
    """

    format: str = "float64"
    scale: int | None = None
    scope: str = "all_messages"
    coefficients: str = "float64"
    version: str = "bp-resolution-v1"

    def __post_init__(self) -> None:
        if type(self.format) is not str or type(self.scope) is not str or type(self.coefficients) is not str:
            raise ValueError("resolution names must be strings")
        if self.format not in _FORMATS:
            raise ValueError(f"unsupported BP resolution: {self.format}")
        if self.format in _INTEGER_BITS:
            if type(self.scale) is not int or not 1 <= self.scale <= 2**31 - 1:
                raise ValueError("fixed-point resolution requires an int32-range positive scale")
        elif self.scale is not None:
            raise ValueError("floating resolution does not use a fixed-point scale")
        if self.scope not in {"scalar_edges", "all_messages", "all_state"}:
            raise ValueError("unknown BP resolution scope")
        if self.coefficients not in {"float64", "same"}:
            raise ValueError("coefficients must be float64 or same as message resolution")
        if self.version != "bp-resolution-v1":
            raise ValueError("unknown BP resolution version")

    @property
    def format_code(self) -> int:
        return _FORMATS[self.format]

    @property
    def fixed_scale(self) -> int:
        return 1 if self.scale is None else self.scale

    def quantize(self, value: float) -> float:
        return float(round_message(float(value), self.format_code, self.fixed_scale))

    def coefficient(self, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("BP coefficient must be finite")
        return self.quantize(value) if self.coefficients == "same" else float(value)

    def as_evidence(self) -> dict[str, str | int | None]:
        return asdict(self)

    @classmethod
    def from_spec(cls, value: Mapping[str, object]) -> "ResolutionPolicy":
        if not isinstance(value, Mapping) or set(value) != {"format", "scale", "scope", "coefficients", "version"}:
            raise ValueError("resolution spec requires its five declared fields")
        return cls(**dict(value))

    @property
    def semantic_identity(self) -> str:
        return sha256(json.dumps(self.as_evidence(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class BpFloodingPolicy:
    """Composable check, damping, and resolution policies for flooding BP.

    ``damping`` is the old-message weight. ``alpha`` and ``beta`` implement
    alpha*max(0, min(abs(incoming))-beta) for min-sum checks.
    """

    check_rule: str = "min_sum"
    resolution: ResolutionPolicy = field(default_factory=lambda: ResolutionPolicy("int8", 16, "scalar_edges"))
    damping: float = 0.0
    alpha: float = 1.0
    beta: float = 0.0
    hard_decision: str = "min_llr"
    zero_syndrome_shortcut: bool = True
    version: str = "bp-flooding-policy-v1"
    check_stabilization: str | None = None
    product_epsilon: float | None = None

    def __post_init__(self) -> None:
        if (type(self.check_rule) is not str or type(self.hard_decision) is not str
                or type(self.zero_syndrome_shortcut) is not bool
                or any(type(value) not in {int, float} for value in (self.damping, self.alpha, self.beta))):
            raise ValueError("BP flooding policy has invalid field types")
        if self.check_rule not in {"min_sum", "sum_product"}:
            raise ValueError("unknown BP check rule")
        if self.hard_decision not in {"min_llr", "strict_pauli", "map_pauli"}:
            raise ValueError("unknown BP4 hard-decision rule")
        if not isinstance(self.resolution, ResolutionPolicy):
            raise ValueError("resolution must be a ResolutionPolicy")
        if not (math.isfinite(self.damping) and 0 <= self.damping < 1
                and math.isfinite(self.alpha) and self.alpha > 0
                and math.isfinite(self.beta) and self.beta >= 0):
            raise ValueError("invalid BP damping, scale, or offset")
        if self.check_rule == "sum_product" and (self.alpha != 1 or self.beta != 0):
            raise ValueError("sum-product has no min-sum scale or offset")
        if self.version == "bp-flooding-policy-v1":
            if self.check_stabilization is not None or self.product_epsilon is not None or self.hard_decision == "map_pauli":
                raise ValueError("new numerical choices require bp-flooding-policy-v2")
        elif self.version == "bp-flooding-policy-v2":
            if (self.check_stabilization not in {"exact_unity", "epsilon_band"}
                    or type(self.product_epsilon) not in {int, float}
                    or not 0 < self.product_epsilon < .5 or not 1.0 - self.product_epsilon < 1.0):
                raise ValueError("v2 requires explicit check stabilization and representable epsilon")
        else:
            raise ValueError("unknown BP flooding policy version")

    @property
    def stabilization_args(self) -> tuple[bool, float]:
        return (self.check_stabilization != "exact_unity", 1e-10 if self.product_epsilon is None else self.product_epsilon)

    @property
    def decision_code(self) -> int:
        return {"min_llr": 0, "strict_pauli": 1, "map_pauli": 2}[self.hard_decision]

    @property
    def coefficients(self) -> tuple[float, float, float, float]:
        q = self.resolution.coefficient
        return q(self.damping), q(1.0 - self.damping), q(self.alpha), q(self.beta)

    def as_evidence(self) -> dict[str, object]:
        contract = {} if self.version == "bp-flooding-policy-v1" else {
            "binary_prior": "log1p(-p)-log(p)",
            "initial_candidate": "prior_decision; round_prior_only_for_all_state",
            "shortcut": "check_prior_candidate_when_enabled",
            "convergence": "final_candidate_validity",
            "reduction_order": "declared_edge_order; min_sum_two_minima",
            "coefficient_orientation": "old_weight=damping; fresh_weight=1-damping",
            "min_sum_degree_one_float_magnitude": 23.7189981105,
        }
        return {**self.as_spec(), **contract, "effective_coefficients": dict(zip(
            ("old_weight", "fresh_weight", "alpha", "beta"), self.coefficients, strict=True,
        ))}

    def as_spec(self) -> dict[str, object]:
        data = asdict(self)
        if self.version == "bp-flooding-policy-v1":
            data.pop("check_stabilization")
            data.pop("product_epsilon")
        return data

    @classmethod
    def from_spec(cls, value: Mapping[str, object]) -> "BpFloodingPolicy":
        required = {"check_rule", "resolution", "damping", "alpha", "beta",
                    "hard_decision", "zero_syndrome_shortcut", "version"}
        if isinstance(value, Mapping) and value.get("version") == "bp-flooding-policy-v2":
            required |= {"check_stabilization", "product_epsilon"}
        if not isinstance(value, Mapping) or set(value) != required:
            raise ValueError("BP flooding spec requires all declared policy fields")
        data = dict(value)
        data["resolution"] = ResolutionPolicy.from_spec(data["resolution"])
        return cls(**data)

    @property
    def semantic_identity(self) -> str:
        return sha256(json.dumps(self.as_evidence(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


DEFAULT_BP4_MIN_SUM = BpFloodingPolicy()


__all__ = ["BpFloodingPolicy", "DEFAULT_BP4_MIN_SUM", "ResolutionPolicy", "round_message"]
