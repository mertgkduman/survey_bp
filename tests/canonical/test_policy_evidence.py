"""Evidence adjacency and ordering contracts for canonical policy bindings."""

from __future__ import annotations

import pytest
from pathlib import Path

from bp_registry.canonical.contracts import PolicyEvidence


def test_canonical_tutorial_has_required_contract_anchors():
    tutorial = Path("docs/canonical-engine.md").read_text(encoding="utf-8").replace("**", "").replace("\n", " ").lower()
    required_anchors = (
        "binary-spa-flooding-f64-v1",
        "log(p(0) / p(1))",
        "s = hx (mod 2)",
        "k = 25",
        "check-major, variable-minor",
        "old v2c snapshot",
        "fresh v2c buffer",
        "update", "schedule", "state_memory", "intervention", "stopping", "selection", "postprocessing",
        "shot, search, member, leg, branch, attempt, iteration, and message",
        "capability-scoped", "private state", "typed decisions",
        "static composition validation", "live-state invariant",
        "reserve", "workvector", "schedule-qualified iteration",
        "frozen decoder-visible candidate", "independent evaluator",
        "canonical_implemented", "development_fixture", "not_assessed",
        "source-faithful", "statistical reproduction",
    )
    assert all(anchor in tutorial for anchor in required_anchors)


def test_profiling_strategy_and_novelty_register_preserve_evidence_limits():
    strategy = Path("docs/profiling-and-tracing-strategy.md").read_text(encoding="utf-8").lower()
    register = Path("docs/research-novelty-and-depth-register.md").read_text(encoding="utf-8").lower()
    strategy_anchors = (
        "d-20", "scientific value", "cost", "sparse structural", "iteration", "edge",
        "max_records", "max_bytes", "truncated", "development-only", "not a campaign default",
        "clean", "representative", "diagnostic", "selected_before_outcome", "inclusion_probability",
        "adapter_overhead", "clean_run_id", "profile_run_id", "semantic_agreement",
        "candidate", "termination", "work", "lineage", "semantic_trace_digest",
        "plot", "missingness", "retention", "race-sensitive", "content identity",
    )
    register_anchors = (
        "d-26", "potential contribution", "executable evidence", "closest precedent",
        "unresolved search", "claim maturity", "profiling", "selective tracing", "provisional",
        "corpus recheck", "not_assessed", "not established methodological novelty",
    )
    assert all(anchor in strategy for anchor in strategy_anchors)
    assert all(anchor in register for anchor in register_anchors)
    assert "diagnostic evidence is not a population estimate" in strategy
    assert "development evidence is not a reproduction claim" in strategy


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
