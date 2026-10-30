"""Losslessly compress completed shot ledgers after verifying summary hashes."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def _digest_stream(stream) -> str:
    digest = sha256()
    for chunk in iter(lambda: stream.read(1024*1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def compress(directory: Path) -> str:
    summary_path = directory / "summary.json"
    plain = directory / "events.jsonl"
    compressed = directory / "events.jsonl.zst"
    if not summary_path.exists() or not plain.exists():
        return "not_complete_or_already_compressed"
    if compressed.exists() or compressed.with_suffix(compressed.suffix+".partial").exists():
        raise FileExistsError(f"compression output already exists: {directory}")
    summary = json.loads(summary_path.read_text())
    with plain.open("rb") as stream:
        original_hash = _digest_stream(stream)
    if original_hash != summary["events_sha256"]:
        raise ValueError(f"original ledger does not match summary: {directory}")
    temporary = compressed.with_suffix(compressed.suffix+".partial")
    subprocess.run(["zstd", "-q", "-3", "-T1", "-o", str(temporary), str(plain)], check=True)
    process = subprocess.Popen(["zstd", "-q", "-dc", str(temporary)], stdout=subprocess.PIPE)
    assert process.stdout is not None
    with process.stdout:
        restored_hash = _digest_stream(process.stdout)
    if process.wait() != 0 or restored_hash != original_hash:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"compressed ledger did not restore exactly: {directory}")
    temporary.rename(compressed)
    receipt = {"schema": "yao-ledger-compression-v1", "codec": "zstd -3 -T1",
               "raw_sha256": original_hash, "compressed_sha256": sha256(compressed.read_bytes()).hexdigest(),
               "raw_bytes": plain.stat().st_size, "compressed_bytes": compressed.stat().st_size}
    (directory / "compression.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    plain.unlink()
    return "compressed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="all completed completion-* and complete-* directories")
    parser.add_argument("--dir", type=Path)
    args = parser.parse_args()
    if args.all == (args.dir is not None):
        parser.error("choose exactly one of --all and --dir")
    if args.dir is not None:
        directories = [args.dir]
    else:
        directories = sorted([*RESULTS.glob("completion-*/"), *RESULTS.glob("complete-*/")])
    for directory in directories:
        status = compress(directory)
        if status == "compressed":
            print(directory, status, flush=True)
