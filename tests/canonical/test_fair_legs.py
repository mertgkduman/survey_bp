"""Fair initial BP and source-informed extra-leg semantics."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from bp_registry.canonical.fair_legs import FairLegConfig, FairLegController
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64
from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule
from bp_registry.canonical.updates import MinSumUpdate


H = np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
S = np.asarray([1, 0], dtype=np.uint8)


def _controller(**changes: object) -> FairLegController:
    controls = dict(initial_iterations=1, extra_iterations_per_unit=2,
                    max_extra_units=4, max_extra_c2v_updates=100,
                    v2c_gamma=0.5, beam_width=2, beam_rounds=2)
    controls.update(changes)
    return FairLegController(H, S, error_rate=0.1, config=FairLegConfig(**controls))


def test_matched_initial_is_single_owned_stage_and_extra_units_are_distinct():
    beam, relay = _controller().run_pair(sample_seed_identity="physical-0")
    assert beam.initial is relay.initial
    assert beam.initial.stage_id == "initial-bp"
    assert beam.initial_work == relay.initial_work
    assert not beam.initial.converged
    assert beam.units and relay.units
    assert all(unit.unit_id.startswith("beam-branch-") for unit in beam.units)
    assert all(unit.unit_id.startswith("relay-leg-") for unit in relay.units)
    assert all(unit.index >= 1 for unit in (*beam.units, *relay.units))
    assert all(unit.parent_id for unit in (*beam.units, *relay.units))
    assert beam.total_work == beam.initial_work + beam.extra_work
    assert relay.total_work == relay.initial_work + relay.extra_work
    for result in (beam, relay):
        if result.candidate is not None:
            assert np.array_equal(H @ result.candidate % 2, S)


def test_verified_initial_can_feed_later_continuations_without_initial_rerun(monkeypatch):
    initial = _controller().initial_bp()
    continuation = _controller()
    continuation.adopt_verified_initial(initial)
    original = continuation._bp_segment

    def count_only_continuations(*, stage_id, **kwargs):
        assert stage_id != "initial-bp"
        return original(stage_id=stage_id, **kwargs)

    monkeypatch.setattr(continuation, "_bp_segment", count_only_continuations)
    assert continuation.run_relay(initial, sample_seed_identity="physical-0").initial is initial
    assert continuation.run_beam(initial).initial is initial
    with pytest.raises(ValueError, match="already"):
        continuation.adopt_verified_initial(initial)


def test_initial_success_stops_both_without_extra_work():
    zero = np.zeros(2, dtype=np.uint8)
    controller = FairLegController(H, zero, error_rate=0.1, config=FairLegConfig(initial_iterations=1))
    beam, relay = controller.run_pair(sample_seed_identity="physical-0")
    assert beam.initial is relay.initial
    assert beam.initial.converged
    assert beam.units == relay.units == ()
    assert beam.extra_work == relay.extra_work
    assert beam.stopping_reason == relay.stopping_reason == "initial_bp_converged"
    assert np.array_equal(beam.candidate, relay.candidate)


def test_gamma_one_matches_canonical_min_sum_and_half_damps_v2c():
    plain = _controller(v2c_gamma=1.0).initial_bp()
    kernel = BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
    reference = kernel.run(H, S, error_rate=0.1, max_iterations=1)
    assert np.array_equal(plain.candidate, reference.candidate)
    assert plain.iterations == reference.iterations
    table = EdgeTable.from_check_matrix(H)
    schedule = FloodingSchedule(table, kernel=kernel, profile=MIN_SUM_CPU_F64)
    old = schedule.initialize(0.1)
    fresh = schedule.sweep(old, S, error_rate=0.1).new_v2c
    half = _controller(v2c_gamma=0.5).initial_bp()
    assert np.allclose([row[2] for row in half.edge_messages], 0.5 * old + 0.5 * fresh)
    assert np.allclose([row[2] for row in plain.edge_messages], fresh)


def test_beam_path_score_normalizes_current_round_llrs_by_iterations():
    segment = _controller().initial_bp()
    summed = np.asarray([2.0, -4.0, 6.0])
    two_steps = replace(segment, sum_llr=summed, iterations=2)
    four_steps = replace(segment, sum_llr=summed, iterations=4)
    assert two_steps.reliability_score == 6.0
    assert four_steps.reliability_score == 3.0


def test_relay_uses_seeded_disordered_memory_and_resets_edge_history():
    controller = _controller(max_extra_units=2, solution_limit=3)
    initial = controller.initial_bp()
    first = controller.run_relay(initial, sample_seed_identity="physical-0")
    replay = controller.run_relay(initial, sample_seed_identity="physical-0")
    changed = controller.run_relay(initial, sample_seed_identity="physical-1")
    assert first.as_evidence() == replay.as_evidence()
    assert first.units[0].gamma_sha256 != changed.units[0].gamma_sha256
    assert -0.24 <= first.units[0].gamma_min <= first.units[0].gamma_max <= 0.66
    assert first.units[0].work.relay_transfers == 1
    assert first.units[0].segment is not None
    assert first.units[0].parent_id == "initial-bp"
    assert first.extra_work.check_to_variable_updates <= controller.config.max_extra_c2v_updates


def test_beam_branch_masks_variable_and_lifts_original_candidate():
    controller = _controller(max_extra_units=2, solution_limit=3)
    initial = controller.initial_bp()
    result = controller.run_beam(initial)
    assert len(result.units) == 2
    variable = initial.next_variable
    assert variable is not None
    assert [unit.segment.fixed for unit in result.units] == [((variable, 0),), ((variable, 1),)]
    for unit in result.units:
        segment = unit.segment
        assert segment is not None
        assert all(var != variable for _check, var, _value in segment.edge_messages)
        assert segment.candidate[variable] == segment.fixed[0][1]
        if segment.converged:
            assert np.array_equal(H @ segment.candidate % 2, S)
        assert segment.work.check_to_variable_updates <= 2 * EdgeTable.from_check_matrix(H[:, segment.unmasked]).edge_count


def test_shared_extra_work_ceiling_denies_full_sweep_for_both_modes():
    controller = _controller(max_extra_c2v_updates=1)
    initial = controller.initial_bp()
    beam = controller.run_beam(initial)
    relay = controller.run_relay(initial, sample_seed_identity="physical-0")
    assert beam.units[0].status == relay.units[0].status == "denied"
    assert beam.extra_work.check_to_variable_updates == relay.extra_work.check_to_variable_updates == 0
    assert beam.stopping_reason == relay.stopping_reason == "shared_work_budget"


def test_invalid_controls_and_duplicate_masks_fail_closed():
    with pytest.raises(ValueError):
        FairLegConfig(v2c_gamma=0.0)
    with pytest.raises(ValueError):
        FairLegConfig(relay_gamma_low=1.0, relay_gamma_high=0.0)
    controller = _controller()
    with pytest.raises(ValueError, match="distinct"):
        controller._bp_segment(fixed=((1, 0), (1, 1)), iterations=1, stage_id="bad")


def test_beam_keeps_full_branch_lineage_and_charges_pruning():
    impossible_h = np.asarray([[1, 1, 0], [0, 0, 0]], dtype=np.uint8)
    impossible_s = np.asarray([1, 1], dtype=np.uint8)
    config = FairLegConfig(initial_iterations=1, extra_iterations_per_unit=1,
                           max_extra_units=4, max_extra_c2v_updates=100,
                           v2c_gamma=0.5, beam_width=1, beam_rounds=2)
    controller = FairLegController(impossible_h, impossible_s, error_rate=0.1, config=config)
    result = controller.run_beam(controller.initial_bp())
    assert result.candidate is None
    assert len(result.units) == 4
    assert sum(unit.status == "pruned" for unit in result.units) == 2
    assert result.extra_work.branch_expansions == 4
    assert result.extra_work.branch_prunes == 2
    assert result.units[2].parent_id in {result.units[0].unit_id, result.units[1].unit_id}
    assert result.units[3].parent_id == result.units[2].parent_id


def test_relay_memory_and_v2c_damping_are_separate_equations():
    from hashlib import sha256

    controller = _controller(max_extra_units=1, solution_limit=2, extra_iterations_per_unit=1)
    initial = controller.initial_bp()
    result = controller.run_relay(initial, sample_seed_identity="physical-0")
    leg = result.units[0].segment
    assert leg is not None
    seed = sha256(f"{controller.config.relay_seed}:physical-0:leg:1".encode()).digest()
    rng = np.random.Generator(np.random.PCG64(int.from_bytes(seed[:16], "big")))
    gamma = rng.uniform(controller.config.relay_gamma_low, controller.config.relay_gamma_high, H.shape[1])
    expected_prior = (1.0 - gamma) * controller.channel_prior + gamma * initial.posterior
    kernel = BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
    table = EdgeTable.from_check_matrix(H)
    schedule = FloodingSchedule(table, kernel=kernel, profile=MIN_SUM_CPU_F64)
    channel_messages = schedule.initialize(0.1)
    first = schedule.sweep(channel_messages, S, error_rate=0.1, prior_llrs=expected_prior)
    assert np.allclose([row[2] for row in leg.edge_messages],
                       0.5 * channel_messages + 0.5 * first.new_v2c)
    assert result.units[0].gamma_sha256 == sha256(np.asarray(gamma, dtype="<f8").tobytes()).hexdigest()


def test_extensions_reject_an_initial_state_from_another_controller():
    first = _controller()
    second = _controller()
    foreign = first.initial_bp()
    with pytest.raises(ValueError, match="exact matched initial"):
        second.run_beam(foreign)
    with pytest.raises(ValueError, match="exact matched initial"):
        second.run_relay(foreign, sample_seed_identity="physical-0")
