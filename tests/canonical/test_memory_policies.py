"""Equation and endpoint contracts for Phase 4 memory-policy variants."""

from __future__ import annotations

import numpy as np
import pytest

from bp_registry.canonical import memory
from bp_registry.canonical.memory import AffinePriorMemory, PDBPFieldMix, PDPrimeDeltaMix, V2CDamping


def test_affine_prior_memory_uses_documented_previous_posterior_coefficient():
    proposal = AffinePriorMemory("relay", 0.25).propose(
        np.asarray([4.0, -2.0]), np.asarray([0.0, 6.0]),
    )
    np.testing.assert_allclose(proposal.prior, [3.0, 0.0])


@pytest.mark.parametrize("alpha, expected", [(0.0, [4.0, -2.0]), (1.0, [0.0, 6.0])])
def test_affine_prior_memory_endpoint_preserves_declared_operand(alpha, expected):
    proposal = AffinePriorMemory("relay", alpha).propose(
        np.asarray([4.0, -2.0]), np.asarray([0.0, 6.0]),
    )
    np.testing.assert_allclose(proposal.prior, expected)


def test_affine_prior_memory_rejects_nonfinite_decoder_visible_operands():
    with pytest.raises(ValueError, match="finite"):
        AffinePriorMemory("relay", 0.5).propose(np.asarray([1.0]), np.asarray([np.nan]))


def test_damping_pdbp_and_pdprime_expose_distinct_targeted_rules():
    """Published message and belief rules remain separately addressable policies."""
    assert all(hasattr(memory, name) for name in ("V2CDamping", "PDBPFieldMix", "PDPrimeDeltaMix"))


@pytest.mark.parametrize(
    ("gamma", "expected"),
    [(0.0, [4.0, -2.0]), (1.0, [0.0, 6.0]), (0.25, [3.0, 0.0])],
)
def test_damping_uses_gokduman_fresh_coefficient_orientation(gamma, expected):
    policy = V2CDamping("damping", gamma)
    proposal = policy.propose(np.asarray([4.0, -2.0]), np.asarray([0.0, 6.0]), boundary="source_iteration")
    np.testing.assert_allclose(proposal.value, expected)
    assert proposal.target == "v2c"
    np.testing.assert_allclose(policy.commit(proposal, policy.initial_state([4.0, -2.0])).v2c, [0.0, 6.0])


def test_damping_rejects_missing_operands_and_wrong_advance_boundary():
    policy = V2CDamping("damping", 0.5, advance_boundary="local_update")
    with pytest.raises(ValueError, match="local_update"):
        policy.propose([1.0], [2.0], boundary="source_iteration")
    with pytest.raises(ValueError, match="nonempty"):
        policy.propose([], [2.0], boundary="local_update")


def test_pdbp_and_pdprime_diverge_on_independent_field_and_edge_fixture():
    pdbp = PDBPFieldMix("pdbp", 0.25)
    pdprime = PDPrimeDeltaMix("pdprime", 0.25)
    old_field = np.asarray([10.0, -4.0])
    pdbp_result = pdbp.propose(old_field, np.asarray([4.0, 2.0]), boundary="source_iteration")
    pdprime_result = pdprime.propose(
        old_field,
        np.asarray([[1.0, 2.0], [3.0, -1.0]]),
        np.asarray([[3.0, 1.0], [2.0, 2.0]]),
        boundary="source_iteration",
    )
    np.testing.assert_allclose(pdbp_result.value, [5.5, 0.5])
    np.testing.assert_allclose(pdprime_result.value, [10.75, -2.5])
    assert not np.array_equal(pdbp_result.value, pdprime_result.value)
    assert pdbp_result.target == pdprime_result.target == "belief"


def test_pdprime_requires_edge_aligned_c2v_operands_and_commits_both_histories():
    policy = PDPrimeDeltaMix("pdprime", 0.5, advance_boundary="local_update")
    old = np.asarray([[1.0, 2.0], [3.0, 4.0]])
    fresh = np.asarray([[2.0, 1.0], [4.0, 3.0]])
    proposal = policy.propose([5.0, -1.0], old, fresh, boundary="local_update")
    state = policy.commit(proposal, policy.initial_state([5.0, -1.0], old))
    np.testing.assert_allclose(state.field, [6.0, -2.0])
    np.testing.assert_allclose(state.c2v, fresh)
    with pytest.raises(ValueError, match="edge-aligned"):
        policy.propose([5.0, -1.0], old, fresh[:1], boundary="local_update")
