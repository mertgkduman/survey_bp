import json
import pickle

import numpy as np
import pytest
import sinter
import stim

from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.memory_execution import MemoryFloodingSchedule
from bp_registry.canonical.schedules import FloodingSchedule
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder


DEM = """error(0.1) D0 L0
error(0.2) D0 D1
error(0.7) D1 L1
error(1) D0 L1
error(0.3) L0"""


def memory(kind, parameters):
    return MemoryCompositionSpec.model_validate({"bindings": [{
        "binding_id": "test", "kind": kind,
        "target": {"affine_prior": "prior", "v2c_damping": "v2c", "pdbp_field_mix": "belief",
                   "pdprime_delta_mix": "belief", "posterior_momentum": "posterior"}[kind],
        "parameters": parameters, "order": 0, "history_owner": "history:test",
        "state_lifetime": "attempt", "advance_boundary": "source_iteration",
        "refresh_boundary": "attempt_start", "source_status": "canonical_adaptation"}]})


@pytest.mark.parametrize("rule,parameter", [("spa", 1.), ("min_sum", 1.),
                                           ("normalized_min_sum", .7), ("offset_min_sum", .3)])
@pytest.mark.parametrize("controller", ["single", "relay", "guided", "beam"])
def test_packed_projection_replay_and_pickle(rule, parameter, controller, tmp_path):
    policy = CircuitPolicy(rule=rule, parameter=parameter, controller=controller,
                           max_attempts=1 if controller == "single" else 5, max_iterations=3)
    factory = pickle.loads(pickle.dumps(PolicyBpSinterDecoder(policy)))
    decoder = factory.compile_decoder_for_dem(dem=stim.DetectorErrorModel(DEM))
    events = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], np.uint8)
    result = decoder.decode_detailed(events)
    expected = (result.faults @ decoder.model.observable_matrix.T) % 2 ^ decoder.model.observable_bias
    np.testing.assert_array_equal(result.predictions, expected)
    packed = decoder.decode_shots_bit_packed(bit_packed_detection_event_data=np.packbits(events, axis=1, bitorder="little"))
    np.testing.assert_array_equal(packed, np.packbits(expected, axis=1, bitorder="little"))
    path = tmp_path / "ledger.jsonl"
    result.write_ledger(path)
    assert decoder.verify_ledger(path)["verified"]
    with pytest.raises(FileExistsError):
        result.write_ledger(path)
    records = result.ledger
    records[1]["prediction"][0] ^= 1
    path.write_text("\n".join(json.dumps(row) for row in records))
    with pytest.raises(ValueError, match="replay"):
        decoder.verify_ledger(path)
    with pytest.raises(ValueError):
        result.faults.setflags(write=True)


@pytest.mark.parametrize("kind,parameters", [
    ("affine_prior", {"alpha": .6}), ("v2c_damping", {"gamma": .3}),
    ("pdbp_field_mix", {"gamma": .4}), ("pdprime_delta_mix", {"gamma": .2}),
    ("posterior_momentum", {"alpha": .8, "gamma": .2}),
])
def test_memory_matches_canonical_heterogeneous_sweep_and_resets(kind, parameters):
    policy = CircuitPolicy(memory=memory(kind, parameters), max_iterations=1)
    decoder = PolicyBpSinterDecoder(policy).compile_decoder_for_dem(dem=stim.DetectorErrorModel(DEM))
    model, kernel = decoder.model, policy.kernel()
    syndrome = np.array([1, 1], np.uint8)
    schedule = MemoryFloodingSchedule(model.table, kernel=kernel, memory=policy.memory)
    prior = model.prior_llrs.copy()
    old = schedule.initialize(.5, prior_llrs=prior)
    prior[:] = 999
    expected = schedule.sweep(old, syndrome, error_rate=.5, source_iteration=0)
    events = np.repeat((syndrome ^ model.syndrome_bias)[None], 2, axis=0)
    result = decoder.decode_detailed(events)
    for row in result.faults:
        np.testing.assert_array_equal(row, expected.candidate)
    for shot in result.ledger[1:]:
        attempt = shot["attempts"][0]
        np.testing.assert_allclose(attempt["posterior"], expected.beliefs, rtol=0, atol=0)
        assert attempt["memory"]["committed_iterations"] == 1
    assert result.ledger[1]["attempts"] == result.ledger[2]["attempts"]


@pytest.mark.parametrize("controller", ["guided", "beam"])
def test_unsatisfiable_problem_accounts_for_all_failed_branches(controller):
    decoder = PolicyBpSinterDecoder(CircuitPolicy(
        controller=controller, max_iterations=2, max_attempts=5, beam_width=2 if controller == "beam" else 1
    )).compile_decoder_for_dem(dem=stim.DetectorErrorModel("error(0.1) D0 D1\nerror(0.2) D0 D1 L0"))
    result = decoder.decode_detailed(np.array([[1, 0]], np.uint8))
    attempts = result.ledger[1]["attempts"]
    assert 1 < len(attempts) <= 5
    assert not result.converged[0]
    assert result.iterations[0] == sum(row["iterations"] for row in attempts)
    for attempt in attempts[1:]:
        assert attempt["parent"] < attempt["attempt"]
        assert len(set(attempt["fixed"])) == len(attempt["fixed"])
        assert attempt["work"]["c2v"] == 2 * decoder.model.table.edge_count


@pytest.mark.parametrize("dem", ["", "error(1) D0 L0", "detector D0\nlogical_observable L0"])
def test_empty_fault_space_zero_iterations_and_empty_batch(dem):
    decoder = PolicyBpSinterDecoder(CircuitPolicy(max_iterations=0)).compile_decoder_for_dem(dem=stim.DetectorErrorModel(dem))
    result = decoder.decode_detailed(np.zeros((3, decoder.model.table.check_count), np.uint8))
    assert not result.iterations.any()
    assert decoder.decode_detailed(np.zeros((0, decoder.model.table.check_count), np.uint8)).predictions.shape[0] == 0
    assert decoder.decode_shots_bit_packed(bit_packed_detection_event_data=np.zeros(
        (0, (decoder.model.table.check_count + 7) // 8), np.uint8)).shape[0] == 0


def test_direct_per_fault_sweep_and_prior_validation():
    decoder = PolicyBpSinterDecoder(CircuitPolicy(max_iterations=1)).compile_decoder_for_dem(dem=stim.DetectorErrorModel(DEM))
    kernel, model = decoder.policy.kernel(), decoder.model
    schedule = FloodingSchedule(model.table, kernel=kernel)
    with pytest.raises(ValueError, match="prior_llrs"):
        schedule.initialize(.5, prior_llrs=np.full(model.table.variable_count, np.nan))
    with pytest.raises(ValueError):
        CircuitPolicy(controller="relay", memory=memory("affine_prior", {"alpha": .5}))
    with pytest.raises(ValueError):
        CircuitPolicy(schedule="serial")
    with pytest.raises(ValueError):
        decoder.decode_detailed(np.zeros((1, 2), float))


def test_sinter_collect_with_custom_policy_decoder(tmp_path):
    circuit = stim.Circuit.generated("repetition_code:memory", distance=3, rounds=2, before_round_data_depolarization=.05)
    stats = sinter.collect(num_workers=1, tasks=[sinter.Task(circuit=circuit)], decoders=["policy"],
                          custom_decoders={"policy": PolicyBpSinterDecoder(CircuitPolicy(
                              rule="normalized_min_sum", parameter=.8, max_iterations=4), ledger_directory=str(tmp_path))},
                          max_shots=12, max_batch_size=4)
    assert len(stats) == 1 and stats[0].shots == 12
    ledgers = list(tmp_path.glob("*.jsonl"))
    assert ledgers and sum(len(path.read_text().splitlines()) - 1 for path in ledgers) == 12


@pytest.mark.parametrize("rule,parameter", [("spa", 1.), ("min_sum", 1.),
                                           ("normalized_min_sum", .7), ("offset_min_sum", .3)])
def test_compiled_attempt_matches_scalar_with_extreme_heterogeneous_priors(rule, parameter):
    dem = stim.DetectorErrorModel(DEM + "\nerror(1e-40) D0\nerror(0.9999999) D1")
    policy = CircuitPolicy(rule=rule, parameter=parameter, max_iterations=7)
    scalar = PolicyBpSinterDecoder(policy.model_copy(update={"backend": "scalar"})).compile_decoder_for_dem(dem=dem)
    compiled = PolicyBpSinterDecoder(policy.model_copy(update={"backend": "compiled"})).compile_decoder_for_dem(dem=dem)
    events = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], np.uint8)
    a, b = scalar.decode_detailed(events), compiled.decode_detailed(events)
    np.testing.assert_array_equal(a.faults, b.faults)
    np.testing.assert_array_equal(a.iterations, b.iterations)
    np.testing.assert_array_equal(a.converged, b.converged)
    for x, y in zip(a.ledger[1:], b.ledger[1:]):
        np.testing.assert_allclose(x["attempts"][0]["posterior"], y["attempts"][0]["posterior"], atol=1e-13, rtol=1e-13)


def test_result_replacement_cannot_keep_stale_evidence():
    from dataclasses import replace
    decoder = PolicyBpSinterDecoder().compile_decoder_for_dem(dem=stim.DetectorErrorModel(DEM))
    result = decoder.decode_detailed(np.zeros((1, 2), np.uint8))
    with pytest.raises(ValueError, match="ledger"):
        replace(result, predictions=result.predictions ^ 1)
