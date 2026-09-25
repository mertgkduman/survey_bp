"""Contract tests for the isolated active-memory v4 benchmark builder."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _module():
    spec = importlib.util.spec_from_file_location("phase4_active_benchmark", Path("scripts/run_phase4_active_benchmark.py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_active_manifest_is_a_controlled_31_leg_memory_contract():
    runner = _module()
    base = json.loads(Path("data/manifests/phase4-memory-relay-b1.json").read_text(encoding="utf-8"))
    manifest = runner.build_active_manifest(
        base, arm="canonical_relay_31", preset="canonical_default", error_rate=.07,
        first_leg_gamma=.125, later_center=.25, later_width=1.25, seed_identity="active-v4-seed",
    )
    relay = manifest["relay"]
    assert relay["fidelity_status"] == "controlled_component_adaptation"
    assert relay["later_leg_memory"] == "disordered"
    assert relay["total_leg_limit"] == 31
    assert relay["legs"][0]["max_iterations"] == 80
    assert all(leg["max_iterations"] == 60 for leg in relay["legs"][1:])
    assert relay["memory_tuning"] == {
        "semantics": "relay_v022_dynamic_affine_prior_css_adaptation", "first_leg_gamma": .125,
        "later_center": .25, "later_width": 1.25, "seed_identity": "active-v4-seed",
        "rng_algorithm": "numpy.PCG64", "refresh": "per_later_leg",
    }
    assert manifest["randomness"]["physical_sample_identity"].endswith("active-v4-p0070")
    assert manifest["memory"]["bindings"][0]["parameters"]["alpha"] == .125
    assert manifest["budgets"]["max_shots"] == 32
    for scope in ("shot", "search", "attempt"):
        assert manifest["budgets"][scope]["max_iterations"] == 80
        assert manifest["budgets"][scope]["work_limits"]["bp_calls"] == 31


def test_active_scan_trigger_is_fixed_before_scan_outcomes():
    plan = _module().active_scan_plan()
    assert plan["codes"]["gross-bb-144"]["rates"] == [.03, .05, .07]
    assert plan["codes"]["hgp-gallager-3-4-seed-20260923"]["rates"] == [.03]
    assert "32" in plan["trigger"]["advance_when"]
    assert plan["no_outcome_dependent_retries"] is True


def test_b1_bounded_profile_is_explicit_and_not_a_short_base_budget():
    runner = _module()
    base = json.loads(Path("data/manifests/phase4-memory-relay-b1.json").read_text(encoding="utf-8"))
    manifest = runner.build_active_manifest(base, arm="canonical_relay_31", preset="source_procedure", error_rate=.07,
                                             first_leg_gamma=.125, later_center=.25, later_width=1.25,
                                             seed_identity="active-v4-seed", work_profile="b1_three_leg")
    assert manifest["budgets"]["max_shots"] == 32
    assert manifest["budgets"]["shot"]["work_limits"]["bp_calls"] == 3
    assert manifest["budgets"]["shot"]["work_limits"]["check_to_variable_updates"] == 529200
    assert manifest["policies"]["update"]["kind"] == "min_sum"
    assert manifest["policies"]["update"]["binding_id"] == "update-min-sum-v1"
    assert manifest["numerical_profile"] == manifest["relay"]["numerical_profile"] == "cpu-float64-min-sum-v1"


def test_active_fact_extractor_requires_gamma_or_memory_evidence():
    runner = _module()
    events = [
        {"kind": "work", "shot_id": 0, "data": {"relay_work_leaves": []}},
        {"kind": "work", "shot_id": 0, "data": {"relay_memory_mode": "dynamic_affine_prior_each_source_iteration", "relay_legs": [{"memory": {"applied_each_source_iteration": True}}]}},
    ]
    fact = runner._attempt_from_events(events, 0)
    assert fact["active_memory_facts"]
    assert fact["distinct_leg_indices"] == []
    assert runner._active_memory_proven({**fact, "distinct_leg_indices": [0]}) is True
    assert runner._active_memory_proven({**fact, "distinct_leg_indices": [0, 1]}) is False
