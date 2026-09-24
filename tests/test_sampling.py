"""Identified samples and explicit decoder-visible observations."""

import importlib.util

import pytest


def _sample_shot():
    assert importlib.util.find_spec("bp_registry.sampling") is not None, (
        "sampling must be a standalone tracer interface"
    )
    from bp_registry.sampling import sample_shot

    return sample_shot


@pytest.mark.parametrize("rate,expected", [(0.0, 0), (1.0, 3)])
def test_x_only_rate_boundaries(small_css_checks, rate, expected):
    from bp_registry.css import CssCode
    hx, hz = small_css_checks
    sample = _sample_shot()(CssCode(hx=hx, hz=hz), shot_id=7, seed=19, x_error_rate=rate)
    assert sample.shot_id == 7
    assert int(sample.hidden_x.sum()) == expected
    assert sample.observation.check_type == "Z"


@pytest.mark.parametrize("bad_rate", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_rates_are_rejected(small_css_checks, bad_rate):
    from bp_registry.css import CssCode
    hx, hz = small_css_checks
    with pytest.raises(ValueError):
        _sample_shot()(CssCode(hx=hx, hz=hz), shot_id=0, seed=1, x_error_rate=bad_rate)


def test_manifest_identity_and_shot_id_replay_the_same_hidden_error(small_css_checks):
    from bp_registry.css import CssCode

    hx, hz = small_css_checks
    code = CssCode(hx=hx, hz=hz)
    sampler = _sample_shot()
    first = sampler(code, manifest_identity="a" * 64, shot_id=9, seed=1, x_error_rate=0.4)
    replay = sampler(code, manifest_identity="a" * 64, shot_id=9, seed=99, x_error_rate=0.4)
    changed = sampler(code, manifest_identity="b" * 64, shot_id=9, seed=1, x_error_rate=0.4)
    assert first.sample_identity == replay.sample_identity
    assert (first.hidden_x == replay.hidden_x).all()
    assert first.sample_identity != changed.sample_identity


def test_separate_xz_observations_are_named_by_check_type(small_css_checks):
    import numpy as np
    from bp_registry.css import CssCode

    hx, hz = small_css_checks
    sample = _sample_shot()(
        CssCode(hx=hx, hz=hz), shot_id=3, seed=7, x_error_rate=1.0, z_error_rate=1.0
    )
    assert sample.observations["Z"].syndrome.tolist() == ((hz @ np.ones(3, dtype=np.uint8)) % 2).tolist()
    assert sample.observations["X"].syndrome.tolist() == ((hx @ np.ones(3, dtype=np.uint8)) % 2).tolist()


def test_parameter_assignment_identity_does_not_consume_or_relabel_physical_samples(small_css_checks):
    from bp_registry.css import CssCode
    from bp_registry.canonical.updates import ParameterGeneratorSpec, ParameterRefreshPlan

    hx, hz = small_css_checks
    code = CssCode(hx=hx, hz=hz)
    baseline = _sample_shot()(code, manifest_identity="a" * 64, shot_id=5, seed=7, x_error_rate=0.4)
    spec = ParameterGeneratorSpec.model_validate({
        "shape": "scalar", "graph_sha256": "b" * 64, "distribution": "uniform",
        "low": 0.0, "high": 1.0, "root_seed_identity": "c" * 64,
    })
    assert ParameterRefreshPlan(scope="attempt", generator=spec).initial_state(
        configuration_identity="policy-a", attempt_identity="attempt:5"
    ).derived_identity != ParameterRefreshPlan(scope="attempt", generator=spec).initial_state(
        configuration_identity="policy-b", attempt_identity="attempt:5"
    ).derived_identity
    matched = _sample_shot()(code, manifest_identity="a" * 64, shot_id=5, seed=999, x_error_rate=0.4)
    assert baseline.sample_identity == matched.sample_identity
    assert (baseline.hidden_x == matched.hidden_x).all()
