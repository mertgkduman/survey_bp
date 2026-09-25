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
    from bp_registry.canonical.verification import validate_phase4_shot

    evidence = validate_phase4_shot(
        tmp_path / "events.jsonl", run_id="phase4-relay-tracer", shot_id=0, trace_root=tmp_path,
    )
    assert evidence["work"] is not None


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


def _three_leg_manifest(run_id: str):
    from bp_registry.canonical.contracts import CanonicalManifestV4

    return CanonicalManifestV4.model_validate({
        "schema_version": 4,
        "run_id": run_id,
        "numerical_profile": "cpu-float64-spa-v1",
        "max_iterations": 3,
        "error_rate": 0.1,
        "policies": _policies(),
        "memory_bindings": [{
            "binding_id": "relay-prior", "kind": "affine_prior", "target": "prior",
            "order": 0, "alpha": 0.5, "state_lifetime": "leg",
        }],
        "relay": {
            "total_leg_limit": 3, "solution_limit": 3,
            "legs": [{"max_iterations": 1}, {"max_iterations": 2}, {"max_iterations": 3}],
        },
    })


def _impossible_syndrome_code():
    from bp_registry.css import CssCode

    # A nonzero observed syndrome on this all-zero check is deliberately
    # unreachable, so every declared Relay leg executes deterministically.
    return CssCode(np.zeros((1, 3), dtype=np.uint8), np.zeros((1, 3), dtype=np.uint8)).validate()


def _relay_controls(*, belief_assemblies: int):
    from bp_registry.canonical.budgets import WorkVector

    resources = WorkVector.zero().as_evidence(structural_event_version=2)
    return {"work_limits": {
        scope: {resource: belief_assemblies if resource == "belief_assemblies" else 100 for resource in resources}
        for scope in ("shot", "search", "attempt")
    }}


def test_three_leg_relay_emits_committed_per_leg_leaves_and_replays_idempotently(tmp_path):
    """Six committed sweeps stay on their own legs through the durable ledger."""
    from bp_registry.canonical.budgets import WorkVector
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.canonical.verification import validate_phase4_shot
    from bp_registry.ledger import read_canonical_events
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    path = tmp_path / "three-leg.jsonl"
    code = _impossible_syndrome_code()
    kwargs = {
        "code": code, "observation": DecoderObservation("Z", np.ones(1, dtype=np.uint8)),
        "hidden_truth": HiddenTruth(np.zeros(3, dtype=np.uint8), np.zeros(3, dtype=np.uint8)),
        "shot_id": 0, "ledger_path": path, "sample_seed_identity": "three-leg-sample", "context": {},
        "execution_controls": _relay_controls(belief_assemblies=100),
    }
    first = run_canonical_structural_shot(_three_leg_manifest("relay-three-leg"), **kwargs)
    before_replay = read_canonical_events(path)
    second = run_canonical_structural_shot(_three_leg_manifest("relay-three-leg"), **kwargs)

    assert first.termination == second.termination == "completed"
    assert read_canonical_events(path) == before_replay
    work = next(event["data"] for event in before_replay if event["kind"] == "work")
    leaves = work["relay_work_leaves"]
    assert [leaf["leg_index"] for leaf in leaves if leaf["kind"] == "leg"] == [0, 1, 1, 2, 2, 2]
    assert [leaf["leg_index"] for leaf in leaves if leaf["kind"] == "transfer"] == [1, 2]
    assert sum(leaf["work_vector"]["belief_assemblies"] for leaf in leaves if leaf["kind"] == "leg" and leaf["leg_index"] == 0) == 3
    assert sum(leaf["work_vector"]["belief_assemblies"] for leaf in leaves if leaf["kind"] == "leg" and leaf["leg_index"] == 1) == 6
    assert sum(leaf["work_vector"]["belief_assemblies"] for leaf in leaves if leaf["kind"] == "leg" and leaf["leg_index"] == 2) == 9
    assert WorkVector.sum(WorkVector.from_evidence(leaf["work_vector"], structural_event_version=2) for leaf in leaves) == WorkVector.from_evidence(work["work_vector"], structural_event_version=2)
    assert validate_phase4_shot(path, run_id="relay-three-leg", shot_id=0, trace_root=tmp_path)["work"] == work["work_vector"]


def test_budget_exhaustion_retains_partial_final_leg_work_with_exact_leaf_total(tmp_path):
    """A rejected second sweep leaves the first committed sweep on the final leg."""
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.canonical.verification import validate_phase4_shot
    from bp_registry.ledger import read_canonical_events
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    path = tmp_path / "partial-leg.jsonl"
    result = run_canonical_structural_shot(
        _three_leg_manifest("relay-partial-leg"), code=_impossible_syndrome_code(),
        observation=DecoderObservation("Z", np.ones(1, dtype=np.uint8)),
        hidden_truth=HiddenTruth(np.zeros(3, dtype=np.uint8), np.zeros(3, dtype=np.uint8)),
        shot_id=0, ledger_path=path, sample_seed_identity="partial-leg-sample", context={},
        execution_controls=_relay_controls(belief_assemblies=12),
    )

    assert result.termination == "budget_exhausted"
    work = next(event["data"] for event in read_canonical_events(path) if event["kind"] == "work")
    assert [row["iterations"] for row in work["relay_legs"]] == [1, 2, 1]
    assert [leaf["leg_index"] for leaf in work["relay_work_leaves"] if leaf["kind"] == "leg"] == [0, 1, 1, 2]
    assert [leaf["leg_index"] for leaf in work["relay_work_leaves"] if leaf["kind"] == "transfer"] == [1, 2]
    assert validate_phase4_shot(path, run_id="relay-partial-leg", shot_id=0, trace_root=tmp_path)["work"] == work["work_vector"]


def test_active_memory_tuning_is_seeded_per_leg_and_retains_actual_application_facts(tmp_path):
    """The controlled mode uses gamma0 first, then un-clipped seeded vectors."""
    from bp_registry.canonical.contracts import CanonicalManifestV4
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.ledger import read_canonical_events
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    raw = _three_leg_manifest("relay-active-memory").model_dump(mode="json")
    raw["relay"].update({
        "legs": [{"max_iterations": 2}, {"max_iterations": 2}, {"max_iterations": 2}],
        "first_leg_iteration_limit": 2,
        "later_leg_iteration_limit": 2,
        "later_leg_memory": "disordered",
        "fidelity_status": "controlled_component_adaptation",
        "memory_tuning": {
            "semantics": "relay_v022_dynamic_affine_prior_css_adaptation",
            "first_leg_gamma": 0.25,
            "later_leg_center": 1.0,
            "later_leg_width": 4.0,
            "seed_identity": "phase4-controlled-relay-memory-v1",
        },
    })
    manifest = CanonicalManifestV4.model_validate(raw)
    path = tmp_path / "active-memory.jsonl"
    result = run_canonical_structural_shot(
        manifest, code=_impossible_syndrome_code(),
        observation=DecoderObservation("Z", np.ones(1, dtype=np.uint8)),
        hidden_truth=HiddenTruth(np.zeros(3, dtype=np.uint8), np.zeros(3, dtype=np.uint8)),
        shot_id=0, ledger_path=path, sample_seed_identity="active-memory-sample", context={},
        execution_controls=_relay_controls(belief_assemblies=100),
    )

    assert result.termination == "completed"
    work = next(event["data"] for event in read_canonical_events(path) if event["kind"] == "work")
    memories = [row["memory"] for row in work["relay_legs"]]
    first, later_one, later_two = memories
    assert first["mode"] == "first_leg_uniform_gamma"
    assert first["declared_first_leg_gamma"] == 0.25
    assert first["gamma_count"] == 3
    assert first["gamma_min"] == first["gamma_max"] == 0.25
    for index, memory in enumerate((later_one, later_two), start=1):
        assert memory["mode"] == "later_leg_disordered_gamma"
        assert memory["leg_index"] == index
        assert memory["later_leg_center"] == 1.0
        assert memory["later_leg_width"] == 4.0
        assert memory["later_leg_low"] == -1.0
        assert memory["later_leg_high"] == 3.0
        assert memory["applied_each_source_iteration"] is True
        assert memory["gamma_count"] == 3
        assert isinstance(memory["derived_seed_identity"], str)
        assert isinstance(memory["pcg64_seed_hex"], str)
        assert -1.0 <= memory["gamma_min"] <= memory["gamma_max"] <= 3.0
    assert later_one["derived_seed_identity"] != later_two["derived_seed_identity"]


def test_active_memory_tuning_requires_a_controlled_adaptation_identity():
    """A source or canonical preset cannot silently acquire tuned semantics."""
    from bp_registry.canonical.contracts import RelaySpecV4

    with pytest.raises(ValueError, match="controlled_component_adaptation"):
        RelaySpecV4.model_validate({
            "total_leg_limit": 1, "legs": [{"max_iterations": 1}],
            "memory_tuning": {
                "semantics": "relay_v022_dynamic_affine_prior_css_adaptation",
                "first_leg_gamma": 0.0, "later_leg_center": 0.0,
                "later_leg_width": 2.0, "seed_identity": "controlled-seed",
            },
        })


def test_active_memory_changes_each_sweep_without_rebuilding_the_leg_schedule(monkeypatch):
    """Dynamic Relay memory updates the prior operand, not schedule topology."""
    import bp_registry.canonical.relay as relay_module
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.contracts import MemoryBindingV4, RelayLegSpec, RelayMemoryTuningV4
    from bp_registry.canonical.numerics import REFERENCE_CPU_F64
    from bp_registry.canonical.schedules import EdgeTable

    class Kernel:
        profile = REFERENCE_CPU_F64

        def prior(self, _error_rate):
            return 2.0

        def check_message(self, *_args, **_kwargs):
            return 1.0

        def variable_message(self, belief, check_message):
            return belief - check_message

        def candidate_from_beliefs(self, beliefs):
            return np.zeros(beliefs.size, dtype=np.uint8)

    original = relay_module.FloodingSchedule
    constructed: list[object] = []
    observed_priors: list[np.ndarray] = []

    class ObservingSchedule(original):
        def __init__(self, *args, **kwargs):
            constructed.append(self)
            super().__init__(*args, **kwargs)

        def sweep(self, *args, **kwargs):
            observed_priors.append(np.array(self.kernel._prior, copy=True))
            return super().sweep(*args, **kwargs)

    monkeypatch.setattr(relay_module, "FloodingSchedule", ObservingSchedule)
    controller = relay_module.RelayController(
        memory_bindings=(MemoryBindingV4(
            binding_id="relay-prior", kind="affine_prior", target="prior", order=0,
            alpha=0.875, state_lifetime="leg",
        ),),
        numerical_profile="cpu-float64-spa-v1",
        memory_tuning=RelayMemoryTuningV4(
            semantics="relay_v022_dynamic_affine_prior_css_adaptation",
            first_leg_gamma=0.5, later_leg_center=0.0, later_leg_width=0.0,
            seed_identity="schedule-reuse-fixture",
        ),
    )
    table = EdgeTable.from_edges(1, 3, [(0, 0), (0, 1), (0, 2)])
    run = controller.run(
        edge_table=table, check_matrix=np.ones((1, 3), dtype=np.uint8),
        syndrome=np.ones(1, dtype=np.uint8), kernel=Kernel(), error_rate=0.1,
        legs=(RelayLegSpec(max_iterations=2), RelayLegSpec(max_iterations=2)),
        budgets=BudgetTree(limits=()), scope="attempt", lineage_prefix="active-schedule",
        solution_limit=2, sample_seed_identity="active-schedule-sample",
    )

    assert run.stopping_reason == "leg_limit"
    assert len(constructed) == 2
    assert len(observed_priors) == 4
    assert np.allclose(observed_priors[0], 2.0)
    assert np.allclose(observed_priors[1], 2.5)
    assert np.allclose(observed_priors[2], 2.0)
    assert np.allclose(observed_priors[3], 2.0)
