"""Closed admission decisions for ordered memory-policy compositions."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import MemoryCompositionSpec


@dataclass(frozen=True, slots=True)
class MemoryCompatibilityDecision:
    """A persisted admission result; rejection always names the missing operand."""

    admitted: bool
    reason: str | None = None
    binding_id: str | None = None


_UPDATE_RULES = frozenset({"binary_spa", "sum_product", "min_sum", "normalized_min_sum", "offset_min_sum"})
_FLOODING_OPERANDS = frozenset({
    ("affine_prior", "prior", "source_iteration"),
    ("v2c_damping", "v2c", "source_iteration"),
    ("pdbp_field_mix", "belief", "source_iteration"),
    ("pdprime_delta_mix", "belief", "source_iteration"),
    ("posterior_momentum", "posterior", "source_iteration"),
})
_LOCAL_OPERANDS = frozenset({
    ("v2c_damping", "v2c", "local_update"),
    # Every Phase 3 local executor already assembles a full fresh belief
    # vector before candidate construction and V2C mutation.  PDBP consumes
    # precisely that decoder-visible field and its separately owned old field.
    ("pdbp_field_mix", "belief", "local_update"),
})


def validate_memory_compatibility(
    composition: MemoryCompositionSpec, *, update_rule: str, schedule: str,
) -> MemoryCompatibilityDecision:
    """Admit only operands with a concrete Phase 3 schedule commit boundary."""
    if update_rule not in _UPDATE_RULES:
        return MemoryCompatibilityDecision(False, f"memory.update_rule_unsupported:{update_rule}")
    if schedule == "flooding":
        operands = _FLOODING_OPERANDS
    elif schedule in {"layered", "check_node_serial", "variable_node_serial"}:
        operands = _LOCAL_OPERANDS
    else:
        return MemoryCompatibilityDecision(False, f"memory.schedule_unsupported:{schedule}")
    for binding in composition.bindings:
        operand = (binding.kind, binding.target, binding.advance_boundary.value)
        if operand not in operands:
            return MemoryCompatibilityDecision(
                False,
                f"memory.target_boundary_unsupported:{binding.target}:{binding.advance_boundary.value}:{schedule}",
                binding.binding_id,
            )
    return MemoryCompatibilityDecision(True)
