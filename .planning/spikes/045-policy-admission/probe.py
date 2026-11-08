from pathlib import Path
from itertools import product
import json
import sys
import numpy as np
import stim

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit_support import Audit
from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder

HERE = Path(__file__).resolve().parent
RULES = [("spa", 1.), ("min_sum", 1.), ("normalized_min_sum", .8), ("offset_min_sum", .3)]
MEMORIES = [("affine_prior", {"alpha": .6}), ("pdbp_field_mix", {"gamma": .4}),
            ("pdprime_delta_mix", {"gamma": .2}),
            ("posterior_momentum", {"alpha": .8, "gamma": .2}), ("v2c_damping", {"gamma": .3})]
DEMS = [stim.DetectorErrorModel("error(0.1) D0 L0\nerror(0.2) D0 D1\nerror(0.7) D1 L1\nerror(1) D0 L1\nerror(0.3) L0"),
        stim.DetectorErrorModel("error(0.1) D0 D1\nerror(0.2) D0 D1 L0")]
EVENTS = np.array(list(product((0, 1), repeat=2)), np.uint8)


def memory(items):
    return MemoryCompositionSpec.model_validate({"bindings": [dict(
        binding_id=f"audit-{i}", kind=kind,
        target={"affine_prior": "prior", "v2c_damping": "v2c", "pdbp_field_mix": "belief",
                "pdprime_delta_mix": "belief", "posterior_momentum": "posterior"}[kind],
        parameters=parameters, order=i, history_owner=f"audit-history-{i}",
        state_lifetime="attempt", advance_boundary="source_iteration",
        refresh_boundary="attempt_start", source_status="canonical_adaptation")
        for i, (kind, parameters) in enumerate(items)]})


def compare(a, b):
    for name in ("faults", "predictions", "converged", "iterations"):
        np.testing.assert_array_equal(getattr(a, name), getattr(b, name))
    for left, right in zip(a.ledger[1:], b.ledger[1:]):
        assert len(left["attempts"]) == len(right["attempts"])
        for x, y in zip(left["attempts"], right["attempts"]):
            np.testing.assert_allclose(x["posterior"], y["posterior"], atol=2e-12, rtol=2e-12)


def policy_matrix():
    choices = [None] + [memory([item]) for item in MEMORIES] + [memory([MEMORIES[i] for i in (0, 1, 3, 4)])]
    rows, saved, accepted, rejected, shots, branching = [], {}, 0, 0, 0, 0
    for (rule, parameter), controller, (mi, mem), backend in product(
            RULES, ("single", "relay", "guided", "beam"), enumerate(choices), ("scalar", "auto", "compiled")):
        config = dict(rule=rule, parameter=parameter, controller=controller, memory=mem, backend=backend,
                      max_iterations=3, max_attempts=1 if controller == "single" else 5,
                      beam_width=2 if controller == "beam" else 1)
        supported = not ((controller == "relay" and mem is not None) or
                         (backend == "compiled" and (mem is not None or controller == "relay")))
        try:
            policy = CircuitPolicy(**config)
        except ValueError as exc:
            assert not supported, str(exc)
            rejected += 1
            rows.append(dict(rule=rule, controller=controller, memory_index=mi, backend=backend, accepted=False))
            continue
        assert supported
        accepted += 1
        for di, dem in enumerate(DEMS):
            decoder = PolicyBpSinterDecoder(policy).compile_decoder_for_dem(dem=dem)
            result = decoder.decode_detailed(EVENTS)
            repeated = decoder.decode_detailed(EVENTS)
            assert repeated.ledger_json == result.ledger_json
            for i, row in enumerate(result.ledger[1:]):
                candidate = result.faults[i]
                residual = np.zeros(2, np.uint8)
                for c, v in decoder.model.table.edges:
                    residual[c] ^= candidate[v]
                assert bool(result.converged[i]) == bool(np.array_equal(residual ^ decoder.model.syndrome_bias, EVENTS[i]))
                expected = (decoder.model.observable_matrix @ candidate) % 2 ^ decoder.model.observable_bias
                np.testing.assert_array_equal(result.predictions[i], expected)
                attempts = row["attempts"]
                assert 1 <= len(attempts) <= policy.max_attempts
                assert int(result.iterations[i]) == sum(a["iterations"] for a in attempts)
                branching += len(attempts) > 1
                for j, attempt in enumerate(attempts):
                    assert attempt["attempt"] == j
                    assert attempt["parent"] is None or attempt["parent"] < j
                    assert 0 <= attempt["iterations"] <= policy.max_iterations
                    if controller != "relay":
                        assert attempt["work"] == dict(c2v=attempt["iterations"] * decoder.model.table.edge_count,
                            v2c=attempt["iterations"] * decoder.model.table.edge_count, candidate_checks=attempt["iterations"] + 1)
                        if mem is not None:
                            assert attempt["memory"]["committed_iterations"] == attempt["iterations"]
                # Same shot in a standalone call must start with clean histories.
                one = decoder.decode_detailed(EVENTS[i:i+1])
                np.testing.assert_array_equal(result.faults[i], one.faults[0])
                if controller != "relay":
                    assert attempts == one.ledger[1]["attempts"]
            key = (rule, controller, mi, di)
            if key in saved:
                compare(saved[key], result)
            else:
                saved[key] = result
            shots += len(EVENTS)
        rows.append(dict(rule=rule, controller=controller, memory_index=mi, backend=backend, accepted=True,
                         execution_backend=result.ledger[0]["execution_backend"]))
    (HERE / "matrix.json").write_text(json.dumps(rows, indent=2) + "\n")
    return dict(configurations=len(rows), accepted=accepted, rejected=rejected, primary_shots=shots,
                branching_shots=branching, repeated_calls_and_single_shots_checked=True)


def identity_and_isolation():
    # V2C gamma is the FRESH weight; other gamma fields have different operands.
    identities = [(kind, {k: 1. if kind == "v2c_damping" or (kind == "posterior_momentum" and k == "alpha") else 0. for k in params})
                  for kind, params in MEMORIES]
    cases = 0
    for rule, parameter in RULES:
        base_policy = CircuitPolicy(rule=rule, parameter=parameter, max_iterations=4, backend="scalar")
        base = PolicyBpSinterDecoder(base_policy).compile_decoder_for_dem(dem=DEMS[0]).decode_detailed(EVENTS)
        for items in [[item] for item in identities] + [[identities[i] for i in (0, 1, 3, 4)]]:
            policy = CircuitPolicy(**base_policy.model_dump(exclude={"memory"}), memory=memory(items))
            factory = PolicyBpSinterDecoder(policy)
            decoder = factory.compile_decoder_for_dem(dem=DEMS[0])
            compare(base, decoder.decode_detailed(EVENTS))
            before = decoder.decode_detailed(EVENTS).ledger_json
            policy.memory.bindings[0].parameters.update({next(iter(policy.memory.bindings[0].parameters)): .7})
            assert factory.compile_decoder_for_dem(dem=DEMS[0]).decode_detailed(EVENTS).ledger_json == before
            exposed = decoder.policy
            exposed.memory.bindings[0].parameters.update({next(iter(exposed.memory.bindings[0].parameters)): .6})
            assert decoder.decode_detailed(EVENTS).ledger_json == before
            cases += 1
    return dict(identity_cases=cases, caller_and_accessor_nested_state_isolated=True)


def ineffective_controls():
    rows = []
    # Static use: solution_limit/relay_alpha are read only inside the Relay branch;
    # bias is read only when expanding guided/beam children. All these cases are
    # currently admitted despite a non-default control with no matching operand.
    examples = [(c, key, value) for c in ("single", "guided", "beam")
                for key, value in (("solution_limit", 2), ("relay_alpha", .25))]
    examples += [(c, "bias", 2.) for c in ("single", "relay")]
    for controller, key, value in examples:
        config = dict(controller=controller, max_attempts=1 if controller == "single" else 5, max_iterations=3)
        base = CircuitPolicy(**config)
        try:
            changed = CircuitPolicy(**config, **{key: value})
        except ValueError:
            continue
        a = PolicyBpSinterDecoder(base).compile_decoder_for_dem(dem=DEMS[1]).decode_detailed(EVENTS)
        b = PolicyBpSinterDecoder(changed).compile_decoder_for_dem(dem=DEMS[1]).decode_detailed(EVENTS)
        assert a.ledger[1:] == b.ledger[1:]
        assert a.ledger[0]["policy"] != b.ledger[0]["policy"]
        rows.append(dict(controller=controller, ignored_control=key, nondefault_value=value,
                         identical_shot_and_attempt_evidence=True))
    (HERE / "ineffective-controls.json").write_text(json.dumps(rows, indent=2) + "\n")
    assert not rows, f"{len(rows)} non-default controller controls admitted without an execution operand"


if __name__ == "__main__":
    audit = Audit(HERE)
    audit.probe("new_circuit_policy_matrix", policy_matrix)
    audit.probe("identity_memory_and_nested_ownership", identity_and_isolation)
    audit.probe("controller_specific_nondefault_controls", ineffective_controls)
    audit.finish()
