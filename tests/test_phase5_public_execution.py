"""Public Phase 5 source qualification and manifest-boundary fixtures."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_source_decisions_qualification_native_availability_restart_distance():
    record = json.loads((ROOT / "docs/evidence/phase5-source-decisions.json").read_text(encoding="utf-8"))
    assert record["schema_version"] == 1
    assert record["recorded_date"] == "2026-09-30"
    assert set(record["arms"]) == {
        "bpgd", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief",
    }
    required = {
        "paper_revision", "source_url", "procedure_anchor", "kernel_family", "trigger",
        "target_and_order", "changed_state", "preserved_state", "reset_rule", "lift_rule",
        "native_repository", "native_commit", "native_availability", "qualification",
        "unresolved", "canonical_identity",
    }
    for arm in record["arms"].values():
        assert required <= set(arm)
        assert arm["unresolved"] is not None
        assert arm["qualification"] in {
            "algorithm_interpretation", "controlled_css_adaptation", "mechanism_only_adaptation"
        }
    assert record["arms"]["bpgd"]["canonical_identity"] == "algorithm1_v2_interpretation"
    assert record["arms"]["impulse"]["native_availability"] == "unverified"
    assert record["arms"]["impulse"]["source_procedure"]["operator"] == "unchanged_graph_negative_infinite_llr"
    assert record["arms"]["impulse"]["canonical_adaptation"]["operator"] == "exact_structural_shortening"
    assert record["arms"]["bpgd"]["native_availability"] == "unverified"
    assert record["arms"]["sign_flip"]["native_availability"] == "unverified"
    assert record["arms"]["syndrome_flip"]["native_commit"] == "0417d33fc2ffb3b442d0397bb09954fc1c6c3938"
    assert record["arms"]["restart_belief"]["native_commit"] == "275535ec981763166c8549d91959dc6e371ec4b1"
    restart = record["arms"]["restart_belief"]
    assert restart["b1_distance"] == {"status": "source_bounded", "lower": 18, "upper": 24}
    assert restart["b1_t_cap"] == 8
    assert restart["qualification"] == "mechanism_only_adaptation"
