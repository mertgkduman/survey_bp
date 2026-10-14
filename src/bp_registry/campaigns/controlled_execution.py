"""Local, receipt-first controlled CSS arm execution.

Each continuation consumes a sealed shared input.  A later invocation can
therefore resume the missing arm without repeating initial BP.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from time import perf_counter_ns
from types import SimpleNamespace
from typing import Any, Callable, Literal

import numpy as np

from ..artifacts import load_artifact
from ..canonical.fair_legs import FairLegConfig, FairLegController
from ..evaluator import evaluate_candidate
from ..manifests import StrictModel
from .contracts import (
    BinaryComponentTerminalV1, MaterializedPhysicalSampleV1, PauliMatchedArmV1,
    PauliMatchedPairV1, canonical_json_bytes,
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


class BinaryArmResultV1(StrictModel):
    candidate: tuple[int, ...] | None = None
    terminal_status: Literal[
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
        "infrastructure_interruption",
    ]
    iterations: int = 0
    work: dict[str, int]


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
        result = run_canonical_materialized_one(
            manifest_paths[input_.component], sample=_shot_from_materialized(materialized_sample),
            materialized_sample_sha256=input_.materialized_sample_sha256, ledger_path=ledger_path,
        )
        if isinstance(result, CanonicalMaterializedRunV1):
            if result.status == "interrupted":
                return BinaryArmResultV1(candidate=None, terminal_status="infrastructure_interruption", iterations=0,
                                         work={"canonical_iterations": 0})
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
            work={"canonical_iterations": int(getattr(result, "iterations", 0))},
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
                                  iterations=x_result.iterations, work=x_result.work, syndrome_sha256=_syndrome_digest(expected_z)),
        BinaryComponentTerminalV1(component="Z", candidate=z_result.candidate, terminal_status=z_result.terminal_status,
                                  iterations=z_result.iterations, work=z_result.work, syndrome_sha256=_syndrome_digest(expected_x)),
    )
    joint_evaluation = _arm_evaluation(code=validated, true_x=true_x, true_z=true_z,
                                       candidate_x=joint_result.candidate_x, candidate_z=joint_result.candidate_z)
    separate_evaluation = _arm_evaluation(code=validated, true_x=true_x, true_z=true_z,
                                          candidate_x=x_result.candidate, candidate_z=z_result.candidate)
    joint = PauliMatchedArmV1(
        arm_id="joint", materialized_sample_sha256=materialized_sample.materialized_sample_sha256,
        candidate_x=joint_result.candidate_x, candidate_z=joint_result.candidate_z,
        terminal_status=(joint_result.terminal_status if joint_evaluation["outcome"] == "no_proposal" else joint_evaluation["outcome"]),
        evaluation=joint_evaluation, work=dict(joint_result.work),
    )
    separate_status = ("nonconvergence" if any(item.terminal_status == "nonconvergence" for item in components)
                       else separate_evaluation["outcome"])
    separate = PauliMatchedArmV1(
        arm_id="separate", materialized_sample_sha256=materialized_sample.materialized_sample_sha256,
        candidate_x=x_result.candidate, candidate_z=z_result.candidate,
        terminal_status=separate_status, evaluation=separate_evaluation,
        work={f"{component.component.lower()}_{name}": amount for component in components for name, amount in component.work.items()},
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
