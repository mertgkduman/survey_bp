"""Bounded, content-addressed semantic trace sidecars.

Trace collection is intentionally an observer: it can drop optional records,
but it has no callable path into the decoding kernel or its control decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from typing import Any, Literal, Mapping

import numpy as np


TRACE_VERSION = 1
_MAX_RECORDS = 1_000_000
_MAX_BYTES = 64 * 1024 * 1024
_MEASUREMENT_ONLY_FIELDS = frozenset({
    "adapter_overhead", "elapsed_ns", "measurement_time", "peak_host_memory",
    "process_cpu_time", "profile_overhead", "runtime", "timestamp", "wall_time",
    "wall_time_ns",
})


def _canonical_value(value: object) -> object:
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in "biuf" or not np.isfinite(value).all():
            raise ValueError("typed trace arrays must have finite numeric values")
        return {"typed_array": {"dtype": str(value.dtype), "shape": list(value.shape), "values": value.tolist()}}
    if isinstance(value, np.generic):
        return _canonical_value(value.item())
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("trace payload values must be finite")
        return value
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    raise ValueError(f"trace payload is not canonical JSON or a typed array: {type(value).__name__}")


def _json_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(_canonical_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        encoded.decode("utf-8")
    except (TypeError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("trace payload is not valid UTF-8 JSON") from error
    return encoded


def _semantic_value(value: object) -> object:
    """Remove observation-only timing/resource values from a trace identity."""
    if isinstance(value, Mapping):
        return {
            str(key): _semantic_value(item)
            for key, item in value.items()
            if str(key) not in _MEASUREMENT_ONLY_FIELDS
        }
    if isinstance(value, (tuple, list)):
        return [_semantic_value(item) for item in value]
    return value


def semantic_digest(records: Mapping[str, object] | tuple[Mapping[str, object], ...] | list[Mapping[str, object]]) -> str:
    """Hash bounded trace semantics while intentionally excluding measurement fields.

    This identity is for replay agreement only.  It neither suppresses the
    raw measurement evidence nor gives a trace observer any control-flow role.
    """
    if not isinstance(records, (Mapping, tuple, list)):
        raise ValueError("semantic trace digest requires a mapping or ordered mapping records")
    return sha256(_json_bytes(_semantic_value(records))).hexdigest()


def _relative_path(relative: str | Path) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("trace destination must be a nonempty relative confined path")
    return path


def _confined_root(root: str | Path, relative: str | Path, *, create: bool) -> Path:
    base = Path(root).resolve(strict=True)
    if not base.is_dir():
        raise ValueError("trace root must be an existing directory")
    relative_path = _relative_path(relative)
    cursor = base
    for part in relative_path.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise ValueError("trace path may not traverse a symlink")
        if create:
            cursor.mkdir(exist_ok=True)
        if cursor.is_symlink() or not cursor.resolve(strict=True).is_relative_to(base):
            raise ValueError("trace path escapes confined root")
    return cursor


@dataclass(frozen=True)
class TracePlan:
    """Explicit optional-observation policy with non-campaign development defaults."""

    root: Path
    level: Literal["off", "full", "filtered"] = "full"
    relative_dir: str = "trace-sidecars"
    iterations: frozenset[int] | None = None
    edges: frozenset[str] | None = None
    max_records: int = 10_000
    max_bytes: int = 1_000_000
    label: Literal["development_default", "prespecified_campaign"] = "development_default"

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))
        _relative_path(self.relative_dir)
        if self.level not in {"off", "full", "filtered"}:
            raise ValueError("unknown trace level")
        if type(self.max_records) is not int or not 0 <= self.max_records <= _MAX_RECORDS:
            raise ValueError("trace record cap must be a bounded nonnegative integer")
        if type(self.max_bytes) is not int or not 0 <= self.max_bytes <= _MAX_BYTES:
            raise ValueError("trace byte cap must be a bounded nonnegative integer")
        truncation_bytes = len(_json_bytes({"trace_version": TRACE_VERSION, "records": [], "truncated": True, "dropped_records": 1}))
        if self.level != "off" and self.max_bytes < truncation_bytes:
            raise ValueError("trace byte cap cannot hold the required truncation fact")
        if self.iterations is not None and any(type(item) is not int or item < 0 for item in self.iterations):
            raise ValueError("trace iteration filters must be nonnegative integers")
        if self.edges is not None and any(not isinstance(item, str) or not item for item in self.edges):
            raise ValueError("trace edge filters must be nonempty strings")

    @classmethod
    def disabled(cls, root: str | Path) -> "TracePlan":
        return cls(root=Path(root), level="off", max_records=0, max_bytes=0)


@dataclass(frozen=True)
class TraceResult:
    sidecar_path: str | None
    sha256: str | None
    records: int
    bytes_written: int
    truncated: bool
    dropped_records: int

    def ledger_link(self) -> dict[str, object] | None:
        if self.sidecar_path is None:
            return None
        return {"path": self.sidecar_path, "sha256": self.sha256, "records": self.records, "bytes": self.bytes_written, "truncated": self.truncated, "dropped_records": self.dropped_records}


class TraceSink:
    """Collect optional records under quotas without changing decoding control flow."""

    def __init__(self, plan: TracePlan):
        self.plan = plan
        self._records: list[dict[str, object]] = []
        self._truncated = False
        self._dropped = 0
        self._finished: TraceResult | None = None

    def _selected(self, iteration: int | None, edge: str | None) -> bool:
        if self.plan.level == "off":
            return False
        if self.plan.level == "full":
            return True
        return ((self.plan.iterations is None or iteration in self.plan.iterations) and (self.plan.edges is None or edge in self.plan.edges))

    def observe(self, *, kind: str, payload: Mapping[str, object], iteration: int | None = None, edge: str | None = None) -> None:
        if self._finished is not None:
            raise ValueError("trace sink is already finalized")
        if not isinstance(kind, str) or not kind:
            raise ValueError("trace record kind must be nonempty")
        if iteration is not None and (type(iteration) is not int or iteration < 0):
            raise ValueError("trace iteration must be a nonnegative integer")
        if edge is not None and (not isinstance(edge, str) or not edge):
            raise ValueError("trace edge must be a nonempty string")
        record: dict[str, object] = {"kind": kind, "payload": _canonical_value(dict(payload))}
        if iteration is not None:
            record["iteration"] = iteration
        if edge is not None:
            record["edge"] = edge
        # Validate before filtering so no malformed payload can later be linked durably.
        _json_bytes(record)
        if not self._selected(iteration, edge):
            return
        prospective = self._records + [record]
        document = {"trace_version": TRACE_VERSION, "records": prospective, "truncated": self._truncated, "dropped_records": self._dropped}
        if len(prospective) > self.plan.max_records or len(_json_bytes(document)) > self.plan.max_bytes:
            self._truncated = True
            self._dropped += 1
            # A cap includes the explicit overflow evidence itself. If required,
            # discard previously retained optional records to preserve that fact.
            while self._records and len(_json_bytes({"trace_version": TRACE_VERSION, "records": self._records, "truncated": True, "dropped_records": self._dropped})) > self.plan.max_bytes:
                self._records.pop()
                self._dropped += 1
            return
        self._records.append(record)

    def finish(self) -> TraceResult:
        if self._finished is not None:
            return self._finished
        if self.plan.level == "off" or (not self._records and not self._truncated):
            self._finished = TraceResult(None, None, 0, 0, self._truncated, self._dropped)
            return self._finished
        payload = {"trace_version": TRACE_VERSION, "records": self._records, "truncated": self._truncated, "dropped_records": self._dropped}
        raw = _json_bytes(payload)
        if len(raw) > self.plan.max_bytes:
            raise ValueError("trace sidecar exceeded its declared byte cap")
        digest = sha256(raw).hexdigest()
        directory = _confined_root(self.plan.root, self.plan.relative_dir, create=True)
        leaf = directory / f"{digest}.json"
        if leaf.exists():
            if leaf.is_symlink() or leaf.read_bytes() != raw:
                raise ValueError("content-addressed trace sidecar conflicts with existing file")
        else:
            try:
                with leaf.open("xb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
            except FileExistsError:
                if leaf.is_symlink() or leaf.read_bytes() != raw:
                    raise ValueError("content-addressed trace sidecar conflicts with existing file")
        relative = leaf.relative_to(Path(self.plan.root).resolve(strict=True)).as_posix()
        self._finished = TraceResult(relative, digest, len(self._records), len(raw), self._truncated, self._dropped)
        return self._finished

    @staticmethod
    def load(root: str | Path, sidecar_path: str | Path, *, expected_sha256: str | None = None) -> dict[str, object]:
        relative = _relative_path(sidecar_path)
        base = Path(root).resolve(strict=True)
        candidate = base / relative
        cursor = base
        for part in relative.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise ValueError("trace path may not traverse a symlink")
        if not candidate.exists() or not candidate.is_file():
            raise ValueError("trace sidecar does not exist")
        raw = candidate.read_bytes()
        digest = sha256(raw).hexdigest()
        if expected_sha256 is not None and digest != expected_sha256:
            raise ValueError("trace sidecar SHA-256 does not match expected digest")
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("trace sidecar is not valid UTF-8 JSON") from error
        if not isinstance(decoded, dict) or decoded.get("trace_version") != TRACE_VERSION or not isinstance(decoded.get("records"), list):
            raise ValueError("trace sidecar has invalid schema")
        return decoded
