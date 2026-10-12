"""Bounded local execution over an already frozen campaign work plan.

This module owns executor observations only. Unit membership, sample identity,
decoder randomness, stopping algebra, and retry planning are supplied by the
frozen plan and other campaign modules.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Callable, Mapping

from .. import sampling
from ..canonical.verification import validate_canonical_shot
from ..ledger import CanonicalResourceInterruption, read_canonical_events
from ..runner import (
    CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1, CanonicalRuntimeAuthorizationV1,
    CanonicalRuntimeGuardV1, canonical_public_manifest_context, canonical_public_shot_context,
    derive_canonical_executable_maxima, guarded_atomic_write_bytes, run_canonical_materialized_one,
    run_canonical_one, verify_declared_executable_limits,
)
from .contracts import (
    CampaignSpecV1, CampaignWorkSpecV1, FailureCountPartialAttemptV1, FailureCountStoppingV1, FailureCountTerminalReceiptV1, FailureCountWorkSpecV1,
    MaterializedPhysicalSampleV1, _MAX_DECODER_WORK, _MAX_EVIDENCE_BYTES,
    _MAX_EVENTS, _MAX_STORAGE_BYTES, build_one_unit_plan, canonical_json_bytes,
)
from .identity import validate_matched_sample_hashes
from .planning import CampaignWorkPlan, ShardPlan
from .shards import _resolve_manifest, _terminal_fact, publish_sealed_shard, seal_receipt


_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
)
_MAX_LOCAL_WORKERS = 64


def _campaign_work_spec(plan: CampaignWorkPlan) -> CampaignWorkSpecV1:
    """Return the shared canonical work contract without erasing FC policy."""
    spec = plan.work_spec
    if isinstance(spec, FailureCountWorkSpecV1):
        return spec.campaign_work_spec
    if isinstance(spec, CampaignWorkSpecV1):
        return spec
    raise ValueError("canonical execution requires a frozen campaign work specification")


def _allowlisted_thread_environment() -> dict[str, str]:
    """Bound nested numerical libraries without inspecting unrelated environment."""
    observed: dict[str, str] = {}
    for name in _THREAD_ENVIRONMENT:
        value = os.environ.get(name)
        if value is None:
            os.environ[name] = "1"
            value = "1"
        if not value.isdecimal() or int(value) < 1:
            raise ValueError(f"{name} must be a positive integer when set")
        observed[name] = value
    return observed


def _unit_record(
    *, unit: Mapping[str, Any], result: Mapping[str, Any], started_ns: int, ended_ns: int,
    environment: Mapping[str, str], process_id: int,
) -> dict[str, Any]:
    """Separate hash-stable scientific unit facts from observational facts."""
    terminal = result.get("terminal_fact")
    if not isinstance(terminal, Mapping) or terminal.get("unit_key") != unit["unit_key"]:
        raise ValueError("unit runner must return a terminal fact for its exact frozen unit")
    expected = {"unit_key", "termination", "outcome", "logical_failure"}
    if set(terminal) != expected or not isinstance(terminal["logical_failure"], bool):
        raise ValueError("unit runner terminal fact has an invalid field set")
    work = result.get("work_vector", {})
    if not isinstance(work, Mapping) or any(
        not isinstance(name, str) or type(value) is not int or value < 0
        for name, value in work.items()
    ):
        raise ValueError("unit runner work vector must contain nonnegative integer facts")
    persisted = result.get("persisted_sample_bytes")
    if persisted is not None and not isinstance(persisted, bytes):
        raise ValueError("persisted sample evidence must be bytes when supplied")
    scientific = {
        "unit_key": unit["unit_key"],
        "physical_sample_identity": unit["physical_sample_identity"],
        "decoder_randomness_identity": unit["decoder_randomness_identity"],
        "terminal_fact": dict(terminal),
        "work_vector": dict(sorted(work.items())),
        "persisted_sample_sha256": None if persisted is None else sha256(persisted).hexdigest(),
    }
    return {
        "schema": "campaign_local_unit_receipt_v1",
        "scientific": scientific,
        "observation": {
            "started_monotonic_ns": started_ns,
            "ended_monotonic_ns": ended_ns,
            "process_id": process_id,
            "environment": dict(environment),
            "resource_observations": [
                {"name": "wall_time_ns", "value": ended_ns - started_ns, "unavailable_reason": None},
                {"name": "backend_device_time", "value": None, "unavailable_reason": "no device profiler configured"},
                {"name": "backend_device_memory", "value": None, "unavailable_reason": "no device profiler configured"},
            ],
        },
    }


def _seal_local_record(*, output_root: str, unit_key: str, record: Mapping[str, Any]) -> str:
    """Publish one worker-private unit receipt through the immutable shard primitive."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"unit-{unit_key}"
    if destination.exists():
        raise ValueError("frozen unit has already been sealed at this execution destination")
    staging = Path(tempfile.mkdtemp(prefix=".campaign-local-", dir=root))
    try:
        seal_receipt(path=staging / "receipt.json", receipt=record)
        publish_sealed_shard(staging=staging, destination=destination)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return str(destination / "receipt.json")


def _execute_local_shard(
    shard: ShardPlan, units: tuple[dict[str, Any], ...], output_root: str,
    unit_runner: Callable[[dict[str, Any], str], Mapping[str, Any]],
) -> dict[str, Any]:
    """Run exactly one frozen shard in a child process, retaining partial work."""
    environment = _allowlisted_thread_environment()
    records: list[dict[str, Any]] = []
    for unit in units:
        started = time.monotonic_ns()
        stage = tempfile.mkdtemp(prefix=".campaign-unit-input-", dir=output_root)
        try:
            result = unit_runner(dict(unit), stage)
            ended = time.monotonic_ns()
            record = _unit_record(
                unit=unit, result=result, started_ns=started, ended_ns=ended,
                environment=environment, process_id=os.getpid(),
            )
            receipt_path = _seal_local_record(
                output_root=output_root, unit_key=str(unit["unit_key"]), record=record,
            )
            records.append({
                "unit_key": unit["unit_key"], "state": "sealed_terminal",
                "receipt_path": receipt_path, **record,
            })
        except BaseException as error:
            ended = time.monotonic_ns()
            incomplete = {
                "schema": "campaign_local_incomplete_attempt_v1",
                "unit_key": unit["unit_key"],
                "physical_sample_identity": unit["physical_sample_identity"],
                "decoder_randomness_identity": unit["decoder_randomness_identity"],
                "state": "sealed_interrupted",
                "error_type": type(error).__name__,
                "observation": {
                    "started_monotonic_ns": started,
                    "ended_monotonic_ns": ended,
                    "process_id": os.getpid(),
                    "environment": dict(environment),
                },
            }
            receipt_path = _seal_local_record(
                output_root=output_root, unit_key=str(unit["unit_key"]), record=incomplete,
            )
            records.append({"receipt_path": receipt_path, **incomplete})
            break
        finally:
            shutil.rmtree(stage, ignore_errors=True)
    return {"shard_id": shard.shard_id, "records": records, "environment": environment}


def execute_local_work_plan(
    plan: CampaignWorkPlan, *, output_root: str | Path, workers: int,
    unit_runner: Callable[[dict[str, Any], str], Mapping[str, Any]],
    shards: tuple[ShardPlan, ...] | None = None,
) -> dict[str, Any]:
    """Execute supplied immutable shards with a bounded process pool.

    ``unit_runner`` is a top-level pickleable adapter that operates only on the
    supplied frozen unit and private staging path. Its result carries terminal
    and work facts; executor timing and resource facts remain observational.
    """
    if not isinstance(plan, CampaignWorkPlan):
        raise ValueError("local execution requires a frozen CampaignWorkPlan")
    if type(workers) is not int or not 1 <= workers <= _MAX_LOCAL_WORKERS:
        raise ValueError(f"workers must be an integer in [1, {_MAX_LOCAL_WORKERS}]")
    if not callable(unit_runner):
        raise ValueError("unit_runner must be a pickleable top-level callable")
    destination = Path(output_root)
    destination.mkdir(parents=True, exist_ok=True)
    units = {unit.key: unit.payload() for unit in plan.units}
    selected_shards = plan.shards if shards is None else tuple(shards)
    known_shards = {shard.shard_id: shard for shard in plan.shards}
    if not selected_shards or any(known_shards.get(shard.shard_id) != shard for shard in selected_shards):
        raise ValueError("local execution must consume a nonempty exact subset of frozen shards")
    ordered_jobs = tuple(
        (shard, tuple(units[key] for key in shard.unit_keys)) for shard in selected_shards
    )
    max_workers = min(workers, len(ordered_jobs))
    completed: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_execute_local_shard, shard, shard_units, str(destination), unit_runner): shard
            for shard, shard_units in ordered_jobs
        }
        for future in as_completed(futures):
            completed.append(future.result())
    records = [record for shard in completed for record in shard["records"]]
    by_unit = {str(record["unit_key"]): record for record in records}
    ordered_records = [by_unit[key] for key in plan.unit_keys if key in by_unit]
    terminal = tuple(record["unit_key"] for record in ordered_records if record["state"] == "sealed_terminal")
    incomplete = tuple(record["unit_key"] for record in ordered_records if record["state"] != "sealed_terminal")
    scientific = tuple(record["scientific"] for record in ordered_records if record["state"] == "sealed_terminal")
    validate_matched_sample_hashes(scientific)
    return {
        "schema": "campaign_local_execution_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "shard_ids": tuple(shard.shard_id for shard, _ in ordered_jobs),
        "terminal_unit_keys": terminal,
        "incomplete_unit_keys": incomplete,
        "scientific_records": scientific,
        "observed_concurrency": max_workers,
        "environment": _allowlisted_thread_environment(),
        "resource_observations": [
            {"name": "scheduler_allocation", "value": None, "unavailable_reason": "local executor has no scheduler allocation"},
            {"name": "aggregate_process_cpu", "value": None, "unavailable_reason": "worker-local CPU facts are not aggregated"},
        ],
        "records": tuple(ordered_records),
    }


def _sealed_local_records(root: Path) -> tuple[dict[str, Any], ...]:
    """Read only published unit receipts; staging files never influence resume."""
    records: list[dict[str, Any]] = []
    for receipt_path in sorted(root.glob("unit-*/receipt.json")):
        try:
            payload = json.loads(receipt_path.read_bytes())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("published local unit receipt is unreadable") from error
        if not isinstance(payload, dict):
            raise ValueError("published local unit receipt must be an object")
        if payload.get("schema") == "campaign_local_unit_receipt_v1":
            scientific = payload.get("scientific")
            if not isinstance(scientific, dict) or not isinstance(scientific.get("unit_key"), str):
                raise ValueError("published terminal receipt lacks scientific identity")
            records.append({"state": "sealed_terminal", "receipt_path": str(receipt_path), **payload,
                            "unit_key": scientific["unit_key"]})
        elif payload.get("schema") == "campaign_local_incomplete_attempt_v1":
            if not isinstance(payload.get("unit_key"), str):
                raise ValueError("published interrupted receipt lacks unit identity")
            records.append({"receipt_path": str(receipt_path), **payload})
        else:
            raise ValueError("published local receipt has an unsupported schema")
    return tuple(records)


def _deterministic_look_stop_receipt(
    *, plan: CampaignWorkPlan, look: int, terminal_records: tuple[dict[str, Any], ...],
    decision: Mapping[str, Any], merge_receipt_sha256: str,
) -> dict[str, Any]:
    required = {"decision_input_hashes", "decision_result", "stop_reason", "should_stop"}
    if set(decision) != required or decision.get("should_stop") is not True:
        raise ValueError("finite-look decision cannot authorize a stop")
    hashes = decision["decision_input_hashes"]
    if not isinstance(hashes, (list, tuple)) or not hashes or any(
        not isinstance(item, str) or len(item) != 64 for item in hashes
    ):
        raise ValueError("finite-look stop decision requires input receipt hashes")
    prefix = plan.completed_prefix(look)
    terminal_keys = {record["unit_key"] for record in terminal_records}
    if not set(prefix).issubset(terminal_keys):
        raise ValueError("finite-look stop requires every unit in its declared boundary")
    if not isinstance(merge_receipt_sha256, str) or len(merge_receipt_sha256) != 64:
        raise ValueError("finite-look stop requires a verified merge receipt hash")
    return {
        "schema": "campaign_look_stop_receipt_v2",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "completed_look": look,
        "completed_boundary_units": len(prefix),
        "merge_receipt_sha256": merge_receipt_sha256,
        "decision_input_hashes": list(hashes),
        "decision_result": dict(decision["decision_result"]),
        "stop_reason": decision["stop_reason"],
        "realized_unit_count": len(terminal_records),
        "overshoot_unit_count": len(terminal_keys - set(prefix)),
        "authorized_undispatched": list(
            key for key in plan.authorized_tail(look) if key not in terminal_keys
        ),
    }


def _publish_stop_receipt(*, path: Path, receipt: Mapping[str, Any]) -> None:
    """Atomically publish deterministic evidence and reject conflicting bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(receipt), sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("retained finite-look receipt conflicts with reconstruction")
        return
    descriptor, staging_name = tempfile.mkstemp(prefix=".look-stop-", dir=path.parent)
    os.close(descriptor)
    staging = Path(staging_name)
    try:
        staging.write_bytes(payload)
        os.replace(staging, path)
    except BaseException:
        if staging.exists():
            staging.unlink()
        raise


def _build_look_merge_receipt(
    *, plan: CampaignWorkPlan, look: int, terminal_records: tuple[dict[str, Any], ...], root: Path,
) -> dict[str, Any]:
    """Rebuild the complete look's merge from sealed local unit bytes."""
    expected = {unit.key: unit for unit in plan.units}
    prefix = set(plan.completed_prefix(look))
    by_key: dict[str, dict[str, Any]] = {}
    for record in terminal_records:
        scientific = record.get("scientific")
        key = record.get("unit_key")
        unit = expected.get(key)
        if unit is None or not isinstance(scientific, dict) or key in by_key:
            raise ValueError("finite-look merge contains an unknown or duplicate terminal")
        if (scientific.get("unit_key") != key
                or scientific.get("physical_sample_identity") != unit.physical_sample_identity
                or scientific.get("decoder_randomness_identity") != unit.decoder_randomness_identity
                or not isinstance(scientific.get("terminal_fact"), dict)
                or scientific["terminal_fact"].get("unit_key") != key):
            raise ValueError("finite-look merge differs from frozen unit identity")
        receipt_path = Path(str(record.get("receipt_path")))
        if (receipt_path != root / f"unit-{key}" / "receipt.json"
                or receipt_path.is_symlink() or not receipt_path.is_file()):
            raise ValueError("finite-look merge requires sealed regular unit receipts")
        receipt_bytes = receipt_path.read_bytes()
        try:
            receipt = json.loads(receipt_bytes)
        except json.JSONDecodeError as error:
            raise ValueError("finite-look merge unit receipt is unreadable") from error
        if (not isinstance(receipt, dict)
                or receipt.get("schema") != "campaign_local_unit_receipt_v1"
                or receipt.get("scientific") != scientific):
            raise ValueError("finite-look merge unit receipt differs from verified scientific facts")
        by_key[str(key)] = {"scientific": scientific, "receipt_sha256": sha256(receipt_bytes).hexdigest()}
    if not prefix.issubset(by_key):
        raise ValueError("finite-look merge requires a complete declared boundary")
    validate_matched_sample_hashes(item["scientific"] for item in by_key.values())
    return {
        "schema": "campaign_local_look_merge_receipt_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "completed_look": look,
        "completed_boundary_units": len(prefix),
        "units": [
            {"unit_key": key, **by_key[key]}
            for key in plan.unit_keys if key in by_key
        ],
    }


def _publish_look_merge_receipt(
    *, plan: CampaignWorkPlan, look: int, terminal_records: tuple[dict[str, Any], ...], root: Path,
) -> str:
    """Seal and reverify the complete look's local evidence before assessment."""
    payload = _build_look_merge_receipt(
        plan=plan, look=look, terminal_records=terminal_records, root=root,
    )
    path = root / f"look-{look}-merge-receipt.json"
    _publish_stop_receipt(path=path, receipt=payload)
    return sha256(path.read_bytes()).hexdigest()


def _existing_stop_receipt(path: Path, *, plan: CampaignWorkPlan) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        receipt = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("retained finite-look receipt is unreadable") from error
    if not isinstance(receipt, dict) or receipt.get("schema") != "campaign_look_stop_receipt_v2":
        raise ValueError("retained finite-look receipt has an invalid schema")
    if receipt.get("campaign_spec_digest") != plan.campaign_spec_digest or receipt.get("campaign_plan_digest") != plan.campaign_plan_digest:
        raise ValueError("retained finite-look receipt differs from frozen scientific identity")
    return receipt


def _failure_count_receipt_path(root: Path) -> Path:
    return root / "failure-count-receipt.json"


def _failure_count_unit_records(
    *, plan: CampaignWorkPlan, root: Path,
) -> tuple[dict[str, Any], ...]:
    """Load only sealed failure-count worker products in frozen ordinal order.

    A retried interrupted unit gets a new immutable attempt directory.  The
    reducer selects its one sealed terminal and rejects competing terminals,
    rather than reopening or replacing any retained receipt.
    """
    expected = {unit.key: (ordinal, unit) for ordinal, unit in enumerate(plan.units, start=1)}
    by_key: dict[str, list[dict[str, Any]]] = {}
    evidence_root = root / "failure-count-units"
    if not evidence_root.exists():
        return ()
    if evidence_root.is_symlink() or not evidence_root.is_dir():
        raise ValueError("failure-count evidence root must be a regular directory")
    for receipt_path in sorted(evidence_root.glob("*/receipt.json")):
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise ValueError("failure-count unit receipt must be a regular file")
        raw = receipt_path.read_bytes()
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("failure-count unit receipt is unreadable") from error
        if not isinstance(record, dict) or record.get("schema") != "campaign_failure_count_unit_receipt_v1":
            raise ValueError("failure-count unit receipt has an invalid schema")
        key, ordinal = record.get("unit_key"), record.get("ordinal")
        expected_unit = expected.get(key) if isinstance(key, str) else None
        if expected_unit is None or ordinal != expected_unit[0]:
            raise ValueError("failure-count unit receipt differs from frozen ordinal identity")
        if record.get("campaign_spec_digest") != plan.campaign_spec_digest or record.get("campaign_plan_digest") != plan.campaign_plan_digest:
            raise ValueError("failure-count unit receipt differs from frozen plan")
        if record.get("state") not in {"sealed_terminal", "sealed_interrupted"}:
            raise ValueError("failure-count unit receipt has an invalid sealed state")
        if canonical_json_bytes(record) + b"\n" != raw:
            raise ValueError("failure-count unit receipt is not canonical sealed bytes")
        by_key.setdefault(key, []).append({**record, "receipt_path": str(receipt_path), "receipt_sha256": sha256(raw).hexdigest()})
    selected: list[dict[str, Any]] = []
    for key, (ordinal, unit) in expected.items():
        records = by_key.get(key, [])
        terminals = [record for record in records if record["state"] == "sealed_terminal"]
        if len(terminals) > 1:
            raise ValueError("failure-count evidence has competing terminal attempts")
        if terminals:
            record = terminals[0]
            scientific = record.get("scientific")
            if not isinstance(scientific, Mapping) or scientific.get("unit_key") != key:
                raise ValueError("failure-count terminal receipt lacks frozen scientific facts")
            terminal = scientific.get("terminal_fact")
            if (not isinstance(terminal, Mapping) or terminal.get("unit_key") != key
                    or type(terminal.get("logical_failure")) is not bool):
                raise ValueError("failure-count terminal receipt lacks a verified failure fact")
            selected.append(record)
        elif records:
            # An interruption is preserved and makes the campaign incomplete;
            # it may be retried only in a fresh attempt directory.
            selected.append(max(records, key=lambda item: int(item.get("attempt", 0))))
    return tuple(sorted(selected, key=lambda item: int(item["ordinal"])))


def _failure_count_merge(
    *, plan: CampaignWorkPlan, terminal_records: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Build the compact, digest-bound merge used by a stop or censor receipt."""
    ordered: list[dict[str, Any]] = []
    for record in terminal_records:
        scientific = record["scientific"]
        ordered.append({
            "ordinal": record["ordinal"], "unit_key": record["unit_key"],
            "receipt_sha256": record["receipt_sha256"],
            "terminal_fact": scientific["terminal_fact"], "work_vector": scientific["work_vector"],
        })
    return {
        "schema": "failure_count_merge_receipt_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "ordered_terminal_records": ordered,
    }


def _publish_failure_count_unit(
    *, root: Path, plan: CampaignWorkPlan, unit: Mapping[str, Any], ordinal: int,
    attempt: int, unit_runner: Callable[[dict[str, Any], str], Mapping[str, Any]],
) -> None:
    """Run one frozen shot and publish an immutable terminal/interruption fact."""
    evidence_root = root / "failure-count-units"
    evidence_root.mkdir(parents=True, exist_ok=True)
    destination = evidence_root / f"{ordinal:09d}-{unit['unit_key']}-attempt-{attempt:03d}"
    if destination.exists():
        raise ValueError("failure-count attempt destination already exists")
    staging_input = tempfile.mkdtemp(prefix=".failure-count-input-", dir=root)
    started = time.monotonic_ns()
    environment = _allowlisted_thread_environment()
    try:
        try:
            result = unit_runner(dict(unit), staging_input)
            ended = time.monotonic_ns()
            local = _unit_record(
                unit=unit, result=result, started_ns=started, ended_ns=ended,
                environment=environment, process_id=os.getpid(),
            )
            record: dict[str, Any] = {
                "schema": "campaign_failure_count_unit_receipt_v1", "state": "sealed_terminal",
                "campaign_spec_digest": plan.campaign_spec_digest, "campaign_plan_digest": plan.campaign_plan_digest,
                "unit_key": unit["unit_key"], "ordinal": ordinal, "attempt": attempt,
                "scientific": local["scientific"], "observation": local["observation"],
            }
        except BaseException as error:
            ended = time.monotonic_ns()
            record = {
                "schema": "campaign_failure_count_unit_receipt_v1", "state": "sealed_interrupted",
                "campaign_spec_digest": plan.campaign_spec_digest, "campaign_plan_digest": plan.campaign_plan_digest,
                "unit_key": unit["unit_key"], "ordinal": ordinal, "attempt": attempt,
                "error_type": type(error).__name__,
                "observation": {"started_monotonic_ns": started, "ended_monotonic_ns": ended,
                                "process_id": os.getpid(), "environment": environment},
            }
        staging = Path(tempfile.mkdtemp(prefix=".failure-count-unit-", dir=evidence_root))
        try:
            seal_receipt(path=staging / "receipt.json", receipt=record)
            publish_sealed_shard(staging=staging, destination=destination)
        except BaseException:
            if staging.exists():
                shutil.rmtree(staging)
            raise
    finally:
        shutil.rmtree(staging_input, ignore_errors=True)


def _failure_count_receipt(
    *, plan: CampaignWorkPlan, stopping: FailureCountStoppingV1,
    terminal_records: tuple[dict[str, Any], ...], max_shots: int,
) -> dict[str, Any]:
    """Reconstruct a terminal receipt exclusively from sealed ordered evidence."""
    terminal = tuple(record for record in terminal_records if record["state"] == "sealed_terminal")
    if tuple(record["ordinal"] for record in terminal) != tuple(range(1, len(terminal) + 1)):
        raise ValueError("failure-count completion must be an exact ordered prefix")
    merge = _failure_count_merge(plan=plan, terminal_records=terminal)
    failure_ordinals = tuple(
        int(record["ordinal"]) for record in terminal
        if record["scientific"]["terminal_fact"]["logical_failure"]
    )
    reached = len(failure_ordinals) >= stopping.target_failures
    if reached:
        target_ordinal = failure_ordinals[stopping.target_failures - 1]
        batch_end = ((target_ordinal - 1) // stopping.batch_size + 1) * stopping.batch_size
        if len(terminal) != min(batch_end, len(plan.units)):
            raise ValueError("target receipt requires the complete authorized terminal batch")
        tail = tuple(range(target_ordinal + 1, len(terminal) + 1))
        state = "target_reached"
        assessment_status = "target_reached_pending_statistical_assessment"
        prefix = terminal[:target_ordinal]
    else:
        if len(terminal) != max_shots:
            raise ValueError("cap-censored receipt requires the frozen first cap")
        target_ordinal = None
        tail = ()
        state = "cap_censored"
        assessment_status = "inconclusive_cap_censored"
        prefix = terminal
    prefix_digest = sha256(canonical_json_bytes(_failure_count_merge(plan=plan, terminal_records=prefix))).hexdigest()
    tail_records = tuple(record for record in terminal if int(record["ordinal"]) in set(tail))
    tail_digest = sha256(canonical_json_bytes(_failure_count_merge(plan=plan, terminal_records=tail_records))).hexdigest()
    payload: dict[str, Any] = {
        "schema": "failure_count_stop_receipt_v1" if reached else "failure_count_censor_receipt_v1",
        "campaign_spec_digest": plan.campaign_spec_digest, "campaign_plan_digest": plan.campaign_plan_digest,
        "terminal_state": state, "assessment_status": assessment_status,
        "target_failures": stopping.target_failures, "batch_size": stopping.batch_size,
        "max_shots": max_shots, "total_completed_shots": len(terminal),
        "cumulative_failures": len(failure_ordinals), "terminal_failure_ordinal": target_ordinal,
        "inferential_prefix_count": len(prefix), "inferential_prefix_sha256": prefix_digest,
        "authorized_tail_ordinals": list(tail), "authorized_tail_count": len(tail),
        "authorized_tail_sha256": tail_digest,
        "sealed_merge": merge, "sealed_merge_sha256": sha256(canonical_json_bytes(merge)).hexdigest(),
        "actual_work": {"completed_shots": len(terminal), "tail_shots": len(tail),
                        "bp_calls": sum(int(record["scientific"]["work_vector"].get("bp_calls", 0)) for record in terminal)},
    }
    if reached:
        payload["cumulative_failures_before_terminal"] = stopping.target_failures - 1
        payload["cumulative_failures_at_terminal"] = stopping.target_failures
    return payload


def verify_failure_count_receipt(*, plan: CampaignWorkPlan, output_root: str | Path) -> dict[str, Any]:
    """Independently rebuild and byte-compare a failure-count terminal receipt."""
    root = Path(output_root)
    path = _failure_count_receipt_path(root)
    if path.is_symlink() or not path.is_file():
        raise ValueError("failure-count terminal receipt is unavailable")
    try:
        retained = json.loads(path.read_bytes())
    except json.JSONDecodeError as error:
        raise ValueError("failure-count terminal receipt is unreadable") from error
    if not isinstance(retained, dict):
        raise ValueError("failure-count terminal receipt has an invalid shape")
    stopping = FailureCountStoppingV1(
        mode="failure_count", target_failures=retained.get("target_failures"), batch_size=retained.get("batch_size"),
        shot_order="campaign_cohort_point_sample_ordinal_v1", failure_event="decoder_logical_failure_v1",
        terminal_batch_authorization_sha256="0" * 64, cap_authorization_sha256="0" * 64,
        terminal_state="cap_censored", cumulative_failures_at_terminal=0,
    )
    records = _failure_count_unit_records(plan=plan, root=root)
    if any(record["state"] != "sealed_terminal" for record in records):
        raise ValueError("failure-count terminal receipt cannot use interrupted evidence")
    expected = _failure_count_receipt(
        plan=plan, stopping=stopping, terminal_records=records, max_shots=retained.get("max_shots"),
    )
    if retained != expected or path.read_bytes() != canonical_json_bytes(expected) + b"\n":
        raise ValueError("failure-count receipt differs from sealed evidence")
    return expected


def dispatch_failure_count_batches(
    plan: CampaignWorkPlan, *, output_root: str | Path, workers: int,
    unit_runner: Callable[[dict[str, Any], str], Mapping[str, Any]], stopping: FailureCountStoppingV1,
    max_shots: int | None = None, fault_after_terminal_merge: bool = False,
) -> dict[str, Any]:
    """Run whole local batches until the target-th failure or the frozen cap.

    The controller deliberately accepts one arm per plan: an ordinal is a
    physical shot, not an arm-dependent completion event.  Multi-arm controlled
    comparisons retain their existing paired execution path and need an
    explicit per-arm failure-count reducer before they can enter this route.
    """
    if not isinstance(plan, CampaignWorkPlan) or not isinstance(stopping, FailureCountStoppingV1):
        raise ValueError("failure-count dispatch requires a frozen plan and stopping contract")
    if type(workers) is not int or workers != 1:
        raise ValueError("failure-count local dispatch currently requires exactly one worker")
    if not callable(unit_runner) or type(fault_after_terminal_merge) is not bool:
        raise ValueError("failure-count dispatch received invalid runner or fault flag")
    if plan.units_per_sample_group != 1:
        raise ValueError("failure-count dispatch requires one frozen decoder arm")
    cap = len(plan.units) if max_shots is None else max_shots
    if type(cap) is not int or cap < stopping.batch_size or cap > len(plan.units) or cap % stopping.batch_size:
        raise ValueError("failure-count max_shots must be a whole authorized batch within the frozen plan")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    path = _failure_count_receipt_path(root)
    if path.exists():
        receipt = verify_failure_count_receipt(plan=plan, output_root=root)
        if receipt["max_shots"] != cap:
            raise ValueError("failure-count retained receipt differs from requested frozen cap")
        return {"status": "terminal", "receipt": receipt, "recovered_receipt": False,
                "terminal_unit_keys": [record["unit_key"] for record in _failure_count_unit_records(plan=plan, root=root)]}
    records = _failure_count_unit_records(plan=plan, root=root)
    terminals = tuple(record for record in records if record["state"] == "sealed_terminal")
    interrupted = tuple(record for record in records if record["state"] != "sealed_terminal")
    if interrupted:
        if len(interrupted) != 1:
            raise ValueError("failure-count interruption does not leave one resumable unit")
        retry = interrupted[0]
        _publish_failure_count_unit(
            root=root, plan=plan, unit=plan.units[int(retry["ordinal"]) - 1].payload(),
            ordinal=int(retry["ordinal"]), attempt=int(retry["attempt"]) + 1, unit_runner=unit_runner,
        )
        records = _failure_count_unit_records(plan=plan, root=root)
        if any(record["state"] != "sealed_terminal" for record in records):
            return {"status": "incomplete", "receipt": None, "recovered_receipt": False,
                    "incomplete_unit_keys": [record["unit_key"] for record in records if record["state"] != "sealed_terminal"],
                    "resumable_unit_keys": [record["unit_key"] for record in records if record["state"] != "sealed_terminal"]}
    if tuple(record["ordinal"] for record in records) != tuple(range(1, len(records) + 1)):
        raise ValueError("failure-count completed evidence is not an ordered frozen prefix")
    completed = len(records)
    failures = sum(bool(record["scientific"]["terminal_fact"]["logical_failure"]) for record in records)
    while completed < cap and failures < stopping.target_failures:
        batch_end = min(completed + stopping.batch_size, cap)
        for ordinal in range(completed + 1, batch_end + 1):
            unit = plan.units[ordinal - 1].payload()
            attempts = sum(record["unit_key"] == unit["unit_key"] for record in records) + 1
            _publish_failure_count_unit(root=root, plan=plan, unit=unit, ordinal=ordinal,
                                        attempt=attempts, unit_runner=unit_runner)
        records = _failure_count_unit_records(plan=plan, root=root)
        if any(record["state"] != "sealed_terminal" for record in records):
            return {"status": "incomplete", "receipt": None, "recovered_receipt": False,
                    "incomplete_unit_keys": [record["unit_key"] for record in records if record["state"] != "sealed_terminal"],
                    "resumable_unit_keys": [record["unit_key"] for record in records if record["state"] != "sealed_terminal"]}
        completed = len(records)
        failures = sum(bool(record["scientific"]["terminal_fact"]["logical_failure"]) for record in records)
    receipt = _failure_count_receipt(plan=plan, stopping=stopping, terminal_records=records, max_shots=cap)
    merge_path = root / "failure-count-merge.json"
    _publish_stop_receipt(path=merge_path, receipt=receipt["sealed_merge"])
    if fault_after_terminal_merge:
        raise InterruptedError("injected interruption after terminal merge before stop receipt")
    _publish_stop_receipt(path=path, receipt=receipt)
    return {"status": "terminal", "receipt": verify_failure_count_receipt(plan=plan, output_root=root),
            "recovered_receipt": True, "terminal_unit_keys": [record["unit_key"] for record in records]}


def dispatch_finite_looks(
    plan: CampaignWorkPlan, *, output_root: str | Path, workers: int,
    unit_runner: Callable[[dict[str, Any], str], Mapping[str, Any]],
    decision_for_look: Callable[..., Mapping[str, Any]], fault_after_decision: bool = False,
) -> dict[str, Any]:
    """Dispatch whole frozen looks and recover a stop receipt before later work.

    The decision callback is pure assessment algebra supplied by the caller.
    This controller only establishes complete boundaries, preserves observed
    records, and atomically retains the resulting authorization receipt.
    """
    if not isinstance(plan, CampaignWorkPlan) or not callable(decision_for_look):
        raise ValueError("finite-look dispatch requires a frozen plan and pure decision callback")
    if type(fault_after_decision) is not bool:
        raise ValueError("fault_after_decision must be a boolean test injection")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    receipt_path = root / "look-stop-receipt.json"
    retained = _existing_stop_receipt(receipt_path, plan=plan)
    retained_look: int | None = None
    if retained is not None:
        retained_look = retained.get("completed_look")
        if type(retained_look) is not int or not 1 <= retained_look <= len(plan.look_boundaries):
            raise ValueError("retained finite-look receipt names an invalid look")
        sealed = _sealed_local_records(root)
        terminal_keys = {record["unit_key"] for record in sealed if record["state"] == "sealed_terminal"}
        if not set(plan.completed_prefix(retained_look)).issubset(terminal_keys):
            raise ValueError("retained finite-look receipt lacks its complete boundary")

    for look in range(1, len(plan.look_boundaries) + 1):
        records = _sealed_local_records(root)
        terminals = tuple(record for record in records if record["state"] == "sealed_terminal")
        prefix = plan.completed_prefix(look)
        terminal_by_key = {record["unit_key"]: record for record in terminals}
        if set(prefix).issubset(terminal_by_key):
            merge_sha256 = _publish_look_merge_receipt(
                plan=plan, look=look, terminal_records=terminals, root=root,
            )
            decision_records = tuple(terminal_by_key[key]["scientific"]["terminal_fact"] for key in prefix)
            decision = decision_for_look(look=look, terminal_records=decision_records)
            if not isinstance(decision, Mapping):
                raise ValueError("finite-look decision callback must return a mapping")
            if retained_look == look and decision.get("should_stop") is not True:
                raise ValueError("retained finite-look receipt conflicts with reconstructed decision")
            if retained_look is not None and look < retained_look and decision.get("should_stop") is True:
                raise ValueError("retained finite-look receipt follows an earlier reconstructed stop")
            if decision.get("should_stop") is True:
                receipt = _deterministic_look_stop_receipt(
                    plan=plan, look=look, terminal_records=terminals, decision=decision,
                    merge_receipt_sha256=merge_sha256,
                )
                if fault_after_decision:
                    raise InterruptedError("injected interruption after decision before receipt publication")
                _publish_stop_receipt(path=receipt_path, receipt=receipt)
                return {
                    "schema": "campaign_finite_look_dispatch_v1", "stopped": True,
                    "recovered_stop_receipt": retained is None, "stop_receipt": receipt,
                    "authorized_undispatched_keys": tuple(receipt["authorized_undispatched"]),
                    "records": _sealed_local_records(root),
                }
            if retained_look == look:
                raise ValueError("retained finite-look receipt was not reconstructed")
            continue
        look_shards = tuple(shard for shard in plan.shards if shard.look == look)
        execution = execute_local_work_plan(
            plan, output_root=root, workers=workers, unit_runner=unit_runner, shards=look_shards,
        )
        records = _sealed_local_records(root)
        terminals = tuple(record for record in records if record["state"] == "sealed_terminal")
        terminal_by_key = {record["unit_key"]: record for record in terminals}
        if not set(prefix).issubset(terminal_by_key):
            return {
                "schema": "campaign_finite_look_dispatch_v1", "stopped": False,
                "recovered_stop_receipt": False, "stop_receipt": None,
                "authorized_undispatched_keys": (), "execution": execution, "records": records,
            }
        merge_sha256 = _publish_look_merge_receipt(
            plan=plan, look=look, terminal_records=terminals, root=root,
        )
        decision_records = tuple(terminal_by_key[key]["scientific"]["terminal_fact"] for key in prefix)
        decision = decision_for_look(look=look, terminal_records=decision_records)
        if not isinstance(decision, Mapping):
            raise ValueError("finite-look decision callback must return a mapping")
        if decision.get("should_stop") is True:
            receipt = _deterministic_look_stop_receipt(
                plan=plan, look=look, terminal_records=terminals, decision=decision,
                merge_receipt_sha256=merge_sha256,
            )
            if fault_after_decision:
                raise InterruptedError("injected interruption after decision before receipt publication")
            _publish_stop_receipt(path=receipt_path, receipt=receipt)
            return {
                "schema": "campaign_finite_look_dispatch_v1", "stopped": True,
                "recovered_stop_receipt": False, "stop_receipt": receipt,
                "authorized_undispatched_keys": tuple(receipt["authorized_undispatched"]),
                "records": _sealed_local_records(root),
            }
    records = _sealed_local_records(root)
    if retained is not None:
        raise ValueError("retained finite-look receipt has no reconstructed stopping look")
    return {"schema": "campaign_finite_look_dispatch_v1", "stopped": False,
            "recovered_stop_receipt": False, "stop_receipt": None,
            "authorized_undispatched_keys": (), "records": records}


def run_one_unit(
    spec: CampaignSpecV1, *, campaign_root: str | Path, output_root: str | Path,
    worker_label: str,
) -> dict[str, Any]:
    """Run exactly the frozen legacy tracer unit; worker label is observational."""
    if not isinstance(worker_label, str) or not worker_label:
        raise ValueError("worker_label must be a nonempty observational label")
    plan = build_one_unit_plan(spec)
    root = Path(campaign_root)
    manifest = _resolve_manifest(root, spec)
    context = canonical_public_shot_context(manifest, shot_id=spec.sample_id)
    if context.decoder_seed_identity != spec.decoder_seed_identity:
        raise ValueError("inner manifest decoder randomness differs from campaign specification")
    destination_root = Path(output_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / f"shard-{plan.shard_id}"
    if destination.exists():
        raise ValueError("sealed campaign shard already exists and cannot be reopened")
    staging = Path(tempfile.mkdtemp(prefix=".campaign-stage-", dir=destination_root))
    try:
        ledger_path = staging / "events.jsonl"
        run_canonical_one(manifest, shot_id=spec.sample_id, ledger_path=ledger_path)
        ledger = ledger_path.read_bytes()
        from ..ledger import read_canonical_events_bytes
        events = read_canonical_events_bytes(ledger)
        terminal_fact = _terminal_fact(events, unit_key=plan.unit_key)
        receipt = {
            "schema": "campaign_shard_receipt_v1", "campaign_spec": spec.model_dump(mode="json", by_alias=True),
            "campaign_spec_digest": plan.campaign_spec_digest, "campaign_plan_digest": plan.campaign_plan_digest,
            "unit_key": plan.unit_key, "shard_id": plan.shard_id,
            "physical_sample_identity": plan.physical_sample_identity,
            "canonical_sample_identity": context.sample_seed_identity,
            "decoder_randomness_identity": plan.decoder_randomness_identity,
            "ledger_sha256": sha256(ledger).hexdigest(), "ledger_bytes": len(ledger),
            "terminal_fact": terminal_fact, "executor_observation": {"worker_label": worker_label},
        }
        seal_receipt(path=staging / "receipt.json", receipt=receipt)
        publish_sealed_shard(staging=staging, destination=destination)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return {**receipt, "receipt_path": str(destination / "receipt.json"),
            "campaign_spec_bytes": plan.campaign_spec_bytes, "campaign_plan_preimage": plan.campaign_plan_preimage}


def _work_manifest_path(root: Path, path_text: str, expected_sha256: str) -> Path:
    """Resolve one declared arm without allowing path or byte substitution."""
    candidate = root.joinpath(*Path(path_text).parts)
    if candidate.is_symlink() or not candidate.is_file() or root not in candidate.resolve().parents:
        raise ValueError("campaign arm manifest must be a confined regular file")
    if sha256(candidate.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("campaign arm manifest bytes differ from the frozen hash")
    return candidate


def _matrix_sha256(context: Any) -> str:
    code = context.code
    return sha256(code.hx.tobytes(order="C") + b"\0" + code.hz.tobytes(order="C")).hexdigest()


def _preflight_work_arms(spec: CampaignWorkSpecV1, root: Path) -> dict[str, tuple[Path, Any]]:
    """Reject equal labels with unequal physical inputs before any evidence write."""
    resolved: dict[str, tuple[Path, Any]] = {}
    required = spec.shared_sampler
    for arm in spec.arms:
        path = _work_manifest_path(root, arm.manifest_path, arm.manifest_sha256)
        context = canonical_public_manifest_context(path, manifest_bytes=path.read_bytes())
        manifest = context.manifest
        actual = {
            "code_id": manifest.artifact.code_id,
            "artifact_raw_sha256": manifest.artifact.raw_sha256,
            "artifact_semantic_sha256": manifest.artifact.semantic_sha256,
            "matrix_sha256": _matrix_sha256(context),
            "x_error_rate": manifest.error_rate,
            "physical_sample_namespace": manifest.randomness.physical_sample_identity or context.manifest_sha256,
            "physical_sample_seed": manifest.randomness.sample_seed,
        }
        expected = {
            "code_id": required.code_id, "artifact_raw_sha256": required.artifact_raw_sha256,
            "artifact_semantic_sha256": required.artifact_semantic_sha256,
            "matrix_sha256": required.matrix_sha256, "x_error_rate": required.x_error_rate,
            "physical_sample_namespace": required.physical_sample_namespace,
            "physical_sample_seed": required.physical_sample_seed,
        }
        if actual != expected:
            raise ValueError("campaign arms have incompatible code or channel sampling material")
        if manifest.randomness.decoder_seed_identity != arm.decoder_seed_identity:
            raise ValueError("campaign arm decoder seed differs from its frozen manifest")
        resolved[arm.arm_id] = (path, context)
    return resolved


def _sample_digest(domain: str, payload: object) -> str:
    return sha256(domain.encode("ascii") + b"\0" + canonical_json_bytes(payload)).hexdigest()


def _materialized_from_sample(*, plan: CampaignWorkPlan, unit: Any, spec: CampaignWorkSpecV1, sample: sampling.ShotSample) -> MaterializedPhysicalSampleV1:
    observations = {
        name: {
            "check_type": observed.check_type, "dtype": observed.syndrome.dtype.name,
            "shape": list(observed.syndrome.shape),
            "bytes_b64": base64.b64encode(observed.syndrome.tobytes(order="C")).decode("ascii"),
        }
        for name, observed in sorted(sample.observations.items())
    }
    x_b64 = base64.b64encode(sample.hidden.x.tobytes(order="C")).decode("ascii")
    z_b64 = base64.b64encode(sample.hidden.z.tobytes(order="C")).decode("ascii")
    error_sha = _sample_digest("bp-registry-physical-error-v1", {"x": x_b64, "z": z_b64})
    unsigned = {
        "schema": "materialized_physical_sample_v1", "physical_sample_identity": unit.physical_sample_identity,
        "sample_seed_identity": sample.sample_identity, "cohort_id": unit.cohort_id, "point_id": unit.point_id,
        "sample_namespace": unit.sample_namespace, "sample_id": unit.sample_id,
        "sampler_contract_sha256": spec.shared_sampler.digest(),
        "x_dtype": "uint8", "x_shape": list(sample.hidden.x.shape), "x_bytes_b64": x_b64,
        "z_dtype": "uint8", "z_shape": list(sample.hidden.z.shape), "z_bytes_b64": z_b64,
        "observations": observations, "physical_error_sha256": error_sha,
    }
    return MaterializedPhysicalSampleV1.model_validate({
        **unsigned,
        "materialized_sample_sha256": _sample_digest("bp-registry-materialized-sample-v1", unsigned),
    })


def _shot_from_materialized(artifact: MaterializedPhysicalSampleV1) -> sampling.ShotSample:
    """Decode immutable bytes back to the exact typed sample given to the runner."""
    import numpy as np
    x = np.frombuffer(base64.b64decode(artifact.x_bytes_b64), dtype=np.uint8).copy().reshape(artifact.x_shape)
    z = np.frombuffer(base64.b64decode(artifact.z_bytes_b64), dtype=np.uint8).copy().reshape(artifact.z_shape)
    observations = {}
    for name, encoded in artifact.observations.items():
        if set(encoded) != {"check_type", "dtype", "shape", "bytes_b64"} or encoded["dtype"] != "uint8":
            raise ValueError("materialized observation has an invalid field set")
        vector = np.frombuffer(base64.b64decode(encoded["bytes_b64"], validate=True), dtype=np.uint8).copy().reshape(tuple(encoded["shape"]))
        observations[name] = sampling.DecoderObservation(encoded["check_type"], vector)
    if set(observations) != {"X", "Z"}:
        raise ValueError("materialized sample must retain both CSS observations")
    from types import MappingProxyType
    return sampling.ShotSample(
        shot_id=artifact.sample_id, sample_identity=artifact.sample_seed_identity,
        hidden=sampling.HiddenTruth(x, z), observation=observations["Z"],
        observations=MappingProxyType(observations),
    )


def materialize_campaign_sample(
    *, plan: CampaignWorkPlan, unit: Any, spec: CampaignWorkSpecV1,
    context: Any, destination: Path, resource_guard: CanonicalRuntimeGuardV1 | None = None,
) -> MaterializedPhysicalSampleV1:
    """Sample once, atomically retain exact bytes, and independently reload them."""
    sample = sampling.sample_shot(
        context.code, manifest_identity=spec.shared_sampler.physical_sample_namespace,
        seed=spec.shared_sampler.physical_sample_seed, shot_id=unit.sample_id,
        x_error_rate=spec.shared_sampler.x_error_rate, z_error_rate=spec.shared_sampler.z_error_rate,
    )
    artifact = _materialized_from_sample(plan=plan, unit=unit, spec=spec, sample=sample)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = artifact.primitive_bytes() + b"\n"
    if destination.exists():
        if destination.is_symlink() or destination.read_bytes() != payload:
            raise ValueError("materialized sample destination conflicts with immutable bytes")
    elif resource_guard is None:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".materialized-", delete=False) as handle:
            handle.write(payload)
            staging = Path(handle.name)
        try:
            os.replace(staging, destination)
        finally:
            if staging.exists():
                staging.unlink()
    else:
        guarded_atomic_write_bytes(
            destination, payload, resource_guard=resource_guard,
            boundary="campaign:materialized_sample",
        )
    reloaded = MaterializedPhysicalSampleV1.model_validate_json(destination.read_bytes())
    if reloaded.materialized_sample_sha256 != artifact.materialized_sample_sha256 or _shot_from_materialized(reloaded).hidden.x.tobytes() != sample.hidden.x.tobytes():
        raise ValueError("materialized sample reload differs from the sampled physical bytes")
    return reloaded


def _campaign_terminal_fact(events: list[dict[str, Any]], *, unit_key: str) -> dict[str, Any]:
    """Translate only supported canonical terminal semantics into campaign classes."""
    terminal_fact = _terminal_fact(events, unit_key=unit_key)
    if terminal_fact["outcome"] == "logical_failure":
        terminal_fact["outcome"] = "wrong_logical_action"
    elif terminal_fact["outcome"] is None and terminal_fact["termination"] == "max_iterations":
        terminal_fact["outcome"] = "nonconvergence"
    elif (terminal_fact["outcome"] is None and terminal_fact["termination"] == "completed"
          and next(event for event in events if event["kind"] == "termination")["data"].get("selection_status") == "unavailable_due_to_stopping"
          and any(event.get("kind") == "work" and event.get("data", {}).get("relay_stopping_reason") == "leg_limit"
                  for event in events)):
        terminal_fact["outcome"] = "nonconvergence"
    elif terminal_fact["outcome"] not in {
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
        "infrastructure_interruption",
    }:
        raise ValueError("canonical terminal outcome cannot be mapped into the frozen campaign taxonomy")
    return terminal_fact


def _campaign_attempt(
    *, plan: CampaignWorkPlan, unit: Any, arm_path: Path, sample_path: Path,
    materialized: MaterializedPhysicalSampleV1, ledger_path: Path,
) -> dict[str, Any]:
    ledger_bytes = ledger_path.read_bytes()
    events = read_canonical_events(ledger_path)
    # The canonical ledger remains byte-for-byte unchanged.  The outer
    # receipt supplies the assessment taxonomy and verification repeats it.
    terminal_fact = _campaign_terminal_fact(events, unit_key=unit.key)
    work_vectors = [event.get("data", {}).get("work_vector") for event in events if isinstance(event.get("data"), Mapping) and "work_vector" in event["data"]]
    if not work_vectors or any(not isinstance(vector, Mapping) for vector in work_vectors):
        raise ValueError("canonical ledger lacks a named work vector")
    work_vector = dict(work_vectors[-1])
    if (not work_vector or any(not isinstance(name, str) or not name or type(value) is not int or value < 0
                               for name, value in work_vector.items())):
        raise ValueError("canonical ledger work vector is invalid")
    if any(dict(vector) != work_vector for vector in work_vectors):
        raise ValueError("canonical ledger work vectors conflict")
    attempt = {
        "schema": "campaign_attempt_receipt_v1", "attempt_id": _sample_digest("bp-registry-campaign-attempt-v1", {"plan": plan.campaign_plan_digest, "unit": unit.key}),
        "campaign_plan_digest": plan.campaign_plan_digest, "unit_key": unit.key,
        "state": "sealed_terminal", "lifecycle": ["planned", "running", "sealed_terminal"],
        "parent_attempt_receipt": None,
    }
    shard = next((item for item in plan.shards if unit.key in item.unit_keys), None)
    if shard is None:
        raise ValueError("canonical attempt unit is absent from the frozen shard plan")
    receipt = {
        "schema": "campaign_canonical_attempt_v1", "attempt": attempt,
        "campaign_spec_digest": plan.campaign_spec_digest, "campaign_plan_digest": plan.campaign_plan_digest,
        "unit_key": unit.key, "selected_shard_id": shard.shard_id,
        "arm_manifest_path": str(arm_path), "arm_manifest_sha256": sha256(arm_path.read_bytes()).hexdigest(),
        "materialized_sample_path": str(sample_path),
        "materialized_sample_sha256": materialized.materialized_sample_sha256,
        "physical_error_sha256": materialized.physical_error_sha256,
        "canonical_ledger_path": str(ledger_path), "canonical_ledger_sha256": sha256(ledger_bytes).hexdigest(),
        "terminal_fact": terminal_fact, "work_vector": dict(sorted(work_vector.items())),
    }
    receipt_bytes = canonical_json_bytes(receipt)
    return {**receipt, "receipt_sha256": sha256(receipt_bytes).hexdigest(), "events": events,
            "terminal_bytes_sha256": sha256(canonical_json_bytes(terminal_fact)).hexdigest(),
            "persisted_sample_sha256": materialized.materialized_sample_sha256,
            "validation_status": "verified", "replay_status": "verified"}


def verify_canonical_attempt(*, record: Mapping[str, Any], plan: CampaignWorkPlan) -> dict[str, Any]:
    """Independently rehash paired evidence before it can enter a campaign merge."""
    if not isinstance(record, Mapping):
        raise ValueError("canonical attempt verification requires a frozen work plan")
    spec = _campaign_work_spec(plan)
    required = {"schema", "attempt", "campaign_spec_digest", "campaign_plan_digest", "unit_key", "selected_shard_id", "arm_manifest_path", "arm_manifest_sha256", "materialized_sample_path", "materialized_sample_sha256", "physical_error_sha256", "canonical_ledger_path", "canonical_ledger_sha256", "terminal_fact", "work_vector", "receipt_sha256", "events", "terminal_bytes_sha256", "persisted_sample_sha256", "validation_status", "replay_status"}
    if set(record) != required or record["schema"] != "campaign_canonical_attempt_v1":
        raise ValueError("canonical attempt receipt has an invalid field set")
    unsigned = {key: value for key, value in record.items() if key not in {"receipt_sha256", "events", "terminal_bytes_sha256", "persisted_sample_sha256", "validation_status", "replay_status"}}
    if sha256(canonical_json_bytes(unsigned)).hexdigest() != record["receipt_sha256"]:
        raise ValueError("canonical attempt receipt bytes differ from its hash")
    unit = next((item for item in plan.units if item.key == record["unit_key"]), None)
    if unit is None:
        raise ValueError("canonical attempt unit is absent from the frozen plan")
    shard = next((item for item in plan.shards if unit.key in item.unit_keys), None)
    if shard is None or record["selected_shard_id"] != shard.shard_id:
        raise ValueError("canonical attempt selected shard differs from the frozen plan")
    sample_path = Path(record["materialized_sample_path"])
    if (sample_path.is_symlink() or not sample_path.is_file()
            or sample_path.stat().st_size > spec.assessment.resources.max_storage_bytes):
        raise ValueError("canonical attempt materialized sample must be a regular file")
    materialized = MaterializedPhysicalSampleV1.model_validate_json(sample_path.read_bytes())
    if (materialized.physical_sample_identity != unit.physical_sample_identity
            or materialized.cohort_id != unit.cohort_id or materialized.point_id != unit.point_id
            or materialized.sample_namespace != unit.sample_namespace or materialized.sample_id != unit.sample_id
            or materialized.sampler_contract_sha256 != spec.shared_sampler.digest()):
        raise ValueError("canonical attempt materialized sample differs from frozen sampling bindings")
    arm = next((item for item in spec.arms if item.arm_id == unit.arm_id), None)
    if arm is None or record["arm_manifest_path"] != str(Path(arm.manifest_path)) and Path(record["arm_manifest_path"]).name != Path(arm.manifest_path).name:
        raise ValueError("canonical attempt manifest path differs from frozen arm")
    manifest = Path(record["arm_manifest_path"])
    if manifest.is_symlink() or not manifest.is_file() or sha256(manifest.read_bytes()).hexdigest() != arm.manifest_sha256 or record["arm_manifest_sha256"] != arm.manifest_sha256:
        raise ValueError("canonical attempt manifest bytes differ from frozen arm")
    ledger = Path(record["canonical_ledger_path"])
    if (ledger.is_symlink() or not ledger.is_file()
            or ledger.stat().st_size > spec.assessment.resources.max_evidence_bytes):
        raise ValueError("canonical attempt ledger must be a bounded regular file")
    if (materialized.materialized_sample_sha256 != record["materialized_sample_sha256"]
            or materialized.physical_error_sha256 != record["physical_error_sha256"]
            or sha256(ledger.read_bytes()).hexdigest() != record["canonical_ledger_sha256"]):
        raise ValueError("canonical attempt hash binding differs from retained evidence")
    events = read_canonical_events(ledger)
    terminal_fact = _campaign_terminal_fact(events, unit_key=unit.key)
    if events != record["events"] or terminal_fact != record["terminal_fact"]:
        raise ValueError("canonical attempt terminal differs from retained ledger")
    vectors = [event.get("data", {}).get("work_vector") for event in events if isinstance(event.get("data"), Mapping) and "work_vector" in event["data"]]
    if (not vectors or any(not isinstance(vector, Mapping) for vector in vectors)
            or any(dict(vector) != record["work_vector"] for vector in vectors)):
        raise ValueError("canonical attempt work vector differs from retained ledger")
    return dict(record)


def run_canonical_work_plan(
    plan: CampaignWorkPlan, *, campaign_root: str | Path, output_root: str | Path,
    shards: tuple[ShardPlan, ...] | None = None,
) -> dict[str, Any]:
    """Execute every paired arm against one retained physical sample per group."""
    if not isinstance(plan, CampaignWorkPlan) or not isinstance(plan.work_spec, CampaignWorkSpecV1):
        raise ValueError("run_canonical_work_plan requires a paired CampaignWorkPlan")
    root = Path(campaign_root).resolve(strict=True)
    destination = Path(output_root)
    if destination.exists() and (not destination.is_dir() or destination.is_symlink()):
        raise ValueError("campaign output root must be a non-symlink directory")
    arm_contexts = _preflight_work_arms(plan.work_spec, root)
    destination.mkdir(parents=True, exist_ok=True)
    selected_shards = plan.shards if shards is None else tuple(shards)
    known_shards = {shard.shard_id: shard for shard in plan.shards}
    if not selected_shards or any(known_shards.get(shard.shard_id) != shard for shard in selected_shards):
        raise ValueError("canonical execution must consume a nonempty exact subset of frozen shards")
    selected_keys = {key for shard in selected_shards for key in shard.unit_keys}
    samples: dict[str, MaterializedPhysicalSampleV1] = {}
    verified: list[dict[str, Any]] = []
    for unit in plan.units:
        if unit.key not in selected_keys:
            continue
        materialized = samples.get(unit.physical_sample_identity)
        sample_path = destination / "samples" / f"{unit.physical_sample_identity}.json"
        arm_path, context = arm_contexts[unit.arm_id]
        if materialized is None:
            materialized = materialize_campaign_sample(plan=plan, unit=unit, spec=plan.work_spec, context=context, destination=sample_path)
            samples[unit.physical_sample_identity] = materialized
        else:
            materialized = MaterializedPhysicalSampleV1.model_validate_json(sample_path.read_bytes())
        if (materialized.physical_sample_identity != unit.physical_sample_identity
                or materialized.cohort_id != unit.cohort_id or materialized.point_id != unit.point_id
                or materialized.sample_namespace != unit.sample_namespace or materialized.sample_id != unit.sample_id
                or materialized.sampler_contract_sha256 != plan.work_spec.shared_sampler.digest()):
            raise ValueError("materialized sample differs from frozen plan bindings")
        ledger_path = destination / "units" / unit.key / "events.jsonl"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        run_canonical_materialized_one(arm_path, sample=_shot_from_materialized(materialized),
                                       materialized_sample_sha256=materialized.materialized_sample_sha256,
                                       ledger_path=ledger_path, manifest_bytes=arm_path.read_bytes())
        record = _campaign_attempt(plan=plan, unit=unit, arm_path=arm_path, sample_path=sample_path,
                                   materialized=materialized, ledger_path=ledger_path)
        receipt_path = ledger_path.parent / "attempt.json"
        receipt_path.write_bytes(canonical_json_bytes({key: value for key, value in record.items() if key not in {"receipt_sha256", "events", "terminal_bytes_sha256", "persisted_sample_sha256", "validation_status", "replay_status"}}) + b"\n")
        verified.append(verify_canonical_attempt(record=record, plan=plan))
    return {"schema": "campaign_canonical_work_execution_v1", "campaign_plan_digest": plan.campaign_plan_digest,
            "shard_ids": tuple(shard.shard_id for shard in selected_shards),
            "materialized_samples": tuple(samples.values()), "verified_attempts": tuple(verified)}


def _checked_add(left: int, right: int, *, name: str) -> int:
    if type(left) is not int or type(right) is not int or left < 0 or right < 0:
        raise ValueError(f"{name} requires nonnegative integer values")
    total = left + right
    if total > 2**63 - 1:
        raise ValueError(f"{name} exceeds the supported counter range")
    return total


def _failure_count_executable_projection(
    *, plan: CampaignWorkPlan, campaign_root: Path, first_ordinal: int, batch_size: int,
    accumulated: Mapping[str, int] | None = None,
) -> tuple[CampaignWorkSpecV1, dict[str, int], Any, Any, Path]:
    """Revalidate executable facts before any bounded unit is materialized."""
    if not isinstance(plan.work_spec, FailureCountWorkSpecV1):
        raise ValueError("bounded canonical execution requires FailureCountWorkSpecV1")
    spec, policy = plan.work_spec.campaign_work_spec, plan.work_spec.policy
    required_batch = policy.batch_size if policy.dispatch_mode == "strict_full_batch" else 1
    if batch_size != required_batch or first_ordinal < 1 or first_ordinal + batch_size - 1 > len(plan.units):
        raise ValueError("bounded canonical execution requires one exact declared ordinal batch")
    if first_ordinal + batch_size - 1 > policy.caps.max_shots:
        raise ValueError("requested ordinal batch exceeds the frozen shot cap")
    arm = spec.arms[0]
    manifest_path = (campaign_root / arm.manifest_path).resolve(strict=True)
    context = canonical_public_manifest_context(manifest_path)
    derived = derive_canonical_executable_maxima(context)
    declared = policy.executable_limits.model_dump(mode="json", by_alias=True, exclude={"schema_name"})
    verify_declared_executable_limits(
        declared, expected_policy_binding=policy.policy_binding_sha256, derived=derived,
    )
    if _maximum_failure_count_partial_receipt_bytes() > derived.partial_receipt_reserve_bytes:
        raise ValueError("failure-count partial receipt cannot fit the verified control reserve")
    if policy.executable_limits.digest() != policy.batch_authorization.executable_limit_receipt_sha256:
        raise ValueError("batch authorization does not bind the verified executable limit receipt")
    projection = {
        "shots": batch_size,
        "work": batch_size * derived.derived_work_per_unit,
        "events": batch_size * derived.derived_events_per_unit,
        "evidence_bytes": _checked_add(batch_size * derived.derived_evidence_bytes_per_unit, derived.partial_receipt_reserve_bytes, name="projected evidence"),
        "storage_bytes": _checked_add(batch_size * derived.derived_storage_bytes_per_unit, derived.partial_receipt_reserve_bytes, name="projected storage"),
    }
    fresh_projection = dict(projection)
    if accumulated is not None:
        projection = {
            name: _checked_add(value, accumulated.get(name, 0), name=f"accumulated {name}")
            for name, value in projection.items()
        }
    authorization = policy.batch_authorization
    if (fresh_projection["shots"] > authorization.max_shots_per_batch
            or fresh_projection["work"] > authorization.max_work_per_batch
            or fresh_projection["events"] > authorization.max_events_per_batch
            or fresh_projection["evidence_bytes"] > authorization.max_evidence_bytes_per_batch
            or fresh_projection["storage_bytes"] > authorization.max_storage_bytes_per_batch):
        raise ValueError("bounded canonical batch exceeds its verified authorization")
    cap_values = {
        "shots": policy.caps.max_shots, "work": policy.caps.max_decoder_work,
        "events": policy.caps.max_events, "evidence_bytes": policy.caps.max_evidence_bytes,
        "storage_bytes": policy.caps.max_storage_bytes,
    }
    exhausted = next((cap for cap in policy.cap_precedence if cap != "wall" and projection.get(
        {"storage": "storage_bytes", "evidence": "evidence_bytes", "events": "events", "work": "work", "shots": "shots"}[cap], 0
    ) > cap_values[{"storage": "storage_bytes", "evidence": "evidence_bytes", "events": "events", "work": "work", "shots": "shots"}[cap]]), None)
    if exhausted is not None:
        raise ValueError(f"bounded canonical batch cannot fit hard resource cap: {exhausted}")
    return spec, projection, context, derived, manifest_path


def _maximum_failure_count_partial_receipt_bytes() -> int:
    """Bound the closed partial schema before any scientific artifact is made."""
    maximum = 2**63 - 1
    common = {
        "schema": "failure_count_partial_attempt_v1", "attempt_id": "a" * 64,
        "attempt_ordinal": _MAX_EVENTS, "attempt_sequence": _MAX_EVENTS,
        "unit_key": "u" * 512, "parent_partial_receipt_sha256": "a" * 64,
        "campaign_spec_digest": "a" * 64, "campaign_plan_digest": "a" * 64,
        "policy_sha256": "a" * 64, "authorization_sha256": "a" * 64,
        "profile_sha256": "a" * 64, "materialized_sample_path": "s" * 4096,
        "materialized_sample_sha256": "a" * 64, "canonical_ledger_path": "l" * 4096,
        "canonical_ledger_sha256": "a" * 64, "last_completed_boundary": "b" * 512,
        "attempted_bytes": _MAX_STORAGE_BYTES, "consumed_decoder_work": _MAX_DECODER_WORK,
        "consumed_events": _MAX_EVENTS, "consumed_evidence_bytes": _MAX_EVIDENCE_BYTES,
        "consumed_storage_bytes": _MAX_STORAGE_BYTES, "consumed_control_receipt_bytes": _MAX_STORAGE_BYTES,
        "completed_shot_credit": 0, "failure_credit": 0,
    }
    wall = FailureCountPartialAttemptV1(
        **common, interruption_kind="interrupted_wall", first_exhausted_cap="wall",
        deadline_ns=0, observed_ns=maximum, overshoot_ns=maximum,
    )
    byte = FailureCountPartialAttemptV1(
        **common, interruption_kind="interrupted_storage", first_exhausted_cap="storage",
        deadline_ns=None, observed_ns=None, overshoot_ns=None,
    )
    return max(len(wall.primitive_bytes()), len(byte.primitive_bytes())) + 1


def _partial_interruption_fields(snapshot: Any) -> tuple[str, str]:
    """Map the engine's closed guard outcomes into campaign receipt names."""
    if snapshot.interruption_kind == "wall_deadline":
        return "interrupted_wall", "wall"
    if snapshot.interruption_kind == "evidence_bytes":
        return "interrupted_evidence", "evidence"
    if snapshot.interruption_kind == "storage_bytes":
        return "interrupted_storage", "storage"
    raise ValueError("strict canonical guard interruption is not a resumable campaign partial")


def _seal_failure_count_partial_attempt(
    *, plan: CampaignWorkPlan, unit: Any, policy: Any, authorization: CanonicalRuntimeAuthorizationV1,
    materialized: MaterializedPhysicalSampleV1 | None, sample_path: Path, ledger_path: Path,
    snapshot: Any, receipt_path: Path, resource_guard: CanonicalRuntimeGuardV1,
    parent_partial_receipt_sha256: str | None, attempt_sequence: int,
) -> tuple[FailureCountPartialAttemptV1, str]:
    """Use the guard's reserved control bytes to retain zero-credit evidence."""
    kind, cap = _partial_interruption_fields(snapshot)
    ledger_digest = None if not ledger_path.exists() else sha256(ledger_path.read_bytes()).hexdigest()
    partial = FailureCountPartialAttemptV1(
        schema="failure_count_partial_attempt_v1",
        attempt_id=sha256(canonical_json_bytes({
            "plan": plan.campaign_plan_digest, "unit": unit.key,
            "authorization": authorization.authorization_identity,
        })).hexdigest(),
        attempt_ordinal=next(index for index, candidate in enumerate(plan.units, start=1) if candidate.key == unit.key),
        attempt_sequence=attempt_sequence,
        unit_key=unit.key, parent_partial_receipt_sha256=parent_partial_receipt_sha256,
        campaign_spec_digest=plan.campaign_spec_digest, campaign_plan_digest=plan.campaign_plan_digest,
        policy_sha256=policy.digest(), authorization_sha256=sha256(canonical_json_bytes(authorization.__dict__ if hasattr(authorization, "__dict__") else {
            "profile_digest": authorization.profile_digest, "authorization_identity": authorization.authorization_identity,
            "mode": authorization.mode, "max_events": authorization.max_events,
            "max_evidence_bytes": authorization.max_evidence_bytes, "max_storage_bytes": authorization.max_storage_bytes,
            "control_receipt_reserve_bytes": authorization.control_receipt_reserve_bytes,
            "monotonic_deadline_ns": authorization.monotonic_deadline_ns,
            "max_event_bytes": authorization.max_event_bytes, "max_artifact_bytes": authorization.max_artifact_bytes,
        })).hexdigest(),
        profile_sha256=authorization.profile_digest,
        materialized_sample_path=str(sample_path), materialized_sample_sha256=(
            None if materialized is None else materialized.materialized_sample_sha256
        ),
        canonical_ledger_path=str(ledger_path), canonical_ledger_sha256=ledger_digest,
        interruption_kind=kind, first_exhausted_cap=cap,
        last_completed_boundary=snapshot.boundary, attempted_bytes=snapshot.attempted_bytes,
        deadline_ns=snapshot.deadline_ns if kind == "interrupted_wall" else None,
        observed_ns=snapshot.after_ns if kind == "interrupted_wall" else None,
        overshoot_ns=snapshot.overshoot_ns if kind == "interrupted_wall" else None,
        consumed_decoder_work=sum(snapshot.committed_work.as_evidence(structural_event_version=4).values()),
        consumed_events=snapshot.scientific_events, consumed_evidence_bytes=snapshot.scientific_evidence_bytes,
        consumed_storage_bytes=snapshot.scientific_storage_bytes,
        consumed_control_receipt_bytes=0,
    )
    # The control receipt records its own exact byte consumption.  Iterate to
    # a fixed point because changing the decimal representation can change the
    # serialized length by one byte at a power-of-ten boundary.
    for _ in range(4):
        payload = partial.primitive_bytes() + b"\n"
        adjusted = partial.model_copy(update={"consumed_control_receipt_bytes": len(payload)})
        if adjusted.primitive_bytes() + b"\n" == payload:
            partial = adjusted
            break
        partial = adjusted
    else:
        raise ValueError("partial receipt byte accounting did not stabilize")
    payload = partial.primitive_bytes() + b"\n"
    guarded_atomic_write_bytes(
        receipt_path, payload, resource_guard=resource_guard,
        boundary="campaign:partial_attempt", control_receipt=True,
    )
    sealed = FailureCountPartialAttemptV1.model_validate_json(receipt_path.read_bytes())
    if sealed != partial or sha256(receipt_path.read_bytes()).hexdigest() != sha256(payload).hexdigest():
        raise ValueError("partial attempt receipt did not survive atomic publication")
    return sealed, sealed.digest()


def verify_failure_count_partial_attempt(
    *, record: FailureCountPartialAttemptV1 | Mapping[str, Any], plan: CampaignWorkPlan,
    receipt_sha256: str,
) -> FailureCountPartialAttemptV1:
    """Rehash zero-credit evidence before it can influence a resume decision."""
    partial = record if isinstance(record, FailureCountPartialAttemptV1) else FailureCountPartialAttemptV1.model_validate(record)
    if partial.digest() != receipt_sha256:
        raise ValueError("partial attempt receipt bytes differ from its hash")
    if not isinstance(plan.work_spec, FailureCountWorkSpecV1):
        raise ValueError("partial attempt requires a frozen failure-count plan")
    policy = plan.work_spec.policy
    if (partial.campaign_spec_digest != plan.campaign_spec_digest
            or partial.campaign_plan_digest != plan.campaign_plan_digest
            or partial.policy_sha256 != policy.digest()):
        raise ValueError("partial attempt differs from the frozen campaign identity")
    if not 1 <= partial.attempt_ordinal <= len(plan.units):
        raise ValueError("partial attempt ordinal is outside the frozen campaign")
    if plan.units[partial.attempt_ordinal - 1].key != partial.unit_key:
        raise ValueError("partial attempt ordinal and unit key differ")
    declared = policy.executable_limits.model_dump(mode="json", by_alias=True, exclude={"schema_name"})
    profile_digest = sha256(b"bp-registry-canonical-executable-maxima-v1\0" + canonical_json_bytes(declared)).hexdigest()
    authorization_identity = sha256(canonical_json_bytes({
        "campaign_plan_digest": plan.campaign_plan_digest, "ordinal": partial.attempt_ordinal,
        "attempt_number": partial.attempt_sequence, "policy": policy.digest(),
        "derived": profile_digest,
    })).hexdigest()
    expected_attempt_id = sha256(canonical_json_bytes({
        "plan": plan.campaign_plan_digest, "unit": partial.unit_key,
        "authorization": authorization_identity,
    })).hexdigest()
    if partial.profile_sha256 != profile_digest or partial.attempt_id != expected_attempt_id:
        raise ValueError("partial attempt has a stale executable profile or attempt identity")
    if (partial.consumed_control_receipt_bytes != len(partial.primitive_bytes()) + 1
            or partial.consumed_control_receipt_bytes > policy.executable_limits.partial_receipt_reserve_bytes
            or partial.consumed_decoder_work > policy.executable_limits.derived_work_per_unit
            or partial.consumed_events > policy.executable_limits.derived_events_per_unit
            or partial.consumed_evidence_bytes > policy.executable_limits.derived_evidence_bytes_per_unit
            or partial.consumed_storage_bytes > policy.executable_limits.derived_storage_bytes_per_unit):
        raise ValueError("partial attempt resource counters exceed verified executable limits")
    sample_path = Path(partial.materialized_sample_path)
    ledger_path = Path(partial.canonical_ledger_path)
    attempt_dir = ledger_path.parent
    output_root = attempt_dir.parent.parent
    if (attempt_dir.parent.name != "attempts" or attempt_dir.name != f"{partial.attempt_ordinal:08d}-{authorization_identity[:16]}"
            or sample_path != output_root / "samples" / f"{plan.units[partial.attempt_ordinal - 1].physical_sample_identity}.json"):
        raise ValueError("partial attempt artifact paths differ from frozen ordinal identity")
    if partial.materialized_sample_sha256 is None:
        if sample_path.exists():
            raise ValueError("partial attempt unexpectedly names an unhashed materialized sample")
    else:
        if sample_path.is_symlink() or not sample_path.is_file():
            raise ValueError("partial attempt materialized sample is not a regular file")
        sample = MaterializedPhysicalSampleV1.model_validate_json(sample_path.read_bytes())
        if sample.materialized_sample_sha256 != partial.materialized_sample_sha256:
            raise ValueError("partial attempt materialized sample differs from retained bytes")
    if partial.canonical_ledger_sha256 is None:
        if ledger_path.exists():
            raise ValueError("partial attempt unexpectedly names an unhashed ledger")
    elif (ledger_path.is_symlink() or not ledger_path.is_file()
          or sha256(ledger_path.read_bytes()).hexdigest() != partial.canonical_ledger_sha256):
        raise ValueError("partial attempt ledger hash differs from retained bytes")
    ledger_bytes = b"" if partial.canonical_ledger_sha256 is None else ledger_path.read_bytes()
    sample_size = 0 if partial.materialized_sample_sha256 is None else sample_path.stat().st_size
    if (partial.consumed_evidence_bytes != len(ledger_bytes)
            or partial.consumed_events != ledger_bytes.count(b"\n")
            or (ledger_bytes and not ledger_bytes.endswith(b"\n"))
            or partial.consumed_storage_bytes not in (len(ledger_bytes), len(ledger_bytes) + sample_size)):
        raise ValueError("partial attempt counters differ from retained sample and ledger bytes")
    return partial


def _resume_parent_for_ordinal(
    *, destination: Path, plan: CampaignWorkPlan, ordinal: int, parent_partial_receipt_sha256: str | None,
) -> tuple[int, str | None]:
    """Preserve immutable attempts and allow only one digest-linked retry."""
    unit_key = plan.units[ordinal - 1].key
    attempts_root = destination / "attempts"
    if not attempts_root.exists():
        return 1, None
    partials: list[FailureCountPartialAttemptV1] = []
    terminals: set[int] = set()
    for directory in attempts_root.iterdir():
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("bounded attempt directory must be a regular directory")
        terminal = directory / "attempt.json"
        if terminal.exists():
            raw = json.loads(terminal.read_bytes())
            terminal_key = raw.get("unit_key")
            if isinstance(terminal_key, str):
                terminal_ordinal = next((index for index, item in enumerate(plan.units, 1) if item.key == terminal_key), None)
                if terminal_ordinal is None:
                    raise ValueError("terminal attempt names a unit outside the frozen plan")
                terminals.add(terminal_ordinal)
        partial_path = directory / "partial-attempt.json"
        if partial_path.exists():
            partial = FailureCountPartialAttemptV1.model_validate_json(partial_path.read_bytes())
            verify_failure_count_partial_attempt(record=partial, plan=plan, receipt_sha256=partial.digest())
            if partial.unit_key == unit_key:
                partials.append(partial)
    if any(item not in terminals for item in range(1, ordinal)):
        raise ValueError("resume requires a contiguous verified terminal prefix")
    if ordinal in terminals:
        raise ValueError("completed ordinal cannot be dispatched again")
    if not partials:
        if parent_partial_receipt_sha256 is not None:
            raise ValueError("resume parent does not name a pending ordinal")
        return 1, None
    by_digest = {partial.digest(): partial for partial in partials}
    if len(by_digest) != len(partials):
        raise ValueError("pending ordinal has duplicate partial attempts")
    children = {partial.parent_partial_receipt_sha256 for partial in partials if partial.parent_partial_receipt_sha256 is not None}
    if any(parent not in by_digest for parent in children):
        raise ValueError("pending ordinal partial parent is absent")
    roots = [digest for digest, partial in by_digest.items() if partial.parent_partial_receipt_sha256 is None]
    leaves = [digest for digest in by_digest if digest not in children]
    if len(roots) != 1 or len(leaves) != 1:
        raise ValueError("pending ordinal has competing partial attempts")
    digest = leaves[0]
    if parent_partial_receipt_sha256 != digest:
        raise ValueError("resume requires the exact pending partial receipt digest")
    return len(partials) + 1, digest


def _retained_partial_for_ordinal(*, destination: Path, plan: CampaignWorkPlan, ordinal: int) -> tuple[FailureCountPartialAttemptV1, str] | None:
    root = destination / "attempts"
    if not root.exists():
        return None
    matches: list[FailureCountPartialAttemptV1] = []
    for receipt in root.glob("*/partial-attempt.json"):
        if receipt.is_symlink() or not receipt.is_file():
            raise ValueError("partial attempt receipt must be a regular file")
        partial = FailureCountPartialAttemptV1.model_validate_json(receipt.read_bytes())
        if partial.attempt_ordinal == ordinal:
            verify_failure_count_partial_attempt(record=partial, plan=plan, receipt_sha256=partial.digest())
            matches.append(partial)
    if not matches:
        return None
    matches.sort(key=lambda item: item.attempt_sequence)
    if (tuple(item.attempt_sequence for item in matches) != tuple(range(1, len(matches) + 1))
            or len({item.attempt_id for item in matches}) != len(matches)):
        raise ValueError("retained partial attempts have a nonmonotonic identity")
    parent = None
    for item in matches:
        if item.parent_partial_receipt_sha256 != parent:
            raise ValueError("retained partial attempts fork the pending ordinal")
        parent = item.digest()
    return matches[-1], matches[-1].digest()


def _retained_bounded_actuals(
    *, destination: Path, campaign_root: Path, plan: CampaignWorkPlan,
) -> tuple[dict[str, int], tuple[dict[str, Any], ...], tuple[tuple[int, int, int], ...]]:
    """Reconstruct spent resources from sealed attempts before a new admission.

    A receipt path alone is not evidence: terminal facts are rebuilt from the
    retained sample and ledger, and partial bytes are checked before charging.
    """
    totals = {"shots": 0, "work": 0, "events": 0, "evidence_bytes": 0, "storage_bytes": 0}
    attempts_root = destination / "attempts"
    if not attempts_root.exists():
        return totals, (), ()
    if attempts_root.is_symlink() or not attempts_root.is_dir():
        raise ValueError("bounded attempt root must be a regular directory")
    units = {unit.key: (ordinal, unit) for ordinal, unit in enumerate(plan.units, 1)}
    arms = {arm.arm_id: arm for arm in _campaign_work_spec(plan).arms}
    terminal_by_ordinal: dict[int, dict[str, Any]] = {}
    wall_by_ordinal: dict[int, tuple[int, int, int]] = {}
    for directory in sorted(attempts_root.iterdir()):
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("bounded attempt directory must be a regular directory")
        terminal_path = directory / "attempt.json"
        partial_path = directory / "partial-attempt.json"
        if terminal_path.exists() and partial_path.exists():
            raise ValueError("bounded attempt cannot be both terminal and partial")
        if partial_path.exists():
            if partial_path.is_symlink() or not partial_path.is_file():
                raise ValueError("partial attempt receipt must be a regular file")
            raw = partial_path.read_bytes()
            partial = FailureCountPartialAttemptV1.model_validate_json(raw)
            if raw != partial.primitive_bytes() + b"\n":
                raise ValueError("partial attempt receipt has noncanonical bytes")
            verify_failure_count_partial_attempt(record=partial, plan=plan, receipt_sha256=partial.digest())
            for name, amount in (
                ("work", partial.consumed_decoder_work), ("events", partial.consumed_events),
                ("evidence_bytes", partial.consumed_evidence_bytes),
                ("storage_bytes", partial.consumed_storage_bytes + partial.consumed_control_receipt_bytes),
            ):
                totals[name] = _checked_add(totals[name], amount, name=f"retained {name}")
            continue
        if not terminal_path.exists():
            raise ValueError("bounded attempt directory has no sealed receipt")
        if terminal_path.is_symlink() or not terminal_path.is_file():
            raise ValueError("terminal attempt receipt must be a regular file")
        raw = terminal_path.read_bytes()
        saved = json.loads(raw)
        match = units.get(saved.get("unit_key")) if isinstance(saved, dict) else None
        if match is None:
            raise ValueError("terminal attempt names a unit outside the frozen plan")
        ordinal, unit = match
        if ordinal in terminal_by_ordinal:
            raise ValueError("bounded evidence contains competing terminal attempts")
        sample_path = destination / "samples" / f"{unit.physical_sample_identity}.json"
        ledger_path = directory / "events.jsonl"
        if any(path.is_symlink() or not path.is_file() for path in (sample_path, ledger_path)):
            raise ValueError("terminal attempt lacks a regular sample or ledger")
        materialized = MaterializedPhysicalSampleV1.model_validate_json(sample_path.read_bytes())
        arm_path = campaign_root / arms[unit.arm_id].manifest_path
        rebuilt = _campaign_attempt(
            plan=plan, unit=unit, arm_path=arm_path, sample_path=sample_path,
            materialized=materialized, ledger_path=ledger_path,
        )
        observation = saved.get("attempt", {}).get("resource_observation")
        rebuilt["attempt"] = {**rebuilt["attempt"], "resource_observation": observation}
        unsigned = {key: value for key, value in rebuilt.items() if key not in {
            "receipt_sha256", "events", "terminal_bytes_sha256", "persisted_sample_sha256",
            "validation_status", "replay_status",
        }}
        if raw != canonical_json_bytes(unsigned) + b"\n":
            raise ValueError("terminal attempt differs from verified canonical reconstruction")
        rebuilt["receipt_sha256"] = sha256(canonical_json_bytes(unsigned)).hexdigest()
        verified = verify_canonical_attempt(record=rebuilt, plan=plan)
        required_observation = {
            "schema", "campaign_plan_digest", "unit_key", "attempt_sequence",
            "authorization_identity", "profile_sha256", "deadline_ns", "observed_ns",
            "overshoot_ns", "scientific_work", "scientific_events", "scientific_evidence_bytes",
            "scientific_storage_bytes", "canonical_ledger_sha256",
            "materialized_sample_sha256",
        }
        if (not isinstance(observation, dict) or set(observation) != required_observation
                or observation["schema"] != "failure_count_unit_observation_v1"
                or observation["campaign_plan_digest"] != plan.campaign_plan_digest
                or observation["unit_key"] != unit.key
                or type(observation["attempt_sequence"]) is not int or observation["attempt_sequence"] < 1
                or observation["canonical_ledger_sha256"] != verified["canonical_ledger_sha256"]
                or observation["materialized_sample_sha256"] != materialized.materialized_sample_sha256):
            raise ValueError("bounded terminal resource observation differs from sealed evidence")
        derived = derive_canonical_executable_maxima(canonical_public_manifest_context(arm_path))
        expected_identity = sha256(canonical_json_bytes({
            "campaign_plan_digest": plan.campaign_plan_digest, "ordinal": ordinal,
            "attempt_number": observation["attempt_sequence"], "policy": plan.work_spec.policy.digest(),
            "derived": derived.digest,
        })).hexdigest()
        if (observation["authorization_identity"] != expected_identity
                or observation["profile_sha256"] != derived.digest
                or directory.name != f"{ordinal:08d}-{expected_identity[:16]}"):
            raise ValueError("bounded terminal observation has a stale authorization or profile")
        deadline, observed, overshoot = (observation[name] for name in ("deadline_ns", "observed_ns", "overshoot_ns"))
        if (any(type(value) is not int or value < 0 for value in (deadline, observed, overshoot))
                or overshoot != max(0, observed - deadline)):
            raise ValueError("bounded terminal wall observation is invalid")
        wall_by_ordinal[ordinal] = (deadline, observed, overshoot)
        ledger_size = ledger_path.stat().st_size
        sample_size = sample_path.stat().st_size
        scientific_storage = observation["scientific_storage_bytes"]
        if (type(observation["scientific_work"]) is not int
                or not sum(verified["work_vector"].values()) <= observation["scientific_work"] <= derived.derived_work_per_unit
                or observation["scientific_events"] != len(verified["events"])
                or observation["scientific_evidence_bytes"] != ledger_size
                or type(scientific_storage) is not int
                or scientific_storage not in (ledger_size + len(raw), ledger_size + len(raw) + sample_size)):
            raise ValueError("bounded terminal resource counters differ from verified artifacts")
        terminal_by_ordinal[ordinal] = verified
        for name, amount in (
            ("shots", 1), ("work", observation["scientific_work"]),
            ("events", observation["scientific_events"]),
            ("evidence_bytes", observation["scientific_evidence_bytes"]),
            ("storage_bytes", scientific_storage),
        ):
            if type(amount) is not int or amount < 0:
                raise ValueError("bounded terminal resource counter is invalid")
            totals[name] = _checked_add(totals[name], amount, name=f"retained {name}")
    if tuple(sorted(terminal_by_ordinal)) != tuple(range(1, len(terminal_by_ordinal) + 1)):
        raise ValueError("bounded terminal evidence is not a contiguous frozen prefix")
    return (totals, tuple(terminal_by_ordinal[index] for index in sorted(terminal_by_ordinal)),
            tuple(wall_by_ordinal[index] for index in sorted(wall_by_ordinal)))


def _publish_bounded_cap_censor(
    *, destination: Path, plan: CampaignWorkPlan, partial_digest: str | None,
    exhausted_cap: str, actuals: Mapping[str, int], terminals: tuple[dict[str, Any], ...],
    walls: tuple[tuple[int, int, int], ...], pending_ordinal: int,
) -> tuple[FailureCountTerminalReceiptV1, Path, str]:
    """Seal an immutable campaign control receipt from verified retained costs."""
    policy = plan.work_spec.policy
    reserve = policy.executable_limits.partial_receipt_reserve_bytes
    storage = actuals["storage_bytes"]
    for _ in range(6):
        terminal = FailureCountTerminalReceiptV1(
            schema="failure_count_terminal_receipt_v1", policy_sha256=policy.digest(),
            campaign_plan_sha256=policy.campaign_plan_sha256,
            executable_limit_receipt_sha256=policy.executable_limits.digest(),
            batch_authorization_sha256=policy.batch_authorization.digest(),
            terminal_state="cap_censored", terminal_failure_ordinal=None,
            cumulative_failures=sum(bool(item["terminal_fact"]["logical_failure"]) for item in terminals),
            total_completed_shots=actuals["shots"], inferential_prefix_sha256=None,
            authorized_tail_ordinals=(), authorized_tail_sha256=None, first_exhausted_cap=exhausted_cap,
            realized_decoder_work=actuals["work"], realized_events=actuals["events"],
            realized_evidence_bytes=actuals["evidence_bytes"], realized_storage_bytes=storage,
            wall_boundaries=walls,
        ).validate_against(policy)
        envelope = {
            "schema": "failure_count_bounded_cap_censor_v1",
            "campaign_plan_digest": plan.campaign_plan_digest,
            "pending_ordinal": pending_ordinal,
            "retained_partial_attempt_sha256": partial_digest,
            "terminal_receipt": terminal.model_dump(mode="json", by_alias=True),
        }
        payload = canonical_json_bytes(envelope) + b"\n"
        next_storage = _checked_add(actuals["storage_bytes"], len(payload), name="cap censor receipt storage")
        if next_storage == storage:
            break
        storage = next_storage
    else:
        raise ValueError("cap censor receipt byte accounting did not stabilize")
    if len(payload) > reserve or storage > policy.caps.max_storage_bytes:
        raise ValueError("bounded cap censor cannot fit its reserved control receipt")
    path = destination / "failure-count-cap-censor.json"
    destination.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise ValueError("retained bounded cap censor conflicts with verified evidence")
    else:
        descriptor, temporary_name = tempfile.mkstemp(prefix=".failure-count-censor-", dir=destination)
        try:
            with open(descriptor, "wb", closefd=True) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
    if path.read_bytes() != payload:
        raise ValueError("bounded cap censor did not survive atomic publication")
    return terminal, path, sha256(payload).hexdigest()


def run_canonical_bounded_batch(
    plan: CampaignWorkPlan, *, campaign_root: str | Path, output_root: str | Path,
    first_ordinal: int, batch_size: int, parent_partial_receipt_sha256: str | None = None,
    clock_ns: Callable[[], int] = time.monotonic_ns,
) -> dict[str, Any]:
    """Execute exactly one frozen contiguous failure-count ordinal batch.

    This deliberately has no scheduler path and never calls
    :func:`run_canonical_work_plan`; every attempted shot is independently
    verified before the caller may use it for failure-count stopping.
    """
    root = Path(campaign_root).resolve(strict=True)
    destination = Path(output_root)
    if destination.exists() and (destination.is_symlink() or not destination.is_dir()):
        raise ValueError("bounded campaign output root must be a regular directory")
    policy = plan.work_spec.policy  # narrowed by the preflight above
    assert isinstance(policy, object)
    retained_before_projection = _retained_partial_for_ordinal(
        destination=destination, plan=plan, ordinal=first_ordinal,
    )
    accumulated, retained_terminals, retained_walls = _retained_bounded_actuals(
        destination=destination, campaign_root=root, plan=plan,
    )
    retained_censor_path = destination / "failure-count-cap-censor.json"
    if retained_censor_path.exists():
        if retained_censor_path.is_symlink() or not retained_censor_path.is_file():
            raise ValueError("retained bounded cap censor must be a regular file")
        retained_censor = json.loads(retained_censor_path.read_bytes())
        if (not isinstance(retained_censor, dict)
                or retained_censor.get("schema") != "failure_count_bounded_cap_censor_v1"
                or retained_censor.get("campaign_plan_digest") != plan.campaign_plan_digest
                or retained_censor.get("pending_ordinal") != first_ordinal
                or not isinstance(retained_censor.get("terminal_receipt"), dict)):
            raise ValueError("retained bounded cap censor forbids further dispatch")
        claimed_cap = retained_censor["terminal_receipt"].get("first_exhausted_cap")
        claimed_partial = retained_censor.get("retained_partial_attempt_sha256")
        if claimed_partial != parent_partial_receipt_sha256:
            raise ValueError("retained bounded cap censor requires the exact pending parent digest")
        if claimed_partial is not None and (retained_before_projection is None or claimed_partial != retained_before_projection[1]):
            raise ValueError("retained bounded cap censor differs from the pending partial")
        terminal, censor_path, censor_sha256 = _publish_bounded_cap_censor(
            destination=destination, plan=plan, partial_digest=claimed_partial,
            exhausted_cap=claimed_cap, actuals=accumulated, terminals=retained_terminals,
            walls=retained_walls, pending_ordinal=first_ordinal,
        )
        return {"schema": "failure_count_canonical_bounded_batch_v1", "campaign_plan_digest": plan.campaign_plan_digest,
                "terminal_receipt": terminal, "retained_partial_attempt_sha256": claimed_partial,
                "terminal_receipt_path": str(censor_path), "terminal_receipt_sha256": censor_sha256,
                "verified_attempts": (), "materialized_samples": (), "pending_ordinal": first_ordinal,
                "actual_resources": {"completed_shots": accumulated["shots"], "decoder_work": accumulated["work"],
                                     "events": accumulated["events"], "evidence_bytes": accumulated["evidence_bytes"],
                                     "storage_bytes": terminal.realized_storage_bytes}}
    try:
        spec, projection, _context, derived, _manifest_path = _failure_count_executable_projection(
            plan=plan, campaign_root=root, first_ordinal=first_ordinal, batch_size=batch_size,
            accumulated=accumulated,
        )
    except ValueError as error:
        prefix = "bounded canonical batch cannot fit hard resource cap: "
        if not str(error).startswith(prefix):
            raise
        partial_pair = retained_before_projection
        if partial_pair is None:
            raise
        partial, partial_digest = partial_pair
        if parent_partial_receipt_sha256 != partial_digest:
            raise ValueError("cap censor requires the exact pending partial receipt digest")
        cap = str(error)[len(prefix):]
        terminal, censor_path, censor_sha256 = _publish_bounded_cap_censor(
            destination=destination, plan=plan, partial_digest=partial_digest,
            exhausted_cap=cap, actuals=accumulated, terminals=retained_terminals,
            walls=retained_walls, pending_ordinal=first_ordinal,
        )
        return {"schema": "failure_count_canonical_bounded_batch_v1", "campaign_plan_digest": plan.campaign_plan_digest,
                "terminal_receipt": terminal, "retained_partial_attempt_sha256": partial_digest,
                "terminal_receipt_path": str(censor_path), "terminal_receipt_sha256": censor_sha256,
                "verified_attempts": (), "materialized_samples": (),
                "actual_resources": {"completed_shots": accumulated["shots"], "decoder_work": accumulated["work"],
                                     "events": accumulated["events"], "evidence_bytes": accumulated["evidence_bytes"],
                                     "storage_bytes": terminal.realized_storage_bytes}}
    destination.mkdir(parents=True, exist_ok=True)
    arm_contexts = _preflight_work_arms(spec, root)
    verified: list[dict[str, Any]] = []
    materialized_samples: list[MaterializedPhysicalSampleV1] = []
    observations: list[tuple[int, int, int]] = []
    runtime_snapshots: list[Any] = []
    for ordinal in range(first_ordinal, first_ordinal + batch_size):
        unit = plan.units[ordinal - 1]
        attempt_number, linked_parent = _resume_parent_for_ordinal(
            destination=destination, plan=plan, ordinal=ordinal,
            parent_partial_receipt_sha256=parent_partial_receipt_sha256,
        )
        arm_path, context = arm_contexts[unit.arm_id]
        sample_path = destination / "samples" / f"{unit.physical_sample_identity}.json"
        deadline_ns = clock_ns() + policy.batch_authorization.per_unit_timeout_ns
        authorization_identity = sha256(canonical_json_bytes({
            "campaign_plan_digest": plan.campaign_plan_digest, "ordinal": ordinal,
            "attempt_number": attempt_number, "policy": policy.digest(), "derived": derived.digest,
        })).hexdigest()
        authorization_kwargs = {
            "profile_digest": derived.digest, "authorization_identity": authorization_identity,
            "max_events": derived.derived_events_per_unit,
            "max_evidence_bytes": (
                derived.derived_evidence_bytes_per_unit - derived.partial_receipt_reserve_bytes
                if policy.dispatch_mode == "strict_full_batch" else min(
                    policy.interruptible_evidence_bytes,
                    policy.caps.max_evidence_bytes - accumulated["evidence_bytes"] - 2 * derived.partial_receipt_reserve_bytes,
                )
            ),
            "max_storage_bytes": (
                derived.derived_storage_bytes_per_unit - derived.partial_receipt_reserve_bytes
                if policy.dispatch_mode == "strict_full_batch" else min(
                    policy.interruptible_storage_bytes,
                    policy.caps.max_storage_bytes - accumulated["storage_bytes"] - 2 * derived.partial_receipt_reserve_bytes,
                )
            ),
            "control_receipt_reserve_bytes": derived.partial_receipt_reserve_bytes,
            "monotonic_deadline_ns": deadline_ns,
            "max_event_bytes": derived.serializer_bytes_per_event,
            "max_artifact_bytes": CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        }
        authorization = (
            CanonicalRuntimeAuthorizationV1.strict_full_unit(
                **authorization_kwargs, derived_events=derived.derived_events_per_unit,
                derived_evidence_bytes=derived.derived_evidence_bytes_per_unit,
                derived_storage_bytes=derived.derived_storage_bytes_per_unit,
            ) if policy.dispatch_mode == "strict_full_batch"
            else CanonicalRuntimeAuthorizationV1.interruptible_unit(**authorization_kwargs)
        )
        guard = CanonicalRuntimeGuardV1(authorization, clock_ns=clock_ns)
        attempt_dir = destination / "attempts" / f"{ordinal:08d}-{authorization_identity[:16]}"
        ledger_path = attempt_dir / "events.jsonl"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            materialized = materialize_campaign_sample(
                plan=plan, unit=unit, spec=spec, context=context, destination=sample_path,
                resource_guard=guard,
            )
        except CanonicalResourceInterruption as error:
            partial, partial_digest = _seal_failure_count_partial_attempt(
                plan=plan, unit=unit, policy=policy, authorization=authorization,
                materialized=None, sample_path=sample_path, ledger_path=ledger_path,
                snapshot=error.snapshot, receipt_path=attempt_dir / "partial-attempt.json",
                resource_guard=guard, parent_partial_receipt_sha256=linked_parent, attempt_sequence=attempt_number,
            )
            spent, _, _ = _retained_bounded_actuals(destination=destination, campaign_root=root, plan=plan)
            return {
                "schema": "failure_count_canonical_bounded_batch_v1",
                "campaign_plan_digest": plan.campaign_plan_digest, "ordinals": (ordinal,),
                "authorization_projection": {"dispatch_allowed": True, **projection},
                "actual_resources": {"completed_shots": spent["shots"], "decoder_work": spent["work"],
                                     "events": spent["events"], "evidence_bytes": spent["evidence_bytes"],
                                     "storage_bytes": spent["storage_bytes"]},
                "wall_boundaries": tuple(observations), "materialized_samples": tuple(materialized_samples),
                "verified_attempts": tuple(verified), "partial_attempt": partial,
                "partial_attempt_sha256": partial_digest, "interruption": error,
                "runtime_snapshots": (guard.snapshot(),),
            }
        engine_result = run_canonical_materialized_one(
            arm_path, sample=_shot_from_materialized(materialized),
            materialized_sample_sha256=materialized.materialized_sample_sha256,
            ledger_path=ledger_path, manifest_bytes=arm_path.read_bytes(),
            runtime_guard=guard,
        )
        observed = clock_ns()
        observations.append((deadline_ns, observed, max(0, observed - deadline_ns)))
        if engine_result.status == "interrupted":
            assert engine_result.interruption is not None
            partial, partial_digest = _seal_failure_count_partial_attempt(
                plan=plan, unit=unit, policy=policy, authorization=authorization,
                materialized=materialized, sample_path=sample_path, ledger_path=ledger_path,
                snapshot=engine_result.interruption.snapshot, receipt_path=attempt_dir / "partial-attempt.json",
                resource_guard=guard, parent_partial_receipt_sha256=linked_parent, attempt_sequence=attempt_number,
            )
            spent, _, _ = _retained_bounded_actuals(destination=destination, campaign_root=root, plan=plan)
            return {
                "schema": "failure_count_canonical_bounded_batch_v1",
                "campaign_plan_digest": plan.campaign_plan_digest,
                "ordinals": tuple(range(first_ordinal, ordinal + 1)),
                "authorization_projection": {"dispatch_allowed": True, **projection},
                "actual_resources": {"completed_shots": spent["shots"], "decoder_work": spent["work"],
                                     "events": spent["events"], "evidence_bytes": spent["evidence_bytes"],
                                     "storage_bytes": spent["storage_bytes"]},
                "wall_boundaries": tuple(observations),
                "materialized_samples": tuple(materialized_samples), "verified_attempts": tuple(verified),
                "partial_attempt": partial, "partial_attempt_sha256": partial_digest,
                "interruption": engine_result.interruption, "runtime_snapshots": (guard.snapshot(),),
            }
        record = _campaign_attempt(
            plan=plan, unit=unit, arm_path=arm_path, sample_path=sample_path,
            materialized=materialized, ledger_path=ledger_path,
        )
        receipt_path = attempt_dir / "attempt.json"
        before_receipt = guard.snapshot()
        observation = {
            "schema": "failure_count_unit_observation_v1",
            "campaign_plan_digest": plan.campaign_plan_digest, "unit_key": unit.key,
            "attempt_sequence": attempt_number, "authorization_identity": authorization_identity,
            "profile_sha256": derived.digest, "deadline_ns": deadline_ns,
            "observed_ns": observed, "overshoot_ns": max(0, observed - deadline_ns),
            "scientific_work": sum(before_receipt.committed_work.as_evidence(structural_event_version=4).values()),
            "scientific_events": before_receipt.scientific_events,
            "scientific_evidence_bytes": before_receipt.scientific_evidence_bytes,
            "scientific_storage_bytes": before_receipt.scientific_storage_bytes,
            "canonical_ledger_sha256": record["canonical_ledger_sha256"],
            "materialized_sample_sha256": materialized.materialized_sample_sha256,
        }
        for _ in range(4):
            unsigned = {
                key: value for key, value in record.items()
                if key not in {"receipt_sha256", "events", "terminal_bytes_sha256", "persisted_sample_sha256", "validation_status", "replay_status"}
            }
            unsigned["attempt"] = {**unsigned["attempt"], "resource_observation": observation}
            receipt_payload = canonical_json_bytes(unsigned) + b"\n"
            expected_storage = before_receipt.scientific_storage_bytes + len(receipt_payload)
            if observation["scientific_storage_bytes"] == expected_storage:
                break
            observation["scientific_storage_bytes"] = expected_storage
        else:
            raise ValueError("terminal resource observation byte accounting did not stabilize")
        record["attempt"] = unsigned["attempt"]
        record["receipt_sha256"] = sha256(canonical_json_bytes(unsigned)).hexdigest()
        guarded_atomic_write_bytes(
            receipt_path, receipt_payload, resource_guard=guard,
            boundary="campaign:terminal_attempt",
        )
        if guard.snapshot().scientific_storage_bytes != observation["scientific_storage_bytes"]:
            raise ValueError("terminal resource observation differs from guarded storage")
        verified.append(verify_canonical_attempt(record=record, plan=plan))
        materialized_samples.append(materialized)
        runtime_snapshots.append(guard.snapshot())
        if observed >= deadline_ns:
            break
    if len(verified) != batch_size:
        spent, retained, walls = _retained_bounded_actuals(
            destination=destination, campaign_root=root, plan=plan,
        )
        terminal, censor_path, censor_sha256 = _publish_bounded_cap_censor(
            destination=destination, plan=plan, partial_digest=None,
            exhausted_cap="wall", actuals=spent, terminals=retained, walls=walls,
            pending_ordinal=first_ordinal + len(verified),
        )
        return {
            "schema": "failure_count_canonical_bounded_batch_v1",
            "campaign_plan_digest": plan.campaign_plan_digest,
            "ordinals": tuple(range(first_ordinal, first_ordinal + len(verified))),
            "pending_ordinal": first_ordinal + len(verified),
            "authorization_projection": {"dispatch_allowed": True, **projection},
            "terminal_receipt": terminal, "terminal_receipt_path": str(censor_path),
            "terminal_receipt_sha256": censor_sha256,
            "verified_attempts": tuple(verified), "materialized_samples": tuple(materialized_samples),
            "wall_boundaries": walls,
            "actual_resources": {"completed_shots": spent["shots"], "decoder_work": spent["work"],
                                 "events": spent["events"], "evidence_bytes": spent["evidence_bytes"],
                                 "storage_bytes": terminal.realized_storage_bytes},
        }
    actual_evidence = sum(Path(item["canonical_ledger_path"]).stat().st_size for item in verified)
    actual_storage = actual_evidence + sum(Path(item["materialized_sample_path"]).stat().st_size for item in verified)
    actual_storage += sum((Path(item["canonical_ledger_path"]).parent / "attempt.json").stat().st_size for item in verified)
    actual_work = sum(
        value for item in verified for value in item["work_vector"].values()
        if type(value) is int
    )
    if actual_evidence > plan.work_spec.policy.caps.max_evidence_bytes or actual_storage > plan.work_spec.policy.caps.max_storage_bytes:
        raise ValueError("bounded canonical execution exceeded a declared evidence or storage cap")
    return {
        "schema": "failure_count_canonical_bounded_batch_v1",
        "campaign_plan_digest": plan.campaign_plan_digest,
        "ordinals": tuple(range(first_ordinal, first_ordinal + batch_size)),
        "authorization_projection": {"dispatch_allowed": True, **projection},
        "actual_resources": {
            "completed_shots": len(verified), "decoder_work": actual_work,
            "evidence_bytes": actual_evidence,
            "storage_bytes": actual_storage,
        },
        "wall_boundaries": tuple(observations),
        "materialized_samples": tuple(materialized_samples), "verified_attempts": tuple(verified),
        "runtime_snapshots": tuple(runtime_snapshots),
    }
