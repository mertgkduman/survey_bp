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
from ..ledger import read_canonical_events
from ..runner import canonical_public_manifest_context, canonical_public_shot_context, run_canonical_materialized_one, run_canonical_one
from .contracts import CampaignSpecV1, CampaignWorkSpecV1, MaterializedPhysicalSampleV1, build_one_unit_plan, canonical_json_bytes
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
    context: Any, destination: Path,
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
    else:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".materialized-", delete=False) as handle:
            handle.write(payload)
            staging = Path(handle.name)
        try:
            os.replace(staging, destination)
        finally:
            if staging.exists():
                staging.unlink()
    reloaded = MaterializedPhysicalSampleV1.model_validate_json(destination.read_bytes())
    if reloaded.materialized_sample_sha256 != artifact.materialized_sample_sha256 or _shot_from_materialized(reloaded).hidden.x.tobytes() != sample.hidden.x.tobytes():
        raise ValueError("materialized sample reload differs from the sampled physical bytes")
    return reloaded


def _campaign_attempt(
    *, plan: CampaignWorkPlan, unit: Any, arm_path: Path, sample_path: Path,
    materialized: MaterializedPhysicalSampleV1, ledger_path: Path,
) -> dict[str, Any]:
    ledger_bytes = ledger_path.read_bytes()
    events = read_canonical_events(ledger_path)
    terminal_fact = _terminal_fact(events, unit_key=unit.key)
    attempt = {
        "schema": "campaign_attempt_receipt_v1", "attempt_id": _sample_digest("bp-registry-campaign-attempt-v1", {"plan": plan.campaign_plan_digest, "unit": unit.key}),
        "campaign_plan_digest": plan.campaign_plan_digest, "unit_key": unit.key,
        "state": "sealed_terminal", "lifecycle": ["planned", "running", "sealed_terminal"],
        "parent_attempt_receipt": None,
    }
    receipt = {
        "schema": "campaign_canonical_attempt_v1", "attempt": attempt,
        "campaign_spec_digest": plan.campaign_spec_digest, "campaign_plan_digest": plan.campaign_plan_digest,
        "unit_key": unit.key, "arm_manifest_path": str(arm_path),
        "materialized_sample_path": str(sample_path),
        "materialized_sample_sha256": materialized.materialized_sample_sha256,
        "physical_error_sha256": materialized.physical_error_sha256,
        "canonical_ledger_path": str(ledger_path), "canonical_ledger_sha256": sha256(ledger_bytes).hexdigest(),
        "terminal_fact": terminal_fact,
    }
    receipt_bytes = canonical_json_bytes(receipt)
    return {**receipt, "receipt_sha256": sha256(receipt_bytes).hexdigest(), "events": events,
            "terminal_bytes_sha256": sha256(canonical_json_bytes(terminal_fact)).hexdigest(),
            "persisted_sample_sha256": materialized.materialized_sample_sha256,
            "validation_status": "verified", "replay_status": "verified"}


def verify_canonical_attempt(*, record: Mapping[str, Any], plan: CampaignWorkPlan) -> dict[str, Any]:
    """Independently rehash paired evidence before it can enter a campaign merge."""
    if not isinstance(plan.work_spec, CampaignWorkSpecV1) or not isinstance(record, Mapping):
        raise ValueError("canonical attempt verification requires a frozen paired work plan")
    required = {"schema", "attempt", "campaign_spec_digest", "campaign_plan_digest", "unit_key", "arm_manifest_path", "materialized_sample_path", "materialized_sample_sha256", "physical_error_sha256", "canonical_ledger_path", "canonical_ledger_sha256", "terminal_fact", "receipt_sha256", "events", "terminal_bytes_sha256", "persisted_sample_sha256", "validation_status", "replay_status"}
    if set(record) != required or record["schema"] != "campaign_canonical_attempt_v1":
        raise ValueError("canonical attempt receipt has an invalid field set")
    unsigned = {key: value for key, value in record.items() if key not in {"receipt_sha256", "events", "terminal_bytes_sha256", "persisted_sample_sha256", "validation_status", "replay_status"}}
    if sha256(canonical_json_bytes(unsigned)).hexdigest() != record["receipt_sha256"]:
        raise ValueError("canonical attempt receipt bytes differ from its hash")
    materialized = MaterializedPhysicalSampleV1.model_validate_json(Path(record["materialized_sample_path"]).read_bytes())
    ledger = Path(record["canonical_ledger_path"])
    if (materialized.materialized_sample_sha256 != record["materialized_sample_sha256"]
            or materialized.physical_error_sha256 != record["physical_error_sha256"]
            or sha256(ledger.read_bytes()).hexdigest() != record["canonical_ledger_sha256"]):
        raise ValueError("canonical attempt hash binding differs from retained evidence")
    unit = next((item for item in plan.units if item.key == record["unit_key"]), None)
    if unit is None:
        raise ValueError("canonical attempt unit is absent from the frozen plan")
    events = read_canonical_events(ledger)
    if events != record["events"] or _terminal_fact(events, unit_key=unit.key) != record["terminal_fact"]:
        raise ValueError("canonical attempt terminal differs from retained ledger")
    return dict(record)


def run_canonical_work_plan(
    plan: CampaignWorkPlan, *, campaign_root: str | Path, output_root: str | Path,
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
    arms = {arm.arm_id: arm for arm in plan.work_spec.arms}
    samples: dict[str, MaterializedPhysicalSampleV1] = {}
    verified: list[dict[str, Any]] = []
    for unit in plan.units:
        materialized = samples.get(unit.physical_sample_identity)
        sample_path = destination / "samples" / f"{unit.physical_sample_identity}.json"
        arm_path, context = arm_contexts[unit.arm_id]
        if materialized is None:
            materialized = materialize_campaign_sample(plan=plan, unit=unit, spec=plan.work_spec, context=context, destination=sample_path)
            samples[unit.physical_sample_identity] = materialized
        else:
            materialized = MaterializedPhysicalSampleV1.model_validate_json(sample_path.read_bytes())
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
            "materialized_samples": tuple(samples.values()), "verified_attempts": tuple(verified)}
