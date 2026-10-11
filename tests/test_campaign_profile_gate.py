"""Regression coverage for the measured campaign authorization gate."""

from __future__ import annotations

import importlib

import pytest

from bp_registry.canonical.budgets import Measurement, RuntimeResourceFacts
from bp_registry.canonical.profiling import CohortSelection, ProfileMeasurement, ReplayLink


def _api():
    try:
        module = importlib.import_module("bp_registry.campaigns.profiling_gate")
    except ModuleNotFoundError:
        module = None
    assert module is not None, "the campaign profiling gate must be available"
    return module


def _profile(*, memory: int | None = 8_192) -> ProfileMeasurement:
    def observed(value: int, *, unit: str) -> Measurement:
        return Measurement.observed(value, method="test:v1", scope="process", unit=unit, precision="exact")

    unavailable = Measurement.unavailable(
        method="test:v1", scope="process", unit="bytes", precision="unknown", reason="not available"
    )
    return ProfileMeasurement(
        runtime=RuntimeResourceFacts(
            wall_time=observed(100, unit="ns"),
            process_cpu_time=observed(80, unit="ns"),
            peak_host_memory=observed(memory, unit="bytes") if memory is not None else unavailable,
            concurrency=observed(1, unit="threads"),
            machine_environment=Measurement.observed(
                "test-host", method="test:v1", scope="host", unit="identity", precision="declared"
            ),
            backend_device_time=unavailable,
            backend_device_memory=unavailable,
        ),
        adapter_overhead=observed(2, unit="ns"),
        python_allocation_peak=observed(4_096, unit="bytes"),
        environment={"OMP_NUM_THREADS": "1"},
        raw_context={},
        enabled=True,
        level="representative",
    )


def _run(*, sample: str, path_class: str, memory: int | None = 8_192, mismatch: bool = False):
    api = _api()
    semantics = {
        "candidate": "candidate", "termination": "converged", "work": {"bp_calls": 1},
        "lineage": "root", "semantic_trace_digest": "a" * 64,
    }
    profiled = dict(semantics)
    if mismatch:
        profiled["candidate"] = "different"
    cohort = CohortSelection.representative(
        run_identity=sample, stratum=path_class, inclusion_probability=0.5,
    )
    link = ReplayLink.create(
        clean_run_id=f"clean-{sample}", profile_run_id=f"profile-{sample}",
        manifest_identity="b" * 64, sample_identity=sample,
        decoder_randomness_identity="c" * 64, ordering_identity="d" * 64,
        cohort=cohort, profiling_level="representative", overhead_ns=2,
        clean_semantics=semantics, profiled_semantics=profiled,
    )
    return api.OperationalEvidenceV1(
        campaign_spec_digest="e" * 64, campaign_plan_digest="f" * 64,
        shard_receipt_sha256="1" * 64, merge_receipt_sha256="2" * 64,
        replay_receipt_sha256="3" * 64, profile_receipt_sha256=("4" if path_class == "fast" else "5") * 64,
        verified_shard=True, verified_merge=True, verified_replay=True,
        replay_link=link, profile=_profile(memory=memory),
        clean_semantics=semantics, profiled_semantics=profiled,
        path_class=path_class, event_count=2, ledger_bytes=300, sidecar_bytes=20,
        replay_wall_time_ns=40, scheduler_launch_overhead_ns=10, shard_fixed_cost_ns=5,
        allocation={"cpus": 1},
    )


def _aggregate(*, memory: int | None = 8_192):
    api = _api()
    return api.aggregate_representative_evidence((
        _run(sample="sample-1", path_class="fast", memory=memory),
        _run(sample="sample-2", path_class="slow", memory=memory),
    ))


def _proposal():
    api = _api()
    return api.ProposedCampaignV1(
        campaign_spec_digest="e" * 64, campaign_plan_digest="f" * 64,
        total_shots=10, max_shard_shots=2, scientific_caps={"max_shots": 10, "max_bp_calls": 10},
        operational_allocation={"workers": 4, "cpus_per_worker": 1},
    )


def _site(**overrides: int | None):
    api = _api()
    values = {
        "max_cpu_time_ns": 800, "max_wall_time_ns": 1_000, "max_storage_bytes": 3_200,
        "max_shard_bytes": 640, "max_replay_time_ns": 400, "max_peak_memory_bytes": 8_192,
        "max_scheduler_cost_ns": 75,
    }
    values.update(overrides)
    return api.SiteCapabilityV1(site_capability_sha256="6" * 64, **values)


def test_representative_clean_profiled_evidence_measures_throughput_storage_and_memory() -> None:
    aggregate = _aggregate()

    assert aggregate.sample_count == 2
    assert aggregate.fast_path_samples == 1
    assert aggregate.slow_path_samples == 1
    assert aggregate.decoder_wall_time_ns == 200
    assert aggregate.ledger_bytes == 600
    assert aggregate.memory_available is True
    assert aggregate.decoder_shots_per_second > 0
    assert aggregate.replay_shots_per_second > 0
    assert aggregate.decoder_ns_per_event == 50
    assert aggregate.ledger_bytes_per_event == 150


def test_semantic_mismatch_and_post_outcome_selection_never_enter_a_projection() -> None:
    api = _api()
    with pytest.raises(ValueError, match="semantic"):
        api.aggregate_representative_evidence((
            _run(sample="sample-1", path_class="fast", mismatch=True),
            _run(sample="sample-2", path_class="slow"),
        ))

    record = _run(sample="sample-1", path_class="fast")
    replacement = {field: getattr(record, field) for field in record.__dataclass_fields__}
    replacement["replay_link"] = ReplayLink.create(
        clean_run_id="new-clean", profile_run_id="new-profile", manifest_identity="b" * 64,
        sample_identity="sample-1", decoder_randomness_identity="c" * 64,
        ordering_identity="d" * 64,
        cohort=CohortSelection.diagnostic(run_identity="sample-1", stratum="fast", reason="outcome"),
        profiling_level="representative", overhead_ns=2,
        clean_semantics=record.clean_semantics, profiled_semantics=record.profiled_semantics,
    )
    with pytest.raises(ValueError, match="representative"):
        api.OperationalEvidenceV1(**replacement)


def test_missing_memory_remains_explicit_and_denies_authorization() -> None:
    aggregate = _aggregate(memory=None)
    assert aggregate.memory_available is False
    assert "peak_host_memory" in aggregate.missing_measurements


def test_authorization_binds_all_measured_receipts_before_allowing_boundary() -> None:
    api = _api()
    boundary = api.authorize_campaign(
        aggregate=_aggregate(), proposal=_proposal(), site=_site(), safety_factor=api.SafetyFactorV1(1, 1),
    )

    assert boundary.decision == "allow"
    assert boundary.replay_receipt_sha256s == ("3" * 64,)
    assert boundary.profile_receipt_sha256s == tuple(sorted(("4" * 64, "5" * 64)))


@pytest.mark.parametrize("field", [
    "max_cpu_time_ns", "max_wall_time_ns", "max_storage_bytes", "max_shard_bytes",
    "max_replay_time_ns", "max_peak_memory_bytes", "max_scheduler_cost_ns",
])
def test_authorization_denies_each_ceiling_exceedance(field: str) -> None:
    api = _api()
    receipt = api.authorize_campaign(
        aggregate=_aggregate(), proposal=_proposal(), site=_site(**{field: 1}), safety_factor=api.SafetyFactorV1(1, 1),
    )
    assert receipt.decision == "deny"
    assert any(field in reason for reason in receipt.reasons)


def test_missing_memory_and_site_capability_are_fail_closed() -> None:
    api = _api()
    missing_memory = api.authorize_campaign(
        aggregate=_aggregate(memory=None), proposal=_proposal(), site=_site(), safety_factor=api.SafetyFactorV1(1, 1),
    )
    missing_site = api.authorize_campaign(
        aggregate=_aggregate(), proposal=_proposal(), site=_site(max_storage_bytes=None), safety_factor=api.SafetyFactorV1(1, 1),
    )

    assert missing_memory.decision == "deny"
    assert "missing_measurement:peak_host_memory" in missing_memory.reasons
    assert missing_site.decision == "deny"
    assert "missing_site_ceiling:max_storage_bytes" in missing_site.reasons


def test_safety_factor_changes_receipt_but_worker_topology_is_not_scientific_identity() -> None:
    api = _api()
    aggregate = _aggregate()
    proposal = _proposal()
    boundary = api.authorize_campaign(
        aggregate=aggregate, proposal=proposal, site=_site(), safety_factor=api.SafetyFactorV1(1, 1),
    )
    changed_margin = api.authorize_campaign(
        aggregate=aggregate, proposal=proposal, site=_site(), safety_factor=api.SafetyFactorV1(2, 1),
    )
    moved_payload = {field: getattr(proposal, field) for field in proposal.__dataclass_fields__}
    moved_payload["operational_allocation"] = {"workers": 8, "cpus_per_worker": 1}
    moved_workers = api.ProposedCampaignV1(**moved_payload)

    assert changed_margin.decision == "deny"
    assert boundary.receipt_sha256 != changed_margin.receipt_sha256
    assert boundary.scientific_identity == api.scientific_authorization_identity(proposal)
    assert boundary.scientific_identity == api.scientific_authorization_identity(moved_workers)
    assert boundary.operational_allocation != moved_workers.operational_allocation


def test_resource_gate_rejects_unbounded_campaign_arithmetic() -> None:
    api = _api()
    with pytest.raises(ValueError, match="bounded"):
        api.ProposedCampaignV1(
            campaign_spec_digest="e" * 64, campaign_plan_digest="f" * 64,
            total_shots=1 << 63, max_shard_shots=1,
            scientific_caps={"max_shots": 1}, operational_allocation={"workers": 1},
        )
