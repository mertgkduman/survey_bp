#!/usr/bin/env python3
"""Resume the sealed BB72 v2 arm after an interrupted Slurm allocation.

Only a trailing, unterminated shot may be removed. The exact original ledger is
retained beside it, and the public canonical runner rechecks all earlier shots.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from bp_registry.cli import run_canonical, verify_run  # noqa: E402
from run_bb72_bpsf_factorial_v2 import OUTPUT, check_seal, prepare  # noqa: E402


ARM = OUTPUT / "p080" / "ms-g1000-bpsf20plus4x5"
EXPECTED_SHOTS = 1280


def _digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def complete_prefix(raw: bytes, *, run_id: str, expected_shots: int) -> tuple[bytes, int | None]:
    """Return a whole-shot prefix and the ID of its sole trailing open shot."""
    if not raw:
        return raw, None
    if not isinstance(run_id, str) or not run_id or expected_shots < 1:
        raise ValueError("invalid recovery contract")
    offset = 0
    current: int | None = None
    current_begin = 0
    next_shot = 0
    for line in raw.splitlines(keepends=True):
        if not line.endswith(b"\n"):
            if current is None:
                if next_shot == expected_shots:
                    raise ValueError("trailing bytes follow the full denominator")
                return raw[:offset], next_shot
            break
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            if current is None:
                raise ValueError("malformed event has no open shot") from error
            break
        if not isinstance(event, dict) or event.get("run_id") != run_id:
            raise ValueError("ledger contains a foreign or invalid run")
        kind, shot_id = event.get("kind"), event.get("shot_id")
        if type(shot_id) is not int or not 0 <= shot_id < expected_shots:
            raise ValueError("ledger shot ID is outside the frozen denominator")
        if current is None:
            if kind != "shot_begin" or shot_id != next_shot:
                raise ValueError("complete shot prefix is not consecutive")
            current = shot_id
            current_begin = offset
        elif shot_id != current or kind == "shot_begin":
            raise ValueError("shot events are interleaved or duplicated")
        offset += len(line)
        if kind == "termination":
            current = None
            next_shot += 1
    if current is None:
        if offset != len(raw) or next_shot != expected_shots:
            raise ValueError("ledger ended between shots before its denominator")
        return raw, None
    if next_shot == expected_shots:
        raise ValueError("open shot follows the full denominator")
    return raw[:current_begin], current


def repair_ledger(path: Path, *, run_id: str, expected_shots: int, source_job_id: str) -> dict:
    raw = path.read_bytes()
    prefix, interrupted_shot = complete_prefix(raw, run_id=run_id, expected_shots=expected_shots)
    receipt = {
        "schema_version": 1,
        "source_job_id": source_job_id,
        "run_id": run_id,
        "original_sha256": _digest(raw),
        "resumed_prefix_sha256": _digest(prefix),
        "interrupted_shot_id": interrupted_shot,
        "removed_bytes": len(raw) - len(prefix),
    }
    if interrupted_shot is None:
        return receipt
    backup = path.with_name(f"events.interrupted-{_digest(raw)[:16]}.jsonl")
    if backup.exists():
        if _digest(backup.read_bytes()) != _digest(raw):
            raise ValueError("interrupted ledger backup conflicts")
    else:
        shutil.copyfile(path, backup)
        if _digest(backup.read_bytes()) != _digest(raw):
            raise ValueError("interrupted ledger backup was not durable")
    receipt["backup_path"] = str(backup)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix="events.repair-", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(prefix)
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, path)
    if _digest(path.read_bytes()) != receipt["resumed_prefix_sha256"]:
        raise ValueError("repaired ledger differs from retained prefix")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-job-id", required=True)
    args = parser.parse_args()
    check_seal()
    paths = prepare()
    matches = [(manifest, root) for manifest, root in paths if root == ARM]
    if len(matches) != 1:
        raise ValueError("frozen final arm was not prepared exactly once")
    manifest, root = matches[0]
    identity = json.loads(manifest.read_text(encoding="utf-8"))["run_id"]
    if (root / "result.json").exists():
        result = verify_run(root)
        if result["final_row_count"] != EXPECTED_SHOTS:
            raise ValueError("existing final arm has wrong denominator")
        print("final arm already verified", flush=True)
        return
    ledger = root / "events.jsonl"
    if not ledger.exists():
        raise ValueError("original sealed arm ledger is missing")
    receipt = repair_ledger(ledger, run_id=identity, expected_shots=EXPECTED_SHOTS,
                            source_job_id=args.source_job_id)
    receipt_path = root / f"recovery-{args.source_job_id}.json"
    payload = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    if receipt_path.exists() and receipt_path.read_bytes() != payload:
        raise ValueError("recovery receipt conflicts")
    receipt_path.write_bytes(payload)
    print(json.dumps(receipt, sort_keys=True), flush=True)
    run_canonical(manifest, root)
    result = verify_run(root)
    if result["final_row_count"] != EXPECTED_SHOTS:
        raise ValueError("recovered final arm has wrong denominator")
    print("recovered final arm verified", flush=True)


if __name__ == "__main__":
    main()
