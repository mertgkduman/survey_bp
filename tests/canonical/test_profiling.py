"""Scientific local-profiling contracts for canonical CSS runs."""

from __future__ import annotations

import pytest


def test_semantic_trace_digest_contract_exists():
    """Replay comparison needs a timing-independent bounded trace identity."""
    from bp_registry.canonical import tracing

    assert hasattr(tracing, "semantic_digest")
    assert tracing.semantic_digest({"candidate": "a", "wall_time_ns": 1}) == tracing.semantic_digest(
        {"candidate": "a", "wall_time_ns": 2}
    )


def test_profile_contract_module_exists():
    """The typed profiler is a project-owned canonical contract."""
    import importlib.util

    assert importlib.util.find_spec("bp_registry.canonical.profiling") is not None


def test_default_local_profile_records_qualified_local_facts_and_separate_overhead():
    from bp_registry.canonical.profiling import LocalProfiler, ProfilingPlan

    plan = ProfilingPlan()
    assert plan.enabled is True
    value, profile = LocalProfiler(plan, environment={
        "OMP_NUM_THREADS": "1",
        "SECRET_TOKEN": "must-not-be-recorded",
        "OPENBLAS_NUM_THREADS": "secret-looking-but-not-a-count",
        "PATH": "/private/path/must-not-be-recorded",
    }).measure(lambda: "clean-result")

    assert value == "clean-result"
    facts = profile.runtime.as_evidence()
    assert facts["wall_time"]["value"] is not None
    assert facts["wall_time"]["method"] == "time.perf_counter_ns:v1"
    assert facts["process_cpu_time"]["value"] is not None
    assert facts["process_cpu_time"]["scope"] == "process"
    assert facts["peak_host_memory"]["method"].startswith("resource.getrusage:RUSAGE_SELF")
    assert profile.adapter_overhead.value is not None
    assert profile.adapter_overhead.method == "profiling_adapter_empty_call:v1"
    assert profile.environment["OMP_NUM_THREADS"] == "1"
    assert "SECRET_TOKEN" not in profile.environment
    assert "OPENBLAS_NUM_THREADS" not in profile.environment
    assert "PATH" not in profile.environment
    assert all("/" not in str(value) for value in profile.environment.values())


def test_public_profile_rss_normalization_requires_linux_and_darwin_equality():
    """The raw platform fact is the exact source for normalized RSS bytes."""
    from bp_registry.canonical.profiling import (
        LocalProfiler,
        ProfilingPlan,
        validate_public_clean_low_overhead_evidence,
    )

    class Resource:
        RUSAGE_SELF = object()

        @staticmethod
        def getrusage(_scope):
            return type("Usage", (), {"ru_maxrss": 7})()

    for system, expected in (("Linux", 7 * 1024), ("Darwin", 7)):
        _value, profile = LocalProfiler(
            ProfilingPlan(), resource_module=Resource(), platform_system=lambda system=system: system,
        ).measure(lambda: None)
        evidence = profile.as_evidence()
        assert evidence["runtime"]["peak_host_memory"]["value"] == expected
        assert validate_public_clean_low_overhead_evidence(evidence).runtime.peak_host_memory.value == expected
        evidence["runtime"]["peak_host_memory"]["value"] += 1
        with pytest.raises(ValueError, match="normalization"):
            validate_public_clean_low_overhead_evidence(evidence)


def test_public_profile_rss_unavailable_contract_matches_each_producer_branch():
    """Every unavailable RSS record has one producer-reachable grammar."""
    from bp_registry.canonical.profiling import (
        LocalProfiler,
        ProfilingPlan,
        validate_public_clean_low_overhead_evidence,
    )

    class Resource:
        RUSAGE_SELF = object()

        @staticmethod
        def getrusage(_scope):
            return type("Usage", (), {"ru_maxrss": 7})()

    def raising(error):
        class RaisingResource:
            RUSAGE_SELF = object()

            @staticmethod
            def getrusage(_scope):
                raise error

        return RaisingResource()

    base_method = "resource.getrusage:RUSAGE_SELF:v1"
    raw_method = "resource.getrusage:RUSAGE_SELF:ru_maxrss:v1"
    cases = [
        ("absent", None, "Linux", base_method, "resource adapter unavailable", {}),
        ("attribute", raising(AttributeError("missing")), "Linux", base_method, "resource adapter unavailable: AttributeError", {}),
        ("os", raising(OSError("adapter")), "Linux", base_method, "resource adapter unavailable: OSError", {}),
        ("value", raising(ValueError("bad")), "Linux", base_method, "resource adapter unavailable: ValueError", {}),
        ("type", raising(TypeError("bad")), "Linux", base_method, "resource adapter unavailable: TypeError", {}),
        ("permission", raising(PermissionError("denied")), "Linux", base_method, "resource adapter unavailable: OSError", {}),
        ("empty-platform", Resource(), "", base_method, "resource adapter unavailable: ValueError", {}),
        ("non-string-platform", Resource(), 7, base_method, "resource adapter unavailable: ValueError", {}),
        (
            "negative",
            type("NegativeResource", (), {"RUSAGE_SELF": object(), "getrusage": staticmethod(lambda _scope: type("Usage", (), {"ru_maxrss": -1})())})(),
            "Linux",
            raw_method,
            "negative RSS observation",
            {},
        ),
        (
            "unsupported-platform",
            Resource(),
            "FreeBSD",
            raw_method,
            "RSS normalization semantics unavailable",
            {"rss_platform": "FreeBSD", "rss_raw_value": 7, "rss_raw_unit": "unknown"},
        ),
    ]

    for _label, resource_module, system, method, reason, raw_context in cases:
        _value, profile = LocalProfiler(
            ProfilingPlan(), resource_module=resource_module, platform_system=lambda system=system: system,
        ).measure(lambda: None)
        rss = profile.runtime.peak_host_memory
        assert (rss.value, rss.method, rss.unavailable_reason, dict(profile.raw_context)) == (
            None, method, reason, raw_context,
        )
        assert validate_public_clean_low_overhead_evidence(profile.as_evidence()) == profile


def test_disabled_and_unavailable_profiles_remain_explicit_or_fail_closed_when_required():
    from bp_registry.canonical.profiling import (
        LocalProfiler,
        ProfilingPlan,
        ProfilingRequirementError,
    )

    value, disabled = LocalProfiler(ProfilingPlan(enabled=False)).measure(lambda: 3)
    assert value == 3
    assert disabled.runtime.wall_time.value is None
    assert disabled.runtime.wall_time.unavailable_reason == "profiling disabled"

    permissive = LocalProfiler(ProfilingPlan(), resource_module=None)
    _value, missing = permissive.measure(lambda: 4)
    assert missing.runtime.peak_host_memory.value is None
    assert missing.runtime.peak_host_memory.unavailable_reason == "resource adapter unavailable"

    strict = LocalProfiler(
        ProfilingPlan(required=frozenset({"peak_host_memory"})), resource_module=None
    )
    with pytest.raises(ProfilingRequirementError, match="peak_host_memory"):
        strict.measure(lambda: 5)


def test_representative_python_allocation_is_opt_in_and_has_typed_missingness():
    from bp_registry.canonical.profiling import LocalProfiler, ProfilingPlan

    _value, profiled = LocalProfiler(ProfilingPlan(track_python_allocations=True)).measure(
        lambda: [item for item in range(50)]
    )
    assert profiled.python_allocation_peak.value is not None
    assert profiled.python_allocation_peak.unit == "bytes"
    assert profiled.python_allocation_peak.scope == "process"


def test_failing_profiled_action_restores_profiler_owned_tracemalloc():
    from bp_registry.canonical.profiling import LocalProfiler, ProfilingPlan

    import tracemalloc

    assert tracemalloc.is_tracing() is False
    profiler = LocalProfiler(ProfilingPlan(track_python_allocations=True))

    try:
        with pytest.raises(RuntimeError, match="planned action failure"):
            profiler.measure(lambda: (_ for _ in ()).throw(RuntimeError("planned action failure")))

        assert tracemalloc.is_tracing() is False
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()


def test_profiler_preserves_caller_owned_tracemalloc_on_failure():
    from bp_registry.canonical.profiling import LocalProfiler, ProfilingPlan

    import tracemalloc

    assert tracemalloc.is_tracing() is False
    tracemalloc.start()
    try:
        profiler = LocalProfiler(ProfilingPlan(track_python_allocations=True))
        with pytest.raises(RuntimeError, match="caller-owned tracer failure"):
            profiler.measure(lambda: (_ for _ in ()).throw(RuntimeError("caller-owned tracer failure")))
        assert tracemalloc.is_tracing() is True
    finally:
        tracemalloc.stop()


def test_prespecified_representative_and_diagnostic_cohorts_keep_distinct_claims():
    from bp_registry.canonical.profiling import CohortSelection

    representative = CohortSelection.representative(
        run_identity="sample-7", stratum="syndrome-weight-2", inclusion_probability=0.25
    )
    diagnostic = CohortSelection.diagnostic(
        run_identity="sample-8", stratum="tail", reason="rare_nonconvergence"
    )

    assert representative.selected_before_outcome is True
    assert representative.population_estimate_eligible is True
    assert representative.inclusion_probability == 0.25
    assert diagnostic.population_estimate_eligible is False
    assert diagnostic.selection_reason == "rare_nonconvergence"
    assert diagnostic.inclusion_probability is None


def test_replay_links_agree_on_semantics_but_not_timing_and_retain_divergence():
    from bp_registry.canonical.profiling import CohortSelection, ReplayLink

    selection = CohortSelection.representative(
        run_identity="sample-7", stratum="syndrome-weight-2", inclusion_probability=0.25
    )
    clean = {
        "candidate": "candidate-a", "termination": "completed", "work": {"bp_calls": 1},
        "lineage": "lineage-a", "semantic_trace_digest": "a" * 64, "wall_time_ns": 10,
    }
    profiled = {**clean, "wall_time_ns": 80}
    link = ReplayLink.create(
        clean_run_id="clean-7", profile_run_id="profile-7", manifest_identity="manifest-a",
        sample_identity="sample-7", decoder_randomness_identity="rng-a", ordering_identity="order-a",
        cohort=selection, profiling_level="representative", overhead_ns=7,
        clean_semantics=clean, profiled_semantics=profiled,
    )
    assert link.semantic_agreement.agrees is True
    assert link.population_estimate_eligible is True
    assert link.overhead_ns == 7

    divergent = ReplayLink.create(
        clean_run_id="clean-8", profile_run_id="profile-8", manifest_identity="manifest-a",
        sample_identity="sample-7", decoder_randomness_identity="rng-a", ordering_identity="order-a",
        cohort=selection, profiling_level="representative", overhead_ns=7,
        clean_semantics=clean, profiled_semantics={**profiled, "candidate": "candidate-b"},
    )
    assert divergent.semantic_agreement.agrees is False
    assert divergent.semantic_agreement.mismatches == ("candidate",)
    assert divergent.status == "diagnostic_divergence"
    assert divergent.population_estimate_eligible is False


def test_replay_rejects_mismatched_cohort_sample_identity():
    from bp_registry.canonical.profiling import CohortSelection, ReplayLink

    selection = CohortSelection.representative(
        run_identity="sample-7", stratum="syndrome-weight-2", inclusion_probability=0.25
    )
    semantics = {
        "candidate": "candidate-a", "termination": "completed", "work": {"bp_calls": 1},
        "lineage": "lineage-a", "semantic_trace_digest": "a" * 64,
    }

    with pytest.raises(ValueError, match="cohort run identity must equal replay sample identity"):
        ReplayLink.create(
            clean_run_id="clean-8", profile_run_id="profile-8", manifest_identity="manifest-a",
            sample_identity="sample-8", decoder_randomness_identity="rng-a", ordering_identity="order-a",
            cohort=selection, profiling_level="representative", overhead_ns=7,
            clean_semantics=semantics, profiled_semantics=semantics,
        )
