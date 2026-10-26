"""Independent four-log-weight oracle for the exploratory reference diagnostic."""

from __future__ import annotations

import math

import numpy as np

from bp_registry.code_constructions import build_b1_ghp
from bp_registry.quaternary.numerics import pauli_hard_decision

from diagnose_bp4_reference_gap import _decode_reference_float, _reference_candidate
from run_reproduction import bp4_graph_from_css, css_syndrome, double_gross, sample_error


# Project I/X/Y/Z labels to the supplied reference's I/X/Z/Y labels, and back.
TRANSLATE = np.asarray((0, 1, 3, 2), dtype=np.uint8)


def _oracle(graph, syndrome: np.ndarray, p: float, limit: int) -> tuple[np.ndarray, int]:
    n, edge_count = graph.prior_llrs.shape[0], graph.labels.size
    labels = TRANSLATE[graph.labels]
    prior = np.log(np.asarray((1 - p, p / 3, p / 3, p / 3), dtype=np.float64))
    v2c = np.repeat(prior[np.newaxis, :], edge_count, axis=0)
    for iteration in range(1, limit + 1):
        projected = np.empty(edge_count, dtype=np.float64)
        for edge, label in enumerate(labels):
            commute = [float(v2c[edge, state]) for state in range(4)
                       if state == 0 or state == label]
            anti = [float(v2c[edge, state]) for state in range(4)
                    if state != 0 and state != label]
            projected[edge] = float(np.logaddexp(commute[0], commute[1]) -
                                    np.logaddexp(anti[0], anti[1]))
        c2v = np.empty(edge_count, dtype=np.float64)
        for check in range(len(graph.row_ptr) - 1):
            start, stop = graph.row_ptr[check:check + 2]
            for edge in range(start, stop):
                product = -1.0 if syndrome[check] else 1.0
                for other in range(start, stop):
                    if other != edge:
                        value = projected[other]
                        product *= 1.0 if value > 40 else -1.0 if value < -40 else math.tanh(value / 2)
                product = max(-1 + 1e-10, min(1 - 1e-10, product))
                c2v[edge] = math.log1p(product) - math.log1p(-product)
        posterior = np.repeat(prior[np.newaxis, :], n, axis=0)
        for edge, label in enumerate(labels):
            variable = graph.variables[edge]
            for state in range(4):
                if state == 0 or state == label:
                    posterior[variable, state] += c2v[edge]
        candidate = np.empty(n, dtype=np.uint8)
        for variable, weights in enumerate(posterior):
            if weights[0] > max(weights[1:]):
                candidate[variable] = 0
            elif weights[1] > weights[2] and weights[1] > weights[3]:
                candidate[variable] = 1
            elif weights[2] > weights[1] and weights[2] > weights[3]:
                candidate[variable] = 2
            else:
                candidate[variable] = 3
        project_candidate = TRANSLATE[candidate]
        parity = np.zeros(len(graph.row_ptr) - 1, dtype=np.uint8)
        for check in range(len(parity)):
            for edge in range(graph.row_ptr[check], graph.row_ptr[check + 1]):
                label = labels[edge]
                state = candidate[graph.variables[edge]]
                parity[check] ^= int(state != 0 and state != label)
        if np.array_equal(parity, syndrome):
            return project_candidate, iteration
        for edge, label in enumerate(labels):
            variable = graph.variables[edge]
            v2c[edge] = posterior[variable]
            for state in range(4):
                if state == 0 or state == label:
                    v2c[edge, state] -= c2v[edge]
    return project_candidate, limit


def main() -> None:
    example = np.asarray([math.log(.1 / .4), math.log(.1 / .1), math.log(.1 / .4)])
    alternate = np.empty(1, dtype=np.uint8)
    _reference_candidate(example[None, :], alternate)
    assert int(pauli_hard_decision(example)) == 1  # Local X.
    assert int(alternate[0]) == 2  # Reference Y in project labels.
    for name, code, p, seed, shots in (
        ("B1", build_b1_ghp(), 0.10, 20261101, 1),
        ("double-Gross", double_gross(), 0.08, 20261031, 3),
    ):
        graph = bp4_graph_from_css(code, p)
        generator = np.random.Generator(np.random.PCG64(seed))
        for shot in range(shots):
            syndrome = css_syndrome(code, sample_error(generator, code.n, p))
            oracle_candidate, oracle_iteration = _oracle(graph, syndrome, p, 1000)
            compiled_candidate, compiled_iteration, _, _ = _decode_reference_float(
                graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                graph.variables, graph.labels, graph.prior_llrs, syndrome, 1000, 0)
            assert np.array_equal(oracle_candidate, compiled_candidate), (name, shot)
            if name == "double-Gross":
                assert oracle_iteration == compiled_iteration, (name, shot)
            else:
                # The four-weight and three-LLR paths have different arithmetic
                # order; pin the observed one-iteration difference separately.
                assert (oracle_iteration, compiled_iteration) == (27, 26)
                print("B1 shot 0: same correction; four-weight oracle stops at 27, LLR diagnostic at 26.")
    print("Four-log-weight oracle matches the diagnostic corrections on four shots.")


if __name__ == "__main__":
    main()
