"""Truth-free projection of MBBP-LD controller evidence into public events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .mbbp import MbbpBasis, MbbpResult
from .problems import OriginalProblem


@dataclass(frozen=True)
class Phase6Projection:
    """Ordered public facts; evaluation remains outside this projection."""

    terminal: str
    events: tuple[tuple[str, Mapping[str, Any]], ...]
    candidate: tuple[int, ...] | None


_LEDGER_KIND = {
    "basis": "transform", "member": "attempt", "candidate_origin": "candidate",
    "duplicate_group": "branch", "selection": "selection", "original_check": "original_check",
    "work_leaf": "work",
}


def phase6_ledger_kind(kind: str) -> str:
    """Encode an explicit Phase 6 event type in the compatible ledger envelope."""
    return _LEDGER_KIND[kind]


def phase6_events(original: OriginalProblem, *, bases: tuple[MbbpBasis, ...], result: MbbpResult,
                  vote_tie_bit: int | None = None) -> Phase6Projection:
    """Preserve every member and candidate-list path without accepting truth.

    The controller has already checked original-syndrome validity before it
    admits an origin.  This projection deliberately records rejected members
    as well, so a ledger cannot turn a losing duplicate into extra frequency.
    """
    events: list[tuple[str, Mapping[str, Any]]] = [
        ("header", {"original_lineage_id": original.lineage_id, "syndrome": original.syndrome.tolist(),
                    "source_status": result.source_status}),
    ]
    augmented = {basis.member_id: basis.augment(original) for basis in bases}
    for basis in bases:
        events.append(("basis", augmented[basis.member_id].as_evidence()))
    for member in result.members:
        events.append(("member", member.as_evidence()))
    for origin in result.selection.origins:
        events.append(("candidate_origin", origin.as_evidence()))
    for group in result.selection.duplicate_groups:
        events.append(("duplicate_group", group.as_evidence()))
    candidate = result.selected_candidate
    terminal_status = result.terminal_status
    if vote_tie_bit is not None:
        raise ValueError("public Phase 6 vote projection is not yet executable")
    if candidate is not None:
        events.append(("selection", result.selection.as_evidence()))
    if candidate is not None:
        events.append(("original_check", {"candidate": list(candidate), "valid": True,
                                            "selected_origin_id": result.selected_origin_id.value if result.selected_origin_id else None}))
    for leaf_id, scope, work in result.work_leaves:
        events.append(("work_leaf", {"leaf_id": leaf_id, "scope": scope,
                                      "work_vector": work.as_evidence(structural_event_version=4)}))
    terminal: dict[str, Any] = {
        "terminal_status": terminal_status,
        "work_vector": result.work.as_evidence(structural_event_version=4),
    }
    if terminal_status == "no_member_converged_zero_return":
        terminal["source_zero_return"] = list(result.source_zero_return or ())
        terminal["selection"] = None
    else:
        terminal["selected_origin_id"] = None if result.selected_origin_id is None else result.selected_origin_id.value
        terminal["candidate"] = None if candidate is None else list(candidate)
    events.append(("termination", terminal))
    return Phase6Projection(terminal_status, tuple(events), candidate)
