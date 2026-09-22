"""Independent algebra and serialization contracts for small CSS codes."""

import hashlib
import struct
import json
import os
from pathlib import Path

import numpy as np
import pytest


def _small_code_with_logicals():
    from bp_registry.css import CssCode

    # The ordered pair has the convention Lx[i] · Lz[i] = 1 over GF(2).
    return CssCode(
        hx=np.array([[1, 1, 0]], dtype=np.uint8),
        hz=np.array([[0, 0, 1]], dtype=np.uint8),
        lx=np.array([[1, 0, 0]], dtype=np.uint8),
        lz=np.array([[1, 1, 0]], dtype=np.uint8),
    ).validate()


def test_css_rejects_noncommuting_checks():
    from bp_registry.css import CssCode

    hx = np.array([[1, 0]], dtype=np.uint8)
    hz = np.array([[1, 0]], dtype=np.uint8)
    with pytest.raises(ValueError):
        CssCode(hx=hx, hz=hz).validate()


def test_css_rejects_nonbinary_entry():
    from bp_registry.css import CssCode

    with pytest.raises(ValueError):
        CssCode(hx=np.array([[2, 0]]), hz=np.array([[0, 1]])).validate()


def test_gf2_rank_and_css_logical_pair_validation():
    import bp_registry.css as css

    assert hasattr(css, "gf2_rank"), "CSS algebra must expose GF(2) rank"
    assert hasattr(css.CssCode, "k"), "CSS codes must expose their encoded dimension"
    gf2_rank = css.gf2_rank
    CssCode = css.CssCode

    # Its determinant is -2, so real rank is 3 while its GF(2) rank is 2.
    dependent_over_gf2 = np.array([[1, 1, 0], [1, 0, 1], [0, 1, 1]], dtype=np.uint8)
    assert np.linalg.matrix_rank(dependent_over_gf2) == 3
    assert gf2_rank(dependent_over_gf2) == 2

    assert _small_code_with_logicals().n == 3
    assert _small_code_with_logicals().k == 1

    with pytest.raises(ValueError, match="pair"):
        CssCode(
            hx=np.array([[1, 1, 0]], dtype=np.uint8),
            hz=np.array([[0, 0, 1]], dtype=np.uint8),
            lx=np.array([[1, 0, 0]], dtype=np.uint8),
            lz=np.array([[0, 0, 1]], dtype=np.uint8),
        ).validate()

    with pytest.raises(ValueError):
        CssCode(
            hx=np.array([[1, 1, 0]], dtype=np.uint8),
            hz=np.array([[0, 0, 1]], dtype=np.uint8),
            lx=np.array([[1, 1, 0]], dtype=np.uint8),
            lz=np.array([[1, 1, 0]], dtype=np.uint8),
        ).validate()


def test_semantic_bytes_are_order_sensitive_and_stable_across_processes(tmp_path):
    import bp_registry.css as css

    assert hasattr(css, "semantic_bytes"), "CSS artifacts need canonical v1 bytes"
    assert hasattr(css, "semantic_sha256"), "CSS artifacts need semantic SHA-256"
    semantic_bytes = css.semantic_bytes
    semantic_sha256 = css.semantic_sha256
    CssCode = css.CssCode

    code = _small_code_with_logicals()
    first = semantic_bytes(code)
    second = semantic_bytes(code)
    assert first == second
    assert semantic_sha256(code) == hashlib.sha256(first).hexdigest()

    # This is an independent v1 golden-byte construction: magic, version, explicit
    # pair convention, then role/dimensions/little-bit-endian matrix payloads.
    expected = b"BPREGCSS" + struct.pack("<H", 1) + struct.pack("<H", 2) + b"XZ"
    for tag, matrix in ((b"X", code.hx), (b"Z", code.hz), (b"x", code.lx), (b"z", code.lz)):
        expected += tag + struct.pack("<II", *matrix.shape)
        expected += np.packbits(matrix.reshape(-1), bitorder="little").tobytes()
    assert first == expected

    reordered = CssCode(
        hx=code.hx[:, ::-1], hz=code.hz[:, ::-1],
        lx=code.lx[:, ::-1], lz=code.lz[:, ::-1],
    ).validate()
    assert semantic_sha256(reordered) != semantic_sha256(code)

    # A fresh interpreter sees precisely the same digest.
    script = (
        "from bp_registry.css import CssCode, semantic_sha256; import numpy as np; "
        "code=CssCode(np.array([[1,1,0]],dtype=np.uint8),np.array([[0,0,1]],dtype=np.uint8),"
        "np.array([[1,0,0]],dtype=np.uint8),np.array([[1,1,0]],dtype=np.uint8)).validate(); "
        "print(semantic_sha256(code))"
    )
    import subprocess
    import sys
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    digest = subprocess.check_output(
        [sys.executable, "-c", script], text=True, env=environment
    ).strip()
    assert digest == semantic_sha256(code)


def test_artifact_loader_confines_paths_and_verifies_both_identities(tmp_path):
    import importlib.util
    import bp_registry.css as css

    assert hasattr(css, "semantic_sha256"), "CSS artifacts need semantic SHA-256"
    assert importlib.util.find_spec("bp_registry.artifacts") is not None, (
        "CSS artifacts need a confined version-dispatched loader"
    )
    semantic_sha256 = css.semantic_sha256
    from bp_registry.artifacts import load_artifact

    root = tmp_path / "approved"
    root.mkdir()
    artifact = root / "fixture.json"
    payload = {
        "format_version": 1,
        "hx": [[1, 1, 0]], "hz": [[0, 0, 1]],
        "lx": [[1, 0, 0]], "lz": [[1, 1, 0]],
    }
    raw_bytes = json.dumps(payload, separators=(",", ":")).encode()
    artifact.write_bytes(raw_bytes)

    loaded = load_artifact(
        root, "fixture.json", expected_raw_sha256=hashlib.sha256(raw_bytes).hexdigest()
    )
    assert loaded.raw_sha256 == hashlib.sha256(raw_bytes).hexdigest()
    assert loaded.semantic_sha256 == semantic_sha256(loaded.code)
    assert loaded.code.k == 1

    with pytest.raises(ValueError, match="raw SHA-256"):
        load_artifact(root, "fixture.json", expected_raw_sha256="0" * 64)
    with pytest.raises(ValueError, match="semantic SHA-256"):
        load_artifact(root, "fixture.json", expected_semantic_sha256="0" * 64)
    with pytest.raises(ValueError, match="approved root"):
        load_artifact(root, "../fixture.json")

    outside = tmp_path / "outside.json"
    outside.write_bytes(raw_bytes)
    (root / "linked.json").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        load_artifact(root, "linked.json")


def test_evaluator_separates_exact_from_degenerate(small_css_checks):
    import numpy as np
    from bp_registry.css import CssCode
    from bp_registry.evaluator import evaluate_candidate

    hx, hz = small_css_checks
    code = CssCode(hx=hx, hz=hz)
    zero = np.zeros(3, dtype=np.uint8)
    stabilizer = hx[0]
    assert evaluate_candidate(code, true_error=zero, candidate=zero).outcome == "exact"
    assert evaluate_candidate(code, true_error=zero, candidate=stabilizer).outcome == "degenerate"
