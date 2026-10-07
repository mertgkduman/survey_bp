"""Public contract for the Phase 10 joint-Pauli tracer."""

from __future__ import annotations

import inspect
import importlib.util
import json
from pathlib import Path

import pytest

from bp_registry.manifests import QuaternaryExperimentV1, parse_manifest, preflight
from bp_registry.quaternary.execution import PauliValue, TracerPauliProblem, run_quaternary_tracer, syndrome_for, verify_quaternary_tracer
from bp_registry.runner import preflight_quaternary, run_quaternary, verify_quaternary_run


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "data/manifests/quaternary-five-qubit-tracer.json"


def test_tracer_public_facade_exists():
    """The installed package must expose a dedicated joint-Pauli tracer."""
    root = Path(__file__).resolve().parents[3]
    assert (root / "src/bp_registry/quaternary/execution.py").is_file()


def manifest_value() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_tracer_non_css_installed_cli_path_preflights_runs_and_replays(tmp_path):
    report = preflight_quaternary(FIXTURE)
    assert report["pauli_encoding"] == "I=0,X=1,Y=2,Z=3"
    result = run_quaternary(FIXTURE, tmp_path)
    assert result["assessment_status"] == "not_assessed"
    assert "performance result" in result["statistical_claim"]
    assert verify_quaternary_run(tmp_path)["verified"] is True


def test_tracer_preserves_non_css_original_checks_and_joint_y_syndrome(tmp_path):
    manifest = parse_manifest(FIXTURE)
    assert isinstance(manifest, QuaternaryExperimentV1)
    problem = TracerPauliProblem(manifest.problem.checks, manifest.problem.syndrome)
    candidate = [PauliValue.I, PauliValue.I, PauliValue.I, PauliValue.Y, PauliValue.I]
    assert syndrome_for(problem, candidate).tolist() == [1, 1, 1, 1]
    before = problem.checks.tobytes(), problem.syndrome.tobytes()
    run_quaternary_tracer(manifest, tmp_path)
    assert (problem.checks.tobytes(), problem.syndrome.tobytes()) == before
    assert not problem.checks.flags.writeable and not problem.syndrome.flags.writeable


def test_tracer_kernel_is_truth_sealed_and_records_smoothing_separately(tmp_path):
    from bp_registry.quaternary import execution

    assert "hidden" not in inspect.signature(execution._decode).parameters
    run_quaternary_tracer(parse_manifest(FIXTURE), tmp_path)
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert events[1]["data"]["hidden_truth_sealed"] is True
    assert events[2]["data"]["decoder_smoothing"] == pytest.approx(1e-12)
    assert events[1]["data"]["sampling"] == "one_categorical_I_X_Y_Z_value_per_qubit"


@pytest.mark.parametrize("field,value", [
    ("problem", None),
    ("channel", None),
])
def test_tracer_rejects_null_public_inputs(field, value):
    data = manifest_value(); data[field] = value
    with pytest.raises(Exception):
        parse_manifest(data)


def test_tracer_rejects_empty_invalid_and_mismatched_public_inputs():
    data = manifest_value(); data["problem"]["checks"] = []
    with pytest.raises(Exception, match="at least|nonempty"):
        parse_manifest(data)
    data = manifest_value(); data["problem"]["checks"][0][0] = 4
    with pytest.raises(Exception, match="I=0"):
        parse_manifest(data)
    data = manifest_value(); data["problem"]["syndrome"] = [0]
    with pytest.raises(Exception, match="syndrome"):
        parse_manifest(data)


def test_tracer_admits_one_qubit_explicit_encoding(tmp_path):
    data = manifest_value()
    data.update(run_id="one-qubit-qbp", problem={"checks": [[int(PauliValue.Z)]], "syndrome": [0]}, channel={"probabilities": [[1.0, 0.0, 0.0, 0.0]], "decoder_smoothing": 1e-12})
    manifest = parse_manifest(data)
    assert isinstance(manifest, QuaternaryExperimentV1)
    result = run_quaternary_tracer(manifest, tmp_path)
    assert result.candidate.tolist() == [PauliValue.I]


def test_tracer_replay_rejects_semantic_tampering(tmp_path):
    manifest = parse_manifest(FIXTURE)
    run_quaternary_tracer(manifest, tmp_path)
    path = tmp_path / "events.jsonl"
    path.write_text(path.read_text().replace('"not_assessed"', '"assessed"', 1), encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        verify_quaternary_tracer(manifest, tmp_path)


def _composition(*, schedule: str = "qbp_flooding", transforms=(), intervention: str = "identity", **intervention_config):
    from bp_registry.quaternary.contracts import QuaternaryCompositionSpec, QuaternaryPolicySpec

    return QuaternaryCompositionSpec(
        kernel=QuaternaryPolicySpec(kind="qbp_scalar_llr", binding_id="kernel"),
        schedule=QuaternaryPolicySpec(kind=schedule, binding_id="schedule"),
        transforms=tuple(
            QuaternaryPolicySpec(kind=kind, binding_id=f"transform-{index}")
            for index, kind in enumerate(transforms)
        ),
        intervention=QuaternaryPolicySpec(kind=intervention, binding_id="intervention", config=intervention_config),
    )


def test_compatibility_resolves_qualified_baseline_with_complete_evidence():
    assert importlib.util.find_spec("bp_registry.quaternary.compatibility") is not None
    from bp_registry.quaternary.compatibility import resolve_quaternary_composition

    resolved = resolve_quaternary_composition(
        _composition(transforms=("qbp_c2v_normalization",)), problem_kind="general_pauli"
    )

    assert resolved.run_fidelity == "source_backed"
    assert resolved.component_fidelity["kernel"] == "source_backed"
    assert resolved.effective_order == (
        "qbp_scalar_llr", "qbp_flooding", "qbp_c2v_normalization", "identity",
    )
    assert resolved.lifecycle["schedule_freshness"] == "complete_old_v2c_snapshot_then_complete_commit"
    assert "scalar_commutation_c2v" in resolved.equations


def test_compatibility_distinguishes_component_and_run_fidelity_for_qbpgd():
    from bp_registry.quaternary.compatibility import resolve_quaternary_composition

    resolved = resolve_quaternary_composition(
        _composition(intervention="qbpgd", continued_messages=True, prior_profile="depolarizing")
    )

    assert resolved.component_fidelity["intervention"] == "source_backed"
    assert resolved.run_fidelity == "canonical_adaptation"
    assert "continued_message_buffers" in resolved.adaptation_reasons
    assert resolved.procedure_basis == "canonical_qbpgd_interpretation_v1"


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"schedule": "layered"}, "unsupported binary"),
        ({"transforms": ("normalized_min_sum",)}, "unsupported binary"),
        ({"intervention": "ambp4"}, "AMBP4"),
        ({"intervention": "asced", "css_only": False}, "non-CSS aSCED"),
    ],
)
def test_compatibility_rejects_unqualified_ports(kwargs, match):
    from bp_registry.quaternary.compatibility import resolve_quaternary_composition

    with pytest.raises(ValueError, match=match):
        resolve_quaternary_composition(_composition(**kwargs), problem_kind="general_pauli")


def test_compatibility_rejects_empty_or_unowned_compositions():
    from bp_registry.quaternary.compatibility import resolve_quaternary_composition
    from bp_registry.quaternary.contracts import QuaternaryCompositionSpec, QuaternaryPolicySpec

    with pytest.raises(ValueError, match="requires kernel"):
        QuaternaryCompositionSpec(
            kernel=None,
            schedule=QuaternaryPolicySpec(kind="qbp_flooding", binding_id="schedule"),
        )
    with pytest.raises(ValueError, match="owns state"):
        resolve_quaternary_composition(
            _composition(intervention="qbpgd", continued_messages=True, prior_profile="depolarizing").model_copy(
                update={"intervention": QuaternaryPolicySpec(kind="qbpgd", binding_id="intervention")}
            )
        )


def _public_v2_manifest() -> dict:
    data = manifest_value()
    data["schema_version"] = "quaternary_experiment_v2"
    data["composition"] = {
        "kernel": {"kind": "qbp_scalar_llr", "binding_id": "kernel"},
        "schedule": {"kind": "qbp_flooding", "binding_id": "schedule"},
        "transforms": [],
        "intervention": {"kind": "identity", "binding_id": "intervention"},
    }
    data["shot_budget"] = 1
    return data


def test_full_public_manifest_resolves_before_sampling_and_replays(tmp_path):
    import bp_registry.manifests as public_manifests

    assert hasattr(public_manifests, "QuaternaryExperimentV2")
    from bp_registry.manifests import QuaternaryExperimentV2

    manifest = parse_manifest(_public_v2_manifest())
    assert isinstance(manifest, QuaternaryExperimentV2)
    report = preflight_quaternary(_public_v2_manifest())
    assert report["composition"]["run_fidelity"] == "source_backed"

    result = run_quaternary(_public_v2_manifest(), tmp_path)
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert result["assessment_status"] == "not_assessed"
    assert events[0]["data"]["resolved_composition"]["run_fidelity"] == "source_backed"
    assert events[-1]["data"]["assessment_status"] == "not_assessed"
    assert verify_quaternary_run(tmp_path)["verified"] is True


def test_full_public_replay_rejects_resolved_identity_and_event_order_tampering(tmp_path):
    run_quaternary(_public_v2_manifest(), tmp_path)
    path = tmp_path / "events.jsonl"
    events = path.read_text(encoding="utf-8").splitlines()
    events[0] = events[0].replace("source_backed", "canonical_adaptation", 1)
    path.write_text("\n".join(events) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        verify_quaternary_run(tmp_path)


def _qbpgd_public_manifest(*, prior_profile: str = "depolarizing") -> dict:
    data = _public_v2_manifest()
    data["composition"]["intervention"] = {
        "kind": "qbpgd", "binding_id": "qbpgd",
        "config": {
            "continued_messages": True, "prior_profile": prior_profile,
            "iterations_per_round": 1, "epsilon": 0.01,
        },
    }
    return data


def test_qbpgd_public_run_keeps_source_component_fidelity_separate_from_adapted_trajectory(tmp_path):
    manifest = _qbpgd_public_manifest()
    report = preflight_quaternary(manifest)
    assert report["composition"]["component_fidelity"]["intervention"] == "source_backed"
    assert report["composition"]["run_fidelity"] == "canonical_adaptation"
    result = run_quaternary(manifest, tmp_path)
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert result["run_fidelity"] == "canonical_adaptation"
    assert result["component_fidelity"]["depolarizing_setup"] == "source_backed"
    assert result["source_author_code_identity"] == "unverified"
    assert any(event["kind"] == "qbpgd_round" for event in events)
    assert events[0]["data"]["resolved_composition"]["run_fidelity"] == "canonical_adaptation"
    assert verify_quaternary_run(tmp_path)["verified"] is True


def test_qbpgd_general_prior_is_a_distinct_adaptation_reason(tmp_path):
    result = run_quaternary(_qbpgd_public_manifest(prior_profile="general_joint"), tmp_path)
    assert result["run_fidelity"] == "canonical_adaptation"
    assert "general_joint_prior" in result["adaptation_reasons"]
    assert "continued_message_buffers" in result["adaptation_reasons"]


def _mbp4_public_manifest(*, transforms=(), alpha: object = 0.75, kernel: str = "qbp_mbp4_fixed_alpha") -> dict:
    data = _public_v2_manifest()
    data["composition"]["kernel"] = {"kind": kernel, "binding_id": "mbp4", "config": {"alpha": alpha}}
    data["composition"]["transforms"] = [
        {"kind": kind, "binding_id": f"transform-{index}"} for index, kind in enumerate(transforms)
    ]
    return data


def test_mbp4_public_source_run_records_fixed_recurrence_and_replays(tmp_path):
    from bp_registry.quaternary import execution

    assert hasattr(execution, "run_quaternary_mbp4")
    manifest = _mbp4_public_manifest()
    report = preflight_quaternary(manifest)
    assert report["composition"]["run_fidelity"] == "source_backed"
    result = run_quaternary(manifest, tmp_path)
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    decode = next(event for event in events if event["kind"] == "mbp4_decode")
    assert decode["data"]["alpha"] == pytest.approx(0.75)
    assert decode["data"]["equation_identity"] == "kuo-lai-2023-mbp4-fixed-inhibition-eq15-18"
    assert decode["data"]["schedule_freshness"] == "complete_old_v2c_snapshot_then_complete_commit"
    assert result["run_fidelity"] == "source_backed"
    assert verify_quaternary_run(tmp_path)["verified"] is True


def test_mbp4_public_unsourced_composition_is_canonical_adaptation_and_tampering_fails_replay(tmp_path):
    manifest = _mbp4_public_manifest(transforms=("qbp_c2v_normalization",))
    report = preflight_quaternary(manifest)
    assert report["composition"]["run_fidelity"] == "canonical_adaptation"
    assert "mbp4_with_qbp_c2v_normalization" in report["composition"]["adaptation_reasons"]
    run_quaternary(manifest, tmp_path)
    path = tmp_path / "events.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace('"alpha":0.75', '"alpha":0.5', 1), encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        verify_quaternary_run(tmp_path)


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"kernel": "ambp4"}, "AMBP4"),
        ({"alpha": [1.0, 0.75]}, "alpha search|fixed alpha"),
        ({"kernel": "binary_memory"}, "unsupported binary"),
    ],
)
def test_mbp4_public_preflight_rejects_adaptive_and_binary_variants(kwargs, match):
    with pytest.raises(ValueError, match=match):
        preflight_quaternary(_mbp4_public_manifest(**kwargs))
