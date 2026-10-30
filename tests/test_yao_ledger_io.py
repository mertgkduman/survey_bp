"""Compressed event ledgers retain the exact bytes committed by the runner."""

from __future__ import annotations

import importlib.util
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest


PATH = Path(__file__).resolve().parents[1] / "data/reproductions/yao-2312-10950-non-osd/ledger_io.py"
SPEC = importlib.util.spec_from_file_location("yao_ledger_io", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
COMPRESS_SPEC = importlib.util.spec_from_file_location("yao_compress_completed", PATH.with_name("compress_completed.py"))
assert COMPRESS_SPEC and COMPRESS_SPEC.loader
COMPRESS = importlib.util.module_from_spec(COMPRESS_SPEC)
COMPRESS_SPEC.loader.exec_module(COMPRESS)


def test_plain_and_compressed_ledger_read_identically(tmp_path: Path) -> None:
    plain = tmp_path / "events.jsonl"
    content = b'{"shot":0}\n{"shot":1}\n'
    plain.write_bytes(content)
    with MODULE.open_event_ledger(plain) as stream:
        assert stream.read() == content
    compressed = tmp_path / "events.jsonl.zst"
    subprocess.run(["zstd", "-q", "-3", "-o", str(compressed), str(plain)], check=True)
    with pytest.raises(ValueError, match="both plain and compressed"):
        with MODULE.open_event_ledger(plain):
            pass
    plain.unlink()
    with MODULE.open_event_ledger(plain) as stream:
        assert stream.read() == content


def test_corrupt_compressed_ledger_fails_closed(tmp_path: Path) -> None:
    plain = tmp_path / "events.jsonl"
    (tmp_path / "events.jsonl.zst").write_bytes(b"not a zstd stream")
    with pytest.raises(ValueError, match="decompression failed"):
        with MODULE.open_event_ledger(plain) as stream:
            stream.read()


def test_compression_requires_matching_summary_and_preserves_raw_digest(tmp_path: Path) -> None:
    plain = tmp_path / "events.jsonl"
    content = b'{"shot":0}\n{"shot":1}\n'
    plain.write_bytes(content)
    summary = tmp_path / "summary.json"
    summary.write_text(json.dumps({"events_sha256": "wrong"}))
    with pytest.raises(ValueError, match="does not match summary"):
        COMPRESS.compress(tmp_path)
    summary.write_text(json.dumps({"events_sha256": sha256(content).hexdigest()}))
    assert COMPRESS.compress(tmp_path) == "compressed"
    assert not plain.exists()
    with MODULE.open_event_ledger(plain) as stream:
        assert sha256(stream.read()).hexdigest() == sha256(content).hexdigest()
    assert COMPRESS.compress(tmp_path) == "not_complete_or_already_compressed"


def test_large_compressed_ledger_splits_and_round_trips_exactly(tmp_path: Path) -> None:
    plain = tmp_path / "events.jsonl"
    content = b"".join(f'{{"shot":{index},"value":"{index % 13}"}}\n'.encode()
                       for index in range(1000))
    plain.write_bytes(content)
    (tmp_path / "summary.json").write_text(json.dumps({"events_sha256": sha256(content).hexdigest()}))
    assert COMPRESS.compress(tmp_path) == "compressed"
    assert COMPRESS.split_compressed(tmp_path, max_part_bytes=100) == "split"
    receipt = json.loads((tmp_path / "compression.json").read_text())
    assert len(receipt["parts"]) > 1
    assert not (tmp_path / "events.jsonl.zst").exists()
    assert all(item["bytes"] <= 100 for item in receipt["parts"])
    with MODULE.open_event_ledger(plain) as stream:
        assert stream.read() == content
    assert COMPRESS.split_compressed(tmp_path, max_part_bytes=100) == "already_split"
    part = tmp_path / receipt["parts"][0]["path"]
    part.write_bytes(b"corrupted" + part.read_bytes())
    with pytest.raises(ValueError, match="wrong size"):
        COMPRESS.split_compressed(tmp_path, max_part_bytes=100)
