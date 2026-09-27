"""Numerical and transactional coverage for the public ordinary-memory path."""

import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.execution import AtomicFloodingExecutor
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.schedules import EdgeTable
from bp_registry.manifests import parse_manifest
from bp_registry.runner import _canonical_kernel_manifest


ROOT = Path(__file__).resolve().parents[2]


def composition(kind, parameters, *, order=0, binding_id="memory", assignment=None):
    target = {"affine_prior": "prior", "v2c_damping": "v2c",
              "pdbp_field_mix": "belief", "pdprime_delta_mix": "belief",
              "posterior_momentum": "posterior"}[kind]
    return MemoryCompositionSpec.model_validate({"bindings": [{
        "binding_id": binding_id, "kind": kind, "target": target,
        "parameters": parameters, "order": order, "history_owner": f"history:{binding_id}",
        "state_lifetime": "attempt", "advance_boundary": "source_iteration",
        "refresh_boundary": "attempt_start", "source_status": "canonical_adaptation",
        **({"assignment": assignment} if assignment is not None else {}),
    }]})


def test_public_projection_preserves_memory_in_executable_contract():
    value = json.loads((ROOT / "data/manifests/canonical-three-qubit-development.json").read_text())
    value.update(schema_version=4, memory=composition("affine_prior", {"alpha": 0.5}).model_dump(mode="json"))
    manifest = parse_manifest(value)
    compact = _canonical_kernel_manifest(manifest)
    assert compact["schema_version"] == 5
    assert compact["memory"] == value["memory"]


def make_schedule(kind, parameters):
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule
    table = (EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])
             if kind == "v2c_damping" else EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]))
    return MemoryFloodingSchedule(table, kernel=BinarySpaKernel(), memory=composition(kind, parameters))


@pytest.mark.parametrize("kind,parameters", [
    ("affine_prior", {"alpha": 0.5}), ("v2c_damping", {"gamma": 0.5}),
    ("pdbp_field_mix", {"gamma": 0.5}), ("pdprime_delta_mix", {"gamma": 0.5}),
    ("posterior_momentum", {"alpha": 0.5, "gamma": 0.5}),
])
def test_two_steps_match_scalar_equations_and_proposals_do_not_mutate_history(kind, parameters):
    schedule = make_schedule(kind, parameters)
    p = schedule.kernel.prior(0.1)
    messages = schedule.initialize(0.1)
    initial = schedule.evidence()
    syndrome = np.zeros(2, dtype=np.uint8) if kind == "v2c_damping" else np.array([1], dtype=np.uint8)
    first = schedule.sweep(messages, syndrome, error_rate=0.1)
    # A degree-two check with odd syndrome sends -p; raw posterior is zero.
    expected_first = 3.0*p if kind == "v2c_damping" else (0.0 if kind == "affine_prior" else (0.75*p if kind == "posterior_momentum" else 0.5*p))
    np.testing.assert_allclose(first.beliefs, expected_first, atol=1e-12)
    expected_messages = 1.5*p if kind == "v2c_damping" else expected_first+p
    np.testing.assert_allclose(first.new_v2c, expected_messages, atol=1e-12)
    assert schedule.evidence() == initial
    schedule.commit(first)
    second = schedule.sweep(first.new_v2c, syndrome, error_rate=0.1)
    expected_second = {"affine_prior": -0.5*p, "v2c_damping": 4.0*p,
                       "pdbp_field_mix": 0.0, "pdprime_delta_mix": 0.25*p,
                       "posterior_momentum": 0.25*p}[kind]
    np.testing.assert_allclose(second.beliefs, expected_second, atol=1e-12)
    if kind == "v2c_damping":
        np.testing.assert_allclose(second.new_v2c, 2.25*p, atol=1e-12)
    assert schedule.evidence()["committed_iterations"] == 1


def test_whole_sweep_budget_denial_preserves_memory_and_messages():
    schedule = make_schedule("pdbp_field_mix", {"gamma": 0.5})
    messages = schedule.initialize(0.1)
    initial = schedule.evidence()
    budgets = BudgetTree(limits=(BudgetLimit("attempt", "check_to_variable_updates", 2),), parents={})
    result = AtomicFloodingExecutor(schedule, budgets, scope="attempt").run_attempt(
        messages, np.array([1], dtype=np.uint8), error_rate=0.1, max_iterations=2,
    )
    assert result.iterations == 1
    assert result.termination.reason == "count_budget_exhausted"
    assert schedule.evidence()["committed_iterations"] == 1
    assert schedule.evidence()["history_sha256"] != initial["history_sha256"]
    np.testing.assert_array_equal(messages, np.full(2, schedule.kernel.prior(0.1)))
    before = schedule.evidence()
    denied_budgets = BudgetTree(limits=(BudgetLimit("attempt", "check_to_variable_updates", 0),), parents={})
    denied = AtomicFloodingExecutor(schedule, denied_budgets, scope="attempt").run_attempt(
        result.v2c, np.array([1], dtype=np.uint8), error_rate=0.1, max_iterations=1,
    )
    assert denied.iterations == 0
    assert schedule.evidence() == before


def test_failed_convergence_check_rolls_back_messages_work_and_memory():
    schedule = make_schedule("pdbp_field_mix", {"gamma": 0.5})
    messages = schedule.initialize(0.1)
    initial = schedule.evidence()
    budgets = BudgetTree(limits=(), parents={})

    def fail(_sweep):
        raise RuntimeError("injected check failure")

    with pytest.raises(RuntimeError, match="injected"):
        AtomicFloodingExecutor(schedule, budgets, scope="attempt").run_attempt(
            messages, np.array([1], dtype=np.uint8), error_rate=0.1, max_iterations=1, is_converged=fail,
        )
    assert schedule.evidence() == initial
    assert budgets.summary("attempt").check_to_variable_updates == 0
    np.testing.assert_array_equal(messages, np.full(2, schedule.kernel.prior(0.1)))


def test_new_attempt_rejects_an_old_uncommitted_proposal():
    schedule = make_schedule("pdbp_field_mix", {"gamma": 0.5})
    messages = schedule.initialize(0.1)
    proposal = schedule.sweep(messages, np.ones(1, dtype=np.uint8), error_rate=0.1)
    schedule.initialize(0.1)
    initial = schedule.evidence()
    with pytest.raises(ValueError, match="foreign or stale"):
        schedule.commit(proposal)
    assert schedule.evidence() == initial


def public_manifest(tmp_path, *, memory=True, iterations=1, cap=None):
    value = json.loads((ROOT / "data/manifests/canonical-three-qubit-development.json").read_text())
    value["run_id"] = "memory-execution-fixture" if memory else "memory-execution-baseline"
    value["randomness"]["physical_sample_identity"] = "memory-test-common-samples-4"
    value["budgets"]["max_shots"] = 1
    for scope in ("shot", "search", "attempt"):
        value["budgets"][scope]["max_iterations"] = iterations
    if cap:
        value["budgets"]["attempt"]["work_limits"].update(cap)
    if memory:
        value.update(schema_version=4, memory=composition("posterior_momentum", {"alpha": 0.1, "gamma": 0.9}).model_dump(mode="json"))
    path = tmp_path / f"{value['run_id']}.json"
    path.write_text(json.dumps(value))
    return path


def test_public_memory_changes_behavior_and_preserves_invalid_candidate(tmp_path):
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events
    baseline_path = public_manifest(tmp_path, memory=False)
    memory_path = public_manifest(tmp_path)
    baseline, output = tmp_path / "baseline", tmp_path / "memory"
    run_canonical(baseline_path, baseline)
    run_canonical(memory_path, output)
    assert verify_run(output)["final_row_count"] == 1
    base = next(event for event in read_canonical_events(baseline / "events.jsonl") if event["kind"] == "termination")
    terminal = next(event for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination")
    assert base["termination"] == "completed"
    assert terminal["termination"] == "max_iterations"
    assert terminal["data"]["diagnostic_candidate"] == [0, 0, 0]
    assert terminal["data"]["diagnostic_candidate_origin"] == "last_committed_sweep"
    assert terminal["data"]["outcome"] is None


@pytest.mark.parametrize("cap,count,diagnostic", [
    ({"bp_calls": 0}, 0, None),
    ({"check_to_variable_updates": 0}, 0, None),
    ({"check_to_variable_updates": 1}, 1, [0, 0, 0]),
])
def test_public_budget_replay_distinguishes_no_proposal_from_invalid_proposal(tmp_path, cap, count, diagnostic):
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events
    path = public_manifest(tmp_path, iterations=3, cap=cap)
    output = tmp_path / "output"
    run_canonical(path, output)
    assert verify_run(output)["final_row_count"] == 1
    terminal = next(event for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination")
    assert terminal["termination"] == "count_budget_exhausted"
    data = terminal["data"]
    assert data["diagnostic_candidate"] == diagnostic
    assert data.get("iterations", 0) == count
    if data["work_vector"]["bp_calls"]:
        assert data["memory_execution"]["committed_iterations"] == count


@pytest.mark.parametrize("field", ["history_sha256", "committed_iterations", "diagnostic_candidate"])
def test_semantic_replay_rejects_rehashed_memory_claims(tmp_path, field):
    from bp_registry.cli import run_canonical
    from bp_registry.ledger import read_canonical_events, _canonical_event_id
    from bp_registry.runner import canonical_public_shot_context
    from bp_registry.canonical.verification import validate_canonical_shot
    path = public_manifest(tmp_path)
    output = tmp_path / "output"
    run_canonical(path, output)
    events = list(read_canonical_events(output / "events.jsonl"))
    terminal = next(event for event in events if event["kind"] == "termination")
    if field == "diagnostic_candidate":
        terminal["data"][field] = [0, 0, 1]
    elif field == "committed_iterations":
        terminal["data"]["memory_execution"][field] = 2
    else:
        terminal["data"]["memory_execution"][field]["memory"] = "0" * 64
    terminal["event_id"] = _canonical_event_id(terminal)
    with pytest.raises(ValueError, match="memory execution|diagnostic candidate"):
        validate_canonical_shot(events, canonical_public_shot_context(path, shot_id=0))


@pytest.mark.parametrize("failed_iteration", [0, 1])
def test_numerical_failure_retains_and_replays_only_committed_memory_prefix(tmp_path, monkeypatch, failed_iteration):
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule
    from bp_registry.canonical.numerics import NumericalFailure
    from bp_registry.ledger import read_canonical_events
    path = public_manifest(tmp_path, iterations=3)
    output = tmp_path / "output"
    original = MemoryFloodingSchedule.sweep

    def failing(self, *args, **kwargs):
        if kwargs.get("source_iteration", 0) == failed_iteration:
            raise NumericalFailure("injected numerical failure")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(MemoryFloodingSchedule, "sweep", failing)
    run_canonical(path, output)
    assert verify_run(output)["final_row_count"] == 1
    data = next(event["data"] for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination")
    assert data["iterations"] == failed_iteration
    assert data["memory_execution"]["committed_iterations"] == failed_iteration
    assert data["work_vector"]["check_to_variable_updates"] == failed_iteration


def test_repeated_fields_use_disjoint_histories_and_explicit_order():
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule
    first = composition("pdbp_field_mix", {"gamma": 0.5}, binding_id="first").bindings[0]
    second = first.model_copy(update={"binding_id": "second", "history_owner": "history:second", "order": 1})
    schedule = MemoryFloodingSchedule(EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), kernel=BinarySpaKernel(), memory=MemoryCompositionSpec(bindings=(first, second)))
    initial = schedule.initialize(0.1)
    p = schedule.kernel.prior(0.1)
    step = schedule.sweep(initial, np.array([1], dtype=np.uint8), error_rate=0.1)
    np.testing.assert_allclose(step.beliefs, 0.75*p)
    schedule.commit(step)
    assert schedule.evidence()["history_sha256"]["first"] != schedule.evidence()["history_sha256"]["second"]
    step2 = schedule.sweep(step.new_v2c, np.array([1], dtype=np.uint8), error_rate=0.1)
    np.testing.assert_allclose(step2.beliefs, 0.3125*p)


@pytest.mark.parametrize("kind,assignment", [
    ("min_sum", None),
    ("normalized_min_sum", {"shape": "scalar", "value": 0.8}),
    ("normalized_min_sum", {"shape": "source_iteration", "values": [0.2, 0.5, 0.8]}),
    ("offset_min_sum", {"shape": "source_iteration", "values": [0.0, 5.0, 10.0]}),
])
def test_public_memory_preserves_min_sum_assignment_dispatch(tmp_path, kind, assignment):
    from bp_registry.cli import run_canonical, verify_run
    path = public_manifest(tmp_path, iterations=3)
    value = json.loads(path.read_text())
    value["numerical_profile"] = "cpu-float64-min-sum-v1"
    value["policies"]["update"]["kind"] = kind
    if assignment:
        value["policies"]["update"]["parameter_assignment"] = assignment
    path.write_text(json.dumps(value))
    output = tmp_path / "output"
    assert run_canonical(path, output)["final_row_count"] == 1
    assert verify_run(output)["final_row_count"] == 1


def test_offset_assignment_advances_with_memory_source_iteration():
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule
    from bp_registry.canonical.numerics import MIN_SUM_CPU_F64
    from bp_registry.canonical.updates import OffsetMinSumUpdate, ParameterAssignment
    schedule = MemoryFloodingSchedule(
        EdgeTable.from_edges(1, 1, [(0, 0)]),
        kernel=BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=OffsetMinSumUpdate(ParameterAssignment.model_validate({"shape": "source_iteration", "values": [0.0, 5.0, 10.0]}))),
        memory=composition("posterior_momentum", {"alpha": 0.1, "gamma": 0.9}),
    )
    messages = schedule.initialize(0.1)
    p = schedule.kernel.prior(0.1)
    for index, expected in enumerate([p-0.25, p-0.6725, p-1.196025]):
        step = schedule.sweep(messages, np.ones(1, dtype=np.uint8), error_rate=0.1, source_iteration=index)
        np.testing.assert_allclose(step.beliefs, expected, atol=1e-12)
        schedule.commit(step)
        messages = step.new_v2c


def test_normalized_assignment_advances_with_memory_source_iteration():
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule
    from bp_registry.canonical.numerics import MIN_SUM_CPU_F64
    from bp_registry.canonical.updates import NormalizedMinSumUpdate, ParameterAssignment

    schedule = MemoryFloodingSchedule(
        EdgeTable.from_edges(1, 1, [(0, 0)]),
        kernel=BinarySpaKernel(
            profile=MIN_SUM_CPU_F64,
            update_rule=NormalizedMinSumUpdate(ParameterAssignment.model_validate({
                "shape": "source_iteration", "values": [0.0, 0.5, 1.0],
            })),
        ),
        memory=composition("posterior_momentum", {"alpha": 0.1, "gamma": 0.9}),
    )
    rule = schedule.kernel.update_rule
    assert rule.check_to_variable(np.asarray([2.0]), syndrome=0, source_iteration=0) == 0.0
    assert rule.check_to_variable(np.asarray([2.0]), syndrome=0, source_iteration=1) == 1.0
    assert rule.check_to_variable(np.asarray([2.0]), syndrome=0, source_iteration=2) == 2.0
    messages = schedule.initialize(0.1)
    for index in range(3):
        step = schedule.sweep(messages, np.ones(1, dtype=np.uint8), error_rate=0.1, source_iteration=index)
        schedule.commit(step)
        messages = step.new_v2c
    assert schedule.evidence()["committed_iterations"] == 3


def test_disordered_affine_prior_assignment_is_decoder_local_replayed_and_atomic():
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule

    assignment = {
        "mode": "uniform", "low": 0.2, "high": 0.8,
        "root_seed_identity": "a" * 64,
    }
    memory = composition("affine_prior", {"alpha": 0.5}, assignment=assignment)
    table = EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)])
    first = MemoryFloodingSchedule(
        table, kernel=BinarySpaKernel(), memory=memory,
        trace_context={"configuration_identity": "arm-a", "decoder_identity": "shot-a"},
    )
    second = MemoryFloodingSchedule(
        table, kernel=BinarySpaKernel(), memory=memory,
        trace_context={"configuration_identity": "arm-a", "decoder_identity": "shot-a"},
    )
    syndrome = np.ones(1, dtype=np.uint8)
    for schedule in (first, second):
        start = schedule.initialize(0.1)
        proposal = schedule.sweep(start, syndrome, error_rate=0.1, source_iteration=0)
        assert schedule.evidence()["committed_iterations"] == 0
        schedule.commit(proposal)

    one = first.evidence()["assignment_evidence"]["memory"]
    two = second.evidence()["assignment_evidence"]["memory"]
    assert one == two
    assert one["algorithm"] == "numpy.PCG64"
    assert one["replay_identity"] == "shot-a:source_iteration:0"
    assert len(one["resolved_values"]) == table.variable_count
    assert all(0.2 <= value <= 0.8 for value in one["resolved_values"])


def test_public_disordered_affine_prior_records_assignment_evidence(tmp_path):
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    path = public_manifest(tmp_path, iterations=2)
    value = json.loads(path.read_text())
    value["memory"] = composition(
        "affine_prior", {"alpha": 0.5}, assignment={
            "mode": "uniform", "low": 0.1, "high": 0.9,
            "root_seed_identity": "b" * 64,
        },
    ).model_dump(mode="json")
    path.write_text(json.dumps(value))
    output = tmp_path / "disordered-public"
    assert run_canonical(path, output)["final_row_count"] == 1
    assert verify_run(output)["final_row_count"] == 1
    terminal = next(event["data"] for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination")
    assignment = terminal["memory_execution"]["assignment_evidence"]["memory"]
    assert assignment["algorithm"] == "numpy.PCG64"
    assert assignment["replay_identity"].endswith("source_iteration:0")
    assert len(assignment["resolved_values"]) == 3


@pytest.mark.parametrize("case,message", [
    ("local", "execution_schedule_unimplemented"),
    ("retained", "execution_lifecycle_unimplemented"),
    ("order", "execution_order_requires"),
    ("pdprime_after_prior", "pdprime_requires_fixed_prior"),
    ("short_offset", "execution_update_assignment_shorter"),
    ("beta", "requires exactly"),
])
def test_unimplemented_or_ambiguous_bindings_reject_before_artifact_loading(tmp_path, monkeypatch, case, message):
    from bp_registry import manifests
    path = public_manifest(tmp_path, iterations=3)
    value = json.loads(path.read_text())
    binding = value["memory"]["bindings"][0]
    if case == "local":
        value["policies"]["schedule"]["kind"] = "check_node_serial"
        value["memory"] = composition("v2c_damping", {"gamma": 0.5}).model_dump(mode="json")
        value["memory"]["bindings"][0]["advance_boundary"] = "local_update"
    elif case == "retained":
        binding["retain_history"] = True
    elif case in {"order", "pdprime_after_prior"}:
        first = composition("v2c_damping" if case == "order" else "affine_prior", {"gamma": 0.5} if case == "order" else {"alpha": 0.5}, binding_id="first").model_dump(mode="json")["bindings"][0]
        second = composition("affine_prior" if case == "order" else "pdprime_delta_mix", {"alpha": 0.5} if case == "order" else {"gamma": 0.5}, binding_id="second").model_dump(mode="json")["bindings"][0]
        second["order"] = 1
        value["memory"]["bindings"] = [first, second]
    elif case == "short_offset":
        value["numerical_profile"] = "cpu-float64-min-sum-v1"
        value["policies"]["update"]["kind"] = "offset_min_sum"
        value["policies"]["update"]["parameter_assignment"] = {"shape": "source_iteration", "values": [0.5]}
    else:
        binding["parameters"] = {"beta": 0.5}
    path.write_text(json.dumps(value))
    monkeypatch.setattr(manifests, "load_artifact", lambda *args, **kwargs: pytest.fail("invalid memory must reject before input loading"))
    with pytest.raises(ValueError, match=message):
        manifests.preflight(path)
