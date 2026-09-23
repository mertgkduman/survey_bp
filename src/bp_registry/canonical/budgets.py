"""Hard scoped budgets and leaf-only scientific work accounting."""

from __future__ import annotations

from dataclasses import dataclass, fields
import math
import numbers
from threading import RLock
from typing import Callable, Iterable, Mapping


_MAX_COUNT = (1 << 63) - 1
_WALL_BOUNDARIES = frozenset({
    "attempt_start", "iteration_boundary", "candidate_selection_boundary", "attempt_end",
})


@dataclass(frozen=True, slots=True)
class WorkVector:
    """Exact, nonnegative atomic work categories; no universal-cost bucket exists."""

    check_to_variable_updates: int = 0
    variable_to_check_updates: int = 0
    belief_assemblies: int = 0
    residual_priority_evaluations: int = 0
    bp_calls: int = 0
    candidate_checks: int = 0
    intervention_actions: int = 0
    branch_expansions: int = 0
    branch_prunes: int = 0
    relay_transfers: int = 0
    fallback_calls: int = 0

    def __post_init__(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, bool) or not isinstance(value, numbers.Integral) or not 0 <= value <= _MAX_COUNT:
                raise ValueError(f"{item.name} must be a bounded nonnegative integer")
            object.__setattr__(self, item.name, int(value))

    @classmethod
    def zero(cls) -> "WorkVector":
        return cls()

    @classmethod
    def from_flooding_counts(cls, *, edge_count: int, variable_count: int) -> "WorkVector":
        return cls(
            check_to_variable_updates=edge_count,
            variable_to_check_updates=edge_count,
            belief_assemblies=variable_count,
            candidate_checks=variable_count,
        )

    @classmethod
    def sum(cls, vectors: Iterable["WorkVector"]) -> "WorkVector":
        result = cls.zero()
        for vector in vectors:
            result = result + vector
        return result

    def __add__(self, other: "WorkVector") -> "WorkVector":
        if not isinstance(other, WorkVector):
            return NotImplemented
        return WorkVector(**{item.name: getattr(self, item.name) + getattr(other, item.name) for item in fields(self)})

    def as_evidence(self) -> dict[str, int]:
        return {item.name: getattr(self, item.name) for item in fields(self)}


@dataclass(frozen=True, slots=True)
class QualifiedIteration:
    """A conventional count that never hides which schedule operation it means."""

    count: int
    schedule: str
    atomic_unit: str

    def __post_init__(self) -> None:
        if isinstance(self.count, bool) or not isinstance(self.count, numbers.Integral) or not 0 <= self.count <= _MAX_COUNT:
            raise ValueError("iteration count must be a bounded nonnegative integer")
        if not isinstance(self.schedule, str) or not self.schedule or not isinstance(self.atomic_unit, str) or not self.atomic_unit:
            raise ValueError("iteration schedule and atomic unit must be nonempty strings")
        object.__setattr__(self, "count", int(self.count))

    def as_evidence(self) -> dict[str, int | str]:
        return {"count": self.count, "schedule": self.schedule, "atomic_unit": self.atomic_unit}


@dataclass(frozen=True, slots=True)
class Measurement:
    """A scoped observed value or explicit unavailable fact, never an implied zero."""

    value: int | float | str | None
    method: str
    scope: str
    unit: str
    precision: str
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        for name in ("method", "scope", "unit", "precision"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError("measurement method, scope, unit, and precision must be nonempty strings")
        if self.value is None:
            if not isinstance(self.unavailable_reason, str) or not self.unavailable_reason:
                raise ValueError("unavailable measurements require a reason")
        else:
            if isinstance(self.value, bool) or not isinstance(self.value, (numbers.Real, str)):
                raise ValueError("measurement values must be finite numbers or strings")
            if isinstance(self.value, numbers.Real) and not math.isfinite(float(self.value)):
                raise ValueError("measurement numeric values must be finite")
            if self.unavailable_reason is not None:
                raise ValueError("observed measurements cannot carry an unavailable reason")

    @classmethod
    def observed(cls, value: int | float | str, *, method: str, scope: str, unit: str, precision: str) -> "Measurement":
        return cls(value, method=method, scope=scope, unit=unit, precision=precision)

    @classmethod
    def unavailable(cls, *, method: str, scope: str, unit: str, precision: str, reason: str) -> "Measurement":
        return cls(None, method=method, scope=scope, unit=unit, precision=precision, unavailable_reason=reason)

    def as_evidence(self) -> dict[str, int | float | str | None]:
        return {
            "value": self.value,
            "method": self.method,
            "scope": self.scope,
            "unit": self.unit,
            "precision": self.precision,
            "unavailable_reason": self.unavailable_reason,
        }


@dataclass(frozen=True, slots=True)
class RuntimeResourceFacts:
    """Same-machine runtime/resource context retained beside algorithmic work."""

    wall_time: Measurement
    process_cpu_time: Measurement
    peak_host_memory: Measurement
    concurrency: Measurement
    machine_environment: Measurement
    backend_device_time: Measurement
    backend_device_memory: Measurement

    def __post_init__(self) -> None:
        if any(not isinstance(getattr(self, item.name), Measurement) for item in fields(self)):
            raise ValueError("runtime resource facts must contain Measurement values")

    def as_evidence(self) -> dict[str, dict[str, int | float | str | None]]:
        return {item.name: getattr(self, item.name).as_evidence() for item in fields(self)}


@dataclass(frozen=True, slots=True)
class BudgetLimit:
    """One hard count limit at one named lifecycle scope."""

    scope: str
    resource: str
    limit: int

    def __post_init__(self) -> None:
        if not isinstance(self.scope, str) or not self.scope:
            raise ValueError("budget scope must be a nonempty string")
        if self.resource not in WorkVector.zero().as_evidence():
            raise ValueError("budget resource must name a WorkVector field")
        if isinstance(self.limit, bool) or not isinstance(self.limit, numbers.Integral) or not 0 <= self.limit <= _MAX_COUNT:
            raise ValueError("budget limit must be a bounded nonnegative integer")
        object.__setattr__(self, "limit", int(self.limit))


@dataclass(frozen=True, slots=True)
class BudgetTermination:
    """Queryable reason that an operational or count boundary stopped execution."""

    binding_scope: str
    resource: str
    configured_limit: int
    consumed_amount: int
    reason: str
    boundary_kind: str | None = None
    observed_elapsed_ns: int | None = None
    overshoot_ns: int | None = None


@dataclass(frozen=True, slots=True)
class _LeafEvent:
    leaf_id: str
    scope: str
    delta: WorkVector


class Reservation:
    """One-shot token which either commits a complete leaf vector or rolls back."""

    def __init__(self, tree: "BudgetTree", *, scope: str, delta: WorkVector, leaf_id: str) -> None:
        self._tree = tree
        self.scope = scope
        self.delta = delta
        self.leaf_id = leaf_id
        self._state = "active"

    @property
    def active(self) -> bool:
        return self._state == "active"

    def commit_once(self) -> None:
        self._tree._finalize(self, commit=True)

    def rollback(self) -> None:
        self._tree._finalize(self, commit=False)

    def __enter__(self) -> "Reservation":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        if self.active:
            self.rollback()
        return False


class BudgetTree:
    """Thread-safe hard limits with leaf-only committed accounting.

    Reservations temporarily occupy every ancestor allowance.  Committed work is
    stored only once, at its leaf; all scope summaries reduce those unique leaves.
    """

    def __init__(self, *, limits: Iterable[BudgetLimit], parents: Mapping[str, str] | None = None) -> None:
        self._parents = dict(parents or {})
        self._limits: dict[tuple[str, str], BudgetLimit] = {}
        for limit in limits:
            if not isinstance(limit, BudgetLimit):
                raise ValueError("limits must contain BudgetLimit values")
            key = (limit.scope, limit.resource)
            if key in self._limits:
                raise ValueError("each scope/resource budget limit must be unique")
            self._limits[key] = limit
        for scope, parent in self._parents.items():
            if not isinstance(scope, str) or not scope or not isinstance(parent, str) or not parent:
                raise ValueError("budget parents must use nonempty scope names")
            self._ancestors(scope)
        self._leaves: dict[str, _LeafEvent] = {}
        self._pending: dict[str, list[Reservation]] = {}
        self._last_termination: BudgetTermination | None = None
        self._lock = RLock()

    @property
    def last_termination(self) -> BudgetTermination | None:
        with self._lock:
            return self._last_termination

    def reserve(self, scope: str, delta: WorkVector, *, leaf_id: str) -> Reservation | None:
        if not isinstance(scope, str) or not scope:
            raise ValueError("reservation scope must be a nonempty string")
        if not isinstance(delta, WorkVector):
            raise ValueError("reservation delta must be a WorkVector")
        if not isinstance(leaf_id, str) or not leaf_id:
            raise ValueError("leaf work ID must be a nonempty string")
        with self._lock:
            lineage = self._ancestors(scope)
            if leaf_id in self._leaves or leaf_id in self._pending:
                raise ValueError("leaf work IDs must be unique")
            for ancestor in lineage:
                used = self.summary(ancestor)
                pending = WorkVector.sum(item.delta for item in self._pending.values() for item in item if ancestor in self._ancestors(item.scope))
                for resource, amount in delta.as_evidence().items():
                    limit = self._limits.get((ancestor, resource))
                    if limit is not None and getattr(used, resource) + getattr(pending, resource) + amount > limit.limit:
                        self._last_termination = BudgetTermination(
                            binding_scope=ancestor,
                            resource=resource,
                            configured_limit=limit.limit,
                            consumed_amount=getattr(used, resource) + getattr(pending, resource),
                            reason="count_budget_exhausted",
                        )
                        return None
            reservation = Reservation(self, scope=scope, delta=delta, leaf_id=leaf_id)
            self._pending[leaf_id] = [reservation]
            return reservation

    def summary(self, scope: str) -> WorkVector:
        with self._lock:
            return WorkVector.sum(event.delta for event in self._leaves.values() if scope in self._ancestors(event.scope))

    def leaf_events(self) -> tuple[tuple[str, str, WorkVector], ...]:
        with self._lock:
            return tuple((event.leaf_id, event.scope, event.delta) for event in self._leaves.values())

    def _ancestors(self, scope: str) -> tuple[str, ...]:
        result: list[str] = []
        current = scope
        while True:
            if current in result:
                raise ValueError("budget parent graph must be acyclic")
            result.append(current)
            parent = self._parents.get(current)
            if parent is None:
                return tuple(result)
            current = parent

    def _finalize(self, reservation: Reservation, *, commit: bool) -> None:
        with self._lock:
            if reservation._tree is not self or reservation._state != "active":
                raise RuntimeError("reservation is already finalized")
            self._pending.pop(reservation.leaf_id, None)
            if commit:
                self._leaves[reservation.leaf_id] = _LeafEvent(reservation.leaf_id, reservation.scope, reservation.delta)
                reservation._state = "committed"
            else:
                reservation._state = "rolled_back"


class WallClockLimit:
    """Monotonic operational deadline, intentionally separate from count budgets."""

    def __init__(self, duration_ns: int, *, clock: Callable[[], int]) -> None:
        if isinstance(duration_ns, bool) or not isinstance(duration_ns, numbers.Integral) or duration_ns < 0:
            raise ValueError("wall-clock duration must be a nonnegative integer nanosecond count")
        self.duration_ns = int(duration_ns)
        self._clock = clock
        self._started_ns: int | None = None

    def check(self, boundary_kind: str, *, scope: str) -> BudgetTermination | None:
        if boundary_kind not in _WALL_BOUNDARIES:
            raise ValueError("wall-clock checks require a declared synchronization boundary")
        observed = self._clock()
        if isinstance(observed, bool) or not isinstance(observed, numbers.Integral):
            raise ValueError("monotonic clock must return integer nanoseconds")
        if self._started_ns is None:
            self._started_ns = int(observed)
            return None
        elapsed = max(0, int(observed) - self._started_ns)
        if elapsed < self.duration_ns:
            return None
        return BudgetTermination(
            binding_scope=scope,
            resource="wall_clock_ns",
            configured_limit=self.duration_ns,
            consumed_amount=elapsed,
            reason="wall_clock_deadline",
            boundary_kind=boundary_kind,
            observed_elapsed_ns=elapsed,
            overshoot_ns=max(0, elapsed - self.duration_ns),
        )
