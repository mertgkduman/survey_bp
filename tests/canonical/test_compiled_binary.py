"""Differential qualification for the optional compiled binary prototype."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("numba")

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2, MIN_SUM_CPU_F64, REFERENCE_CPU_F64
from bp_registry.canonical.schedules import FloodingSchedule
from bp_registry.canonical.updates import MinSumUpdate


ROOT = Path(__file__).resolve().parents[2]


def _reference(rule: str) -> BinarySpaKernel:
    return BinarySpaKernel() if rule == "spa" else BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())


def test_spa_v2_is_default_and_frozen_v1_remains_selectable() -> None:
    h = np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    syndrome = np.asarray([1, 0], dtype=np.uint8)
    assert BinarySpaKernel(profile=BINARY_SPA_F64_V2).profile is BINARY_SPA_F64_V2
    assert BinarySpaKernel().profile.profile_id == "binary-spa-flooding-f64-v3"
    for profile in (BINARY_SPA_F64_V2, REFERENCE_CPU_F64):
        graph = CompiledBinaryFlooding.from_check_matrix(h, profile=profile)
        expected = BinarySpaKernel(profile=profile).run(h, syndrome, error_rate=.08, max_iterations=12)
        actual = graph.run(syndrome, error_rate=.08, max_iterations=12)
        assert (actual.iterations, actual.converged) == (expected.iterations, expected.converged)
        np.testing.assert_array_equal(actual.candidate, expected.candidate)


@pytest.mark.parametrize("rule", ["spa", "min_sum"])
def test_bb72_fixed_seed_matches_reference_decisions_and_sweeps(rule: str) -> None:
    h = np.asarray(json.loads((ROOT / "data/artifacts/bb72-css.json").read_text())["hz"], dtype=np.uint8)
    rng = np.random.default_rng(11019)
    errors = (rng.random((24, h.shape[1])) < .08).astype(np.uint8)
    syndromes = np.asarray((errors @ h.T) % 2, dtype=np.uint8)
    compiled = CompiledBinaryFlooding.from_check_matrix(h, rule=rule)
    bound = compiled.bind_error_rate(.08)
    reference = _reference(rule)
    schedule = FloodingSchedule(compiled.table, kernel=reference, profile=reference.profile)
    for syndrome in syndromes:
        expected = reference.run(h, syndrome, error_rate=.08, max_iterations=10)
        actual = compiled.run(syndrome, error_rate=.08, max_iterations=10)
        bound_actual = bound.run(syndrome, max_iterations=10)
        assert (actual.converged, actual.iterations) == (expected.converged, expected.iterations)
        np.testing.assert_array_equal(actual.candidate, expected.candidate)
        assert (bound_actual.converged, bound_actual.iterations) == (expected.converged, expected.iterations)
        np.testing.assert_array_equal(bound_actual.candidate, expected.candidate)
    for syndrome in (syndromes[0], syndromes[1], syndromes[2]):
        old_reference = schedule.initialize(.08)
        old_compiled = old_reference.copy()
        for _ in range(3):
            expected = schedule.sweep(old_reference, syndrome, error_rate=.08)
            actual = compiled.sweep(old_compiled, syndrome, error_rate=.08)
            for field in ("check_to_variable", "beliefs", "new_v2c"):
                np.testing.assert_allclose(getattr(actual, field), getattr(expected, field), rtol=0, atol=1e-12)
            np.testing.assert_array_equal(actual.candidate, expected.candidate)
            old_reference, old_compiled = expected.new_v2c, actual.new_v2c


@pytest.mark.parametrize("rule", ["spa", "min_sum"])
def test_degree_one_disconnected_and_zero_edge_graphs(rule: str) -> None:
    reference = _reference(rule)
    for h in (
        np.asarray([[1, 0, 0], [0, 1, 0]], dtype=np.uint8),
        np.asarray([[1, 1, 0], [0, 0, 1]], dtype=np.uint8),
        np.zeros((2, 3), dtype=np.uint8),
    ):
        compiled = CompiledBinaryFlooding.from_check_matrix(h, rule=rule)
        for syndrome in (np.zeros(h.shape[0], dtype=np.uint8), np.ones(h.shape[0], dtype=np.uint8)):
            for cap in (0, 1, 5):
                expected = reference.run(h, syndrome, error_rate=.2, max_iterations=cap)
                actual = compiled.run(syndrome, error_rate=.2, max_iterations=cap)
                assert (actual.converged, actual.iterations) == (expected.converged, expected.iterations)
                np.testing.assert_array_equal(actual.candidate, expected.candidate)


def test_rejects_nonbinary_inputs_and_unknown_policy() -> None:
    with pytest.raises(ValueError):
        CompiledBinaryFlooding.from_check_matrix(np.asarray([[2]], dtype=np.int64))
    with pytest.raises(ValueError):
        CompiledBinaryFlooding.from_check_matrix(np.asarray([[1]], dtype=np.uint8), rule="offset_min_sum")
    compiled = CompiledBinaryFlooding.from_check_matrix(np.asarray([[1]], dtype=np.uint8))
    with pytest.raises(ValueError):
        compiled.run(np.asarray([2], dtype=np.uint8), error_rate=.1, max_iterations=1)
    with pytest.raises(ValueError):
        compiled.run(np.asarray([1], dtype=np.uint8), error_rate=0, max_iterations=1)


@pytest.mark.parametrize("rule", ["spa", "min_sum"])
def test_clipped_initial_messages_and_public_sweep_snapshot(rule: str) -> None:
    h = np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    syndrome = np.asarray([1, 0], dtype=np.uint8)
    compiled = CompiledBinaryFlooding.from_check_matrix(h, rule=rule)
    reference = _reference(rule)
    for error_rate in (1e-12, 1 - 1e-12):
        expected = reference.run(h, syndrome, error_rate=error_rate, max_iterations=4)
        actual = compiled.run(syndrome, error_rate=error_rate, max_iterations=4)
        assert (actual.converged, actual.iterations) == (expected.converged, expected.iterations)
        np.testing.assert_array_equal(actual.candidate, expected.candidate)
        old = np.full(compiled.table.edge_count, 1e6, dtype=np.float64)
        snapshot = compiled.sweep(old, syndrome, error_rate=error_rate)
        saved = snapshot.new_v2c.copy()
        compiled.sweep(snapshot.new_v2c, syndrome, error_rate=error_rate)
        compiled.run(syndrome, error_rate=error_rate, max_iterations=4)
        np.testing.assert_array_equal(snapshot.new_v2c, saved)
