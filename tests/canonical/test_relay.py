"""Public-path tracer contracts for the Phase 4 Relay-BP adaptation."""

from __future__ import annotations

import numpy as np
import pytest


def test_source_preset_exposes_its_own_fidelity_and_complete_leg_contract():
    """The source procedure remains a named, immutable CSS adaptation."""
    from bp_registry.canonical.relay import RelayPreset

    source = RelayPreset.source_procedure()

    assert source.name == "relay-source-internal-bp-v0.2.2"
    assert source.procedure == "source_internal_bp"
    assert source.fidelity_status == "source_procedure_css_adaptation"
    assert source.total_leg_limit == 301
    assert source.first_leg_iteration_limit == 80
    assert source.later_leg_iteration_limit == 60
    assert source.transfer == "posterior_only"
    assert source.first_leg_memory == "uniform"
    assert source.later_leg_memory == "disordered"
    with pytest.raises((AttributeError, TypeError)):
        source.total_leg_limit = 1  # type: ignore[misc]


def test_canonical_preset_has_distinct_controlled_identity_and_bounded_stopping():
    """The controlled default cannot silently inherit source-procedure identity."""
    from bp_registry.canonical.relay import RelayPreset

    source = RelayPreset.source_procedure()
    canonical = RelayPreset.canonical_default()

    assert canonical.name == "relay-canonical-css-default-v1"
    assert canonical.procedure == "canonical_internal_bp"
    assert canonical.fidelity_status == "canonical_css_adaptation"
    assert canonical != source
    assert canonical.total_leg_limit == len(canonical.legs)
    assert canonical.total_leg_limit >= 1
    assert canonical.solution_limit >= 1


def test_leg_limit_counts_one_pre_leg_plus_declared_later_legs():
    """A total leg limit is never interpreted as only the later-leg count."""
    from bp_registry.canonical.relay import RelayPreset

    preset = RelayPreset.canonical_default().with_controls(total_leg_limit=3)

    assert len(preset.legs) == 3
    assert preset.legs[0].max_iterations == preset.first_leg_iteration_limit
    assert all(leg.max_iterations == preset.later_leg_iteration_limit for leg in preset.legs[1:])


def test_score_selection_keeps_the_first_leg_when_scores_tie():
    """Stable relay selection preserves source ordering without hidden truth."""
    from bp_registry.canonical.relay import RelayCandidateScore, RelayController

    first = RelayCandidateScore(leg_index=0, syndrome_weight=1, prior_weight=2.0)
    later = RelayCandidateScore(leg_index=1, syndrome_weight=1, prior_weight=2.0)

    assert RelayController.select_candidate((later, first)) is first


def test_ablation_controls_are_adaptations_and_never_mutate_source_preset():
    """Each changed Relay component has a controlled identity and leaves the source frozen."""
    from bp_registry.canonical.relay import RelayPreset

    source = RelayPreset.source_procedure()
    ablated = source.ablation(one_leg=True, posterior_transfer=False, later_leg_memory="uniform")

    assert source.total_leg_limit == 301
    assert source.transfer == "posterior_only"
    assert source.later_leg_memory == "disordered"
    assert ablated.name == "relay-controlled-source_internal_bp-v1"
    assert ablated.fidelity_status == "controlled_component_adaptation"
    assert ablated.total_leg_limit == 1
    assert ablated.transfer == "disabled"
    assert ablated.later_leg_memory == "uniform"
    assert ablated.as_spec().fidelity_status == "controlled_component_adaptation"


def test_no_transfer_one_leg_uniform_and_disordered_controls_are_independent():
    """Relay component arms isolate exactly the requested control."""
    from bp_registry.canonical.relay import RelayPreset

    source = RelayPreset.source_procedure()

    assert source.ablation(posterior_transfer=False).transfer == "disabled"
    assert source.ablation(one_leg=True).total_leg_limit == 1
    assert source.ablation(later_leg_memory="uniform").later_leg_memory == "uniform"
    assert RelayPreset.canonical_default().ablation(later_leg_memory="disordered").later_leg_memory == "disordered"


def test_numerical_profile_and_source_parameter_sweep_controls_remain_explicit():
    """A source sweep or numerical control cannot collapse into the source configuration."""
    from bp_registry.canonical.relay import RelayPreset

    source = RelayPreset.source_procedure()
    sweep = source.ablation(source_parameter_sweep=(-0.10, 0.10))
    numerical = source.ablation(numerical_profile="cpu-float64-spa-v1")

    assert sweep.source_parameter_sweep == (-0.10, 0.10)
    assert numerical.numerical_profile == "cpu-float64-spa-v1"
    assert sweep.fidelity_status == numerical.fidelity_status == "controlled_component_adaptation"


def _policies() -> dict[str, object]:
    return {
        "update": {"kind": "binary_spa", "binding_id": "update", "state_lifetime": "message"},
        "schedule": {"kind": "flooding", "binding_id": "schedule", "state_lifetime": "iteration"},
        "state_memory": {"kind": "identity", "binding_id": "memory", "state_lifetime": "leg"},
        "intervention": {"kind": "identity", "binding_id": "intervention", "state_lifetime": "search"},
        "stopping": {"kind": "syndrome_or_budget", "binding_id": "stopping", "state_lifetime": "iteration"},
        "selection": {"kind": "stable_first", "binding_id": "selection", "state_lifetime": "attempt"},
        "postprocessing": {"kind": "identity", "binding_id": "post", "state_lifetime": "attempt"},
    }


def test_tracer_two_leg_relay_is_public_truth_blind_and_transfers_only_posterior(tmp_path):
    """The persisted Relay composition reaches the structural engine and freezes selection before truth."""
    from bp_registry.canonical.contracts import CanonicalManifestV4
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.css import fixture_code
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    code = fixture_code()
    hidden_x = np.asarray([1, 0, 0], dtype=np.uint8)
    observation = DecoderObservation("Z", code.hz @ hidden_x % 2)
    manifest = CanonicalManifestV4.model_validate({
        "schema_version": 4,
        "run_id": "phase4-relay-tracer",
        "numerical_profile": "cpu-float64-spa-v1",
        "max_iterations": 4,
        "error_rate": 0.1,
        "policies": _policies(),
        "memory_bindings": [{
            "binding_id": "relay-prior", "kind": "affine_prior", "target": "prior",
            "order": 0, "alpha": 0.5, "state_lifetime": "leg",
        }],
        "relay": {"total_leg_limit": 2, "legs": [{"max_iterations": 4}, {"max_iterations": 4}]},
    })

    result = run_canonical_structural_shot(
        manifest, code=code, observation=observation,
        hidden_truth=HiddenTruth(hidden_x, np.zeros(3, dtype=np.uint8)), shot_id=0,
        ledger_path=tmp_path / "events.jsonl", sample_seed_identity="sample-0", context={"tracer": True},
    )

    assert result.termination == "completed"
    events = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    assert "relay_transfer" in events
    assert "llr_log_p0_over_p1" in events


def test_relay_leaf_accounting_is_idempotent_and_retains_per_leg_ancestry():
    """Committed Relay work has one stable leaf even if delivery is retried."""
    from bp_registry.canonical.budgets import RelayWorkAccounting, WorkVector

    accounting = RelayWorkAccounting(shot_identity="run:0")
    assert accounting.commit(
        kind="leg", leg_index=0, lineage_id="attempt-a:leg:0",
        leaf_id="relay:attempt-a:leg:0:sweep:1",
        delta=WorkVector(bp_calls=1, check_to_variable_updates=2),
    ) is True
    assert accounting.commit(
        kind="transfer", leg_index=1, lineage_id="attempt-a:leg:0",
        leaf_id="relay:attempt-a:transfer:1", delta=WorkVector(relay_transfers=1),
    ) is True
    assert accounting.commit(
        kind="candidate", leg_index=1, lineage_id="attempt-a:leg:1",
        leaf_id="relay:attempt-a:candidate:1", delta=WorkVector(candidate_checks=1),
    ) is True
    assert accounting.commit(
        kind="selection", leg_index=1, lineage_id="attempt-a:leg:1",
        leaf_id="relay:attempt-a:selection", delta=WorkVector(order_selection=1),
    ) is True
    assert accounting.commit(
        kind="transfer", leg_index=1, lineage_id="attempt-a:leg:0",
        leaf_id="relay:attempt-a:transfer:1", delta=WorkVector(relay_transfers=1),
    ) is False

    leaves = accounting.leaves()
    assert [leaf["kind"] for leaf in leaves] == ["leg", "transfer", "candidate", "selection"]
    assert accounting.summary().as_evidence()["relay_transfers"] == 1
    assert accounting.by_leg(1).as_evidence()["candidate_checks"] == 1
