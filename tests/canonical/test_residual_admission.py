"""Conventional source-scoped sRBP admits only undamped variable updates."""
from dataclasses import replace

import numpy as np
import pytest

from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import (
    REFERENCE_CPU_F64, BINARY_SPA_F64_V2, BINARY_SPA_F64_V3,
)
from bp_registry.canonical.residual import SyndromeResidualSchedule
from bp_registry.canonical.schedules import EdgeTable


def table():
    return EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])


@pytest.mark.parametrize('profile', [None, BINARY_SPA_F64_V2, BINARY_SPA_F64_V3,
    replace(BINARY_SPA_F64_V2, v2c_damping=.6),
    replace(BINARY_SPA_F64_V3, v2c_damping=.6)])
def test_residual_rejects_ignored_damping_before_state_exists(profile):
    kernel = BinarySpaKernel() if profile is None else BinarySpaKernel(profile=profile)
    with pytest.raises(ValueError, match='undamped'):
        SyndromeResidualSchedule(table(), kernel=kernel)


@pytest.mark.parametrize('profile', [REFERENCE_CPU_F64,
    replace(BINARY_SPA_F64_V2, v2c_damping=0.),
    replace(BINARY_SPA_F64_V3, v2c_damping=0.)])
def test_residual_admits_legacy_and_explicit_undamped_profiles(profile):
    schedule = SyndromeResidualSchedule(table(), kernel=BinarySpaKernel(profile=profile))
    v2c, c2v, syndrome = np.array([1., 2., 3., 4.]), np.zeros(4), np.zeros(2, dtype=np.uint8)
    cache = schedule.initialize(v2c, c2v, syndrome, error_rate=.2)
    proposal = schedule.propose_local_step(v2c, c2v, cache, syndrome, error_rate=.2)
    assert proposal.selection.index == 2
    # Construction and proposal formation preserve caller-owned messages.
    np.testing.assert_array_equal(v2c, [1., 2., 3., 4.])
    np.testing.assert_array_equal(c2v, np.zeros(4))
