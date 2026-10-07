"""Closed compatibility authority for the Phase 10 quaternary BP policies."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Literal

from .contracts import QuaternaryCompositionSpec, QuaternaryResolvedComposition


_BINARY_KINDS = frozenset({
    "binary_spa", "spa", "min_sum", "normalized_min_sum", "offset_min_sum",
    "layered", "check_node_serial", "variable_node_serial", "residual",
    "randomized", "group_shuffled", "damping", "field_mixing", "momentum",
    "ewa", "relay", "relay_memory",
})
_SOURCE_REVISIONS = (
    "lai-kuo-2021-scalar-llr-bp4-v3",
    "kuo-lai-2020-bp4-serial-v2",
)


def _semantic_identity(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_binary(kind: str) -> None:
    if kind in _BINARY_KINDS or kind.startswith("binary_"):
        raise ValueError(f"unsupported binary policy port: {kind}")


def _config_string(config: dict[str, object], name: str) -> str | None:
    value = config.get(name)
    return value if isinstance(value, str) else None


def resolve_quaternary_composition(
    composition: QuaternaryCompositionSpec,
    *,
    problem_kind: Literal["general_pauli", "css"] = "general_pauli",
) -> QuaternaryResolvedComposition:
    """Resolve a closed composition before artifact resolution or sampling.

    Source fidelity is intentionally a property of the whole run.  A
    source-backed component may participate in an adapted composition, which is
    why ``component_fidelity`` and ``run_fidelity`` are stored independently.
    """
    if not isinstance(composition, QuaternaryCompositionSpec):
        raise ValueError("quaternary compatibility requires QuaternaryCompositionSpec")
    if problem_kind not in {"general_pauli", "css"}:
        raise ValueError("quaternary problem kind must be general_pauli or css")

    assert composition.kernel is not None and composition.schedule is not None and composition.intervention is not None
    kernel, schedule, intervention = composition.kernel, composition.schedule, composition.intervention
    for _role, policy in composition.in_role_order():
        _reject_binary(policy.kind)

    if kernel.kind != "qbp_scalar_llr":
        raise ValueError(f"unknown quaternary kernel kind: {kernel.kind}")
    if schedule.kind not in {"qbp_flooding", "qbp_variable_serial"}:
        raise ValueError(f"unknown or unsupported quaternary schedule kind: {schedule.kind}")
    if any(transform.kind not in {"qbp_c2v_normalization", "qbp_c2v_offset"} for transform in composition.transforms):
        unknown = next(transform.kind for transform in composition.transforms if transform.kind not in {"qbp_c2v_normalization", "qbp_c2v_offset"})
        raise ValueError(f"unknown quaternary C2V transform kind: {unknown}")
    if len({transform.kind for transform in composition.transforms}) != len(composition.transforms):
        raise ValueError("quaternary C2V transform kinds may occur at most once")

    component_fidelity: dict[str, Literal["source_backed", "canonical_adaptation"]] = {
        "kernel": "source_backed", "schedule": "source_backed", "intervention": "source_backed",
    }
    for index in range(len(composition.transforms)):
        component_fidelity[f"transform:{index}"] = "source_backed"
    effective_order = (kernel.kind, schedule.kind, *(item.kind for item in composition.transforms), intervention.kind)
    equations = {
        "scalar_commutation_c2v": "Delta_m_to_n = (-1)^s_m boxplus_{n_prime != n}(lambda_{n_prime to m})",
        "three_llr_v2c": "Gamma_n_to_m = Lambda_n + sum_{m_prime != m} commutation(W_m_prime_n, sigma) Delta_m_prime_to_n",
    }
    lifecycle = {
        "kernel_state_owner": "qbp_session",
        "schedule_freshness": "complete_old_v2c_snapshot_then_complete_commit" if schedule.kind == "qbp_flooding" else "variable_serial_immediate_v2c_visibility",
        "c2v_transform_scope": "scalar_commutation_c2v_after_check_reduction_before_variable_assembly",
        "truth_boundary": "decoder_receives_only_original_problem_observation_and_priors",
    }
    reasons: list[str] = []
    revisions = list(_SOURCE_REVISIONS)
    procedure_basis = "source_scalar_llr_bp4_v1"

    if composition.transforms:
        equations["c2v_transforms"] = "; ".join(
            "Delta/alpha_c" if transform.kind == "qbp_c2v_normalization" else "sign(Delta)max(0,abs(Delta)-beta)"
            for transform in composition.transforms
        )
        revisions.append("lai-kuo-2021-c2v-transform-v3")
    if len(composition.transforms) > 1:
        reasons.append("transform_combination_not_source_defined")

    if intervention.kind == "identity":
        pass
    elif intervention.kind == "qbpgd":
        continued = intervention.config.get("continued_messages")
        prior_profile = _config_string(intervention.config, "prior_profile")
        if type(continued) is not bool or prior_profile not in {"depolarizing", "general_joint"}:
            raise ValueError("Q-BPGD owns state incompletely or lacks a declared prior profile")
        component_fidelity["intervention"] = "source_backed"
        equations["qbpgd_fixation"] = "raw=(1-epsilon,epsilon,epsilon,epsilon); normalize_only_by_common_sum"
        lifecycle["qbpgd_buffer_owner"] = "qbpgd_controller"
        lifecycle["qbpgd_message_lifecycle"] = "continue_committed_qbp_edge_messages" if continued else "reset_not_qualified"
        revisions.append("yao-2023-qbpgd-algorithm-3-v2")
        procedure_basis = "canonical_qbpgd_interpretation_v1"
        if continued:
            reasons.append("continued_message_buffers")
        else:
            raise ValueError("Q-BPGD buffer lifecycle is incomplete without continued-message ownership")
        if prior_profile == "general_joint":
            reasons.append("general_joint_prior")
    elif intervention.kind == "mbp4":
        raise ValueError("MBP4 execution is reserved until its distinct recurrence is implemented")
    elif intervention.kind == "ambp4":
        raise ValueError("AMBP4 requires its complete adaptive search contract and is unsupported")
    elif intervention.kind in {"asced", "asced_overcomplete"}:
        css_only = intervention.config.get("css_only")
        if problem_kind != "css" or css_only is not True:
            raise ValueError("non-CSS aSCED is unsupported without a separate splitter derivation")
        raise ValueError("aSCED execution is reserved until qualified splitter output is available")
    else:
        raise ValueError(f"unknown quaternary intervention kind: {intervention.kind}")

    run_fidelity: Literal["source_backed", "canonical_adaptation"] = "canonical_adaptation" if reasons else "source_backed"
    identity_payload = {
        "composition": composition.model_dump(mode="json"), "problem_kind": problem_kind,
        "component_fidelity": component_fidelity, "run_fidelity": run_fidelity,
        "procedure_basis": procedure_basis, "effective_order": effective_order,
        "equations": equations, "source_revision": revisions, "lifecycle": lifecycle,
        "adaptation_reasons": reasons,
    }
    resolved = {key: value for key, value in identity_payload.items() if key not in {"composition", "problem_kind"}}
    return QuaternaryResolvedComposition(**resolved, semantic_identity=_semantic_identity(identity_payload))


__all__ = ["resolve_quaternary_composition"]
