"""Typed evidence boundary for the exact isolated native aSCED reference."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..canonical.metrics import MetricFact


_SOURCE_COMMIT = "816772071486615dfc7d71d1e15df597edc58a26"
_SPEC_SHA256 = "55359962431c055cf971171f81d75997282beb29e8928a8d82e023fbb6c1f24e"
_CANONICAL = ("I", "X", "Y", "Z")
_NATIVE = ("I", "X", "Z", "Y")


@dataclass(frozen=True, slots=True)
class NativeAscedIdentity:
    """The native reference identity, deliberately distinct from canonical aSCED."""

    source_commit: str = _SOURCE_COMMIT
    source_spec_sha256: str = _SPEC_SHA256
    canonical_pauli_order: tuple[str, ...] = _CANONICAL
    native_pauli_order: tuple[str, ...] = _NATIVE

    @classmethod
    def approved(cls) -> "NativeAscedIdentity":
        return cls()

    def canonical_to_native(self, labels: tuple[str, ...]) -> tuple[str, ...]:
        if any(label not in self.canonical_pauli_order for label in labels):
            raise ValueError("canonical Pauli labels must be I, X, Y, or Z")
        lookup = dict(zip(self.canonical_pauli_order, self.native_pauli_order, strict=True))
        return tuple(lookup[label] for label in labels)

    def native_to_canonical(self, labels: tuple[str, ...]) -> tuple[str, ...]:
        if any(label not in self.native_pauli_order for label in labels):
            raise ValueError("native Pauli labels must be I, X, Z, or Y")
        lookup = dict(zip(self.native_pauli_order, self.canonical_pauli_order, strict=True))
        return tuple(lookup[label] for label in labels)


@dataclass(frozen=True, slots=True)
class NativeAscedResult:
    """Observed aggregate facts and source-qualified native missingness."""

    identity: NativeAscedIdentity
    trials: int
    logical_errors: int
    logical_error_rate: float
    metric_facts: tuple[MetricFact, ...]
    assessment: str

    def __post_init__(self) -> None:
        if self.trials <= 0 or self.logical_errors < 0 or self.logical_errors > self.trials:
            raise ValueError("native aggregate counters must be bounded by the actual denominator")
        if self.assessment != "not_assessed":
            raise ValueError("bounded native aggregate evidence remains not_assessed")
        facts = {fact.metric: fact for fact in self.metric_facts}
        if facts.get("native_trials", None) is None or facts["native_trials"].value != self.trials:
            raise ValueError("native trials must remain an observed aggregate fact")
        if facts.get("native_logical_errors", None) is None or facts["native_logical_errors"].value != self.logical_errors:
            raise ValueError("native logical errors must remain an observed aggregate fact")
        for metric in ("native_random_seed", "native_shot_identity", "native_injected_error", "native_per_path_counters", "native_edge_updates", "native_control_flow_events"):
            if metric not in facts or facts[metric].missingness.value != "unavailable":
                raise ValueError(f"{metric} must remain explicitly unavailable")

    def metric(self, name: str) -> MetricFact:
        for fact in self.metric_facts:
            if fact.metric == name:
                return fact
        raise KeyError(name)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_native_asced_receipt(receipt_path: Path, *, spec_path: Path) -> dict[str, object]:
    """Independently validate receipt identity and native aggregate completeness."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "phase10-asced-run-receipt-v1" or receipt.get("terminal") != "native_success":
        raise ValueError("receipt must be a successful native aSCED terminal")
    if _sha256(spec_path) != _SPEC_SHA256 or receipt.get("source_spec_sha256") != _SPEC_SHA256:
        raise ValueError("receipt does not bind the approved source specification")
    identity = receipt.get("native_identity")
    aggregate = receipt.get("aggregate")
    if not isinstance(identity, dict) or identity.get("commit") != _SOURCE_COMMIT:
        raise ValueError("receipt source commit differs from the approved native identity")
    if not isinstance(aggregate, dict) or aggregate.get("native_pauli_order") != list(_NATIVE):
        raise ValueError("receipt does not preserve native I/X/Z/Y order")
    if not isinstance(aggregate.get("trials"), int) or aggregate["trials"] <= 0:
        raise ValueError("receipt lacks an actual native trial denominator")
    return receipt


def run_native_asced_reference(receipt_path: Path, *, spec_path: Path) -> NativeAscedResult:
    """Load a completed native receipt without invoking or substituting canonical code."""
    receipt = verify_native_asced_receipt(receipt_path, spec_path=spec_path)
    aggregate = receipt["aggregate"]
    assert isinstance(aggregate, dict)
    facts = tuple(MetricFact.from_evidence(fact) for fact in receipt["metric_facts"])
    return NativeAscedResult(
        identity=NativeAscedIdentity.approved(),
        trials=int(aggregate["trials"]), logical_errors=int(aggregate["logical_errors"]),
        logical_error_rate=float(aggregate["logical_error_rate"]), metric_facts=facts,
        assessment=str(receipt["assessment"]),
    )


__all__ = ["NativeAscedIdentity", "NativeAscedResult", "run_native_asced_reference", "verify_native_asced_receipt"]
