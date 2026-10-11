"""Regression tests for the campaign statistical decision boundary."""

from __future__ import annotations

import math
import importlib

import pytest
from scipy.stats import binomtest

from bp_registry.campaigns.contracts import TargetReferenceV1
_HASH = "a" * 64


def _statistics_api() -> object:
    try:
        return importlib.import_module("bp_registry.campaigns.statistics")
    except ModuleNotFoundError:
        return None


def _exact_binomial_rate(*args: object, **kwargs: object) -> object:
    api = _statistics_api()
    assert api is not None, "campaign statistics module must provide exact rates"
    return api.exact_binomial_rate(*args, **kwargs)


def _target_interval_decision(*args: object, **kwargs: object) -> object:
    api = _statistics_api()
    assert api is not None, "campaign statistics module must provide target decisions"
    return api.target_interval_decision(*args, **kwargs)


@pytest.mark.parametrize("shots", range(1, 8))
def test_binomial_matches_scipy_for_every_small_count(shots: int) -> None:
    for failures in range(shots + 1):
        result = _exact_binomial_rate(
            failures=failures,
            shots=shots,
            alpha=0.05,
            count_receipt_sha256=_HASH,
        )
        expected = binomtest(failures, shots).proportion_ci(
            confidence_level=0.95,
            method="exact",
        )
        assert result.failures == failures
        assert result.shots == shots
        assert result.estimate == failures / shots
        assert result.interval == pytest.approx((expected.low, expected.high))


def test_zero_failure_keeps_positive_upper_exact_bound() -> None:
    result = _exact_binomial_rate(
        failures=0, shots=10, alpha=0.05, count_receipt_sha256=_HASH,
    )
    assert result.estimate == 0.0
    assert result.interval[0] == 0.0
    assert 0.0 < result.interval[1] < 1.0


def test_all_failure_keeps_subunit_lower_exact_bound() -> None:
    result = _exact_binomial_rate(
        failures=10, shots=10, alpha=0.05, count_receipt_sha256=_HASH,
    )
    assert result.estimate == 1.0
    assert 0.0 < result.interval[0] < 1.0
    assert result.interval[1] == 1.0


@pytest.mark.parametrize("failures,shots", [(0, 0), (-1, 1), (2, 1), (True, 1), (1, True)])
def test_binomial_rejects_invalid_integer_counts(failures: int, shots: int) -> None:
    with pytest.raises(ValueError):
        _exact_binomial_rate(
            failures=failures, shots=shots, alpha=0.05, count_receipt_sha256=_HASH,
        )


def _target() -> TargetReferenceV1:
    return TargetReferenceV1(
        target_id="p050",
        target_receipt_sha256="b" * 64,
        lower=0.30,
        upper=0.40,
        absolute_tolerance=0.05,
    )


def _rate(failures: int, shots: int) -> object:
    return _exact_binomial_rate(
        failures=failures, shots=shots, alpha=0.05, count_receipt_sha256=_HASH,
    )


def test_target_decision_uses_containment_disjointness_and_overlap() -> None:
    target = _target()
    passed = _target_interval_decision(
        _rate(35, 100), target, input_receipt_hashes={"target": "b" * 64},
    )
    failed = _target_interval_decision(
        _rate(0, 100), target, input_receipt_hashes={"target": "b" * 64},
    )
    inconclusive = _target_interval_decision(
        _rate(25, 100), target, input_receipt_hashes={"target": "b" * 64},
    )
    assert passed.verdict == "pass"
    assert failed.verdict == "fail"
    assert inconclusive.verdict == "inconclusive"
    assert passed.acceptable_interval == pytest.approx((0.25, 0.45))
    assert passed.rule_id == "target_interval_containment_v1"


def test_target_decision_clips_to_probability_domain_and_requires_source_n_when_declared() -> None:
    target = TargetReferenceV1(
        target_id="edge",
        target_receipt_sha256="b" * 64,
        lower=0.0,
        upper=0.02,
        absolute_tolerance=0.10,
    )
    result = _target_interval_decision(
        _rate(0, 100),
        target,
        input_receipt_hashes={"target": "b" * 64},
        source_denominator_required=True,
        source_denominator=None,
    )
    assert result.acceptable_interval == (0.0, 0.12)
    assert result.verdict == "inconclusive"
    assert result.reason == "missing_required_source_denominator"
    assert math.isfinite(result.computed_interval[1])
