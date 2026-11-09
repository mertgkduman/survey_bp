"""Cross-regime policy qualification with heterogeneous signed channels."""
import json
from dataclasses import asdict
from itertools import product

import numpy as np
import pytest
import stim

from bp_registry.canonical.policy_decoder import BinaryPolicy, BinaryPolicyDecoder
from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.schedules import EdgeTable
from bp_registry.canonical.updates import ParameterAssignment
from bp_registry.circuit import SharedPolicySinterDecoder


CONTROLLERS = {
    "guided_decimation": dict(kind="guided_decimation", variant="algorithm1_v2_interpretation",
        source_revision="arxiv:2312.10950v2", finite_bias_magnitude=25.0,
        zero_rule="positive_prior_for_zero_posterior", final_round_rule="return_after_last_fixation",
        round_limit=2, sweeps_per_round=1),
    "impulse": dict(realization="exact_shortening", selection="minimum_original_weight",
                    baseline_sweeps=1, attempt_sweeps=1, attempt_cap=2),
    "freezing": dict(period_sweeps=1, lifetime_sweeps=1, retry_cap=2, root_seed="freeze"),
    "syndrome_flip": dict(baseline_sweeps=2, attempt_sweeps=1, top_k=2, max_weight=1, test_cap=2, root_seed="sf"),
    "sign_flip": dict(alpha=0.875, trunk_sweeps=1, continuation_sweeps=1),
    "restart_belief": dict(preset="source_exact_distance", code_id="declared-test-code",
        eta=1, t_cap=1, root_sweeps=1, residual_sweeps=1, exact_distance=3),
    "mbbp": dict(bases=[dict(member_id="base", local_ordinal=0, partition_identity="explicit",
        permutation_identity="identity", redundant_transforms=[[1, 1]])], max_iterations=2),
    "beam": dict(initial_iterations=1, extra_iterations_per_unit=1, max_extra_units=2),
    "relay": dict(legs=[dict(max_iterations=2), dict(max_iterations=2)],
        memory_bindings=[dict(binding_id="relay", kind="affine_prior", target="prior",
                             order=0, alpha=0.5, state_lifetime="leg")]),
}


def memory(kind, local=False):
    target = dict(affine_prior="prior", pdbp_field_mix="belief", pdprime_delta_mix="belief",
                  posterior_momentum="posterior", v2c_damping="v2c")[kind]
    params = dict(alpha=0.5) if kind == "affine_prior" else dict(gamma=0.5)
    if kind == "posterior_momentum":
        params["alpha"] = 0.5
    return MemoryCompositionSpec.model_validate(dict(bindings=[dict(binding_id="memory", kind=kind,
        target=target, parameters=params, order=0, history_owner="history:memory", state_lifetime="attempt",
        advance_boundary="local_update" if local and kind != "affine_prior" else "source_iteration",
        refresh_boundary="attempt_start", source_status="canonical_adaptation")]))


def policies():
    for schedule in ("flooding", "layered", "check_node_serial", "variable_node_serial"):
        for rule in ("spa", "min_sum", "normalized_min_sum", "offset_min_sum"):
            yield BinaryPolicy(schedule=schedule, rule=rule, max_iterations=3, backend="scalar",
                               partitions=((0,), (1,)) if schedule == "layered" else None)
        for kind in ("affine_prior", "pdbp_field_mix", "pdprime_delta_mix", "posterior_momentum", "v2c_damping"):
            yield BinaryPolicy(schedule=schedule, max_iterations=3, backend="scalar",
                               partitions=((0,), (1,)) if schedule == "layered" else None,
                               memory=memory(kind, local=schedule != "flooding"))
        if schedule != "flooding":
            for refresh in ("configuration", "attempt", "sweep"):
                yield BinaryPolicy(schedule=schedule, randomized=refresh, max_iterations=3,
                                   partitions=((0,), (1,)) if schedule == "layered" else None)
    for schedule in ("group_shuffled", "residual"):
        yield BinaryPolicy(schedule=schedule, max_iterations=3)
    for kind, options in CONTROLLERS.items():
        yield BinaryPolicy(controller=kind, options=options)


@pytest.mark.parametrize("policy", list(policies()))
def test_cpu_circuit_same_execution_and_reset(policy, tmp_path):
    # Duplicate detector rows permit both satisfiable and unsatisfiable inputs;
    # unequal signed priors expose accidental uniform-channel initialization.
    dem = stim.DetectorErrorModel("error(0.1) D0 D1 L0\nerror(0.7) D0 D1\nerror(1) L1")
    decoder = SharedPolicySinterDecoder(policy).compile_decoder_for_dem(dem=dem)
    events = np.array(list(product((0, 1), repeat=2)), dtype=np.uint8)
    batch = decoder.decode_detailed(events)
    cpu = BinaryPolicyDecoder(np.ones((2, 2), dtype=np.uint8), policy)
    for i, event in enumerate(events):
        result = cpu.decode(event, prior_llrs=decoder.model.prior_llrs,
                            shot_identity=batch.ledger[i + 1]["binary_execution"]["shot_identity"])
        assert result.ledger == batch.ledger[i + 1]["binary_execution"]
        assert result.converged == np.array_equal((cpu.h @ result.candidate) % 2, event)
        assert cpu.verify_ledger(result.ledger_json)
    np.testing.assert_array_equal(batch.predictions[:, 0], batch.faults[:, 0])
    np.testing.assert_array_equal(batch.predictions[:, 1], 1)
    assert decoder.decode_detailed(events).ledger_json == batch.ledger_json
    path = tmp_path / "ledger.jsonl"
    batch.write_ledger(path)
    assert decoder.verify_ledger(path)["verified"]
    packed = decoder.decode_shots_bit_packed(bit_packed_detection_event_data=np.packbits(events, axis=1, bitorder="little"))
    np.testing.assert_array_equal(np.unpackbits(packed, axis=1, count=2, bitorder="little"), batch.predictions)


@pytest.mark.parametrize("rule", ["spa", "min_sum", "normalized_min_sum", "offset_min_sum"])
def test_compiled_scalar_heterogeneous_parity(rule):
    rng = np.random.default_rng(827)
    h = np.array([[1, 1, 0, 1], [0, 1, 1, 0]], dtype=np.uint8)
    for _ in range(12):
        prior = rng.uniform(-60, 60, 4)
        syndrome = rng.integers(0, 2, 2, dtype=np.uint8)
        a = BinaryPolicyDecoder(h, BinaryPolicy(rule=rule, backend="compiled", max_iterations=4)).decode(syndrome, prior_llrs=prior)
        b = BinaryPolicyDecoder(h, BinaryPolicy(rule=rule, backend="scalar", max_iterations=4)).decode(syndrome, prior_llrs=prior)
        np.testing.assert_array_equal(a.candidate, b.candidate)
        assert (a.iterations, a.converged) == (b.iterations, b.converged)
        np.testing.assert_allclose(a.ledger["execution"]["posterior"], b.ledger["execution"]["posterior"], atol=1e-10)


def test_single_check_spa_against_enumerated_distribution():
    prior = np.array([0.8, -1.3, 2.2])
    h = np.ones((1, 3), dtype=np.uint8)
    for syndrome in (0, 1):
        result = BinaryPolicyDecoder(h, BinaryPolicy(backend="scalar", max_iterations=1)).decode([syndrome], prior_llrs=prior)
        if result.iterations == 0:
            continue  # Explicit prior shortcut, before a factor update.
        weights = {bits: np.exp(-np.dot(prior, bits)) for bits in product((0, 1), repeat=3) if sum(bits) % 2 == syndrome}
        posterior = [np.log(sum(w for b, w in weights.items() if b[j] == 0) /
                            sum(w for b, w in weights.items() if b[j] == 1)) for j in range(3)]
        np.testing.assert_allclose(result.ledger["execution"]["posterior"], posterior, atol=1e-12)


@pytest.mark.parametrize("shape", ["source_iteration", "check", "edge"])
def test_assignment_admission_and_execution(shape):
    h = np.ones((2, 2), dtype=np.uint8)
    table = EdgeTable.from_check_matrix(h)
    assignment = ParameterAssignment(shape=shape, values=(0.0, 0.5) if shape != "edge" else (0.0, 0.2, 0.5, 0.9),
                                    graph_sha256=None if shape == "source_iteration" else table.graph_sha256)
    decoder = BinaryPolicyDecoder(h, BinaryPolicy(rule="normalized_min_sum", parameter=assignment, max_iterations=2))
    result = decoder.decode([0, 1], prior_llrs=[2.0, 1.0])
    assert result.iterations == 2
    assert decoder.verify_ledger(result.ledger_json)
    if shape != "source_iteration":
        with pytest.raises(ValueError, match="graph"):
            BinaryPolicyDecoder(np.eye(2, dtype=np.uint8), decoder.policy)


def test_closed_admission_snapshot_and_replay_rejection():
    with pytest.raises(ValueError, match="compiled"):
        BinaryPolicy(schedule="check_node_serial", backend="compiled")
    with pytest.raises(ValueError, match="unknown"):
        BinaryPolicy(controller="beam", options={"unused": 1})
    with pytest.raises(ValueError, match="own"):
        BinaryPolicy(controller="beam", max_iterations=2)
    policy = BinaryPolicy(controller="freezing", options=CONTROLLERS["freezing"].copy())
    decoder = BinaryPolicyDecoder(np.ones((2, 2), dtype=np.uint8), policy)
    policy.options["retry_cap"] = 50
    decoder.policy.options["retry_cap"] = 99
    assert decoder.policy.options["retry_cap"] == 2
    result = decoder.decode([0, 1], prior_llrs=[2., -1.])
    tampered = result.ledger
    tampered["candidate"][0] ^= 1
    with pytest.raises(ValueError, match="replay"):
        decoder.verify_ledger(json.dumps(tampered))


def test_explicit_prior_session_reset_mapping_and_ownership():
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.budgets import BudgetTree
    prior = np.array([2., -3., 4.])
    table = EdgeTable.from_check_matrix(np.array([[1, 1, 1]], dtype=np.uint8))
    session = BpSession(table, np.array([1], dtype=np.uint8), error_rate=.1, prior_llrs=prior)
    prior[:] = 88
    np.testing.assert_array_equal(session.state.prior, [2., -3., 4.])
    tree = BudgetTree(limits=(), parents={})
    child = session.reset_fresh(budgets=tree, leaf_id="same")
    np.testing.assert_array_equal(child.state.prior, session.state.prior)
    shortened = EdgeTable.from_check_matrix(np.array([[1, 1]], dtype=np.uint8))
    with pytest.raises(ValueError, match="mapped"):
        session.reset_fresh(budgets=tree, leaf_id="bad", edge_table=shortened)
    branch = session.reset_fresh(budgets=tree, leaf_id="mapped", edge_table=shortened, prior_llrs=session.state.prior[[0, 2]])
    np.testing.assert_array_equal(branch.state.prior, [2., 4.])
    with pytest.raises(ValueError):
        branch.state.prior.setflags(write=True)


@pytest.mark.parametrize("scope", ["configuration", "attempt", "source_iteration"])
@pytest.mark.parametrize("schedule", ["flooding", "check_node_serial"])
def test_generated_parameters_refresh_only_at_declared_boundary(scope, schedule):
    from bp_registry.canonical.updates import ParameterRefreshPlan, ParameterGeneratorSpec
    h = np.ones((2, 2), dtype=np.uint8)
    generator = ParameterGeneratorSpec(shape="edge", graph_sha256=EdgeTable.from_check_matrix(h).graph_sha256,
        distribution="uniform", low=0.2, high=0.9, root_seed_identity="a" * 64)
    p = BinaryPolicy(rule="normalized_min_sum", schedule=schedule, max_iterations=3,
                     parameter_refresh=ParameterRefreshPlan(scope=scope, generator=generator))
    d = BinaryPolicyDecoder(h, p)
    result = d.decode([0, 1], prior_llrs=[2., -1.])
    records = result.ledger["execution"]["parameter_refreshes"]
    assert len(records) == (3 if scope == "source_iteration" else 1)
    assert [r["source_iteration"] for r in records] == list(range(len(records)))
    assert d.verify_ledger(result.ledger_json)


@pytest.mark.parametrize("kind", ["guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief"])
def test_existing_damped_controller_counterparts(kind):
    d = BinaryPolicyDecoder(np.ones((2, 2), dtype=np.uint8),
        BinaryPolicy(controller=kind, options=CONTROLLERS[kind], damping_gamma=0.5))
    result = d.decode([0, 1], prior_llrs=[2., -1.])
    assert not result.converged
    assert result.iterations > 0
    assert d.verify_ledger(result.ledger_json)


@pytest.mark.parametrize("tie_bit", [0, 1])
def test_existing_mbbp_voting_validates_aggregate(tie_bit):
    d = BinaryPolicyDecoder(np.ones((2, 2), dtype=np.uint8),
        BinaryPolicy(controller="mbbp", options=CONTROLLERS["mbbp"], vote_tie_bit=tie_bit))
    result = d.decode([0, 1], prior_llrs=[2., -1.])
    assert "vote_decision" in result.ledger["execution"]
    assert not result.converged
    assert d.verify_ledger(result.ledger_json)


@pytest.mark.parametrize("format_name", ["float16", "float32", "float64", "int8", "int16", "int32"])
@pytest.mark.parametrize("scope", ["scalar_edges", "all_messages", "all_state"])
@pytest.mark.parametrize("check_rule", ["sum_product", "min_sum"])
def test_vector_precision_policies_match_existing_uniform_contract(format_name, scope, check_rule):
    from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy
    from bp_registry.canonical.compiled import CompiledBinaryFlooding
    h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    fp = BpFloodingPolicy(check_rule=check_rule, resolution=ResolutionPolicy(format_name,
        16 if format_name.startswith("int") else None, scope, "same"), damping=.25,
        alpha=.75 if check_rule == "min_sum" else 1., beta=.25 if check_rule == "min_sum" else 0.,
        version="bp-flooding-policy-v3" if check_rule == "sum_product" else "bp-flooding-policy-v2",
        check_stabilization="log_domain" if check_rule == "sum_product" else "exact_unity", product_epsilon=1e-10)
    canonical = CompiledBinaryFlooding.from_check_matrix(h, rule="spa" if check_rule == "sum_product" else "min_sum", policy=fp)
    d = BinaryPolicyDecoder(h, BinaryPolicy(flooding_policy=fp, max_iterations=3))
    for s in product((0, 1), repeat=2):
        syndrome = np.asarray(s, dtype=np.uint8)
        a, b = canonical.run(syndrome, error_rate=.7, max_iterations=3), d.decode(syndrome, error_rate=.7)
        np.testing.assert_array_equal(a.candidate, b.candidate)
        assert (a.iterations, a.converged) == (b.iterations, b.converged)
        assert d.verify_ledger(b.ledger_json)


def test_sparse_large_graph_setup_does_not_materialize_dense_matrix(monkeypatch):
    from scipy.sparse import csr_matrix
    monkeypatch.setattr(csr_matrix, "toarray", lambda *a, **k: pytest.fail("dense graph allocation"))
    table = EdgeTable.from_edges(10000, 20000, [(i, i) for i in range(10000)])
    decoder = BinaryPolicyDecoder(table)
    assert decoder.row_ptr.nbytes + decoder.variables.nbytes < 200_000
    with pytest.raises(ValueError):
        decoder.variables.setflags(write=True)


def test_shortening_retains_each_surviving_channel_prior(monkeypatch):
    from bp_registry.canonical.intervention_session import BpSession
    from bp_registry.canonical.impulse import ImpulseController
    from bp_registry.canonical.problems import OriginalProblem
    from bp_registry.canonical.budgets import BudgetTree
    seen = []
    original_init = BpSession.__init__

    def observe(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        seen.append(self.state.prior.copy())

    monkeypatch.setattr(BpSession, "__init__", observe)
    h = np.ones((2, 3), dtype=np.uint8)
    original = OriginalProblem("original-prior-test", np.zeros((0, 3), dtype=np.uint8), h, np.array([0, 1], dtype=np.uint8))
    run = ImpulseController(CONTROLLERS["impulse"]).run(original, error_rate=.1,
        prior_llrs=np.array([2., -3., 4.]), budgets=BudgetTree(limits=(), parents={}))
    np.testing.assert_array_equal(seen[0], [2., -3., 4.])
    assert [a.target_index for a in run.attempts] == [0, 1]
    np.testing.assert_array_equal(seen[1], [-3., 4.])
    np.testing.assert_array_equal(seen[2], [2., 4.])


def test_capability_inventory_tracks_executable_closed_policy_names():
    from typing import get_args
    from bp_registry.policy_capabilities import capability_inventory
    inventory = capability_inventory()
    shared = inventory["shared_binary_and_circuit"]
    for key, field in (("updates", "rule"), ("schedules", "schedule"), ("controllers", "controller")):
        assert shared[key] == list(get_args(BinaryPolicy.model_fields[field].annotation))
    shared["controllers"].clear()
    assert capability_inventory()["shared_binary_and_circuit"]["controllers"]
    assert inventory["scope"] == "existing_or_source_defined_counterparts_only"


def test_closed_nested_controls_and_empty_local_operands():
    from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy
    p = BinaryPolicy(flooding_policy=BpFloodingPolicy(check_rule="sum_product", resolution=ResolutionPolicy(),
        version="bp-flooding-policy-v3", check_stabilization="log_domain", product_epsilon=1e-10))
    data = p.model_dump(mode="json")
    data["flooding_policy"]["resolution"]["unused"] = 1
    with pytest.raises(ValueError, match="unknown"):
        BinaryPolicy.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError):
        BinaryPolicy(controller="mbbp", options=CONTROLLERS["mbbp"], vote_tie_bit=False)
    with pytest.raises(ValueError, match="nonempty"):
        BinaryPolicyDecoder(np.zeros((0, 2), dtype=np.uint8), BinaryPolicy(schedule="check_node_serial"))


@pytest.mark.parametrize("schedule", ["flooding", "check_node_serial"])
def test_disordered_affine_memory_replays_with_heterogeneous_priors(schedule):
    spec = memory("affine_prior", local=schedule != "flooding").model_dump(mode="json")
    spec["bindings"][0]["assignment"] = dict(mode="uniform", low=.2, high=.8, root_seed_identity="b" * 64)
    p = BinaryPolicy(schedule=schedule, max_iterations=3, memory=MemoryCompositionSpec.model_validate(spec))
    d = BinaryPolicyDecoder(np.ones((2, 2), dtype=np.uint8), p)
    result = d.decode([0, 1], prior_llrs=[2., -1.])
    assert result.iterations == (3 if schedule == "flooding" else 6)
    assert d.verify_ledger(result.ledger_json)


def test_disordered_relay_uses_existing_source_tuning_with_vector_priors():
    options = dict(CONTROLLERS["relay"], memory_tuning=dict(
        semantics="relay_v022_dynamic_affine_prior_css_adaptation", first_leg_gamma=.1,
        later_leg_center=.2, later_leg_width=.9, seed_identity="source-relay"))
    d = BinaryPolicyDecoder(np.ones((2, 2), dtype=np.uint8), BinaryPolicy(controller="relay", options=options))
    result = d.decode([0, 1], prior_llrs=[2., -1.])
    assert result.iterations == 4
    assert d.verify_ledger(result.ledger_json)


def test_ordinary_work_totals_equal_unique_committed_leaves():
    d = BinaryPolicyDecoder(np.ones((2, 2), dtype=np.uint8), BinaryPolicy(backend="scalar", max_iterations=3))
    result = d.decode([0, 1], prior_llrs=[2., -1.])
    execution = result.ledger["execution"]
    leaves = execution["leaves"]
    assert len({leaf[0] for leaf in leaves}) == len(leaves)
    assert {k: sum(leaf[2][k] for leaf in leaves) for k in execution["work"]} == execution["work"]
    assert execution["work"]["check_to_variable_updates"] == 12
    assert execution["work"]["bp_calls"] == 1
    assert result.ledger["output_validation_work"]["original_checks"] == 1


def test_source_controls_cannot_be_silently_inactive_or_ambiguously_ordered():
    with pytest.raises(ValueError, match="Relay-only"):
        BinaryPolicy(controller="beam", options=dict(relay_seed="unused"))
    options = json.loads(json.dumps(CONTROLLERS["relay"]))
    options["memory_bindings"][0]["order"] = 1
    with pytest.raises(ValueError, match="contiguous"):
        BinaryPolicy(controller="relay", options=options)


def chunking_fixture():
    h = np.array([[1,1,0,0,0,0,0,0], [0,1,0,0,0,1,1,0],
                  [1,0,0,1,0,0,1,0], [0,0,1,1,1,0,0,1]], dtype=np.uint8)
    rates = [.1686279273722417, .2151861424206105, .23636213203981687, .13467950863149117,
             .1601663007877624, .2939527271376381, .2398796318588651, .23689172971836636]
    dem = stim.DetectorErrorModel("\n".join(f"error({p}) " +
        " ".join(f"D{c}" for c in np.flatnonzero(h[:, v])) + f" L{v}" for v, p in enumerate(rates)))
    return dem, np.tile(np.array([0, 1, 1, 1], dtype=np.uint8), (8, 1))


@pytest.mark.parametrize("scope", ["attempt", "sweep"])
def test_sinter_randomized_counterexample_is_independent_of_batch_partition(scope):
    dem, events = chunking_fixture()
    decoder = SharedPolicySinterDecoder(BinaryPolicy(schedule="variable_node_serial", randomized=scope,
        rule="min_sum", max_iterations=5)).compile_decoder_for_dem(dem=dem)
    packed = np.packbits(events, axis=1, bitorder="little")
    together = decoder.decode_shots_bit_packed(bit_packed_detection_event_data=packed)
    separated = np.vstack([decoder.decode_shots_bit_packed(bit_packed_detection_event_data=row[None]) for row in packed])
    np.testing.assert_array_equal(together, separated)
    assert decoder.decode_detailed(events).converged.all()


def identity_policies():
    h = np.array([[1, 1, 1, 0], [0, 1, 0, 1]], dtype=np.uint8)
    table = EdgeTable.from_check_matrix(h)
    from bp_registry.canonical.updates import ParameterGeneratorSpec, ParameterRefreshPlan
    for schedule in ("layered", "check_node_serial", "variable_node_serial"):
        for scope in ("configuration", "attempt", "sweep"):
            yield BinaryPolicy(schedule=schedule, randomized=scope, max_iterations=3,
                               partitions=((0,), (1,)) if schedule == "layered" else None)
    yield BinaryPolicy(schedule="group_shuffled", max_iterations=3)
    for scope in ("configuration", "attempt", "source_iteration"):
        yield BinaryPolicy(rule="normalized_min_sum", max_iterations=3,
            parameter_refresh=ParameterRefreshPlan(scope=scope, generator=ParameterGeneratorSpec(
                shape="edge", graph_sha256=table.graph_sha256, distribution="uniform",
                low=.2, high=.9, root_seed_identity="a" * 64)))
    for schedule in ("flooding", "check_node_serial"):
        spec = memory("affine_prior", local=schedule != "flooding").model_dump(mode="json")
        spec["bindings"][0]["assignment"] = dict(mode="uniform", low=.2, high=.8, root_seed_identity="b" * 64)
        yield BinaryPolicy(schedule=schedule, max_iterations=3, memory=MemoryCompositionSpec.model_validate(spec))
    for kind, options in CONTROLLERS.items():
        yield BinaryPolicy(controller=kind, options=options)
    yield BinaryPolicy(controller="relay", options=dict(CONTROLLERS["relay"], memory_tuning=dict(
        semantics="relay_v022_dynamic_affine_prior_css_adaptation", first_leg_gamma=.1,
        later_leg_center=.2, later_leg_width=.9, seed_identity="source-relay")))


@pytest.mark.parametrize("policy", list(identity_policies()))
def test_all_identity_consumers_preserve_execution_across_transport(policy):
    import pickle
    from concurrent.futures import ThreadPoolExecutor

    dem = stim.DetectorErrorModel("error(0.1) D0 L0\nerror(0.7) D0 D1 L1\nerror(0.2) D0\nerror(0.3) D1")
    events = np.array([[0, 0], [0, 1], [1, 0], [1, 1], [0, 1], [1, 0]], dtype=np.uint8)
    factory = SharedPolicySinterDecoder(policy)
    decoder = factory.compile_decoder_for_dem(dem=dem)
    fresh = pickle.loads(pickle.dumps(factory)).compile_decoder_for_dem(dem=dem)
    batch = decoder.decode_detailed(events)
    assert batch.ledger[0]["schema"] == "circuit-shared-policy-ledger-v2"
    assert batch.ledger[0]["random_identity"]["version"] == "observation-v2"
    expected = [row["binary_execution"] for row in batch.ledger[1:]]
    for i, event in enumerate(events):
        single = fresh.decode_detailed(event[None])
        assert single.ledger[1]["binary_execution"] == expected[i]
        np.testing.assert_array_equal(single.predictions[0], batch.predictions[i])
    permutation = [5, 3, 0, 4, 2, 1]
    reordered = fresh.decode_detailed(events[permutation])
    assert [row["binary_execution"] for row in reordered.ledger[1:]] == [expected[i] for i in permutation]
    # Concurrent calls share only immutable graph/configuration, not RNG state.
    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent = list(pool.map(lambda event: decoder.decode_detailed(event[None]), events))
    assert [result.ledger[1]["binary_execution"] for result in concurrent] == expected
    assert expected[1] == expected[4] and expected[2] == expected[5]


@pytest.mark.parametrize("scope", ["attempt", "sweep"])
def test_shared_v1_ledgers_replay_without_changing_historical_bytes(scope, tmp_path):
    from pathlib import Path
    dem, events = chunking_fixture()
    policy = BinaryPolicy(schedule="variable_node_serial", randomized=scope, rule="min_sum", max_iterations=5)
    fixture = Path(__file__).parents[1] / "circuit" / "fixtures" / f"shared-v1-{scope}.jsonl"
    historical = fixture.read_bytes()
    current = SharedPolicySinterDecoder(policy).compile_decoder_for_dem(dem=dem)
    assert current.verify_ledger(fixture)["verified"]
    legacy = SharedPolicySinterDecoder(policy, identity_version="batch-index-v1").compile_decoder_for_dem(dem=dem)
    result = legacy.decode_detailed(events)
    assert result.ledger == [json.loads(line) for line in historical.decode().splitlines()]
    out = tmp_path / "legacy.jsonl"
    result.write_ledger(out)
    assert out.read_bytes() == historical == fixture.read_bytes()


def test_v2_identity_binds_policy_model_and_normalized_observation(tmp_path):
    from hashlib import sha256
    from bp_registry.canonical.policy_decoder import canonical_json
    from bp_registry.batch_records import encode_records, write_records

    policy = BinaryPolicy(schedule="variable_node_serial", randomized="attempt", max_iterations=2)
    dem = stim.DetectorErrorModel("error(0.1) D0 L0\nerror(0.2) D8 L1")
    decoder = SharedPolicySinterDecoder(policy).compile_decoder_for_dem(dem=dem)
    events = np.zeros((2, 9), dtype=np.uint8); events[1, 8] = 1
    batch = decoder.decode_detailed(events)
    meta = batch.ledger[0]["random_identity"]
    context = dict(domain="circuit-observation-v2", model_sha256=decoder.model.execution_sha256,
                   policy=policy.model_dump(mode="json"))
    digest = sha256(canonical_json(context).encode()).digest()
    assert meta["context_sha256"] == digest.hex()
    for i, row in enumerate(batch.ledger[1:]):
        assert row["binary_execution"]["shot_identity"] == "circuit-observation-v2:" + sha256(digest + events[i].tobytes()).hexdigest()
    assert batch.ledger[1]["binary_execution"]["shot_identity"] != batch.ledger[2]["binary_execution"]["shot_identity"]
    changed_policy = BinaryPolicy.model_validate_json(policy.model_copy(update={"seed": "other"}).model_dump_json())
    changed = SharedPolicySinterDecoder(changed_policy).compile_decoder_for_dem(dem=dem).decode_detailed(events)
    assert changed.ledger[0]["random_identity"] != meta
    changed_model = SharedPolicySinterDecoder(policy).compile_decoder_for_dem(
        dem=stim.DetectorErrorModel("error(0.1) D0 L1\nerror(0.2) D8 L0")).decode_detailed(events)
    assert changed_model.ledger[0]["random_identity"] != meta
    packed = np.packbits(events, axis=1, bitorder="little")
    clean = decoder.decode_shots_bit_packed(bit_packed_detection_event_data=packed)
    packed[:, 1] |= 0xfe  # Padding bits are not detector observations.
    np.testing.assert_array_equal(clean, decoder.decode_shots_bit_packed(bit_packed_detection_event_data=packed))
    for mutation in ("version", "context_sha256"):
        records = batch.ledger
        records[0]["random_identity"][mutation] = "incorrect"
        path = tmp_path / f"tampered-{mutation}.jsonl"
        write_records(path, encode_records(records), batch.ledger_schema)
        with pytest.raises(ValueError, match="replay"):
            decoder.verify_ledger(path)
    empty = decoder.decode_detailed(np.empty((0, 9), dtype=np.uint8))
    path = tmp_path / "empty.jsonl"; empty.write_ledger(path)
    assert decoder.verify_ledger(path)["shots"] == 0


@pytest.mark.parametrize("version", ["unknown", None, 2, True])
def test_unknown_shared_identity_versions_rejected_at_construction(version):
    from bp_registry.circuit.shared_policies import SharedCompiledPolicyDecoder
    from bp_registry.circuit import DemBinaryModel
    with pytest.raises(ValueError, match="identity"):
        SharedPolicySinterDecoder(identity_version=version)
    with pytest.raises(ValueError, match="identity"):
        SharedCompiledPolicyDecoder(DemBinaryModel.from_dem(stim.DetectorErrorModel("error(0.1) D0")),
                                    BinaryPolicy(), identity_version=version)


@pytest.mark.parametrize("schema", ["circuit-shared-policy-ledger-v999", "circuit-shared-policy-ledger-v1"])
def test_shared_ledger_rejects_unknown_schema_and_identity_downgrade(schema, tmp_path):
    from bp_registry.batch_records import encode_records, write_records

    decoder = SharedPolicySinterDecoder().compile_decoder_for_dem(
        dem=stim.DetectorErrorModel("error(0.1) D0 L0"))
    records = decoder.decode_detailed(np.array([[1]], dtype=np.uint8)).ledger
    records[0]["schema"] = schema
    records[0].pop("random_identity")
    path = tmp_path / "changed-schema.jsonl"
    write_records(path, encode_records(records), schema)
    with pytest.raises(ValueError, match="schema|replay"):
        decoder.verify_ledger(path)
