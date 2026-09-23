"""Evidence adjacency and ordering contracts for canonical policy bindings."""

from __future__ import annotations

import pytest
from pathlib import Path

from bp_registry.canonical.contracts import PolicyEvidence


def test_canonical_tutorial_has_required_contract_anchors():
    tutorial = Path("docs/canonical-engine.md").read_text(encoding="utf-8")
    required_anchors = (
        "binary-spa-flooding-f64-v1",
        "log(P(0) / P(1))",
        "s = Hx (mod 2)",
        "K = 25",
        "check-major, variable-minor",
        "old v2c snapshot",
        "fresh v2c buffer",
        "update", "schedule", "state_memory", "intervention", "stopping", "selection", "postprocessing",
        "shot, search, member, leg, branch, attempt, iteration, and message",
        "capability-scoped", "private state", "typed decisions",
        "static composition validation", "live-state invariant",
        "reserve", "WorkVector", "schedule-qualified iteration",
        "frozen decoder-visible candidate", "independent evaluator",
        "canonical_implemented", "development_fixture", "not_assessed",
        "source-faithful", "statistical reproduction",
    )
    assert all(anchor in tutorial for anchor in required_anchors)


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
