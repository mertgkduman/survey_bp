"""Bounded, shell-free Slurm transport for immutable campaign work plans.

This module translates an already frozen :class:`CampaignWorkPlan` to a
bounded scheduler request.  It never creates, splits, reorders, or otherwise
changes scientific work.  Scheduler allocation and availability facts are
observations that belong in executor receipts, outside scientific identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Callable, Final, Mapping, Sequence

from .execution import execute_local_work_plan
from .identity import validate_matched_sample_hashes
from .planning import CampaignWorkPlan, ShardPlan


_MAX_ARRAY_TASKS: Final = 100_000
_MAX_CONCURRENT_TASKS: Final = 10_000
_MAX_CPUS_PER_TASK: Final = 64
_MAX_MEMORY_MB: Final = 1_048_576
_MAX_WALL_MINUTES: Final = 10_080
_MAX_IDENTIFIER_LENGTH: Final = 64
_MAX_ELAPSED_SECONDS: Final = 31_622_400
_MAX_ACCOUNTING_RECORDS: Final = 1_024
_MAX_ACCOUNTING_BYTES: Final = 64 * 1024
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_ACCOUNTING_JOB_ID = re.compile(r"\d+(?:_\d+)?(?:\.[A-Za-z0-9_.-]+)?\Z")
_ACCOUNTING_STATE = re.compile(r"[A-Z][A-Z_]*(?:\+[A-Z_]+)?\Z")
_ACCOUNTING_ELAPSED = re.compile(r"(?:\d+-)?\d{1,4}:\d{2}:\d{2}\Z")
_ACCOUNTING_HEADER: Final = ("JobIDRaw", "State", "Elapsed", "AllocCPUS")


def _bounded_integer(value: object, *, name: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [1, {maximum}]")
    return value


def _validated_identifier(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{name} must be a bounded scheduler identifier")
    return value


@dataclass(frozen=True, slots=True)
class SlurmAllocation:
    """A bounded scheduler request that cannot alter a campaign work plan."""

    partition: str | None
    qos: str | None
    account: str | None
    wall_minutes: int
    memory_mb: int
    cpus_per_task: int
    max_concurrent_tasks: int

    def __post_init__(self) -> None:
        for name in ("partition", "qos", "account"):
            value = getattr(self, name)
            if value is not None:
                _validated_identifier(value, name=name)
        _bounded_integer(self.wall_minutes, name="wall_minutes", maximum=_MAX_WALL_MINUTES)
        _bounded_integer(self.memory_mb, name="memory_mb", maximum=_MAX_MEMORY_MB)
        _bounded_integer(self.cpus_per_task, name="cpus_per_task", maximum=_MAX_CPUS_PER_TASK)
        _bounded_integer(
            self.max_concurrent_tasks,
            name="max_concurrent_tasks",
            maximum=_MAX_CONCURRENT_TASKS,
        )

    def payload(self) -> dict[str, object]:
        """Return receipt-only allocation fields in a stable order."""
        return {
            "partition": self.partition,
            "qos": self.qos,
            "account": self.account,
            "wall_minutes": self.wall_minutes,
            "memory_mb": self.memory_mb,
            "cpus_per_task": self.cpus_per_task,
            "max_concurrent_tasks": self.max_concurrent_tasks,
        }


@dataclass(frozen=True, slots=True)
class SchedulerObservation:
    """Allowlisted scheduler facts attached to one array-task receipt.

    The values are deliberately observational.  They are not input to work
    planning, sample derivation, or assessment and have no place in either
    campaign digest.
    """

    job_id: str
    task_id: str
    allocated_cpus: int
    elapsed_seconds: int
    state: str
    exit_code: int
    accounting_available: bool | None
    accounting_unavailable_reason: str | None
    launch_overhead_seconds: int
    shard_fixed_cost_seconds: int

    def __post_init__(self) -> None:
        _validated_identifier(self.job_id, name="job_id")
        if not isinstance(self.task_id, str) or not self.task_id.isdecimal() or str(int(self.task_id)) != self.task_id:
            raise ValueError("task_id must be a canonical decimal Slurm array index")
        _bounded_integer(self.allocated_cpus, name="allocated_cpus", maximum=_MAX_CPUS_PER_TASK)
        if type(self.elapsed_seconds) is not int or not 0 <= self.elapsed_seconds <= _MAX_ELAPSED_SECONDS:
            raise ValueError(f"elapsed_seconds must be an integer in [0, {_MAX_ELAPSED_SECONDS}]")
        for name in ("launch_overhead_seconds", "shard_fixed_cost_seconds"):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value <= _MAX_ELAPSED_SECONDS:
                raise ValueError(f"{name} must be an integer in [0, {_MAX_ELAPSED_SECONDS}]")
        if self.state not in {"COMPLETED", "FAILED", "PREEMPTED", "CANCELLED"}:
            raise ValueError("scheduler state must be a supported terminal Slurm state")
        if type(self.exit_code) is not int or not 0 <= self.exit_code <= 255:
            raise ValueError("exit_code must be an integer in [0, 255]")
        if self.state == "COMPLETED" and self.exit_code != 0:
            raise ValueError("COMPLETED scheduler state requires exit code zero")
        if self.state != "COMPLETED" and self.exit_code == 0:
            raise ValueError("non-completed scheduler state requires a nonzero exit code")
        if self.accounting_available is True:
            if self.accounting_unavailable_reason is not None:
                raise ValueError("available accounting cannot carry an unavailable reason")
        elif self.accounting_available is None:
            if not isinstance(self.accounting_unavailable_reason, str) or not self.accounting_unavailable_reason:
                raise ValueError("unavailable accounting requires an explicit reason")
        else:
            raise ValueError("accounting_available must be true or unavailable")

    def payload(self) -> dict[str, int | str | bool | None]:
        return {
            "job_id": self.job_id,
            "task_id": self.task_id,
            "allocated_cpus": self.allocated_cpus,
            "elapsed_seconds": self.elapsed_seconds,
            "state": self.state,
            "exit_code": self.exit_code,
            "accounting_available": self.accounting_available,
            "accounting_unavailable_reason": self.accounting_unavailable_reason,
            "launch_overhead_seconds": self.launch_overhead_seconds,
            "shard_fixed_cost_seconds": self.shard_fixed_cost_seconds,
        }


def _validated_allowlists(allowed_values: Mapping[str, object]) -> dict[str, frozenset[str]]:
    if not isinstance(allowed_values, Mapping):
        raise ValueError("scheduler allowlists must be a mapping")
    result: dict[str, frozenset[str]] = {}
    for field in ("partition", "qos", "account"):
        raw_values = allowed_values.get(field, ())
        if not isinstance(raw_values, (set, frozenset, tuple, list)):
            raise ValueError(f"{field} allowlist must be a finite collection")
        values = frozenset(_validated_identifier(value, name=field) for value in raw_values)
        result[field] = values
    if set(allowed_values) - set(result):
        raise ValueError("scheduler allowlists contain unsupported fields")
    return result


def _validated_entrypoint(entrypoint: object) -> tuple[str, ...]:
    if not isinstance(entrypoint, tuple) or not 1 <= len(entrypoint) <= 16:
        raise ValueError("Slurm entrypoint must be a bounded argv tuple")
    if any(
        not isinstance(argument, str)
        or not argument
        or len(argument) > 1_024
        or "\x00" in argument
        or "\n" in argument
        or "\r" in argument
        for argument in entrypoint
    ):
        raise ValueError("Slurm entrypoint arguments must be bounded text")
    return entrypoint


def build_sbatch_argv(
    plan: CampaignWorkPlan,
    *,
    allocation: SlurmAllocation,
    allowed_values: Mapping[str, object],
    entrypoint: tuple[str, ...],
) -> tuple[str, ...]:
    """Build a literal ``sbatch`` argv for every precomputed shard in ``plan``.

    ``subprocess.run(argv, shell=False)`` can consume the result directly.  The
    resulting array indexes only select from ``plan.shards``; allocation stays
    outside both campaign digests and therefore cannot change the science.
    """
    if not isinstance(plan, CampaignWorkPlan):
        raise ValueError("Slurm transport requires a frozen CampaignWorkPlan")
    if not isinstance(allocation, SlurmAllocation):
        raise ValueError("Slurm transport requires a validated allocation")
    if not plan.shards or len(plan.shards) > _MAX_ARRAY_TASKS:
        raise ValueError("frozen campaign shard count exceeds bounded Slurm array width")
    if allocation.max_concurrent_tasks > len(plan.shards):
        raise ValueError("max_concurrent_tasks cannot exceed frozen array width")
    allowlists = _validated_allowlists(allowed_values)
    for field in ("partition", "qos", "account"):
        value = getattr(allocation, field)
        if value is not None and value not in allowlists[field]:
            raise ValueError(f"{field} must appear in the site allowlist when supplied")
    executable = _validated_entrypoint(entrypoint)
    argv = [
        "sbatch",
        f"--array=0-{len(plan.shards) - 1}%{allocation.max_concurrent_tasks}",
        f"--cpus-per-task={allocation.cpus_per_task}",
        f"--mem={allocation.memory_mb}M",
        f"--time={allocation.wall_minutes}",
    ]
    for field in ("partition", "qos", "account"):
        value = getattr(allocation, field)
        if value is not None:
            argv.append(f"--{field}={value}")
    return tuple(argv + ["--", *executable])


def select_array_shard(plan: CampaignWorkPlan, array_task_id: object) -> ShardPlan:
    """Resolve exactly one zero-based Slurm array task to one frozen shard."""
    if not isinstance(plan, CampaignWorkPlan):
        raise ValueError("Slurm array selection requires a frozen CampaignWorkPlan")
    if not isinstance(array_task_id, str) or not array_task_id.isdecimal():
        raise ValueError("SLURM_ARRAY_TASK_ID must be a decimal array index")
    index = int(array_task_id)
    if str(index) != array_task_id or not 0 <= index < len(plan.shards):
        raise ValueError("SLURM_ARRAY_TASK_ID does not select a frozen shard")
    return plan.shards[index]


def _capability(value: int | bool | None, unavailable_reason: str | None) -> dict[str, int | bool | str | None]:
    return {"value": value, "unavailable_reason": unavailable_reason}


def _reported_integer(text: str | None, field: str) -> int | None:
    if text is None:
        return None
    match = re.search(rf"(?:^|\s){re.escape(field)}=(\d+)(?:\s|$)", text)
    if match is None:
        return None
    value = int(match.group(1))
    return value if value <= _MAX_MEMORY_MB else None


def _accounting_unavailable_reason(sacct_text: str | None) -> str | None:
    """Validate a bounded `sacct --parsable2` record before trusting it exists."""
    if sacct_text is None:
        return "sacct output was not supplied"
    if not sacct_text.strip():
        return "sacct output was empty"
    if len(sacct_text.encode("utf-8")) > _MAX_ACCOUNTING_BYTES:
        return "sacct output exceeds the bounded accounting record size"
    lines = [line for line in sacct_text.splitlines() if line.strip()]
    if len(lines) < 2 or len(lines) - 1 > _MAX_ACCOUNTING_RECORDS:
        return "sacct output did not contain a bounded accounting record"
    if tuple(lines[0].rstrip("|").split("|")) != _ACCOUNTING_HEADER:
        return "sacct output did not use the documented accounting header"
    for line in lines[1:]:
        fields = line.rstrip("|").split("|")
        if len(fields) != len(_ACCOUNTING_HEADER):
            return "sacct output contained a malformed accounting record"
        job_id, state, elapsed, allocated_cpus = fields
        if (
            _ACCOUNTING_JOB_ID.fullmatch(job_id) is None
            or _ACCOUNTING_STATE.fullmatch(state) is None
            or _ACCOUNTING_ELAPSED.fullmatch(elapsed) is None
            or not allocated_cpus.isdecimal()
            or not 1 <= int(allocated_cpus) <= _MAX_ARRAY_TASKS * _MAX_CPUS_PER_TASK
        ):
            return "sacct output contained a malformed accounting record"
    return None


def parse_site_capabilities(
    *, scontrol_text: str | None, sacct_text: str | None,
) -> dict[str, dict[str, int | bool | str | None]]:
    """Parse supplied, read-only scheduler observations without inventing policy.

    Callers may obtain the text through their site's approved observation path.
    This parser deliberately performs no subprocess invocation and reports
    unavailable accounting distinctly from a zero-valued scheduler fact.
    """
    if scontrol_text is not None and not isinstance(scontrol_text, str):
        raise ValueError("scontrol capability text must be text or unavailable")
    if sacct_text is not None and not isinstance(sacct_text, str):
        raise ValueError("sacct capability text must be text or unavailable")
    max_array_size = _reported_integer(scontrol_text, "MaxArraySize")
    default_memory = _reported_integer(scontrol_text, "DefMemPerCPU")
    unavailable_scontrol = "scontrol output was not supplied" if scontrol_text is None else "field not reported by site"
    accounting_reason = _accounting_unavailable_reason(sacct_text)
    return {
        "max_array_size": _capability(max_array_size, None if max_array_size is not None else unavailable_scontrol),
        "default_memory_mb": _capability(default_memory, None if default_memory is not None else unavailable_scontrol),
        "accounting_available": _capability(
            True if accounting_reason is None else None,
            accounting_reason,
        ),
    }


def scientific_records_digest(records: Sequence[Mapping[str, Any]]) -> str:
    """Hash only already-reconstructed scientific facts in frozen record order."""
    if not isinstance(records, (tuple, list)) or any(not isinstance(record, Mapping) for record in records):
        raise ValueError("scientific records must be an ordered mapping sequence")
    payload = json.dumps(list(records), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return sha256(payload).hexdigest()


def _scheduler_receipt(
    *, plan: CampaignWorkPlan, shard: ShardPlan, allocation: SlurmAllocation,
    observation: SchedulerObservation, execution: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if execution is None:
        terminal: tuple[str, ...] = ()
        incomplete = shard.unit_keys
        scientific: tuple[Mapping[str, Any], ...] = ()
        records: tuple[Mapping[str, Any], ...] = ()
    else:
        terminal = tuple(execution["terminal_unit_keys"])
        incomplete = tuple(execution["incomplete_unit_keys"])
        scientific = tuple(execution["scientific_records"])
        records = tuple(execution["records"])
    return {
        "schema": "campaign_slurm_task_receipt_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "shard_id": shard.shard_id,
        "terminal_unit_keys": terminal,
        "incomplete_unit_keys": incomplete,
        "resume_unit_keys": incomplete,
        "scientific_records": scientific,
        "records": records,
        "executor_receipt": {
            "requested_allocation": allocation.payload(),
            "scheduler": observation.payload(),
        },
    }


def execute_slurm_array_task(
    plan: CampaignWorkPlan,
    *,
    array_task_id: str,
    output_root: str | Path,
    unit_runner: Callable[[dict[str, Any], str], Mapping[str, Any]],
    allocation: SlurmAllocation,
    observation: SchedulerObservation,
) -> dict[str, Any]:
    """Execute one selected frozen shard, or retain its scheduler interruption.

    A non-completed scheduler task never invokes the decoder.  Its exact
    selected shard remains visibly incomplete for the established resume
    reducer, rather than becoming a fabricated scientific terminal.
    """
    shard = select_array_shard(plan, array_task_id)
    if not isinstance(allocation, SlurmAllocation) or not isinstance(observation, SchedulerObservation):
        raise ValueError("Slurm task execution requires validated receipt observations")
    if observation.task_id != array_task_id:
        raise ValueError("scheduler task receipt differs from selected array task")
    execution: Mapping[str, Any] | None = None
    if observation.state == "COMPLETED":
        execution = execute_local_work_plan(
            plan,
            output_root=output_root,
            workers=1,
            unit_runner=unit_runner,
            shards=(shard,),
        )
    return _scheduler_receipt(
        plan=plan, shard=shard, allocation=allocation,
        observation=observation, execution=execution,
    )


def execute_synthetic_slurm_array(
    plan: CampaignWorkPlan,
    *,
    output_root: str | Path,
    unit_runner: Callable[[dict[str, Any], str], Mapping[str, Any]],
    allocation: SlurmAllocation,
    observations: Sequence[SchedulerObservation],
) -> dict[str, Any]:
    """Run a bounded, deterministic array harness for transport equivalence tests.

    This is deliberately not a scheduler client.  It supplies documented task
    observations to the same single-shard entry point so tests can distinguish
    scheduling receipts from replayable scientific evidence without submitting
    any work to a site scheduler.
    """
    if not isinstance(plan, CampaignWorkPlan) or not isinstance(allocation, SlurmAllocation):
        raise ValueError("synthetic Slurm execution requires frozen plan and allocation")
    typed_observations = tuple(observations)
    if len(typed_observations) != len(plan.shards) or any(
        not isinstance(item, SchedulerObservation) for item in typed_observations
    ):
        raise ValueError("synthetic Slurm execution requires one observation per frozen shard")
    task_ids = tuple(item.task_id for item in typed_observations)
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("synthetic Slurm execution rejects duplicate array delivery")
    expected_ids = tuple(str(index) for index in range(len(plan.shards)))
    if set(task_ids) != set(expected_ids):
        raise ValueError("synthetic Slurm execution requires exact frozen array coverage")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    task_receipts = tuple(
        execute_slurm_array_task(
            plan,
            array_task_id=task_id,
            output_root=root / f"array-{task_id}",
            unit_runner=unit_runner,
            allocation=allocation,
            observation=next(item for item in typed_observations if item.task_id == task_id),
        )
        for task_id in expected_ids
    )
    records_by_key = {
        str(record["unit_key"]): record
        for receipt in task_receipts
        for record in receipt["scientific_records"]
    }
    scientific = tuple(records_by_key[key] for key in plan.unit_keys if key in records_by_key)
    validate_matched_sample_hashes(scientific)
    terminal = tuple(record["unit_key"] for record in scientific)
    incomplete = tuple(
        key for receipt in task_receipts for key in receipt["incomplete_unit_keys"]
    )
    return {
        "schema": "campaign_synthetic_slurm_execution_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "terminal_unit_keys": terminal,
        "incomplete_unit_keys": incomplete,
        "scientific_records": scientific,
        "merge_receipt_sha256": scientific_records_digest(scientific),
        "task_receipts": task_receipts,
    }
