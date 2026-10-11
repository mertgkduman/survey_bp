"""Evidence-state contracts for Phase 9 CSS source qualification."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _json(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_bhatnagar_unavailable_receipt_binds_known_bytes_without_numeric_targets() -> None:
    receipt = _json(
        "literature_policies/bhatnagar-2026-impulse-decoding/"
        "paper_reproduction/source-qualification-v1.json"
    )

    assert receipt["paper"]["revision"] == "arXiv:2606.18240v1"
    assert receipt["paper"]["sha256"] == (
        "ad7b63a456b9ec16a20aa7712b8be1f1c8d0cad48f6702583746b05363940208"
    )
    assert receipt["vector_figure"]["sha256"] == (
        "7e49980c87891a7bd21bbeca29563e2026713ef59e447e34e654118f96a454d1"
    )
    assert receipt["author_numeric_data"]["status"] == "unavailable_to_workspace"
    assert receipt["author_implementation"]["status"] == "identity_unverified"
    assert receipt["target_extraction"]["status"] == "blocked"
    assert "numeric_targets" not in receipt


def test_bhatnagar_unavailable_receipt_requires_complete_later_author_admission() -> None:
    receipt = _json(
        "literature_policies/bhatnagar-2026-impulse-decoding/"
        "paper_reproduction/source-qualification-v1.json"
    )

    route = receipt["later_author_artifact_admission"]
    assert route["status"] == "eligible_when_complete"
    assert set(route["required_fields"]) == {
        "byte_snapshot", "communication_or_access_date", "curve_or_column_identity", "revision",
    }
    assert receipt["pinned_digitization"]["status"] == "eligible_unperformed"
