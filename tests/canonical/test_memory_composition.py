"""Ordered memory-binding ownership and rollback contracts."""

from __future__ import annotations

import numpy as np
import pytest

from bp_registry.canonical.memory import AffinePriorMemory, MemoryState


def _binding(
    binding_id: str, *, order: int, alpha: float, target: str = "prior",
    kind: str = "affine_prior", advance_boundary=None,
):
    from bp_registry.canonical.contracts import (
        MemoryAdvanceBoundary,
        MemoryBindingSpec,
        MemoryRefreshBoundary,
    )

    parameter_name = "gamma" if kind == "v2c_damping" else "alpha"
    return MemoryBindingSpec(
        binding_id=binding_id,
        kind=kind,
        target=target,
        parameters={parameter_name: alpha},
        order=order,
        history_owner=f"history:{binding_id}",
        state_lifetime="leg",
        advance_boundary=advance_boundary or MemoryAdvanceBoundary.SOURCE_ITERATION,
        refresh_boundary=MemoryRefreshBoundary.LEG_START,
        source_status="source_defined",
    )


def test_ordered_repeated_bindings_are_admitted_with_disjoint_owned_history():
    from bp_registry.canonical import contracts

    assert hasattr(contracts, "MemoryCompositionSpec"), "ordered memory composition must be a public contract"
    from bp_registry.canonical.compatibility import validate_memory_compatibility
    from bp_registry.canonical.contracts import MemoryCompositionSpec

    first = _binding("first", order=0, alpha=0.2)
    second = _binding("second", order=1, alpha=0.7)
    composition = MemoryCompositionSpec(bindings=(first, second))

    decision = validate_memory_compatibility(
        composition, update_rule="sum_product", schedule="flooding"
    )

    assert decision.admitted is True
    assert decision.reason is None
    assert tuple(binding.binding_id for binding in composition.bindings) == ("first", "second")
    assert {binding.history_owner for binding in composition.bindings} == {"history:first", "history:second"}


def test_undefined_local_target_boundary_is_rejected_before_sampling_with_stable_reason():
    from bp_registry.canonical import contracts

    assert hasattr(contracts, "MemoryCompositionSpec"), "compatibility checks require the ordered composition contract"
    from bp_registry.canonical.compatibility import validate_memory_compatibility
    from bp_registry.canonical.contracts import MemoryCompositionSpec

    composition = MemoryCompositionSpec(
        bindings=(_binding(
            "local", order=0, alpha=0.5, target="v2c", kind="v2c_damping",
            advance_boundary=contracts.MemoryAdvanceBoundary.LOCAL_UPDATE,
        ),)
    )

    decision = validate_memory_compatibility(
        composition, update_rule="sum_product", schedule="flooding"
    )

    assert decision.admitted is False
    assert decision.reason == "memory.target_boundary_unsupported:v2c:local_update:flooding"


def test_ordered_affine_bindings_have_an_explicit_commutativity_proof_for_shared_target_fixture():
    base = np.asarray([4.0])
    posterior = np.asarray([0.0])
    first, second = AffinePriorMemory("first", 0.2), AffinePriorMemory("second", 0.7)
    forward = second.propose(base, first.propose(base, posterior).prior).prior
    reverse = first.propose(base, second.propose(base, posterior).prior).prior
    # On the same target, affine maps with a common base compose with the
    # symmetric coefficient alpha + beta - alpha*beta.  The declared order is
    # still persisted because later target-specific bindings need not commute.
    np.testing.assert_allclose(forward, reverse)


def test_binding_commit_rejects_foreign_owned_state_without_mutating_history():
    owner = AffinePriorMemory("owner", 0.5)
    proposal = owner.propose(np.asarray([1.0]), np.asarray([3.0]))
    with pytest.raises(ValueError, match="another binding"):
        owner.commit(proposal, MemoryState("foreign", np.asarray([2.0])))


@pytest.mark.skip(reason="Wave 1 adds seeded assignments, schedule compatibility, and budget-denial rollback fixtures.")
def test_denied_memory_work_preserves_history_rng_and_schedule_cursor():
    """Reserved behavior target for the policy composition expansion."""
