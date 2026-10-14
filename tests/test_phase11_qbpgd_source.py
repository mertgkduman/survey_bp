"""Regression coverage for the Q-BPGD Figure 7 A5 source target."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ARTIFACT = Path("data/artifacts/quaternary-a5.json")
PROVENANCE = Path("data/artifacts/quaternary-a5.provenance.json")


def test_a5_tracer_reconstructs_the_official_polynomial_css_artifact():
    from bp_registry.quaternary.problems import construct_qbpgd_a5_css

    code, receipt = construct_qbpgd_a5_css()

    assert code.n == 180
    assert receipt["construction"] == {
        "l": 90,
        "a_exponents": [0, 28, 80, 89],
        "b_exponents": [0, 2, 21, 25],
        "circulant_convention": "row_i_column_(i+exponent)_mod_l",
    }
    assert receipt["checks"]["commutes"] is True
    assert receipt["checks"]["claimed_parameters"] == {"n": 180, "k": 10}
    assert receipt["distance"]["status"] == "source_reported_bounds"
    assert receipt["distance"]["independently_verified"] is False
    assert receipt["artifact"]["pauli_semantic_sha256"] == sha256(code.semantic_bytes()).hexdigest()


def test_a5_artifact_and_provenance_bind_reconstructed_bytes_and_source_bounds():
    from bp_registry.quaternary.problems import build_qbpgd_a5_css_artifact
    from bp_registry.css import CssCode, semantic_sha256

    assert ARTIFACT.is_file() and PROVENANCE.is_file()
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    code = CssCode(**{key: artifact[key] for key in ("hx", "hz", "lx", "lz")}).validate()
    rebuilt, receipt = build_qbpgd_a5_css_artifact()

    assert code.hx.tolist() == rebuilt.hx.tolist()
    assert sha256(ARTIFACT.read_bytes()).hexdigest() == provenance["artifact"]["raw_sha256"]
    assert semantic_sha256(code) == provenance["artifact"]["semantic_sha256"] == receipt["artifact"]["semantic_sha256"]
    assert provenance["independent_validation"]["commutator_nonzero_entries"] == 0
    assert provenance["distance"] == {"independently_verified": False, "status": "source_reported_bounds", "value": "15<=d<=18"}
