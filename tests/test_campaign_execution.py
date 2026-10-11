"""One-unit tracer coverage for the immutable campaign boundary."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
INNER_MANIFEST = "data/manifests/canonical-three-qubit-development.json"


def _campaign_api():
    """Keep the RED failure an assertion about the public campaign capability."""
    try:
        return importlib.import_module("bp_registry.campaigns")
    except ModuleNotFoundError:
        return None


def _spec_payload() -> dict[str, object]:
    manifest_bytes = (ROOT / INNER_MANIFEST).read_bytes()
    from bp_registry.manifests import manifest_digest, preflight

    manifest_namespace = manifest_digest(preflight(ROOT / INNER_MANIFEST).manifest)
    return {
        "schema": "campaign_spec_v1",
        "inner_manifest_path": INNER_MANIFEST,
        "inner_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "source_lock_sha256": "1" * 64,
        "environment_lock_sha256": "2" * 64,
        "cohort_id": "tracer",
        "point_id": "p100",
        "sample_namespace": manifest_namespace,
        "sample_id": 1,
        "arm_id": "identity",
        "decoder_seed_identity": "canonical-deterministic-no-local-randomness-v1",
        "final_look": 1,
        "alpha": 0.05,
        "outcome_rule": "all_terminal_shots_are_logical_failures",
        "max_events": 64,
        "max_evidence_bytes": 1_000_000,
    }


def test_tracer_runs_seals_verifies_and_reconstructs_zero_failure(tmp_path: Path):
    """A frozen one-shot CSS unit has replayable, exact all-shot evidence."""
    api = _campaign_api()
    assert api is not None, "campaign_spec_v1 tracer must provide the campaign package"

    spec = api.CampaignSpecV1.model_validate(_spec_payload())
    first = api.run_one_unit(spec, campaign_root=ROOT, output_root=tmp_path / "first", worker_label="local-a")
    second = api.run_one_unit(spec, campaign_root=ROOT, output_root=tmp_path / "second", worker_label="slurm-999")

    assert first["campaign_spec_digest"] == second["campaign_spec_digest"]
    assert first["campaign_plan_digest"] == second["campaign_plan_digest"]
    assert first["unit_key"] == second["unit_key"]
    assert first["physical_sample_identity"] == second["physical_sample_identity"]
    assert first["terminal_fact"] == second["terminal_fact"]
    assert "campaign_plan_digest" not in first["unit_key"]
    assert b"campaign_plan_digest" not in first["campaign_spec_bytes"]
    assert b"campaign_plan_digest" not in first["campaign_plan_preimage"]

    checked = api.verify_shard(first["receipt_path"], campaign_root=ROOT)
    report = api.reconstruct_fixed_shot(checked)
    assert report["completed"] == 1
    assert report["failures"] == 0
    assert report["interval"]["method"] == "exact"
    assert report["interval"]["upper"] > 0.0


def test_identity_is_acyclic_and_changes_only_with_scientific_primitives():
    """Executor labels never enter scientific identities, while source locks do."""
    api = _campaign_api()
    assert api is not None, "campaign_spec_v1 tracer must provide the campaign package"

    original = api.CampaignSpecV1.model_validate(_spec_payload())
    changed_payload = json.loads(json.dumps(_spec_payload()))
    changed_payload["source_lock_sha256"] = "3" * 64
    changed = api.CampaignSpecV1.model_validate(changed_payload)

    original_plan = api.build_one_unit_plan(original)
    changed_plan = api.build_one_unit_plan(changed)
    assert original_plan.campaign_spec_digest != changed_plan.campaign_spec_digest
    assert original_plan.unit_key != changed_plan.unit_key
    assert original_plan.campaign_plan_digest != changed_plan.campaign_plan_digest
    assert b"campaign_plan_digest" not in original_plan.campaign_spec_bytes
    assert b"campaign_plan_digest" not in original_plan.campaign_plan_preimage


def test_sample_identity_is_arm_and_worker_neutral_but_decoder_randomness_is_arm_scoped():
    """Matched arms retain bytes while decoder-local streams remain independent."""
    from bp_registry.campaigns.identity import (
        decoder_randomness_identity,
        physical_sample_identity,
    )

    scientific = "a" * 64
    sample = physical_sample_identity(
        campaign_spec_digest=scientific,
        cohort_id="bb144",
        point_id="p005",
        sample_namespace="shared-errors-v1",
        sample_id=7,
    )
    assert sample == physical_sample_identity(
        campaign_spec_digest=scientific,
        cohort_id="bb144",
        point_id="p005",
        sample_namespace="shared-errors-v1",
        sample_id=7,
    )
    left = decoder_randomness_identity(
        campaign_spec_digest=scientific, arm_id="spa", sample_id=7,
        decoder_seed_identity="spa-seed-v1",
    )
    right = decoder_randomness_identity(
        campaign_spec_digest=scientific, arm_id="ms", sample_id=7,
        decoder_seed_identity="ms-seed-v1",
    )
    assert left != right


def test_persisted_sample_receipt_rejects_tampered_bytes_before_decoder_use():
    """A non-reproducible backend gets one hash-bound artifact for all arms."""
    from bp_registry.campaigns.identity import (
        PersistedSampleReceiptV1,
        physical_sample_identity,
        verify_persisted_sample,
    )

    artifact = b"fixed physical error vector"
    sample = physical_sample_identity(
        campaign_spec_digest="a" * 64, cohort_id="bb144", point_id="p005",
        sample_namespace="shared-errors-v1", sample_id=7,
    )
    receipt = PersistedSampleReceiptV1(
        campaign_spec_digest="a" * 64, cohort_id="bb144", point_id="p005",
        sample_namespace="shared-errors-v1", sample_id=7,
        physical_sample_identity=sample, artifact_sha256=sha256(artifact).hexdigest(),
        artifact_bytes=len(artifact),
    )
    assert verify_persisted_sample(receipt, artifact) == artifact
    with pytest.raises(ValueError, match="digest"):
        verify_persisted_sample(receipt, b"X" + artifact[1:])


def _planning_inputs():
    from bp_registry.campaigns.planning import CampaignCoordinateV1

    return (
        "a" * 64,
        (CampaignCoordinateV1(
            cohort_id="bb144", point_id="p005", sample_namespace="shared-errors-v1",
            sample_ids=(2, 7),
        ),),
        {"spa": "spa-seed-v1", "ms": "ms-seed-v1"},
    )


def test_unit_key_and_shard_plan_are_acyclic_complete_and_topology_invariant():
    """Scientific shards are fixed before a local or scheduler allocation exists."""
    from bp_registry.campaigns.planning import freeze_work_plan, validate_executor_allocation

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    permuted = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates,
        arm_seed_identities={"ms": "ms-seed-v1", "spa": "spa-seed-v1"},
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    assert plan.campaign_plan_digest == permuted.campaign_plan_digest
    assert plan.unit_keys == permuted.unit_keys
    assert len(plan.unit_keys) == 4
    assert len(set(plan.unit_keys)) == 4
    assert set(key for shard in plan.shards for key in shard.unit_keys) == set(plan.unit_keys)
    assert b"campaign_plan_digest" not in plan.campaign_plan_preimage
    assert set(plan.completed_prefix(1)).isdisjoint(plan.authorized_tail(1))
    assert set(plan.completed_prefix(1)) | set(plan.authorized_tail(1)) == set(plan.unit_keys)
    assert validate_executor_allocation(plan, {shard.shard_id: index for index, shard in enumerate(plan.shards)})
    with pytest.raises(ValueError, match="exactly"):
        validate_executor_allocation(plan, {plan.shards[0].shard_id: 0})


def test_shard_plan_rejects_duplicate_coordinates_and_excessive_bounds():
    """A campaign fails before materializing ambiguous or unbounded work."""
    from bp_registry.campaigns.planning import CampaignCoordinateV1, freeze_work_plan

    with pytest.raises(ValueError, match="unique"):
        CampaignCoordinateV1(
            cohort_id="bb144", point_id="p005", sample_namespace="shared-errors-v1",
            sample_ids=(7, 7),
        )
    digest, coordinates, arms = _planning_inputs()
    with pytest.raises(ValueError, match="max_total_units"):
        freeze_work_plan(
            campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
            look_sample_boundaries=(1, 2), units_per_shard=2, max_total_units=3,
        )


def _bounded_unit_runner(unit: dict[str, object], staging: str) -> dict[str, object]:
    """Pickle-safe deterministic worker fixture for frozen campaign units."""
    del staging
    return {
        "terminal_fact": {
            "unit_key": unit["unit_key"],
            "termination": "converged",
            "outcome": "exact",
            "logical_failure": False,
        },
        "work_vector": {"bp_calls": 1},
        "persisted_sample_bytes": (
            "sample:" + str(unit["physical_sample_identity"])
        ).encode("ascii"),
    }


def _failing_unit_runner(unit: dict[str, object], staging: str) -> dict[str, object]:
    if str(unit["arm_id"]) == "ms":
        raise RuntimeError("injected worker interruption")
    return _bounded_unit_runner(unit, staging)


def test_local_workers_and_arm_order_preserve_frozen_scientific_evidence(tmp_path: Path):
    """Changing bounded pool topology cannot change frozen arm/sample facts."""
    from bp_registry.campaigns.execution import execute_local_work_plan
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    serial = execute_local_work_plan(
        plan, output_root=tmp_path / "serial", workers=1, unit_runner=_bounded_unit_runner,
    )
    parallel = execute_local_work_plan(
        plan, output_root=tmp_path / "parallel", workers=2, unit_runner=_bounded_unit_runner,
    )
    assert serial["scientific_records"] == parallel["scientific_records"]
    assert serial["terminal_unit_keys"] == plan.unit_keys
    assert parallel["observed_concurrency"] <= 2
    assert set(parallel["environment"]) <= {
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
    }
    assert all("unavailable_reason" in item for item in parallel["resource_observations"])


def test_local_worker_failure_seals_incomplete_and_retains_completed_units(tmp_path: Path):
    """An interrupted shard retains completed units and leaves only missing work resumable."""
    from bp_registry.campaigns.execution import execute_local_work_plan
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    result = execute_local_work_plan(
        plan, output_root=tmp_path / "interrupted", workers=2, unit_runner=_failing_unit_runner,
    )
    assert result["incomplete_unit_keys"]
    assert set(result["terminal_unit_keys"]).isdisjoint(result["incomplete_unit_keys"])
    sealed = {record["unit_key"] for record in result["records"]}
    assert sealed < set(plan.unit_keys)
    assert all(Path(record["receipt_path"]).is_file() for record in result["records"])


def _stop_after_first_complete_look(*, look: int, terminal_records: tuple[dict[str, object], ...]) -> dict[str, object]:
    inputs = sorted(str(record["unit_key"]) for record in terminal_records)
    return {
        "decision_input_hashes": [sha256("|".join(inputs).encode("ascii")).hexdigest()],
        "decision_result": {"look": look, "terminal_count": len(inputs)},
        "stop_reason": "all_primary_decisions_resolved",
        "should_stop": look == 1,
    }


def test_finite_look_recovers_stop_receipt_before_any_later_dispatch(tmp_path: Path):
    """A post-decision crash recovers its exact receipt before the next look runs."""
    from bp_registry.campaigns.execution import dispatch_finite_looks
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    root = tmp_path / "finite-look"
    with pytest.raises(InterruptedError, match="after decision"):
        dispatch_finite_looks(
            plan, output_root=root, workers=2, unit_runner=_bounded_unit_runner,
            decision_for_look=_stop_after_first_complete_look, fault_after_decision=True,
        )
    first_look = set(plan.completed_prefix(1))
    assert {path.parent.name.removeprefix("unit-") for path in root.glob("unit-*/receipt.json")} == first_look
    recovered = dispatch_finite_looks(
        plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
        decision_for_look=_stop_after_first_complete_look,
    )
    assert recovered["recovered_stop_receipt"] is True
    assert recovered["authorized_undispatched_keys"] == plan.authorized_tail(1)
    assert {path.parent.name.removeprefix("unit-") for path in root.glob("unit-*/receipt.json")} == first_look
    assert (root / "look-stop-receipt.json").is_file()


def test_finite_look_rejects_a_forged_retained_stop_tail(tmp_path: Path):
    """A retained receipt is checked against the complete frozen boundary again."""
    from bp_registry.campaigns.execution import dispatch_finite_looks
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    root = tmp_path / "forged-stop"
    dispatch_finite_looks(
        plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
        decision_for_look=_stop_after_first_complete_look,
    )
    receipt_path = root / "look-stop-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["authorized_undispatched"] = []
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="conflicts"):
        dispatch_finite_looks(
            plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
            decision_for_look=_stop_after_first_complete_look,
        )


def test_finite_look_maximum_retains_all_realized_units(tmp_path: Path):
    """The maximum declared look stops only after all matched arm units finish."""
    from bp_registry.campaigns.execution import dispatch_finite_looks
    from bp_registry.campaigns.planning import freeze_work_plan

    def maximum(*, look: int, terminal_records: tuple[dict[str, object], ...]) -> dict[str, object]:
        return {
            "decision_input_hashes": [sha256(str(look).encode("ascii")).hexdigest()],
            "decision_result": {"look": look}, "stop_reason": "maximum_reached",
            "should_stop": look == 2,
        }

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    result = dispatch_finite_looks(
        plan, output_root=tmp_path / "maximum", workers=2, unit_runner=_bounded_unit_runner,
        decision_for_look=maximum,
    )
    assert result["stop_receipt"]["stop_reason"] == "maximum_reached"
    assert result["authorized_undispatched_keys"] == ()
    assert len(result["records"]) == len(plan.unit_keys)


def _slurm_api():
    """Keep Slurm transport RED evidence focused on the public adapter."""
    try:
        return importlib.import_module("bp_registry.campaigns.slurm")
    except ModuleNotFoundError:
        return None


def test_slurm_argv_and_array_selection_are_bounded_and_shell_free():
    """A scheduler can select one frozen shard without gaining planning authority."""
    api = _slurm_api()
    assert api is not None, "campaigns must provide the bounded Slurm adapter"

    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    allocation = api.SlurmAllocation(
        partition="research", qos="short", account="bp", wall_minutes=30,
        memory_mb=512, cpus_per_task=1, max_concurrent_tasks=1,
    )
    argv = api.build_sbatch_argv(
        plan, allocation=allocation,
        allowed_values={"partition": {"research"}, "qos": {"short"}, "account": {"bp"}},
        entrypoint=("/usr/bin/python3", "-m", "bp_registry.campaigns.slurm_entry"),
    )
    assert argv == (
        "sbatch", "--array=0-1%1", "--cpus-per-task=1", "--mem=512M", "--time=30",
        "--partition=research", "--qos=short", "--account=bp", "--",
        "/usr/bin/python3", "-m", "bp_registry.campaigns.slurm_entry",
    )
    assert api.select_array_shard(plan, "1") == plan.shards[1]
    for invalid in (None, "", "-1", "2", "1;touch", " 1"):
        with pytest.raises(ValueError):
            api.select_array_shard(plan, invalid)
    with pytest.raises(ValueError, match="allowlist"):
        api.build_sbatch_argv(
            plan,
            allocation=api.SlurmAllocation(
                partition="unapproved", qos="short", account="bp", wall_minutes=30,
                memory_mb=512, cpus_per_task=1, max_concurrent_tasks=1,
            ),
            allowed_values={"partition": {"research"}, "qos": {"short"}, "account": {"bp"}},
            entrypoint=("/usr/bin/python3",),
        )
    with pytest.raises(ValueError, match="scheduler identifier"):
        api.SlurmAllocation(
            partition="research;touch", qos="short", account="bp", wall_minutes=30,
            memory_mb=512, cpus_per_task=1, max_concurrent_tasks=1,
        )
    with pytest.raises(ValueError, match="cpus_per_task"):
        api.SlurmAllocation(
            partition="research", qos="short", account="bp", wall_minutes=30,
            memory_mb=512, cpus_per_task=65, max_concurrent_tasks=1,
        )


def test_slurm_capability_parser_preserves_missing_accounting_as_unavailable():
    """Unknown site policy remains unavailable and cannot become a campaign default."""
    api = _slurm_api()
    assert api is not None, "campaigns must provide the bounded Slurm adapter"

    capabilities = api.parse_site_capabilities(
        scontrol_text="MaxArraySize=32 DefMemPerCPU=2048", sacct_text=None,
    )
    assert capabilities["max_array_size"] == {
        "value": 32, "unavailable_reason": None,
    }
    assert capabilities["default_memory_mb"] == {
        "value": 2048, "unavailable_reason": None,
    }
    assert capabilities["accounting_available"] == {
        "value": None, "unavailable_reason": "sacct output was not supplied",
    }


def _slurm_allocation(api):
    return api.SlurmAllocation(
        partition="research", qos="short", account="bp", wall_minutes=30,
        memory_mb=512, cpus_per_task=1, max_concurrent_tasks=1,
    )


def _scheduler_observation(api, *, task_id: str, state: str = "COMPLETED"):
    return api.SchedulerObservation(
        job_id="81234", task_id=task_id, allocated_cpus=1, elapsed_seconds=2,
        state=state, exit_code=0 if state == "COMPLETED" else 1,
        accounting_available=None, accounting_unavailable_reason="sacct was unavailable",
        launch_overhead_seconds=1, shard_fixed_cost_seconds=1,
    )


def test_executor_equivalence_keeps_scheduler_receipts_out_of_scientific_results(tmp_path: Path):
    """Synthetic array delivery must reproduce local frozen science byte-for-byte."""
    api = _slurm_api()
    assert api is not None and hasattr(api, "execute_synthetic_slurm_array"), (
        "campaigns must execute frozen shards through the synthetic Slurm harness"
    )
    from bp_registry.campaigns.execution import execute_local_work_plan
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    local = execute_local_work_plan(
        plan, output_root=tmp_path / "local", workers=1, unit_runner=_bounded_unit_runner,
    )
    slurm = api.execute_synthetic_slurm_array(
        plan, output_root=tmp_path / "slurm", unit_runner=_bounded_unit_runner,
        allocation=_slurm_allocation(api),
        observations=tuple(_scheduler_observation(api, task_id=str(index)) for index in range(len(plan.shards))),
    )
    assert slurm["terminal_unit_keys"] == local["terminal_unit_keys"]
    assert slurm["scientific_records"] == local["scientific_records"]
    assert slurm["merge_receipt_sha256"] == api.scientific_records_digest(local["scientific_records"])
    assert all("scheduler" not in record for record in slurm["scientific_records"])
    assert all(receipt["executor_receipt"]["scheduler"]["accounting_available"] is None for receipt in slurm["task_receipts"])
    assert all(receipt["executor_receipt"]["scheduler"]["launch_overhead_seconds"] == 1 for receipt in slurm["task_receipts"])


def test_scheduler_receipt_preemption_cancellation_and_duplicate_delivery_are_incomplete(tmp_path: Path):
    """Scheduler outcomes retain observations and leave only their frozen units resumable."""
    api = _slurm_api()
    assert api is not None and hasattr(api, "execute_slurm_array_task"), (
        "campaigns must retain scheduler receipts for one frozen array task"
    )
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    for state in ("FAILED", "PREEMPTED", "CANCELLED"):
        receipt = api.execute_slurm_array_task(
            plan, array_task_id="0", output_root=tmp_path / state,
            unit_runner=_bounded_unit_runner, allocation=_slurm_allocation(api),
            observation=_scheduler_observation(api, task_id="0", state=state),
        )
        assert receipt["terminal_unit_keys"] == ()
        assert receipt["incomplete_unit_keys"] == plan.shards[0].unit_keys
        assert receipt["resume_unit_keys"] == plan.shards[0].unit_keys
        assert receipt["executor_receipt"]["scheduler"]["state"] == state
        assert receipt["executor_receipt"]["scheduler"]["accounting_available"] is None
    with pytest.raises(ValueError, match="duplicate"):
        api.execute_synthetic_slurm_array(
            plan, output_root=tmp_path / "duplicate", unit_runner=_bounded_unit_runner,
            allocation=_slurm_allocation(api),
            observations=(
                _scheduler_observation(api, task_id="0"),
                _scheduler_observation(api, task_id="0"),
            ),
        )


def _write_cli_campaign(path: Path) -> Path:
    path.write_text(json.dumps({"campaign_spec": _spec_payload()}, sort_keys=True), encoding="utf-8")
    return path


def _run_campaign_module(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "bp_registry.campaigns.cli", *arguments],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )


def test_cli_preflight_and_plan_freeze_identity_before_any_execution(tmp_path: Path):
    """The public command rejects drift before it can write a run receipt."""
    campaign = _write_cli_campaign(tmp_path / "campaign.json")
    output_root = tmp_path / "campaign-output"

    preflight = _run_campaign_module(
        "preflight", "--campaign", str(campaign), "--campaign-root", str(ROOT),
        "--output-root", str(output_root),
    )

    assert preflight.returncode == 0, preflight.stderr
    payload = json.loads(preflight.stdout)
    assert payload["status"] == "ok"
    assert len(payload["campaign_spec_digest"]) == 64
    assert not output_root.exists()
