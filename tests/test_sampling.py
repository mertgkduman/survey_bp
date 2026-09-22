"""Identified samples and explicit decoder-visible observations."""

import pytest


@pytest.mark.parametrize("rate,expected", [(0.0, 0), (1.0, 3)])
def test_x_only_rate_boundaries(small_css_checks, rate, expected):
    from bp_registry.css import CssCode
    from bp_registry.sampling import sample_shot

    hx, hz = small_css_checks
    sample = sample_shot(CssCode(hx=hx, hz=hz), shot_id=7, seed=19, x_error_rate=rate)
    assert sample.shot_id == 7
    assert int(sample.hidden_x.sum()) == expected
    assert sample.observation.check_type == "Z"


@pytest.mark.parametrize("bad_rate", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_rates_are_rejected(small_css_checks, bad_rate):
    from bp_registry.css import CssCode
    from bp_registry.sampling import sample_shot

    hx, hz = small_css_checks
    with pytest.raises(ValueError):
        sample_shot(CssCode(hx=hx, hz=hz), shot_id=0, seed=1, x_error_rate=bad_rate)

