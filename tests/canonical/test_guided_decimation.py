"""Phase 5 tracer for the versioned guided-decimation intervention."""

from __future__ import annotations

import numpy as np
import pytest


def _policies() -> dict[str, object]:
    return {
        "update": {"kind": "binary_spa", "binding_id": "update", "state_lifetime": "message"},
        "schedule": {"kind": "flooding", "binding_id": "schedule", "state_lifetime": "iteration"},
        "state_memory": {"kind": "identity", "binding_id": "memory", "state_lifetime": "attempt"},
        "intervention": {"kind": "guided_decimation", "binding_id": "guided", "state_lifetime": "search"},
        "stopping": {"kind": "syndrome_or_budget", "binding_id": "stopping", "state_lifetime": "iteration"},
        "selection": {"kind": "stable_first", "binding_id": "selection", "state_lifetime": "attempt"},
        "postprocessing": {"kind": "identity", "binding_id": "post", "state_lifetime": "attempt"},
    }


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 6, "run_id": "phase5-guided-tracer",
        "numerical_profile": "cpu-float64-spa-v1", "max_iterations": 1,
        "error_rate": 0.1, "policies": _policies(),
        "intervention": {
            "kind": "guided_decimation", "variant": "algorithm1_v2_interpretation",
            "source_revision": "arxiv:2312.10950v2", "finite_bias_magnitude": 25.0,
            "zero_rule": "positive_prior_for_zero_posterior",
            "final_round_rule": "return_after_last_fixation",
            "round_limit": 1, "sweeps_per_round": 1,
        },
    }


def test_historical_manifest_and_strict_v6_contract():
    from bp_registry.canonical.contracts import CanonicalManifestV6, parse_canonical_manifest

    parsed = parse_canonical_manifest(_manifest())
    assert isinstance(parsed, CanonicalManifestV6)
    assert parsed.intervention.finite_bias_magnitude == 25.0
    assert parse_canonical_manifest(parsed.model_dump_json()) == parsed
    bad = _manifest()
    bad["unexpected"] = 1
    with pytest.raises(ValueError):
        parse_canonical_manifest(bad)
    historical = _manifest()
    historical["schema_version"] = 3
    historical.pop("intervention")
    with pytest.raises(ValueError):
        parse_canonical_manifest(historical)


def test_denial_rollback_keeps_parent_session_exactly_intact():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.guided_decimation import GuidedDecimationController
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.schedules import EdgeTable

    h = np.asarray([[0, 1, 1], [1, 0, 1]], dtype=np.uint8)
    session = BpSession(EdgeTable.from_check_matrix(h), np.asarray([0, 1], dtype=np.uint8), error_rate=0.1)
    state = session.state
    denied = BudgetTree(limits=[BudgetLimit("attempt", "intervention_actions", 0)], parents={})
    controller = GuidedDecimationController(_manifest()["intervention"])
    transition = controller.fix_one(session, posterior=np.asarray([2.0, -2.0, 1.0]), budgets=denied)
    assert not transition.admitted
    assert transition.proposal.target_index == 0
    assert transition.termination == "count_budget_exhausted"
    assert session.state is state
    assert session.state.digest == state.digest
    assert denied.summary("attempt").intervention_actions == 0


def test_proposal_carries_source_mutation_work_and_rejects_untrusted_action():
    from pydantic import TypeAdapter
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.contracts import FinitePriorBiasAction, InterventionAction
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.schedules import EdgeTable

    adapter = TypeAdapter(InterventionAction)
    action = adapter.validate_python({"kind": "finite_prior_bias", "target_index": 0, "signed_llr": 25.0})
    assert isinstance(action, FinitePriorBiasAction)
    with pytest.raises(ValueError):
        adapter.validate_python({"kind": "execute_python", "target_index": 0})
    with pytest.raises(ValueError):
        adapter.validate_python({"kind": "finite_prior_bias", "target_index": 0, "signed_llr": float("inf")})
    h = np.asarray([[1, 1]], dtype=np.uint8)
    session = BpSession(EdgeTable.from_check_matrix(h), np.asarray([1], dtype=np.uint8), error_rate=0.1)
    proposal = session.propose_finite_prior(
        0, 25.0, source_variant="algorithm1_v2_interpretation", target_order=(0, 1),
    )
    assert proposal.action_payload == action
    assert proposal.anticipated_work.fixation_actions == 1
    assert proposal.anticipated_work.ranking_scans == 2
    assert proposal.stream_identity == "not_applicable"
    assert proposal.child_lineage_id.startswith("working-")
    assert proposal.preserved_fields == ("graph", "syndrome", "v2c", "c2v")
    budget = BudgetTree(limits=(), parents={})
    transition = session.commit_intervention(proposal, budgets=budget, leaf_id="fix-test")
    assert transition.admitted
    assert budget.summary("attempt") == proposal.anticipated_work


def test_tracer_original_validation_and_hidden_truth_sealing(tmp_path):
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.css import CssCode
    from bp_registry.ledger import read_canonical_events
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    h = np.asarray([[0, 1, 1], [1, 0, 1]], dtype=np.uint8)
    code = CssCode(hx=np.zeros((1, 3), dtype=np.uint8), hz=h)
    observation = DecoderObservation("Z", np.asarray([1, 0], dtype=np.uint8))
    def run(truth: np.ndarray, path):
        manifest = _manifest()
        manifest["intervention"]["round_limit"] = 2
        return run_canonical_structural_shot(
            manifest, code=code, observation=observation,
            hidden_truth=HiddenTruth(truth, np.zeros(3, dtype=np.uint8)),
            shot_id=0, ledger_path=path, sample_seed_identity="sample-0", context={"tracer": True},
        )
    first = run(np.asarray([0, 1, 0], dtype=np.uint8), tmp_path / "one.jsonl")
    second = run(np.asarray([1, 0, 1], dtype=np.uint8), tmp_path / "two.jsonl")
    one = read_canonical_events(tmp_path / "one.jsonl")
    two = read_canonical_events(tmp_path / "two.jsonl")
    interventions = [row for row in one if row["kind"] == "intervention"]
    assert len(interventions) == 1
    assert interventions[0]["data"]["target_index"] == 0
    assert interventions[0]["data"]["finite_bias_magnitude"] == 25.0
    assert interventions[0]["data"]["state_before"] != interventions[0]["data"]["state_after"]
    assert next(row for row in one if row["kind"] == "work")["data"]["work_vector"]["bp_calls"] == 2
    assert [row["data"] for row in one if row["kind"] != "termination"] == [
        row["data"] for row in two if row["kind"] != "termination"
    ]
    assert first.termination == second.termination
    assert np.array_equal(first.candidate, second.candidate)
    assert first.candidate is not None
    assert np.array_equal((h @ first.candidate) % 2, observation.syndrome)
    assert first.evaluation.outcome == "exact"
    assert second.evaluation.outcome == "logical_failure"
