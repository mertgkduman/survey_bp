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
