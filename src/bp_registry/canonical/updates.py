"""Closed check-update rules for the canonical binary CSS kernel."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

import numpy as np

from .numerics import MIN_SUM_CPU_F64, NumericalProfile, finite_saturate


class CheckUpdateRule(Protocol):
    """A decoder-visible, deterministic check-to-variable rule."""

    def check_to_variable(self, incoming: np.ndarray, *, syndrome: int) -> float: ...

    def evidence(self) -> "UpdateRuleEvidence": ...


@dataclass(frozen=True, slots=True)
class UpdateRuleEvidence:
    """Named procedure and numerical identity retained beside terminal evidence."""

    kind: str
    numerical_profile: str
    procedure: str

    def as_evidence(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MinSumUpdate:
    """Float64 binary min-sum with inherited degree-one and sign conventions."""

    profile: NumericalProfile = MIN_SUM_CPU_F64

    def check_to_variable(self, incoming: np.ndarray, *, syndrome: int) -> float:
        values = finite_saturate(incoming, boundary="min_sum_input", profile=self.profile)
        if values.ndim != 1:
            raise ValueError("min_sum_input must be a one-dimensional LLR array")
        if type(syndrome) not in (int, np.int64, np.int32) or int(syndrome) not in (0, 1):
            raise ValueError("syndrome must be a binary integer")
        # An empty extrinsic set is a degree-one check.  Zero has positive sign
        # for the product, preserving the inherited deterministic convention.
        magnitude = self.profile.saturation if values.size == 0 else float(np.min(np.abs(values)))
        negative_count = int(np.count_nonzero(values < 0.0))
        sign = -1.0 if (negative_count + int(syndrome)) % 2 else 1.0
        return float(finite_saturate(sign * magnitude, boundary="min_sum_output", profile=self.profile))

    def evidence(self) -> UpdateRuleEvidence:
        return UpdateRuleEvidence(
            kind="min_sum",
            numerical_profile=self.profile.profile_id,
            procedure="signed extrinsic minimum with zero-positive sign product and post-magnitude saturation",
        )
