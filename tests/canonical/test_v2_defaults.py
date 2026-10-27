"""Promoted defaults and versioned public replay boundaries."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2, REFERENCE_CPU_F64
from bp_registry.cli import run_canonical, verify_run
from bp_registry.manifests import (
    CanonicalExperimentV9, QuaternaryExperimentV2, QuaternaryExperimentV3,
    parse_manifest,
)
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import QBP4_F64_V1, QBP4_F64_V2
from bp_registry.runner import preflight_canonical, preflight_quaternary, run_quaternary, verify_quaternary_run


ROOT = Path(__file__).resolve().parents[2]


def test_unversioned_plain_constructors_select_v2_and_explicit_v1_is_stable() -> None:
    h = np.asarray([[1, 1]], dtype=np.uint8)
    assert BinarySpaKernel().profile is BINARY_SPA_F64_V2
    assert CompiledBinaryFlooding.from_check_matrix(h).profile is BINARY_SPA_F64_V2
    assert ScalarLlrBp4Kernel().profile is QBP4_F64_V2
    assert BinarySpaKernel(profile=REFERENCE_CPU_F64).profile is REFERENCE_CPU_F64
    assert CompiledBinaryFlooding.from_check_matrix(h, profile=REFERENCE_CPU_F64).profile is REFERENCE_CPU_F64
    assert ScalarLlrBp4Kernel(profile=QBP4_F64_V1).profile is QBP4_F64_V1
    assert CompiledBp4Graph.__dataclass_fields__["profile"].default is QBP4_F64_V2


def test_public_binary_v9_defaults_to_v2_and_historical_v2_stays_v1(tmp_path: Path) -> None:
    historical = json.loads((ROOT / "data/manifests/canonical-three-qubit-development.json").read_text())
    assert preflight_canonical(ROOT / "data/manifests/canonical-three-qubit-development.json")[
        "resolved_numerical_profile"
    ]["profile_id"] == REFERENCE_CPU_F64.profile_id
    promoted = dict(historical)
    promoted["schema_version"] = 9
    promoted["run_id"] = "canonical-v2-default-test"
    del promoted["numerical_profile"]
    parsed = parse_manifest(promoted)
    assert isinstance(parsed, CanonicalExperimentV9)
    assert parsed.numerical_profile == "cpu-float64-spa-v2"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(promoted), encoding="utf-8")
    assert preflight_canonical(path)["resolved_numerical_profile"]["profile_id"] == BINARY_SPA_F64_V2.profile_id
    assert run_canonical(path, tmp_path / "result")["final_row_count"] == 2
    assert verify_run(tmp_path / "result")["final_row_count"] == 2
    bad = dict(promoted)
    bad["numerical_profile"] = "cpu-float64-spa-v1"
    with pytest.raises(ValueError):
        parse_manifest(bad)


def test_public_quaternary_v3_defaults_to_v2_and_v2_keeps_its_identity(tmp_path: Path) -> None:
    base = json.loads((ROOT / "data/manifests/quaternary-five-qubit-tracer.json").read_text())
    base["schema_version"] = "quaternary_experiment_v2"
    base["composition"] = {
        "kernel": {"kind": "qbp_scalar_llr", "binding_id": "kernel"},
        "schedule": {"kind": "qbp_flooding", "binding_id": "schedule"},
        "transforms": [],
        "intervention": {"kind": "identity", "binding_id": "intervention"},
    }
    base["shot_budget"] = 1
    assert isinstance(parse_manifest(base), QuaternaryExperimentV2)
    promoted = dict(base)
    promoted["schema_version"] = "quaternary_experiment_v3"
    parsed = parse_manifest(promoted)
    assert isinstance(parsed, QuaternaryExperimentV3)
    assert parsed.numerical_profile == QBP4_F64_V2.profile_id
    path = tmp_path / "q.json"
    path.write_text(json.dumps(promoted), encoding="utf-8")
    preflight = preflight_quaternary(path)
    assert preflight["numerical_profile"] == QBP4_F64_V2.profile_id
    assert preflight["composition"]["run_fidelity"] == "canonical_adaptation"
    assert preflight["composition"]["component_fidelity"]["kernel"] == "canonical_adaptation"
    assert run_quaternary(path, tmp_path / "result")["final_row_count"] == 1
    assert verify_quaternary_run(tmp_path / "result")["verified"] is True
    bad = dict(promoted)
    bad["composition"] = {**promoted["composition"], "schedule": {"kind": "qbp_variable_serial", "binding_id": "schedule"}}
    with pytest.raises(ValueError):
        parse_manifest(bad)
    transformed = dict(promoted)
    transformed["composition"] = {**promoted["composition"], "transforms": [
        {"kind": "qbp_c2v_normalization", "binding_id": "normalization", "config": {"alpha_c": 2.0}},
    ]}
    with pytest.raises(ValueError):
        parse_manifest(transformed)
