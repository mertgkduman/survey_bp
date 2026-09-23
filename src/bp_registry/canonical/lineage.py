"""Stable, typed append-only lineage identifiers for canonical execution."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Literal


LineageKind = Literal["original", "working", "attempt", "candidate"]


@dataclass(frozen=True, order=True)
class LineageId:
    kind: LineageKind
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("lineage values must be nonempty")


@dataclass(frozen=True)
class LineageEdge:
    relation: Literal["identity", "attempt", "candidate"]
    parent: LineageId
    child: LineageId


def stable_lineage_id(kind: LineageKind, payload: object) -> LineageId:
    """Content identity intentionally excludes arrival order and elapsed time."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return LineageId(kind, f"{kind}-{sha256(encoded.encode()).hexdigest()[:20]}")
