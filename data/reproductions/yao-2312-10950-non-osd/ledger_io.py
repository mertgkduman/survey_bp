"""Read an immutable shot ledger as bytes, plain or losslessly zstd-compressed."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
from typing import BinaryIO, Iterator


@contextmanager
def open_event_ledger(plain_path: Path) -> Iterator[BinaryIO]:
    compressed_path = plain_path.with_name(plain_path.name + ".zst")
    receipt_path = plain_path.with_name("compression.json")
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    parts = receipt.get("parts", [])
    if plain_path.exists():
        if compressed_path.exists() or parts:
            raise ValueError(f"both plain and compressed ledgers exist: {plain_path}")
        with plain_path.open("rb") as stream:
            yield stream
        return
    if compressed_path.exists() and parts:
        raise ValueError(f"both whole and split compressed ledgers exist: {plain_path}")
    if not compressed_path.exists() and not parts:
        raise FileNotFoundError(plain_path)
    cat = None
    if parts:
        paths = [plain_path.parent / item["path"] for item in parts]
        if any(path.parent != plain_path.parent or not path.exists() for path in paths):
            raise ValueError(f"split compressed ledger has missing/unsafe parts: {plain_path}")
        cat = subprocess.Popen(["cat", *map(str, paths)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert cat.stdout is not None
        process = subprocess.Popen(["zstd", "-q", "-dc"], stdin=cat.stdout,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cat.stdout.close()
    else:
        process = subprocess.Popen(["zstd", "-q", "-dc", str(compressed_path)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    try:
        yield process.stdout
        process.stdout.close()
        stderr = process.stderr.read().decode() if process.stderr is not None else ""
        status = process.wait()
        if cat is not None:
            cat_stderr = cat.stderr.read().decode() if cat.stderr is not None else ""
            if cat.wait() != 0:
                raise ValueError(f"split compressed ledger concatenation failed: {cat_stderr}")
        if status != 0:
            raise ValueError(f"zstd decompression failed: {compressed_path}: {stderr}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stderr is not None:
            process.stderr.close()
        if cat is not None:
            if cat.poll() is None:
                cat.kill()
                cat.wait()
            if cat.stderr is not None:
                cat.stderr.close()
