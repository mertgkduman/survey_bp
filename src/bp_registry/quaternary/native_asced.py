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


def _required_successful_command(commands: object, *, contains: tuple[str, ...], label: str) -> None:
    if not isinstance(commands, list):
        raise ValueError(f"{label} receipt lacks command records")
    for record in commands:
        if not isinstance(record, dict) or record.get("returncode") != 0:
            continue
        command = record.get("command")
        if isinstance(command, list) and all(token in command for token in contains):
            return
    raise ValueError(f"{label} receipt lacks the required successful {' '.join(contains)} command")


def _build_receipt_for(run_receipt: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    name = run_receipt.name
    if "-run-receipt" not in name:
        raise ValueError("native run receipt needs an explicit build receipt path")
    return run_receipt.with_name(name.replace("-run-receipt", "-build-receipt"))


def verify_native_asced_receipt(
    receipt_path: Path, *, spec_path: Path, build_receipt_path: Path | None = None,
) -> dict[str, object]:
    """Verify the source, build, run, command, and aggregate evidence chain."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "phase10-asced-run-receipt-v1" or receipt.get("terminal") != "native_success":
        raise ValueError("receipt must be a successful native aSCED terminal")
    if _sha256(spec_path) != _SPEC_SHA256 or receipt.get("source_spec_sha256") != _SPEC_SHA256:
        raise ValueError("receipt does not bind the approved source specification")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    source = spec.get("source")
    proposal = spec.get("build_proposal")
    if not isinstance(source, dict) or not isinstance(proposal, dict):
        raise ValueError("approved source specification is incomplete")
    build_path = _build_receipt_for(receipt_path, build_receipt_path)
    if not build_path.is_file() or receipt.get("build_receipt_sha256") != _sha256(build_path):
        raise ValueError("native receipt does not bind the actual build receipt")
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if (build.get("schema") != "phase10-asced-build-receipt-v1" or build.get("terminal") != "build_success"
            or build.get("source_spec_sha256") != _SPEC_SHA256
            or build.get("execution_authority", "approved_native") != "approved_native"
            or build.get("disposable_root") != str(Path(spec["build_proposal"]["disposable_root"]).resolve())
            or build.get("source_digests_before") != source.get("source_digests")
            or build.get("source_digests_after") != source.get("source_digests")):
        raise ValueError("build receipt does not retain the approved source chain")
    _required_successful_command(build.get("commands"), contains=("git", "checkout"), label="build")
    _required_successful_command(build.get("commands"), contains=("--build",), label="build")
    _required_successful_command(build.get("commands"), contains=("--install",), label="build")
    if receipt.get("build_terminal") != "build_success":
        raise ValueError("native receipt does not retain a successful build terminal")
    if receipt.get("source_digests_before_run") != source.get("source_digests") or receipt.get("source_digests_after_run") != source.get("source_digests"):
        raise ValueError("native receipt source digests do not match the approved build")
    _required_successful_command(receipt.get("commands"), contains=(str(receipt.get("physical_error_rate")),), label="native run")
    identity = receipt.get("native_identity")
    aggregate = receipt.get("aggregate")
    if not isinstance(identity, dict) or identity.get("commit") != _SOURCE_COMMIT:
        raise ValueError("receipt source commit differs from the approved native identity")
    if not isinstance(aggregate, dict) or aggregate.get("native_pauli_order") != list(_NATIVE):
        raise ValueError("receipt does not preserve native I/X/Z/Y order")
    counters = ("trials", "logical_errors", "failure_I", "failure_II", "success_I", "success_II")
    if any(type(aggregate.get(counter)) is not int for counter in counters) or aggregate["trials"] <= 0:
        raise ValueError("receipt lacks an actual native trial denominator")
    if any(aggregate[counter] < 0 or aggregate[counter] > aggregate["trials"] for counter in counters[1:]):
        raise ValueError("native aggregate counters are outside the actual denominator")
    if aggregate["logical_errors"] != aggregate["failure_I"] + aggregate["failure_II"]:
        raise ValueError("native logical-error aggregate does not equal retained failure classes")
    rate = aggregate.get("logical_error_rate")
    if not isinstance(rate, (int, float)) or isinstance(rate, bool) or rate != aggregate["logical_errors"] / aggregate["trials"]:
        raise ValueError("native logical-error rate does not match its aggregate counters")
    bounds = proposal.get("native_bounds")
    if (not isinstance(bounds, dict) or receipt.get("code") != "GB46"
            or receipt.get("workers") != bounds.get("workers")
            or receipt.get("max_trials") != bounds.get("max_trials")
            or receipt.get("target_errors") != bounds.get("target_errors")
            or receipt.get("physical_error_rate") != 0.05):
        raise ValueError("native receipt command configuration differs from the approved probe")
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
