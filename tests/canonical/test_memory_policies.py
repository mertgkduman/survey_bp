"""Equation and endpoint contracts for Phase 4 memory-policy variants."""

from __future__ import annotations

import numpy as np
import pytest

from bp_registry.canonical import memory
from bp_registry.canonical.memory import AffinePriorMemory


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
