"""Bounded local execution over an already frozen campaign work plan.

This module owns executor observations only. Unit membership, sample identity,
decoder randomness, stopping algebra, and retry planning are supplied by the
frozen plan and other campaign modules.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Callable, Mapping

from ..runner import canonical_public_shot_context, run_canonical_one
from .contracts import CampaignSpecV1, build_one_unit_plan
from .identity import validate_matched_sample_hashes
from .planning import CampaignWorkPlan, ShardPlan
from .shards import _resolve_manifest, _terminal_fact, publish_sealed_shard, seal_receipt


_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
)
_MAX_LOCAL_WORKERS = 64


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
