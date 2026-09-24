"""Ordered memory-binding ownership and rollback contracts."""

from __future__ import annotations

import numpy as np
import pytest

from bp_registry.canonical.memory import AffinePriorMemory, MemoryState


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
