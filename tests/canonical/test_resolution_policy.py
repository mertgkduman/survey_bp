"""Numerical boundaries and corrected compiled MS policy behavior."""

from __future__ import annotations

import json

import numpy as np
import pytest

pytest.importorskip("numba")

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.css import CssCode
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2
from bp_registry.quaternary.problems import PauliCode
from bp_registry.resolution import BpFloodingPolicy, DEFAULT_BP4_MIN_SUM, ResolutionPolicy


def test_resolution_formats_round_at_declared_boundaries() -> None:
    for name, dtype in (("float16", np.float16), ("float32", np.float32), ("float64", np.float64)):
        policy = ResolutionPolicy(name)
        for value in (0.1, -1.234567, 2 ** -20, 127.125):
            assert policy.quantize(value) == float(dtype(value))
    q8 = ResolutionPolicy("int8", 16)
    assert q8.quantize(1 / 32) == 0.0  # halfway, ties to even
    assert q8.quantize(3 / 32) == 0.125
    assert q8.quantize(100.0) == 127 / 16
    assert q8.quantize(-100.0) == -127 / 16
    assert ResolutionPolicy("int16", 256).quantize(0.1) == 26 / 256
    assert ResolutionPolicy("int32", 1024).quantize(0.1) == 102 / 1024
    with pytest.raises(ValueError):
        ResolutionPolicy("int8")
    with pytest.raises(ValueError):
        ResolutionPolicy("float32", 16)


def test_coefficients_have_explicit_format_and_replay_identity() -> None:
    quantized = BpFloodingPolicy(
        resolution=ResolutionPolicy("int8", 16, coefficients="same"),
        damping=0.1, alpha=0.9, beta=0.1,
    )
    assert quantized.coefficients == (0.125, 0.875, 0.875, 0.125)
    unquantized = BpFloodingPolicy(
        resolution=ResolutionPolicy("int8", 16, coefficients="float64"),
        damping=0.1, alpha=0.9, beta=0.1,
    )
    assert unquantized.coefficients == (0.1, 0.9, 0.9, 0.1)
    assert quantized.semantic_identity != unquantized.semantic_identity
    assert BpFloodingPolicy.from_spec(json.loads(json.dumps(quantized.as_spec()))) == quantized
    with pytest.raises(ValueError):
        BpFloodingPolicy.from_spec({**quantized.as_spec(), "unknown": 1})


def test_bp4_min_sum_default_projects_before_q8_rounding() -> None:
    code = PauliCode(checks=np.asarray([[1, 1]], dtype=np.uint8))
    priors = np.tile((.999997, .000001, .000001, .000001), (2, 1))
    graph = CompiledBp4Graph.from_code(code, priors, rule="min_sum")
    assert graph.policy is DEFAULT_BP4_MIN_SUM
    assert graph.profile is QBP4_F64_V2
    old = graph.initial_v2c()
    old[1] = np.asarray([-20.0, -19.0, 20.0])
    sweep = graph.sweep(old, np.asarray([0], dtype=np.uint8))
    # Commute and anticommute log masses are ~20 and ~19. If each were
    # clipped to the Q8 range before subtraction, this message would be zero.
    assert sweep.c2v[0] == 1.0
    assert sweep.v2c.dtype == np.float64
    assert np.any(np.abs(sweep.v2c) > 127 / 16)


def test_binary_min_sum_accepts_the_same_resolution_and_quantized_damping() -> None:
    h = np.asarray([[1, 1], [0, 1]], dtype=np.uint8)
    policy = BpFloodingPolicy(
        check_rule="min_sum", resolution=ResolutionPolicy("int8", 16, coefficients="same"),
        damping=0.1, alpha=1.0, beta=0.1,
    )
    graph = CompiledBinaryFlooding.from_check_matrix(h, rule="min_sum", policy=policy)
    syndrome = np.asarray([1, 0], dtype=np.uint8)
    sweep = graph.sweep(np.asarray([1.0, 1.0, 1.0]), syndrome, error_rate=0.1)
    assert np.all(sweep.check_to_variable * 16 == np.rint(sweep.check_to_variable * 16))
    assert np.all(sweep.new_v2c * 16 == np.rint(sweep.new_v2c * 16))
    bound = graph.bind_error_rate(.1).run(syndrome, max_iterations=3)
    direct = graph.run(syndrome, error_rate=.1, max_iterations=3)
    assert (bound.converged, bound.iterations) == (direct.converged, direct.iterations)
    np.testing.assert_array_equal(bound.candidate, direct.candidate)


def test_css_constructor_preserves_x_then_z_syndrome_order() -> None:
    code = CssCode(
        hx=np.asarray([[1, 1, 0]], dtype=np.uint8),
        hz=np.asarray([[0, 0, 1]], dtype=np.uint8),
    )
    graph = CompiledBp4Graph.from_css(code, .08, rule="min_sum")
    assert graph.policy is DEFAULT_BP4_MIN_SUM
    np.testing.assert_array_equal(graph.row_ptr, [0, 2, 3])
    np.testing.assert_array_equal(graph.labels, [1, 1, 3])
    np.testing.assert_array_equal(graph.variables, [0, 1, 2])
    np.testing.assert_allclose(graph.prior_llrs, np.log((1 - .08) / (.08 / 3)))
    with pytest.raises(ValueError):
        CompiledBp4Graph.from_css(CssCode(hx=code.hx, hz=np.asarray([[1, 0, 0]])), .08)


def test_resolution_policy_composes_with_sum_product_in_both_families() -> None:
    policy = BpFloodingPolicy(
        check_rule="sum_product",
        resolution=ResolutionPolicy("float32", scope="all_messages", coefficients="same"),
        damping=.1,
    )
    code = PauliCode(checks=np.asarray([[1, 1]], dtype=np.uint8))
    priors = np.tile((.9, 1 / 30, 1 / 30, 1 / 30), (2, 1))
    bp4 = CompiledBp4Graph.from_code(code, priors, policy=policy)
    binary = CompiledBinaryFlooding.from_check_matrix(
        np.asarray([[1, 1]], dtype=np.uint8), policy=policy,
    )
    s = np.asarray([1], dtype=np.uint8)
    assert bp4.run(s, max_iterations=2).candidate.shape == (2,)
    assert binary.run(s, error_rate=.1, max_iterations=2).candidate.shape == (2,)
    with pytest.raises(ValueError):
        BpFloodingPolicy(check_rule="sum_product", beta=.25)


@pytest.mark.parametrize("format_name,scale", [
    ("float16", None), ("float32", None), ("float64", None),
    ("int8", 16), ("int16", 256), ("int32", 1024),
])
def test_both_families_execute_each_format(format_name: str, scale: int | None) -> None:
    resolution = ResolutionPolicy(format_name, scale, "all_state", "same")
    policy = BpFloodingPolicy(resolution=resolution, damping=.1)
    code = PauliCode(checks=np.asarray([[1, 1]], dtype=np.uint8))
    priors = np.tile((.9, 1 / 30, 1 / 30, 1 / 30), (2, 1))
    bp4 = CompiledBp4Graph.from_code(code, priors, policy=policy)
    binary = CompiledBinaryFlooding.from_check_matrix(
        np.asarray([[1, 1]], dtype=np.uint8), rule="min_sum", policy=policy,
    )
    s = np.asarray([1], dtype=np.uint8)
    bp4_result = bp4.run(s, max_iterations=3)
    binary_result = binary.run(s, error_rate=.1, max_iterations=3)
    assert bp4_result.candidate.shape == binary_result.candidate.shape == (2,)
    assert 0 <= bp4_result.iterations <= 3
    assert 0 <= binary_result.iterations <= 3
