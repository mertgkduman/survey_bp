"""Durable, versioned JSONL accounting for individual decoder shots."""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
from typing import Any, Iterator, Mapping
from uuid import uuid4

try:
    import fcntl
except ImportError as error:  # pragma: no cover - Phase 1 targets POSIX HPC hosts.
    raise RuntimeError("the Phase 1 local ledger requires POSIX advisory locks") from error


LEDGER_VERSION = 1
ShotKey = tuple[str, int]


class ShotOwnershipError(ValueError):
    """A live process already owns this stable run/shot identity."""


def _key(run_id: str, shot_id: int) -> ShotKey:
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id must be a nonempty string")
    if type(shot_id) is not int or shot_id < 0:
        raise ValueError("shot_id must be a nonnegative integer")
    return run_id, shot_id


def _owner_lock_path(path: Path, key: ShotKey) -> Path:
    encoded = json.dumps(key, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return path.with_name(f".{path.name}.{sha256(encoded).hexdigest()}.owner.lock")


@contextmanager
def _journal_lock(path: Path) -> Iterator[None]:
    lock_path = path.with_name(f".{path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _try_owner_lock(path: Path, key: ShotKey) -> Any | None:
    lock_path = _owner_lock_path(path, key)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None
    return handle


def _release_owner(handle: Any) -> None:
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def _validate_event(event: Mapping[str, Any]) -> None:
    kind = event.get("kind")
    if kind not in {"begin", "terminal"}:
        raise ValueError("ledger event kind must be begin or terminal")
    if event.get("ledger_version") != LEDGER_VERSION:
        raise ValueError(f"unsupported ledger_version {event.get('ledger_version')!r}")
    _key(event.get("run_id"), event.get("shot_id"))
    if kind == "begin":
        owner = event.get("owner")
        valid_owner = isinstance(owner, dict) and all(
            isinstance(owner.get(field), str) and owner[field] for field in ("nonce", "node")
        ) and type(owner.get("pid")) is int
        if not valid_owner:
            raise ValueError("begin event requires owner nonce, node, and pid")
        if not isinstance(event.get("sample_seed_identity"), str) or not event["sample_seed_identity"]:
            raise ValueError("begin event requires a nonempty sample_seed_identity")
    elif not isinstance(event.get("termination"), str) or not event["termination"]:
        raise ValueError("terminal event requires a termination status")


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at line {number}") from error
        if not isinstance(event, dict):
            raise ValueError(f"ledger event at line {number} is not an object")
        _validate_event(event)
        events.append(event)
    return events


def _append_durable(path: Path, event: Mapping[str, Any]) -> None:
    _validate_event(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _states(events: list[dict[str, Any]]) -> tuple[dict[ShotKey, dict[str, Any]], dict[ShotKey, dict[str, Any]]]:
    begun: dict[ShotKey, dict[str, Any]] = {}
    terminal: dict[ShotKey, dict[str, Any]] = {}
    for event in events:
        key = _key(event["run_id"], event["shot_id"])
        if event["kind"] == "begin":
            if key in terminal:
                raise ValueError(f"begin follows terminal for {key!r}")
            previous = begun.get(key)
            if previous is not None and previous != event:
                raise ValueError(f"conflicting duplicate begin for {key!r}")
            begun.setdefault(key, event)
        else:
            if key not in begun:
                raise ValueError(f"terminal without begin for {key!r}")
            previous = terminal.get(key)
            if previous is not None and previous != event:
                raise ValueError(f"conflicting duplicate terminal for {key!r}")
            terminal.setdefault(key, event)
    return begun, terminal


def _terminal_defaults(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Make unavailable facts explicit rather than silently turning them into zero."""

    terminal = dict(fields)
    terminal.setdefault("selected_output", None)
    terminal.setdefault("selection_status", "unavailable")
    terminal.setdefault("native_converged", None)
    terminal.setdefault("native_iterations", None)
    terminal.setdefault("native_edge_updates", None)
    terminal.setdefault("native_internals_unavailable_reason", "not observed in this terminal record")
    terminal.setdefault("outcome", None)
    if terminal["outcome"] is None:
        terminal.setdefault("outcome_unavailable_reason", "outcome was not evaluated")
    terminal.setdefault("postselection", "unavailable")
    terminal.setdefault("observed_termination", True)
    return terminal


def _interrupted_terminal(begin: Mapping[str, Any]) -> dict[str, Any]:
    identity = {
        field: begin[field]
        for field in (
            "manifest_sha256", "source_uri", "source_revision", "source_anchor", "code_id",
            "experiment_relation", "expected_output_status", "sample_seed_identity",
            "decoder_config", "decoder_version", "paper_uri", "paper_revision", "paper_anchor",
            "implementation_source_artifact_sha256",
        ) if field in begin
    }
    return {
        "kind": "terminal", "ledger_version": LEDGER_VERSION,
        "run_id": begin["run_id"], "shot_id": begin["shot_id"], **identity,
        **_terminal_defaults({
            "termination": "interrupted",
            "termination_inference": "reconciled_after_owner_release",
            "observed_termination": False,
            "native_internals_unavailable_reason": (
                "owner released without a terminal record; native internals were not observed"
            ),
            "outcome_unavailable_reason": "interrupted before independent evaluation completed",
        }),
    }


class LedgerWriter:
    """Append validated events while retaining per-shot ownership until final fsync."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._owners: dict[ShotKey, Any] = {}

    def begin(self, *, run_id: str, shot_id: int, **fields: Any) -> None:
        key = _key(run_id, shot_id)
        if key in self._owners:
            return
        if "owner" in fields or "ledger_version" in fields:
            raise ValueError("owner and ledger_version are assigned by LedgerWriter")
        owner_handle = _try_owner_lock(self.path, key)
        if owner_handle is None:
            raise ShotOwnershipError(f"shot {key!r} is actively owned by another process")
        event = {
            "kind": "begin", "ledger_version": LEDGER_VERSION, "run_id": run_id, "shot_id": shot_id,
            "owner": {"nonce": uuid4().hex, "node": socket.gethostname(), "pid": os.getpid()}, **fields,
        }
        try:
            with _journal_lock(self.path):
                begun, terminal = _states(_read_events(self.path))
                if key in terminal:
                    raise ValueError(f"shot {key!r} already has a terminal record")
                if key in begun:
                    raise ValueError(f"shot {key!r} has an unresolved begin; reconcile it first")
                _append_durable(self.path, event)
            self._owners[key] = owner_handle
        except BaseException:
            _release_owner(owner_handle)
            raise

    def terminal(self, *, run_id: str, shot_id: int, **fields: Any) -> None:
        key = _key(run_id, shot_id)
        if "ledger_version" in fields or "kind" in fields:
            raise ValueError("terminal kind and ledger_version are assigned by LedgerWriter")
        owner_handle = self._owners.get(key)
        try:
            with _journal_lock(self.path):
                begun, terminal = _states(_read_events(self.path))
                if key not in begun:
                    raise ValueError(f"terminal requires a prior begin for {key!r}")
                event = {
                    "kind": "terminal", "ledger_version": LEDGER_VERSION,
                    "run_id": run_id, "shot_id": shot_id,
                    "sample_seed_identity": begun[key].get("sample_seed_identity"),
                    **_terminal_defaults(fields),
                }
                if key in terminal:
                    if terminal[key] != event:
                        raise ValueError(f"conflicting duplicate terminal for {key!r}")
                    return
                if owner_handle is None:
                    raise ShotOwnershipError(f"shot {key!r} is not owned by this writer")
                _append_durable(self.path, event)
        finally:
            if owner_handle is not None:
                self._owners.pop(key, None)
                _release_owner(owner_handle)

    def append(self, event: Mapping[str, Any]) -> None:
        """Compatibility entry point that still routes through typed lifecycle methods."""

        data = dict(event)
        kind = data.pop("kind", None)
        if data.pop("ledger_version", LEDGER_VERSION) != LEDGER_VERSION:
            raise ValueError("append cannot alter ledger_version")
        if "owner" in data:
            raise ValueError("append cannot alter ownership metadata")
        try:
            run_id, shot_id = data.pop("run_id"), data.pop("shot_id")
        except KeyError as error:
            raise ValueError("ledger event requires run_id and shot_id") from error
        if kind == "begin":
            self.begin(run_id=run_id, shot_id=shot_id, **data)
        elif kind == "terminal":
            self.terminal(run_id=run_id, shot_id=shot_id, **data)
        else:
            raise ValueError("ledger event kind must be begin or terminal")

    def close(self) -> None:
        for key, handle in list(self._owners.items()):
            self._owners.pop(key, None)
            _release_owner(handle)

    def __enter__(self) -> "LedgerWriter":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


Writer = LedgerWriter


def reconcile(path: str | Path) -> list[dict[str, Any]]:
    """Repair abandoned begins only when their per-shot owner lock is free."""

    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with _journal_lock(journal):
        begun, terminal = _states(_read_events(journal))
        for key, begin in begun.items():
            if key in terminal:
                continue
            owner_handle = _try_owner_lock(journal, key)
            if owner_handle is None:
                continue
            try:
                repair = _interrupted_terminal(begin)
                _append_durable(journal, repair)
                terminal[key] = repair
            finally:
                _release_owner(owner_handle)
        return list(terminal.values())


def summarize(path: str | Path) -> dict[str, Any]:
    """Reconstruct all reported counts from terminal rows, never begin rows."""

    final_rows = reconcile(path)
    outcomes = Counter(
        row["outcome"] if row.get("outcome") is not None else "unavailable" for row in final_rows
    )
    return {
        "total_final": len(final_rows),
        "terminations": dict(Counter(row["termination"] for row in final_rows)),
        "outcomes": dict(outcomes),
        "nonconverged": sum(row.get("native_converged") is False for row in final_rows),
        "interrupted": sum(row.get("termination") == "interrupted" for row in final_rows),
        "postselected": sum(row.get("postselection") not in {None, "none", "unavailable"} for row in final_rows),
    }
