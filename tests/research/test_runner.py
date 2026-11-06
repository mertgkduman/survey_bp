from __future__ import annotations

import json
from pathlib import Path

import pytest

from bp_registry.research.contracts import interface_contract, materialize_experiment, validate_experiment
from bp_registry.research.runner import run_experiment


ROOT = Path(__file__).resolve().parents[2]


def specimen() -> dict:
    return {
        "schema": "research-experiment-v1", "id": "runner-fixture",
        "problem": {"kind": "css_code_capacity", "code": {"kind": "embedded_css", "hx": [[1, 1, 0]], "hz": [[0, 0, 1]], "lx": [[1, 0, 0]], "lz": [[1, 1, 0]]}},
        "channel": {"kind": "depolarizing"},
        "decoder": {"family": "binary_css", "implementation": "compiled", "variant": "plain", "rule": "sum_product", "numerical_profile": "binary-spa-flooding-f64-v2", "policy": None, "schedule": "flooding", "stop_on_convergence": True},
        "rate_points": [{"physical_p": 0.1, "decoder_p0": 0.1}],
        "sampling": {"seed": 7, "shot_start": 2, "shots": 2},
        "budgets": {"max_shots": 2, "max_iterations": 3},
        "provenance": {"relation": "development_fixture", "source_spec_id": None, "notes": None},
    }


def test_interface_contract_exposes_machine_constraints() -> None:
    contract = interface_contract()
    assert contract["defaults"]["binary"]["schedule"] == "flooding"
    assert contract["ui_fields"]["decoder_p0"]["exclusiveMinimum"] == 0
    assert contract["cross_rule_objects"]
    assert contract["rules_by_family"]["circuit_dem_bp"] == ["spa", "min_sum"]
    assert contract["circuit_rule_profiles"]["min_sum"] == "binary-min-sum-flooding-f64-v1"


def test_embedded_css_is_algebraically_validated() -> None:
    bad = specimen()
    bad["problem"]["code"]["hz"] = [[1, 0, 0]]
    with pytest.raises(ValueError, match="commute"):
        validate_experiment(bad)


def test_binary_full_block_runner_writes_immutable_bounded_outputs(tmp_path: Path) -> None:
    output = tmp_path / "result"
    summary = run_experiment(specimen(), output=output)
    assert summary["rows"][0]["n"] == 2
    assert {"requested-spec.json", "effective-spec.json", "events.jsonl", "summary.json", "summary.csv", "result-manifest.json", "run-manifest.json", "status.json"} <= {path.name for path in output.iterdir()}
    assert json.loads((output / "status.json").read_text())["status"] == "completed"
    events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    assert len(events) == 2
    assert all("candidate_x" in row and "candidate_z" in row for row in events)
    assert all(row["termination_reason"] and row["lineage"]["candidate"] for row in events)
    aggregate = summary["rows"][0]
    assert aggregate["exact_successes"] + aggregate["stabilizer_equivalent_successes"] + aggregate["failures"] == 2
    assert aggregate["type_i"] + aggregate["type_ii"] <= aggregate["failures"]
    assert aggregate["work_unit"] == "binary_component_sweeps"
    assert aggregate["converged_shots"] + aggregate["unconverged_shots"] == 2
    assert "lazy Numba JIT" in summary["timing_note"]
    with pytest.raises(FileExistsError):
        run_experiment(specimen(), output=output)


def test_retired_three_qubit_fixture_is_not_a_public_registered_code() -> None:
    value = specimen()
    value["problem"]["code"] = {"kind": "registered", "id": "three-qubit"}
    with pytest.raises(ValueError, match="unavailable"):
        materialize_experiment(value, ROOT)


def test_bp4_frozen_v1_plain_profile_uses_independent_pauli_evaluation(tmp_path: Path) -> None:
    value = specimen()
    value["problem"]["kind"] = "pauli_code_capacity"
    value["decoder"] = {"family": "bp4", "implementation": "compiled", "variant": "plain", "rule": "sum_product", "numerical_profile": "quaternary-bp4-f64-v1", "policy": None, "schedule": "flooding", "stop_on_convergence": True}
    value["sampling"]["shots"] = 1
    value["budgets"]["max_shots"] = 1
    summary = run_experiment(value, output=tmp_path / "bp4")
    assert summary["rows"][0]["n"] == 1
    event = json.loads((tmp_path / "bp4/events.jsonl").read_text())
    assert event["family"] == "bp4" and "candidate" in event
    assert summary["rows"][0]["work_unit"] == "bp4_joint_sweeps"


def test_bp4_default_min_sum_policy_is_recorded_not_silently_dropped(tmp_path: Path) -> None:
    value = specimen()
    value["problem"]["kind"] = "pauli_code_capacity"
    value["decoder"] = {"family": "bp4", "implementation": "compiled", "variant": "plain", "rule": "min_sum", "numerical_profile": "quaternary-bp4-f64-v2", "policy": None, "schedule": "flooding", "stop_on_convergence": True}
    value["sampling"]["shots"] = value["budgets"]["max_shots"] = 1
    summary = run_experiment(value, output=tmp_path / "bp4-ms")
    assert summary["effective_configuration"]["check_rule"] == "min_sum"
    assert summary["effective_configuration"]["resolution"]["format"] == "int8"


def test_resolution_policy_and_effective_quantized_coefficients_are_honored(tmp_path: Path) -> None:
    value = specimen()
    value["decoder"].update({"rule": "min_sum", "policy": {
        "version": "bp-flooding-policy-v1", "check_rule": "min_sum",
        "resolution": {"version": "bp-resolution-v1", "format": "int8", "scale": 16, "scope": "all_messages", "coefficients": "same"},
        "damping": .1, "alpha": .9, "beta": .1, "hard_decision": "min_llr", "zero_syndrome_shortcut": True,
    }})
    summary = run_experiment(value, output=tmp_path / "q8")
    coefficients = summary["effective_configuration"]["x_component"]["effective_coefficients"]
    assert coefficients == {"old_weight": .125, "fresh_weight": .875, "alpha": .875, "beta": .125}


def test_qbpgd_total_budget_and_binary_fixed_stopping_are_rejected() -> None:
    value = specimen()
    value["problem"]["kind"] = "pauli_code_capacity"
    value["decoder"] = {"family": "bp4", "implementation": "compiled", "variant": "qbpgd", "rule": "sum_product", "numerical_profile": "quaternary-bp4-f64-v2", "policy": None, "schedule": "flooding", "stop_on_convergence": True, "qbpgd": {"iterations_per_round": 3, "epsilon": 1e-6, "round_limit": 3}}
    value["budgets"]["max_iterations"] = 8
    with pytest.raises(ValueError, match="total max_iterations"):
        validate_experiment(value)
    binary = specimen()
    binary["decoder"]["stop_on_convergence"] = False
    with pytest.raises(ValueError, match="stop_on_convergence"):
        validate_experiment(binary)


def test_bounded_qbpgd_executes_with_the_result_iterations_field(tmp_path: Path) -> None:
    value = specimen()
    value["problem"]["kind"] = "pauli_code_capacity"
    value["decoder"] = {"family": "bp4", "implementation": "compiled", "variant": "qbpgd", "rule": "sum_product", "numerical_profile": "quaternary-bp4-f64-v2", "policy": None, "schedule": "flooding", "stop_on_convergence": True, "qbpgd": {"iterations_per_round": 1, "epsilon": 1e-6, "round_limit": 2}}
    value["sampling"]["shots"] = value["budgets"]["max_shots"] = 1
    value["budgets"]["max_iterations"] = 2
    summary = run_experiment(value, output=tmp_path / "qbpgd")
    event = json.loads((tmp_path / "qbpgd/events.jsonl").read_text())
    assert event["iterations"] <= 2
    assert summary["rows"][0]["work_unit"] == "bp4_joint_sweeps"


def test_zero_and_noncommuting_embedded_codes_are_rejected() -> None:
    zero = specimen()
    zero["problem"]["code"]["hx"] = []
    with pytest.raises(ValueError):
        validate_experiment(zero)
    noncommuting = specimen()
    noncommuting["problem"]["code"]["hz"] = [[1, 0, 0]]
    with pytest.raises(ValueError, match="commute"):
        validate_experiment(noncommuting)


def test_circuit_summary_partitions_observable_failures_by_detector_fit(tmp_path: Path) -> None:
    pytest.importorskip("stim")
    pytest.importorskip("sinter")
    value = {"schema": "research-experiment-v1", "id": "circuit-fixture",
        "problem": {"kind": "circuit", "circuit": {"kind": "inline_stim", "text": "R 0\nX_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]"}, "dem": {"decompose_errors": False}},
        "channel": {"kind": "embedded_circuit"}, "decoder": {"family": "circuit_dem_bp", "implementation": "canonical_sinter", "rule": "spa", "numerical_profile": "binary-spa-flooding-f64-v1", "schedule": "flooding", "max_iterations": 2, "tie_break": "zero"},
        "rate_points": [{"label": "embedded_circuit"}], "sampling": {"seed": 5, "shot_start": 1, "shots": 1}, "budgets": {"max_shots": 2, "max_iterations": 2}, "provenance": {"relation": "development_fixture", "source_spec_id": None, "notes": None}}
    summary = run_experiment(value, output=tmp_path / "circuit")
    row = summary["rows"][0]
    assert row["type_i"] + row["type_ii"] == row["failures"]
    assert row["work_unit"] == "circuit_dem_bp_sweeps"
    assert row["exact_successes"] is row["stabilizer_equivalent_successes"] is None
    assert row["observable_successes"] + row["failures"] == 1
    event = json.loads((tmp_path / "circuit/events.jsonl").read_text())
    assert event["outcome"] in {"observable_success", "observable_failure"}
    assert event["termination_reason"]


def test_circuit_shot_prefix_uses_one_shot_stim_chunks_for_stream_identity() -> None:
    stim = pytest.importorskip("stim")
    circuit = stim.Circuit("R 0\nX_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]")
    prefix = circuit.compile_detector_sampler(seed=21)
    for _ in range(3):
        prefix.sample(shots=1, separate_observables=True)
    actual = prefix.sample(shots=1, separate_observables=True)
    full = circuit.compile_detector_sampler(seed=21)
    expected = None
    for _ in range(4):
        expected = full.sample(shots=1, separate_observables=True)
    assert expected is not None
    assert (actual[0] == expected[0]).all() and (actual[1] == expected[1]).all()


@pytest.mark.parametrize("invalid", [0.2, 257, -255])
def test_custom_code_does_not_coerce_invalid_entries_to_uint8(invalid):
    value = specimen()
    value["problem"]["code"]["hx"][0][0] = invalid
    with pytest.raises(ValueError):
        validate_experiment(value)


def test_explicit_physical_probabilities_and_bp4_graph_validate_before_export():
    value = specimen()
    value["channel"] = {"kind": "explicit", "probabilities": [.5, .5]}
    value["rate_points"] = [{"decoder_p0": .1}]
    with pytest.raises(ValueError, match="shape|probabilit"):
        validate_experiment(value)
    value = specimen()
    value["problem"] = {"kind": "pauli_code_capacity", "code": {"kind": "embedded_css", "hx": [[1, 1, 0]], "hz": [[1, 1, 0]]}}
    value["decoder"]["family"] = "bp4"
    value["decoder"]["numerical_profile"] = "quaternary-bp4-f64-v2"
    with pytest.raises(ValueError, match="isolated"):
        validate_experiment(value)


def test_qbpgd_min_sum_policy_composes_with_guided_decimation():
    value = specimen()
    value["problem"]["kind"] = "pauli_code_capacity"
    value["decoder"].update(family="bp4", numerical_profile="quaternary-bp4-f64-v2", variant="qbpgd", rule="min_sum", qbpgd={"iterations_per_round": 1, "round_limit": 2, "epsilon": 1e-10})
    assert validate_experiment(value)["decoder"]["rule"] == "min_sum"


def test_inline_circuit_requires_real_stim_and_observables():
    pytest.importorskip("stim")
    value = json.loads((ROOT / "research/examples/circuit.json").read_text())
    for content in (123, "", "R 0\nM 0", "NOT_AN_INSTRUCTION 0"):
        value["problem"]["circuit"]["text"] = content
        with pytest.raises(ValueError):
            validate_experiment(value)


def test_interruption_preserves_request_implementation_and_partial_ledger(tmp_path, monkeypatch):
    from bp_registry.research import runner
    def interrupted(spec, code, *, emit=None, collect=True):
        emit({"kind": "interruption-test", "shot_id": 0})
        raise KeyboardInterrupt("test interruption")
    monkeypatch.setattr(runner, "_binary_rows", interrupted)
    output = tmp_path / "interrupted"
    with pytest.raises(KeyboardInterrupt):
        run_experiment(specimen(), output=output)
    assert json.loads((output / "status.json").read_text())["status"] == "failed_partial"
    assert json.loads((output / "run-manifest.json").read_text())["provenance"]["implementation_sha256"]
    assert (output / "events.jsonl").read_text()
    assert not (output / "summary.json").exists()


@pytest.mark.parametrize("family,profile", [("binary_css", "binary-spa-flooding-f64-v2"), ("bp4", "quaternary-bp4-f64-v1"), ("bp4", "quaternary-bp4-f64-v2")])
def test_custom_codes_without_supplied_logicals_use_row_space_evaluation(tmp_path, family, profile):
    value = specimen()
    del value["problem"]["code"]["lx"]
    del value["problem"]["code"]["lz"]
    value["decoder"].update(family=family, numerical_profile=profile)
    value["problem"]["kind"] = "pauli_code_capacity" if family == "bp4" else "css_code_capacity"
    result = run_experiment(value, output=tmp_path / family)
    assert result["rows"][0]["n"] == 2
    assert not result["input_identity"]["logical_basis_available"]


def test_sample_identity_includes_code_but_excludes_decoder_settings():
    import numpy as np
    from bp_registry.css import CssCode
    from bp_registry.research.runner import _sample_pauli
    first = CssCode(hx=np.array([[1, 1, 0]]), hz=np.array([[0, 0, 1]])).validate()
    second = CssCode(hx=np.array([[1, 0, 1]]), hz=np.array([[0, 1, 0]])).validate()
    kwargs = {"point": {"physical_p": .1, "decoder_p0": .1}, "channel": {"kind": "depolarizing"}, "seed": 7, "shot_id": 2, "point_index": 0}
    one = _sample_pauli(first, **kwargs)
    two = _sample_pauli(second, **kwargs)
    assert one.sample_identity != two.sample_identity
    kwargs["point"]["decoder_p0"] = .2
    assert _sample_pauli(first, **kwargs).sample_identity == one.sample_identity


def test_binary_identity_check_is_rejected_before_export():
    from bp_registry.research.export import package_files
    value = specimen()
    value["problem"]["code"] = {"kind": "embedded_css", "hx": [[0, 0, 0]], "hz": [[1, 1, 0]]}
    with pytest.raises(ValueError, match="identity-only"):
        validate_experiment(value)
    with pytest.raises(ValueError, match="identity-only"):
        package_files(value, repository=ROOT)


def test_registered_empty_check_family_is_explicitly_unsupported():
    import numpy as np
    from bp_registry.css import CssCode
    value = specimen()
    value["problem"]["code"] = {"kind": "registered", "id": "empty-x"}
    code = CssCode(hx=np.zeros((0, 3), dtype=np.uint8), hz=np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)).validate()
    with pytest.raises(ValueError, match="nonempty X and Z"):
        validate_experiment(value, repository={"empty-x": code})


def test_registered_zero_logicals_code_keeps_portable_input_shape(tmp_path):
    import numpy as np
    from bp_registry.css import CssCode
    value = specimen()
    value["problem"]["code"] = {"kind": "registered", "id": "zero-logicals"}
    code = CssCode(hx=np.array([[1, 1]], dtype=np.uint8), hz=np.array([[1, 1]], dtype=np.uint8), lx=np.zeros((0, 2), dtype=np.uint8), lz=np.zeros((0, 2), dtype=np.uint8)).validate()
    result = materialize_experiment(value, {"zero-logicals": code})
    validate_experiment(result)
    assert "lx" not in result["problem"]["code"]
    assert run_experiment(result, output=tmp_path / "zero-logicals")["rows"][0]["n"] == 2


def test_postprocessing_failure_marks_retained_events_as_partial(tmp_path, monkeypatch):
    from bp_registry.research import runner
    def broken_summary(*args, **kwargs):
        raise RuntimeError("test aggregation failure")
    monkeypatch.setattr(runner, "_summary_rows", broken_summary)
    output = tmp_path / "postprocess-failed"
    with pytest.raises(RuntimeError, match="aggregation"):
        run_experiment(specimen(), output=output)
    assert len((output / "events.jsonl").read_text().splitlines()) == 2
    assert json.loads((output / "status.json").read_text())["status"] == "failed_partial"
    assert not (output / "result-manifest.json").exists()


def test_circuit_min_sum_records_its_rule_specific_numerical_identity(tmp_path):
    pytest.importorskip("stim")
    pytest.importorskip("sinter")
    value = json.loads((ROOT / "research/examples/circuit.json").read_text())
    value["decoder"].update(rule="min_sum", numerical_profile="binary-min-sum-flooding-f64-v1")
    value["sampling"].update(shots=1, shot_start=0)
    value["budgets"]["max_shots"] = 1
    result = run_experiment(value, output=tmp_path / "circuit-ms")
    assert result["effective_configuration"]["numerical_profile"]["profile_id"] == "binary-min-sum-flooding-f64-v1"
    assert result["effective_configuration"]["numerical_profile"]["normalization"] == "min_sum"
    value["decoder"]["numerical_profile"] = "binary-spa-flooding-f64-v1"
    with pytest.raises(ValueError):
        validate_experiment(value)


@pytest.mark.parametrize("prior,seed,expected", [(.9, 5, "initial_candidate_fit"), (.5, 5, "iteration_cap")])
def test_circuit_zero_iterations_reports_initial_fit_or_cap(tmp_path, prior, seed, expected):
    pytest.importorskip("stim")
    pytest.importorskip("sinter")
    value = json.loads((ROOT / "research/examples/circuit.json").read_text())
    value["problem"]["circuit"]["text"] = f"R 0\nX_ERROR({prior}) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]\n"
    value["decoder"]["max_iterations"] = value["budgets"]["max_iterations"] = 0
    value["sampling"].update(seed=seed, shots=4, shot_start=0)
    value["budgets"]["max_shots"] = 4
    output = tmp_path / "initial"
    run_experiment(value, output=output)
    events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    assert all(row["termination_reason"] == ("initial_candidate_fit" if row["converged"] else "iteration_cap") for row in events)
    assert any(row["termination_reason"] == expected for row in events)


def test_portable_python_api_rejects_non_json_arrays_before_export(tmp_path):
    import numpy as np
    from bp_registry.research.export import package_files
    value = specimen()
    value["problem"]["code"]["hx"] = np.array(value["problem"]["code"]["hx"], dtype=np.uint8)
    with pytest.raises(ValueError, match="JSON-compatible"):
        validate_experiment(value)
    with pytest.raises(ValueError, match="JSON-compatible"):
        package_files(value, repository=ROOT)
    value = specimen()
    value["channel"] = {"kind": "explicit", "probabilities": np.array([.7, .1, .1, .1])}
    with pytest.raises(ValueError, match="JSON-compatible"):
        validate_experiment(value)


def test_unmodified_qbpgd_path_remains_the_frozen_v2_recurrence():
    import numpy as np
    from bp_registry.css import CssCode
    from bp_registry.quaternary.compiled import CompiledBp4Graph, _decode_qbpgd_v2
    from bp_registry.quaternary.numerics import QBP4_F64_V2
    code = CssCode(np.asarray([[1, 1]], dtype=np.uint8), np.asarray([[1, 1]], dtype=np.uint8)).validate()
    graph = CompiledBp4Graph.from_css(code, .1)
    syndrome = np.asarray([1, 0], dtype=np.uint8)
    expected = _decode_qbpgd_v2(graph.row_ptr, graph.variable_ptr, graph.variable_edges, graph.variables, graph.labels, graph.prior_llrs, syndrome, 1, 1e-10, 2, float("inf"), QBP4_F64_V2.product_epsilon, QBP4_F64_V2.v2c_damping)
    actual = graph.run_qbpgd(syndrome, iterations_per_round=1, epsilon=1e-10, round_limit=2)
    assert actual.candidate.tolist() == expected[0].tolist()
    assert (actual.iterations, actual.rounds, actual.fixations, actual.converged) == tuple(expected[1:])


def test_qbpgd_policy_recurrence_preserves_the_committed_message_trajectory_through_fixation():
    import numpy as np
    from bp_registry.css import CssCode
    from bp_registry.quaternary.compiled import CompiledBp4Graph
    from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy
    code = CssCode(np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8), np.asarray([[1, 1, 1]], dtype=np.uint8)).validate()
    baseline = CompiledBp4Graph.from_css(code, .1)
    policy = BpFloodingPolicy(check_rule="sum_product", resolution=ResolutionPolicy("float64", None, "all_messages"), damping=0., hard_decision="strict_pauli", zero_syndrome_shortcut=False)
    composed = CompiledBp4Graph.from_css(code, .1, policy=policy)
    syndrome = np.asarray([0, 0, 1], dtype=np.uint8)
    expected = baseline.run_qbpgd(syndrome, iterations_per_round=1, epsilon=1e-10, round_limit=3)
    actual = composed.run_qbpgd(syndrome, iterations_per_round=1, epsilon=1e-10, round_limit=3)
    assert expected.fixations == actual.fixations == 3
    assert (actual.candidate.tolist(), actual.iterations, actual.rounds, actual.converged) == (expected.candidate.tolist(), expected.iterations, expected.rounds, expected.converged)
