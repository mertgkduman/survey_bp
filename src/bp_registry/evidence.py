"""Versioned, source-linked evidence records for the BP mapping study.

The registry deliberately records source claims separately from experiment maturity.
An observed paper claim is ``mapped_only`` until an independent execution or
assessment supplies the corresponding evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
import threading
from typing import Any, Iterable, Mapping

try:  # The project is deployed on POSIX HPC systems; retain an in-process lock fallback.
    import fcntl
except ImportError:  # pragma: no cover - exercised only on non-POSIX hosts.
    fcntl = None


PROTOCOL_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "research_questions",
        "searches",
        "cutoff",
        "inclusion_criteria",
        "exclusion_criteria",
        "screening",
        "adjudication",
        "snowballing",
        "extraction_dictionary",
        "update_rule",
    }
)
EVIDENCE_MATURITY = frozenset(
    {"mapped_only", "reference_executable", "canonical_implemented", "statistically_assessed"}
)
CLAIM_STATES = frozenset({"established", "inferred", "unresolved"})


class EventConflictError(ValueError):
    """A stable event ID was reused with different scientific content."""


@dataclass(frozen=True)
class Claim:
    """A statement with a precise source revision and local paper anchor."""

    work_id: str
    revision_id: str
    anchor: str
    statement: str
    taxonomy: Mapping[str, Any] = field(default_factory=dict)
    claim_state: str = "established"
    evidence_maturity: str = "mapped_only"
    value: Any = None
    value_status: str = "explicitly_unavailable"

    def __post_init__(self) -> None:
        if not all((self.work_id, self.revision_id, self.anchor, self.statement)):
            raise ValueError("claims require work ID, revision ID, anchor, and statement")
        if self.claim_state not in CLAIM_STATES:
            raise ValueError(f"unknown claim state: {self.claim_state}")
        if self.evidence_maturity not in EVIDENCE_MATURITY:
            raise ValueError(f"unknown evidence maturity: {self.evidence_maturity}")


def _canonical_payload(event: Mapping[str, Any], *, include_event_id: bool = False) -> str:
    """Return stable JSON for identity and conflict comparisons."""

    payload = {
        key: value
        for key, value in event.items()
        if key != "event_order" and (include_event_id or key != "event_id")
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_event_id(event: Mapping[str, Any]) -> str:
    """Derive a content-addressed identifier when a source does not supply one."""

    return f"event-{sha256(_canonical_payload(event).encode('utf-8')).hexdigest()[:20]}"


def replay_events(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Replay an append-only history, preserving first-seen event order.

    Repeating identical records is idempotent.  Reusing an identity for altered
    content raises instead of silently overwriting a screening decision.
    """

    history: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for raw_event in events:
        event = dict(raw_event)
        event_id = str(event.get("event_id") or stable_event_id(event))
        event["event_id"] = event_id
        previous = by_id.get(event_id)
        if previous is not None:
            if _canonical_payload(previous) != _canonical_payload(event):
                raise EventConflictError(f"conflicting content for event_id {event_id!r}")
            continue
        by_id[event_id] = event
        history.append(event)
    return history


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    """Reject incomplete mapping protocols before they can be presented as reproducible."""

    missing = sorted(field for field in PROTOCOL_REQUIRED_FIELDS if not protocol.get(field))
    if missing:
        raise ValueError(f"protocol lacks required non-empty fields: {', '.join(missing)}")
    screening = protocol["screening"]
    if not isinstance(screening, Mapping) or not screening.get("title_and_abstract") or not screening.get("full_text"):
        raise ValueError("protocol requires title/abstract and full-text screening procedures")


class EvidenceRegistry:
    """Small JSONL registry with lock-protected, content-addressed event writes."""

    _locks: dict[Path, threading.RLock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, event_path: str | Path):
        self.event_path = Path(event_path)
        self.event_path.parent.mkdir(parents=True, exist_ok=True)
        with self._locks_guard:
            self._lock = self._locks.setdefault(self.event_path.resolve(), threading.RLock())
        self._history: list[dict[str, Any]] = []
        self.works: dict[str, dict[str, Any]] = {}
        self._reload()

    def _read_events(self) -> list[dict[str, Any]]:
        if not self.event_path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(self.event_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSONL event at line {line_number}") from error
            if not isinstance(record, dict):
                raise ValueError(f"event at line {line_number} is not an object")
            records.append(record)
        return records

    def _rebuild_works(self) -> None:
        works: dict[str, dict[str, Any]] = {}
        for event in self._history:
            if event.get("kind") != "search":
                continue
            for hit in event.get("raw_hits", []):
                work_id = hit.get("normalized_work_id")
                revision_id = hit.get("revision_id")
                if not work_id:
                    continue
                work = works.setdefault(str(work_id), {"raw_hit_ids": [], "revision_ids": []})
                raw_hit_id = hit.get("raw_hit_id")
                if raw_hit_id and raw_hit_id not in work["raw_hit_ids"]:
                    work["raw_hit_ids"].append(raw_hit_id)
                if revision_id and revision_id not in work["revision_ids"]:
                    work["revision_ids"].append(revision_id)
        self.works = works

    def _reload(self) -> None:
        self._history = replay_events(self._read_events())
        self._rebuild_works()

    def history(self) -> list[dict[str, Any]]:
        return [dict(event) for event in self._history]

    def append_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        """Append one event or return an identical pre-existing event atomically."""

        candidate = dict(event)
        candidate["event_id"] = str(candidate.get("event_id") or stable_event_id(candidate))
        lock_path = self.event_path.with_suffix(f"{self.event_path.suffix}.lock")
        with self._lock:
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    self._reload()
                    for existing in self._history:
                        if existing["event_id"] != candidate["event_id"]:
                            continue
                        if _canonical_payload(existing) != _canonical_payload(candidate):
                            raise EventConflictError(
                                f"conflicting content for event_id {candidate['event_id']!r}"
                            )
                        return dict(existing)
                    candidate["event_order"] = len(self._history) + 1
                    with self.event_path.open("a", encoding="utf-8") as event_file:
                        event_file.write(json.dumps(candidate, sort_keys=True, ensure_ascii=False) + "\n")
                        event_file.flush()
                    self._reload()
                    return dict(self._history[-1])
                finally:
                    if fcntl is not None:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def import_search_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        """Import a source search, retaining each raw hit before work-level deduplication."""

        required = {"kind", "source_uri", "query", "cutoff", "raw_hits", "timestamp"}
        missing = sorted(required.difference(event))
        if missing:
            raise ValueError(f"search event lacks fields: {', '.join(missing)}")
        if event["kind"] != "search":
            raise ValueError("import_search_event accepts only kind='search'")
        if not isinstance(event["raw_hits"], list):
            raise ValueError("raw_hits must be a list, including an explicit empty list")
        for hit in event["raw_hits"]:
            if not isinstance(hit, Mapping) or not hit.get("raw_hit_id") or not hit.get("normalized_work_id"):
                raise ValueError("each raw hit requires raw_hit_id and normalized_work_id")
        return self.append_event(event)

    def screen(
        self,
        work_id: str,
        revision_id: str,
        *,
        stage: str,
        decision: str,
        reason: str,
        reviewer: str = "registry-maintainer",
        adjudicator: str | None = None,
        timestamp: str = "1970-01-01T00:00:00Z",
    ) -> dict[str, Any]:
        """Append a reviewable screening decision without replacing earlier decisions."""

        if not all((work_id, revision_id, stage, decision, reason, reviewer, timestamp)):
            raise ValueError("screening events require identity, stage, decision, reason, reviewer, and timestamp")
        return self.append_event(
            {
                "kind": "screening_decision",
                "work_id": work_id,
                "revision_id": revision_id,
                "stage": stage,
                "decision": decision,
                "reason": reason,
                "reviewer": reviewer,
                "adjudicator": adjudicator,
                "timestamp": timestamp,
            }
        )


def query_claims(claims: Iterable[Mapping[str, Any] | Claim], **filters: Any) -> list[Mapping[str, Any] | Claim]:
    """Filter taxonomy records without collapsing unresolved into established claims."""

    matches: list[Mapping[str, Any] | Claim] = []
    for claim in claims:
        if isinstance(claim, Claim):
            direct = {
                "work_id": claim.work_id,
                "revision_id": claim.revision_id,
                "claim_state": claim.claim_state,
                "evidence_maturity": claim.evidence_maturity,
            }
            taxonomy = claim.taxonomy
        else:
            direct = claim
            taxonomy = claim.get("taxonomy", {})
        if all(direct.get(key, taxonomy.get(key)) == value for key, value in filters.items()):
            matches.append(claim)
    return matches
