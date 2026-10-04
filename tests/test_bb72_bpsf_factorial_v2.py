"""Frozen BB72 BP-SF factorial geometry and compatible public manifests."""

from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.run_bb72_bpsf_factorial_v2 import (
    _contrast, _holm, arms, configurations, design, make_manifest,
)


def test_factorial_grid_and_matched_new_sample_namespace():
    spec = design()
    configs = configurations(spec)
    assert len(configs) == 12
    assert len(arms(spec)) == 24
    assert {row["update"] for row in configs} == {"binary_spa", "min_sum"}
    assert {row["mode"] for row in configs} == {"bp20", "bp40", "bpsf20plus4x5"}
    assert spec["cohort"]["physical_sample_identity_prefix"] != "bb72-css-bp-v1-evaluation"
    assert spec["cohort"]["sample_seed"] != 720302


def test_public_arms_keep_kernel_damping_and_work_explicit(monkeypatch):
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    spec = design()
    configs = {row["id"]: row for row in configurations(spec)}
    rate = .08
    bp20 = make_manifest(spec, configs["ms-g0500-bp20"], rate)
    bp40 = make_manifest(spec, configs["ms-g0500-bp40"], rate)
    bpsf = make_manifest(spec, configs["ms-g0500-bpsf20plus4x5"], rate)
    assert {row["randomness"]["physical_sample_identity"] for row in (bp20, bp40, bpsf)} == {
        "bb72-bpsf-factorial-v2-evaluation-p080"
    }
    assert {row["budgets"]["max_shots"] for row in (bp20, bp40, bpsf)} == {1280}
    assert [row["budgets"]["attempt"]["max_iterations"] for row in (bp20, bp40, bpsf)] == [20, 40, 40]
    assert bpsf["policies"]["update"]["kind"] == "min_sum"
    assert bpsf["numerical_profile"] == "cpu-float64-min-sum-v1"
    assert bpsf["intervention"]["baseline_sweeps"] == 20
    assert bpsf["intervention"]["attempt_sweeps"] == 5
    assert bpsf["intervention"]["test_cap"] == 4
    assert bpsf["memory"]["bindings"][0]["parameters"]["gamma"] == .5
    assert all(row["budgets"]["attempt"]["work_limits"]["check_to_variable_updates"] == 8640
               for row in (bp20, bp40, bpsf))


def test_primary_paired_contrast_and_holm_are_two_sided():
    def shot(identity, outcome):
        return {"sample_identity": identity, "outcome": outcome}
    reference = {i: shot(f"sample-{i}", "exact" if i < 6 else None) for i in range(10)}
    other = {i: shot(f"sample-{i}", "exact" if i < 8 else None) for i in range(10)}
    result = _contrast(reference, other)
    assert (result["newly_valid"], result["lost_valid"], result["failure_rate_difference"]) == (2, 0, -.2)
    assert _holm({"a": .02, "b": .04}) == {"a": .04, "b": .04}
    changed = deepcopy(other)
    changed[0]["sample_identity"] = "different"
    with pytest.raises(ValueError, match="unmatched"):
        _contrast(reference, changed)
