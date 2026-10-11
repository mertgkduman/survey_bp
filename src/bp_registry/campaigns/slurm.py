"""Bounded, shell-free Slurm transport for immutable campaign work plans.

This module translates an already frozen :class:`CampaignWorkPlan` to a
bounded scheduler request.  It never creates, splits, reorders, or otherwise
changes scientific work.  Scheduler allocation and availability facts are
observations that belong in executor receipts, outside scientific identity.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Mapping

from .planning import CampaignWorkPlan, ShardPlan


_MAX_ARRAY_TASKS: Final = 100_000
_MAX_CONCURRENT_TASKS: Final = 10_000
_MAX_CPUS_PER_TASK: Final = 64
_MAX_MEMORY_MB: Final = 1_048_576
_MAX_WALL_MINUTES: Final = 10_080
_MAX_IDENTIFIER_LENGTH: Final = 64
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")


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
    return {
        "max_array_size": _capability(max_array_size, None if max_array_size is not None else unavailable_scontrol),
        "default_memory_mb": _capability(default_memory, None if default_memory is not None else unavailable_scontrol),
        "accounting_available": _capability(
            True if sacct_text is not None else None,
            None if sacct_text is not None else "sacct output was not supplied",
        ),
    }
