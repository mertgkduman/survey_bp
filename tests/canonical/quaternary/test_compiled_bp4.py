"""Differential qualification of the optional plain BP4 compiled prototype."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("numba")

from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import QBP4_F64_V1, QBP4_F64_V2
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem, compile_css_artifact


ROOT = Path(__file__).resolve().parents[3]


def _gb46() -> tuple[PauliCode, np.ndarray, list[np.ndarray]]:
    code = compile_css_artifact(
        parse_pinned_gb46_css((ROOT / "data/artifacts/gb46-h44.alist").read_bytes()),
        source_artifact_identity="gb46-h44-pinned-alist",
    )
    priors = np.tile([.92, .08 / 3, .08 / 3, .08 / 3], (code.n, 1))
    rng = np.random.default_rng(11019)
    rng.random((24, 72))  # Advance to the original benchmark's four-state sample stream.
    errors = np.zeros((8, code.n), dtype=np.uint8)
    for row in errors:
        selected = rng.random(code.n) < .08
        row[selected] = rng.choice(np.asarray([1, 2, 3], dtype=np.uint8), size=int(selected.sum()))
    return code, priors, [code.syndrome(error) for error in errors]


def test_new_compiled_default_and_explicit_v1_replay() -> None:
    code, priors, syndromes = _gb46()
    assert CompiledBp4Graph.from_code(code, priors).profile is QBP4_F64_V2
    old_graph = CompiledBp4Graph.from_code(code, priors, profile=QBP4_F64_V1)
    problem = QuaternaryOriginalProblem("original-compiled-frozen-v1", code, syndromes[0])
    expected = ScalarLlrBp4Kernel(profile=QBP4_F64_V1).new_session(problem, priors).run(max_iterations=8)
    actual = old_graph.run(syndromes[0], max_iterations=8)
    assert (actual.iterations, actual.converged) == (expected.iteration, expected.converged)
    np.testing.assert_array_equal(actual.candidate, expected.candidate)


def test_gb46_decisions_and_iterations_match_reference_for_early_and_fixed_caps() -> None:
    code, priors, syndromes = _gb46()
    compiled = CompiledBp4Graph.from_code(code, priors)
    reference = ScalarLlrBp4Kernel()
    for index, syndrome in enumerate(syndromes):
        problem = QuaternaryOriginalProblem(f"original-compiled-{index}", code, syndrome)
        for stop in (True, False):
            actual = compiled.run(syndrome, max_iterations=8, stop_on_convergence=stop)
            session = reference.new_session(problem, priors)
            if stop:
                expected = session.run(max_iterations=8)
            else:
                for _ in range(8):
                    expected = session.sweep(stop_on_convergence=False)
            assert (actual.iterations, actual.converged) == (expected.iteration, expected.converged)
            np.testing.assert_array_equal(actual.candidate, expected.candidate)


def test_gb46_first_three_sweep_buffers_match_reference() -> None:
    code, priors, syndromes = _gb46()
    compiled = CompiledBp4Graph.from_code(code, priors)
    reference = ScalarLlrBp4Kernel()
    for index in (0, 4, 5):
        session = reference.new_session(QuaternaryOriginalProblem(f"original-buffer-{index}", code, syndromes[index]), priors)
        old = compiled.initial_v2c()
        for _ in range(3):
            expected = session.sweep(stop_on_convergence=False)
            actual = compiled.sweep(old, syndromes[index])
            for field in ("c2v", "v2c", "beliefs", "marginals"):
                np.testing.assert_allclose(getattr(actual, field), getattr(expected, field), rtol=0, atol=1e-12)
            np.testing.assert_array_equal(actual.candidate, expected.candidate)
            assert actual.converged == expected.converged
            old = actual.v2c


def test_one_check_and_invalid_syndrome() -> None:
    code = PauliCode(checks=np.asarray([[1, 3]], dtype=np.uint8))
    priors = np.asarray([[.55, .10, .25, .10], [.25, .30, .20, .25]], dtype=np.float64)
    compiled = CompiledBp4Graph.from_code(code, priors)
    for syndrome in (np.asarray([0], dtype=np.uint8), np.asarray([1], dtype=np.uint8)):
        expected = ScalarLlrBp4Kernel().new_session(
            QuaternaryOriginalProblem("original-compiled-tree", code, syndrome), priors,
        ).sweep(stop_on_convergence=False)
        actual = compiled.sweep(compiled.initial_v2c(), syndrome)
        np.testing.assert_allclose(actual.c2v, expected.c2v, rtol=0, atol=1e-12)
        np.testing.assert_array_equal(actual.candidate, expected.candidate)
    with pytest.raises(ValueError):
        compiled.run(np.asarray([2], dtype=np.uint8), max_iterations=2)


def test_public_sweep_marginals_and_snapshot_survive_decode() -> None:
    code, priors, syndromes = _gb46()
    compiled = CompiledBp4Graph.from_code(code, priors)
    snapshot = compiled.sweep(compiled.initial_v2c(), syndromes[0])
    saved = tuple(getattr(snapshot, field).copy() for field in ("c2v", "v2c", "beliefs", "marginals", "candidate"))
    compiled.run(syndromes[1], max_iterations=8, stop_on_convergence=False)
    for field, expected in zip(("c2v", "v2c", "beliefs", "marginals", "candidate"), saved, strict=True):
        np.testing.assert_array_equal(getattr(snapshot, field), expected)
    np.testing.assert_allclose(snapshot.marginals.sum(axis=1), 1.0, rtol=0, atol=1e-15)
