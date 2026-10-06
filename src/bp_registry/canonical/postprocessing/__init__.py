"""Immutable, decoder-visible handoff to the released standalone LSD seam."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from ..problems import WorkingProblem

ReliabilityConvention = Literal["natural_log_odds_log_p0_over_p1"]
LsdMethod = Literal["LSD_0", "LSD_E", "LSD_CS"]


def _readonly_binary(value: np.ndarray, *, length: int, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != (length,) or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary vector with the original column length")
    copied = np.array(array, dtype=np.uint8, copy=True)
    copied.setflags(write=False)
    return copied


def _readonly_llr(value: np.ndarray, *, length: int) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (length,) or not np.all(np.isfinite(array)):
        raise ValueError("posterior_llr must be finite and have the original column length")
    copied = np.array(array, copy=True)
    copied.setflags(write=False)
    return copied


@dataclass(frozen=True)
class FailedAttemptSnapshot:
    """A completed BP attempt frozen before any optional postprocessing."""

    attempt_lineage_id: str
    working: WorkingProblem
    candidate: np.ndarray
    posterior_llr: np.ndarray
    original_residual_weight: int
    original_channel_nll: float
    declared_attempt_ordinal: int
    reliability_convention: ReliabilityConvention = "natural_log_odds_log_p0_over_p1"

    def __post_init__(self) -> None:
        n = self.working.original.hz.shape[1]
        if not self.attempt_lineage_id or self.original_residual_weight < 0 or self.declared_attempt_ordinal < 0:
            raise ValueError("failed attempt identity and decoder-visible rank fields are invalid")
        if not np.isfinite(self.original_channel_nll):
            raise ValueError("original_channel_nll must be finite")
        if self.reliability_convention != "natural_log_odds_log_p0_over_p1":
            raise ValueError("only canonical natural-log odds reliability is translatable")
        object.__setattr__(self, "candidate", _readonly_binary(self.candidate, length=n, name="candidate"))
        object.__setattr__(self, "posterior_llr", _readonly_llr(self.posterior_llr, length=n))

    @property
    def rank(self) -> tuple[int, float, int, str]:
        return (self.original_residual_weight, self.original_channel_nll,
                self.declared_attempt_ordinal, self.attempt_lineage_id)


@dataclass(frozen=True)
class PostprocessingHandoff:
    snapshot: FailedAttemptSnapshot
    method: LsdMethod
    order: int


@dataclass(frozen=True)
class PostprocessingResult:
    status: str
    bp_only_candidate: tuple[int, ...] | None
    candidate: tuple[int, ...] | None
    original_valid: bool | None
    selected_attempt_lineage_id: str | None
    native_calls: int
    stable_tie_order: tuple[int, ...] = ()
    error: str | None = None


def _load_lsd_decoder():
    from ldpc.lsd_decoder import LsdDecoder
    return LsdDecoder


class LsdPostprocessor:
    """Closed adapter for the released :class:`ldpc.lsd_decoder.LsdDecoder`."""

    def __init__(self, *, method: LsdMethod, order: int) -> None:
        if method not in {"LSD_0", "LSD_E", "LSD_CS"} or type(order) is not int or order < 0:
            raise ValueError("LSD method/order is not an admitted closed binding")
        self.method, self.order = method, order

    def run(self, snapshot: FailedAttemptSnapshot) -> PostprocessingResult:
        weights = np.abs(snapshot.posterior_llr)
        tie_order = tuple(sorted(range(weights.size), key=lambda column: (float(weights[column]), column)))
        try:
            decoder = _load_lsd_decoder()(snapshot.working.original.hz, bits_per_step=1,
                                          lsd_method=self.method, lsd_order=self.order)
            raw = np.asarray(decoder.decode(snapshot.working.original.syndrome, weights))
        except Exception as error:
            return PostprocessingResult("native_failure", tuple(snapshot.candidate.tolist()), None, None,
                                        snapshot.attempt_lineage_id, 1, tie_order, type(error).__name__)
        try:
            candidate = _readonly_binary(raw, length=weights.size, name="LSD candidate")
        except ValueError:
            return PostprocessingResult("invalid_candidate", tuple(snapshot.candidate.tolist()), None, False,
                                        snapshot.attempt_lineage_id, 1, tie_order)
        valid = bool(np.array_equal((snapshot.working.original.hz @ candidate) % 2,
                                    snapshot.working.original.syndrome))
        return PostprocessingResult("success" if valid else "invalid_candidate",
                                    tuple(snapshot.candidate.tolist()), tuple(candidate.tolist()), valid,
                                    snapshot.attempt_lineage_id, 1, tie_order)


class PostprocessingController:
    """Invoke exactly one optional processor after the complete BP composition fails."""

    def __init__(self, postprocessor: LsdPostprocessor | None) -> None:
        self.postprocessor = postprocessor

    def execute(self, snapshots: tuple[FailedAttemptSnapshot, ...], *, bp_succeeded: bool) -> PostprocessingResult:
        if self.postprocessor is None:
            return PostprocessingResult("disabled", None, None, None, None, 0)
        if bp_succeeded:
            return PostprocessingResult("not_triggered_bp_success", None, None, None, None, 0)
        if not snapshots:
            return PostprocessingResult("not_triggered_no_failed_snapshot", None, None, None, None, 0)
        return self.postprocessor.run(min(snapshots, key=lambda snapshot: snapshot.rank))
