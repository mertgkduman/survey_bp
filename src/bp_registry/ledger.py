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
CANONICAL_LEDGER_VERSION = 2
CANONICAL_SCHEDULE_LEDGER_VERSION = 3
CANONICAL_RELAY_LEDGER_VERSION = 4
CANONICAL_INTERVENTION_LEDGER_VERSION = 5
CANONICAL_ENSEMBLE_LEDGER_VERSION = 6
CANONICAL_POSTPROCESSING_LEDGER_VERSION = 7
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
    elif "native_metric_facts" in event:
        _native_metric_facts_from_evidence(event["native_metric_facts"])


def _native_metric_facts_from_evidence(value: Any) -> tuple[Any, ...]:
    """Validate a native metric envelope without inferring opaque internals."""
    from .canonical.metrics import MetricFact

    if not isinstance(value, list):
        raise ValueError("native_metric_facts must be a list of typed metric facts")
    facts = tuple(MetricFact.from_evidence(item) for item in value)
    if len({fact.metric for fact in facts}) != len(facts):
        raise ValueError("native_metric_facts cannot contain duplicate metric names")
    return facts


def _unavailable_native_metric_evidence(reason: str) -> list[dict[str, int | float | str | None]]:
    """Record unobserved native internals as facts instead of synthesized counts."""
    from .canonical.metrics import unavailable_metric

    return [
        unavailable_metric(
            metric, method="ledger.reconcile", scope="native_decoder_call", unit=unit,
            qualification="terminal_not_observed", reason=reason,
        ).as_evidence()
        for metric, unit in (
            ("native_iterations", "native_iterations"),
            ("native_edge_updates", "edge_messages"),
            ("native_control_flow_events", "events"),
        )
    ]


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
    if "native_metric_facts" in terminal:
        terminal["native_metric_facts"] = [
            fact.as_evidence() for fact in _native_metric_facts_from_evidence(terminal["native_metric_facts"])
        ]
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
            "implementation_source_artifact_sha256", "artifact_raw_sha256",
            "artifact_semantic_sha256", "artifact_path",
        ) if field in begin
    }
    unavailable_reason = "owner released without a terminal record; native internals were not observed"
    return {
        "kind": "terminal", "ledger_version": LEDGER_VERSION,
        "run_id": begin["run_id"], "shot_id": begin["shot_id"], **identity,
        **_terminal_defaults({
            "termination": "interrupted",
            "termination_inference": "reconciled_after_owner_release",
            "observed_termination": False,
            "native_internals_unavailable_reason": unavailable_reason,
            "native_metric_facts": _unavailable_native_metric_evidence(unavailable_reason),
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
    availability: dict[str, Counter[str]] = {}
    for fact in query_native_metric_facts(path):
        availability.setdefault(fact["metric"], Counter())[fact["missingness"]] += 1
    return {
        "total_final": len(final_rows),
        "terminations": dict(Counter(row["termination"] for row in final_rows)),
        "outcomes": dict(outcomes),
        "nonconverged": sum(row.get("native_converged") is False for row in final_rows),
        "interrupted": sum(row.get("termination") == "interrupted" for row in final_rows),
        "postselected": sum(row.get("postselection") not in {None, "none", "unavailable"} for row in final_rows),
        "native_metric_availability": {
            metric: {
                "observed": counts["observed"],
                "unavailable": counts["unavailable"],
            }
            for metric, counts in sorted(availability.items())
        },
    }


def query_native_metric_facts(
    path: str | Path, *, metric: str | None = None,
) -> list[dict[str, int | float | str | None]]:
    """Return typed terminal facts; unavailable values are never reduced to zero."""
    if metric is not None and (not isinstance(metric, str) or not metric):
        raise ValueError("native metric filter must be a nonempty string")
    result: list[dict[str, int | float | str | None]] = []
    for row in reconcile(path):
        for fact in _native_metric_facts_from_evidence(row.get("native_metric_facts", [])):
            if metric is None or fact.metric == metric:
                result.append({
                    "run_id": row["run_id"], "shot_id": row["shot_id"], **fact.as_evidence(),
                })
    return result


# Canonical CSS structural evidence is a deliberately separate v2 grammar.  It
# is not read by, or conditionally accepted by, the historical v1 shot journal.
_CANONICAL_EVENT_KINDS = frozenset({
    "shot_begin", "attempt", "intervention", "branch", "branch_pruned",
    "relay_transfer", "candidate", "fallback", "selection", "termination",
    "work", "runtime", "missingness", "trace_link", "trace_truncated",
    "transform", "lift", "original_check", "evaluation",
    "basis", "member", "candidate_origin", "duplicate_group", "work_leaf",
    "bp_only", "final",
})


def _canonical_event_bytes(event: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(dict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValueError("canonical event must contain finite UTF-8 JSON values") from error


def _validate_canonical_event(event: Mapping[str, Any]) -> None:
    if event.get("ledger_version") not in {
        CANONICAL_LEDGER_VERSION, CANONICAL_SCHEDULE_LEDGER_VERSION, CANONICAL_RELAY_LEDGER_VERSION,
        CANONICAL_INTERVENTION_LEDGER_VERSION, CANONICAL_ENSEMBLE_LEDGER_VERSION,
        CANONICAL_POSTPROCESSING_LEDGER_VERSION,
    }:
        raise ValueError("unsupported canonical ledger version")
    if event.get("kind") not in _CANONICAL_EVENT_KINDS:
        raise ValueError("unknown canonical structural event kind")
    _key(event.get("run_id"), event.get("shot_id"))
    if not isinstance(event.get("event_id"), str) or not event["event_id"]:
        raise ValueError("canonical event requires a stable event_id")
    if event["kind"] == "shot_begin" and (not isinstance(event.get("sample_seed_identity"), str) or not event["sample_seed_identity"]):
        raise ValueError("canonical shot_begin requires a sample_seed_identity")
    if event["kind"] == "termination" and (not isinstance(event.get("termination"), str) or not event["termination"]):
        raise ValueError("canonical termination event requires a termination status")
    data = event.get("data", {})
    if not isinstance(data, dict):
        raise ValueError("canonical event data must be an object")
    if event.get("ledger_version") == CANONICAL_INTERVENTION_LEDGER_VERSION:
        from .canonical.budgets import WorkVector

        if event["kind"] == "shot_begin":
            if (set(data) != {"schema_version", "compact_schema_version", "identity", "payload"}
                    or data["schema_version"] != 5 or data["compact_schema_version"] not in {6, 7}):
                raise ValueError("intervention shot_begin requires a registered compact contract version")
        elif set(data) != {"identity", "payload"}:
            raise ValueError("V5 intervention event requires exact identity and payload fields")
        if not isinstance(data.get("identity"), dict) or not isinstance(data.get("payload"), dict):
            raise ValueError("V5 intervention identity and payload must be objects")
        if event["kind"] == "work":
            payload = data["payload"]
            if set(payload) != {"work_vector", "leaves"} or not isinstance(payload["leaves"], list):
                raise ValueError("V5 work requires vector and exact leaf list")
            WorkVector.from_evidence(payload["work_vector"], structural_event_version=4)
            seen: set[str] = set()
            for leaf in payload["leaves"]:
                if not isinstance(leaf, dict) or set(leaf) != {"leaf_id", "scope", "work_vector"}:
                    raise ValueError("V5 work leaf has an invalid exact field set")
                if not isinstance(leaf["leaf_id"], str) or not leaf["leaf_id"] or leaf["leaf_id"] in seen:
                    raise ValueError("V5 work leaves require unique stable IDs")
                if leaf["scope"] != "attempt":
                    raise ValueError("V5 work leaf requires attempt scope")
                WorkVector.from_evidence(leaf["work_vector"], structural_event_version=4)
                seen.add(leaf["leaf_id"])
    if event.get("ledger_version") == CANONICAL_ENSEMBLE_LEDGER_VERSION:
        if event["kind"] == "shot_begin":
            if (set(data) != {"schema_version", "identity", "payload"}
                    or data["schema_version"] != 7):
                raise ValueError("ensemble shot_begin requires the V7 public contract")
        elif set(data) != {"identity", "payload"}:
            raise ValueError("V6 ensemble event requires exact identity and payload fields")
        if not isinstance(data.get("identity"), dict) or not isinstance(data.get("payload"), dict):
            raise ValueError("V6 ensemble identity and payload must be objects")
    if event.get("ledger_version") == CANONICAL_RELAY_LEDGER_VERSION:
        if event["kind"] == "shot_begin" and data.get("schema_version") != 4:
            raise ValueError("V4 Relay ledger evidence requires a V4 manifest declaration")
        if event["kind"] == "relay_transfer":
            required = {
                "representation", "vector_length", "producer_leg_lineage_id", "numerical_profile",
                "clipping_evidence", "digest", "relay_leaf_id",
            }
            if not required.issubset(data) or data["representation"] != "llr_log_p0_over_p1":
                raise ValueError("V4 Relay transfers require exact posterior and leaf evidence")
            if type(data["vector_length"]) is not int or data["vector_length"] < 1:
                raise ValueError("V4 Relay transfers require a positive vector length")
            if not all(isinstance(data[field], str) and data[field] for field in required - {"vector_length"}):
                raise ValueError("V4 Relay transfers require stable string evidence")
        if event["kind"] == "work" and "relay_work_leaves" in data:
            leaves = data["relay_work_leaves"]
            if not isinstance(leaves, list) or not leaves:
                raise ValueError("V4 Relay work requires a nonempty leaf list when present")
            seen_leaves: set[str] = set()
            for leaf in leaves:
                if not isinstance(leaf, dict) or set(leaf) != {"kind", "leg_index", "lineage_id", "leaf_id", "work_vector"}:
                    raise ValueError("V4 Relay work leaf has an invalid exact field set")
                if leaf["kind"] not in {"leg", "transfer", "candidate", "selection"} or type(leaf["leg_index"]) is not int or leaf["leg_index"] < 0:
                    raise ValueError("V4 Relay work leaf has invalid ancestry")
                if not isinstance(leaf["lineage_id"], str) or not leaf["lineage_id"] or not isinstance(leaf["leaf_id"], str) or not leaf["leaf_id"] or leaf["leaf_id"] in seen_leaves:
                    raise ValueError("V4 Relay work leaves must have unique stable IDs")
                seen_leaves.add(leaf["leaf_id"])
    if event.get("ledger_version") == CANONICAL_SCHEDULE_LEDGER_VERSION and event["kind"] == "termination":
        if set(data) != {"schedule_terminal", "deterministic_facts"}:
            raise ValueError("V3 schedule terminal requires exact deterministic evidence fields")
        facts = data["deterministic_facts"]
        if not isinstance(facts, dict) or set(facts) != {"candidate", "policy_effects", "rng_identities"}:
            raise ValueError("V3 schedule terminal requires candidate, policy, and RNG facts")
        if (
            not isinstance(facts["candidate"], list)
            or not isinstance(facts["policy_effects"], dict)
            or not isinstance(facts["rng_identities"], dict)
            or not all(isinstance(value, str) and value for value in facts["rng_identities"].values())
        ):
            raise ValueError("V3 schedule terminal deterministic facts are invalid")
        from .canonical.verification import reconstruct_schedule_terminal

        reconstruct_schedule_terminal(data["schedule_terminal"])
    sidecar = event.get("sidecar")
    if sidecar is not None:
        if not isinstance(sidecar, dict):
            raise ValueError("canonical sidecar link must be an object")
        path, digest = sidecar.get("path"), sidecar.get("sha256")
        if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError("canonical sidecar path must be relative and confined")
        if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("canonical sidecar link requires a lowercase SHA-256")
    _canonical_event_bytes(event)


def _canonical_event_id(event: Mapping[str, Any]) -> str:
    content = dict(event)
    content.pop("event_id", None)
    return "canonical-" + sha256(_canonical_event_bytes(content)).hexdigest()[:20]


def _relay_work_leaves(event: Mapping[str, Any], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return explicit V4 leaves; synthesize legacy aggregate records only.

    Current Relay execution provides committed per-leg leaves.  The fallback
    below remains solely so historical V4 journals written before that contract
    can still be read and structurally reconstructed.
    """
    from .canonical.budgets import WorkVector

    data = event["data"]
    if "relay_work_leaves" in data:
        return data["relay_work_leaves"]
    try:
        total = WorkVector.from_evidence(data["work_vector"], structural_event_version=2)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("V4 Relay work event requires a V2 work vector") from error
    matching = [
        row for row in existing if row["kind"] == "relay_transfer"
        and row["run_id"] == event["run_id"] and row["shot_id"] == event["shot_id"]
    ]
    if total.relay_transfers != len(matching):
        raise ValueError("V4 Relay transfer leaves must exactly match the recorded transfer count")
    legs = data.get("relay_legs")
    if not isinstance(legs, (list, tuple)) or not legs or not isinstance(legs[0], Mapping):
        raise ValueError("V4 Relay work requires ordered leg ancestry")
    first_lineage = legs[0].get("lineage_id")
    if not isinstance(first_lineage, str) or not first_lineage:
        raise ValueError("V4 Relay work requires the first leg lineage")
    residual_values = total.as_evidence(structural_event_version=2)
    residual_values["relay_transfers"] = 0
    leaves: list[dict[str, Any]] = [{
        "kind": "leg", "leg_index": 0, "lineage_id": first_lineage,
        "leaf_id": "relay-work:" + sha256(
            f"{event['run_id']}:{event['shot_id']}:{first_lineage}".encode("utf-8")
        ).hexdigest()[:20],
        "work_vector": residual_values,
    }]
    for index, row in enumerate(matching, start=1):
        transfer = row["data"]
        leaves.append({
            "kind": "transfer", "leg_index": index,
            "lineage_id": transfer["producer_leg_lineage_id"],
            "leaf_id": transfer["relay_leaf_id"],
            "work_vector": WorkVector(relay_transfers=1).as_evidence(structural_event_version=2),
        })
    return leaves


def _read_canonical_event_text(text: str) -> list[dict[str, Any]]:
    """Parse one already-read canonical JSONL snapshot with the path grammar."""
    result: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    states: dict[ShotKey, str] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid canonical JSONL at line {number}") from error
        if not isinstance(event, dict):
            raise ValueError(f"canonical event at line {number} is not an object")
        _validate_canonical_event(event)
        if event["event_id"] != _canonical_event_id(event):
            raise ValueError(f"canonical event at line {number} has an invalid event_id")
        previous = seen.get(event["event_id"])
        if previous is not None:
            if previous != event:
                raise ValueError(f"conflicting canonical event ID at line {number}")
            continue
        key = _key(event["run_id"], event["shot_id"])
        state = states.get(key)
        if event["kind"] == "shot_begin":
            if state is not None:
                raise ValueError("canonical shot_begin is duplicated or follows a terminal event")
            states[key] = "open"
        elif state != "open":
            raise ValueError("canonical structural event requires a prior open shot_begin")
        if event["kind"] == "termination":
            states[key] = "terminal"
        seen[event["event_id"]] = event
        result.append(event)
    return result


def read_canonical_events_bytes(snapshot: bytes) -> list[dict[str, Any]]:
    """Validate canonical evidence from one caller-owned immutable byte snapshot."""
    if not isinstance(snapshot, bytes):
        raise TypeError("canonical ledger snapshot must be bytes")
    try:
        text = snapshot.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("canonical ledger snapshot is not UTF-8") from error
    return _read_canonical_event_text(text)


def read_canonical_events(path: str | Path) -> list[dict[str, Any]]:
    """Read validated v2/V3 structural evidence without weakening v1 validation."""
    journal = Path(path)
    if not journal.exists():
        return []
    return _read_canonical_event_text(journal.read_text(encoding="utf-8"))


def query_canonical_events(
    path: str | Path, *, run_id: str | None = None, shot_id: int | None = None,
    kind: str | None = None,
) -> list[dict[str, Any]]:
    """Return a filtered view of validated v2 evidence without replaying it."""
    if shot_id is not None and (type(shot_id) is not int or shot_id < 0):
        raise ValueError("shot_id filter must be a nonnegative integer")
    return [
        event for event in read_canonical_events(path)
        if (run_id is None or event["run_id"] == run_id)
        and (shot_id is None or event["shot_id"] == shot_id)
        and (kind is None or event["kind"] == kind)
    ]


class CanonicalEventWriter:
    """Durably append sparse versioned control-flow facts for canonical CSS shots."""

    def __init__(self, path: str | Path, *, structural_event_version: int = CANONICAL_LEDGER_VERSION):
        if structural_event_version not in {CANONICAL_LEDGER_VERSION, CANONICAL_SCHEDULE_LEDGER_VERSION, CANONICAL_RELAY_LEDGER_VERSION, CANONICAL_INTERVENTION_LEDGER_VERSION, CANONICAL_ENSEMBLE_LEDGER_VERSION, CANONICAL_POSTPROCESSING_LEDGER_VERSION}:
            raise ValueError("unsupported canonical structural event version")
        self.path = Path(path)
        self.structural_event_version = structural_event_version
        self._owners: dict[ShotKey, Any] = {}

    def _append(self, event: dict[str, Any]) -> None:
        if event["kind"] == "shot_begin" and event["data"].get("schema_version") == 4 and self.structural_event_version == CANONICAL_LEDGER_VERSION:
            self.structural_event_version = CANONICAL_RELAY_LEDGER_VERSION
        if self.structural_event_version == CANONICAL_RELAY_LEDGER_VERSION and event["kind"] == "relay_transfer":
            data = event["data"]
            data.setdefault("relay_leaf_id", "relay-transfer:" + sha256(
                f"{data.get('producer_leg_lineage_id')}:{data.get('digest')}".encode("utf-8")
            ).hexdigest()[:20])
        if self.structural_event_version == CANONICAL_RELAY_LEDGER_VERSION and event["kind"] == "work":
            event["data"]["relay_work_leaves"] = _relay_work_leaves(event, read_canonical_events(self.path))
        if self.structural_event_version == CANONICAL_RELAY_LEDGER_VERSION and event["kind"] == "termination":
            prior_work = [
                row["data"]["work_vector"] for row in read_canonical_events(self.path)
                if row["kind"] == "work" and row["run_id"] == event["run_id"] and row["shot_id"] == event["shot_id"]
            ]
            if len(prior_work) == 1:
                event["data"].setdefault("work_vector", prior_work[0])
        event["ledger_version"] = self.structural_event_version
        event["event_id"] = _canonical_event_id(event)
        _validate_canonical_event(event)
        key = _key(event["run_id"], event["shot_id"])
        if event["kind"] != "shot_begin" and self._owners.get(key) is None:
            raise ShotOwnershipError(f"canonical shot {key!r} is not owned by this writer")
        with _journal_lock(self.path):
            current = read_canonical_events(self.path)
            if any(row["event_id"] == event["event_id"] for row in current):
                return
            state = None
            for row in current:
                if _key(row["run_id"], row["shot_id"]) == key:
                    state = "terminal" if row["kind"] == "termination" else "open"
            if event["kind"] == "shot_begin":
                if state is not None:
                    raise ValueError("canonical shot_begin is duplicated or follows a terminal event")
            elif state != "open":
                raise ValueError("canonical structural event requires a prior open shot_begin")
            _canonical_event_bytes(event)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(_canonical_event_bytes(event).decode("utf-8") + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def begin(self, *, run_id: str, shot_id: int, sample_seed_identity: str, **data: Any) -> None:
        key = _key(run_id, shot_id)
        if key in self._owners:
            return
        owner = _try_owner_lock(self.path, key)
        if owner is None:
            raise ShotOwnershipError(f"canonical shot {key!r} is actively owned by another process")
        try:
            self._append({"kind": "shot_begin", "run_id": run_id, "shot_id": shot_id, "sample_seed_identity": sample_seed_identity, "data": data})
            self._owners[key] = owner
        except BaseException:
            _release_owner(owner)
            raise

    def event(self, *, run_id: str, shot_id: int, kind: str, data: Mapping[str, Any] | None = None, sidecar: Mapping[str, Any] | None = None) -> None:
        if kind in {"shot_begin", "termination"}:
            raise ValueError("canonical reserved lifecycle kinds must use begin() and terminal()")
        event: dict[str, Any] = {"kind": kind, "run_id": run_id, "shot_id": shot_id, "data": dict(data or {})}
        if sidecar is not None:
            event["sidecar"] = dict(sidecar)
        self._append(event)

    def terminal(self, *, run_id: str, shot_id: int, termination: str, data: Mapping[str, Any] | None = None) -> None:
        key = _key(run_id, shot_id)
        owner = self._owners.get(key)
        try:
            if owner is None:
                raise ShotOwnershipError(f"canonical shot {key!r} is not owned by this writer")
            self._append({"kind": "termination", "run_id": run_id, "shot_id": shot_id, "termination": termination, "data": dict(data or {})})
        finally:
            if owner is not None:
                self._owners.pop(key, None)
                _release_owner(owner)

    def close(self) -> None:
        for key, owner in list(self._owners.items()):
            self._owners.pop(key, None)
            _release_owner(owner)

    def __enter__(self) -> "CanonicalEventWriter":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
        return None
