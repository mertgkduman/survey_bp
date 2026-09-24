"""Independent identity and algebra gates for Phase 3 CSS pilot artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np


ARTIFACTS = Path("data/artifacts")


def _construction_module():
    assert importlib.util.find_spec("bp_registry.code_constructions") is not None, (
        "Phase 3 needs deterministic source-traced CSS construction helpers"
    )
    from bp_registry import code_constructions

    return code_constructions


def test_b1_builder_freezes_exact_source_construction_and_project_logicals():
    constructions = _construction_module()
    from bp_registry.css import gf2_rank, semantic_sha256

    code = constructions.build_b1_ghp()
    assert code.hx.shape == code.hz.shape == (441, 882)
    assert code.n == 882 and code.k == 24
    assert gf2_rank(code.hx) == gf2_rank(code.hz) == 429
    assert not np.any((code.hx.astype(np.int64) @ code.hz.astype(np.int64).T) % 2)
    assert np.array_equal(code.hx.sum(axis=1), np.full(441, 6))
    assert np.array_equal(code.hz.sum(axis=1), np.full(441, 6))
    assert np.array_equal(code.hx.sum(axis=0), np.full(882, 3))
    assert np.array_equal(code.hz.sum(axis=0), np.full(882, 3))
    assert code.lx is not None and code.lz is not None
    assert code.lx.shape == code.lz.shape == (24, 882)

    metadata = json.loads((ARTIFACTS / "b1-panteleev-kalachev-v3.json").read_text())
    assert metadata["code_id"] == "b1-ghp-882"
    assert metadata["source"]["archive_member"] == "matrices/ghpc_3_3_N882_K24.tex"
    assert metadata["source"]["archive_member_sha256"] == (
        "91be6649c066b88d46e1b232ac16c3e7cb94f8a928fd9f82834663b16e9d8e83"
    )
    assert metadata["logical_provenance"]["status"] == "project-derived"
    assert metadata["assessment_status"] == "not_assessed"
    assert metadata["distance"] == {"status": "source_bounded", "lower": 18, "upper": 24}

    with np.load(ARTIFACTS / "b1-panteleev-kalachev-v3.npz", allow_pickle=False) as frozen:
        assert set(frozen.files) == {"hx", "hz", "lx", "lz"}
        assert np.array_equal(frozen["hx"], code.hx)
        assert np.array_equal(frozen["hz"], code.hz)
        assert np.array_equal(frozen["lx"], code.lx)
        assert np.array_equal(frozen["lz"], code.lz)
    raw = (ARTIFACTS / "b1-panteleev-kalachev-v3.npz").read_bytes()
    assert metadata["artifact"]["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert metadata["artifact"]["semantic_sha256"] == semantic_sha256(code)


def test_b1_polynomial_order_and_regeneration_are_explicit():
    constructions = _construction_module()

    code = constructions.build_b1_ghp()
    first_block = code.hx[:63, :441]
    # Rows 0..62 encode x^27 at block 0, 1 at block 5, and x^54 at block 6.
    assert np.array_equal(first_block[0], np.concatenate((
        np.eye(63, dtype=np.uint8)[27], np.zeros(63 * 4, dtype=np.uint8),
        np.eye(63, dtype=np.uint8)[0], np.eye(63, dtype=np.uint8)[54],
    )))
    assert np.array_equal(constructions.build_b1_ghp().hx, code.hx)
