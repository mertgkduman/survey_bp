"""Run on CUDA hardware or explicitly with NUMBA_ENABLE_CUDASIM=1."""
from dataclasses import replace
import json
import numpy as np
import pytest
from numba import cuda, config

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
from bp_registry.resolution import STABLE_SPA_F64, BpFloodingPolicy, ResolutionPolicy
from bp_registry.gpu import CudaFlooding


MS = BpFloodingPolicy(check_rule="min_sum", resolution=ResolutionPolicy("float64"),
                     version="bp-flooding-policy-v2", check_stabilization="exact_unity",
                     product_epsilon=1e-10, hard_decision="map_pauli")
POLICIES = [STABLE_SPA_F64, MS, replace(MS, alpha=.7, damping=.2), replace(MS, beta=.3, damping=.1)]
available = pytest.mark.skipif(not cuda.is_available(), reason="requires CUDA hardware or explicit CUDA simulator")


def binary(policy):
    return CompiledBinaryFlooding.from_check_matrix(np.array([[1, 1, 0], [0, 1, 1], [1, 0, 0]], np.uint8),
                                                    rule="spa" if policy.check_rule == "sum_product" else "min_sum",
                                                    policy=policy)


def pauli(policy):
    code = PauliCode(np.array([[1, 1, 0], [3, 3, 0], [0, 0, 2]], np.uint8))
    probabilities = np.array([[.6, .1, .2, .1], [.1, .2, .3, .4], [.25, .25, .25, .25]])
    return CompiledBp4Graph.from_code(code, probabilities, policy=policy)


@available
@pytest.mark.parametrize("family", ["binary", "pauli"])
@pytest.mark.parametrize("policy", POLICIES)
def test_cpu_gpu_candidate_stopping_and_ledger_parity(family, policy, tmp_path):
    graph = binary(policy) if family == "binary" else pauli(policy)
    gpu = (CudaFlooding.from_binary(graph, error_rate=.7, allow_simulator=True) if family == "binary"
           else CudaFlooding.from_pauli(graph, allow_simulator=True))
    syndromes = np.array([[0, 0, 0], [1, 0, 1], [0, 1, 1]], np.uint8)
    result = gpu.run_batch(syndromes, max_iterations=3)
    for s, candidate, iterations, valid in zip(syndromes, result.candidates, result.iterations, result.converged):
        cpu = graph.run(s, max_iterations=3, **({"error_rate": .7} if family == "binary" else {}))
        np.testing.assert_array_equal(candidate, cpu.candidate)
        assert (iterations, valid) == (cpu.iterations, cpu.converged)
    path = tmp_path / "gpu.jsonl"
    result.write_ledger(path)
    assert gpu.verify_ledger(path)["verified"]
    rows = result.ledger
    rows[1]["work"]["c2v"] += 1
    path.write_text("\n".join(json.dumps(row) for row in rows))
    with pytest.raises(ValueError, match="replay"):
        gpu.verify_ledger(path)
    with pytest.raises(ValueError):
        result.candidates.setflags(write=True)
    with pytest.raises(ValueError, match="bound evidence"):
        replace(result, candidates=result.candidates ^ 1)


@available
@pytest.mark.parametrize("family", ["binary", "pauli"])
def test_zero_steps_empty_batch_fixed_stopping_and_chunking(family):
    graph = binary(STABLE_SPA_F64) if family == "binary" else pauli(STABLE_SPA_F64)
    gpu = (CudaFlooding.from_binary(graph, error_rate=.7, allow_simulator=True) if family == "binary"
           else CudaFlooding.from_pauli(graph, allow_simulator=True))
    s = np.array([[0, 0, 0], [1, 0, 1]], np.uint8)
    result = gpu.run_batch(s, max_iterations=0, workspace_bytes=500)
    for i in range(2):
        cpu = graph.run(s[i], max_iterations=0, **({"error_rate": .7} if family == "binary" else {}))
        np.testing.assert_array_equal(result.candidates[i], cpu.candidate)
        assert result.converged[i] == cpu.converged
    assert gpu.run_batch(s[:0], max_iterations=0).candidates.shape == (0, 3)
    if family == "pauli":
        fixed = gpu.run_batch(s[:1], max_iterations=2, stop_on_convergence=False)
        cpu = graph.run(s[0], max_iterations=2, stop_on_convergence=False)
        assert fixed.iterations[0] == 2
        np.testing.assert_array_equal(fixed.candidates[0], cpu.candidate)
    with pytest.raises(ValueError, match="workspace"):
        gpu.run_batch(s, max_iterations=1, workspace_bytes=1)
    chunked = gpu.run_batch(s, max_iterations=2, workspace_bytes=500)
    whole = gpu.run_batch(s, max_iterations=2)
    np.testing.assert_array_equal(chunked.candidates, whole.candidates)
    np.testing.assert_array_equal(chunked.iterations, whole.iterations)


@available
def test_empty_binary_graph():
    graph = CompiledBinaryFlooding.from_check_matrix(np.zeros((1, 0), np.uint8), policy=STABLE_SPA_F64)
    gpu = CudaFlooding.from_binary(graph, error_rate=.1, allow_simulator=True)
    result = gpu.run_batch(np.array([[0], [1]], np.uint8), max_iterations=2)
    assert result.candidates.shape == (2, 0)
    np.testing.assert_array_equal(result.converged, [True, False])
    np.testing.assert_array_equal(result.iterations, [0, 2])


def test_unsupported_policy_and_unavailable_device_are_explicit():
    graph = CompiledBinaryFlooding.from_check_matrix(np.array([[1]], np.uint8))
    with pytest.raises(ValueError, match="explicit float64"):
        CudaFlooding.from_binary(graph, error_rate=.1, allow_simulator=True)
    if not cuda.is_available():
        with pytest.raises(RuntimeError, match="unavailable"):
            CudaFlooding.from_binary(binary(STABLE_SPA_F64), error_rate=.1)
    elif config.ENABLE_CUDASIM:
        with pytest.raises(RuntimeError, match="simulator"):
            CudaFlooding.from_binary(binary(STABLE_SPA_F64), error_rate=.1)


@available
def test_numerical_failure_rejects_entire_batch():
    graph = binary(replace(MS, alpha=1e308, zero_syndrome_shortcut=False))
    gpu = CudaFlooding.from_binary(graph, error_rate=.1, allow_simulator=True)
    with pytest.raises(FloatingPointError, match="entire batch"):
        gpu.run_batch(np.array([[1, 0, 1], [0, 1, 0]], np.uint8), max_iterations=2)


@available
@pytest.mark.parametrize("decision", ["min_llr", "strict_pauli"])
def test_pauli_tie_rules_without_initial_shortcut(decision):
    graph = pauli(replace(MS, hard_decision=decision, zero_syndrome_shortcut=False))
    gpu = CudaFlooding.from_pauli(graph, allow_simulator=True)
    syndromes = np.array([[0, 0, 0], [1, 0, 1]], np.uint8)
    for limit in (0, 2):
        actual = gpu.run_batch(syndromes, max_iterations=limit)
        for i, s in enumerate(syndromes):
            expected = graph.run(s, max_iterations=limit)
            np.testing.assert_array_equal(actual.candidates[i], expected.candidate)
            assert (actual.iterations[i], actual.converged[i]) == (expected.iterations, expected.converged)


@available
def test_input_snapshot_survives_caller_mutation_at_launch():
    gpu = CudaFlooding.from_binary(binary(STABLE_SPA_F64), error_rate=.1, allow_simulator=True)
    syndromes = np.array([[1, 0, 1]], np.uint8)
    original_input = syndromes.copy()
    original_kernel = gpu._kernel
    class MutatingLaunch:
        def __getitem__(self, shape):
            def launch(*args):
                syndromes[:] = 0
                original_kernel[shape](*args)
            return launch
    gpu._kernel = MutatingLaunch()
    actual = gpu.run_batch(syndromes, max_iterations=2)
    np.testing.assert_array_equal(actual.syndromes, original_input)
    expected = gpu._graph.run(original_input[0], error_rate=.1, max_iterations=2)
    np.testing.assert_array_equal(actual.candidates[0], expected.candidate)


@available
@pytest.mark.parametrize("family", ["binary", "pauli"])
@pytest.mark.parametrize("policy", [STABLE_SPA_F64, replace(MS, alpha=.7, beta=.2, damping=.3)])
def test_first_sweep_numeric_buffers_match_cpu(family, policy):
    graph = binary(policy) if family == "binary" else pauli(policy)
    gpu = (CudaFlooding.from_binary(graph, error_rate=.23, allow_simulator=True) if family == "binary"
           else CudaFlooding.from_pauli(graph, allow_simulator=True))
    n, states = gpu._prior.shape
    edges = len(graph.variables)
    syndrome = np.array([1, 0, 1], np.uint8)
    old = cuda.device_array((1, edges, states), np.float64)
    comm, prefix, c2v = (cuda.device_array((1, edges), np.float64) for _ in range(3))
    beliefs = cuda.device_array((1, n, states), np.float64)
    candidate = cuda.device_array((1, n), np.uint8)
    iterations = cuda.device_array(1, np.int64)
    valid, failures = (cuda.device_array(1, np.uint8) for _ in range(2))
    gpu._kernel[1, 128](*gpu._device, cuda.to_device(syndrome[None]), 1, policy.check_rule == "min_sum",
                       *policy.coefficients, policy.product_epsilon, policy.decision_code, False, False,
                       old, comm, prefix, c2v, beliefs, candidate, iterations, valid, failures)
    if family == "binary":
        expected = graph.sweep(gpu._prior[graph.variables, 0], syndrome, error_rate=.23)
        np.testing.assert_allclose(beliefs.copy_to_host()[0, :, 0], expected.beliefs, atol=2e-13, rtol=2e-13)
        np.testing.assert_allclose(old.copy_to_host()[0, :, 0], expected.new_v2c, atol=2e-13, rtol=2e-13)
    else:
        expected = graph.sweep(graph.initial_v2c(), syndrome)
        np.testing.assert_allclose(beliefs.copy_to_host()[0], expected.beliefs, atol=2e-13, rtol=2e-13)
        np.testing.assert_allclose(old.copy_to_host()[0], expected.v2c, atol=2e-13, rtol=2e-13)
    np.testing.assert_allclose(c2v.copy_to_host()[0], expected.check_to_variable if family == "binary" else expected.c2v, atol=2e-13, rtol=2e-13)
    assert not failures.copy_to_host().any()
