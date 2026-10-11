"""Adversarial coverage for immutable source-target receipts."""

from __future__ import annotations

from datetime import date
from hashlib import sha256

import pytest
from pydantic import ValidationError


def _table_receipt():
    from bp_registry.campaigns.targets import (
        ByteSnapshotV1,
        SourceDenominatorV1,
        SourceIdentityV1,
        TableCellLocatorV1,
        TableTargetReceiptV1,
        ValueBoundsV1,
    )

    return TableTargetReceiptV1(
        schema="campaign_table_target_v1",
        target_id="synthetic-table-p010",
        source=SourceIdentityV1(
            uri_or_doi="https://doi.org/10.0000/synthetic",
            revision="published-v1",
            accessed_on=date(2026, 10, 11),
        ),
        location=TableCellLocatorV1(table_id="Table 2", row_id="p=0.010", column_id="LER"),
        source_snapshot=ByteSnapshotV1.from_bytes("papers/synthetic/table-2.csv", b"p,ler\n.01,.02\n"),
        reported=ValueBoundsV1(value=0.02, lower_error=0.003, upper_error=0.004, precision=0.001),
        source_denominator=SourceDenominatorV1(status="unavailable", reason="paper reports no count"),
    )


def test_source_table_round_trip_and_digest_bind_source_precision_and_denominator():
    receipt = _table_receipt()
    encoded = receipt.model_dump_json(by_alias=True)
    assert type(receipt).model_validate_json(encoded) == receipt

    source_changed = receipt.model_copy(
        update={"source_snapshot": type(receipt.source_snapshot).from_bytes("papers/synthetic/table-2.csv", b"p,ler\n.01,.03\n")},
    )
    precision_changed = receipt.model_copy(
        update={"reported": receipt.reported.model_copy(update={"precision": 0.0001})},
    )
    observed = receipt.model_copy(
        update={"source_denominator": type(receipt.source_denominator)(status="observed", count=1000)},
    )
    assert len({receipt.digest(), source_changed.digest(), precision_changed.digest(), observed.digest()}) == 4
    assert receipt.source_snapshot.integrity_statement == "sha256_integrity_linkage_not_authorship_v1"


@pytest.mark.parametrize("path", ["/absolute.csv", "../escape.csv", "paper/../escape.csv"])
def test_source_snapshot_rejects_path_escape(path: str):
    from bp_registry.campaigns.targets import ByteSnapshotV1

    with pytest.raises(ValidationError):
        ByteSnapshotV1.from_bytes(path, b"x")


def test_source_snapshot_rejects_symlink_escape_and_tampering(tmp_path):
    from bp_registry.campaigns.targets import read_confined_snapshot

    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_bytes(b"not evidence")
    (evidence_root / "link.csv").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        read_confined_snapshot(evidence_root, "link.csv")

    source = evidence_root / "table.csv"
    source.write_bytes(b"source bytes")
    snapshot = read_confined_snapshot(evidence_root, "table.csv")
    assert snapshot.sha256 == sha256(b"source bytes").hexdigest()
    source.write_bytes(b"changed bytes")
    assert sha256(source.read_bytes()).hexdigest() != snapshot.sha256


def test_unavailable_denominator_never_infers_an_observed_count():
    from bp_registry.campaigns.targets import SourceDenominatorV1

    unavailable = SourceDenominatorV1(status="unavailable", reason="not published")
    assert unavailable.count is None
    with pytest.raises(ValidationError):
        SourceDenominatorV1(status="unavailable", count=10, reason="not published")
    with pytest.raises(ValidationError):
        SourceDenominatorV1(status="observed")
