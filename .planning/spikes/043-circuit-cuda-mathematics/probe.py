"""Independent factor enumeration, not a transcription of the BP hot loops."""
from pathlib import Path
from itertools import product
from dataclasses import replace
import json
import math
import sys
from hashlib import sha256
import numpy as np
import stim
from scipy.special import expit, softmax

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit_support import Audit
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
H = np.array([[1, 1, 1, 0, 0], [0, 0, 1, 1, 1]], np.uint8)


def reference(prior, syndrome, rule, parameter, limit):
    edges = list(zip(*np.nonzero(H)))
    old = np.array([prior[v] for _, v in edges])
    posterior = prior.copy()
    candidate = (posterior < 0).astype(np.uint8)
    if np.array_equal(H @ candidate % 2, syndrome):
        return candidate, posterior, 0, True
    for iteration in range(1, limit + 1):
        c2v = np.empty(len(edges))
        for e, (check, _) in enumerate(edges):
            incoming = np.array([old[j] for j, (c, _) in enumerate(edges) if c == check and j != e])
            sums, minima = [0., 0.], [math.inf, math.inf]
            for fixed in (0, 1):
                for assignment in product((0, 1), repeat=len(incoming)):
                    if (sum(assignment) + fixed) % 2 != syndrome[check]:
                        continue
                    bits = np.asarray(assignment)
                    sums[fixed] += float(np.prod(np.where(bits, expit(-incoming), expit(incoming))))
                    minima[fixed] = min(minima[fixed], float(np.dot(bits, incoming)))
            if rule == "spa":
                message = math.log(sums[0]) - math.log(sums[1])
            else:
                message = minima[1] - minima[0]
                if rule == "normalized_min_sum":
                    message *= parameter
                if rule == "offset_min_sum":
                    message = math.copysign(max(0., abs(message) - parameter), message)
                message = np.clip(message, -25., 25.)
            c2v[e] = message
        posterior = prior.copy()
        for e, (_, v) in enumerate(edges):
            posterior[v] += c2v[e]
        if rule != "spa":
            posterior = np.clip(posterior, -25., 25.)
        candidate = (posterior < 0).astype(np.uint8)
        fresh = np.array([posterior[v] - c2v[e] for e, (_, v) in enumerate(edges)])
        old = .1 * old + .9 * fresh if rule == "spa" else np.clip(fresh, -25., 25.)
        if np.array_equal(H @ candidate % 2, syndrome):
            return candidate, posterior, iteration, True
    return candidate, posterior, limit, bool(np.array_equal(H @ candidate % 2, syndrome))


def circuit_factors():
    rng = np.random.default_rng(4301)
    rows, worst = [], 0.
    for sample in range(12):
        rates = rng.uniform(.03, .97, 5)
        prior = np.log1p(-rates) - np.log(rates)
        dem = stim.DetectorErrorModel("\n".join(
            f"error({p}) " + " ".join(f"D{c}" for c in np.flatnonzero(H[:, v])) + f" L{v}"
            for v, p in enumerate(rates)))
        for rule, parameter in (("spa", 1.), ("min_sum", 1.), ("normalized_min_sum", .8), ("offset_min_sum", .3)):
            for cap, bits in product((0, 1, 5), product((0, 1), repeat=2)):
                s = np.array(bits, np.uint8)
                expected = reference(prior, s, rule, parameter, cap)
                for backend in ("scalar", "compiled"):
                    decoder = PolicyBpSinterDecoder(CircuitPolicy(rule=rule, parameter=parameter,
                        backend=backend, max_iterations=cap)).compile_decoder_for_dem(dem=dem)
                    actual = decoder.decode_detailed(s[None])
                    posterior = np.asarray(actual.ledger[1]["attempts"][0]["posterior"])
                    error = float(abs(posterior - expected[1]).max())
                    worst = max(worst, error)
                    np.testing.assert_array_equal(actual.faults[0], expected[0])
                    np.testing.assert_allclose(posterior, expected[1], atol=2e-12, rtol=2e-12)
                    assert (actual.iterations[0], actual.converged[0]) == (expected[2], expected[3])
                    rows.append(dict(sample=sample, rates=rates.tolist(), syndrome=s.tolist(),
                        rule=rule, parameter=parameter, cap=cap, backend=backend,
                        candidate=actual.faults[0].tolist(), iterations=int(actual.iterations[0]),
                        converged=bool(actual.converged[0]), posterior_error=error))
    (HERE / "factor-cases.json").write_text(json.dumps(rows, indent=2) + "\n")
    return dict(comparisons=len(rows), seed=4301, max_error=worst, tolerance=2e-12)


def finite_failure():
    outcomes = {}
    for backend in ("scalar", "compiled", "auto"):
        policy = CircuitPolicy(rule="normalized_min_sum", parameter=1e308, backend=backend, max_iterations=1)
        decoder = PolicyBpSinterDecoder(policy).compile_decoder_for_dem(dem=stim.DetectorErrorModel("error(0.1) D0 L0"))
        try:
            result = decoder.decode_detailed(np.array([[1]], np.uint8))
            outcomes[backend] = dict(returned=True, candidate=result.faults.tolist(), converged=result.converged.tolist())
        except Exception as exc:
            outcomes[backend] = dict(returned=False, exception=type(exc).__name__, message=str(exc))
    (HERE / "overflow-counterexample.json").write_text(json.dumps(outcomes, indent=2) + "\n")
    assert all(not item["returned"] for item in outcomes.values()), outcomes
    return outcomes


def carried_math():
    old = json.loads((HERE.parent / "042-batch-evidence-fix/results.json").read_text())
    names = ["quaternary/compiled.py", "quaternary/kernel.py", "quaternary/numerics.py",
             "resolution.py", "check_numerics.py"]
    for name in names:
        relative = f"src/bp_registry/{name}"
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == old["source_hashes"][relative], relative
    return dict(status="reused_unchanged_source", exact_tree_cases=192, covariance_cases=100,
                receipt_sha256=sha256((HERE.parent / "042-batch-evidence-fix/results.json").read_bytes()).hexdigest(),
                modules=names)


def cuda_trees():
    from numba import cuda, config
    from bp_registry.canonical.compiled import CompiledBinaryFlooding
    from bp_registry.quaternary.compiled import CompiledBp4Graph
    from bp_registry.quaternary.problems import PauliCode
    from bp_registry.resolution import STABLE_SPA_F64
    from bp_registry.gpu import CudaFlooding
    assert config.ENABLE_CUDASIM, "This probe is specifically labelled as simulation"
    policy = replace(STABLE_SPA_F64, damping=0., zero_syndrome_shortcut=False)
    rng = np.random.default_rng(4302)
    worst, cases = 0., 0
    for family in ("binary", "pauli"):
        for sample in range(4):
            h = np.zeros((4, 5), np.uint8)
            labels = np.ones(5, np.uint8) if family == "binary" else rng.integers(1, 4, 5, dtype=np.uint8)
            for c in range(4):
                h[c, c:c+2] = labels[c:c+2]
            s = rng.integers(0, 2, 4, dtype=np.uint8)
            if family == "binary":
                p = (.13, .31, .69, .87)[sample]
                graph = CompiledBinaryFlooding.from_check_matrix(h, policy=policy)
                gpu = CudaFlooding.from_binary(graph, error_rate=p, allow_simulator=True)
                probabilities = np.tile([1-p, p], (5, 1))
            else:
                probabilities = rng.dirichlet(np.ones(4), 5)
                graph = CompiledBp4Graph.from_code(PauliCode(h), probabilities, policy=policy)
                gpu = CudaFlooding.from_pauli(graph, allow_simulator=True)
            assignments = np.array(list(product(range(probabilities.shape[1]), repeat=5)), np.uint8)
            if family == "binary":
                syn = assignments @ h.T % 2
            else:
                syn = np.sum((h[None] != 0) & (assignments[:, None] != 0) & (assignments[:, None] != h[None]), axis=2) % 2
            weights = np.prod(probabilities[np.arange(5)[None], assignments], axis=1) * np.all(syn == s, axis=1)
            weights /= weights.sum()
            expected = np.array([[weights[assignments[:, v] == a].sum() for a in range(probabilities.shape[1])] for v in range(5)])
            n, states = gpu._prior.shape
            edges = len(graph.variables)
            old = cuda.device_array((1, edges, states), np.float64)
            comm, prefix, c2v = (cuda.device_array((1, edges), np.float64) for _ in range(3))
            beliefs = cuda.device_array((1, n, states), np.float64)
            candidate = cuda.device_array((1, n), np.uint8)
            it = cuda.device_array(1, np.int64)
            ok, failed = (cuda.device_array(1, np.uint8) for _ in range(2))
            gpu._kernel[1, 128](*gpu._device, cuda.to_device(s[None]), 4, False,
                *policy.coefficients, policy.product_epsilon, policy.decision_code, False, False,
                old, comm, prefix, c2v, beliefs, candidate, it, ok, failed)
            assert not failed.copy_to_host().any()
            actual = softmax(np.concatenate((np.zeros((n, 1)), -beliefs.copy_to_host()[0]), axis=1), axis=1)
            error = float(abs(actual - expected).max())
            worst = max(worst, error)
            np.testing.assert_allclose(actual, expected, atol=2e-12, rtol=2e-12)
            cases += 1
    return dict(cases=cases, seed=4302, max_error=worst, tolerance=2e-12,
                backend="cuda-simulator", scope="new independent tree oracle; existing H200 tests retained separately")


if __name__ == "__main__":
    a = Audit(HERE)
    for name, function in (("independent_circuit_factor_updates", circuit_factors),
            ("carried_unchanged_Pauli_mathematics", carried_math),
            ("independent_CUDA_tree_marginals", cuda_trees),
            ("finite_intermediate_failure_parity", finite_failure)):
        a.probe(name, function)
    a.finish()
