"""Qualification contracts for the isolated Phase 7 standalone OSD seam."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "data/qualifications/phase7-standalone-osd-baec4c8.json"
APPROVED_COMMIT = "baec4c8bfa2a679b0ba0e72df5582e277cd6918b"


def test_qualification_receipt_binds_exact_source_build_api_and_primary_environment():
    """Only a passing, immutable receipt may identify the optional worker."""
    assert RECEIPT.is_file(), "the approved OSD source must be qualified before admission"
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert receipt["disposition"] == "passed"
    assert receipt["source"]["commit"] == APPROVED_COMMIT
    assert receipt["source"]["repository"] == "https://github.com/quantumgizmos/ldpc.git"
    assert len(receipt["source"]["tree_sha256"]) == 64
    assert len(receipt["build"]["wheel_sha256"]) == 64
    assert receipt["primary_environment"]["ldpc_version_before"] == "2.4.1"
    assert receipt["primary_environment"]["ldpc_version_after"] == "2.4.1"
    assert receipt["api"]["module"] == "ldpc.osd_decoder"
    assert receipt["api"]["class"] == "OsdDecoder"
    assert {"OSD_0", "OSD_E", "OSD_CS"} <= set(receipt["api"]["methods"])
    assert receipt["fixtures"]["all_syndrome_valid"] is True
    assert receipt["receipt_sha256"] == _digest_without_receipt_sha(receipt)


def _digest_without_receipt_sha(receipt: dict[str, object]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_sha256", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
