"""One sealed MBBP member set feeding the declared list and vote arms."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter_ns
import tomllib
from types import SimpleNamespace
from typing import Any

import numpy as np

from ..artifacts import load_artifact
from ..canonical.lineage import stable_lineage_id
from ..canonical.mbbp import MbbpBasis, MbbpController, MbbpSpec
from ..canonical.phase6 import execute_declared_mbbp_decision
from ..canonical.problems import OriginalProblem
from .contracts import MaterializedPhysicalSampleV1
from .controlled import ControlledArmReceiptV1, SharedMBBPMemberSetReceiptV1
from .controlled_execution import _component, _json_line, _publish_exact, _receipt_with_bytes, _validated_terminal
from .execution import _shot_from_materialized, _work_manifest_path, materialize_campaign_sample
from .planning import CampaignWorkPlan, UnitKey


def _policy(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    relative = manifest["policy_path"]
    path = _work_manifest_path(root, relative, manifest["policy_sha256"])
    document = tomllib.loads(path.read_text())
    ensemble = document["ensemble"]
    if (ensemble["kind"] != "mbbp_ld" or ensemble["source_status"] != "canonical_adaptation"
            or document["update"]["kind"] != "normalized_min_sum"
            or document["schedule"]["kind"] != "check_node_serial"
            or document["update"]["parameter_assignment"] != {"shape": "scalar", "value": 0.875}):
        raise ValueError("controlled MBBP policy has an unsupported mechanism")
    for item in ensemble["bases"]:
        if item["transform_kind"] != "one_hot_original_check_rows":
            raise ValueError("controlled MBBP requires one-hot original check rows")
    if len(ensemble["bases"]) != ensemble["max_total_members"]:
        raise ValueError("controlled MBBP member count differs from declared ensemble")
    return document


def _arm(root: Path, plan: CampaignWorkPlan, unit: UnitKey, supplied: dict[str, Any]):
    arm = next((item for item in plan.work_spec.arms if item.arm_id == unit.arm_id), None)
    if arm is None:
        raise ValueError("controlled MBBP arm is absent from frozen work")
    path = _work_manifest_path(root, arm.manifest_path, arm.manifest_sha256)
    if json.loads(path.read_bytes()) != supplied:
        raise ValueError("controlled MBBP arm manifest differs from frozen bytes")
    return arm


def _spec_for_original(document: dict[str, Any], check_count: int) -> MbbpSpec:
    ensemble = document["ensemble"]
    bases = []
    for item in ensemble["bases"]:
        transforms = []
        for row in item["source_rows"]:
            if type(row) is not int or row < 0 or row >= check_count:
                raise ValueError("controlled MBBP source row is outside original checks")
            transforms.append(tuple(int(index == row) for index in range(check_count)))
        bases.append(MbbpBasis(
            item["member_id"], item["local_ordinal"], item["partition_identity"],
            item["permutation_identity"], tuple(transforms),
        ))
    return MbbpSpec(tuple(bases), max_iterations=ensemble["max_iterations"],
                    max_member_c2v_updates=ensemble["max_member_c2v_updates"])


def _original(code: Any, sample: Any, unit: UnitKey) -> OriginalProblem:
    lineage = stable_lineage_id("original", {"physical_sample_identity": unit.physical_sample_identity,
                                             "sample_id": unit.sample_id})
    return OriginalProblem(lineage.value, code.hx, code.hz, sample.observation.syndrome)


def _shared_path(root: Path, unit: UnitKey) -> Path:
    return root / "shared" / f"{unit.physical_sample_identity}.json"


def _load_shared(root: Path, unit: UnitKey, original: OriginalProblem) -> SharedMBBPMemberSetReceiptV1:
    path = _shared_path(root, unit)
    if path.is_symlink() or not path.is_file():
        raise ValueError("controlled MBBP shared member receipt is missing")
    raw = path.read_bytes()
    receipt = SharedMBBPMemberSetReceiptV1.model_validate_json(raw)
    if (raw != receipt.primitive_bytes() + b"\n"
            or receipt.sample_identity != unit.physical_sample_identity
            or receipt.sample_id != unit.sample_id):
        raise ValueError("controlled MBBP shared member bytes differ from frozen sample")
    receipt.to_result(original)
    return receipt


def _produce_shared(
    *, root: Path, unit: UnitKey, original: OriginalProblem, policy: dict[str, Any],
    error_rate: float, provenance: str,
) -> SharedMBBPMemberSetReceiptV1:
    spec = _spec_for_original(policy, original.hz.shape[0])
    starts: dict[str, int] = {}
    runtimes: dict[str, int] = {}

    def observe(boundary: str, _work: Any, _leaf: str | None) -> None:
        parts = boundary.split(":")
        if len(parts) == 3 and parts[0] == "mbbp":
            if parts[2] == "before_member":
                starts[parts[1]] = perf_counter_ns()
            elif parts[2] == "after_member":
                runtimes[parts[1]] = perf_counter_ns() - starts[parts[1]]

    result = MbbpController(spec).run(original, error_rate=error_rate, boundary_observer=observe)
    rows = [_json_line({"schema": "controlled_event_v1", "kind": "mbbp_member",
                        "physical_sample_identity": unit.physical_sample_identity,
                        "member": member.as_evidence()}) for member in result.members]
    rows.append(_json_line({"schema": "controlled_event_v1", "kind": "mbbp_selection",
                            "physical_sample_identity": unit.physical_sample_identity,
                            "selection": result.selection.as_evidence()}))
    event_bytes = b"".join(rows)
    _publish_exact(root / "events" / f"shared-{unit.physical_sample_identity}.jsonl", event_bytes)
    components = []
    for index, member in enumerate(result.members):
        component = _component(
            component_id=member.member_id, role="mbbp_member", source_status="canonical_adaptation",
            converged=member.converged, iterations=0,
            configured={"max_iterations": spec.max_iterations,
                        "max_member_c2v_updates": spec.max_member_c2v_updates or 0},
            work=member.work.as_evidence(structural_event_version=4),
            runtime_ns=runtimes[member.member_id], events=1,
            evidence_bytes=len(rows[index]) + (len(rows[-1]) if index == 0 else 0),
            storage_bytes=len(rows[index]) + (len(rows[-1]) if index == 0 else 0),
            provenance_sha256=provenance,
        )
        component = component.model_copy(update={
            "iterations": component.iterations.model_copy(update={
                "status": "unavailable", "value": None,
                "reason": "member iteration count is absent from the canonical MBBP terminal",
            }),
        })
        components.append(component)
    for _ in range(8):
        receipt = SharedMBBPMemberSetReceiptV1.from_result(
            sample_identity=unit.physical_sample_identity, sample_id=unit.sample_id,
            original_lineage_id=original.lineage_id, result=result, components=tuple(components))
        amount = len(receipt.primitive_bytes()) + 1
        first = components[0]
        updated = first.model_copy(update={"storage_bytes": first.storage_bytes.model_copy(update={
            "value": first.evidence_bytes.value + amount})})
        if updated.storage_bytes.value == first.storage_bytes.value:
            break
        components[0] = updated
    else:
        raise ValueError("controlled MBBP shared receipt size did not stabilize")
    _publish_exact(_shared_path(root, unit), receipt.primitive_bytes() + b"\n")
    return receipt


def run_mbbp_controlled_unit(
    *, plan: CampaignWorkPlan, unit: UnitKey, arm_manifest: dict[str, Any],
    campaign_root: Path, output_root: Path,
) -> ControlledArmReceiptV1:
    if (unit.key not in plan.unit_keys or unit.arm_id not in {"list", "vote"}
            or arm_manifest.get("runner") != "controlled_shared_mbbp_v1"
            or arm_manifest.get("arm_id") != unit.arm_id):
        raise ValueError("controlled MBBP unit differs from frozen work")
    arm = _arm(campaign_root, plan, unit, arm_manifest)
    policy = _policy(campaign_root, arm_manifest)
    loaded = load_artifact(campaign_root, arm_manifest["artifact_path"],
                           expected_raw_sha256=arm_manifest["artifact_raw_sha256"],
                           expected_semantic_sha256=arm_manifest["artifact_semantic_sha256"])
    materialized = materialize_campaign_sample(
        plan=plan, unit=unit, spec=plan.work_spec, context=SimpleNamespace(code=loaded.code),
        destination=output_root / "samples" / f"{unit.physical_sample_identity}.json")
    sample = _shot_from_materialized(materialized)
    original = _original(loaded.code, sample, unit)
    shared = (_produce_shared(root=output_root, unit=unit, original=original, policy=policy,
                              error_rate=plan.work_spec.shared_sampler.x_error_rate,
                              provenance=arm.manifest_sha256)
              if unit.arm_id == "list" else _load_shared(output_root, unit, original))
    result = shared.to_result(original)
    vote_bit = None if unit.arm_id == "list" else policy["vote"]["tie_bit"]
    started = perf_counter_ns()
    decision = execute_declared_mbbp_decision(original, result=result, vote_tie_bit=vote_bit)
    decision_ns = perf_counter_ns() - started
    candidate = None if decision.selected_candidate is None else np.asarray(decision.selected_candidate, dtype=np.uint8)
    started = perf_counter_ns()
    terminal = _validated_terminal(loaded.code, sample.hidden.x, candidate)
    validation_ns = perf_counter_ns() - started
    decision_event = _json_line({"schema": "controlled_event_v1", "kind": unit.arm_id,
                                 "unit_key": unit.key, "shared_input_receipt_sha256": shared.digest(),
                                 "decision": decision.as_evidence()})
    validation_event = _json_line({"schema": "controlled_event_v1", "kind": "original_validation",
                                   "unit_key": unit.key, "terminal_status": terminal,
                                   "candidate": None if candidate is None else candidate.tolist(),
                                   "physical_sample_identity": unit.physical_sample_identity})
    event_bytes = decision_event + validation_event
    _publish_exact(output_root / "events" / f"{unit.key}.jsonl", event_bytes)
    component = _component(
        component_id=unit.arm_id, role=f"{unit.arm_id}_decision", source_status="canonical_adaptation",
        converged=None, iterations=None, configured={"decision_calls": 1},
        work={"decision_calls": 1}, runtime_ns=decision_ns, events=1,
        evidence_bytes=len(decision_event), storage_bytes=len(decision_event),
        provenance_sha256=arm.manifest_sha256,
        shared_input_receipt_sha256=shared.digest())
    validation = _component(
        component_id=f"{unit.arm_id}:original_validation", role="original_validation",
        source_status="canonical_adaptation", converged=None, iterations=None,
        configured={"original_checks": 1}, work={"original_checks": int(candidate is not None)},
        runtime_ns=validation_ns, events=1, evidence_bytes=len(validation_event),
        storage_bytes=len(validation_event), provenance_sha256=arm.manifest_sha256)
    receipt = _receipt_with_bytes(payload={
        "schema": "controlled_arm_receipt_v1", "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest, "unit_key": unit.key,
        "physical_sample_identity": unit.physical_sample_identity, "sample_id": unit.sample_id,
        "arm_id": unit.arm_id, "materialized_sample_sha256": materialized.materialized_sample_sha256,
        "shared_input_receipt_sha256": shared.digest(), "shared_component_sha256": None,
        "validation_component": validation,
        "candidate": None if candidate is None else tuple(int(bit) for bit in candidate),
        "terminal_status": terminal, "event_ledger_sha256": sha256(event_bytes).hexdigest(),
        "event_ledger_bytes": len(event_bytes),
    }, component=component)
    _publish_exact(output_root / "units" / f"{unit.key}.json", receipt.primitive_bytes() + b"\n")
    return receipt


def verify_mbbp_controlled_unit(
    *, plan: CampaignWorkPlan, unit: UnitKey, arm_manifest: dict[str, Any],
    campaign_root: Path, output_root: Path,
) -> ControlledArmReceiptV1:
    """Reconstruct both decisions and truth evaluation from sealed member bytes."""
    paths = (output_root / "units" / f"{unit.key}.json",
             output_root / "samples" / f"{unit.physical_sample_identity}.json",
             output_root / "events" / f"{unit.key}.jsonl")
    if any(path.is_symlink() or not path.is_file() for path in paths):
        raise ValueError("controlled MBBP unit lacks sealed evidence")
    raw = paths[0].read_bytes()
    receipt = ControlledArmReceiptV1.model_validate_json(raw)
    sample_raw = paths[1].read_bytes()
    sample_record = MaterializedPhysicalSampleV1.model_validate_json(sample_raw)
    if sample_raw != sample_record.primitive_bytes() + b"\n":
        raise ValueError("controlled MBBP physical sample has noncanonical bytes")
    if (raw != receipt.primitive_bytes() + b"\n" or receipt.unit_key != unit.key
            or receipt.campaign_spec_digest != plan.campaign_spec_digest
            or receipt.campaign_plan_digest != plan.campaign_plan_digest
            or receipt.arm_id != unit.arm_id
            or receipt.physical_sample_identity != unit.physical_sample_identity
            or receipt.sample_id != unit.sample_id
            or receipt.materialized_sample_sha256 != sample_record.materialized_sample_sha256
            or sample_record.sampler_contract_sha256 != plan.work_spec.shared_sampler.digest()):
        raise ValueError("controlled MBBP arm or sample differs from frozen plan")
    _arm(campaign_root, plan, unit, arm_manifest)
    policy = _policy(campaign_root, arm_manifest)
    loaded = load_artifact(campaign_root, arm_manifest["artifact_path"],
                           expected_raw_sha256=arm_manifest["artifact_raw_sha256"],
                           expected_semantic_sha256=arm_manifest["artifact_semantic_sha256"])
    sample = _shot_from_materialized(sample_record)
    original = _original(loaded.code, sample, unit)
    shared = _load_shared(output_root, unit, original)
    result = shared.to_result(original)
    if (tuple(shared.member_ids) != tuple(item.member_id for item in _spec_for_original(policy, original.hz.shape[0]).bases)
            or receipt.shared_input_receipt_sha256 != shared.digest()):
        raise ValueError("controlled MBBP member order or input digest changed")
    shared_event = output_root / "events" / f"shared-{unit.physical_sample_identity}.jsonl"
    if shared_event.is_symlink() or not shared_event.is_file():
        raise ValueError("controlled MBBP member events are missing")
    shared_rows = [json.loads(line) for line in shared_event.read_bytes().splitlines()]
    if ([row.get("kind") for row in shared_rows] != ["mbbp_member"] * len(shared.member_ids) + ["mbbp_selection"]
            or [row.get("member") for row in shared_rows[:-1]] != result.as_evidence()["members"]
            or shared_rows[-1].get("selection") != result.selection.as_evidence()):
        raise ValueError("controlled MBBP member events differ from sealed result")
    for index, component in enumerate(shared.components):
        expected_bytes = len(_json_line(shared_rows[index])) + (len(_json_line(shared_rows[-1])) if index == 0 else 0)
        expected_storage = expected_bytes + (len(shared.primitive_bytes()) + 1 if index == 0 else 0)
        if (component.evidence_bytes.value != expected_bytes or component.storage_bytes.value != expected_storage
                or component.actual_work != result.members[index].work.as_evidence(structural_event_version=4)):
            raise ValueError("controlled MBBP member cost differs from sealed events")
    event_bytes = paths[2].read_bytes()
    rows = [json.loads(line) for line in event_bytes.splitlines()]
    decision = execute_declared_mbbp_decision(
        original, result=result, vote_tie_bit=None if unit.arm_id == "list" else policy["vote"]["tie_bit"])
    candidate = None if decision.selected_candidate is None else np.asarray(decision.selected_candidate, dtype=np.uint8)
    terminal = _validated_terminal(loaded.code, sample.hidden.x, candidate)
    if (event_bytes != b"".join(_json_line(row) for row in rows)
            or len(rows) != 2 or [row.get("kind") for row in rows] != [unit.arm_id, "original_validation"]
            or rows[0].get("decision") != decision.as_evidence()
            or rows[0].get("shared_input_receipt_sha256") != shared.digest()
            or rows[1].get("terminal_status") != terminal
            or rows[1].get("candidate") != (None if candidate is None else candidate.tolist())
            or receipt.terminal_status != terminal
            or receipt.candidate != (None if candidate is None else tuple(int(bit) for bit in candidate))
            or receipt.event_ledger_sha256 != sha256(event_bytes).hexdigest()
            or receipt.event_ledger_bytes != len(event_bytes)):
        raise ValueError("controlled MBBP decision differs from independent reconstruction")
    component = receipt.component
    if (component is None or component.shared_input_receipt_sha256 != shared.digest()
            or component.evidence_bytes.value != len(_json_line(rows[0]))
            or component.storage_bytes.value != len(_json_line(rows[0])) + len(raw)
            or component.actual_work != {"decision_calls": 1}
            or receipt.validation_component.evidence_bytes.value != len(_json_line(rows[1]))
            or receipt.validation_component.storage_bytes.value != len(_json_line(rows[1]))
            or receipt.validation_component.actual_work != {"original_checks": int(candidate is not None)}):
        raise ValueError("controlled MBBP decision cost differs from retained bytes")
    return receipt
