"""Bounded binary source-policy checks for the Yao BPGD development backend."""

import numpy as np
import pytest

from bp_registry.canonical.compiled import CompiledBinaryFlooding


@pytest.fixture
def graph() -> CompiledBinaryFlooding:
    return CompiledBinaryFlooding.from_check_matrix(np.asarray(((1, 1),), dtype=np.uint8))


def test_paper_bpgd_continues_buffers_and_checks_after_complete_blocks(graph: CompiledBinaryFlooding) -> None:
    syndrome = np.asarray((1,), dtype=np.uint8)
    capped = graph.run_paper_bpgd(syndrome, error_rate=.1, sweeps_per_round=2, round_limit=1)
    assert not capped.converged
    assert (capped.iterations, capped.rounds, capped.fixations) == (2, 1, 1)
    completed = graph.run_paper_bpgd(syndrome, error_rate=.1, sweeps_per_round=2, round_limit=2)
    assert completed.converged
    assert (completed.iterations, completed.rounds, completed.fixations) == (4, 2, 1)
    assert np.array_equal((np.asarray(((1, 1),), dtype=np.uint8) @ completed.candidate) % 2, syndrome)


def test_paper_bp_returns_first_syndrome_match_and_random_order_is_seeded(graph: CompiledBinaryFlooding) -> None:
    syndrome = np.asarray((0,), dtype=np.uint8)
    plain = graph.run_paper_bp(syndrome, error_rate=.1, max_iterations=100)
    assert plain.converged and plain.iterations == 1
    draws = np.asarray((.9, .1), dtype=np.float64)
    first = graph.run_paper_bpgd(np.asarray((1,), dtype=np.uint8), error_rate=.1,
                                 sweeps_per_round=1, order="uniform_random", random_draws=draws)
    second = graph.run_paper_bpgd(np.asarray((1,), dtype=np.uint8), error_rate=.1,
                                  sweeps_per_round=1, order="uniform_random", random_draws=draws)
    assert np.array_equal(first.candidate, second.candidate)
    assert first.iterations == second.iterations
