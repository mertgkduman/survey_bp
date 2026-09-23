"""Typed, local-only profiling facts for scientifically comparable CSS runs.

This module measures process-local runtime resources.  It deliberately does
not infer unavailable counters, inspect arbitrary environment variables, or
present instrumented duration as a clean-run estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
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
        if any(
            (isinstance(value, str) and (not value.isdecimal() or int(value) < 1))
            or (isinstance(value, int) and (isinstance(value, bool) or value < 1))
            or not isinstance(value, (str, int))
            for value in environment.values()
        ):
            raise ValueError("profile environment values must be positive thread counts")
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


@dataclass(frozen=True, slots=True)
class CohortSelection:
    """Declared meaning of an already selected clean/profile sample."""

    cohort: Literal["clean", "representative", "diagnostic"]
    run_identity: str
    stratum: str
    inclusion_probability: float | None
    selection_reason: str
    selected_before_outcome: bool

    def __post_init__(self) -> None:
        if self.cohort not in {"clean", "representative", "diagnostic"}:
            raise ValueError("profiling cohort must be clean, representative, or diagnostic")
        if not isinstance(self.run_identity, str) or not self.run_identity or not isinstance(self.stratum, str) or not self.stratum:
            raise ValueError("cohort run identity and decoder-independent stratum must be nonempty")
        if not isinstance(self.selection_reason, str) or not self.selection_reason:
            raise ValueError("cohort selection reason must be explicit")
        if type(self.selected_before_outcome) is not bool:
            raise ValueError("cohort outcome ordering must be explicit")
        if self.cohort == "representative":
            if not self.selected_before_outcome:
                raise ValueError("representative profiling must be selected before outcomes")
            if not isinstance(self.inclusion_probability, (int, float)) or isinstance(self.inclusion_probability, bool) or not 0 < float(self.inclusion_probability) <= 1:
                raise ValueError("representative inclusion probability must be in (0, 1]")
            object.__setattr__(self, "inclusion_probability", float(self.inclusion_probability))
        elif self.inclusion_probability is not None:
            raise ValueError("clean and diagnostic cohorts do not carry sampled inclusion probabilities")

    @classmethod
    def clean(cls, *, run_identity: str, stratum: str = "full_population") -> "CohortSelection":
        return cls("clean", run_identity, stratum, None, "full_clean_population", True)

    @classmethod
    def representative(cls, *, run_identity: str, stratum: str, inclusion_probability: float) -> "CohortSelection":
        # Callers create this record at selection time, before any outcome is available.
        return cls("representative", run_identity, stratum, inclusion_probability, "prespecified_stratified_pair", True)

    @classmethod
    def diagnostic(cls, *, run_identity: str, stratum: str, reason: str) -> "CohortSelection":
        return cls("diagnostic", run_identity, stratum, None, reason, False)

    @property
    def population_estimate_eligible(self) -> bool:
        """Only a pre-outcome representative paired selection may estimate profiling population facts."""
        return self.cohort == "representative" and self.selected_before_outcome

    def as_evidence(self) -> dict[str, object]:
        return {
            "cohort": self.cohort,
            "run_identity": self.run_identity,
            "stratum": self.stratum,
            "inclusion_probability": self.inclusion_probability,
            "selection_reason": self.selection_reason,
            "selected_before_outcome": self.selected_before_outcome,
            "population_estimate_eligible": self.population_estimate_eligible,
        }


@dataclass(frozen=True, slots=True)
class SemanticAgreement:
    """A replay comparison with visible mismatch fields rather than silent exclusion."""

    agrees: bool
    mismatches: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.agrees) is not bool or tuple(sorted(set(self.mismatches))) != self.mismatches:
            raise ValueError("semantic agreement mismatches must be ordered and unique")
        if self.agrees != (not self.mismatches):
            raise ValueError("semantic agreement must match its mismatch fields")


_SEMANTIC_FIELDS = ("candidate", "termination", "work", "lineage", "semantic_trace_digest")


def compare_semantics(clean: Mapping[str, object], profiled: Mapping[str, object]) -> SemanticAgreement:
    """Compare decoder semantics only; runtime and profiling facts are intentionally excluded."""
    if not isinstance(clean, Mapping) or not isinstance(profiled, Mapping):
        raise ValueError("replay semantics must be mappings")
    mismatches: list[str] = []
    for field in _SEMANTIC_FIELDS:
        if field not in clean or field not in profiled or clean[field] != profiled[field]:
            mismatches.append(field)
    return SemanticAgreement(not mismatches, tuple(mismatches))


@dataclass(frozen=True, slots=True)
class ReplayLink:
    """Immutable clean/profile pairing with truth-preserving divergent diagnostics."""

    clean_run_id: str
    profile_run_id: str
    manifest_identity: str
    sample_identity: str
    decoder_randomness_identity: str
    ordering_identity: str
    cohort: CohortSelection
    profiling_level: str
    overhead_ns: int
    retention: Literal["paired_summary", "bounded_trace", "retained_divergence"]
    semantic_agreement: SemanticAgreement

    def __post_init__(self) -> None:
        for name in ("clean_run_id", "profile_run_id", "manifest_identity", "sample_identity", "decoder_randomness_identity", "ordering_identity", "profiling_level"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError("replay identities and profiling level must be nonempty strings")
        if self.clean_run_id == self.profile_run_id:
            raise ValueError("clean and profiled runs must have distinct run IDs")
        if not isinstance(self.cohort, CohortSelection) or not isinstance(self.semantic_agreement, SemanticAgreement):
            raise ValueError("replay link requires typed cohort and semantic agreement")
        if self.cohort.run_identity != self.sample_identity:
            raise ValueError("cohort run identity must equal replay sample identity")
        if type(self.overhead_ns) is not int or self.overhead_ns < 0:
            raise ValueError("profile replay overhead must be a nonnegative integer nanosecond count")
        if self.retention not in {"paired_summary", "bounded_trace", "retained_divergence"}:
            raise ValueError("replay retention must be explicit and bounded")

    @classmethod
    def create(
        cls,
        *,
        clean_run_id: str,
        profile_run_id: str,
        manifest_identity: str,
        sample_identity: str,
        decoder_randomness_identity: str,
        ordering_identity: str,
        cohort: CohortSelection,
        profiling_level: str,
        overhead_ns: int,
        clean_semantics: Mapping[str, object],
        profiled_semantics: Mapping[str, object],
        retention: Literal["paired_summary", "bounded_trace", "retained_divergence"] = "paired_summary",
    ) -> "ReplayLink":
        agreement = compare_semantics(clean_semantics, profiled_semantics)
        if not agreement.agrees:
            retention = "retained_divergence"
        return cls(
            clean_run_id, profile_run_id, manifest_identity, sample_identity,
            decoder_randomness_identity, ordering_identity, cohort, profiling_level,
            overhead_ns, retention, agreement,
        )

    @property
    def status(self) -> Literal["paired_agreement", "diagnostic_divergence"]:
        return "paired_agreement" if self.semantic_agreement.agrees else "diagnostic_divergence"

    @property
    def population_estimate_eligible(self) -> bool:
        return self.cohort.population_estimate_eligible and self.semantic_agreement.agrees

    def as_evidence(self) -> dict[str, object]:
        return {
            "clean_run_id": self.clean_run_id,
            "profile_run_id": self.profile_run_id,
            "manifest_identity": self.manifest_identity,
            "sample_identity": self.sample_identity,
            "decoder_randomness_identity": self.decoder_randomness_identity,
            "ordering_identity": self.ordering_identity,
            "cohort": self.cohort.as_evidence(),
            "profiling_level": self.profiling_level,
            "overhead_ns": self.overhead_ns,
            "retention": self.retention,
            "semantic_agreement": {"agrees": self.semantic_agreement.agrees, "mismatches": list(self.semantic_agreement.mismatches)},
            "status": self.status,
            "population_estimate_eligible": self.population_estimate_eligible,
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
            if (value := self._environment.get(key)) is not None and value.isdecimal() and int(value) >= 1
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
        action_error: BaseException | None = None
        try:
            try:
                result = action()
            except BaseException as error:
                action_error = error
                raise
            finally:
                wall_end, cpu_end = self._clock(), self._cpu_clock()
        finally:
            try:
                allocation = self._allocation_end(allocation_started_here, allocation_prior)
            except BaseException:
                if action_error is None:
                    raise
        peak, raw_context = self._peak_rss()
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
