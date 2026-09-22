"""Minimal append-only JSONL shot ledger; hardened in Plan 05."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class Writer:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")

    def append(self, event: dict[str, Any]) -> None:
        self._handle.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def begin(self, *, run_id: str, shot_id: int, **fields: Any) -> None:
        self.append({"kind": "begin", "run_id": run_id, "shot_id": shot_id, **fields})

    def terminal(self, *, run_id: str, shot_id: int, **fields: Any) -> None:
        self.append({"kind": "terminal", "run_id": run_id, "shot_id": shot_id, **fields})

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "Writer":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


LedgerWriter = Writer


def reconcile(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    begun: dict[tuple[str, int], dict[str, Any]] = {}
    final: dict[tuple[str, int], dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        key = (event["run_id"], event["shot_id"])
        if event["kind"] == "begin":
            begun.setdefault(key, event)
        elif event["kind"] == "terminal":
            final.setdefault(key, event)
    for key, event in begun.items():
        final.setdefault(key, {"kind": "terminal", "run_id": key[0], "shot_id": key[1],
                               "termination": "interrupted", "observed_termination": False,
                               "manifest_sha256": event.get("manifest_sha256")})
    return list(final.values())
