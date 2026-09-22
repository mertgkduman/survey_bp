"""Evidence gates for a CSS publication-code artifact selection."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


INVENTORY = Path("data/evidence/code-inventory.json")
DECISIONS = Path("docs/phase1-source-decisions.md")


def test_inventory_distinguishes_b1_c2_and_gross_and_records_d04_gate():
    inventory = json.loads(INVENTORY.read_text())
    by_id = {candidate["code_id"]: candidate for candidate in inventory["candidates"]}
    assert set(by_id) == {"gross-bb-144", "b1-lifted-product-882", "bpgd-c2-hgp-1922"}
    assert by_id["b1-lifted-product-882"]["family"] == "lifted_product"
    assert by_id["bpgd-c2-hgp-1922"]["family"] == "hypergraph_product"
    assert by_id["gross-bb-144"]["implementation"]["revision"]
    assert inventory["selection"]["decision"] == "conditional_gross_pending_artifact_validation"
    assert "exact source rows" in inventory["selection"]["d04_rule"]


def test_verified_candidate_requires_source_matrix_logical_and_independent_evidence():
    inventory = json.loads(INVENTORY.read_text())
    for candidate in inventory["candidates"]:
        if candidate["verification_status"] != "verified":
            continue
        assert candidate["implementation"]["revision"]
        assert candidate["matrix_identity"]["status"] == "established"
        assert candidate["ordered_logical_identity"]["status"] == "established"
        assert candidate["independent_validation"]["status"] == "passed"


def test_decisions_report_has_conditional_selection_and_rejection_rationale():
    report = DECISIONS.read_text()
    assert "## Conditional ranking before the source probe" in report
    assert "## Final D-04 decision and rejected candidates" in report
    assert "conditionally selected for Task 2" in report
    assert "Gross/BB-144" in report and "B1" in report and "C2" in report


def _independent_bravyi_checks(parameters):
    """A separate implementation of the source's stated shift construction."""
    ell, m = parameters["ell"], parameters["m"]
    eye_ell, eye_m = np.eye(ell, dtype=np.uint8), np.eye(m, dtype=np.uint8)
    x = {i: np.kron(np.roll(eye_ell, i, axis=1), eye_m) for i in range(ell)}
    y = {i: np.kron(eye_ell, np.roll(eye_m, i, axis=1)) for i in range(m)}
    a = (x[parameters["a1"]] + y[parameters["a2"]] + y[parameters["a3"]]) % 2
    b = (y[parameters["b1"]] + x[parameters["b2"]] + x[parameters["b3"]]) % 2
    return np.hstack((a, b)), np.hstack((b.T, a.T))


def test_selected_artifact_regenerates_pinned_rows_and_independent_algebra():
    from bp_registry.artifacts import load_artifact
    from bp_registry.css import gf2_rank

    provenance = json.loads(Path("data/artifacts/selected-css.provenance.json").read_text())
    expected = provenance["artifact"]
    loaded = load_artifact(
        "data/artifacts", "selected-css.json",
        expected_raw_sha256=expected["raw_sha256"],
        expected_semantic_sha256=expected["semantic_sha256"],
    )
    regenerated_hx, regenerated_hz = _independent_bravyi_checks(provenance["source"]["parameters"])
    assert np.array_equal(loaded.code.hx, regenerated_hx)
    assert np.array_equal(loaded.code.hz, regenerated_hz)
    assert loaded.code.k == 12
    assert gf2_rank(loaded.code.hx) == gf2_rank(loaded.code.hz) == 66
    assert not np.any((loaded.code.hx @ loaded.code.hz.T) % 2)
    assert provenance["source"]["revision"]
    assert provenance["source"]["source_file_sha256"]
    assert provenance["logical_provider"]["source_lx_row_sha256"]
    assert provenance["logical_provider"]["source_lz_row_sha256"]


def test_selected_identity_rejects_row_bit_and_logical_pair_mutations(tmp_path):
    from bp_registry.artifacts import load_artifact

    provenance = json.loads(Path("data/artifacts/selected-css.provenance.json").read_text())
    payload = json.loads(Path("data/artifacts/selected-css.json").read_text())
    for name, mutate in {
        "row-order": lambda item: item["hx"].reverse(),
        "bit": lambda item: item["hx"][0].__setitem__(0, item["hx"][0][0] ^ 1),
        "logical-pair": lambda item: item["lz"].reverse(),
    }.items():
        changed = json.loads(json.dumps(payload))
        mutate(changed)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(changed, separators=(",", ":")))
        with pytest.raises(ValueError, match="SHA-256"):
            load_artifact(
                tmp_path, path.name,
                expected_semantic_sha256=provenance["artifact"]["semantic_sha256"],
            )
