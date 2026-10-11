"""Immutable campaign-shard publication, validation, and one-look reduction."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping

from scipy.stats import binomtest

from ..canonical.verification import validate_canonical_shot
from ..ledger import read_canonical_events_bytes
from ..runner import canonical_public_shot_context
from .contracts import CampaignSpecV1, build_one_unit_plan, canonical_json_bytes
from .planning import CampaignWorkPlan


_MAX_SIDECARS = 1_000
_SEALED_STATES = frozenset({"sealed_interrupted", "sealed_terminal"})


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _private_mode(path: Path) -> None:
    """Reject group/world-readable staging products before publication."""
    mode = stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)
    if mode & 0o077:
        raise ValueError("sealed shard staging must be private to its caller")


def _seal_tree(staging: Path) -> None:
    if staging.is_symlink() or not staging.is_dir():
        raise ValueError("sealed shard staging must be a real private directory")
    _private_mode(staging)
    for path in sorted(staging.rglob("*")):
        if path.is_symlink():
            raise ValueError("sealed shard files must not contain symlinks")
        if path.is_dir():
            _private_mode(path)
            _fsync_directory(path)
        elif path.is_file():
            # The caller owns the private staging directory.  Normalize files
            # created through normal umask defaults before their durable seal.
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            _fsync_file(path)
        else:
            raise ValueError("sealed shard files must be regular files or directories")


def publish_sealed_shard(*, staging: Path, destination: Path) -> None:
    """Atomically publish a fully fsynced private shard on its destination FS."""
    if destination.exists() or destination.is_symlink():
        raise ValueError("sealed campaign shard already exists and cannot be reopened")
    _seal_tree(staging)
    if staging.stat().st_dev != destination.parent.stat().st_dev:
        raise ValueError("sealed shard staging and destination must share a filesystem")
    _fsync_directory(staging)
    os.replace(staging, destination)
    _fsync_directory(destination.parent)


def _read_regular_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("sealed shard files must be regular non-symlink files")
    return path.read_bytes()


def _digest(value: bytes) -> str:
    return sha256(value).hexdigest()


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def attempt_receipt_digest(receipt: Mapping[str, Any]) -> str:
    """Return the identity of immutable attempt receipt bytes."""
    return _digest(canonical_json_bytes(dict(receipt)))


def validate_attempt_lineage(attempts: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate immutable attempt-state receipts for one frozen campaign unit.

    A receipt records the only allowed durable transition: planned, then
    running, then one sealed final state.  A retry can name only an interrupted
    parent, never a completed terminal receipt.
    """
    if not isinstance(attempts, (tuple, list)) or not attempts:
        raise ValueError("attempt lineage must contain at least one receipt")
    by_id: dict[str, Mapping[str, Any]] = {}
    for receipt in attempts:
        if not isinstance(receipt, Mapping) or receipt.get("schema") != "campaign_attempt_receipt_v1":
            raise ValueError("attempt lineage contains an unsupported receipt")
        attempt_id = receipt.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id or attempt_id in by_id:
            raise ValueError("attempt lineage requires unique nonempty attempt IDs")
        if not isinstance(receipt.get("unit_key"), str) or not receipt["unit_key"]:
            raise ValueError("attempt lineage requires a unit key")
        if not _is_digest(receipt.get("campaign_plan_digest")):
            raise ValueError("attempt lineage requires a campaign plan digest")
        state = receipt.get("state")
        lifecycle = receipt.get("lifecycle")
        if state not in _SEALED_STATES or lifecycle != ["planned", "running", state]:
            raise ValueError("attempt lineage has an invalid sealed state transition")
        parent = receipt.get("parent_attempt_receipt")
        if parent is not None and (not isinstance(parent, str) or not parent):
            raise ValueError("attempt lineage parent must be an attempt receipt ID")
        by_id[attempt_id] = receipt

    unit_keys = {str(receipt["unit_key"]) for receipt in by_id.values()}
    digests = {str(receipt["campaign_plan_digest"]) for receipt in by_id.values()}
    if len(unit_keys) != 1 or len(digests) != 1:
        raise ValueError("attempt lineage cannot mix campaign units or plans")
    for attempt_id, receipt in by_id.items():
        parent = receipt.get("parent_attempt_receipt")
        if parent is None:
            continue
        parent_receipt = by_id.get(parent)
        if parent_receipt is None:
            raise ValueError("attempt lineage parent is missing")
        if parent_receipt["state"] != "sealed_interrupted":
            raise ValueError("attempt parent must be sealed_interrupted before retry")
        cursor = parent
        seen = {attempt_id}
        while cursor is not None:
            if cursor in seen:
                raise ValueError("attempt lineage contains a cycle")
            seen.add(cursor)
            value = by_id[cursor].get("parent_attempt_receipt")
            cursor = value if isinstance(value, str) else None
    terminal_ids = tuple(sorted(
        attempt_id for attempt_id, receipt in by_id.items() if receipt["state"] == "sealed_terminal"
    ))
    interrupted_ids = tuple(sorted(
        attempt_id for attempt_id, receipt in by_id.items() if receipt["state"] == "sealed_interrupted"
    ))
    return {
        "unit_key": next(iter(unit_keys)),
        "campaign_plan_digest": next(iter(digests)),
        "attempt_ids": tuple(sorted(by_id)),
        "terminal_attempt_ids": terminal_ids,
        "interrupted_attempt_ids": interrupted_ids,
        "attempt_receipt_hashes": tuple(sorted(attempt_receipt_digest(receipt) for receipt in by_id.values())),
    }


def _resolve_manifest(campaign_root: Path, spec: CampaignSpecV1) -> Path:
    root = campaign_root.resolve(strict=True)
    path = root
    for part in Path(spec.inner_manifest_path).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("inner manifest may not be a symlink")
    resolved = path.resolve(strict=True)
    if resolved != root and root not in resolved.parents:
        raise ValueError("inner manifest escapes campaign root")
    if sha256(_read_regular_bytes(path)).hexdigest() != spec.inner_manifest_sha256:
        raise ValueError("inner manifest digest differs from frozen campaign specification")
    return path


def _confined_sidecar(receipt_file: Path, relative_path: str) -> Path:
    candidate = receipt_file.parent / relative_path
    if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
        raise ValueError("sealed shard sidecar path must be relative and confined")
    resolved_parent = receipt_file.parent.resolve(strict=True)
    resolved = candidate.resolve(strict=True)
    if resolved != resolved_parent and resolved_parent not in resolved.parents:
        raise ValueError("sealed shard sidecar escapes its shard directory")
    return candidate


def _verify_sidecars(*, receipt_file: Path, receipt: Mapping[str, Any], events: list[dict[str, Any]], byte_limit: int) -> None:
    """Verify every event-linked sidecar from one bounded immutable snapshot."""
    event_sidecars: dict[str, str] = {}
    for event in events:
        sidecar = event.get("sidecar")
        if sidecar is None:
            continue
        path = sidecar["path"]
        digest = sidecar["sha256"]
        previous = event_sidecars.setdefault(path, digest)
        if previous != digest:
            raise ValueError("canonical event sidecar path has conflicting digests")
    declared = receipt.get("sidecars", [])
    if not isinstance(declared, list) or len(declared) > _MAX_SIDECARS:
        raise ValueError("sealed shard sidecars must be a bounded list")
    expected: dict[str, tuple[str, int]] = {}
    for item in declared:
        if not isinstance(item, Mapping) or set(item) != {"path", "sha256", "bytes"}:
            raise ValueError("sealed shard sidecar receipt has an invalid field set")
        path, digest, size = item["path"], item["sha256"], item["bytes"]
        if not isinstance(path, str) or not path or not _is_digest(digest) or type(size) is not int or size < 0:
            raise ValueError("sealed shard sidecar receipt is invalid")
        if path in expected:
            raise ValueError("sealed shard sidecar receipt contains a duplicate path")
        expected[path] = (digest, size)
    if set(event_sidecars) != set(expected):
        raise ValueError("sealed shard sidecar receipt differs from canonical events")
    total = 0
    for path, (digest, size) in expected.items():
        snapshot = _read_regular_bytes(_confined_sidecar(receipt_file, path))
        total += len(snapshot)
        if total > byte_limit or len(snapshot) != size or _digest(snapshot) != digest:
            raise ValueError("sealed shard sidecar bytes differ from its receipt")


def _verify_v2_envelope(receipt: Mapping[str, Any], *, unit_key: str) -> None:
    """Require v2 products to bind operational facts without trusting them."""
    required = {
        "schema", "campaign_spec", "campaign_spec_digest", "campaign_plan_digest", "unit_key", "shard_id",
        "physical_sample_identity", "canonical_sample_identity", "decoder_randomness_identity", "ledger_sha256",
        "ledger_bytes", "sidecars", "terminal_fact", "attempt", "executor_observation", "environment",
        "timing", "source_identity", "expected_unit_keys", "terminal_unit_keys", "open_unit_keys",
        "validation_status", "replay_status",
    }
    if set(receipt) != required:
        raise ValueError("campaign shard v2 receipt has an invalid field set")
    if receipt["expected_unit_keys"] != [unit_key] or receipt["terminal_unit_keys"] != [unit_key] or receipt["open_unit_keys"] != []:
        raise ValueError("campaign shard v2 receipt has inconsistent unit coverage")
    if receipt["validation_status"] != "verified" or receipt["replay_status"] != "verified":
        raise ValueError("campaign shard v2 receipt is not independently verified")
    for field in ("executor_observation", "environment", "timing", "source_identity", "attempt"):
        if not isinstance(receipt[field], Mapping):
            raise ValueError(f"campaign shard v2 {field} must retain typed facts")
    attempt = dict(receipt["attempt"])
    attempt.setdefault("schema", "campaign_attempt_receipt_v1")
    validate_attempt_lineage((attempt,))


def _terminal_fact(events: list[dict[str, Any]], *, unit_key: str) -> dict[str, Any]:
    terminal = next(event for event in events if event["kind"] == "termination")
    outcome = terminal["data"].get("outcome")
    logical_failure = outcome not in {"exact", "stabilizer_equivalent"}
    return {
        "unit_key": unit_key,
        "termination": terminal["termination"],
        "outcome": outcome,
        "logical_failure": logical_failure,
    }


def seal_receipt(*, path: Path, receipt: Mapping[str, Any]) -> None:
    """Write compact receipt bytes once; callers publish its directory atomically."""
    payload = canonical_json_bytes(dict(receipt)) + b"\n"
    path.write_bytes(payload)
    _fsync_file(path)


def verify_shard(receipt_path: str | Path, *, campaign_root: str | Path) -> dict[str, Any]:
    """Revalidate one sealed byte snapshot before reporting any terminal outcome."""
    receipt_file = Path(receipt_path)
    receipt_bytes = _read_regular_bytes(receipt_file)
    try:
        receipt = json.loads(receipt_bytes)
    except json.JSONDecodeError as error:
        raise ValueError("sealed shard receipt is not JSON") from error
    if not isinstance(receipt, dict) or receipt.get("schema") not in {"campaign_shard_receipt_v1", "campaign_shard_receipt_v2"}:
        raise ValueError("unsupported shard receipt")
    spec = CampaignSpecV1.model_validate(receipt.get("campaign_spec"))
    manifest = _resolve_manifest(Path(campaign_root), spec)
    plan = build_one_unit_plan(spec)
    expected = {
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "unit_key": plan.unit_key,
        "shard_id": plan.shard_id,
        "physical_sample_identity": plan.physical_sample_identity,
        "decoder_randomness_identity": plan.decoder_randomness_identity,
    }
    if any(receipt.get(name) != value for name, value in expected.items()):
        raise ValueError("sealed shard receipt differs from the frozen campaign plan")
    ledger = _read_regular_bytes(receipt_file.parent / "events.jsonl")
    if len(ledger) != receipt.get("ledger_bytes") or sha256(ledger).hexdigest() != receipt.get("ledger_sha256"):
        raise ValueError("sealed shard ledger receipt mismatch")
    if len(ledger) > spec.max_evidence_bytes:
        raise ValueError("sealed shard exceeds campaign evidence bound")
    events = read_canonical_events_bytes(ledger)
    if len(events) > spec.max_events:
        raise ValueError("sealed shard exceeds campaign event bound")
    context = canonical_public_shot_context(manifest, shot_id=spec.sample_id)
    validate_canonical_shot(events, context)
    if context.decoder_seed_identity != spec.decoder_seed_identity:
        raise ValueError("inner manifest decoder randomness differs from campaign specification")
    manifest_namespace = context.manifest_sha256
    from ..manifests import preflight
    parsed = preflight(manifest).manifest
    manifest_namespace = parsed.randomness.physical_sample_identity or manifest_namespace
    if manifest_namespace != spec.sample_namespace:
        raise ValueError("inner manifest physical sample namespace differs from campaign specification")
    terminal_fact = _terminal_fact(events, unit_key=receipt["unit_key"])
    if receipt.get("terminal_fact") != terminal_fact:
        raise ValueError("sealed shard terminal fact differs from immutable ledger")
    _verify_sidecars(receipt_file=receipt_file, receipt=receipt, events=events, byte_limit=spec.max_evidence_bytes)
    if receipt["schema"] == "campaign_shard_receipt_v2":
        _verify_v2_envelope(receipt, unit_key=plan.unit_key)
    return {**receipt, "events": events, "terminal_fact": terminal_fact}


def reconstruct_fixed_shot(verified_shard: Mapping[str, Any]) -> dict[str, Any]:
    """Compute the declared one-look all-shot rate from a verified terminal only."""
    terminal = verified_shard.get("terminal_fact")
    if not isinstance(terminal, Mapping) or not isinstance(terminal.get("logical_failure"), bool):
        raise ValueError("verified shard has no all-shot terminal outcome")
    failures, completed = int(terminal["logical_failure"]), 1
    interval = binomtest(failures, completed).proportion_ci(confidence_level=0.95, method="exact")
    return {
        "campaign_spec_digest": verified_shard["campaign_spec_digest"],
        "campaign_plan_digest": verified_shard["campaign_plan_digest"],
        "completed": completed,
        "failures": failures,
        "estimate": failures / completed,
        "interval": {
            "method": "exact",
            "confidence_level": 0.95,
            "lower": float(interval.low),
            "upper": float(interval.high),
        },
        "status": "fixed_shot_complete",
    }


def verify_look_stop_receipt(
    *, plan: CampaignWorkPlan, receipt: Mapping[str, Any], terminal_unit_keys: set[str],
) -> tuple[str, ...]:
    """Verify a completed-look stop receipt before authorizing undispatched work."""
    required = {
        "schema", "campaign_plan_digest", "completed_look", "decision_input_hashes", "decision_result",
        "stop_reason", "realized_count", "overshoot_count", "authorized_undispatched",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != required or receipt.get("schema") != "campaign_look_stop_receipt_v1":
        raise ValueError("look stop receipt has an invalid field set")
    if receipt["campaign_plan_digest"] != plan.campaign_plan_digest:
        raise ValueError("look stop receipt differs from frozen campaign plan")
    look = receipt["completed_look"]
    if type(look) is not int:
        raise ValueError("look stop receipt requires a declared completed look")
    prefix = set(plan.completed_prefix(look))
    if not prefix.issubset(terminal_unit_keys):
        raise ValueError("look stop receipt requires a fully terminal completed look")
    hashes = receipt["decision_input_hashes"]
    if not isinstance(hashes, list) or not hashes or len(set(hashes)) != len(hashes) or not all(_is_digest(value) for value in hashes):
        raise ValueError("look stop receipt requires unique decision input hashes")
    if not isinstance(receipt["decision_result"], Mapping) or not isinstance(receipt["stop_reason"], str) or not receipt["stop_reason"]:
        raise ValueError("look stop receipt lacks its decision facts")
    if any(type(receipt[field]) is not int or receipt[field] < 0 for field in ("realized_count", "overshoot_count")):
        raise ValueError("look stop receipt has invalid realized or overshoot count")
    if receipt["realized_count"] != len(terminal_unit_keys) or receipt["overshoot_count"] != len(terminal_unit_keys - prefix):
        raise ValueError("look stop receipt count facts differ from verified terminals")
    expected = tuple(key for key in plan.authorized_tail(look) if key not in terminal_unit_keys)
    actual = receipt["authorized_undispatched"]
    if not isinstance(actual, list) or tuple(actual) != expected:
        raise ValueError("look stop receipt has an invalid authorized undispatched tail")
    return expected


def _verified_attempt_record(record: Mapping[str, Any], *, plan: CampaignWorkPlan) -> tuple[str, Mapping[str, Any]]:
    if not isinstance(record, Mapping):
        raise ValueError("merge requires verified attempt records")
    if record.get("validation_status") != "verified" or record.get("replay_status") != "verified":
        raise ValueError("merge accepts only independently verified attempt records")
    if not _is_digest(record.get("receipt_sha256")):
        raise ValueError("verified attempt record requires its immutable receipt hash")
    attempt = record.get("attempt")
    if not isinstance(attempt, Mapping):
        raise ValueError("verified attempt record lacks attempt receipt")
    if attempt.get("campaign_plan_digest") != plan.campaign_plan_digest:
        raise ValueError("verified attempt record differs from frozen campaign plan")
    unit_key = attempt.get("unit_key")
    if not isinstance(unit_key, str) or not unit_key:
        raise ValueError("verified attempt record lacks unit key")
    if attempt.get("state") == "sealed_terminal":
        terminal = record.get("terminal_fact")
        events = record.get("events")
        if not _is_digest(record.get("terminal_bytes_sha256")) or not isinstance(terminal, Mapping) or terminal.get("unit_key") != unit_key:
            raise ValueError("verified terminal record lacks immutable terminal facts")
        if not isinstance(events, (list, tuple)) or any(not isinstance(event, Mapping) or not isinstance(event.get("event_id"), str) for event in events):
            raise ValueError("verified terminal record lacks reconstructed events")
    elif "terminal_fact" in record or "terminal_bytes_sha256" in record:
        raise ValueError("nonterminal attempt cannot claim terminal evidence")
    return unit_key, attempt


def merge_verified_attempts(
    *, plan: CampaignWorkPlan, verified_attempts: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
    look_stop_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Reduce validated immutable attempt snapshots by exact frozen unit coverage.

    This function deliberately accepts only records already returned by an
    independent shard verifier.  It never reads shard summaries and never
    assigns a denominator contribution to an unverified or open attempt.
    """
    if not isinstance(plan, CampaignWorkPlan):
        raise ValueError("merge requires a frozen CampaignWorkPlan")
    if not isinstance(verified_attempts, (tuple, list)):
        raise ValueError("merge requires an ordered collection of verified attempts")
    expected = tuple(plan.unit_keys)
    expected_set = set(expected)
    by_unit: dict[str, list[Mapping[str, Any]]] = {}
    unexpected: set[str] = set()
    for record in verified_attempts:
        unit_key, _ = _verified_attempt_record(record, plan=plan)
        if unit_key not in expected_set:
            unexpected.add(unit_key)
            continue
        by_unit.setdefault(unit_key, []).append(record)

    terminals: dict[str, Mapping[str, Any]] = {}
    terminal_events: list[tuple[int, str, Mapping[str, Any]]] = []
    explicit_final: set[str] = set()
    incomplete: set[str] = set()
    redundant_hashes: set[str] = set()
    attempt_hashes: set[str] = set()
    for unit_key, records in by_unit.items():
        lineage = validate_attempt_lineage([record["attempt"] for record in records])
        if lineage["unit_key"] != unit_key or lineage["campaign_plan_digest"] != plan.campaign_plan_digest:
            raise ValueError("verified attempt lineage differs from frozen unit")
        attempt_hashes.update(str(record["receipt_sha256"]) for record in records)
        terminal_records = sorted(
            (record for record in records if record["attempt"]["state"] == "sealed_terminal"),
            key=lambda record: str(record["receipt_sha256"]),
        )
        if terminal_records:
            first = terminal_records[0]
            first_digest = first["terminal_bytes_sha256"]
            first_fact = canonical_json_bytes(first["terminal_fact"])
            for record in terminal_records[1:]:
                if record["terminal_bytes_sha256"] != first_digest or canonical_json_bytes(record["terminal_fact"]) != first_fact:
                    raise ValueError("conflicting terminal retries for one frozen unit")
                redundant_hashes.add(str(record["receipt_sha256"]))
            terminals[unit_key] = first
            position = expected.index(unit_key)
            terminal_events.extend((position, str(event["event_id"]), event) for event in first["events"])
        elif any(record.get("final_nonterminal") is True for record in records):
            explicit_final.add(unit_key)
        else:
            incomplete.add(unit_key)

    terminal_keys = set(terminals)
    authorized_tail: tuple[str, ...] = ()
    stop_hashes: tuple[str, ...] = ()
    if look_stop_receipt is not None:
        authorized_tail = verify_look_stop_receipt(plan=plan, receipt=look_stop_receipt, terminal_unit_keys=terminal_keys)
        stop_hashes = (attempt_receipt_digest(look_stop_receipt),)
    accounted = terminal_keys | explicit_final | incomplete | set(authorized_tail)
    missing = expected_set - accounted
    ordered_events = [dict(event) for _, _, event in sorted(terminal_events, key=lambda item: (item[0], item[1]))]
    payload = {
        "schema": "campaign_merge_receipt_v1",
        "campaign_plan_digest": plan.campaign_plan_digest,
        "terminal_unit_keys": [key for key in expected if key in terminal_keys],
        "explicit_final_nonterminal_keys": [key for key in expected if key in explicit_final],
        "incomplete_unit_keys": [key for key in expected if key in incomplete],
        "authorized_undispatched_keys": list(authorized_tail),
        "unexpected_unit_keys": sorted(unexpected),
        "redundant_attempt_receipt_hashes": sorted(redundant_hashes),
        "conflicting_unit_keys": [],
        "missing_unit_keys": [key for key in expected if key in missing],
        "attempt_receipt_hashes": sorted(attempt_hashes),
        "stop_receipt_hashes": list(stop_hashes),
        "terminal_facts": [dict(terminals[key]["terminal_fact"]) for key in expected if key in terminals],
        "events": ordered_events,
    }
    receipt_bytes = canonical_json_bytes(payload)
    return {**payload, "receipt_bytes": receipt_bytes, "receipt_sha256": _digest(receipt_bytes)}
