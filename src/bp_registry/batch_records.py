"""Canonical JSONL batch records with content binding and exclusive publication."""
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def encode_records(records):
    records = json.loads(canonical_json(records))
    records[0].pop("ledger_sha256", None)
    digest = sha256(canonical_json(records).encode()).hexdigest()
    records[0]["ledger_sha256"] = digest
    return canonical_json(records)


def validate_records(encoded, schema):
    records = json.loads(encoded)
    if not isinstance(records, list) or not records or records[0].get("schema") != schema:
        raise ValueError("invalid batch ledger schema")
    if encode_records(records) != canonical_json(records):
        raise ValueError("batch ledger content binding mismatch; replay rejected")
    if any(row.get("shot") != i for i, row in enumerate(records[1:])):
        raise ValueError("batch ledger shot sequence mismatch")
    return records


def write_records(path, encoded, schema):
    records = validate_records(encoded, schema)
    destination = Path(path)
    # Write completely before publishing; a failed call never leaves a partial
    # ledger at the requested path. The hard link is an atomic no-replace step.
    fd, temporary = tempfile.mkstemp(prefix=".batch-", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            for row in records:
                stream.write(canonical_json(row) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
    finally:
        os.unlink(temporary)


def read_records(path, schema):
    return validate_records(canonical_json([json.loads(line) for line in Path(path).read_text().splitlines()]), schema)
