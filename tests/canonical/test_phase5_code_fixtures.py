"""Fixed BB-144 and generated-HGP intervention fixtures; no sampled shots."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry.canonical.budgets import BudgetTree, WorkVector
from bp_registry.canonical.contracts import Phase5InterventionContract
from bp_registry.canonical.lineage import stable_lineage_id
from bp_registry.canonical.phase5 import execute_phase5_controller
from bp_registry.canonical.problems import OriginalProblem
from bp_registry.canonical.restarting import RestartSpec
from bp_registry.manifests import preflight


ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "bb144": {
        "manifest": "phase3-pilot-bb144.json", "n": 144, "checks": 72,
        "fixed_errors": 12, "syndrome_hex": "3f00fc000000000000",
        "raw": "2c02a3b99bf7267acf35efe28e0a2ef0d3827e5a22b948d53da14ae8df68ceb0",
        "guided_target": 24, "freeze_target": 77, "sign_target": 72,
    },
    "hgp": {
        "manifest": "phase3-pilot-hgp-gallager.json", "n": 225, "checks": 108,
        "fixed_errors": 16, "syndrome_hex": "ffff0000f0ff0f0000ffff000000",
        "raw": "b31c99a754fb377acfb5e2cb2edc2cb7e55c4d1e78feb4aa84c171c051a78c44",
        "guided_target": 162, "freeze_target": 12, "sign_target": 0,
    },
}


def _gf2_product(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """Independent row parity, separate from production transform and controller code."""
    return np.asarray([
        sum(int(bit) & int(value) for bit, value in zip(row, vector, strict=True)) % 2
        for row in matrix
    ], dtype=np.uint8)


def _fixed_case(label: str):
    info = CASES[label]
    manifest_path = ROOT / "data/manifests" / info["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    resolved = preflight(manifest_path)
    artifact = manifest["artifact"]
    artifact_path = ROOT / artifact["root"] / artifact["path"]
    actual_raw = sha256(artifact_path.read_bytes()).hexdigest()
    assert actual_raw == artifact["raw_sha256"]
    if info["raw"]:
        assert actual_raw == info["raw"]
    resolved.code.validate()
    hz = resolved.code.hz
    assert hz.shape == (info["checks"], info["n"])
    assert resolved.code.hx.shape[1] == info["n"]
    assert resolved.code.lx.shape[1] == info["n"]
    assert resolved.code.lz.shape[1] == info["n"]
    if label == "hgp":
        metadata = json.loads((ROOT / "data/artifacts/hgp-gallager-3-4-seed-20260923.json").read_text())
        assert metadata["generator"]["seed"] == 20260923
        assert metadata["constituent"]["shape"] == [9, 12]
        assert metadata["code"]["n"] == 225
        assert metadata["code"]["k_gf2"] == 29
        assert metadata["artifact"]["raw_sha256"] == actual_raw
    error = np.zeros(info["n"], dtype=np.uint8)
    error[:info["fixed_errors"]] = 1
    syndrome = np.unpackbits(np.frombuffer(bytes.fromhex(info["syndrome_hex"]), dtype=np.uint8), bitorder="little")[:info["checks"]]
    assert np.array_equal(_gf2_product(hz, error), syndrome)
    original = OriginalProblem(
        stable_lineage_id("original", {"fixed_code_fixture": label}).value,
        resolved.code.hx, hz, syndrome,
    )
    return info, original, error


@pytest.mark.parametrize("label", ["bb144", "hgp"])
def test_phase5_bb144_hgp_algebra_fixed_shortening_and_lift(label):
    info, original, error = _fixed_case(label)
    hz = original.hz
    fixed = (0, 1)
    assignment = (1, 1)
    free = tuple(index for index in range(info["n"]) if index not in fixed)
    shortened = hz[:, free]
    residual = original.syndrome ^ _gf2_product(hz[:, fixed], np.asarray(assignment, dtype=np.uint8))
    working_candidate = error[list(free)]
    assert np.array_equal(_gf2_product(shortened, working_candidate), residual)
    lifted = np.zeros(info["n"], dtype=np.uint8)
    lifted[list(free)] = working_candidate
    lifted[list(fixed)] = assignment
    assert np.array_equal(lifted, error)
    assert np.array_equal(_gf2_product(hz, lifted), original.syndrome)
    assert not np.array_equal(_gf2_product(hz, np.zeros(info["n"], dtype=np.uint8)), original.syndrome)


def _spec(kind: str) -> Phase5InterventionContract:
    design = json.loads((ROOT / "data/manifests/phase5-b1-calibration.json").read_text(encoding="utf-8"))
    declaration = dict(design["arm_manifests"][kind]["intervention"])
    # Fixed code fixtures keep their own decoder stream when the sampled B1
    # pilot advances to a fresh calibration namespace.
    if declaration.get("root_seed") is not None:
        declaration["root_seed"] = "phase5-b1-calibration-decoder-v1"
    for field in (
        "sweeps_per_round", "baseline_sweeps", "attempt_sweeps", "period_sweeps",
        "lifetime_sweeps", "trunk_sweeps", "continuation_sweeps",
    ):
        if field in declaration:
            declaration[field] = 2 if kind == "syndrome_flip" and field == "baseline_sweeps" else 1
    for field in ("round_limit", "attempt_cap", "retry_cap", "test_cap"):
        if field in declaration:
            declaration[field] = 1
    return Phase5InterventionContract.model_validate(declaration)


@pytest.mark.parametrize("label", ["bb144", "hgp"])
@pytest.mark.parametrize("kind", ["guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip"])
def test_phase5_bb144_hgp_bpgd_impulse_freezing_syndrome_flip_sign_flip_fixed_policy(label, kind):
    info, original, _error = _fixed_case(label)
    spec = _spec(kind)
    budget = BudgetTree(limits=(), parents={"search": "shot", "attempt": "search"})
    result = execute_phase5_controller(
        spec, original, error_rate=0.07, budgets=budget,
        max_iterations=2, owner_identity=f"fixture-{label}-{kind}",
    )
    assert result.qualification == spec.qualification
    assert result.work == WorkVector.sum(delta for _leaf, _scope, delta in result.leaves)
    assert len({leaf for leaf, _scope, _delta in result.leaves}) == len(result.leaves)
    assert all(scope == "attempt" for _leaf, scope, _delta in result.leaves)
    assert result.work.original_checks >= 1
    if result.candidate is not None:
        assert np.array_equal(_gf2_product(original.hz, np.asarray(result.candidate)), original.syndrome)
    if kind == "guided_decimation":
        assert result.attempts[0]["selected_target"] == info["guided_target"]
        assert result.attempts[0]["state_after"] != result.attempts[0]["state_before"]
        assert result.work.fixation_actions == 1
        assert result.work.ranking_scans == info["n"]
    elif kind == "impulse":
        assert result.attempts[0]["target_index"] == 0
        assert result.attempts[0]["initial_iteration"] == 0
        assert result.attempts[0]["working_lineage_id"].startswith("working-")
        assert result.work.transformations == 1
        assert result.work.lifted_coordinates == info["n"]
    elif kind == "freezing":
        assert result.attempts[0]["target_index"] == info["freeze_target"]
        assert result.attempts[0]["reset_rule"] == "fresh_structural_branch_then_release_to_original"
        assert result.work.transformations == 2
    elif kind == "syndrome_flip":
        assert result.attempts[0]["test_vector"].count(1) == 1
        assert result.attempts[0]["working_lineage_id"].startswith("working-")
        assert result.work.order_generation == 1
        assert result.work.lifted_coordinates == info["n"]
    else:
        assert result.header["target_index"] == info["sign_target"]
        assert result.header["v2c_before"] == result.header["v2c_after_action"]
        assert result.header["c2v_before"] == result.header["c2v_after_action"]
        assert result.work.intervention_actions == 1


@pytest.mark.parametrize("label", ["bb144", "hgp"])
def test_phase5_bb144_hgp_restart_unavailable_without_exact_distance(label):
    info, original, _error = _fixed_case(label)
    with pytest.raises(ValueError, match="distance"):
        RestartSpec(
            preset="source_exact_distance", code_id=label, eta=1, t_cap=1,
            root_sweeps=1, residual_sweeps=1, exact_distance=None,
        )
    with pytest.raises(ValueError, match="B1 mechanism"):
        RestartSpec(
            preset="b1_tcap8_mechanism", code_id=label, eta=1, t_cap=8,
            root_sweeps=1, residual_sweeps=1,
        )
    assert original.hz.shape[1] == info["n"]


def test_phase5_hgp_fixed_policy_repeats_byte_equivalent():
    _info, original, _error = _fixed_case("hgp")
    spec = _spec("syndrome_flip")
    def evidence():
        outcome = execute_phase5_controller(
            spec, original, error_rate=0.07,
            budgets=BudgetTree(limits=(), parents={"search": "shot", "attempt": "search"}),
            max_iterations=2, owner_identity="fixture-hgp-syndrome_flip",
        )
        return json.dumps({"header": outcome.header, "attempts": outcome.attempts,
                           "work": outcome.work.as_evidence(structural_event_version=4)},
                          sort_keys=True, separators=(",", ":"))
    assert evidence() == evidence()
