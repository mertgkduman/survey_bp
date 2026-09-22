"""Evidence gates for a CSS publication-code artifact selection."""

from __future__ import annotations

import json
from pathlib import Path


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
