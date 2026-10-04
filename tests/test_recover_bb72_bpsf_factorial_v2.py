"""Guard the sealed BB72 v2 interruption recovery boundary."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from recover_bb72_bpsf_factorial_v2 import complete_prefix, repair_ledger  # noqa: E402


def _event(kind: str, shot: int) -> bytes:
    return (json.dumps({"kind": kind, "run_id": "sealed-run", "shot_id": shot}) + "\n").encode()


def test_only_trailing_open_shot_is_removed_and_original_is_retained(tmp_path: Path) -> None:
    prefix = _event("shot_begin", 0) + _event("work", 0) + _event("termination", 0)
    raw = prefix + _event("shot_begin", 1) + _event("attempt", 1) + b'{"kind":"work"'
    ledger = tmp_path / "events.jsonl"
    ledger.write_bytes(raw)
    receipt = repair_ledger(ledger, run_id="sealed-run", expected_shots=2, source_job_id="123")
    assert ledger.read_bytes() == prefix
    assert Path(receipt["backup_path"]).read_bytes() == raw
    assert receipt["original_sha256"] == sha256(raw).hexdigest()
    assert receipt["interrupted_shot_id"] == 1
    assert receipt["removed_bytes"] == len(raw) - len(prefix)


def test_complete_ledger_is_unchanged(tmp_path: Path) -> None:
    raw = _event("shot_begin", 0) + _event("termination", 0)
    ledger = tmp_path / "events.jsonl"
    ledger.write_bytes(raw)
    receipt = repair_ledger(ledger, run_id="sealed-run", expected_shots=1, source_job_id="123")
    assert ledger.read_bytes() == raw
    assert receipt["interrupted_shot_id"] is None
    assert list(tmp_path.glob("events.interrupted-*")) == []


def test_partial_next_begin_after_completed_shot_is_preserved_then_trimmed(tmp_path: Path) -> None:
    prefix = _event("shot_begin", 0) + _event("termination", 0)
    ledger = tmp_path / "events.jsonl"
    ledger.write_bytes(prefix + b'{"data":')
    receipt = repair_ledger(ledger, run_id="sealed-run", expected_shots=2, source_job_id="123")
    assert ledger.read_bytes() == prefix
    assert receipt["interrupted_shot_id"] == 1


@pytest.mark.parametrize("raw", [
    _event("shot_begin", 0) + _event("termination", 0) + _event("shot_begin", 2),
    _event("shot_begin", 0) + _event("shot_begin", 0),
    _event("shot_begin", 0) + _event("work", 1),
    _event("shot_begin", 0) + _event("termination", 0) + _event("work", 1),
    _event("shot_begin", 0).replace(b"sealed-run", b"foreign-run"),
])
def test_conflicting_or_nontrailing_content_fails_closed(raw: bytes) -> None:
    with pytest.raises(ValueError):
        complete_prefix(raw, run_id="sealed-run", expected_shots=2)
