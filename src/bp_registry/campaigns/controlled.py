"""Typed, content-bound evidence for matched controlled CSS components."""

from __future__ import annotations

from hashlib import sha256
import math
from typing import Any, Literal

import numpy as np
from pydantic import Field, StrictBool, StrictInt, field_validator, model_validator

from ..manifests import StrictModel
from .contracts import canonical_json_bytes


_SHA256 = r"^[0-9a-f]{64}$"
_MissingStatus = Literal["observed", "not_applicable", "unavailable"]


class ControlledBooleanV1(StrictModel):
    status: _MissingStatus
    value: StrictBool | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def exact_status(self) -> "ControlledBooleanV1":
        if self.status == "observed":
            if self.value is None or self.reason is not None:
                raise ValueError("observed Boolean requires a value without a missingness reason")
        elif self.value is not None or self.reason is None:
            raise ValueError("missing Boolean requires a reason and no value")
        return self


class ControlledCountV1(StrictModel):
    status: _MissingStatus
    value: StrictInt | None = Field(default=None, ge=0, le=2**63 - 1)
    reason: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def exact_status(self) -> "ControlledCountV1":
        if self.status == "observed":
            if self.value is None or self.reason is not None:
                raise ValueError("observed count requires a value without a missingness reason")
        elif self.value is not None or self.reason is None:
            raise ValueError("missing count requires a reason and no value")
        return self


class ControlledTextV1(StrictModel):
    status: _MissingStatus
    value: str | None = Field(default=None, min_length=1, max_length=512)
    reason: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def exact_status(self) -> "ControlledTextV1":
        if self.status == "observed":
            if self.value is None or self.reason is not None:
                raise ValueError("observed text requires a value without a missingness reason")
        elif self.value is not None or self.reason is None:
            raise ValueError("missing text requires a reason and no value")
        return self


class ControlledComponentEvidenceV1(StrictModel):
    """A single producer's status, effort, and scoped resource facts."""

    schema_name: Literal["controlled_component_evidence_v1"] = Field(alias="schema", serialization_alias="schema")
    component_id: str = Field(min_length=1, max_length=256)
    role: Literal[
        "initial_bp", "relay", "beam", "spa_flooding", "spa_check_node_serial",
        "mbbp_member", "list_decision", "vote_decision", "original_validation",
    ]
    source_status: Literal["controlled_css_adaptation", "canonical_adaptation"]
    convergence_status: ControlledBooleanV1
    iterations: ControlledCountV1
    configured_limits: dict[str, StrictInt] = Field(min_length=1, max_length=128)
    actual_work: dict[str, StrictInt] = Field(min_length=1, max_length=128)
    runtime_ns: ControlledCountV1
    peak_rss_bytes: ControlledCountV1
    events: ControlledCountV1
    evidence_bytes: ControlledCountV1
    storage_bytes: ControlledCountV1
    interruption: ControlledTextV1
    provenance_sha256: str = Field(pattern=_SHA256)
    shared_input_receipt_sha256: str | None = Field(default=None, pattern=_SHA256)

    @model_validator(mode="after")
    def coherent_component(self) -> "ControlledComponentEvidenceV1":
        if any(type(value) is not int or value < 0 for value in self.configured_limits.values()):
            raise ValueError("configured limits must be nonnegative integers")
        if any(type(value) is not int or value < 0 for value in self.actual_work.values()):
            raise ValueError("actual work must be nonnegative integers")
        decision = self.role in {"list_decision", "vote_decision"}
        if decision and (self.convergence_status.status != "not_applicable"
                         or self.iterations.status != "not_applicable"):
            raise ValueError("list/vote decisions do not have BP convergence or iterations")
        if self.role in {"relay", "beam", "list_decision", "vote_decision"} and self.shared_input_receipt_sha256 is None:
            raise ValueError("continuation or decision requires a shared input receipt")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return sha256(b"bp-registry-controlled-component-v1\0" + self.primitive_bytes()).hexdigest()


class FairInitialStateV1(StrictModel):
    """Complete decoder-visible initial state, including edge messages."""

    candidate: tuple[StrictInt, ...] = Field(min_length=1)
    posterior: tuple[float, ...] = Field(min_length=1)
    sum_llr: tuple[float, ...] = Field(min_length=1)
    edge_messages: tuple[tuple[StrictInt, StrictInt, float], ...]
    unmasked: tuple[StrictInt, ...]
    fixed: tuple[tuple[StrictInt, StrictInt], ...]
    iterations: StrictInt = Field(ge=0, le=2**63 - 1)
    converged: StrictBool
    work: dict[str, StrictInt] = Field(min_length=1)
    stage_id: str = Field(min_length=1, max_length=256)

    @field_validator("candidate", "posterior", "sum_llr", "edge_messages", "unmasked", "fixed", mode="before")
    @classmethod
    def tuple_sequences(cls, value: Any) -> Any:
        return tuple(tuple(item) if isinstance(item, list) else item for item in value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def valid_state(self) -> "FairInitialStateV1":
        from dataclasses import fields
        from ..canonical.budgets import WorkVector

        n = len(self.candidate)
        if (len(self.posterior) != n or len(self.sum_llr) != n
                or any(value not in (0, 1) for value in self.candidate)
                or any(not math.isfinite(value) for value in (*self.posterior, *self.sum_llr))):
            raise ValueError("initial state has invalid candidate or posterior dimensions")
        if any(variable < 0 or variable >= n for variable in self.unmasked):
            raise ValueError("initial state has an invalid unmasked variable")
        if any(variable < 0 or variable >= n or bit not in (0, 1) for variable, bit in self.fixed):
            raise ValueError("initial state has an invalid fixed variable")
        if any(check < 0 or variable < 0 or variable >= n or not math.isfinite(message)
               for check, variable, message in self.edge_messages):
            raise ValueError("initial state has an invalid edge message")
        names = {item.name for item in fields(WorkVector)}
        if set(self.work) != names:
            raise ValueError("initial state work vector must contain every V4 dimension")
        WorkVector(**self.work)
        return self

    def to_segment(self):
        from ..canonical.budgets import WorkVector
        from ..canonical.fair_legs import BPSegment

        return BPSegment(
            candidate=np.asarray(self.candidate, dtype=np.uint8),
            posterior=np.asarray(self.posterior, dtype=np.float64),
            sum_llr=np.asarray(self.sum_llr, dtype=np.float64),
            edge_messages=self.edge_messages, unmasked=self.unmasked,
            fixed=self.fixed, iterations=self.iterations, converged=self.converged,
            work=WorkVector(**self.work), stage_id=self.stage_id,
        )


class SharedInitialBPReceiptV1(StrictModel):
    """One sealed initial BP state consumed by baseline, Relay, and Beam."""

    schema_name: Literal["shared_initial_bp_receipt_v1"] = Field(alias="schema", serialization_alias="schema")
    sample_identity: str = Field(pattern=_SHA256)
    sample_id: StrictInt = Field(ge=0, le=1_000_000)
    component: ControlledComponentEvidenceV1
    state: FairInitialStateV1

    @model_validator(mode="after")
    def component_matches_state(self) -> "SharedInitialBPReceiptV1":
        if (self.component.role != "initial_bp"
                or self.state.stage_id != "initial-bp"
                or self.component.component_id != self.state.stage_id
                or self.component.iterations.status != "observed"
                or self.component.iterations.value != self.state.iterations
                or self.component.convergence_status.status != "observed"
                or self.component.convergence_status.value != self.state.converged
                or any(self.state.work.get(name) != amount for name, amount in self.component.actual_work.items())):
            raise ValueError("shared initial component differs from decoder-visible state")
        return self

    @classmethod
    def from_segment(
        cls, *, sample_identity: str, sample_id: int,
        component: ControlledComponentEvidenceV1 | dict[str, Any], segment: Any,
    ) -> "SharedInitialBPReceiptV1":
        from ..canonical.fair_legs import BPSegment

        if not isinstance(segment, BPSegment):
            raise ValueError("shared initial receipt requires one BPSegment")
        state = {
            "candidate": tuple(int(value) for value in segment.candidate),
            "posterior": tuple(float(value) for value in segment.posterior),
            "sum_llr": tuple(float(value) for value in segment.sum_llr),
            "edge_messages": segment.edge_messages,
            "unmasked": segment.unmasked, "fixed": segment.fixed,
            "iterations": segment.iterations, "converged": segment.converged,
            "work": segment.work.as_evidence(structural_event_version=4),
            "stage_id": segment.stage_id,
        }
        return cls.model_validate({"schema": "shared_initial_bp_receipt_v1",
                                   "sample_identity": sample_identity, "sample_id": sample_id,
                                   "component": component, "state": state})

    def to_segment(self):
        return self.state.to_segment()

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return sha256(b"bp-registry-shared-initial-bp-v1\0" + self.primitive_bytes()).hexdigest()


class ControlledArmReceiptV1(StrictModel):
    """One frozen arm terminal, with shared computation and validation separate."""

    schema_name: Literal["controlled_arm_receipt_v1"] = Field(alias="schema", serialization_alias="schema")
    campaign_spec_digest: str = Field(pattern=_SHA256)
    campaign_plan_digest: str = Field(pattern=_SHA256)
    unit_key: str = Field(pattern=_SHA256)
    physical_sample_identity: str = Field(pattern=_SHA256)
    sample_id: StrictInt = Field(ge=0, le=1_000_000)
    arm_id: str = Field(min_length=1, max_length=128)
    materialized_sample_sha256: str = Field(pattern=_SHA256)
    shared_input_receipt_sha256: str | None = Field(default=None, pattern=_SHA256)
    shared_component_sha256: str | None = Field(default=None, pattern=_SHA256)
    component: ControlledComponentEvidenceV1 | None = None
    validation_component: ControlledComponentEvidenceV1
    candidate: tuple[StrictInt, ...] | None = None
    terminal_status: Literal[
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
    ]
    event_ledger_sha256: str = Field(pattern=_SHA256)
    event_ledger_bytes: StrictInt = Field(ge=1)

    @model_validator(mode="after")
    def exact_component_roles(self) -> "ControlledArmReceiptV1":
        if self.validation_component.role != "original_validation":
            raise ValueError("controlled arm requires independent original-validation evidence")
        if self.arm_id == "initial_bp":
            if self.component is not None or self.shared_component_sha256 is None:
                raise ValueError("initial BP terminal must reference its one shared producer")
        elif self.arm_id in {"relay", "beam", "list", "vote"}:
            if (self.component is None or self.component.role != (
                    self.arm_id if self.arm_id in {"relay", "beam"} else f"{self.arm_id}_decision")
                    or self.component.shared_input_receipt_sha256 != self.shared_input_receipt_sha256):
                raise ValueError("controlled arm component differs from its shared input")
        if self.arm_id in {"initial_bp", "relay", "beam", "list", "vote"} and self.shared_input_receipt_sha256 is None:
            raise ValueError("shared controlled arm requires an input receipt digest")
        if self.candidate is not None and any(bit not in (0, 1) for bit in self.candidate):
            raise ValueError("controlled arm candidate must be binary")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return sha256(b"bp-registry-controlled-arm-v1\0" + self.primitive_bytes()).hexdigest()


class SharedMBBPMemberSetReceiptV1(StrictModel):
    """One ordered MBBP execution, reused by list and vote decisions."""

    schema_name: Literal["shared_mbbp_member_set_receipt_v1"] = Field(alias="schema", serialization_alias="schema")
    sample_identity: str = Field(pattern=_SHA256)
    sample_id: StrictInt = Field(ge=0, le=1_000_000)
    original_lineage_id: str = Field(min_length=1, max_length=256)
    member_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    result: dict[str, Any]
    components: tuple[ControlledComponentEvidenceV1, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def complete_ordered_members(self) -> "SharedMBBPMemberSetReceiptV1":
        from dataclasses import fields
        from ..canonical.budgets import WorkVector

        members = self.result.get("members")
        if (not isinstance(members, list) or len(members) != len(self.member_ids)
                or len(set(self.member_ids)) != len(self.member_ids)
                or tuple(item.get("member_id") for item in members if isinstance(item, dict)) != self.member_ids
                or len(self.components) != len(self.member_ids)):
            raise ValueError("shared MBBP receipt must contain every declared member exactly once")
        work_names = {item.name for item in fields(WorkVector)}
        for index, (member, component) in enumerate(zip(members, self.components, strict=True)):
            if (not isinstance(member, dict) or set(member) != {
                    "member_id", "local_ordinal", "lineage_id", "basis_identity", "initial_state_identity",
                    "schedule", "normalized_min_sum_alpha", "status", "candidate", "original_valid",
                    "admitted", "work",
                } or member["local_ordinal"] != index or component.role != "mbbp_member"
                    or component.component_id != member["member_id"]
                    or component.convergence_status.status != "observed"
                    or component.convergence_status.value != (member["status"] in {
                        "converged_original_valid", "converged_original_invalid"})
                    or not isinstance(member["work"], dict) or set(member["work"]) != work_names
                    or any(member["work"].get(name) != amount for name, amount in component.actual_work.items())):
                raise ValueError("shared MBBP member or typed component differs from the frozen order and work")
            WorkVector(**member["work"])
        if self.result.get("source_status") != "canonical_adaptation":
            raise ValueError("shared MBBP member set must retain canonical adaptation status")
        return self

    @classmethod
    def from_result(
        cls, *, sample_identity: str, sample_id: int, original_lineage_id: str,
        result: Any, components: tuple[ControlledComponentEvidenceV1, ...],
    ) -> "SharedMBBPMemberSetReceiptV1":
        from ..canonical.mbbp import MbbpResult

        if not isinstance(result, MbbpResult):
            raise ValueError("shared MBBP receipt requires an executed member result")
        return cls.model_validate({
            "schema": "shared_mbbp_member_set_receipt_v1", "sample_identity": sample_identity,
            "sample_id": sample_id, "original_lineage_id": original_lineage_id,
            "member_ids": tuple(member.member_id for member in result.members),
            "result": result.as_evidence(), "components": components,
        })

    def to_result(self, original: Any):
        """Rebuild decisions from sealed members without running member BP."""
        from ..canonical.budgets import WorkVector
        from ..canonical.candidate_selection import CandidateOrigin, FrequencyOverWeightScore, freeze_candidate_list
        from ..canonical.lineage import LineageId
        from ..canonical.mbbp import MbbpMember, MbbpResult
        from ..canonical.problems import OriginalProblem

        if not isinstance(original, OriginalProblem) or original.lineage_id != self.original_lineage_id:
            raise ValueError("shared MBBP receipt differs from its original problem")
        members = []
        for item in self.result["members"]:
            lineage = LineageId("member", item["lineage_id"])
            members.append(MbbpMember(
                member_id=item["member_id"], local_ordinal=item["local_ordinal"], lineage_id=lineage,
                basis_identity=item["basis_identity"], initial_state_identity=item["initial_state_identity"],
                schedule=item["schedule"], normalized_min_sum_alpha=item["normalized_min_sum_alpha"],
                status=item["status"], candidate=None if item["candidate"] is None else tuple(item["candidate"]),
                original_valid=item["original_valid"], work=WorkVector(**item["work"]),
            ))
        frozen = tuple(members)
        origins = tuple(CandidateOrigin(
            lineage_id=member.lineage_id, local_ordinal=member.local_ordinal,
            candidate=member.candidate, eligible=member.admitted, reason=member.status,
        ) for member in frozen)
        selection = freeze_candidate_list(
            original, declared_origins=tuple(member.lineage_id for member in frozen),
            origins=origins, score_policy=FrequencyOverWeightScore(),
        )
        if selection.as_evidence() != self.result.get("selection"):
            raise ValueError("shared MBBP selection differs from sealed member terminals")
        selected = next((member for member in frozen if member.lineage_id == selection.selected_origin_id), None)
        no_converged = not any(member.converged for member in frozen)
        terminal = ("selected_original_valid_candidate" if selected is not None else
                    "no_member_converged_zero_return" if no_converged else "no_admitted_member_candidate")
        leaves = self.result.get("work_leaves")
        if not isinstance(leaves, list):
            raise ValueError("shared MBBP receipt lacks work leaves")
        if (any(not isinstance(item, dict) or set(item) != {"leaf_id", "scope", "work"}
                for item in leaves)
                or len({item["leaf_id"] for item in leaves}) != len(leaves)):
            raise ValueError("shared MBBP receipt has duplicate or malformed work leaves")
        leaf_work = sum((WorkVector(**item["work"]) for item in leaves), start=WorkVector.zero())
        member_work = sum((member.work for member in frozen), start=WorkVector.zero())
        if leaf_work != member_work:
            raise ValueError("shared MBBP work leaves differ from member totals")
        rebuilt = MbbpResult(
            source_status="canonical_adaptation", terminal_status=terminal, members=frozen,
            selection=selection, selected_candidate=None if selected is None else selected.candidate,
            selected_origin_id=None if selected is None else selected.lineage_id,
            source_zero_return=tuple(0 for _ in range(original.hz.shape[1])) if no_converged else None,
            work=member_work,
            work_leaves=tuple((item["leaf_id"], item["scope"], WorkVector(**item["work"])) for item in leaves),
        )
        if rebuilt.as_evidence() != self.result:
            raise ValueError("shared MBBP result differs from independent sealed-member reconstruction")
        return rebuilt

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return sha256(b"bp-registry-shared-mbbp-members-v1\0" + self.primitive_bytes()).hexdigest()


class ControlledFamilyReceiptV1(StrictModel):
    """Complete-group controlled inference and its exact frozen missing set."""

    schema_name: Literal["controlled_family_receipt_v1"] = Field(alias="schema", serialization_alias="schema")
    family_id: Literal["relay_beam", "mbbp_list_vote", "schedule"]
    campaign_spec_digest: str = Field(pattern=_SHA256)
    campaign_plan_digest: str = Field(pattern=_SHA256)
    source_design_sha256: str = Field(pattern=_SHA256)
    arm_order: tuple[str, ...]
    comparisons: tuple[tuple[str, str], ...]
    expected_sample_identities: tuple[str, ...]
    complete_sample_identities: tuple[str, ...]
    missing_unit_keys: tuple[str, ...]
    paired_tables: dict[str, dict[str, Any]]
    holm_result: dict[str, Any]
    status: Literal["complete", "inconclusive_partial"]

    @model_validator(mode="after")
    def exact_family(self) -> "ControlledFamilyReceiptV1":
        expected = {
            "relay_beam": (("initial_bp", "relay", "beam"),
                           (("initial_bp", "relay"), ("initial_bp", "beam"))),
            "mbbp_list_vote": (("list", "vote"), (("list", "vote"),)),
            "schedule": (("spa_flooding", "spa_check_node_serial"),
                         (("spa_flooding", "spa_check_node_serial"),)),
        }
        order, comparisons = expected[self.family_id]
        if self.arm_order != order or self.comparisons != comparisons:
            raise ValueError("controlled family order or primary contrasts differ from the frozen design")
        if (len(set(self.expected_sample_identities)) != len(self.expected_sample_identities)
                or any(len(value) != 64 for value in self.expected_sample_identities)
                or any(value not in self.expected_sample_identities for value in self.complete_sample_identities)
                or len(set(self.complete_sample_identities)) != len(self.complete_sample_identities)
                or len(set(self.missing_unit_keys)) != len(self.missing_unit_keys)):
            raise ValueError("controlled family has invalid matched group membership")
        comparison_ids = {f"{a}-vs-{b}" for a, b in comparisons}
        if (set(self.paired_tables) != (comparison_ids if self.status == "complete" else set())
                or self.holm_result.get("frozen_family_size") != len(comparisons)
                or self.holm_result.get("family_id") != self.family_id):
            raise ValueError("controlled family paired or Holm membership differs from the frozen design")
        if self.status == "complete" and (
                self.missing_unit_keys or self.complete_sample_identities != self.expected_sample_identities):
            raise ValueError("complete controlled family requires all frozen matched groups")
        if self.status == "inconclusive_partial" and not self.missing_unit_keys:
            raise ValueError("partial controlled family requires an exact missing unit set")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return sha256(b"bp-registry-controlled-family-v1\0" + self.primitive_bytes()).hexdigest()


class ControlledCostProjectionV1(StrictModel):
    """Charge shared computation once and every later producer separately."""

    schema_name: Literal["controlled_cost_projection_v1"] = Field(alias="schema", serialization_alias="schema")
    shared_component_sha256s: tuple[str, ...]
    incremental_component_sha256s: dict[str, str]
    validation_component_sha256s: dict[str, str]
    common_work: dict[str, StrictInt]
    incremental_work: dict[str, dict[str, StrictInt]]
    validation_work: dict[str, dict[str, StrictInt]]
    total_work: dict[str, StrictInt]
    total_runtime_ns: ControlledCountV1
    total_evidence_bytes: ControlledCountV1
    total_storage_bytes: ControlledCountV1

    @model_validator(mode="after")
    def exact_once(self) -> "ControlledCostProjectionV1":
        all_digests = (*self.shared_component_sha256s, *self.incremental_component_sha256s.values(),
                       *self.validation_component_sha256s.values())
        if len(all_digests) != len(set(all_digests)):
            raise ValueError("controlled cost projection duplicates a producing component")
        if (set(self.incremental_work) != set(self.incremental_component_sha256s)
                or set(self.validation_work) != set(self.validation_component_sha256s)):
            raise ValueError("controlled cost projection has missing or extra work leaves")
        summed: dict[str, int] = {}
        for work in (self.common_work, *self.incremental_work.values(), *self.validation_work.values()):
            for name, amount in work.items():
                if type(amount) is not int or amount < 0:
                    raise ValueError("controlled cost work must be a nonnegative integer")
                summed[name] = summed.get(name, 0) + amount
        if self.total_work != dict(sorted(summed.items())):
            raise ValueError("controlled total work differs from unique producing leaves")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))


def project_controlled_costs(
    *, shared: tuple[ControlledComponentEvidenceV1, ...],
    shared_input_receipt_sha256: str,
    incremental: dict[str, ControlledComponentEvidenceV1],
    validation: dict[str, ControlledComponentEvidenceV1],
) -> ControlledCostProjectionV1:
    """Project measured cost without charging a shared initial/member twice."""
    if not shared or len({item.digest() for item in shared}) != len(shared):
        raise ValueError("controlled cost requires unique shared producer receipts")
    if any(item.role not in {"initial_bp", "mbbp_member"} for item in shared):
        raise ValueError("controlled common cost requires initial BP or MBBP member producers")
    if any(item.role == "original_validation" for item in incremental.values()):
        raise ValueError("original validation cost must remain separate from decoder continuation")
    if any(item.role != "original_validation" for item in validation.values()):
        raise ValueError("validation cost requires original-validation producers")
    if len(shared_input_receipt_sha256) != 64 or any(char not in "0123456789abcdef" for char in shared_input_receipt_sha256):
        raise ValueError("controlled cost requires a shared receipt SHA-256")
    if any(item.shared_input_receipt_sha256 is not None
           and item.shared_input_receipt_sha256 != shared_input_receipt_sha256 for item in incremental.values()):
        raise ValueError("incremental component differs from the shared producer lineage")
    common: dict[str, int] = {}
    for item in shared:
        for name, amount in item.actual_work.items():
            common[name] = common.get(name, 0) + amount
    extra = {name: dict(item.actual_work) for name, item in sorted(incremental.items())}
    checks = {name: dict(item.actual_work) for name, item in sorted(validation.items())}
    total: dict[str, int] = {}
    for work in (common, *extra.values(), *checks.values()):
        for name, amount in work.items():
            total[name] = total.get(name, 0) + amount
    components = (*shared, *incremental.values(), *validation.values())

    def sum_observed(attribute: str) -> ControlledCountV1:
        leaves = [getattr(item, attribute) for item in components]
        if any(leaf.status != "observed" for leaf in leaves):
            return ControlledCountV1(status="unavailable", reason=f"{attribute} unavailable for one or more producing components")
        return ControlledCountV1(status="observed", value=sum(leaf.value for leaf in leaves))

    return ControlledCostProjectionV1.model_validate({
        "schema": "controlled_cost_projection_v1",
        "shared_component_sha256s": tuple(item.digest() for item in shared),
        "incremental_component_sha256s": {name: item.digest() for name, item in sorted(incremental.items())},
        "validation_component_sha256s": {name: item.digest() for name, item in sorted(validation.items())},
        "common_work": dict(sorted(common.items())), "incremental_work": extra,
        "validation_work": checks, "total_work": dict(sorted(total.items())),
        "total_runtime_ns": sum_observed("runtime_ns"),
        "total_evidence_bytes": sum_observed("evidence_bytes"),
        "total_storage_bytes": sum_observed("storage_bytes"),
    })
