"""Independent CSS outcome classification against immutable observations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .css import CssCode, in_row_space


Outcome = Literal["invalid_syndrome", "exact", "stabilizer_equivalent", "logical_failure"]


@dataclass(frozen=True)
class Evaluation:
    outcome: Outcome
    logical_action_agrees: bool | None


def _vector(value: np.ndarray | None, name: str, n: int) -> np.ndarray:
    if value is None:
        return np.zeros(n, dtype=np.uint8)
    array = np.asarray(value)
    if array.shape != (n,) or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be a binary vector of length {n}")
    if np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be binary")
    return np.array(array, dtype=np.uint8, copy=True)


def evaluate_candidate(
    code: CssCode,
    *,
    true_error: np.ndarray | None = None,
    candidate: np.ndarray | None = None,
    true_x: np.ndarray | None = None,
    true_z: np.ndarray | None = None,
    candidate_x: np.ndarray | None = None,
    candidate_z: np.ndarray | None = None,
) -> Evaluation:
    """Classify candidate recovery using original checks and hidden truth only.

    The legacy ``true_error``/``candidate`` aliases express an X-only shot.
    The full arguments keep X and Z residuals separate for later CSS pilots.
    """
    if true_error is not None:
        if true_x is not None:
            raise ValueError("provide either true_error or true_x")
        true_x = true_error
    if candidate is not None:
        if candidate_x is not None:
            raise ValueError("provide either candidate or candidate_x")
        candidate_x = candidate
    validated = code.validate()
    original_x = _vector(true_x, "true X error", validated.n)
    original_z = _vector(true_z, "true Z error", validated.n)
    proposed_x = _vector(candidate_x, "candidate X error", validated.n)
    proposed_z = _vector(candidate_z, "candidate Z error", validated.n)
    expected_z_check = (validated.hz.astype(np.int64) @ original_x) % 2
    expected_x_check = (validated.hx.astype(np.int64) @ original_z) % 2
    if not np.array_equal((validated.hz.astype(np.int64) @ proposed_x) % 2, expected_z_check) or not np.array_equal(
        (validated.hx.astype(np.int64) @ proposed_z) % 2, expected_x_check
    ):
        return Evaluation("invalid_syndrome", None)
    residual_x, residual_z = original_x ^ proposed_x, original_z ^ proposed_z
    if not residual_x.any() and not residual_z.any():
        return Evaluation("exact", True)
    stabilizer_equivalent = in_row_space(validated.hx, residual_x) and in_row_space(
        validated.hz, residual_z
    )
    if validated.lx is None or validated.lz is None:
        return Evaluation(
            "stabilizer_equivalent" if stabilizer_equivalent else "logical_failure", None
        )
    logical_x_action = (residual_x.astype(np.int64) @ validated.lz.astype(np.int64).T) % 2
    logical_z_action = (residual_z.astype(np.int64) @ validated.lx.astype(np.int64).T) % 2
    logical_trivial = not bool(logical_x_action.any() or logical_z_action.any())
    agrees = stabilizer_equivalent == logical_trivial
    if not agrees:
        raise RuntimeError("logical action disagrees with stabilizer row-space classification")
    return Evaluation("stabilizer_equivalent" if stabilizer_equivalent else "logical_failure", agrees)
