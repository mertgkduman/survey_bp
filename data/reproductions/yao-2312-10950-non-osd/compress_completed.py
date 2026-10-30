"""Losslessly compress completed shot ledgers after verifying summary hashes."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
MAX_GIT_PART_BYTES = 64 * 1024 * 1024


def _digest_stream(stream) -> str:
    digest = sha256()
    for chunk in iter(lambda: stream.read(1024*1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _verify_parts(directory: Path, parts: list[dict], expected_sha256: str) -> None:
    combined = sha256()
    for item in parts:
        path = directory / item["path"]
        if not path.exists() or path.stat().st_size != item["bytes"]:
            raise ValueError(f"compressed-ledger part missing or wrong size: {path}")
        digest = sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024*1024), b""):
                digest.update(block)
                combined.update(block)
        if digest.hexdigest() != item["sha256"]:
            raise ValueError(f"compressed-ledger part hash mismatch: {path}")
    if combined.hexdigest() != expected_sha256:
        raise ValueError("compressed-ledger concatenation hash mismatch")


def split_compressed(directory: Path, *, max_part_bytes: int = MAX_GIT_PART_BYTES) -> str:
    """Split a verified zstd frame into ordered, individually hashable Git-sized parts."""
    if max_part_bytes < 1:
        raise ValueError("max_part_bytes must be positive")
    compressed = directory / "events.jsonl.zst"
    receipt_path = directory / "compression.json"
    receipt = json.loads(receipt_path.read_text())
    if "parts" in receipt:
        parts = receipt["parts"]
        if not parts:
            raise ValueError("compressed-ledger receipt has no parts")
        _verify_parts(directory, parts, receipt["compressed_sha256"])
        if compressed.exists():
            compressed.unlink()  # Recover an interrupted final unlink after receipt commit.
        return "already_split"
    if not compressed.exists():
        raise FileNotFoundError(compressed)
    if compressed.stat().st_size <= max_part_bytes:
        return "not_needed"
    with compressed.open("rb") as source:
        if _digest_stream(source) != receipt["compressed_sha256"]:
            raise ValueError("compressed ledger differs from its receipt")
    if list(directory.glob("events.jsonl.zst.part-*")):
        raise FileExistsError("orphan compressed-ledger parts require inspection")
    parts = []
    combined = sha256()
    with compressed.open("rb") as source:
        index = 0
        while True:
            block = source.read(max_part_bytes)
            if not block:
                break
            name = f"events.jsonl.zst.part-{index:03d}"
            temporary = directory / (name + ".partial")
            temporary.write_bytes(block)
            combined.update(block)
            parts.append({"path": name, "bytes": len(block),
                          "sha256": sha256(block).hexdigest()})
            index += 1
    if combined.hexdigest() != receipt["compressed_sha256"]:
        raise ValueError("compressed-part concatenation differs from original")
    for item in parts:
        (directory / (item["path"] + ".partial")).rename(directory / item["path"])
    _verify_parts(directory, parts, receipt["compressed_sha256"])
    updated = {**receipt, "parts": parts}
    temporary_receipt = receipt_path.with_suffix(".json.partial")
    temporary_receipt.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n")
    temporary_receipt.replace(receipt_path)
    compressed.unlink()
    return "split"


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
    split_compressed(directory)
    return "compressed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="all completed completion-* and complete-* directories")
    parser.add_argument("--dir", type=Path)
    parser.add_argument("--split-existing", type=Path,
                        help="split a previously compressed ledger above the per-file limit")
    args = parser.parse_args()
    if sum((args.all, args.dir is not None, args.split_existing is not None)) != 1:
        parser.error("choose exactly one of --all, --dir, and --split-existing")
    if args.split_existing is not None:
        print(args.split_existing, split_compressed(args.split_existing))
        raise SystemExit(0)
    if args.dir is not None:
        directories = [args.dir]
    else:
        directories = sorted([*RESULTS.glob("completion-*/"), *RESULTS.glob("complete-*/")])
    for directory in directories:
        status = compress(directory)
        if status == "compressed":
            print(directory, status, flush=True)
