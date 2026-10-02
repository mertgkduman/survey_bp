"""Independent small-code identity and algebra checks for the frozen BB72 fixture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry.css import CssCode, gf2_rank, semantic_sha256
from tools.freeze_bb72_source import SourceGateError, matrix_hashes, source_parameters


ARTIFACT = Path("data/artifacts/bb72-css.json")
PROVENANCE = Path("data/artifacts/bb72-css.provenance.json")


def test_source_comment_requires_unique_exact_bb72_recipe():
    block = "# [[72,12,6]]\n#ell,m = 6,6\n#a1,a2,a3=3,1,2\n#b1,b2,b3=3,1,2\n"
    assert source_parameters(block) == {
        "ell": 6, "m": 6, "a1": 3, "a2": 1, "a3": 2, "b1": 3, "b2": 1, "b3": 2,
    }
    with pytest.raises(SourceGateError):
        source_parameters(block + block)
    with pytest.raises(SourceGateError):
        source_parameters(block.replace("#ell,m = 6,6", "#ell,m = 12,6"))


def test_frozen_bb72_matches_independent_polynomial_expansion_and_css_algebra():
    frozen = json.loads(ARTIFACT.read_text())
    code = CssCode(*(np.asarray(frozen[key], dtype=np.uint8) for key in ("hx", "hz", "lx", "lz"))).validate()
    identity = np.eye(6, dtype=np.uint8)
    x = lambda power: np.kron(np.roll(identity, power, axis=1), identity)
    y = lambda power: np.kron(identity, np.roll(identity, power, axis=1))
    a = (x(3) + y(1) + y(2)) % 2
    b = (y(3) + x(1) + x(2)) % 2
    np.testing.assert_array_equal(code.hx, np.hstack((a, b)))
    np.testing.assert_array_equal(code.hz, np.hstack((b.T, a.T)))
    assert code.hx.shape == code.hz.shape == (36, 72)
    assert code.lx.shape == code.lz.shape == (12, 72)
    assert (gf2_rank(code.hx), gf2_rank(code.hz), code.k) == (30, 30, 12)
    np.testing.assert_array_equal(code.hx.sum(axis=1), np.full(36, 6))
    np.testing.assert_array_equal(code.hz.sum(axis=1), np.full(36, 6))
    np.testing.assert_array_equal(code.hx.sum(axis=0), np.full(72, 3))
    np.testing.assert_array_equal(code.hz.sum(axis=0), np.full(72, 3))
    np.testing.assert_array_equal((code.lx.astype(int) @ code.lz.astype(int).T) % 2, np.eye(12))

    provenance = json.loads(PROVENANCE.read_text())
    assert provenance["source"]["revision"] == "fa77e3333d3ec44c79d8f914dd24c040d1da471b"
    assert provenance["source"]["source_file_sha256"] == "e919e1830b88468c5d257c0119656576a7999f92743dfeccd389a967524b3d2c"
    assert provenance["logical_provider"]["status"] == "project_derived"
    assert provenance["distance"]["independently_verified"] is False
    assert hashlib.sha256(ARTIFACT.read_bytes()).hexdigest() == provenance["artifact"]["raw_sha256"]
    assert semantic_sha256(code) == provenance["artifact"]["semantic_sha256"]
    assert matrix_hashes(code) == provenance["artifact"]["matrix_hashes"]


def test_bb72_public_manifest_pins_every_matrix_and_does_not_claim_reproduction():
    manifest = json.loads(Path("data/manifests/phase3-pilot-bb72.json").read_text())
    provenance = json.loads(PROVENANCE.read_text())
    assert manifest["artifact"]["code_id"] == "bravyi-bb-72"
    assert manifest["artifact"]["path"] == "bb72-css.json"
    assert manifest["artifact"]["raw_sha256"] == provenance["artifact"]["raw_sha256"]
    assert manifest["artifact"]["semantic_sha256"] == provenance["artifact"]["semantic_sha256"]
    assert manifest["artifact"]["matrix_hashes"] == provenance["artifact"]["matrix_hashes"]
    assert manifest["evidence"]["assessment_status"] == "not_assessed"
