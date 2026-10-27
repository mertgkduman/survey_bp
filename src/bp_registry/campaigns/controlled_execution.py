"""Local, receipt-first controlled CSS arm execution.

Each continuation consumes a sealed shared input.  A later invocation can
therefore resume the missing arm without repeating initial BP.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import stat
import tempfile
from time import perf_counter_ns
from types import SimpleNamespace
from typing import Any, Callable, Literal

import numpy as np

from ..artifacts import load_artifact
from ..canonical.fair_legs import FairLegConfig, FairLegController
from ..css import CssCode
from ..evaluator import evaluate_candidate
from ..manifests import StrictModel
from .contracts import (
    BinaryComponentTerminalV1, MaterializedPhysicalSampleV1, PauliMatchedArmV1,
    OutcomeMatrixV1, OutcomeTreatmentV1, PauliMatchedPairV1, canonical_json_bytes,
)
from .controlled import ControlledArmReceiptV1, ControlledComponentEvidenceV1, SharedInitialBPReceiptV1
from .execution import _shot_from_materialized, materialize_campaign_sample
from .planning import CampaignWorkPlan, UnitKey


def _publish_exact(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise ValueError("controlled evidence path conflicts with immutable bytes")
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".controlled-", delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        stage = Path(handle.name)
    try:
        os.replace(stage, path)
    finally:
        stage.unlink(missing_ok=True)


def _json_line(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _component(
    *, component_id: str, role: str, source_status: str, converged: bool | None,
    iterations: int | None, configured: dict[str, int], work: dict[str, int],
    runtime_ns: int, events: int, evidence_bytes: int, storage_bytes: int,
    provenance_sha256: str, shared_input_receipt_sha256: str | None = None,
) -> ControlledComponentEvidenceV1:
    return ControlledComponentEvidenceV1.model_validate({
        "schema": "controlled_component_evidence_v1", "component_id": component_id,
        "role": role, "source_status": source_status,
        "convergence_status": ({"status": "observed", "value": converged} if converged is not None else
                               {"status": "not_applicable", "reason": "independent validation is not BP"}),
        "iterations": ({"status": "observed", "value": iterations} if iterations is not None else
                       {"status": "not_applicable", "reason": "independent validation is not BP"}),
        "configured_limits": configured, "actual_work": work,
        "runtime_ns": {"status": "observed", "value": runtime_ns},
        "peak_rss_bytes": {"status": "unavailable", "reason": "shared local process does not expose component RSS"},
        "events": {"status": "observed", "value": events},
        "evidence_bytes": {"status": "observed", "value": evidence_bytes},
        "storage_bytes": {"status": "observed", "value": storage_bytes},
        "interruption": {"status": "not_applicable", "reason": "component completed"},
        "provenance_sha256": provenance_sha256,
        "shared_input_receipt_sha256": shared_input_receipt_sha256,
    })


def _validated_terminal(code: Any, hidden_x: np.ndarray, candidate: np.ndarray | None) -> str:
    if candidate is None:
        return "nonconvergence"
    observed = evaluate_candidate(
        code, true_x=hidden_x, true_z=np.zeros_like(hidden_x),
        candidate_x=candidate, candidate_z=np.zeros_like(hidden_x),
    ).outcome
    return "wrong_logical_action" if observed == "logical_failure" else observed


def _receipt_with_bytes(
    *, payload: dict[str, Any], component: ControlledComponentEvidenceV1 | None,
) -> ControlledArmReceiptV1:
    """Account the receipt's own bytes once in its producing component."""
    if component is None:
        current = payload["validation_component"]
        for _ in range(8):
            candidate = ControlledArmReceiptV1.model_validate({**payload, "validation_component": current})
            amount = len(candidate.primitive_bytes()) + 1
            updated = current.model_copy(update={
                "storage_bytes": current.storage_bytes.model_copy(update={
                    "value": current.evidence_bytes.value + amount,
                }),
            })
            if updated.storage_bytes.value == current.storage_bytes.value:
                return candidate
            current = updated
        raise ValueError("baseline receipt byte accounting did not stabilize")
    current = component
    for _ in range(8):
        candidate = ControlledArmReceiptV1.model_validate({**payload, "component": current})
        amount = len(candidate.primitive_bytes()) + 1
        updated = current.model_copy(update={
            "storage_bytes": current.storage_bytes.model_copy(update={
                "value": current.evidence_bytes.value + amount,
            }),
        })
        if updated.storage_bytes.value == current.storage_bytes.value:
            return candidate
        current = updated
    raise ValueError("controlled receipt byte accounting did not stabilize")


def _sealed_initial(
    *, plan: CampaignWorkPlan, unit: UnitKey, code: Any, sample: Any,
    config: FairLegConfig, source_status: str, provenance_sha256: str,
    destination: Path,
) -> SharedInitialBPReceiptV1:
    controller = FairLegController(code.hz, sample.observation.syndrome,
                                   error_rate=plan.work_spec.shared_sampler.x_error_rate, config=config)
    started = perf_counter_ns()
    initial = controller.initial_bp()
    runtime_ns = perf_counter_ns() - started
    event = _json_line({
        "schema": "controlled_event_v1", "kind": "initial_bp",
        "physical_sample_identity": unit.physical_sample_identity,
        "state": initial.as_evidence(),
    })
    event_path = destination / "events" / f"shared-{unit.physical_sample_identity}.jsonl"
    _publish_exact(event_path, event)
    configured = {name: value for name, value in config.as_evidence().items() if type(value) is int}
    component = _component(
        component_id="initial-bp", role="initial_bp", source_status=source_status,
        converged=initial.converged, iterations=initial.iterations,
        configured=configured, work=initial.work.as_evidence(structural_event_version=4),
        runtime_ns=runtime_ns, events=1, evidence_bytes=len(event), storage_bytes=len(event),
        provenance_sha256=provenance_sha256,
    )
    for _ in range(8):
        receipt = SharedInitialBPReceiptV1.from_segment(
            sample_identity=unit.physical_sample_identity, sample_id=unit.sample_id,
            component=component, segment=initial,
        )
        amount = len(receipt.primitive_bytes()) + 1
        updated = component.model_copy(update={
            "storage_bytes": component.storage_bytes.model_copy(update={
                "value": len(event) + amount,
            }),
        })
        if updated.storage_bytes.value == component.storage_bytes.value:
            break
        component = updated
    else:
        raise ValueError("shared initial receipt byte accounting did not stabilize")
    _publish_exact(destination / "shared" / f"{unit.physical_sample_identity}.json", receipt.primitive_bytes() + b"\n")
    return receipt


def _load_initial(destination: Path, unit: UnitKey) -> SharedInitialBPReceiptV1:
    path = destination / "shared" / f"{unit.physical_sample_identity}.json"
    if path.is_symlink() or not path.is_file():
        raise ValueError("controlled continuation lacks its sealed shared initial BP")
    raw = path.read_bytes()
    receipt = SharedInitialBPReceiptV1.model_validate_json(raw)
    if (raw != receipt.primitive_bytes() + b"\n"
            or receipt.sample_identity != unit.physical_sample_identity
            or receipt.sample_id != unit.sample_id):
        raise ValueError("shared initial BP receipt differs from frozen physical sample")
    return receipt


def run_fair_controlled_unit(
    *, plan: CampaignWorkPlan, unit: UnitKey, arm_manifest: dict[str, Any],
    campaign_root: Path, output_root: Path,
) -> ControlledArmReceiptV1:
    """Execute one missing fair leg from the same physical and initial receipts."""
    if (plan.work_spec is None or unit.key not in plan.unit_keys
            or arm_manifest.get("runner") != "controlled_fair_leg_v1"
            or arm_manifest.get("arm_id") != unit.arm_id
            or unit.arm_id not in {"initial_bp", "relay", "beam"}):
        raise ValueError("fair unit differs from frozen controlled work")
    arm = next(item for item in plan.work_spec.arms if item.arm_id == unit.arm_id)
    manifest_path = campaign_root / arm.manifest_path
    if (manifest_path.is_symlink() or not manifest_path.is_file()
            or sha256(manifest_path.read_bytes()).hexdigest() != arm.manifest_sha256
            or json.loads(manifest_path.read_bytes()) != arm_manifest):
        raise ValueError("fair arm manifest differs from frozen bytes")
    loaded = load_artifact(
        campaign_root, arm_manifest["artifact_path"],
        expected_raw_sha256=arm_manifest["artifact_raw_sha256"],
        expected_semantic_sha256=arm_manifest["artifact_semantic_sha256"],
    )
    code = loaded.code
    config = FairLegConfig(**arm_manifest["controls"])
    manifest_sha = arm.manifest_sha256
    sample_path = output_root / "samples" / f"{unit.physical_sample_identity}.json"
    materialized = materialize_campaign_sample(
        plan=plan, unit=unit, spec=plan.work_spec,
        context=SimpleNamespace(code=code), destination=sample_path,
    )
    assert isinstance(materialized, MaterializedPhysicalSampleV1)
    sample = _shot_from_materialized(materialized)
    shared_path = output_root / "shared" / f"{unit.physical_sample_identity}.json"
    shared = (_sealed_initial(
        plan=plan, unit=unit, code=code, sample=sample, config=config,
        source_status=arm_manifest["source_status"], provenance_sha256=manifest_sha,
        destination=output_root,
    ) if unit.arm_id == "initial_bp" and not (shared_path.exists() or shared_path.is_symlink())
        else _load_initial(output_root, unit))
    initial_manifest_sha = next(item.manifest_sha256 for item in plan.work_spec.arms
                                if item.arm_id == "initial_bp")
    if shared.component.provenance_sha256 != initial_manifest_sha:
        raise ValueError("shared initial BP provenance differs from frozen baseline")
    controller = FairLegController(code.hz, sample.observation.syndrome,
                                   error_rate=plan.work_spec.shared_sampler.x_error_rate, config=config)
    initial = controller.adopt_verified_initial(shared.to_segment())
    if unit.arm_id == "initial_bp":
        result = None
        candidate = initial.candidate if initial.converged else None
        work = None
        iterations = None
        converged = None
        runtime_ns = None
    else:
        started = perf_counter_ns()
        result = (controller.run_relay(initial, sample_seed_identity=sample.sample_identity)
                  if unit.arm_id == "relay" else controller.run_beam(initial))
        runtime_ns = perf_counter_ns() - started
        candidate = result.candidate
        work = result.extra_work.as_evidence(structural_event_version=4)
        iterations = sum(item.segment.iterations for item in result.units if item.segment is not None)
        converged = candidate is not None
    started = perf_counter_ns()
    terminal = _validated_terminal(code, sample.hidden.x, candidate)
    validation_ns = perf_counter_ns() - started
    decode_event = None if result is None else _json_line({
        "schema": "controlled_event_v1", "kind": unit.arm_id,
        "unit_key": unit.key, "shared_input_receipt_sha256": shared.digest(),
        "result": result.as_evidence(),
    })
    validation_event = _json_line({
        "schema": "controlled_event_v1", "kind": "original_validation",
        "unit_key": unit.key, "terminal_status": terminal,
        "candidate": None if candidate is None else candidate.tolist(),
        "physical_sample_identity": unit.physical_sample_identity,
    })
    event_bytes = (decode_event or b"") + validation_event
    event_path = output_root / "events" / f"{unit.key}.jsonl"
    _publish_exact(event_path, event_bytes)
    configured = {name: value for name, value in config.as_evidence().items() if type(value) is int}
    component = None if result is None else _component(
        component_id=unit.arm_id, role=unit.arm_id, source_status=arm_manifest["source_status"],
        converged=converged, iterations=iterations, configured=configured,
        work=work, runtime_ns=runtime_ns, events=1, evidence_bytes=len(decode_event),
        storage_bytes=len(decode_event), provenance_sha256=manifest_sha,
        shared_input_receipt_sha256=shared.digest(),
    )
    validation = _component(
        component_id=f"{unit.arm_id}:original_validation", role="original_validation",
        source_status=arm_manifest["source_status"], converged=None, iterations=None,
        configured={"original_checks": 1}, work={"original_checks": int(candidate is not None)}, runtime_ns=validation_ns,
        events=1, evidence_bytes=len(validation_event), storage_bytes=len(validation_event),
        provenance_sha256=manifest_sha,
    )
    receipt = _receipt_with_bytes(payload={
        "schema": "controlled_arm_receipt_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "unit_key": unit.key, "physical_sample_identity": unit.physical_sample_identity,
        "sample_id": unit.sample_id,
        "arm_id": unit.arm_id,
        "materialized_sample_sha256": materialized.materialized_sample_sha256,
        "shared_input_receipt_sha256": shared.digest(),
        "shared_component_sha256": shared.component.digest() if result is None else None,
        "validation_component": validation,
        "candidate": None if candidate is None else tuple(int(bit) for bit in candidate),
        "terminal_status": terminal,
        "event_ledger_sha256": sha256(event_bytes).hexdigest(),
        "event_ledger_bytes": len(event_bytes),
    }, component=component)
    _publish_exact(output_root / "units" / f"{unit.key}.json", receipt.primitive_bytes() + b"\n")
    return receipt


def verify_fair_controlled_unit(
    *, plan: CampaignWorkPlan, unit: UnitKey, arm_manifest: dict[str, Any],
    campaign_root: Path, output_root: Path,
) -> ControlledArmReceiptV1:
    """Replay one sealed fair terminal and cost lineage without decoder work."""
    if unit.key not in plan.unit_keys or arm_manifest.get("arm_id") != unit.arm_id:
        raise ValueError("controlled verification unit differs from frozen work")
    receipt_path = output_root / "units" / f"{unit.key}.json"
    sample_path = output_root / "samples" / f"{unit.physical_sample_identity}.json"
    event_path = output_root / "events" / f"{unit.key}.jsonl"
    if any(path.is_symlink() or not path.is_file() for path in (receipt_path, sample_path, event_path)):
        raise ValueError("controlled unit lacks regular sealed evidence")
    raw = receipt_path.read_bytes()
    receipt = ControlledArmReceiptV1.model_validate_json(raw)
    if raw != receipt.primitive_bytes() + b"\n":
        raise ValueError("controlled arm receipt has noncanonical bytes")
    materialized_raw = sample_path.read_bytes()
    materialized = MaterializedPhysicalSampleV1.model_validate_json(materialized_raw)
    if materialized_raw != materialized.primitive_bytes() + b"\n":
        raise ValueError("controlled physical sample has noncanonical bytes")
    if (receipt.unit_key != unit.key
            or receipt.campaign_spec_digest != plan.campaign_spec_digest
            or receipt.campaign_plan_digest != plan.campaign_plan_digest
            or receipt.physical_sample_identity != unit.physical_sample_identity
            or receipt.sample_id != unit.sample_id
            or receipt.arm_id != unit.arm_id
            or receipt.materialized_sample_sha256 != materialized.materialized_sample_sha256
            or materialized.physical_sample_identity != unit.physical_sample_identity
            or materialized.cohort_id != unit.cohort_id
            or materialized.point_id != unit.point_id
            or materialized.sample_namespace != unit.sample_namespace
            or materialized.sample_id != unit.sample_id
            or materialized.sampler_contract_sha256 != plan.work_spec.shared_sampler.digest()):
        raise ValueError("controlled arm or sample differs from frozen plan")
    event_bytes = event_path.read_bytes()
    if (len(event_bytes) != receipt.event_ledger_bytes
            or sha256(event_bytes).hexdigest() != receipt.event_ledger_sha256
            or not event_bytes.endswith(b"\n")):
        raise ValueError("controlled event ledger differs from sealed arm")
    rows = [json.loads(line) for line in event_bytes.splitlines()]
    expected_kinds = (["original_validation"] if unit.arm_id == "initial_bp"
                      else [unit.arm_id, "original_validation"])
    if ([row.get("kind") for row in rows] != expected_kinds
            or any(row.get("schema") != "controlled_event_v1" or row.get("unit_key") != unit.key for row in rows)):
        raise ValueError("controlled event order differs from declared arm")
    shared = _load_initial(output_root, unit)
    if receipt.shared_input_receipt_sha256 != shared.digest():
        raise ValueError("controlled arm shared initial digest differs from sealed input")
    initial_manifest_sha = next(item.manifest_sha256 for item in plan.work_spec.arms
                                if item.arm_id == "initial_bp")
    if shared.component.provenance_sha256 != initial_manifest_sha:
        raise ValueError("shared initial BP provenance differs from frozen baseline")
    shared_event_path = output_root / "events" / f"shared-{unit.physical_sample_identity}.jsonl"
    if shared_event_path.is_symlink() or not shared_event_path.is_file():
        raise ValueError("shared initial event ledger is absent")
    shared_event = shared_event_path.read_bytes()
    if len(shared_event.splitlines()) != 1:
        raise ValueError("shared initial event ledger must have one producer event")
    shared_row = json.loads(shared_event)
    if (shared_row.get("kind") != "initial_bp"
            or shared_row.get("physical_sample_identity") != unit.physical_sample_identity
            or shared_row.get("state") != shared.to_segment().as_evidence()
            or shared.component.evidence_bytes.value != len(shared_event)
            or shared.component.storage_bytes.value != len(shared_event) + len(shared.primitive_bytes()) + 1):
        raise ValueError("shared initial component differs from its state or actual bytes")
    if unit.arm_id == "initial_bp":
        if (receipt.shared_component_sha256 != shared.component.digest()
                or receipt.component is not None):
            raise ValueError("baseline duplicates or changes shared initial BP")
        candidate = shared.to_segment().candidate if shared.state.converged else None
    else:
        result = rows[0].get("result")
        if (not isinstance(result, dict)
                or rows[0].get("shared_input_receipt_sha256") != shared.digest()
                or receipt.component is None
                or receipt.component.actual_work != result.get("extra_work")
                or receipt.component.iterations.value != sum(
                    item["segment"]["iterations"] for item in result.get("units", [])
                    if item.get("segment") is not None)
                or receipt.component.convergence_status.value != (result.get("candidate") is not None)):
            raise ValueError("controlled continuation component differs from retained events")
        candidate = None if result.get("candidate") is None else np.asarray(result["candidate"], dtype=np.uint8)
    loaded = load_artifact(
        campaign_root, arm_manifest["artifact_path"],
        expected_raw_sha256=arm_manifest["artifact_raw_sha256"],
        expected_semantic_sha256=arm_manifest["artifact_semantic_sha256"],
    )
    sample = _shot_from_materialized(materialized)
    terminal = _validated_terminal(loaded.code, sample.hidden.x, candidate)
    if (receipt.terminal_status != terminal
            or receipt.candidate != (None if candidate is None else tuple(int(bit) for bit in candidate))
            or rows[-1].get("terminal_status") != terminal
            or rows[-1].get("candidate") != (None if candidate is None else candidate.tolist())):
        raise ValueError("controlled terminal differs from independent original-problem evaluation")
    decode_bytes = b"" if unit.arm_id == "initial_bp" else _json_line(rows[0])
    validation_bytes = _json_line(rows[-1])
    if (receipt.validation_component.evidence_bytes.value != len(validation_bytes)
            or receipt.validation_component.actual_work != {"original_checks": int(candidate is not None)}
            or receipt.validation_component.storage_bytes.value != len(validation_bytes) + (
                len(raw) if unit.arm_id == "initial_bp" else 0)):
        raise ValueError("controlled original-validation cost differs from actual bytes")
    if receipt.component is not None and (
            receipt.component.evidence_bytes.value != len(decode_bytes)
            or receipt.component.storage_bytes.value != len(decode_bytes) + len(raw)):
        raise ValueError("controlled continuation cost differs from actual bytes")
    return receipt


_MATCHED_TERMINALS = (
    "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
    "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
    "infrastructure_interruption",
)

_MATCHED_OUTCOME_MATRIX = OutcomeMatrixV1(
    rule_id="all_shot_v1",
    treatments=tuple(
        OutcomeTreatmentV1(
            terminal_status=status,
            all_shot=("incomplete" if status == "infrastructure_interruption" else
                      "success" if status in {"exact", "stabilizer_equivalent"} else "failure"),
            conditional=("incomplete" if status == "infrastructure_interruption" else
                         "accepted" if status in {"exact", "stabilizer_equivalent", "wrong_logical_action", "postselected_rejection"} else "excluded"),
        )
        for status in _MATCHED_TERMINALS
    ),
)


# A separate arm cannot be successful unless both marginal decoders finished
# successfully.  When both components failed, retain one deterministic terminal
# rather than letting candidate evaluation overwrite either component result.
_SEPARATE_COMPONENT_TERMINAL_PRECEDENCE = (
    "infrastructure_interruption", "timeout", "invalid_syndrome", "nonconvergence",
    "no_proposal", "postselected_rejection", "wrong_logical_action",
)
_SUCCESSFUL_COMPONENT_TERMINALS = frozenset({"exact", "stabilizer_equivalent"})


def _separate_component_terminal(components: tuple[BinaryComponentTerminalV1, BinaryComponentTerminalV1]) -> str | None:
    """Return the controlling component terminal, or ``None`` if both succeeded."""
    statuses = {component.terminal_status for component in components}
    for status in _SEPARATE_COMPONENT_TERMINAL_PRECEDENCE:
        if status in statuses:
            return status
    if statuses <= _SUCCESSFUL_COMPONENT_TERMINALS:
        return None
    raise ValueError("separate comparison has an unsupported component terminal")


class JointArmInputV1(StrictModel):
    """Decoder-visible joint input; physical truth is deliberately absent."""

    probabilities: tuple[tuple[float, ...], ...]
    x_syndrome: tuple[int, ...]
    z_syndrome: tuple[int, ...]
    physical_sample_identity: str
    materialized_sample_sha256: str


class BinaryArmInputV1(StrictModel):
    """D-05 narrow view for a separate binary component."""

    component: Literal["X", "Z"]
    prior: tuple[float, ...]
    syndrome: tuple[int, ...]
    physical_sample_identity: str
    materialized_sample_sha256: str


class JointArmResultV1(StrictModel):
    candidate_x: tuple[int, ...] | None = None
    candidate_z: tuple[int, ...] | None = None
    terminal_status: Literal[
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
        "infrastructure_interruption",
    ]
    iterations: int = 0
    work: dict[str, int]
    runtime_ns: int = 0
    timing_boundary: Literal["decoder_callback_wall_v1"] = "decoder_callback_wall_v1"


class BinaryArmResultV1(StrictModel):
    candidate: tuple[int, ...] | None = None
    terminal_status: Literal[
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
        "infrastructure_interruption",
    ]
    iterations: int = 0
    work: dict[str, int]
    runtime_ns: int = 0
    timing_boundary: Literal["decoder_callback_wall_v1"] = "decoder_callback_wall_v1"


def canonical_binary_materialized_decoder(
    *, materialized_sample: MaterializedPhysicalSampleV1,
    manifest_paths: dict[Literal["X", "Z"], Path], ledger_directory: Path,
) -> Callable[[BinaryArmInputV1], BinaryArmResultV1]:
    """Adapt the canonical materialized runner without exposing physical truth.

    The closure owns the evaluator-only materialized bytes and gives the
    canonical runner the exact shared digest for both components.  The decoder
    callback itself receives only :class:`BinaryArmInputV1`, making D-05's
    marginal-information boundary auditable at the public seam.
    """
    if not isinstance(materialized_sample, MaterializedPhysicalSampleV1):
        raise ValueError("canonical binary adapter requires a materialized sample")
    if set(manifest_paths) != {"X", "Z"}:
        raise ValueError("canonical binary adapter requires one X and one Z manifest")

    def decode(input_: BinaryArmInputV1) -> BinaryArmResultV1:
        from ..runner import CanonicalMaterializedRunV1, run_canonical_materialized_one

        ledger_path = ledger_directory / f"{input_.component.lower()}-events.jsonl"
        started = perf_counter_ns()
        result = run_canonical_materialized_one(
            manifest_paths[input_.component], sample=_shot_from_materialized(materialized_sample),
            materialized_sample_sha256=input_.materialized_sample_sha256, ledger_path=ledger_path,
        )
        if isinstance(result, CanonicalMaterializedRunV1):
            if result.status == "interrupted":
                return BinaryArmResultV1(candidate=None, terminal_status="infrastructure_interruption", iterations=0,
                                         work={"canonical_iterations": 0}, runtime_ns=perf_counter_ns() - started)
            result = result.terminal
        if result is None:
            raise ValueError("canonical binary materialized runner returned no terminal result")
        # Canonical ledgers retain selected output; accepting no candidate keeps
        # D-08's all-shot record explicit instead of manufacturing a recovery.
        selected: tuple[int, ...] | None = None
        if ledger_path.is_file():
            for line in reversed(ledger_path.read_text(encoding="utf-8").splitlines()):
                event = json.loads(line)
                data = event.get("data", event)
                output = data.get("selected_output") if isinstance(data, dict) else None
                if isinstance(output, list) and all(type(bit) is int and bit in (0, 1) for bit in output):
                    selected = tuple(output)
                    break
        raw_outcome = getattr(result, "outcome", None)
        status = _status_from_evaluation(raw_outcome) if isinstance(raw_outcome, str) else "no_proposal"
        return BinaryArmResultV1(
            candidate=selected, terminal_status=status if selected is not None else "no_proposal",
            iterations=int(getattr(result, "iterations", 0)),
            work={"canonical_iterations": int(getattr(result, "iterations", 0))}, runtime_ns=perf_counter_ns() - started,
        )

    return decode


def _matched_digest(payload: object) -> str:
    return sha256(b"bp-registry-pauli-matched-pair-v1\0" + canonical_json_bytes(payload)).hexdigest()


def _matched_bits(encoded: str, shape: tuple[int, ...]) -> np.ndarray:
    bits = np.frombuffer(base64.b64decode(encoded, validate=True), dtype=np.uint8).copy().reshape(shape)
    if bits.ndim != 1 or np.any((bits != 0) & (bits != 1)):
        raise ValueError("materialized matched-comparison errors must be binary vectors")
    return bits


def _status_from_evaluation(outcome: str) -> str:
    return "wrong_logical_action" if outcome == "logical_failure" else outcome


def _all_shot(status: str) -> Literal["success", "failure", "incomplete"]:
    return next(item.all_shot for item in _MATCHED_OUTCOME_MATRIX.treatments if item.terminal_status == status)


def _arm_evaluation(*, code: Any, true_x: np.ndarray, true_z: np.ndarray,
                    candidate_x: tuple[int, ...] | None, candidate_z: tuple[int, ...] | None) -> dict[str, Any]:
    if candidate_x is None or candidate_z is None:
        return {"outcome": "no_proposal", "logical_action_agrees": None}
    evaluation = evaluate_candidate(
        code, true_x=true_x, true_z=true_z,
        candidate_x=np.asarray(candidate_x, dtype=np.uint8),
        candidate_z=np.asarray(candidate_z, dtype=np.uint8),
    )
    return {"outcome": _status_from_evaluation(evaluation.outcome), "logical_action_agrees": evaluation.logical_action_agrees}


def _syndrome_digest(syndrome: tuple[int, ...]) -> str:
    return sha256(canonical_json_bytes(list(syndrome))).hexdigest()


def run_joint_separate_unit(
    *, code: Any, materialized_sample: MaterializedPhysicalSampleV1,
    joint_probabilities: tuple[tuple[float, ...], ...],
    joint_decoder: Callable[[JointArmInputV1], JointArmResultV1],
    binary_decoder: Callable[[BinaryArmInputV1], BinaryArmResultV1],
) -> PauliMatchedPairV1:
    """Run D-06 paired inference from one immutable Pauli sample.

    Callback inputs model the actual decoder boundary.  The evaluator-owned
    materialized error is decoded only after both arms return, and never enters
    either callback object.  Production adapters may call the existing
    ``run_canonical_materialized_one`` behind ``binary_decoder``; this narrow
    seam keeps the marginal isolation testable without another binary engine.
    """
    if not isinstance(materialized_sample, MaterializedPhysicalSampleV1):
        raise ValueError("matched comparison requires a validated materialized physical sample")
    materialized_sample = MaterializedPhysicalSampleV1.model_validate(
        materialized_sample.model_dump(mode="json", by_alias=True)
    )
    validated = code.validate()
    if len(joint_probabilities) != validated.n or any(len(row) != 4 for row in joint_probabilities):
        raise ValueError("joint probabilities must provide one I,X,Y,Z row per code qubit")
    rows = np.asarray(joint_probabilities, dtype=np.float64)
    if not np.all(np.isfinite(rows)) or np.any(rows < 0) or not np.allclose(rows.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("joint probabilities must be finite I,X,Y,Z rows summing to one")
    true_x = _matched_bits(materialized_sample.x_bytes_b64, materialized_sample.x_shape)
    true_z = _matched_bits(materialized_sample.z_bytes_b64, materialized_sample.z_shape)
    if true_x.shape != (validated.n,) or true_z.shape != (validated.n,):
        raise ValueError("materialized sample and comparison code have incompatible sizes")
    expected_z = tuple(int(value) for value in ((validated.hz.astype(np.int64) @ true_x) % 2).tolist())
    expected_x = tuple(int(value) for value in ((validated.hx.astype(np.int64) @ true_z) % 2).tolist())
    observed = materialized_sample.observations
    if set(observed) != {"X", "Z"}:
        raise ValueError("matched comparison requires both immutable CSS observations")
    # Decoder calls occur before evaluator access to the materialized error.
    joint_result = joint_decoder(JointArmInputV1(
        probabilities=tuple(tuple(float(value) for value in row) for row in rows),
        x_syndrome=expected_x, z_syndrome=expected_z,
        physical_sample_identity=materialized_sample.physical_sample_identity,
        materialized_sample_sha256=materialized_sample.materialized_sample_sha256,
    ))
    x_result = binary_decoder(BinaryArmInputV1(
        component="X", prior=tuple(float(value) for value in rows[:, 1] + rows[:, 2]), syndrome=expected_z,
        physical_sample_identity=materialized_sample.physical_sample_identity,
        materialized_sample_sha256=materialized_sample.materialized_sample_sha256,
    ))
    z_result = binary_decoder(BinaryArmInputV1(
        component="Z", prior=tuple(float(value) for value in rows[:, 2] + rows[:, 3]), syndrome=expected_x,
        physical_sample_identity=materialized_sample.physical_sample_identity,
        materialized_sample_sha256=materialized_sample.materialized_sample_sha256,
    ))
    if not isinstance(joint_result, JointArmResultV1) or not isinstance(x_result, BinaryArmResultV1) or not isinstance(z_result, BinaryArmResultV1):
        raise ValueError("matched comparison decoder callbacks must return typed terminal results")
    for result in (joint_result, x_result, z_result):
        if result.iterations < 0 or not result.work or any(type(value) is not int or value < 0 for value in result.work.values()):
            raise ValueError("matched comparison terminal work must be explicit nonnegative integers")
    components = (
        BinaryComponentTerminalV1(component="X", candidate=x_result.candidate, terminal_status=x_result.terminal_status,
                                  iterations=x_result.iterations, work=x_result.work, runtime_ns=x_result.runtime_ns,
                                  timing_boundary=x_result.timing_boundary, syndrome_sha256=_syndrome_digest(expected_z)),
        BinaryComponentTerminalV1(component="Z", candidate=z_result.candidate, terminal_status=z_result.terminal_status,
                                  iterations=z_result.iterations, work=z_result.work, runtime_ns=z_result.runtime_ns,
                                  timing_boundary=z_result.timing_boundary, syndrome_sha256=_syndrome_digest(expected_x)),
    )
    joint_evaluation = _arm_evaluation(code=validated, true_x=true_x, true_z=true_z,
                                       candidate_x=joint_result.candidate_x, candidate_z=joint_result.candidate_z)
    separate_evaluation = _arm_evaluation(code=validated, true_x=true_x, true_z=true_z,
                                          candidate_x=x_result.candidate, candidate_z=z_result.candidate)
    joint = PauliMatchedArmV1(
        arm_id="joint", materialized_sample_sha256=materialized_sample.materialized_sample_sha256,
        candidate_x=joint_result.candidate_x, candidate_z=joint_result.candidate_z,
        terminal_status=(joint_result.terminal_status if joint_evaluation["outcome"] == "no_proposal" else joint_evaluation["outcome"]),
        all_shot=_all_shot(joint_result.terminal_status if joint_evaluation["outcome"] == "no_proposal" else joint_evaluation["outcome"]),
        evaluation=joint_evaluation, work=dict(joint_result.work), runtime_ns=joint_result.runtime_ns,
        timing_boundary=joint_result.timing_boundary,
    )
    component_terminal = _separate_component_terminal(components)
    separate_status = component_terminal if component_terminal is not None else separate_evaluation["outcome"]
    separate = PauliMatchedArmV1(
        arm_id="separate", materialized_sample_sha256=materialized_sample.materialized_sample_sha256,
        candidate_x=x_result.candidate, candidate_z=z_result.candidate,
        terminal_status=separate_status, all_shot=_all_shot(separate_status), evaluation=separate_evaluation,
        work={f"{component.component.lower()}_{name}": amount for component in components for name, amount in component.work.items()},
        runtime_ns=x_result.runtime_ns + z_result.runtime_ns, timing_boundary=x_result.timing_boundary,
    )
    unsigned = {
        "schema": "pauli_matched_pair_v1", "decision_ids": ("D-05", "D-06", "D-08"),
        "physical_sample_identity": materialized_sample.physical_sample_identity,
        "physical_error_sha256": materialized_sample.physical_error_sha256,
        "materialized_sample_sha256": materialized_sample.materialized_sample_sha256,
        "joint": joint.model_dump(mode="json"), "separate": separate.model_dump(mode="json"),
        "components": tuple(component.model_dump(mode="json") for component in components),
    }
    return PauliMatchedPairV1.model_validate({**unsigned, "record_sha256": _matched_digest(unsigned)})


def _phase11_load_code(*, root: Path, code: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    """Load a digest-bound controlled code while retaining its qualification."""
    required = {"code_id", "artifact_path", "artifact_sha256", "source", "run_fidelity"}
    if code.get("code_id") == "GB46":
        if set(code) != required:
            raise ValueError("controlled GB46 code identity is incomplete")
        artifact = (root / code["artifact_path"]).resolve()
        if root not in (artifact, *artifact.parents) or artifact.is_symlink() or not artifact.is_file():
            raise ValueError("controlled GB46 artifact is unavailable")
        artifact_bytes = artifact.read_bytes()
        if code["run_fidelity"] != "canonical_adaptation" or sha256(artifact_bytes).hexdigest() != code["artifact_sha256"]:
            raise ValueError("controlled GB46 artifact identity differs from the frozen design")
        from ..quaternary.asced import parse_pinned_gb46_css
        return parse_pinned_gb46_css(artifact_bytes), {"code_id": "GB46"}
    required |= {"provenance_path", "provenance_sha256", "distance_qualification", "logical_operator_qualification"}
    if code.get("code_id") != "BB72" or set(code) != required:
        raise ValueError("controlled BB72 code identity is incomplete")
    artifact = (root / code["artifact_path"]).resolve()
    provenance = (root / code["provenance_path"]).resolve()
    if any(root not in (path, *path.parents) or path.is_symlink() or not path.is_file() for path in (artifact, provenance)):
        raise ValueError("controlled BB72 artifact or provenance is unavailable")
    if sha256(artifact.read_bytes()).hexdigest() != code["artifact_sha256"] or sha256(provenance.read_bytes()).hexdigest() != code["provenance_sha256"]:
        raise ValueError("controlled BB72 artifact or provenance identity differs from the frozen design")
    try:
        payload, provenance_payload = json.loads(artifact.read_bytes()), json.loads(provenance.read_bytes())
        parsed = CssCode(
            hx=np.asarray(payload["hx"], dtype=np.uint8), hz=np.asarray(payload["hz"], dtype=np.uint8),
            lx=np.asarray(payload["lx"], dtype=np.uint8), lz=np.asarray(payload["lz"], dtype=np.uint8),
        ).validate()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("controlled BB72 artifact is not a valid qualified CSS code") from error
    if (provenance_payload.get("distance", {}).get("status") != "source_reported"
            or provenance_payload.get("distance", {}).get("value") != 6
            or provenance_payload.get("logical_provider", {}).get("status") != "project_derived"
            or provenance_payload.get("logical_provider", {}).get("source_logical_equivalence") != "not_assessed"):
        raise ValueError("controlled BB72 provenance qualifications differ from the frozen design")
    return parsed, {
        "code_id": "BB72", "code_provenance_sha256": code["provenance_sha256"],
        "distance_qualification": code["distance_qualification"],
        "logical_operator_qualification": code["logical_operator_qualification"],
    }


def preflight_phase11_controlled_design(*, root: Path, design_path: Path) -> dict[str, Any]:
    """Validate a bounded, source-qualified controlled-calibration identity before writes.

    This admission gate deliberately consumes only the project-owned, pinned
    GB46 check artifact and the frozen fixed-marginal design.  Source-study
    targets and source-campaign fields are rejected here so a caller cannot
    accidentally turn calibration evidence into reproduction evidence.
    """
    from .statistics import load_fixed_marginal_design

    root = root.resolve(strict=True)
    resolved = design_path.resolve(strict=True)
    if root not in (resolved, *resolved.parents) or resolved.is_symlink() or not resolved.is_file():
        raise ValueError("controlled design must be a regular file beneath the campaign root")
    raw = resolved.read_bytes()
    try:
        design = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("controlled design is not valid JSON") from error
    if not isinstance(design, dict):
        raise ValueError("controlled design must be a JSON object")
    prohibited = {"source_target", "source_campaign", "source_target_fields", "paper_target"}
    if prohibited & set(design):
        raise ValueError("controlled design must not contain source-campaign fields")
    required = {
        "schema", "study_id", "evidence_lane", "code", "fixed_marginal_design",
        "sample_ranges", "calibration_limits", "claim_scope", "publication_authorization",
    }
    if set(design) != required or design["schema"] != "phase11_controlled_calibration_v1":
        raise ValueError("controlled design has an invalid field set or schema")
    if design["evidence_lane"] != "controlled_canonical_adaptation":
        raise ValueError("controlled design must remain in the canonical-adaptation lane")
    if design["publication_authorization"] != "deny" or "no_source_reproduction" not in design["claim_scope"]:
        raise ValueError("controlled design must retain its calibration-only, deny-by-default scope")
    code = design["code"]
    if not isinstance(code, dict) or code.get("run_fidelity") != "canonical_adaptation":
        raise ValueError("controlled code identity must retain canonical-adaptation fidelity")
    parsed_code, code_receipt = _phase11_load_code(root=root, code=code)
    fixed = design["fixed_marginal_design"]
    if not isinstance(fixed, dict) or set(fixed) != {"path", "sha256", "point_order"}:
        raise ValueError("controlled fixed-marginal identity is incomplete")
    fixed_path = (root / fixed["path"]).resolve()
    if root not in (fixed_path, *fixed_path.parents) or fixed_path.is_symlink() or not fixed_path.is_file():
        raise ValueError("controlled fixed-marginal design is unavailable")
    if sha256(fixed_path.read_bytes()).hexdigest() != fixed["sha256"]:
        raise ValueError("controlled fixed-marginal design digest differs from the frozen design")
    sweep = load_fixed_marginal_design(fixed_path)
    if tuple(fixed["point_order"]) != sweep.point_order:
        raise ValueError("controlled fixed-marginal point order differs from the frozen design")
    ranges = design["sample_ranges"]
    if not isinstance(ranges, dict) or set(ranges) != set(sweep.point_order):
        raise ValueError("controlled sample ranges must cover exactly the frozen channel rows")
    assigned: set[int] = set()
    for point in sweep.point_order:
        pair = ranges[point]
        if (not isinstance(pair, list) or len(pair) != 2 or any(type(value) is not int or value < 0 for value in pair)
                or pair[0] > pair[1]):
            raise ValueError("controlled sample ranges must be nonnegative inclusive pairs")
        members = set(range(pair[0], pair[1] + 1))
        if assigned & members:
            raise ValueError("controlled sample ranges must be disjoint")
        assigned |= members
    limits = design["calibration_limits"]
    if (not isinstance(limits, dict) or set(limits) != {"max_pairs_per_point", "max_iterations", "max_wall_seconds_per_pair", "max_output_bytes"}
            or any(type(limits[key]) is not int or limits[key] < 1 for key in limits)):
        raise ValueError("controlled calibration limits must be bounded positive integers")
    if any((ranges[point][1] - ranges[point][0] + 1) > limits["max_pairs_per_point"] for point in sweep.point_order):
        raise ValueError("controlled sample range exceeds the calibration pair cap")
    return {
        "schema": "phase11_controlled_preflight_v1",
        "study_id": design["study_id"], "design_sha256": sha256(raw).hexdigest(),
        "code_artifact_sha256": code["artifact_sha256"], "code_qubits": parsed_code.n, **code_receipt,
        "fixed_marginal_design_sha256": fixed["sha256"], "point_order": list(sweep.point_order),
        "sample_ranges": ranges, "publication_authorization": "deny",
    }


def _phase11_digest(domain: str, payload: object) -> str:
    return sha256(domain.encode("ascii") + b"\0" + canonical_json_bytes(payload)).hexdigest()


def _phase11_safe_root(path: Path) -> Path:
    """Admit an explicitly selected regular output directory without links."""
    # ``resolve`` follows a dangling output-root symlink, which turns a
    # caller-selected local destination into an arbitrary write target.  Keep
    # the lexical absolute path and reject links at every existing component.
    lexical = path.expanduser().absolute()
    for component in (lexical, *lexical.parents):
        if component.is_symlink():
            raise ValueError("controlled output root must not contain a symlink")
    if lexical.exists() and not lexical.is_dir():
        raise ValueError("controlled output root must be a regular directory")
    return lexical


def _phase11_publish_exact(root: Path, relative: tuple[str, ...], payload: bytes) -> None:
    """Publish immutable Phase 11 bytes below a verified root without links."""
    if not relative or any(not part or part in {".", ".."} or "/" in part for part in relative):
        raise ValueError("controlled evidence requires a relative output path")
    root = _phase11_safe_root(root)
    root.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(root, flags)
    try:
        for component in relative[:-1]:
            try:
                os.mkdir(component, mode=0o755, dir_fd=directory_fd)
            except FileExistsError:
                pass
            next_fd = os.open(component, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        leaf = relative[-1]
        try:
            existing = os.stat(leaf, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if not stat.S_ISREG(existing.st_mode):
                raise ValueError("controlled evidence path conflicts with immutable bytes")
            read_fd = os.open(leaf, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
            try:
                if os.read(read_fd, len(payload) + 1) != payload or os.read(read_fd, 1):
                    raise ValueError("controlled evidence path conflicts with immutable bytes")
            finally:
                os.close(read_fd)
            return
        stage = f".phase11-{os.getpid()}-{secrets.token_hex(12)}"
        create_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        stage_fd = os.open(stage, create_flags, 0o600, dir_fd=directory_fd)
        try:
            os.write(stage_fd, payload)
            os.fsync(stage_fd)
        finally:
            os.close(stage_fd)
        try:
            os.link(stage, leaf, src_dir_fd=directory_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
        except FileExistsError as error:
            raise ValueError("controlled evidence path conflicts with immutable bytes") from error
        finally:
            try:
                os.unlink(stage, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
    finally:
        os.close(directory_fd)


def _phase11_sample(*, code: Any, design_sha256: str, point_id: str, sample_id: int,
                    probabilities: tuple[float, float, float, float]) -> MaterializedPhysicalSampleV1:
    """Materialize one sealed I/X/Y/Z sample before either decoder sees it."""
    physical_identity = _phase11_digest("phase11-gb46-physical-sample-v1", {
        "design_sha256": design_sha256, "point_id": point_id, "sample_id": sample_id,
    })
    seed_identity = _phase11_digest("phase11-gb46-sampler-v1", {"physical_sample_identity": physical_identity})
    seed = int.from_bytes(sha256(seed_identity.encode("ascii")).digest()[:16], "big")
    values = np.random.Generator(np.random.PCG64(seed)).choice(4, size=code.n, p=np.asarray(probabilities))
    x = np.isin(values, (1, 2)).astype(np.uint8)
    z = np.isin(values, (2, 3)).astype(np.uint8)
    x_b64, z_b64 = base64.b64encode(x.tobytes()).decode("ascii"), base64.b64encode(z.tobytes()).decode("ascii")
    z_syndrome = ((code.hz.astype(np.int64) @ x) % 2).astype(np.uint8)
    x_syndrome = ((code.hx.astype(np.int64) @ z) % 2).astype(np.uint8)
    def observed(check_type: str, bits: np.ndarray) -> dict[str, Any]:
        return {"check_type": check_type, "dtype": "uint8", "shape": list(bits.shape),
                "bytes_b64": base64.b64encode(bits.tobytes()).decode("ascii")}
    unsigned = {
        "schema": "materialized_physical_sample_v1", "physical_sample_identity": physical_identity,
        "sample_seed_identity": seed_identity, "cohort_id": "phase11-gb46-controlled-calibration",
        "point_id": point_id, "sample_namespace": "phase11-gb46-fixed-marginal-v1", "sample_id": sample_id,
        "sampler_contract_sha256": _phase11_digest("phase11-gb46-sampler-contract-v1", {
            "code_n": code.n, "probabilities": probabilities, "pauli_order": "I,X,Y,Z"}),
        "x_dtype": "uint8", "x_shape": [code.n], "x_bytes_b64": x_b64,
        "z_dtype": "uint8", "z_shape": [code.n], "z_bytes_b64": z_b64,
        "observations": {"X": observed("X", x_syndrome), "Z": observed("Z", z_syndrome)},
        "physical_error_sha256": _phase11_digest("bp-registry-physical-error-v1", {"x": x_b64, "z": z_b64}),
    }
    return MaterializedPhysicalSampleV1.model_validate({
        **unsigned,
        "materialized_sample_sha256": _phase11_digest("bp-registry-materialized-sample-v1", unsigned),
    })


def _phase11_joint_decoder(code: Any, *, max_iterations: int, max_work: int) -> Callable[[JointArmInputV1], JointArmResultV1]:
    """Adapt the project's scalar four-state canonical kernel to the public seam."""
    from ..quaternary.execution import TracerPauliProblem, _decode

    checks = np.vstack((np.where(code.hx, 1, 0), np.where(code.hz, 3, 0))).astype(np.uint8)
    def decode(input_: JointArmInputV1) -> JointArmResultV1:
        started = perf_counter_ns()
        problem = TracerPauliProblem(checks=checks, syndrome=np.asarray(input_.x_syndrome + input_.z_syndrome, dtype=np.uint8))
        candidate, _marginals, work, terminal = _decode(
            problem, channel=np.asarray(input_.probabilities, dtype=np.float64),
            max_iterations=max_iterations, max_work=max_work, epsilon=1e-12,
        )
        return JointArmResultV1(
            candidate_x=tuple(int(value in (1, 2)) for value in candidate),
            candidate_z=tuple(int(value in (2, 3)) for value in candidate),
            terminal_status="exact" if terminal == "completed" else "nonconvergence",
            iterations=max_iterations if terminal == "max_iterations" else min(max_iterations, 1), work=work,
            runtime_ns=perf_counter_ns() - started,
        )
    return decode


def _phase11_binary_decoder(code: Any, *, max_iterations: int) -> Callable[[BinaryArmInputV1], BinaryArmResultV1]:
    """Use the existing canonical binary SPA kernel on each declared marginal."""
    from ..canonical.kernel import BinarySpaKernel

    from ..canonical.numerics import REFERENCE_CPU_F64
    kernel = BinarySpaKernel(profile=REFERENCE_CPU_F64)
    def decode(input_: BinaryArmInputV1) -> BinaryArmResultV1:
        started = perf_counter_ns()
        matrix = code.hz if input_.component == "X" else code.hx
        prior = float(input_.prior[0])
        result = kernel.run(matrix, np.asarray(input_.syndrome, dtype=np.uint8), error_rate=prior, max_iterations=max_iterations)
        return BinaryArmResultV1(
            candidate=tuple(int(value) for value in result.candidate),
            terminal_status="exact" if result.converged else "nonconvergence",
            iterations=result.iterations, work={"canonical_spa_iterations": result.iterations},
            runtime_ns=perf_counter_ns() - started,
        )
    return decode


def _phase11_pair_path(output_root: Path, point_id: str, sample_id: int) -> Path:
    return output_root / "pairs" / point_id / f"{sample_id}.json"


def _phase11_execution_context(*, root: Path, design_path: Path, preflight: dict[str, Any]) -> tuple[Any, dict[str, Any], dict[str, int]]:
    """Load the sealed code, channel rows, and bounded decoder limits once."""
    from .statistics import load_fixed_marginal_design

    design = json.loads(design_path.read_bytes())
    code = _phase11_load_code(root=root, code=design["code"])[0]
    fixed = load_fixed_marginal_design(root / "data/studies/phase11-fixed-marginal-design.json")
    rows = {row.point_id: row for row in fixed.rows}
    limits = design["calibration_limits"]
    if set(rows) != set(preflight["point_order"]):
        raise ValueError("controlled execution rows differ from admitted preflight")
    return code, rows, limits


def _phase11_pair_semantics(pair: PauliMatchedPairV1) -> dict[str, Any]:
    """Retain only deterministic evidence; callback wall time is observational."""
    evidence = pair.model_dump(mode="json", by_alias=True, exclude={"record_sha256"})
    for arm in ("joint", "separate"):
        evidence[arm].pop("runtime_ns", None)
        evidence[arm].pop("timing_boundary", None)
    for component in evidence["components"]:
        component.pop("runtime_ns", None)
        component.pop("timing_boundary", None)
    return evidence


def _phase11_expected_pair(
    *, code: Any, rows: dict[str, Any], limits: dict[str, int], preflight: dict[str, Any], point_id: str, sample_id: int,
) -> tuple[MaterializedPhysicalSampleV1, PauliMatchedPairV1]:
    probabilities = rows[point_id].probabilities
    sample = _phase11_sample(
        code=code, design_sha256=preflight["design_sha256"], point_id=point_id,
        sample_id=sample_id, probabilities=probabilities,
    )
    pair = run_joint_separate_unit(
        code=code, materialized_sample=sample,
        joint_probabilities=tuple(probabilities for _ in range(code.n)),
        joint_decoder=_phase11_joint_decoder(code, max_iterations=limits["max_iterations"], max_work=1000000),
        binary_decoder=_phase11_binary_decoder(code, max_iterations=limits["max_iterations"]),
    )
    return sample, pair


def _phase11_load_pairs(
    *, output_root: Path, preflight: dict[str, Any], code: Any, rows: dict[str, Any], limits: dict[str, int],
) -> dict[str, list[PauliMatchedPairV1]]:
    pairs: dict[str, list[PauliMatchedPairV1]] = {point: [] for point in preflight["point_order"]}
    seen: set[str] = set()
    for point_id in preflight["point_order"]:
        lower, upper = preflight["sample_ranges"][point_id]
        for sample_id in range(lower, upper + 1):
            path = _phase11_pair_path(output_root, point_id, sample_id)
            if path.is_symlink() or not path.is_file():
                continue
            pair = PauliMatchedPairV1.model_validate_json(path.read_bytes())
            pair.verify_replay()
            sample, expected_pair = _phase11_expected_pair(
                code=code, rows=rows, limits=limits, preflight=preflight, point_id=point_id, sample_id=sample_id,
            )
            if (
                pair.physical_sample_identity != sample.physical_sample_identity
                or pair.physical_error_sha256 != sample.physical_error_sha256
                or pair.materialized_sample_sha256 != sample.materialized_sample_sha256
            ):
                raise ValueError("controlled pair does not bind the deterministic materialized sample")
            if _phase11_pair_semantics(pair) != _phase11_pair_semantics(expected_pair):
                raise ValueError("controlled pair deterministic arm evidence differs from replay")
            if pair.physical_sample_identity in seen:
                raise ValueError("controlled pair output duplicates a physical sample")
            seen.add(pair.physical_sample_identity)
            pairs[point_id].append(pair)
    return pairs


def _phase11_shard_ranges(preflight: dict[str, Any], shard: tuple[str, int, int] | None) -> dict[str, tuple[int, int]]:
    declared = {point: tuple(bounds) for point, bounds in preflight["sample_ranges"].items()}
    if shard is None:
        return declared
    point_id, lower, upper = shard
    if point_id not in declared or type(lower) is not int or type(upper) is not int:
        raise ValueError("controlled shard must name one declared point and integer range")
    start, end = declared[point_id]
    # An inverted in-bounds interval is a valid empty shard; it writes no pair.
    if lower > upper:
        if not (start <= upper + 1 <= lower <= end + 1):
            raise ValueError("empty controlled shard must lie at a declared range boundary")
        return {point_id: (lower, upper)}
    if not (start <= lower <= upper <= end):
        raise ValueError("controlled shard escapes its declared deterministic range")
    return {point_id: (lower, upper)}


def run_phase11_controlled(*, root: Path, design_path: Path, output_root: Path, resume: bool = False,
                           shard: tuple[str, int, int] | None = None) -> dict[str, Any]:
    """Run or resume only the predeclared bounded GB46 calibration pairs."""
    preflight = preflight_phase11_controlled_design(root=root, design_path=design_path)
    destination = _phase11_safe_root(output_root)
    identity = {"schema": "phase11_controlled_identity_v1", "preflight": preflight}
    _phase11_publish_exact(destination, ("identity.json",), _json_line(identity))
    code, rows, limits = _phase11_execution_context(root=root, design_path=design_path, preflight=preflight)
    completed = 0
    shard_ranges = _phase11_shard_ranges(preflight, shard)
    for point_id in preflight["point_order"]:
        if point_id not in shard_ranges:
            continue
        probabilities = rows[point_id].probabilities
        lower, upper = shard_ranges[point_id]
        for sample_id in range(lower, upper + 1):
            path = _phase11_pair_path(destination, point_id, sample_id)
            if path.exists() or path.is_symlink():
                if not resume:
                    existing = PauliMatchedPairV1.model_validate_json(path.read_bytes())
                    expected = _phase11_sample(code=code, design_sha256=preflight["design_sha256"], point_id=point_id,
                                               sample_id=sample_id, probabilities=probabilities)
                    if existing.physical_sample_identity != expected.physical_sample_identity:
                        raise ValueError("existing controlled pair has a changed sample identity")
                continue
            _sample, pair = _phase11_expected_pair(
                code=code, rows=rows, limits=limits, preflight=preflight, point_id=point_id, sample_id=sample_id,
            )
            _phase11_publish_exact(destination, ("pairs", point_id, f"{sample_id}.json"), pair.primitive_bytes() + b"\n")
            completed += 1
    # A partial shard is deliberately not assessed or presented as complete.
    if set(shard_ranges) != set(preflight["point_order"]) or any(
        list(shard_ranges[point]) != preflight["sample_ranges"][point] for point in shard_ranges
    ):
        return {"schema": "phase11_controlled_shard_v1", "new_pairs": completed,
                "shard": shard, "assessment_status": "incomplete_shard", "publication_authorization": "deny"}
    verified = verify_phase11_controlled(root=root, design_path=design_path, output_root=destination)
    return {"schema": "phase11_controlled_run_v1", "new_pairs": completed, **verified}


def verify_phase11_controlled(*, root: Path, design_path: Path, output_root: Path) -> dict[str, Any]:
    """Fail closed on missing, altered, duplicate, or cross-design pair evidence."""
    preflight = preflight_phase11_controlled_design(root=root, design_path=design_path)
    destination = _phase11_safe_root(output_root)
    identity_path = destination / "identity.json"
    if identity_path.is_symlink() or not identity_path.is_file() or identity_path.read_bytes() != _json_line({"schema": "phase11_controlled_identity_v1", "preflight": preflight}):
        raise ValueError("controlled output identity differs from the admitted design")
    code, rows, limits = _phase11_execution_context(root=root, design_path=design_path, preflight=preflight)
    pairs = _phase11_load_pairs(output_root=destination, preflight=preflight, code=code, rows=rows, limits=limits)
    expected = sum(upper - lower + 1 for lower, upper in preflight["sample_ranges"].values())
    actual = sum(len(value) for value in pairs.values())
    if actual != expected:
        raise ValueError("controlled output lacks one or more complete matched pairs")
    failures = {"joint": 0, "separate": 0}
    work: dict[str, int] = {}
    arm_runtime_ns = {"joint": 0, "separate": 0}
    component_runtime_ns = {"X": 0, "Z": 0}
    timing_boundaries: set[str] = set()
    terminals: dict[str, int] = {}
    for point_pairs in pairs.values():
        for pair in point_pairs:
            for arm in (pair.joint, pair.separate):
                failures[arm.arm_id] += int(arm.all_shot == "failure")
                terminals[f"{arm.arm_id}:{arm.terminal_status}"] = terminals.get(f"{arm.arm_id}:{arm.terminal_status}", 0) + 1
                for name, amount in arm.work.items():
                    key = f"{arm.arm_id}:{name}"
                    work[key] = work.get(key, 0) + amount
                if arm.runtime_ns is None or arm.timing_boundary is None:
                    raise ValueError("controlled verification requires typed arm runtime evidence")
                arm_runtime_ns[arm.arm_id] += arm.runtime_ns
                timing_boundaries.add(arm.timing_boundary)
            for component in pair.components:
                if component.runtime_ns is None or component.timing_boundary is None:
                    raise ValueError("controlled verification requires typed binary component runtime evidence")
                component_runtime_ns[component.component] += component.runtime_ns
                timing_boundaries.add(component.timing_boundary)
    if timing_boundaries != {"decoder_callback_wall_v1"}:
        raise ValueError("controlled verification requires one disclosed decoder timing boundary")
    return {"schema": "phase11_controlled_verify_v1", "design_sha256": preflight["design_sha256"],
            "complete_pairs": actual, "paired_denominators": {point: len(values) for point, values in pairs.items()},
            "arm_failures": failures, "terminal_status_counts": dict(sorted(terminals.items())),
            "arm_work": dict(sorted(work.items())), "arm_runtime_ns": arm_runtime_ns,
            "component_runtime_ns": component_runtime_ns, "timing_boundary": "decoder_callback_wall_v1",
            "publication_authorization": "deny"}


def replay_phase11_controlled(*, root: Path, design_path: Path, output_root: Path) -> dict[str, Any]:
    """Recompute pair identities and records, rejecting any nondeterministic output."""
    verified = verify_phase11_controlled(root=root, design_path=design_path, output_root=output_root)
    preflight = preflight_phase11_controlled_design(root=root, design_path=design_path)
    code, rows, limits = _phase11_execution_context(root=root, design_path=design_path, preflight=preflight)
    pairs = _phase11_load_pairs(output_root=output_root, preflight=preflight, code=code, rows=rows, limits=limits)
    for point_id, values in pairs.items():
        for pair in values:
            sample_id = next(
                sample_id for sample_id in range(preflight["sample_ranges"][point_id][0], preflight["sample_ranges"][point_id][1] + 1)
                if _phase11_sample(code=code, design_sha256=preflight["design_sha256"], point_id=point_id,
                                   sample_id=sample_id, probabilities=rows[point_id].probabilities).physical_sample_identity == pair.physical_sample_identity
            )
            expected, _pair = _phase11_expected_pair(
                code=code, rows=rows, limits=limits, preflight=preflight, point_id=point_id, sample_id=sample_id,
            )
            if expected.materialized_sample_sha256 != pair.materialized_sample_sha256:
                raise ValueError("controlled replay sample differs from retained pair")
    return {"schema": "phase11_controlled_replay_v1", **verified}


def assess_phase11_controlled(*, root: Path, design_path: Path, output_root: Path) -> dict[str, Any]:
    """Produce the fixed-design assessment only from verified complete pairs."""
    from .statistics import assess_correlation_sweep
    verify_phase11_controlled(root=root, design_path=design_path, output_root=output_root)
    preflight = preflight_phase11_controlled_design(root=root, design_path=design_path)
    code, rows, limits = _phase11_execution_context(root=root, design_path=design_path, preflight=preflight)
    result = assess_correlation_sweep(
        design_path=root / "data/studies/phase11-fixed-marginal-design.json",
        point_pairs=_phase11_load_pairs(output_root=output_root, preflight=preflight, code=code, rows=rows, limits=limits),
    )
    payload = {"schema": "phase11_controlled_assessment_v1", "publication_authorization": "deny",
               "assessment": {"design_sha256": result.design_sha256,
                              "rows": [{"point_id": row.point_id, "d_y": row.d_y,
                                        "complete_pairs": row.complete_pairs} for row in result.rows]}}
    _phase11_publish_exact(_phase11_safe_root(output_root), ("assessment.json",), _json_line(payload))
    return payload
