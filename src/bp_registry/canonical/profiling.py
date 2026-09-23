"""Typed, local-only profiling facts for scientifically comparable CSS runs.

This module measures process-local runtime resources.  It deliberately does
not infer unavailable counters, inspect arbitrary environment variables, or
present instrumented duration as a clean-run estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import os
import platform
try:  # ``resource`` is intentionally optional on non-POSIX hosts.
    import resource as _resource
except ImportError:  # pragma: no cover - exercised through injected adapter
    _resource = None
import threading
import time
import tracemalloc as _tracemalloc
from types import MappingProxyType
from typing import Callable, Literal, Mapping, TypeVar

from .budgets import Measurement, RuntimeResourceFacts


_T = TypeVar("_T")
_ALLOWLISTED_ENVIRONMENT = frozenset({
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
})
_REQUIRED_FACTS = frozenset({
    "wall_time", "process_cpu_time", "peak_host_memory", "python_allocation_peak",
})


class ProfilingRequirementError(RuntimeError):
    """A strict plan requested a counter the local adapter cannot observe."""


@dataclass(frozen=True, slots=True)
class ProfilingPlan:
    """An explicit local profiling level, not a publication campaign default."""

    enabled: bool = True
    required: frozenset[str] = frozenset()
    track_python_allocations: bool = False
    level: Literal["low_overhead", "representative"] = "low_overhead"

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool or type(self.track_python_allocations) is not bool:
            raise ValueError("profiling switches must be booleans")
        if self.level not in {"low_overhead", "representative"}:
            raise ValueError("profiling level must be low_overhead or representative")
        required = frozenset(self.required)
        if required - _REQUIRED_FACTS:
            raise ValueError("strict profiling requirements name unknown facts")
        object.__setattr__(self, "required", required)


@dataclass(frozen=True, slots=True)
class ProfileMeasurement:
    """Observed local facts, with adapter overhead isolated from run duration."""

    runtime: RuntimeResourceFacts
    adapter_overhead: Measurement
    python_allocation_peak: Measurement
    environment: Mapping[str, str | int]
    raw_context: Mapping[str, str | int]
    enabled: bool
    level: str

    def __post_init__(self) -> None:
        if not isinstance(self.runtime, RuntimeResourceFacts) or not isinstance(self.adapter_overhead, Measurement):
            raise ValueError("profile measurement requires typed runtime and overhead facts")
        if not isinstance(self.python_allocation_peak, Measurement):
            raise ValueError("profile measurement requires typed allocation facts")
        if not isinstance(self.enabled, bool) or not isinstance(self.level, str) or not self.level:
            raise ValueError("profile enabled state and level must be explicit")
        environment = dict(self.environment)
        if set(environment) - _ALLOWLISTED_ENVIRONMENT:
            raise ValueError("profile environment contains a non-allowlisted field")
        if any(not isinstance(value, (str, int)) or "/" in str(value) for value in environment.values()):
            raise ValueError("profile environment values must be scalar and path-free")
        raw_context = dict(self.raw_context)
        if any(not isinstance(key, str) or not isinstance(value, (str, int)) for key, value in raw_context.items()):
            raise ValueError("profile raw context must use scalar non-secret facts")
        object.__setattr__(self, "environment", MappingProxyType(environment))
        object.__setattr__(self, "raw_context", MappingProxyType(raw_context))

    def as_evidence(self) -> dict[str, object]:
        return {
            "runtime": self.runtime.as_evidence(),
            "adapter_overhead": self.adapter_overhead.as_evidence(),
            "python_allocation_peak": self.python_allocation_peak.as_evidence(),
            "environment": dict(self.environment),
            "raw_context": dict(self.raw_context),
            "enabled": self.enabled,
            "level": self.level,
        }


def _unavailable(*, method: str, scope: str, unit: str, reason: str) -> Measurement:
    return Measurement.unavailable(method=method, scope=scope, unit=unit, precision="unknown", reason=reason)


class LocalProfiler:
    """Small standard-library adapter with explicit process-local scope."""

    def __init__(
        self,
        plan: ProfilingPlan,
        *,
        environment: Mapping[str, str] | None = None,
        clock: Callable[[], int] = time.perf_counter_ns,
        cpu_clock: Callable[[], int] = time.process_time_ns,
        resource_module: object | None = _resource,
        tracemalloc_module: object | None = _tracemalloc,
        platform_system: Callable[[], str] = platform.system,
    ) -> None:
        if not isinstance(plan, ProfilingPlan):
            raise ValueError("local profiler requires a ProfilingPlan")
        self.plan = plan
        self._environment = dict(os.environ if environment is None else environment)
        self._clock = clock
        self._cpu_clock = cpu_clock
        self._resource = resource_module
        self._tracemalloc = tracemalloc_module
        self._platform_system = platform_system

    def _environment_context(self) -> dict[str, str | int]:
        return {
            key: value for key in sorted(_ALLOWLISTED_ENVIRONMENT)
            if (value := self._environment.get(key)) is not None and "/" not in value
        }

    def _concurrency(self) -> Measurement:
        return Measurement.observed(
            threading.active_count(), method="threading.active_count:v1", scope="process", unit="threads", precision="instantaneous"
        )

    def _machine(self) -> Measurement:
        # A fixed label identifies this local standard-library adapter without
        # serializing hostnames, working directories, or arbitrary environment.
        return Measurement.observed("local-stdlib-cpu", method="profile_adapter:v1", scope="host", unit="identity", precision="declared")

    def _peak_rss(self) -> tuple[Measurement, dict[str, str | int]]:
        if self._resource is None:
            return _unavailable(method="resource.getrusage:RUSAGE_SELF:v1", scope="process", unit="bytes", reason="resource adapter unavailable"), {}
        try:
            usage = self._resource.getrusage(self._resource.RUSAGE_SELF)  # type: ignore[attr-defined]
            raw = int(usage.ru_maxrss)
            system = self._platform_system()
        except (AttributeError, OSError, ValueError, TypeError) as error:
            return _unavailable(method="resource.getrusage:RUSAGE_SELF:v1", scope="process", unit="bytes", reason=f"resource adapter unavailable: {type(error).__name__}"), {}
        if raw < 0:
            return _unavailable(method="resource.getrusage:RUSAGE_SELF:ru_maxrss:v1", scope="process", unit="bytes", reason="negative RSS observation"), {}
        if system == "Linux":
            normalized, raw_unit = raw * 1024, "kilobytes"
        elif system == "Darwin":
            normalized, raw_unit = raw, "bytes"
        else:
            return _unavailable(method="resource.getrusage:RUSAGE_SELF:ru_maxrss:v1", scope="process", unit="bytes", reason="RSS normalization semantics unavailable"), {
                "rss_platform": system,
                "rss_raw_value": raw,
                "rss_raw_unit": "unknown",
            }
        return Measurement.observed(
            normalized,
            method="resource.getrusage:RUSAGE_SELF:ru_maxrss:v1",
            scope="process",
            unit="bytes",
            precision="platform-qualified peak",
        ), {"rss_platform": system, "rss_raw_value": raw, "rss_raw_unit": raw_unit, "rss_normalized_unit": "bytes"}

    def _allocation_start(self) -> tuple[bool, Measurement | None]:
        if not self.plan.track_python_allocations:
            return False, _unavailable(method="tracemalloc.get_traced_memory:v1", scope="process", unit="bytes", reason="representative allocation profiling disabled")
        if self._tracemalloc is None:
            return False, _unavailable(method="tracemalloc.get_traced_memory:v1", scope="process", unit="bytes", reason="tracemalloc adapter unavailable")
        try:
            already_tracing = self._tracemalloc.is_tracing()  # type: ignore[attr-defined]
            if not already_tracing:
                self._tracemalloc.start()  # type: ignore[attr-defined]
            self._tracemalloc.reset_peak()  # type: ignore[attr-defined]
            return not already_tracing, None
        except (AttributeError, RuntimeError) as error:
            return False, _unavailable(method="tracemalloc.get_traced_memory:v1", scope="process", unit="bytes", reason=f"tracemalloc adapter unavailable: {type(error).__name__}")

    def _allocation_end(self, started_here: bool, prior: Measurement | None) -> Measurement:
        if prior is not None:
            return prior
        assert self._tracemalloc is not None
        try:
            _current, peak = self._tracemalloc.get_traced_memory()  # type: ignore[attr-defined]
            return Measurement.observed(int(peak), method="tracemalloc.get_traced_memory:v1", scope="process", unit="bytes", precision="Python allocator peak")
        except (AttributeError, RuntimeError) as error:
            return _unavailable(method="tracemalloc.get_traced_memory:v1", scope="process", unit="bytes", reason=f"tracemalloc adapter unavailable: {type(error).__name__}")
        finally:
            if started_here:
                self._tracemalloc.stop()  # type: ignore[attr-defined]

    def _overhead(self) -> Measurement:
        start = self._clock()
        self._cpu_clock()
        self._peak_rss()
        elapsed = max(0, self._clock() - start)
        return Measurement.observed(elapsed, method="profiling_adapter_empty_call:v1", scope="process", unit="ns", precision="1 ns")

    def _disabled(self) -> ProfileMeasurement:
        unavailable = _unavailable(method="not_collected", scope="process", unit="ns", reason="profiling disabled")
        return ProfileMeasurement(
            RuntimeResourceFacts(
                wall_time=unavailable,
                process_cpu_time=unavailable,
                peak_host_memory=_unavailable(method="not_collected", scope="process", unit="bytes", reason="profiling disabled"),
                concurrency=_unavailable(method="not_collected", scope="process", unit="threads", reason="profiling disabled"),
                machine_environment=_unavailable(method="not_collected", scope="host", unit="identity", reason="profiling disabled"),
                backend_device_time=_unavailable(method="not_applicable", scope="backend", unit="ns", reason="CPU execution"),
                backend_device_memory=_unavailable(method="not_applicable", scope="backend", unit="bytes", reason="CPU execution"),
            ),
            _unavailable(method="not_collected", scope="process", unit="ns", reason="profiling disabled"),
            _unavailable(method="not_collected", scope="process", unit="bytes", reason="profiling disabled"),
            {}, {}, False, self.plan.level,
        )

    def _enforce_required(self, profile: ProfileMeasurement) -> None:
        facts = {
            "wall_time": profile.runtime.wall_time,
            "process_cpu_time": profile.runtime.process_cpu_time,
            "peak_host_memory": profile.runtime.peak_host_memory,
            "python_allocation_peak": profile.python_allocation_peak,
        }
        missing = sorted(name for name in self.plan.required if facts[name].value is None)
        if missing:
            raise ProfilingRequirementError("strict profiling requirements unavailable: " + ", ".join(missing))

    def measure(self, action: Callable[[], _T]) -> tuple[_T, ProfileMeasurement]:
        """Run once and return its result plus process-local observation facts."""
        if not callable(action):
            raise ValueError("profiled action must be callable")
        if not self.plan.enabled:
            return action(), self._disabled()
        overhead = self._overhead()
        allocation_started_here, allocation_prior = self._allocation_start()
        wall_start, cpu_start = self._clock(), self._cpu_clock()
        try:
            result = action()
        finally:
            wall_end, cpu_end = self._clock(), self._cpu_clock()
        peak, raw_context = self._peak_rss()
        allocation = self._allocation_end(allocation_started_here, allocation_prior)
        profile = ProfileMeasurement(
            RuntimeResourceFacts(
                wall_time=Measurement.observed(max(0, wall_end - wall_start), method="time.perf_counter_ns:v1", scope="process", unit="ns", precision="1 ns"),
                process_cpu_time=Measurement.observed(max(0, cpu_end - cpu_start), method="time.process_time_ns:v1", scope="process", unit="ns", precision="1 ns"),
                peak_host_memory=peak,
                concurrency=self._concurrency(),
                machine_environment=self._machine(),
                backend_device_time=_unavailable(method="not_applicable", scope="backend", unit="ns", reason="CPU execution"),
                backend_device_memory=_unavailable(method="not_applicable", scope="backend", unit="bytes", reason="CPU execution"),
            ),
            overhead,
            allocation,
            self._environment_context(),
            raw_context,
            True,
            self.plan.level,
        )
        self._enforce_required(profile)
        return result, profile
