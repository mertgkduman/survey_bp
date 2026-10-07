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


def _problem(n: int = 2) -> QuaternaryOriginalProblem:
    """A small commuting code whose rows expose X and Z components separately."""
    checks = np.vstack((
        np.full(n, Pauli.X, dtype=np.uint8),
        np.full(n, Pauli.Z, dtype=np.uint8),
    ))
    code = PauliCode(checks=checks, row_roles=("x", "z"))
    return QuaternaryOriginalProblem("original-sampling-fixture", code, np.zeros(2, dtype=np.uint8))


def _one_pauli_channel(label: Pauli) -> JointPauliChannel:
    """Put one deterministic Pauli on the first of two CSS-overlapping qubits."""
    row = np.zeros(4, dtype=np.float64)
    row[int(label)] = 1.0
    return JointPauliChannel.explicit([row, [1.0, 0.0, 0.0, 0.0]], n=2)


def test_public_joint_pauli_sampling_module_is_available():
    """QBP-02 requires a dedicated categorical joint-channel boundary."""
    assert importlib.util.find_spec("bp_registry.quaternary.sampling") is not None


def test_public_categorical_pauli_sampler_is_available():
    """QBP-02 must expose one categorical draw per physical qubit."""
    assert callable(sample_joint_pauli)


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


@pytest.mark.parametrize("label", [Pauli.I, Pauli.X, Pauli.Y, Pauli.Z])
def test_categorical_exact_pauli_channels_produce_one_deterministic_pauli(label):
    probabilities = np.zeros(4, dtype=np.float64)
    probabilities[int(label)] = 1.0
    sample = sample_joint_pauli(
        _problem(), channel=_one_pauli_channel(label),
        shot_id=7,
        manifest_identity="sampling-deterministic-v1",
    )

    assert sample.hidden.paulis.tolist() == [label, Pauli.I]
    assert sample.hidden.x.tolist() == [int(label in (Pauli.X, Pauli.Y)), 0]
    assert sample.hidden.z.tolist() == [int(label in (Pauli.Y, Pauli.Z)), 0]
    assert sample.observation.syndrome.tolist() == [int(label in (Pauli.Y, Pauli.Z)), int(label in (Pauli.X, Pauli.Y))]


def test_single_y_flips_both_css_component_observations():
    sample = sample_joint_pauli(
        _problem(), channel=_one_pauli_channel(Pauli.Y),
        shot_id=0, manifest_identity="single-y-v1",
    )

    assert sample.observation.syndrome.tolist() == [1, 1]
    assert sample.hidden.paulis.tolist() == [Pauli.Y, Pauli.I]


def test_correlated_joint_distribution_retains_y_mass_and_xz_covariance():
    channel = JointPauliChannel.explicit([0.5, 0.0, 0.5, 0.0], n=1)

    assert channel.resolved_probabilities[0, Pauli.Y] == 0.5
    assert channel.x_rate(0) == 0.5
    assert channel.z_rate(0) == 0.5
    assert channel.xz_covariance(0) == pytest.approx(0.25)


def test_exact_cumulative_boundaries_use_i_x_y_z_ownership(monkeypatch):
    channel = JointPauliChannel.explicit([0.1, 0.2, 0.3, 0.4], n=4)
    draws = iter([0.0, 0.1, 0.3, 0.6])
    monkeypatch.setattr("bp_registry.quaternary.sampling._rng", lambda identity, shot: type("Rng", (), {"random": lambda self: next(draws)})())

    sample = sample_joint_pauli(_problem(4), channel=channel, shot_id=0, manifest_identity="boundary-v1")

    assert sample.hidden.paulis.tolist() == [Pauli.I, Pauli.X, Pauli.Y, Pauli.Z]


def test_replay_identity_binds_channel_order_and_shot_and_rejects_tampering():
    channel = JointPauliChannel.depolarizing(0.4, n=2)
    first = sample_joint_pauli(_problem(), channel=channel, shot_id=3, manifest_identity="replay-v1")
    second = sample_joint_pauli(_problem(), channel=channel, shot_id=3, manifest_identity="replay-v1")

    assert first.sample_identity == second.sample_identity
    assert first.hidden.paulis.tolist() == second.hidden.paulis.tolist()
    assert first.ledger["channel_identity"] == channel.identity
    assert first.ledger["pauli_order"] == "I,X,Y,Z"
    tampered = JointPauliChannel.depolarizing(0.5, n=1)
    assert tampered.identity != channel.identity
    assert first.sample_identity != hashlib.sha256(f"joint-pauli-sample-v1\0replay-v1\0{tampered.identity}\03".encode()).hexdigest()
