"""Regression counterexamples from the v3 policy/evidence audit."""
from dataclasses import dataclass, fields, replace
from pathlib import Path
import json
import numpy as np
import pytest

from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64, BINARY_SPA_F64_V3
from bp_registry.canonical.updates import MinSumUpdate
from bp_registry.canonical.numerics import REFERENCE_CPU_F64, BINARY_SPA_F64_V2
from bp_registry.quaternary.numerics import QBP4_F64_V1, QBP4_F64_V2, QBP4_F64_V3


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


PROFILES = (REFERENCE_CPU_F64, MIN_SUM_CPU_F64, BINARY_SPA_F64_V2, BINARY_SPA_F64_V3,
            QBP4_F64_V1, QBP4_F64_V2, QBP4_F64_V3)


def parameters(profile):
    if profile in (REFERENCE_CPU_F64, MIN_SUM_CPU_F64, QBP4_F64_V1):
        return {'saturation'}
    return {'check_cap', 'product_epsilon', 'v2c_damping'} | ({'check_rule'} if profile in (QBP4_F64_V2, QBP4_F64_V3) else set())


@pytest.mark.parametrize('profile,field', [
    pytest.param(profile, f.name, id=f'{profile.profile_id}:{f.name}')
    for profile in PROFILES for f in fields(profile) if f.name not in parameters(profile) | {'profile_id'}
])
def test_fixed_profile_evidence_cannot_be_changed(profile, field):
    value = getattr(profile, field)
    changed = 'unsupported_semantics' if isinstance(value, str) else value + 1
    with pytest.raises(ValueError):
        replace(profile, **{field: changed})


@pytest.mark.parametrize('profile', PROFILES, ids=lambda p: p.profile_id)
def test_existing_profile_serialization_is_unchanged(profile):
    frozen = json.loads(Path('.planning/spikes/017-profile-evidence-fix/frozen-profiles.json').read_text())
    assert profile.as_evidence() == frozen[profile.profile_id]


@pytest.mark.parametrize('profile', PROFILES, ids=lambda p: p.profile_id)
def test_subclass_defaults_cannot_relabel_precision(profile):
    @dataclass(frozen=True)
    class PretendFloat32(type(profile)):
        dtype: str = 'float32'

    with pytest.raises(ValueError, match='dtype'):
        PretendFloat32()


@pytest.mark.parametrize('profile', PROFILES, ids=lambda p: p.profile_id)
def test_implemented_profile_parameters_remain_available(profile):
    if 'saturation' in parameters(profile):
        custom = replace(profile, saturation=12.3)
        assert custom.as_evidence()['saturation'] == 12.3
    else:
        custom = replace(profile, check_cap=17., product_epsilon=1e-7, v2c_damping=.6)
        assert custom.as_evidence()['check_cap'] == 17.
        if 'check_rule' in parameters(profile):
            assert replace(profile, check_rule='boxplus').check_rule == 'boxplus'


@pytest.mark.parametrize('profile', PROFILES, ids=lambda p: p.profile_id)
@pytest.mark.parametrize('value', [float('nan'), float('inf'), -1., True, 'invalid'])
def test_profile_parameters_reject_invalid_numeric_values(profile, value):
    for field in parameters(profile) - {'check_rule'}:
        with pytest.raises(ValueError):
            replace(profile, **{field: value})


@pytest.mark.parametrize('profile', [BINARY_SPA_F64_V2, QBP4_F64_V2], ids=lambda p: p.profile_id)
def test_historical_undamped_alias_has_exact_recorded_parameters(profile):
    alias = profile.profile_id + '-undamped'
    preserved = replace(profile, profile_id=alias, v2c_damping=0.)
    assert preserved.as_evidence() == {**profile.as_evidence(), 'profile_id': alias, 'v2c_damping': 0.}
    for changes in ({'v2c_damping': .1}, {'check_cap': 17.}, {'product_epsilon': 1e-7}, {'dtype': 'float32'}):
        with pytest.raises(ValueError):
            replace(preserved, **changes)


@pytest.mark.parametrize('profile', PROFILES, ids=lambda p: p.profile_id)
def test_custom_study_labels_preserve_semantics_and_reserved_identities(profile):
    if profile == MIN_SUM_CPU_F64:
        # A custom min-sum label is bound to its explicit normalization marker.
        custom = replace(profile, profile_id='study-minsum')
    else:
        custom = replace(profile, profile_id='study-tuning-arm-1')
    assert {k: v for k, v in custom.as_evidence().items() if k != 'profile_id'} == {
        k: v for k, v in profile.as_evidence().items() if k != 'profile_id'}
    other = QBP4_F64_V3.profile_id if profile != QBP4_F64_V3 else BINARY_SPA_F64_V3.profile_id
    for bad in ('', 'contains spaces', other):
        with pytest.raises(ValueError):
            replace(profile, profile_id=bad)
