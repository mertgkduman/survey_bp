"""Regression coverage for Phase 9's authored CSS source receipts."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
YAO = ROOT / "literature_policies/yao-2024-guided-decimation/paper_reproduction/source-targets-v1.json"
RABETI = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/source-targets-v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_yao_tracer_preserves_literal_target_rounding_and_identity_gaps():
    payload = _load(YAO)
    tracer = next(item for item in payload["targets"] if item["target_id"] == "yao-fig3-bpgd-t001-p010")

    assert payload["source_archive"]["sha256"] == "8ddade4c50c9b12853e5431c53f4906fd29913bbf3be306422bafd984a05d654"
    assert tracer["literal_decimal"] == "0.855932"
    assert tracer["rounding_interval"] == {"lower": 0.8559315, "upper": 0.8559325}
    assert tracer["stopping"]["status"] == "observed"
    assert "ordered_paper_checks_and_logicals_unverified" in tracer["identity_gaps"]
    assert "author_implementation_and_settings_unverified" in tracer["identity_gaps"]
    assert tracer["faithful_eligible"] is False


def test_yao_tracer_refuses_faithful_eligibility_when_any_d02_gap_remains():
    payload = _load(YAO)
    tracer = next(item for item in payload["targets"] if item["target_id"] == "yao-fig3-bpgd-t001-p010")
    for gap in tracer["identity_gaps"]:
        candidate = copy.deepcopy(tracer)
        candidate["identity_gaps"].remove(gap)
        assert candidate["faithful_eligible"] is False


def test_authored_coordinates_are_unique_and_keep_locator_specific_stopping_status():
    yao = _load(YAO)
    rabeti = _load(RABETI)

    assert len(yao["targets"]) == 70
    assert len({(item["figure"], item["curve"], item["p_literal"]) for item in yao["targets"]}) == 70
    assert len(rabeti["targets"]) == 7
    assert {item["p_literal"] for item in rabeti["targets"]} == {"0.04", "0.05", "0.06", "0.07", "0.08", "0.09", "0.10"}
    assert all(item["stopping"]["status"] == "unavailable" for item in yao["targets"] if item["figure"] == "Figure 6")
    assert all(item["stopping"]["status"] == "observed" for item in rabeti["targets"])


def test_source_receipt_models_validate_and_candidate_b1_never_becomes_author_supplied():
    from bp_registry.campaigns.targets import SourceExperimentQualificationReceiptV1, TableTargetReceiptV1

    for path in (YAO, RABETI):
        payload = _load(path)
        for receipt in payload["table_target_receipts"]:
            TableTargetReceiptV1.model_validate_json(json.dumps(receipt))
        for receipt in payload["source_experiment_qualifications"]:
            qualified = SourceExperimentQualificationReceiptV1.model_validate_json(json.dumps(receipt))
            assert qualified.faithful_eligible is False
            assert qualified.native_assessment.status == "identity_unverified"
        assert payload["candidate_artifact"]["logical_provenance"]["author_supplied"] is False
        assert payload["canonical_adaptation"]["assessment_label"] == "canonical_adaptation"


def test_source_archive_digest_and_literal_receipts_are_stable():
    for path in (YAO, RABETI):
        payload = _load(path)
        assert len(payload["source_archive"]["sha256"]) == 64
        assert all(item["literal_decimal"] for item in payload["targets"])
