"""Pinned Yao non-OSD source extraction and exact C2 HP construction."""

from pathlib import Path
import runpy

import numpy as np

from bp_registry.code_constructions import build_b1_ghp, build_c2_hp
from bp_registry.css import semantic_sha256


def test_c2_source_polynomial_builds_pinned_css_code() -> None:
    code = build_c2_hp()
    assert (code.n, code.k) == (1922, 50)
    assert code.hx.shape == code.hz.shape == (961, 1922)
    assert np.all(code.hx.sum(axis=0) == 3)
    assert np.all(code.hz.sum(axis=0) == 3)
    assert np.all(code.hx.sum(axis=1) == 6)
    assert np.all(code.hz.sum(axis=1) == 6)
    assert semantic_sha256(code) == "a3ea36c9b1a588b133e24dd9ff27fd4964c495cc8a9ae4c875c36b635ac0903b"


def test_source_figure_extraction_preserves_conflicting_b1_t10_values() -> None:
    import json

    source = Path(__file__).resolve().parents[1] / "data/reproductions/yao-2312-10950-non-osd/source_points.json"
    extracted = json.loads(source.read_text())
    assert extracted["figures"]["3"]["curves"]["bpgd_t10"]["0.06000"] == 0.003891
    assert extracted["figures"]["4"]["curves"]["bpgd_t10"]["0.06000"] == 0.00367352876


def test_binary_outcomes_count_stabilizer_equivalence_as_success() -> None:
    path = Path(__file__).resolve().parents[1] / "data/reproductions/yao-2312-10950-non-osd/run_point.py"
    runner = runpy.run_path(str(path))
    code = build_b1_ghp()
    truth = np.zeros(code.n, dtype=np.uint8)
    syndrome = np.zeros(code.hz.shape[0], dtype=np.uint8)
    packed_hx = np.packbits(code.hx, axis=1, bitorder="little")
    packed_hz = np.packbits(code.hz, axis=1, bitorder="little")
    masks = runner["_binary_masks"](code)
    stabilizer = runner["_outcome"](code.hx[0], truth, syndrome, packed_hx, packed_hz,
                                     code, masks, None)
    logical = runner["_outcome"](code.lx[0], truth, syndrome, packed_hx, packed_hz,
                                  code, masks, None)
    assert stabilizer == {"type_i": False, "type_ii": False,
                          "exact_success": False, "stabilizer_success": True}
    assert logical["type_ii"] and not logical["type_i"]
