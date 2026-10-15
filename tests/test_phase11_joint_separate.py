"""Matched-sample boundary tests for the Phase 11 controlled comparison."""

from __future__ import annotations

import base64
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from bp_registry.campaigns.contracts import MaterializedPhysicalSampleV1, canonical_json_bytes
from bp_registry.campaigns.controlled_execution import (
    BinaryArmInputV1,
    BinaryArmResultV1,
    JointArmInputV1,
    JointArmResultV1,
    canonical_binary_materialized_decoder,
    run_joint_separate_unit,
)
from bp_registry.css import CssCode


def _digest(domain: str, payload: object) -> str:
    return sha256(domain.encode("ascii") + b"\0" + canonical_json_bytes(payload)).hexdigest()


def _sample() -> tuple[CssCode, MaterializedPhysicalSampleV1]:
    code = CssCode(
        hx=np.asarray([[1, 1]], dtype=np.uint8),
        hz=np.asarray([[1, 1]], dtype=np.uint8),
    ).validate()
    x = np.asarray([1, 0], dtype=np.uint8)
    z = np.asarray([0, 1], dtype=np.uint8)
    x_b64 = base64.b64encode(x.tobytes()).decode("ascii")
    z_b64 = base64.b64encode(z.tobytes()).decode("ascii")
    observations = {
        "X": {"check_type": "X", "dtype": "uint8", "shape": [1], "bytes_b64": base64.b64encode(np.asarray([1], dtype=np.uint8).tobytes()).decode("ascii")},
        "Z": {"check_type": "Z", "dtype": "uint8", "shape": [1], "bytes_b64": base64.b64encode(np.asarray([1], dtype=np.uint8).tobytes()).decode("ascii")},
    }
    unsigned = {
        "schema": "materialized_physical_sample_v1", "physical_sample_identity": "1" * 64,
        "sample_seed_identity": "2" * 64, "cohort_id": "phase11-tracer", "point_id": "independent_xz",
        "sample_namespace": "phase11-gb46", "sample_id": 0, "sampler_contract_sha256": "3" * 64,
        "x_dtype": "uint8", "x_shape": [2], "x_bytes_b64": x_b64,
        "z_dtype": "uint8", "z_shape": [2], "z_bytes_b64": z_b64,
        "observations": observations,
        "physical_error_sha256": _digest("bp-registry-physical-error-v1", {"x": x_b64, "z": z_b64}),
    }
    return code, MaterializedPhysicalSampleV1.model_validate({
        **unsigned,
        "materialized_sample_sha256": _digest("bp-registry-materialized-sample-v1", unsigned),
    })


def test_tracer_identical_sample_marginals_and_hidden_truth_boundary():
    code, sample = _sample()
    seen: list[object] = []

    def joint(input_: JointArmInputV1) -> JointArmResultV1:
        seen.append(input_)
        return JointArmResultV1(candidate_x=(1, 0), candidate_z=(0, 1), terminal_status="exact", iterations=2, work={"sweeps": 2})

    def binary(input_: BinaryArmInputV1) -> BinaryArmResultV1:
        seen.append(input_)
        assert set(input_.model_dump()) == {"component", "prior", "syndrome", "physical_sample_identity", "materialized_sample_sha256"}
        return BinaryArmResultV1(candidate=(1, 0) if input_.component == "X" else (0, 1), terminal_status="exact", iterations=3, work={"sweeps": 3})

    record = run_joint_separate_unit(
        code=code, materialized_sample=sample,
        joint_probabilities=((0.9, 0.04, 0.02, 0.04),) * 2,
        joint_decoder=joint, binary_decoder=binary,
    )

    assert record.physical_sample_identity == sample.physical_sample_identity
    assert record.joint.materialized_sample_sha256 == sample.materialized_sample_sha256
    assert record.separate.materialized_sample_sha256 == sample.materialized_sample_sha256
    binary_inputs = [item for item in seen if isinstance(item, BinaryArmInputV1)]
    assert [item.component for item in binary_inputs] == ["X", "Z"]
    assert [item.prior for item in binary_inputs] == [(0.06, 0.06), (0.06, 0.06)]
    assert record.joint.evaluation["outcome"] == "exact"
    assert record.separate.evaluation["outcome"] == "exact"


@pytest.mark.parametrize("x_status,z_status", [
    ("nonconvergence", "exact"), ("exact", "nonconvergence"), ("nonconvergence", "nonconvergence"),
])
def test_partial_nonconvergence_keeps_components_and_all_shot_pair(x_status: str, z_status: str):
    code, sample = _sample()

    def joint(_: JointArmInputV1) -> JointArmResultV1:
        return JointArmResultV1(candidate_x=(1, 0), candidate_z=(0, 1), terminal_status="exact", work={"sweeps": 1})

    def binary(input_: BinaryArmInputV1) -> BinaryArmResultV1:
        status = x_status if input_.component == "X" else z_status
        candidate = (1, 0) if input_.component == "X" else (0, 1)
        return BinaryArmResultV1(candidate=candidate, terminal_status=status, iterations=4, work={"sweeps": 4})

    record = run_joint_separate_unit(
        code=code, materialized_sample=sample,
        joint_probabilities=((0.9, 0.04, 0.02, 0.04),) * 2,
        joint_decoder=joint, binary_decoder=binary,
    )

    assert tuple(component.terminal_status for component in record.components) == (x_status, z_status)
    assert record.separate.candidate_x == (1, 0)
    assert record.separate.candidate_z == (0, 1)
    assert record.separate.terminal_status == "nonconvergence"
    assert record.separate.all_shot == "failure"
    assert record.separate.evaluation["outcome"] == "exact"


@pytest.mark.parametrize("status, expected_all_shot", [
    ("wrong_logical_action", "failure"),
    ("postselected_rejection", "failure"),
    ("no_proposal", "failure"),
    ("nonconvergence", "failure"),
    ("invalid_syndrome", "failure"),
    ("timeout", "failure"),
    ("infrastructure_interruption", "incomplete"),
])
def test_unsuccessful_component_prevents_separate_success(status: str, expected_all_shot: str):
    """Candidate agreement cannot override a component's terminal evidence."""
    code, sample = _sample()

    def joint(_: JointArmInputV1) -> JointArmResultV1:
        return JointArmResultV1(candidate_x=(1, 0), candidate_z=(0, 1), terminal_status="exact", work={"sweeps": 1})

    def binary(input_: BinaryArmInputV1) -> BinaryArmResultV1:
        return BinaryArmResultV1(
            candidate=(1, 0) if input_.component == "X" else (0, 1),
            terminal_status=status if input_.component == "X" else "exact", work={"sweeps": 1},
        )

    record = run_joint_separate_unit(
        code=code, materialized_sample=sample,
        joint_probabilities=((0.9, 0.04, 0.02, 0.04),) * 2,
        joint_decoder=joint, binary_decoder=binary,
    )

    assert record.separate.evaluation["outcome"] == "exact"
    assert record.separate.terminal_status == status
    assert record.separate.all_shot == expected_all_shot


def test_replay_and_tamper_reject_changed_evidence():
    code, sample = _sample()

    def joint(_: JointArmInputV1) -> JointArmResultV1:
        return JointArmResultV1(candidate_x=(1, 0), candidate_z=(0, 1), terminal_status="exact", work={"sweeps": 1})

    def binary(input_: BinaryArmInputV1) -> BinaryArmResultV1:
        return BinaryArmResultV1(candidate=(1, 0) if input_.component == "X" else (0, 1), terminal_status="exact", work={"sweeps": 1})

    record = run_joint_separate_unit(
        code=code, materialized_sample=sample,
        joint_probabilities=((0.9, 0.04, 0.02, 0.04),) * 2,
        joint_decoder=joint, binary_decoder=binary,
    )
    assert record.verify_replay().record_sha256 == record.record_sha256
    tampered = record.model_dump(mode="json", by_alias=True)
    tampered["components"][0]["candidate"] = [0, 0]
    with pytest.raises(ValueError, match="digest"):
        type(record).model_validate(tampered)
    changed_sample = sample.model_copy(update={"x_bytes_b64": base64.b64encode(b"\0\0").decode("ascii")})
    with pytest.raises(ValueError, match="physical error digest"):
        run_joint_separate_unit(
            code=code, materialized_sample=changed_sample,
            joint_probabilities=((0.9, 0.04, 0.02, 0.04),) * 2,
            joint_decoder=joint, binary_decoder=binary,
        )


def test_duplicate_or_partial_pair_evidence_is_rejected():
    code, sample = _sample()

    def joint(_: JointArmInputV1) -> JointArmResultV1:
        return JointArmResultV1(candidate_x=(1, 0), candidate_z=(0, 1), terminal_status="exact", work={"sweeps": 1})

    def binary(input_: BinaryArmInputV1) -> BinaryArmResultV1:
        return BinaryArmResultV1(candidate=(1, 0) if input_.component == "X" else (0, 1), terminal_status="exact", work={"sweeps": 1})

    record = run_joint_separate_unit(
        code=code, materialized_sample=sample,
        joint_probabilities=((0.9, 0.04, 0.02, 0.04),) * 2,
        joint_decoder=joint, binary_decoder=binary,
    )
    duplicate = record.model_dump(mode="json", by_alias=True)
    duplicate["separate"]["arm_id"] = "joint"
    with pytest.raises(ValueError, match="exactly one joint"):
        type(record).model_validate(duplicate)
    swapped = record.model_dump(mode="json", by_alias=True)
    swapped["components"] = list(reversed(swapped["components"]))
    with pytest.raises(ValueError, match="ordered X then Z"):
        type(record).model_validate(swapped)
    partial = record.model_dump(mode="json", by_alias=True)
    partial.pop("separate")
    with pytest.raises(ValueError, match="Field required"):
        type(record).model_validate(partial)


def test_component_adapter_uses_canonical_materialized_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _, sample = _sample()
    calls: list[dict[str, object]] = []

    def fake_runner(_: Path, **kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        ledger = Path(str(kwargs["ledger_path"]))
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text('{"data":{"selected_output":[1,0]}}\n', encoding="utf-8")
        return SimpleNamespace(outcome="exact", iterations=7)

    monkeypatch.setattr("bp_registry.runner.run_canonical_materialized_one", fake_runner)
    decoder = canonical_binary_materialized_decoder(
        materialized_sample=sample,
        manifest_paths={"X": tmp_path / "x.json", "Z": tmp_path / "z.json"}, ledger_directory=tmp_path,
    )
    result = decoder(BinaryArmInputV1(
        component="X", prior=(0.06, 0.06), syndrome=(1,),
        physical_sample_identity=sample.physical_sample_identity,
        materialized_sample_sha256=sample.materialized_sample_sha256,
    ))
    assert result.candidate == (1, 0)
    assert result.terminal_status == "exact"
    assert calls[0]["materialized_sample_sha256"] == sample.materialized_sample_sha256


def test_bb72_typed_work_and_wall_runtime_are_retained_without_unit_conversion():
    """Each arm keeps its own named work and identical timing boundary."""
    code, sample = _sample()

    def joint(_: JointArmInputV1) -> JointArmResultV1:
        return JointArmResultV1(
            candidate_x=(1, 0), candidate_z=(0, 1), terminal_status="exact", work={"bp4_sweeps": 2},
            runtime_ns=20, timing_boundary="decoder_callback_wall_v1",
        )

    def binary(input_: BinaryArmInputV1) -> BinaryArmResultV1:
        return BinaryArmResultV1(
            candidate=(1, 0) if input_.component == "X" else (0, 1), terminal_status="exact",
            work={"binary_spa_iterations": 3}, runtime_ns=10, timing_boundary="decoder_callback_wall_v1",
        )

    record = run_joint_separate_unit(
        code=code, materialized_sample=sample, joint_probabilities=((0.9, 0.04, 0.02, 0.04),) * 2,
        joint_decoder=joint, binary_decoder=binary,
    )

    assert record.joint.work == {"bp4_sweeps": 2}
    assert record.separate.work == {"x_binary_spa_iterations": 3, "z_binary_spa_iterations": 3}
    assert record.joint.runtime_ns == 20
    assert record.separate.runtime_ns == 20
    assert record.joint.timing_boundary == record.separate.timing_boundary == "decoder_callback_wall_v1"
