"""Immutable, decoder-visible handoff to the released standalone LSD seam."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Literal, Protocol

import numpy as np
from bp_registry.compiled_contracts import immutable_snapshot

from ..problems import WorkingProblem
from ..budgets import WorkVector

ReliabilityConvention = Literal["natural_log_odds_log_p0_over_p1"]
LsdMethod = Literal["LSD_0", "LSD_E", "LSD_CS"]
CompositionSnapshotDisposition = Literal[
    "compatible", "incompatible", "composition_success", "unsupported_composition",
]


def _original_valid(working: WorkingProblem, candidate: np.ndarray) -> bool:
    observed = (working.original.hz.astype(np.int64) @ candidate.astype(np.int64)) % 2
    return bool(np.array_equal(observed.astype(np.uint8), working.original.syndrome))


def _original_channel_nll(candidate: np.ndarray, *, error_rate: float) -> float:
    if not math.isfinite(error_rate) or not 0.0 < error_rate < 0.5:
        raise ValueError("snapshot error_rate must lie in (0, 0.5)")
    ones = int(np.count_nonzero(candidate))
    zeros = int(candidate.size - ones)
    return float(-(ones * math.log(error_rate) + zeros * math.log1p(-error_rate)))


def _readonly_binary(value: np.ndarray, *, length: int, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != (length,) or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary vector with the original column length")
    copied = immutable_snapshot(array, dtype=np.uint8)
    return copied


def _readonly_llr(value: np.ndarray, *, length: int) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (length,) or not np.all(np.isfinite(array)):
        raise ValueError("posterior_llr must be finite and have the original column length")
    copied = immutable_snapshot(array)
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
    termination: str = "iteration_cap"
    transform_identity: str = "identity"
    work: WorkVector = field(default_factory=WorkVector.zero)

    def __post_init__(self) -> None:
        n = self.working.original.hz.shape[1]
        if (not self.attempt_lineage_id or self.original_residual_weight < 0 or self.declared_attempt_ordinal < 0
                or not self.termination or not self.transform_identity or not isinstance(self.work, WorkVector)):
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
class CompositionSnapshotResult:
    """Closed, truth-free fallback disposition for one completed composition."""

    disposition: CompositionSnapshotDisposition
    snapshots: tuple[FailedAttemptSnapshot, ...] = ()
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.disposition == "compatible":
            if not self.snapshots or self.reason is not None:
                raise ValueError("compatible composition requires snapshots and no reason")
        elif self.snapshots:
            raise ValueError("non-compatible composition cannot expose fallback snapshots")
        elif not self.reason:
            raise ValueError("non-compatible composition requires a stable reason")


class CompositionSnapshotAdapter(Protocol):
    """Typed bridge from one completed composition to fallback eligibility."""

    composition_kind: str


SUPPORTED_COMPOSITION_KINDS = frozenset({"flooding", "mbbp"})
UNSUPPORTED_COMPOSITION_REASONS = MappingProxyType({
    "relay": "unsupported_relay_missing_complete_terminal_snapshot_contract",
    "fair_beam": "unsupported_fair_beam_missing_complete_terminal_snapshot_contract",
    "fair_relay": "unsupported_fair_relay_missing_complete_terminal_snapshot_contract",
    "guided_decimation": "unsupported_guided_decimation_missing_complete_terminal_snapshot_contract",
    "impulse": "unsupported_impulse_missing_complete_terminal_snapshot_contract",
    "v5_intervention": "unsupported_v5_intervention_missing_complete_terminal_snapshot_contract",
    "v6_intervention": "unsupported_v6_intervention_missing_complete_terminal_snapshot_contract",
    "restart": "unsupported_restart_missing_complete_terminal_snapshot_contract",
    "transformed": "unsupported_transformed_composition_missing_complete_terminal_snapshot_contract",
})


def unsupported_composition(composition_kind: str) -> CompositionSnapshotResult:
    """Fail closed before public execution for controllers without complete snapshots."""
    reason = UNSUPPORTED_COMPOSITION_REASONS.get(
        composition_kind, "unsupported_composition_missing_complete_terminal_snapshot_contract",
    )
    return CompositionSnapshotResult("unsupported_composition", reason=reason)


def adapt_flooding_attempt(
    attempt: object, *, working: WorkingProblem, error_rate: float,
    attempt_lineage_id: str, declared_attempt_ordinal: int,
) -> CompositionSnapshotResult:
    """Freeze one completed flooding result before any evaluator or fallback call."""
    candidate = getattr(attempt, "terminal_candidate", None)
    posterior = getattr(attempt, "terminal_posterior", None)
    if candidate is None:
        return CompositionSnapshotResult("incompatible", reason="missing_terminal_candidate")
    try:
        frozen_candidate = _readonly_binary(candidate, length=working.original.hz.shape[1], name="candidate")
    except ValueError:
        return CompositionSnapshotResult("incompatible", reason="terminal_candidate_shape_or_binary_mismatch")
    if _original_valid(working, frozen_candidate):
        return CompositionSnapshotResult("composition_success", reason="original_valid_bp_candidate")
    if posterior is None:
        return CompositionSnapshotResult("incompatible", reason="missing_terminal_posterior")
    observed = np.asarray(posterior, dtype=np.float64)
    if observed.shape != (working.original.hz.shape[1],):
        return CompositionSnapshotResult("incompatible", reason="terminal_posterior_shape_mismatch")
    if not np.all(np.isfinite(observed)):
        return CompositionSnapshotResult("incompatible", reason="nonfinite_terminal_posterior")
    residual = (working.original.hz.astype(np.int64) @ frozen_candidate.astype(np.int64)) % 2
    termination = getattr(getattr(attempt, "termination", None), "kind", None) or "iteration_cap"
    snapshot = FailedAttemptSnapshot(
        attempt_lineage_id=attempt_lineage_id,
        working=working,
        candidate=frozen_candidate,
        posterior_llr=observed,
        original_residual_weight=int(np.count_nonzero(residual != working.original.syndrome)),
        original_channel_nll=_original_channel_nll(frozen_candidate, error_rate=error_rate),
        declared_attempt_ordinal=declared_attempt_ordinal,
        termination=str(termination),
        transform_identity=working.transform_identity,
    )
    return CompositionSnapshotResult("compatible", snapshots=(snapshot,))


def adapt_mbbp_result(
    result: object, *, working: WorkingProblem, error_rate: float,
) -> CompositionSnapshotResult:
    """Freeze every declared failed MBBP member after the ensemble is complete."""
    members = tuple(getattr(result, "members", ()))
    if not members:
        return CompositionSnapshotResult("incompatible", reason="missing_declared_mbbp_members")
    if any(getattr(member, "original_valid", None) is True for member in members):
        return CompositionSnapshotResult("composition_success", reason="original_valid_mbbp_member")
    snapshots: list[FailedAttemptSnapshot] = []
    for member in members:
        member_id = str(getattr(member, "member_id", "unknown"))
        candidate = getattr(member, "candidate", None)
        posterior = getattr(member, "terminal_posterior", None)
        if candidate is None:
            return CompositionSnapshotResult("incompatible", reason=f"mbbp_member_{member_id}_missing_terminal_candidate")
        if posterior is None:
            return CompositionSnapshotResult("incompatible", reason=f"mbbp_member_{member_id}_missing_terminal_posterior")
        try:
            frozen_candidate = _readonly_binary(candidate, length=working.original.hz.shape[1], name="candidate")
        except ValueError:
            return CompositionSnapshotResult("incompatible", reason=f"mbbp_member_{member_id}_terminal_candidate_shape_or_binary_mismatch")
        if _original_valid(working, frozen_candidate):
            return CompositionSnapshotResult("composition_success", reason="original_valid_mbbp_member")
        observed = np.asarray(posterior, dtype=np.float64)
        if observed.shape != (working.original.hz.shape[1],):
            return CompositionSnapshotResult("incompatible", reason=f"mbbp_member_{member_id}_terminal_posterior_shape_mismatch")
        if not np.all(np.isfinite(observed)):
            return CompositionSnapshotResult("incompatible", reason=f"mbbp_member_{member_id}_nonfinite_terminal_posterior")
        residual = (working.original.hz.astype(np.int64) @ frozen_candidate.astype(np.int64)) % 2
        snapshots.append(FailedAttemptSnapshot(
            attempt_lineage_id=str(getattr(getattr(member, "lineage_id", None), "value", "")),
            working=working,
            candidate=frozen_candidate,
            posterior_llr=observed,
            original_residual_weight=int(np.count_nonzero(residual != working.original.syndrome)),
            original_channel_nll=_original_channel_nll(frozen_candidate, error_rate=error_rate),
            declared_attempt_ordinal=int(getattr(member, "local_ordinal", -1)),
            termination=str(getattr(member, "status", "unknown")),
            transform_identity=f"mbbp_basis:{getattr(member, 'basis_identity', member_id)}",
            work=getattr(member, "work", WorkVector.zero()),
        ))
    ordered = tuple(sorted(snapshots, key=lambda snapshot: (snapshot.declared_attempt_ordinal, snapshot.attempt_lineage_id)))
    return CompositionSnapshotResult("compatible", snapshots=ordered)


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


class PostprocessingProcessor(Protocol):
    """One closed fallback method, selected before postprocessing begins."""

    def run(self, snapshot: FailedAttemptSnapshot) -> PostprocessingResult: ...


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

    def __init__(self, postprocessor: PostprocessingProcessor | None) -> None:
        self.postprocessor = postprocessor

    def execute(self, snapshots: tuple[FailedAttemptSnapshot, ...], *, bp_succeeded: bool) -> PostprocessingResult:
        if self.postprocessor is None:
            return PostprocessingResult("disabled", None, None, None, None, 0)
        if bp_succeeded:
            return PostprocessingResult("not_triggered_bp_success", None, None, None, None, 0)
        if not snapshots:
            return PostprocessingResult("not_triggered_no_failed_snapshot", None, None, None, None, 0)
        return self.postprocessor.run(min(snapshots, key=lambda snapshot: snapshot.rank))

    def execute_composition(self, composition: CompositionSnapshotResult) -> PostprocessingResult:
        """Consume only a closed completed-composition disposition."""
        return self.execute(
            composition.snapshots,
            bp_succeeded=composition.disposition == "composition_success",
        )
