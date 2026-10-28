"""Source coordinates, B2 construction, and independent study evaluator."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import runpy

import numpy as np

from bp_registry.code_constructions import build_b2_ghp
from bp_registry.css import semantic_sha256


ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "data/reproductions/yao-2312-10950-vanilla"


def test_figure_7_and_8_qbp_points_are_exact_tex_transcriptions() -> None:
    points = json.loads((STUDY / "source_points.json").read_text())
    assert points["qbp_iterations"] == 100
    assert points["curves"]["a5"]["p_to_qbp_rate"] == {
        "0.04": .000236, "0.05": .000876, "0.06": .003159,
        "0.07": .011972, "0.08": .039651, "0.09": .093809, "0.10": .1443,
    }
    assert points["curves"]["b2"]["p_to_qbp_rate"] == {
        "0.04": .000406, "0.05": .001265, "0.06": .002569,
        "0.07": .006755, "0.08": .015077, "0.09": .029780, "0.10": .060326,
    }


def test_b2_source_matrix_and_logicals_have_pinned_identity() -> None:
    code = build_b2_ghp()
    receipt = json.loads((STUDY / "codes/b2.json").read_text())
    assert (code.n, code.k) == (882, 48)
    assert semantic_sha256(code) == receipt["css_semantic_sha256"]
    assert sha256(code.hx.tobytes()).hexdigest() == receipt["hx_sha256"]
    assert sha256(code.hz.tobytes()).hexdigest() == receipt["hz_sha256"]
    np.testing.assert_array_equal(np.unique(code.hx.sum(axis=1)), [8])
    np.testing.assert_array_equal(np.unique(code.hx.sum(axis=0)), [3, 5])
    np.testing.assert_array_equal((code.hx.astype(np.int64) @ code.hz.astype(np.int64).T) % 2,
                                  np.zeros((441, 441), dtype=np.uint8))
    assert code.lx is not None and code.lz is not None
    np.testing.assert_array_equal((code.lx.astype(np.int64) @ code.lz.astype(np.int64).T) % 2,
                                  np.eye(48, dtype=np.uint8))


def test_independent_syndrome_and_logical_signatures_agree_with_matrix_algebra() -> None:
    study = runpy.run_path(str(STUDY / "run.py"))
    code = build_b2_ghp()
    evaluator = study["_syndrome_evaluator"](code)
    masks = study["_logical_masks"](code)
    rng = np.random.default_rng(231210950)
    for _ in range(8):
        paulis = rng.integers(0, 4, size=code.n, dtype=np.uint8)
        bits = study["PAULI_BITS"][paulis]
        actual = study["_original_syndrome"](evaluator, paulis)
        sx = (code.hx.astype(np.int64) @ bits[:, 1].astype(np.int64) % 2).astype(np.uint8)
        sz = (code.hz.astype(np.int64) @ bits[:, 0].astype(np.int64) % 2).astype(np.uint8)
        np.testing.assert_array_equal(actual, np.concatenate((sx, sz)))
        logical = ((code.lz.astype(np.int64) @ bits[:, 0].astype(np.int64)
                    + code.lx.astype(np.int64) @ bits[:, 1].astype(np.int64)) % 2).astype(np.uint64)
        signature = int(np.sum(logical << np.arange(code.k, dtype=np.uint64)))
        assert study["_logical_signature"](paulis, masks) == signature


def test_decoder_files_bind_four_undamped_vanilla_profiles() -> None:
    study = runpy.run_path(str(STUDY / "run.py"))
    specs = study["_decoder_specs"]()
    assert tuple(specs) == ("bp4_v1", "bp4_v2", "binary_v1", "binary_v2")
    assert all(spec["max_iterations"] == 100 and spec["damping_old"] == 0 for spec in specs.values())
    code = study["_load_code"]("a5")
    graphs = study["_graphs"](code, .08)
    assert graphs["bp4_v1"].profile.profile_id == specs["bp4_v1"]["numerical_profile"]
    assert graphs["bp4_v2"].profile.profile_id == specs["bp4_v2"]["numerical_profile"]
    assert graphs["bp4_v2"].profile.v2c_damping == 0.0
    assert graphs["binary_v2"][0].graph.profile.v2c_damping == 0.0
