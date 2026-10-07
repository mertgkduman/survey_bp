"""Behavior contracts for categorical joint Pauli sampling."""

from __future__ import annotations

import hashlib
import importlib.util

import numpy as np
import pytest

from bp_registry.quaternary.algebra import Pauli
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem
try:
    from bp_registry.quaternary.sampling import (
        DecoderPriorSmoothing,
        JointPauliChannel,
    )
except ModuleNotFoundError:
    DecoderPriorSmoothing = JointPauliChannel = None

try:
    from bp_registry.quaternary.sampling import sample_joint_pauli
except ImportError:
    sample_joint_pauli = None


def _problem(n: int = 1) -> QuaternaryOriginalProblem:
    """A small commuting code whose rows expose X and Z components separately."""
    checks = np.vstack((
        np.full(n, Pauli.X, dtype=np.uint8),
        np.full(n, Pauli.Z, dtype=np.uint8),
    ))
    code = PauliCode(checks=checks, row_roles=("x", "z"))
    return QuaternaryOriginalProblem("original-sampling-fixture", code, np.zeros(2, dtype=np.uint8))


def test_public_joint_pauli_sampling_module_is_available():
    """QBP-02 requires a dedicated categorical joint-channel boundary."""
    assert importlib.util.find_spec("bp_registry.quaternary.sampling") is not None


@pytest.mark.parametrize("p,expected", [
    (0.0, [1.0, 0.0, 0.0, 0.0]),
    (1.0, [0.0, 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]),
])
def test_named_depolarizing_endpoint_channels_preserve_exact_physical_zeros(p, expected):
    channel = JointPauliChannel.depolarizing(p, n=2)

    assert channel.kind == "depolarizing"
    assert channel.scalar_physical_p == p
    assert channel.pauli_order == "I,X,Y,Z"
    assert channel.resolved_probabilities.shape == (2, 4)
    assert channel.resolved_probabilities[0].tolist() == expected
    assert not channel.resolved_probabilities.flags.writeable


@pytest.mark.parametrize("p", [-1e-15, 1.000000000000001, float("nan"), float("inf"), True])
def test_named_depolarizing_rejects_nonfinite_and_out_of_range_endpoints(p):
    with pytest.raises(ValueError, match="p"):
        JointPauliChannel.depolarizing(p, n=1)


def test_shared_and_per_qubit_tables_are_retained_without_normalization():
    shared = JointPauliChannel.explicit([0.4, 0.1, 0.2, 0.3], n=2)
    per_qubit = JointPauliChannel.explicit(
        [[1.0, 0.0, 0.0, 0.0], [0.25, 0.25, 0.4, 0.1]], n=2
    )

    assert shared.kind == "explicit_shared"
    assert shared.raw_declaration == ((0.4, 0.1, 0.2, 0.3),)
    assert shared.resolved_probabilities.tolist() == [[0.4, 0.1, 0.2, 0.3]] * 2
    assert shared.scalar_physical_p is None
    assert shared.physical_nonidentity_rates.tolist() == [0.6, 0.6]
    assert per_qubit.kind == "explicit_per_qubit"
    assert per_qubit.resolved_probabilities.tolist() == [[1.0, 0.0, 0.0, 0.0], [0.25, 0.25, 0.4, 0.1]]
    assert per_qubit.scalar_physical_p is None
    assert per_qubit.physical_nonidentity_rates.tolist() == [0.0, 0.75]


@pytest.mark.parametrize("table", [
    [0.4, 0.1, 0.2],
    [[0.4, 0.1, 0.2, 0.3], [0.4, 0.1, 0.2, 0.3], [0.4, 0.1, 0.2, 0.3]],
    [0.4, 0.1, 0.2, 0.300000000002],
    [0.4, -0.1, 0.2, 0.5],
    [0.4, 0.1, float("nan"), 0.3],
])
def test_explicit_channels_reject_malformed_tables_without_normalizing(table):
    with pytest.raises(ValueError):
        JointPauliChannel.explicit(table, n=2)


def test_table_tolerance_is_persisted_but_probability_rows_are_unchanged():
    table = np.asarray([0.1, 0.2, 0.3, 0.4000000000005], dtype=np.float64)
    channel = JointPauliChannel.explicit(table, n=1)

    assert channel.row_sum_tolerance == 1e-12
    assert np.array_equal(channel.resolved_probabilities[0], table)


def test_decoder_smoothing_has_a_separate_identity_and_cannot_change_channel():
    channel = JointPauliChannel.depolarizing(0.0, n=1)
    smoothing = DecoderPriorSmoothing(floor=1e-9)

    assert channel.resolved_probabilities.tolist() == [[1.0, 0.0, 0.0, 0.0]]
    assert smoothing.identity != channel.identity
    assert smoothing.apply(channel.resolved_probabilities).tolist() == [[1.0, 1e-9, 1e-9, 1e-9]]
    assert channel.resolved_probabilities.tolist() == [[1.0, 0.0, 0.0, 0.0]]
