"""Evidence adjacency and ordering contracts for canonical policy bindings."""

from __future__ import annotations

import pytest

from bp_registry.canonical.contracts import PolicyEvidence


def test_policy_evidence_requires_a_primary_basis_and_ordered_invariants():
    evidence = PolicyEvidence(
        source_anchors=["https://example.test/paper#eq-1"],
        invariants=["first invariant", "second invariant"],
    )
    assert evidence.model_dump(mode="json")["invariants"] == ["first invariant", "second invariant"]

    with pytest.raises(ValueError, match="source anchor or precise procedure"):
        PolicyEvidence(invariants=["checked"])
    with pytest.raises(ValueError, match="nonempty ordered invariants"):
        PolicyEvidence(procedure="A deterministic no-op.", invariants=[])
