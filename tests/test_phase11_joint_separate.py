"""Matched-sample boundary tests for the Phase 11 controlled comparison."""

from __future__ import annotations

import base64
from hashlib import sha256

import numpy as np

from bp_registry.campaigns.contracts import MaterializedPhysicalSampleV1, canonical_json_bytes
from bp_registry.campaigns.controlled_execution import (
    BinaryArmInputV1,
    BinaryArmResultV1,
    JointArmInputV1,
    JointArmResultV1,
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
