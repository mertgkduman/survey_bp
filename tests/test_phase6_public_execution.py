"""Closed MBBP-LD public contract and truth-free structural projection."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


def _v7() -> dict[str, object]:
    value = json.loads(Path("data/manifests/canonical-three-qubit-development.json").read_text())
    value["schema_version"] = 7
    value["numerical_profile"] = "cpu-float64-min-sum-v1"
    policies = value["policies"]
    assert isinstance(policies, dict)
    policies["update"].update({"kind": "normalized_min_sum", "parameter_assignment": {"shape": "scalar", "value": 0.875}})
    policies["schedule"].update({"kind": "check_node_serial"})
    policies["state_memory"].update({"kind": "identity"})
    value["ensemble"] = {
        "kind": "mbbp_ld", "source_status": "canonical_adaptation", "member_state": "independent",
        "max_iterations": 8, "max_member_c2v_updates": 100, "max_total_members": 1,
        "no_member_terminal": "no_member_converged_zero_return",
        "bases": [{"member_id": "member-0", "local_ordinal": 0, "partition_identity": "p0",
                    "permutation_identity": "q0", "transform_kind": "one_hot_original_check_rows",
                    "redundant_transforms": [[1]]}],
    }
    value["list_selection"] = {"kind": "frequency_over_weight_plus_one", "tie_rule": "local_ordinal_then_lineage"}
    return value


def test_phase6_schema_requires_closed_mbbp_controls():
    from bp_registry.manifests import CanonicalExperimentV7, parse_manifest

    value = _v7()
    parsed = parse_manifest(value)
    assert isinstance(parsed, CanonicalExperimentV7)
    assert parsed.ensemble.no_member_terminal == "no_member_converged_zero_return"
    bad = _v7()
    bad["ensemble"]["bases"][0]["redundant_transforms"] = [[1, 1]]
    with pytest.raises(ValueError, match="one-hot"):
        parse_manifest(bad)
    bad = _v7()
    bad["policies"]["schedule"]["kind"] = "flooding"
    with pytest.raises(ValueError, match="MBBP-LD"):
        parse_manifest(bad)


def test_phase6_projection_preserves_no_member_zero_return_without_selection():
    from bp_registry.canonical.mbbp import MbbpBasis, MbbpController, MbbpSpec
    from bp_registry.canonical.phase6 import phase6_events
    from bp_registry.canonical.problems import OriginalProblem

    original = OriginalProblem("original-test", np.array([[1, 0]], dtype=np.uint8),
                               np.array([[1, 0]], dtype=np.uint8), np.array([1], dtype=np.uint8))
    basis = MbbpBasis("member-0", 0, "p0", "q0", ((1,),))
    # A zero member cap denies every local step and exercises the source sentinel.
    result = MbbpController(MbbpSpec((basis,), max_iterations=1, max_member_c2v_updates=0)).run(original, error_rate=0.1)
    projection = phase6_events(original, bases=(basis,), result=result)
    kinds = [kind for kind, _payload in projection.events]
    assert projection.terminal == "no_member_converged_zero_return"
    assert "selection" not in kinds and "original_check" not in kinds and "evaluation" not in kinds
    terminal = projection.events[-1][1]
    assert terminal["source_zero_return"] == [0, 0]
    assert terminal["selection"] is None


def test_phase6_member_projection_preserves_historical_payload_grammar():
    """Phase 7-only reliability must not rewrite sealed V7 member events."""
    from bp_registry.canonical.mbbp import MbbpBasis, MbbpController, MbbpSpec
    from bp_registry.canonical.phase6 import phase6_events
    from bp_registry.canonical.problems import OriginalProblem

    original = OriginalProblem("original-phase6-payload", np.array([[1, 0]], dtype=np.uint8),
                               np.array([[1, 0]], dtype=np.uint8), np.array([1], dtype=np.uint8))
    basis = MbbpBasis("member-0", 0, "p0", "q0", ((1,),))
    result = MbbpController(MbbpSpec((basis,), max_iterations=1, max_member_c2v_updates=0)).run(
        original, error_rate=0.1,
    )

    member = next(payload for kind, payload in phase6_events(original, bases=(basis,), result=result).events
                  if kind == "member")

    assert set(member) == {
        "member_id", "local_ordinal", "lineage_id", "basis_identity", "initial_state_identity",
        "schedule", "normalized_min_sum_alpha", "status", "candidate", "original_valid", "admitted", "work",
    }
    assert result.members[0].terminal_posterior is None


def test_phase6_historical_schema_six_retains_its_dispatch():
    from bp_registry.manifests import parse_manifest

    value = _v7()
    value["schema_version"] = 6
    value.pop("ensemble")
    value.pop("list_selection")
    value["numerical_profile"] = "cpu-float64-spa-v1"
    with pytest.raises(ValueError):
        # This has V7 policies, but parsing remains V6 rather than being
        # accidentally admitted as an ensemble schema.
        parse_manifest(value)


def test_phase6_public_execution_replays_and_rejects_tampered_member(tmp_path):
    from bp_registry.canonical.execution import run_phase6_structural_shot
    from bp_registry.canonical.verification import PublicShotContext, validate_canonical_shot
    from bp_registry.css import fixture_code
    from bp_registry.ledger import read_canonical_events
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    value = _v7()
    value["ensemble"]["max_member_c2v_updates"] = 0
    code = fixture_code()
    syndrome = np.zeros(code.hz.shape[0], dtype=np.uint8)
    context = PublicShotContext(
        manifest_sha256="a" * 64, artifact_raw_sha256="b" * 64, artifact_semantic_sha256="c" * 64,
        compact_manifest=value, sample_seed_identity="seed", run_id=value["run_id"], shot_id=0,
        check_type="Z", syndrome=tuple(int(bit) for bit in syndrome), code_id="fixture",
        evidence_relation="canonical_implemented", fixture="development_fixture", assessment_status="not_assessed",
        decoder_seed_identity="decoder", code=code, hidden_truth=HiddenTruth(np.zeros(code.n, dtype=np.uint8), np.zeros(code.n, dtype=np.uint8)),
        error_rate=float(value["error_rate"]), max_iterations=3,
    )
    path = tmp_path / "events.jsonl"
    outcome = run_phase6_structural_shot(value, code=code, observation=DecoderObservation("Z", syndrome),
                                         hidden_truth=context.hidden_truth, shot_id=0, ledger_path=path,
                                         sample_seed_identity="seed", context={}, verification_context=context)
    events = read_canonical_events(path)
    assert outcome.termination == "no_member_converged_zero_return"
    validate_canonical_shot(events, context)
    member = next(event for event in events if event["kind"] == "member")
    member["data"]["payload"]["status"] = "iteration_cap"
    with pytest.raises(ValueError, match="differs"):
        validate_canonical_shot(events, context)
