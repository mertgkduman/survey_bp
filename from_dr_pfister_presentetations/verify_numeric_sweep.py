"""Algebraic checks for the experimental BP4 and binary numeric kernels."""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding, _decode as legacy_binary_decode
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
from bp_registry.quaternary.numerics import QBP4_F64_V2

from diagnose_bp4_reference_gap import _decode_reference_float
from numeric_sweep_kernel import _boxplus, _check_message, decode_bp4_numeric, decode_binary_numeric
from run_reproduction import bp4_graph_from_css, css_syndrome, double_gross, sample_error


def main() -> None:
    for left, right in ((-3.0, 2.0), (0.0, 4.0), (5.0, 7.0), (-8.0, -4.0)):
        expected = 2 * math.atanh(math.tanh(left / 2) * math.tanh(right / 2))
        assert math.isclose(_boxplus(left, right), expected, abs_tol=1e-12, rel_tol=0)
    assert _boxplus(100., 100.) > 90.0
    incoming = np.asarray((2., -3., 4.))
    for syndrome in (0, 1):
        product = (-1 if syndrome else 1) * math.tanh(incoming[1] / 2) * math.tanh(incoming[2] / 2)
        expected = 2 * math.atanh(product)
        assert math.isclose(_check_message(incoming, 0, 3, 0, syndrome, 0, math.inf, 1e-10),
                            expected, abs_tol=1e-12, rel_tol=0)
        assert math.isclose(_check_message(incoming, 0, 3, 0, syndrome, 1, math.inf, 1e-10),
                            expected, abs_tol=1e-12, rel_tol=0)
    degree_one = np.asarray((0.,))
    assert math.isclose(_check_message(degree_one, 0, 1, 0, 0, 1, math.inf, 1e-10),
                        23.718998027710036, abs_tol=1e-12)

    code = double_gross()
    graph = bp4_graph_from_css(code, .08)
    production_bp4 = replace(graph, profile=QBP4_F64_V2)
    rng = np.random.Generator(np.random.PCG64(20261031))
    for shot in range(20):
        truth = sample_error(rng, code.n, .08)
        syndrome = css_syndrome(code, truth)
        candidate, iterations, _ = decode_bp4_numeric(
            graph.row_ptr, graph.variable_ptr, graph.variable_edges, graph.variables,
            graph.labels, graph.prior_llrs, syndrome, 1000, 0, math.inf, 1e-10, 0.)
        old, old_iterations, _, _ = _decode_reference_float(
            graph.row_ptr, graph.variable_ptr, graph.variable_edges, graph.variables,
            graph.labels, graph.prior_llrs, syndrome, 1000, 0)
        assert iterations == old_iterations and np.array_equal(candidate, old), shot
        new, new_iterations, new_converged = decode_bp4_numeric(
            graph.row_ptr, graph.variable_ptr, graph.variable_edges, graph.variables,
            graph.labels, graph.prior_llrs, syndrome, 1000, 0, math.inf, 1e-10, .1)
        production = production_bp4.run(syndrome, max_iterations=1000)
        assert (production.iterations, production.converged) == (new_iterations, new_converged)
        assert np.array_equal(production.candidate, new)
    binary_matrix = np.asarray(((1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 1, 1)), dtype=np.uint8)
    binary_graph = CompiledBinaryFlooding.from_check_matrix(binary_matrix)
    prior = math.log((1 - .08) / .08)
    for syndrome in (np.asarray((0, 0, 0), dtype=np.uint8),
                     np.asarray((1, 0, 1), dtype=np.uint8)):
        candidate, iterations, converged = decode_binary_numeric(
            binary_graph.row_ptr, binary_graph.variables, 4, prior, syndrome,
            8, 1, math.inf, 1e-10, 0.)
        old, old_converged, old_iterations = legacy_binary_decode(
            binary_graph.row_ptr, binary_graph.variables, 4, syndrome,
            prior, 25., 0, 8)
        assert iterations == old_iterations and converged == old_converged
        assert np.array_equal(candidate, old)
        production_binary = CompiledBinaryFlooding.from_check_matrix(binary_matrix, profile=BINARY_SPA_F64_V2)
        production_prior = production_binary._inputs(syndrome, .08)[1]
        newest, new_iterations, new_converged = decode_binary_numeric(
            production_binary.row_ptr, production_binary.variables, 4, production_prior, syndrome,
            8, 0, math.inf, 1e-10, .1)
        actual = production_binary.run(syndrome, error_rate=.08, max_iterations=8)
        assert (actual.iterations, actual.converged) == (new_iterations, new_converged)
        assert np.array_equal(actual.candidate, newest)
    print("Numeric BP4 and binary check algebra, reference replay, and finite small-graph agreement passed.")


if __name__ == "__main__":
    main()
