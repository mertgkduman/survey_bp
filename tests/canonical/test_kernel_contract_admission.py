"""Regression counterexamples from the v3 policy/evidence audit."""
from dataclasses import replace
import numpy as np
import pytest

from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64, BINARY_SPA_F64_V3
from bp_registry.canonical.updates import MinSumUpdate


@pytest.mark.parametrize('profile', [MIN_SUM_CPU_F64, replace(MIN_SUM_CPU_F64, saturation=20.)])
def test_plain_spa_rejects_min_sum_profile_in_both_backends(profile):
    with pytest.raises(ValueError, match='SPA.*profile'):
        BinarySpaKernel(profile=profile)
    with pytest.raises(ValueError, match='SPA.*profile'):
        CompiledBinaryFlooding.from_check_matrix(np.array([[1, 1, 1]], dtype=np.uint8), profile=profile)


def test_explicit_min_sum_and_default_spa_keep_distinct_equations():
    incoming = np.array([1., 2.])
    scalar = BinarySpaKernel(update_rule=MinSumUpdate())
    assert scalar.profile == MIN_SUM_CPU_F64
    assert scalar.check_message(incoming, 0) == 1.
    plain = BinarySpaKernel()
    assert plain.profile == BINARY_SPA_F64_V3
    assert plain.check_message(incoming, 0) == pytest.approx(2 * np.arctanh(np.tanh(.5) * np.tanh(1.)))
    compiled = CompiledBinaryFlooding.from_check_matrix(np.array([[1, 1, 1]], dtype=np.uint8), rule='min_sum')
    assert compiled.profile == MIN_SUM_CPU_F64
