"""Read an immutable shot ledger as bytes, plain or losslessly zstd-compressed."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import subprocess
from typing import BinaryIO, Iterator


@contextmanager
def open_event_ledger(plain_path: Path) -> Iterator[BinaryIO]:
    compressed_path = plain_path.with_name(plain_path.name + ".zst")
    if plain_path.exists():
        if compressed_path.exists():
            raise ValueError(f"both plain and compressed ledgers exist: {plain_path}")
        with plain_path.open("rb") as stream:
            yield stream
        return
    if not compressed_path.exists():
        raise FileNotFoundError(plain_path)
    process = subprocess.Popen(["zstd", "-q", "-dc", str(compressed_path)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    try:
        yield process.stdout
        process.stdout.close()
        stderr = process.stderr.read().decode() if process.stderr is not None else ""
        if process.wait() != 0:
            raise ValueError(f"zstd decompression failed: {compressed_path}: {stderr}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stderr is not None:
            process.stderr.close()
