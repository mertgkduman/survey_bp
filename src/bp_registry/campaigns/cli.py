"""Strict, JSON-only lifecycle command for bounded campaign evidence.

The command deliberately owns only input validation, artifact publication, and
route selection.  Campaign identities, execution, shard verification, and
statistical reconstruction stay in the modules that define their scientific
contracts.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import math
from pathlib import Path, PurePosixPath
import sys
import tempfile
from typing import Any, Callable, Mapping

from pydantic import ValidationError

from ..manifests import preflight as preflight_manifest
from .contracts import CampaignSpecV1, CampaignWorkSpecV1, MaterializedPhysicalSampleV1, build_one_unit_plan, canonical_json_bytes
from .execution import (
    _build_look_merge_receipt, _deterministic_look_stop_receipt, _sealed_local_records,
    dispatch_finite_looks, run_canonical_work_plan, run_one_unit, verify_canonical_attempt,
)
from .planning import CampaignCoordinateV1, CampaignWorkPlan, freeze_campaign_work_spec, freeze_work_plan
from .shards import derive_resume_plan, merge_verified_attempts
from .reporting import reconstruct_campaign_report, verify_campaign_report, verify_campaign_routes
from .shards import reconstruct_fixed_shot, verify_shard
from .slurm import (
    SchedulerObservation,
    SlurmAllocation,
    build_sbatch_argv,
    execute_synthetic_slurm_array,
    parse_site_capabilities,
    select_array_shard,
)


_CLI_SCHEMA = "bp_registry_campaign_cli_v1"
_PLAN_SCHEMA = "campaign_cli_plan_v1"
_MERGE_SCHEMA = "campaign_cli_merge_v1"
_MAX_JSON_BYTES = 4 * 1024 * 1024


def _json_bytes(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("JSON input must be a regular non-symlink file")
    contents = path.read_bytes()
    if len(contents) > _MAX_JSON_BYTES:
        raise ValueError("JSON input exceeds the bounded CLI size")
    return contents


def _read_json(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    try:
        payload = json.loads(_json_bytes(path))
    except json.JSONDecodeError as error:
        raise ValueError("JSON input is malformed") from error
    if not isinstance(payload, dict):
        raise ValueError("JSON input must be an object")
    return payload


def _existing_root(value: str, *, name: str) -> Path:
    root = Path(value)
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"{name} must be an existing non-symlink directory")
    return root.resolve(strict=True)


def _confined_file(root: Path, relative_path: str, *, name: str) -> Path:
    path = PurePosixPath(relative_path)
    if not relative_path or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{name} must be a confined relative path")
    candidate = root.joinpath(*path.parts)
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{name} cannot traverse a symlink")
    if not candidate.is_file() or candidate.is_symlink():
        raise ValueError(f"{name} must identify a regular file")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError(f"{name} escapes its declared root")
    return resolved


def _output_root(value: str) -> Path:
    """Create only the explicitly named output root, rejecting symlink hops."""
    root = Path(value)
    if root.exists():
        if not root.is_dir() or root.is_symlink():
            raise ValueError("output_root must be a non-symlink directory")
        return root.resolve(strict=True)
    parent = root.parent
    if not parent.is_dir() or parent.is_symlink():
        raise ValueError("output_root parent must be an existing non-symlink directory")
    parent = parent.resolve(strict=True)
    target = parent / root.name
    target.mkdir(mode=0o700)
    return target.resolve(strict=True)


def _publish_json(path: Path, payload: Mapping[str, Any]) -> Path:
    contents = canonical_json_bytes(dict(payload)) + b"\n"
    if path.exists():
        if not path.is_file() or path.is_symlink() or path.read_bytes() != contents:
            raise ValueError("published campaign artifact conflicts with immutable bytes")
        return path
    descriptor, temporary_name = tempfile.mkstemp(prefix=".campaign-cli-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with open(descriptor, "wb", closefd=True) as handle:
            handle.write(contents)
            handle.flush()
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return path


def _validated_target_receipts(spec: CampaignSpecV1, value: object, campaign_root: Path) -> dict[str, str]:
    if spec.assessment is None or not isinstance(value, Mapping):
        raise ValueError("campaign launch requires target receipt paths for its frozen assessment")
    expected = {target.target_id: target.target_receipt_sha256 for target in spec.assessment.targets}
    if set(value) != set(expected) or any(not isinstance(path, str) for path in value.values()):
        raise ValueError("target receipt paths must cover each frozen assessment target exactly once")
    paths = {str(target_id): str(relative_path) for target_id, relative_path in value.items()}
    for target_id, relative_path in paths.items():
        receipt = _confined_file(campaign_root, relative_path, name="target receipt path")
        if sha256(receipt.read_bytes()).hexdigest() != expected[target_id]:
            raise ValueError("target receipt SHA-256 differs from frozen assessment")
    return dict(sorted(paths.items()))


def _campaign_spec(campaign_path: str, campaign_root: Path) -> tuple[CampaignSpecV1, dict[str, str]]:
    document = _read_json(campaign_path)
    permitted_fields = {"campaign_spec", "target_receipts", "operational_gate"}
    if set(document) not in ({"campaign_spec", "target_receipts"}, permitted_fields) or not isinstance(document["campaign_spec"], Mapping):
        raise ValueError("campaign document must contain campaign_spec and target_receipts")
    if "operational_gate" in document:
        _validate_operational_gate(document["operational_gate"], campaign_root)
    spec = CampaignSpecV1.model_validate(document["campaign_spec"])
    manifest = _confined_file(campaign_root, spec.inner_manifest_path, name="inner_manifest_path")
    if sha256(manifest.read_bytes()).hexdigest() != spec.inner_manifest_sha256:
        raise ValueError("inner manifest SHA-256 differs from frozen campaign specification")
    preflight_manifest(manifest)
    target_receipts = _validated_target_receipts(spec, document["target_receipts"], campaign_root)
    return spec, target_receipts


def _validate_operational_gate(value: object, campaign_root: Path) -> None:
    """Validate non-scientific Phase 8 gate metadata before any artifact write.

    The metadata names the additional fast/slow fixtures used by the bounded
    operational check.  It never enters a one-unit scientific digest, but it
    must be complete and content-bound so a preflight cannot silently switch
    the representative paths or declare a publication assessment.
    """
    if not isinstance(value, Mapping):
        raise ValueError("operational_gate must be an object")
    expected = {
        "schema", "label", "assessment_status", "physical_sample_identity",
        "preselected_sample_ids", "eligible_manifests", "synthetic_fixtures",
    }
    if set(value) != expected or value.get("schema") != "phase8_operational_gate_v1":
        raise ValueError("operational_gate has an invalid schema or field set")
    if value.get("label") != "development_fixture" or value.get("assessment_status") != "not_assessed":
        raise ValueError("operational_gate must remain a development_fixture and not_assessed")
    if not isinstance(value.get("physical_sample_identity"), str) or not value["physical_sample_identity"]:
        raise ValueError("operational_gate requires a shared physical sample identity")
    sample_ids = value.get("preselected_sample_ids")
    if not isinstance(sample_ids, list) or len(sample_ids) < 2 or any(type(item) is not int or item < 0 for item in sample_ids) or len(set(sample_ids)) != len(sample_ids):
        raise ValueError("operational_gate requires multiple unique preselected sample IDs")
    manifests = value.get("eligible_manifests")
    if not isinstance(manifests, Mapping) or set(manifests) != {"fast", "slow"}:
        raise ValueError("operational_gate requires fast and slow eligible manifests")
    for entry in manifests.values():
        if not isinstance(entry, list) or len(entry) != 2:
            raise ValueError("operational_gate manifest entries must be path/digest pairs")
        path_text, expected_sha = entry
        if not isinstance(path_text, str) or not isinstance(expected_sha, str):
            raise ValueError("operational_gate manifest entries must be path/digest pairs")
        path = _confined_file(campaign_root, path_text, name="operational_gate manifest")
        if sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise ValueError("operational_gate manifest SHA-256 differs from frozen metadata")
        preflight_manifest(path)
    fixtures = value.get("synthetic_fixtures")
    if not isinstance(fixtures, Mapping) or set(fixtures) != {"fixed_shot", "finite_look_post_decision_crash"}:
        raise ValueError("operational_gate requires fixed-shot and finite-look crash fixtures")
    fixed = fixtures["fixed_shot"]
    finite = fixtures["finite_look_post_decision_crash"]
    if not isinstance(fixed, Mapping) or fixed.get("mode") != "fixed_shot":
        raise ValueError("operational_gate fixed-shot fixture is invalid")
    if not isinstance(finite, Mapping) or finite.get("mode") != "finite_look" or finite.get("fault") != "after_decision_before_receipt_publication":
        raise ValueError("operational_gate finite-look crash fixture is invalid")


def _plan_payload(spec: CampaignSpecV1, target_receipts: Mapping[str, str]) -> dict[str, Any]:
    plan = build_one_unit_plan(spec)
    return {
        "schema": _PLAN_SCHEMA,
        "campaign_spec": spec.model_dump(mode="json", by_alias=True),
        "target_receipts": dict(sorted(target_receipts.items())),
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "unit_key": plan.unit_key,
        "shard_id": plan.shard_id,
        "assessment_digest": spec.assessment.digest() if spec.assessment is not None else None,
    }


def _load_plan(plan_path: str, campaign_root: Path) -> tuple[CampaignSpecV1, dict[str, Any]]:
    payload = _read_json(plan_path)
    expected_fields = {
        "schema", "campaign_spec", "target_receipts", "campaign_spec_digest", "campaign_plan_digest", "unit_key", "shard_id", "assessment_digest",
    }
    if set(payload) != expected_fields or payload.get("schema") != _PLAN_SCHEMA:
        raise ValueError("campaign plan has an invalid schema or field set")
    if not isinstance(payload.get("campaign_spec"), Mapping):
        raise ValueError("campaign plan lacks its frozen campaign specification")
    spec = CampaignSpecV1.model_validate(payload["campaign_spec"])
    target_receipts = _campaign_spec_from_frozen(spec, campaign_root, payload.get("target_receipts"))
    expected = _plan_payload(spec, target_receipts)
    if payload != expected:
        raise ValueError("campaign plan differs from its frozen scientific identities")
    return spec, payload


def _campaign_spec_from_frozen(spec: CampaignSpecV1, campaign_root: Path, target_receipts: object) -> dict[str, str]:
    manifest = _confined_file(campaign_root, spec.inner_manifest_path, name="inner_manifest_path")
    if sha256(manifest.read_bytes()).hexdigest() != spec.inner_manifest_sha256:
        raise ValueError("inner manifest SHA-256 differs from frozen campaign specification")
    preflight_manifest(manifest)
    return _validated_target_receipts(spec, target_receipts, campaign_root)


def _artifact(*, status: str, plan: Mapping[str, Any], **values: Any) -> dict[str, Any]:
    return {
        "schema": _CLI_SCHEMA,
        "status": status,
        "campaign_spec_digest": plan["campaign_spec_digest"],
        "campaign_plan_digest": plan["campaign_plan_digest"],
        "assessment_digest": plan["assessment_digest"],
        **values,
    }


def _work_document(campaign_path: str, root: Path) -> CampaignWorkSpecV1:
    document = _read_json(campaign_path)
    if set(document) != {"campaign_work_spec"} or not isinstance(document["campaign_work_spec"], Mapping):
        raise ValueError("paired campaign document must contain exactly campaign_work_spec")
    spec = CampaignWorkSpecV1.model_validate(document["campaign_work_spec"])
    # This is intentionally a no-write preflight.  The executor repeats it
    # before sampling so no plan artifact can authorize input drift.
    from .execution import _preflight_work_arms
    _preflight_work_arms(spec, root)
    return spec


def _work_plan_payload(spec: CampaignWorkSpecV1) -> dict[str, Any]:
    plan = freeze_campaign_work_spec(spec)
    return {
        "schema": "campaign_work_plan_v1",
        "campaign_work_spec": spec.model_dump(mode="json", by_alias=True),
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "assessment_digest": spec.assessment.digest(),
        "units": [unit.payload() for unit in plan.units],
        "shards": [shard.payload() for shard in plan.shards],
        "look_sample_boundaries": list(plan.look_boundaries),
    }


def _load_work_plan(plan_path: str, root: Path) -> tuple[CampaignWorkSpecV1, CampaignWorkPlan, dict[str, Any]]:
    payload = _read_json(plan_path)
    required = {"schema", "campaign_work_spec", "campaign_spec_digest", "campaign_plan_digest", "assessment_digest", "units", "shards", "look_sample_boundaries"}
    if set(payload) != required or payload.get("schema") != "campaign_work_plan_v1" or not isinstance(payload.get("campaign_work_spec"), Mapping):
        raise ValueError("paired campaign plan has an invalid schema or field set")
    spec = CampaignWorkSpecV1.model_validate(payload["campaign_work_spec"])
    expected = _work_plan_payload(spec)
    if payload != expected:
        raise ValueError("paired campaign plan differs from its frozen scientific inputs")
    from .execution import _preflight_work_arms
    _preflight_work_arms(spec, root)
    return spec, freeze_campaign_work_spec(spec), payload


def _paired_run(
    args: argparse.Namespace, *, root: Path, output: Path,
    shards: tuple[Any, ...] | None = None,
    allocation: SlurmAllocation | None = None,
    observation: SchedulerObservation | None = None,
) -> dict[str, Any]:
    _spec, plan, payload = _load_work_plan(args.plan, root)
    selected = plan.shards if shards is None else tuple(shards)
    if observation is not None and observation.state != "COMPLETED":
        serializable = {
            "schema": "campaign_paired_shard_run_v1", "campaign_spec_digest": plan.campaign_spec_digest,
            "campaign_plan_digest": plan.campaign_plan_digest, "selected_shard_id": selected[0].shard_id,
            "attempts": [], "materialized_sample_sha256s": [], "physical_error_sha256s": [],
            "incomplete_unit_keys": list(selected[0].unit_keys),
            "executor_receipt": {"requested_allocation": allocation.payload(), "scheduler": observation.payload()},
        }
    else:
        execution = run_canonical_work_plan(plan, campaign_root=root, output_root=output, shards=selected)
        serializable = {
            "schema": "campaign_paired_run_v1" if shards is None else "campaign_paired_shard_run_v1",
            "campaign_spec_digest": plan.campaign_spec_digest,
            "campaign_plan_digest": plan.campaign_plan_digest,
            "attempts": list(execution["verified_attempts"]),
            "materialized_sample_sha256s": [item.materialized_sample_sha256 for item in execution["materialized_samples"]],
            "physical_error_sha256s": [item.physical_error_sha256 for item in execution["materialized_samples"]],
        }
        if shards is not None:
            serializable.update({
                "selected_shard_id": selected[0].shard_id,
                "incomplete_unit_keys": [],
                "executor_receipt": {"requested_allocation": allocation.payload(), "scheduler": observation.payload()},
            })
    artifact = _publish_json(output / ("paired-run.json" if shards is None else "paired-shard-run.json"), serializable)
    attempts = serializable["attempts"]
    return _artifact(status="ok", plan=payload, phase="run_local" if shards is None else "run_shard",
                     executor_route="local" if shards is None else "slurm",
                     artifact_path=str(artifact), artifact_sha256=sha256(artifact.read_bytes()).hexdigest(),
                     unit_count=len(plan.units) if shards is None else len(selected[0].unit_keys),
                     shard_count=len(plan.shards) if shards is None else 1,
                     terminal_unit_keys=[item["unit_key"] for item in attempts],
                     incomplete_unit_keys=serializable.get("incomplete_unit_keys", []),
                     materialized_sample_sha256s=serializable["materialized_sample_sha256s"],
                     physical_error_sha256s=serializable["physical_error_sha256s"])


def _paired_attempts(receipt_path: str, *, plan: CampaignWorkPlan) -> tuple[dict[str, Any], ...]:
    payload = _read_json(receipt_path)
    required = {"schema", "campaign_spec_digest", "campaign_plan_digest", "attempts", "materialized_sample_sha256s", "physical_error_sha256s"}
    shard_required = required | {"selected_shard_id", "incomplete_unit_keys", "executor_receipt"}
    if frozenset(payload) not in {frozenset(required), frozenset(shard_required)} or payload.get("schema") not in {"campaign_paired_run_v1", "campaign_paired_shard_run_v1"}:
        raise ValueError("paired run artifact has an invalid schema or field set")
    if payload["campaign_spec_digest"] != plan.campaign_spec_digest or payload["campaign_plan_digest"] != plan.campaign_plan_digest:
        raise ValueError("paired run artifact differs from the frozen plan")
    attempts = payload.get("attempts")
    if not isinstance(attempts, list):
        raise ValueError("paired run artifact lacks attempts")
    return tuple(verify_canonical_attempt(record=item, plan=plan) for item in attempts)


def _route_neutral_trace(events: object) -> bytes:
    """Remove only canonical profiler observations from a semantic event trace."""
    if not isinstance(events, list):
        raise ValueError("mixed-route delivery requires canonical event records")
    trace = []
    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("mixed-route delivery requires canonical event mappings")
        retained = dict(event)
        retained.pop("event_id", None)  # event IDs hash the excluded profiler values.
        data = retained.get("data")
        if not isinstance(data, Mapping):
            raise ValueError("mixed-route delivery event lacks canonical data")
        semantic_data = dict(data)
        # The runner records process timing/RSS beneath these keys.  They are
        # executor observations; every other canonical field remains exact.
        for observation in ("profile", "decode_runtime", "setup_runtime"):
            semantic_data.pop(observation, None)
        retained["data"] = semantic_data
        trace.append(retained)
    return canonical_json_bytes(trace)


def _route_neutral_attempts(
    attempts: tuple[dict[str, Any], ...], *, plan: CampaignWorkPlan,
) -> tuple[dict[str, Any], ...]:
    """Collapse equivalent cross-route delivery before the lineage reducer.

    Paths and scheduler observations identify delivery, never the scientific
    attempt.  A second delivery is accepted only when its sealed canonical
    facts, materialized bytes, and selected frozen shard exactly agree.
    """
    by_unit: dict[str, list[dict[str, Any]]] = {}
    for record in attempts:
        by_unit.setdefault(str(record["unit_key"]), []).append(record)
    selected: list[dict[str, Any]] = []
    fields = (
        "campaign_spec_digest", "campaign_plan_digest", "unit_key", "selected_shard_id",
        "arm_manifest_sha256", "materialized_sample_sha256", "physical_error_sha256",
        "terminal_bytes_sha256", "terminal_fact", "work_vector",
    )
    for unit in plan.units:
        records = by_unit.get(unit.key, [])
        if not records:
            continue
        reference = canonical_json_bytes({field: records[0][field] for field in fields})
        reference_trace = _route_neutral_trace(records[0]["events"])
        if any(
            canonical_json_bytes({field: record[field] for field in fields}) != reference
            or _route_neutral_trace(record["events"]) != reference_trace
            for record in records[1:]
        ):
            raise ValueError("mixed-route delivery has conflicting canonical terminal evidence")
        selected.append(min(records, key=lambda record: str(record["receipt_sha256"])))
    return tuple(selected)


def _materialized_sample_index(attempts: tuple[dict[str, Any], ...]) -> dict[str, dict[str, Any]]:
    """Re-read every retained sample artifact into a deterministic evidence index."""
    by_identity: dict[str, dict[str, Any]] = {}
    for record in attempts:
        sample_path = Path(record["materialized_sample_path"])
        if sample_path.is_symlink() or not sample_path.is_file():
            raise ValueError("paired merge materialized sample must be a regular file")
        artifact = MaterializedPhysicalSampleV1.model_validate_json(sample_path.read_bytes())
        if (artifact.materialized_sample_sha256 != record["materialized_sample_sha256"]
                or artifact.physical_error_sha256 != record["physical_error_sha256"]):
            raise ValueError("paired merge materialized sample differs from verified attempt")
        entry = by_identity.setdefault(artifact.physical_sample_identity, {
            "physical_sample_identity": artifact.physical_sample_identity,
            "materialized_sample_sha256": artifact.materialized_sample_sha256,
            "physical_error_sha256": artifact.physical_error_sha256,
            "cohort_id": artifact.cohort_id,
            "point_id": artifact.point_id,
            "sample_namespace": artifact.sample_namespace,
            "sample_id": artifact.sample_id,
            "paths": [],
        })
        if (entry["materialized_sample_sha256"] != artifact.materialized_sample_sha256
                or entry["physical_error_sha256"] != artifact.physical_error_sha256):
            raise ValueError("paired merge physical identity has conflicting materialized bytes")
        entry["paths"].append(str(sample_path.resolve(strict=True)))
    return {
        identity: {**entry, "paths": sorted(set(entry["paths"]))}
        for identity, entry in sorted(by_identity.items())
    }


def _load_indexed_materialized_samples(
    index: Mapping[str, Any], *, artifact_roots: tuple[Path, ...],
) -> dict[str, MaterializedPhysicalSampleV1]:
    """Rehydrate typed samples from the independently checked merge descriptors."""
    if not isinstance(index, Mapping) or not index:
        raise ValueError("paired merge artifact lacks materialized sample descriptors")
    samples: dict[str, MaterializedPhysicalSampleV1] = {}
    required = {
        "physical_sample_identity", "materialized_sample_sha256", "physical_error_sha256",
        "cohort_id", "point_id", "sample_namespace", "sample_id", "paths",
    }
    for identity, descriptor in index.items():
        if not isinstance(identity, str) or not isinstance(descriptor, Mapping) or set(descriptor) != required:
            raise ValueError("paired merge materialized sample descriptor has an invalid field set")
        paths = descriptor["paths"]
        if not isinstance(paths, list) or not paths or any(not isinstance(path, str) for path in paths):
            raise ValueError("paired merge materialized sample descriptor lacks paths")
        loaded: list[MaterializedPhysicalSampleV1] = []
        for raw_path in paths:
            path = Path(raw_path)
            if (path.is_symlink() or not path.is_file()
                    or not any(path.resolve(strict=True).is_relative_to(root) for root in artifact_roots)):
                raise ValueError("paired merge materialized sample path is unavailable")
            artifact = MaterializedPhysicalSampleV1.model_validate_json(path.read_bytes())
            if any(getattr(artifact, name) != descriptor[name] for name in required - {"paths"}):
                raise ValueError("paired merge materialized sample descriptor differs from retained bytes")
            loaded.append(artifact)
        if any(item.primitive_bytes() != loaded[0].primitive_bytes() for item in loaded[1:]):
            raise ValueError("paired merge materialized sample paths differ for one physical identity")
        if identity != loaded[0].physical_sample_identity:
            raise ValueError("paired merge materialized sample index key differs from retained identity")
        samples[identity] = loaded[0]
    return samples


def _paired_merge(args: argparse.Namespace, *, root: Path, plan: CampaignWorkPlan, payload: Mapping[str, Any]) -> dict[str, Any]:
    artifact_index = []
    attempts = []
    for receipt in args.receipt:
        receipt_path = Path(receipt).resolve(strict=True)
        artifact_index.append({"path": str(receipt_path), "sha256": sha256(receipt_path.read_bytes()).hexdigest()})
        attempts.extend(_paired_attempts(str(receipt_path), plan=plan))
    all_attempts = tuple(attempts)
    merged = merge_verified_attempts(plan=plan, verified_attempts=_route_neutral_attempts(all_attempts, plan=plan))
    persisted = {key: value for key, value in merged.items() if key != "receipt_bytes"}
    envelope = {
        "schema": "campaign_paired_merge_envelope_v1",
        "canonical_merge": persisted,
        "verified_attempts": list(all_attempts),
        "attempt_artifacts": sorted(artifact_index, key=lambda item: (item["path"], item["sha256"])),
        "materialized_samples_by_identity": _materialized_sample_index(all_attempts),
    }
    output = _output_root(args.output_root)
    artifact = _publish_json(output / "campaign-paired-merge.json", envelope)
    return _artifact(status="ok", plan=payload, phase="merge", artifact_path=str(artifact),
                     artifact_sha256=sha256(artifact.read_bytes()).hexdigest(), member_count=len(all_attempts))


def _paired_merge_payload(path: str, *, plan: CampaignWorkPlan) -> dict[str, Any]:
    payload = _read_json(path)
    required = {"schema", "canonical_merge", "verified_attempts", "attempt_artifacts", "materialized_samples_by_identity"}
    if set(payload) != required or payload.get("schema") != "campaign_paired_merge_envelope_v1":
        raise ValueError("paired merge artifact has an invalid envelope")
    attempts = payload["verified_attempts"]
    if not isinstance(attempts, list):
        raise ValueError("paired merge artifact lacks independently verified attempts")
    verified = tuple(verify_canonical_attempt(record=item, plan=plan) for item in attempts)
    reduced_attempts = _route_neutral_attempts(verified, plan=plan)
    full = merge_verified_attempts(plan=plan, verified_attempts=reduced_attempts)
    expected = {key: value for key, value in full.items() if key != "receipt_bytes"}
    artifacts = payload["attempt_artifacts"]
    if (not isinstance(artifacts, list) or not artifacts
            or any(not isinstance(item, Mapping) or set(item) != {"path", "sha256"} for item in artifacts)):
        raise ValueError("paired merge artifact lacks bounded attempt indexes")
    for item in artifacts:
        receipt = Path(str(item["path"]))
        if receipt.is_symlink() or not receipt.is_file() or sha256(receipt.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("paired merge artifact input receipt index differs from retained bytes")
    artifact_roots = tuple(
        Path(str(item["path"])).resolve(strict=True).parent for item in artifacts
    )
    indexed_samples = _load_indexed_materialized_samples(
        payload["materialized_samples_by_identity"], artifact_roots=artifact_roots,
    )
    if (payload["canonical_merge"] != expected
            or payload["attempt_artifacts"] != sorted((dict(item) for item in artifacts), key=lambda item: (str(item["path"]), str(item["sha256"])))
            or payload["materialized_samples_by_identity"] != _materialized_sample_index(verified)):
        raise ValueError("paired merge artifact differs from verified attempt reduction")
    return {**full, "verified_attempts": reduced_attempts,
            "materialized_samples_by_identity": indexed_samples}


def _paired_report_inputs(
    *, plan: CampaignWorkPlan, spec: CampaignWorkSpecV1, merged: Mapping[str, Any],
) -> dict[str, Any]:
    """Build report inputs only from the independently verified merge envelope."""
    if spec.assessment is None:
        raise ValueError("paired report requires a frozen assessment")
    receipt = {
        key: value for key, value in merged.items()
        if key not in {"verified_attempts", "materialized_samples_by_identity"}
    }
    attempts = merged.get("verified_attempts")
    if not isinstance(attempts, tuple):
        raise ValueError("paired report requires reverified terminal attempts")
    return {
        "plan": plan,
        "assessment": spec.assessment,
        "merge_receipt": receipt,
        "input_receipt_hashes": {
            "campaign": plan.campaign_spec_digest,
            "plan": plan.campaign_plan_digest,
            "assessment": spec.assessment.digest(),
            "merge": receipt["receipt_sha256"],
            **{f"target:{item.target_id}": item.target_receipt_sha256 for item in spec.assessment.targets},
        },
        "source_denominator_required_by_target": spec.source_denominator_required_by_target,
        "source_denominators": spec.source_denominators,
        "target_arm_ids": spec.target_arm_ids,
        "materialized_samples_by_identity": merged["materialized_samples_by_identity"],
        "work_vectors_by_unit": {item["unit_key"]: item["work_vector"] for item in attempts},
        # Canonical attempt ledgers presently expose no report allowlisted
        # executor observations.  The reporting contract records this typed
        # missingness instead of manufacturing host or scheduler values.
        "observations": {},
    }


def _verify_paired_report(
    *, report_path: str, plan: CampaignWorkPlan, spec: CampaignWorkSpecV1, merged: Mapping[str, Any],
) -> tuple[Any, str]:
    """Reconstruct a retained report before accepting any of its cache bytes."""
    report_file = Path(report_path)
    retained = _read_json(report_path)
    expected = reconstruct_campaign_report(**_paired_report_inputs(plan=plan, spec=spec, merged=merged))
    expected_payload = asdict(expected)
    expected_bytes = canonical_json_bytes(expected_payload) + b"\n"
    if _json_bytes(report_file) != expected_bytes or canonical_json_bytes(retained) != canonical_json_bytes(expected_payload):
        raise ValueError("retained campaign report differs from independent reconstruction")
    # The byte check binds the persisted cache; this delegated check keeps the
    # public report-verification contract exercised on every installed replay.
    verify_campaign_report(report=expected, **_paired_report_inputs(plan=plan, spec=spec, merged=merged))
    return expected, sha256(expected_bytes).hexdigest()


def _paired_scientific_identity(plan: CampaignWorkPlan) -> dict[str, str]:
    """Construct the complete route-independent identity required for retry reduction."""
    spec = plan.work_spec
    if not isinstance(spec, CampaignWorkSpecV1):
        raise ValueError("paired resume requires a frozen paired work specification")
    return {
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "source_lock_sha256": spec.source_lock_sha256,
        "environment_lock_sha256": spec.environment_lock_sha256,
        "dependency_lock_sha256": spec.dependency_lock_sha256,
        "sample_namespace_digest": sha256(canonical_json_bytes({
            "namespace": spec.shared_sampler.physical_sample_namespace,
            "sampler_contract_sha256": spec.shared_sampler.digest(),
        })).hexdigest(),
        "stopping_rule_digest": sha256(canonical_json_bytes(
            spec.assessment.stopping.model_dump(mode="json")
        )).hexdigest(),
        "assessment_digest": spec.assessment.digest(),
    }


def _paired_resume_decision(*, look: int, terminal_records: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """A fixed-shot campaign has no early-stop decision to reconstruct.

    Finite-look campaigns are reduced by the shared statistical entry point
    before publication.  Returning false here keeps their later units blocked
    until that evidence is provided, rather than inventing a stop decision.
    """
    digest = sha256(canonical_json_bytes({"look": look, "terminal_records": terminal_records})).hexdigest()
    return {
        "decision_input_hashes": [digest], "decision_result": {"look": look},
        "stop_reason": "no_cli_stop_decision", "should_stop": False,
    }


def _preflight(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    # Validate the explicit future root but leave it absent: preflight never writes.
    output = Path(args.output_root)
    if output.exists() and (not output.is_dir() or output.is_symlink()):
        raise ValueError("output_root must be a non-symlink directory when it exists")
    if not output.exists() and (not output.parent.is_dir() or output.parent.is_symlink()):
        raise ValueError("output_root parent must be an existing non-symlink directory")
    spec, target_receipts = _campaign_spec(args.campaign, root)
    return _artifact(status="ok", plan=_plan_payload(spec, target_receipts), phase="preflight", sampling_performed=False)


def _plan(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    document = _read_json(args.campaign)
    if "campaign_work_spec" in document:
        spec = _work_document(args.campaign, root)
        payload = _work_plan_payload(spec)
        output = _output_root(args.output_root)
        artifact = _publish_json(output / "campaign-work-plan.json", payload)
        return _artifact(status="ok", plan=payload, phase="plan", artifact_path=str(artifact),
                         artifact_sha256=sha256(artifact.read_bytes()).hexdigest(),
                         unit_count=len(payload["units"]), shard_count=len(payload["shards"]))
    spec, target_receipts = _campaign_spec(args.campaign, root)
    payload = _plan_payload(spec, target_receipts)
    output = _output_root(args.output_root)
    artifact = _publish_json(output / "campaign-plan.json", payload)
    return _artifact(status="ok", plan=payload, phase="plan", artifact_path=str(artifact), artifact_sha256=sha256(artifact.read_bytes()).hexdigest())


def _run(args: argparse.Namespace, *, route: str) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    if _read_json(args.plan).get("schema") == "campaign_work_plan_v1":
        if route == "local":
            return _paired_run(args, root=root, output=_output_root(args.output_root))
        if args.allocation is None or args.scheduler_observation is None:
            raise ValueError("paired run-shard requires allocation and scheduler observation receipts")
        _spec, work_plan, _payload = _load_work_plan(args.plan, root)
        shard = select_array_shard(work_plan, args.array_task_id)
        allocation = SlurmAllocation(**_read_json(args.allocation))
        observation = SchedulerObservation(**_read_json(args.scheduler_observation))
        if observation.task_id != args.array_task_id or observation.allocated_cpus > allocation.cpus_per_task:
            raise ValueError("scheduler observation differs from the bounded selected allocation")
        return _paired_run(args, root=root, output=_output_root(args.output_root), shards=(shard,),
                           allocation=allocation, observation=observation)
    spec, plan = _load_plan(args.plan, root)
    if route == "slurm" and args.array_task_id != "0":
        raise ValueError("one-unit campaign plans expose only frozen Slurm array task 0")
    output = _output_root(args.output_root)
    run = run_one_unit(spec, campaign_root=root, output_root=output, worker_label=route)
    return _artifact(
        status="ok", plan=plan, phase="run_shard" if route == "slurm" else "run_local",
        executor_route=route, receipt_path=run["receipt_path"], receipt_sha256=sha256(Path(run["receipt_path"]).read_bytes()).hexdigest(),
        unit_key=run["unit_key"], shard_id=run["shard_id"], terminal_fact=run["terminal_fact"],
    )


def _verify(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    if args.report is not None:
        if args.plan is None or args.merge is None:
            raise ValueError("report verification requires --plan and --merge")
        spec, plan, payload = _load_work_plan(args.plan, root)
        merged = _paired_merge_payload(args.merge, plan=plan)
        report, artifact_sha = _verify_paired_report(
            report_path=args.report, plan=plan, spec=spec, merged=merged,
        )
        return _artifact(status="ok", plan=payload, phase="verify", verified=True,
                         report_path=str(Path(args.report).resolve()), report_sha256=report.report_sha256,
                         report_artifact_sha256=artifact_sha,
                         merge_receipt_sha256=report.merge_receipt_sha256)
    if args.plan is not None and _read_json(args.plan).get("schema") == "campaign_work_plan_v1":
        _spec, plan, payload = _load_work_plan(args.plan, root)
        attempts = _paired_attempts(args.receipt, plan=plan)
        return _artifact(status="ok", plan=payload, phase="verify", verified=True,
                         receipt_path=str(Path(args.receipt).resolve()),
                         receipt_sha256=sha256(Path(args.receipt).read_bytes()).hexdigest(),
                         verified_attempt_count=len(attempts))
    receipt = Path(args.receipt)
    checked = verify_shard(receipt, campaign_root=root)
    report = reconstruct_fixed_shot(checked)
    spec = CampaignSpecV1.model_validate(checked["campaign_spec"])
    plan = {
        "campaign_spec_digest": checked["campaign_spec_digest"],
        "campaign_plan_digest": checked["campaign_plan_digest"],
        "assessment_digest": spec.assessment.digest() if spec.assessment else None,
    }
    return _artifact(status="ok", plan=plan, phase="verify", verified=True, receipt_path=str(receipt.resolve()),
                     receipt_sha256=sha256(receipt.read_bytes()).hexdigest(), report=report)


def _verify_routes(args: argparse.Namespace) -> dict[str, Any]:
    """Replay both route chains, then publish an input-bound equivalence receipt."""
    root = _existing_root(args.campaign_root, name="campaign_root")
    spec, plan, payload = _load_work_plan(args.plan, root)
    local_merged = _paired_merge_payload(args.local_merge, plan=plan)
    slurm_merged = _paired_merge_payload(args.slurm_merge, plan=plan)
    local_report, local_report_artifact_sha = _verify_paired_report(
        report_path=args.local_report, plan=plan, spec=spec, merged=local_merged,
    )
    slurm_report, slurm_report_artifact_sha = _verify_paired_report(
        report_path=args.slurm_report, plan=plan, spec=spec, merged=slurm_merged,
    )
    compared = verify_campaign_routes(
        local_report=local_report, slurm_report=slurm_report,
        local_merge_receipt=local_merged, slurm_merge_receipt=slurm_merged,
    )
    output_path = Path(args.output)
    output_parent = _existing_root(str(output_path.parent), name="route receipt output parent")
    if not output_path.name:
        raise ValueError("route receipt output must name a file")
    artifact = _publish_json(output_parent / output_path.name, {
        **compared,
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "local": {
            "merge_sha256": sha256(_json_bytes(Path(args.local_merge))).hexdigest(),
            "report_sha256": local_report.report_sha256,
            "report_artifact_sha256": local_report_artifact_sha,
        },
        "slurm": {
            "merge_sha256": sha256(_json_bytes(Path(args.slurm_merge))).hexdigest(),
            "report_sha256": slurm_report.report_sha256,
            "report_artifact_sha256": slurm_report_artifact_sha,
        },
    })
    return _artifact(status="ok", plan=payload, phase="verify_routes", verified=True,
                     scientific_records_match=True, artifact_path=str(artifact),
                     artifact_sha256=sha256(artifact.read_bytes()).hexdigest())


def _verify_operational_gate(args: argparse.Namespace) -> dict[str, Any]:
    """Verify the retained Phase 8 bounded-gate bundle without rerunning it."""
    if not isinstance(args.output, str) or not args.output:
        raise ValueError("operational gate verify requires --output")
    root = _existing_root(args.campaign_root, name="campaign_root")
    spec, target_receipts = _campaign_spec(args.campaign, root)
    output = _existing_root(args.output, name="output")
    required = {
        "campaign-seal.json", "scheduler-capability.json", "merge-receipt.json",
        "assessment.json", "profiling-authorization.json", "finite-look-recovery.json",
    }
    paths = {name: _confined_file(output, name, name="operational gate receipt") for name in required}
    expected_plan = _plan_payload(spec, target_receipts)
    if _read_json(str(paths["campaign-seal.json"])) != expected_plan:
        raise ValueError("operational gate campaign seal differs from frozen campaign inputs")
    local_receipts = tuple(sorted(output.glob("local/shard-*/receipt.json")))
    if len(local_receipts) != 1:
        raise ValueError("operational gate requires exactly one retained local tracer receipt")
    checked = verify_shard(local_receipts[0], campaign_root=root)
    if checked["campaign_plan_digest"] != expected_plan["campaign_plan_digest"]:
        raise ValueError("operational gate local receipt differs from campaign seal")
    merged = _read_json(str(paths["merge-receipt.json"]))
    if merged.get("campaign_plan_digest") != expected_plan["campaign_plan_digest"]:
        raise ValueError("operational gate merge differs from campaign seal")
    assessment = _read_json(str(paths["assessment.json"]))
    if assessment.get("assessment_status") != "evidence_reconstructed":
        raise ValueError("operational gate assessment was not evidence reconstructed")
    finite = _read_json(str(paths["finite-look-recovery.json"]))
    if finite.get("recovered_stop_receipt") is not True or finite.get("next_look_submissions") != 0 or finite.get("pre_crash_receipt_sha256s") != finite.get("post_crash_receipt_sha256s"):
        raise ValueError("operational gate finite-look recovery proof is incomplete")
    campaign_document = _read_json(args.campaign)
    gate = campaign_document.get("operational_gate")
    if not isinstance(gate, Mapping):
        raise ValueError("operational gate metadata is missing")
    work_plan = _operational_work_plan(spec, root, gate)
    finite_root = _existing_root(output / "finite-look", name="finite-look evidence")
    actual_hashes = _finite_evidence_hashes(finite_root)
    if (finite.get("campaign_spec_digest") != work_plan.campaign_spec_digest
            or finite.get("campaign_plan_digest") != work_plan.campaign_plan_digest
            or actual_hashes != finite["pre_crash_receipt_sha256s"]
            or "look-1-merge-receipt.json" not in actual_hashes):
        raise ValueError("operational gate finite-look evidence differs from frozen plan")
    records = _sealed_local_records(finite_root)
    terminals = tuple(record for record in records if record["state"] == "sealed_terminal")
    prefix = work_plan.completed_prefix(1)
    if {record["unit_key"] for record in terminals} != set(prefix):
        raise ValueError("operational gate finite-look terminal set differs from completed boundary")
    expected_merge = _build_look_merge_receipt(
        plan=work_plan, look=1, terminal_records=terminals, root=finite_root,
    )
    merge_file = _confined_file(finite_root, "look-1-merge-receipt.json", name="finite-look merge")
    if merge_file.read_bytes() != canonical_json_bytes(expected_merge) + b"\n":
        raise ValueError("operational gate finite-look merge differs from sealed units")
    terminal_by_key = {record["unit_key"]: record for record in terminals}
    decision = _operational_stop_decision(
        look=1, terminal_records=tuple(terminal_by_key[key]["scientific"]["terminal_fact"] for key in prefix),
    )
    expected_stop = _deterministic_look_stop_receipt(
        plan=work_plan, look=1, terminal_records=terminals, decision=decision,
        merge_receipt_sha256=sha256(merge_file.read_bytes()).hexdigest(),
    )
    stop_file = _confined_file(finite_root, "look-stop-receipt.json", name="finite-look stop")
    if stop_file.read_bytes() != canonical_json_bytes(expected_stop) + b"\n":
        raise ValueError("operational gate finite-look stop differs from reconstructed merge and decision")
    scheduler = _read_json(str(paths["scheduler-capability.json"]))
    capabilities = scheduler.get("capabilities")
    if not isinstance(capabilities, Mapping) or capabilities.get("accounting_available", {}).get("value") is not None:
        raise ValueError("operational gate scheduler receipt is not an unavailable-site observation")
    authorization = _read_json(str(paths["profiling-authorization.json"]))
    if authorization.get("decision") != "deny" or authorization.get("assessment_status") != "not_assessed":
        raise ValueError("operational gate must retain a not-assessed production denial")
    receipt_hashes = {name: sha256(path.read_bytes()).hexdigest() for name, path in sorted(paths.items())}
    return _artifact(
        status="ok", plan=expected_plan, phase="verify_operational_gate", verified=True,
        retained_receipt_sha256s=receipt_hashes, production_authorization="deny",
        recovered_stop_receipt=True, next_look_submissions=0,
    )


def _merge(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    if args.plan is not None and _read_json(args.plan).get("schema") == "campaign_work_plan_v1":
        _spec, plan, payload = _load_work_plan(args.plan, root)
        return _paired_merge(args, root=root, plan=plan, payload=payload)
    if not args.receipt:
        raise ValueError("merge requires at least one preserved receipt")
    members = []
    for receipt_text in args.receipt:
        receipt = Path(receipt_text)
        checked = verify_shard(receipt, campaign_root=root)
        members.append({
            "receipt_path": str(receipt.resolve()), "receipt_sha256": sha256(receipt.read_bytes()).hexdigest(),
            "campaign_spec_digest": checked["campaign_spec_digest"], "campaign_plan_digest": checked["campaign_plan_digest"],
            "unit_key": checked["unit_key"], "report": reconstruct_fixed_shot(checked),
        })
    identity = {(member["campaign_spec_digest"], member["campaign_plan_digest"]) for member in members}
    if len(identity) != 1 or len({member["unit_key"] for member in members}) != len(members):
        raise ValueError("merge requires unique receipts for exactly one frozen campaign")
    spec_digest, plan_digest = identity.pop()
    payload = _canonical_merge_payload(spec_digest=spec_digest, plan_digest=plan_digest, members=members)
    output = _output_root(args.output_root)
    artifact = _publish_json(output / "campaign-merge.json", payload)
    return {"schema": _CLI_SCHEMA, "status": "ok", "phase": "merge", "campaign_spec_digest": spec_digest,
            "campaign_plan_digest": plan_digest, "artifact_path": str(artifact),
            "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(), "member_count": len(members)}


def _canonical_merge_payload(
    *, spec_digest: str, plan_digest: str, members: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return the canonical merge and a hash over its non-recursive content."""
    unsigned = {
        "schema": _MERGE_SCHEMA,
        "campaign_spec_digest": spec_digest,
        "campaign_plan_digest": plan_digest,
        "members": sorted(members, key=lambda item: str(item["unit_key"])),
    }
    return {
        **unsigned,
        "merge_content_sha256": sha256(canonical_json_bytes(unsigned)).hexdigest(),
    }


def _verified_merge(merge_path: str, campaign_root: Path) -> dict[str, Any]:
    """Rebuild a merge receipt from verified immutable shard bytes.

    Merge JSON is a cache of a canonical reduction, never evidence by itself.
    Every consumer re-verifies the referenced shard and requires byte-for-byte
    equality with the reduction it reconstructs.
    """
    merge_file = Path(merge_path)
    payload = _read_json(merge_path)
    expected_fields = {
        "schema", "campaign_spec_digest", "campaign_plan_digest", "members", "merge_content_sha256",
    }
    if set(payload) != expected_fields or payload.get("schema") != _MERGE_SCHEMA:
        raise ValueError("merge receipt has an invalid schema or field set")
    raw_members = payload.get("members")
    if not isinstance(raw_members, list) or not raw_members:
        raise ValueError("merge receipt requires nonempty members")
    members: list[dict[str, Any]] = []
    for member in raw_members:
        expected_member_fields = {
            "receipt_path", "receipt_sha256", "campaign_spec_digest",
            "campaign_plan_digest", "unit_key", "report",
        }
        if not isinstance(member, Mapping) or set(member) != expected_member_fields:
            raise ValueError("merge receipt member has an invalid field set")
        receipt_path = Path(str(member["receipt_path"]))
        checked = verify_shard(receipt_path, campaign_root=campaign_root)
        reconstructed = {
            "receipt_path": str(receipt_path.resolve()),
            "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
            "campaign_spec_digest": checked["campaign_spec_digest"],
            "campaign_plan_digest": checked["campaign_plan_digest"],
            "unit_key": checked["unit_key"],
            "report": reconstruct_fixed_shot(checked),
        }
        members.append(reconstructed)
    identity = {(member["campaign_spec_digest"], member["campaign_plan_digest"]) for member in members}
    if len(identity) != 1 or len({member["unit_key"] for member in members}) != len(members):
        raise ValueError("merge receipt has incomplete or duplicate frozen unit coverage")
    spec_digest, plan_digest = identity.pop()
    expected = _canonical_merge_payload(spec_digest=spec_digest, plan_digest=plan_digest, members=members)
    if payload != expected or merge_file.read_bytes() != canonical_json_bytes(expected) + b"\n":
        raise ValueError("merge receipt differs from verified canonical reconstruction")
    return expected


def _resume(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    if _read_json(args.plan).get("schema") == "campaign_work_plan_v1":
        _spec, work_plan, payload = _load_work_plan(args.plan, root)
        merged = _paired_merge_payload(args.merge, plan=work_plan)
        resumed = derive_resume_plan(
            plan=work_plan, verified_attempts=merged["verified_attempts"],
            scientific_identity=_paired_scientific_identity(work_plan),
            decision_for_look=_paired_resume_decision,
        )
        missing = resumed["resumable_unit_keys"]
        return _artifact(status="ok", plan=payload, phase="resume", resumable_unit_keys=missing,
                         exact_missing_set=missing, complete=not missing,
                         attempt_plans=resumed["attempt_plans"],
                         recovered_look_stop_receipts=resumed["recovered_look_stop_receipts"],
                         authorized_undispatched_keys=resumed["authorized_undispatched_keys"])
    _spec, plan = _load_plan(args.plan, root)
    merge = _verified_merge(args.merge, root)
    if merge.get("schema") != _MERGE_SCHEMA or merge.get("campaign_spec_digest") != plan["campaign_spec_digest"] or merge.get("campaign_plan_digest") != plan["campaign_plan_digest"]:
        raise ValueError("merge receipt differs from the frozen campaign plan")
    units = [member.get("unit_key") for member in merge.get("members", [])]
    if units != [plan["unit_key"]]:
        raise ValueError("merge receipt has incomplete or unexpected frozen unit coverage")
    return _artifact(status="ok", plan=plan, phase="resume", resumable_unit_keys=[], exact_missing_set=[])


def _assess(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    plan_path = getattr(args, "plan", None)
    if plan_path is not None and _read_json(plan_path).get("schema") == "campaign_work_plan_v1":
        spec, work_plan, payload = _load_work_plan(plan_path, root)
        merged = _paired_merge_payload(args.merge, plan=work_plan)
        if args.output_root is None:
            raise ValueError("paired assess requires --output-root for immutable report publication")
        report = reconstruct_campaign_report(**_paired_report_inputs(
            plan=work_plan, spec=spec, merged=merged,
        ))
        artifact = _publish_json(_output_root(args.output_root) / "assessment.json", asdict(report))
        return _artifact(status="ok", plan=payload, phase="assess", assessment_status="evidence_reconstructed",
                         artifact_path=str(artifact), artifact_sha256=sha256(artifact.read_bytes()).hexdigest(),
                         report=asdict(report), report_sha256=report.report_sha256,
                         merge_receipt_sha256=report.merge_receipt_sha256)
    merge = _verified_merge(args.merge, root)
    reports = [member["report"] for member in merge["members"]]
    failures = sum(report["failures"] for report in reports)
    completed = sum(report["completed"] for report in reports)
    return {"schema": _CLI_SCHEMA, "status": "ok", "phase": "assess",
            "campaign_spec_digest": merge["campaign_spec_digest"], "campaign_plan_digest": merge["campaign_plan_digest"],
            "completed": completed, "failures": failures, "assessment_status": "evidence_reconstructed"}


def _emit_slurm(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    if _read_json(args.plan).get("schema") == "campaign_work_plan_v1":
        _spec, work_plan, plan = _load_work_plan(args.plan, root)
    else:
        spec, plan = _load_plan(args.plan, root)
        work_plan = freeze_work_plan(
            campaign_spec_digest=plan["campaign_spec_digest"],
            coordinates=(CampaignCoordinateV1(cohort_id=spec.cohort_id, point_id=spec.point_id,
                                              sample_namespace=spec.sample_namespace, sample_ids=(spec.sample_id,)),),
            arm_seed_identities={spec.arm_id: spec.decoder_seed_identity}, look_sample_boundaries=(1,), units_per_shard=1,
        )
    allocation = SlurmAllocation(**_read_json(args.allocation))
    allowlists = _read_json(args.site_allowlists)
    argv = build_sbatch_argv(work_plan, allocation=allocation, allowed_values=allowlists,
                             entrypoint=("bp-registry-campaign", "run-shard", "--plan", str(Path(args.plan).resolve())))
    return _artifact(status="ok", plan=plan, phase="emit_slurm", sbatch_argv=list(argv), shard_count=len(work_plan.shards))


def _site_capability(args: argparse.Namespace) -> dict[str, Any]:
    scontrol = None if args.scontrol is None else _json_bytes(Path(args.scontrol)).decode("utf-8")
    sacct = None if args.sacct is None else _json_bytes(Path(args.sacct)).decode("utf-8")
    return {"schema": _CLI_SCHEMA, "status": "ok", "phase": "site_capability",
            "capabilities": parse_site_capabilities(scontrol_text=scontrol, sacct_text=sacct)}


def _operational_unit_runner(unit: dict[str, Any], staging: str) -> dict[str, Any]:
    """Deterministic, synthetic transport fixture; it never runs a decoder."""
    del staging
    return {
        "terminal_fact": {
            "unit_key": unit["unit_key"], "termination": "converged",
            "outcome": "exact", "logical_failure": False,
        },
        "work_vector": {"bp_calls": 1},
        "persisted_sample_bytes": f"phase8:{unit['physical_sample_identity']}".encode("ascii"),
    }


def _operational_stop_decision(*, look: int, terminal_records: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    keys = tuple(sorted(str(record["unit_key"]) for record in terminal_records))
    return {
        "decision_input_hashes": [sha256("|".join(keys).encode("ascii")).hexdigest()],
        "decision_result": {"look": look, "terminal_count": len(keys)},
        "stop_reason": "all_primary_decisions_resolved", "should_stop": look == 1,
    }


def _operational_work_plan(spec: CampaignSpecV1, root: Path, gate: Mapping[str, Any]):
    manifests = gate["eligible_manifests"]
    sample_ids = tuple(gate["preselected_sample_ids"])
    seeds: dict[str, str] = {}
    for arm, entry in manifests.items():
        manifest = preflight_manifest(_confined_file(root, entry[0], name="operational_gate manifest")).manifest
        seeds[str(arm)] = manifest.randomness.decoder_seed_identity
    return freeze_work_plan(
        campaign_spec_digest=build_one_unit_plan(spec).campaign_spec_digest,
        coordinates=(CampaignCoordinateV1(
            cohort_id=spec.cohort_id, point_id=spec.point_id,
            sample_namespace=spec.sample_namespace, sample_ids=sample_ids,
        ),),
        arm_seed_identities=seeds, look_sample_boundaries=(1, 2), units_per_shard=2,
    )


def _finite_evidence_hashes(root: Path) -> dict[str, str]:
    paths = sorted((*root.glob("unit-*/receipt.json"), *root.glob("look-*-merge-receipt.json")))
    if any(path.is_symlink() or not path.is_file() for path in paths):
        raise ValueError("finite-look evidence must contain regular receipt files")
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest() for path in paths}


def _operational_fixture(args: argparse.Namespace) -> dict[str, Any]:
    """Retain the bounded local/Slurm finite-look transport proof for Phase 8."""
    root = _existing_root(args.campaign_root, name="campaign_root")
    document = _read_json(args.campaign)
    spec, target_receipts = _campaign_spec(args.campaign, root)
    gate = document.get("operational_gate")
    if not isinstance(gate, Mapping):
        raise ValueError("operational fixture requires operational_gate metadata")
    work_plan = _operational_work_plan(spec, root, gate)
    output = _output_root(args.output_root)
    finite_root = output / "finite-look"
    try:
        dispatch_finite_looks(
            work_plan, output_root=finite_root, workers=1,
            unit_runner=_operational_unit_runner,
            decision_for_look=_operational_stop_decision, fault_after_decision=True,
        )
    except InterruptedError:
        pass
    else:
        raise ValueError("operational fixture fault injection did not interrupt")
    pre_crash = _finite_evidence_hashes(finite_root)
    recovered = dispatch_finite_looks(
        work_plan, output_root=finite_root, workers=1,
        unit_runner=_operational_unit_runner, decision_for_look=_operational_stop_decision,
    )
    post_crash = _finite_evidence_hashes(finite_root)
    if not recovered["recovered_stop_receipt"] or pre_crash != post_crash:
        raise ValueError("operational fixture did not recover immutable pre-crash evidence")
    allocation = SlurmAllocation(
        partition=None, qos=None, account=None, wall_minutes=5, memory_mb=256,
        cpus_per_task=1, max_concurrent_tasks=1,
    )
    observations = tuple(
        SchedulerObservation(
            job_id="phase8-synthetic", task_id=str(index), allocated_cpus=1,
            elapsed_seconds=0, state="COMPLETED", exit_code=0,
            accounting_available=None, accounting_unavailable_reason="synthetic harness has no site accounting",
            launch_overhead_seconds=0, shard_fixed_cost_seconds=0,
        )
        for index in range(len(work_plan.shards))
    )
    synthetic = execute_synthetic_slurm_array(
        work_plan, output_root=output / "synthetic-slurm", unit_runner=_operational_unit_runner,
        allocation=allocation, observations=observations,
    )
    payload = {
        "schema": "phase8_operational_fixture_receipt_v1",
        "label": "development_fixture", "assessment_status": "not_assessed",
        "campaign_spec_digest": work_plan.campaign_spec_digest,
        "campaign_plan_digest": work_plan.campaign_plan_digest,
        "preflight_campaign_plan_digest": _plan_payload(spec, target_receipts)["campaign_plan_digest"],
        "pre_crash_receipt_sha256s": pre_crash,
        "post_crash_receipt_sha256s": post_crash,
        "recovered_stop_receipt": recovered["recovered_stop_receipt"],
        "authorized_undispatched_keys": list(recovered["authorized_undispatched_keys"]),
        "next_look_submissions": 0,
        "synthetic_slurm_terminal_unit_keys": list(synthetic["terminal_unit_keys"]),
        "synthetic_slurm_incomplete_unit_keys": list(synthetic["incomplete_unit_keys"]),
    }
    artifact = _publish_json(output / "finite-look-recovery.json", payload)
    return {
        "schema": _CLI_SCHEMA, "status": "ok", "phase": "operational_fixture",
        "artifact_path": str(artifact), "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
        "recovered_stop_receipt": True, "next_look_submissions": 0,
    }


def _profile_gate(args: argparse.Namespace) -> dict[str, Any]:
    profile = _read_json(args.profile)
    required = {"measured", "limit", "unit"}
    numeric = (profile.get("measured"), profile.get("limit"))
    if (
        set(profile) != required
        or any(type(value) not in (int, float) or not math.isfinite(float(value)) for value in numeric)
        or not isinstance(profile["unit"], str)
    ):
        raise ValueError("profile gate requires measured, limit, and unit fields")
    if profile["measured"] < 0 or profile["limit"] <= 0 or profile["measured"] > profile["limit"]:
        raise ValueError("profile gate rejects an absent, negative, or over-limit measurement")
    return {"schema": _CLI_SCHEMA, "status": "ok", "phase": "profile_gate", "profile": profile}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("preflight", _preflight), ("plan", _plan)):
        item = commands.add_parser(name)
        item.add_argument("--campaign", required=True)
        item.add_argument("--campaign-root", required=True)
        item.add_argument("--output-root", required=True)
        item.set_defaults(handler=handler)
    for name, route in (("run-local", "local"), ("run-shard", "slurm")):
        item = commands.add_parser(name)
        item.add_argument("--plan", required=True)
        item.add_argument("--campaign-root", required=True)
        item.add_argument("--output-root", required=True)
        if route == "slurm":
            item.add_argument("--array-task-id", required=True)
            item.add_argument("--allocation")
            item.add_argument("--scheduler-observation")
        item.set_defaults(handler=lambda args, selected=route: _run(args, route=selected))
    item = commands.add_parser("emit-slurm")
    item.add_argument("--plan", required=True); item.add_argument("--campaign-root", required=True)
    item.add_argument("--allocation", required=True); item.add_argument("--site-allowlists", required=True)
    item.set_defaults(handler=_emit_slurm)
    item = commands.add_parser("verify")
    verification_input = item.add_mutually_exclusive_group()
    verification_input.add_argument("--receipt"); verification_input.add_argument("--report"); verification_input.add_argument("--campaign")
    item.add_argument("--merge"); item.add_argument("--plan")
    item.add_argument("--campaign-root", required=True); item.add_argument("--output")
    item.set_defaults(handler=lambda args: _verify_operational_gate(args) if args.campaign is not None else _verify(args) if args.receipt is not None or args.report is not None else (_ for _ in ()).throw(ValueError("verify requires --receipt, --report, or --campaign")))
    item = commands.add_parser("merge")
    item.add_argument("--receipt", action="append", required=True); item.add_argument("--plan"); item.add_argument("--campaign-root", required=True); item.add_argument("--output-root", required=True); item.set_defaults(handler=_merge)
    item = commands.add_parser("resume")
    item.add_argument("--plan", required=True); item.add_argument("--merge", required=True); item.add_argument("--campaign-root", required=True); item.set_defaults(handler=_resume)
    item = commands.add_parser("assess")
    item.add_argument("--merge", required=True); item.add_argument("--plan"); item.add_argument("--campaign-root", required=True); item.add_argument("--output-root"); item.set_defaults(handler=_assess)
    item = commands.add_parser("verify-routes")
    item.add_argument("--plan", required=True); item.add_argument("--local-merge", required=True); item.add_argument("--local-report", required=True)
    item.add_argument("--slurm-merge", required=True); item.add_argument("--slurm-report", required=True)
    item.add_argument("--campaign-root", required=True); item.add_argument("--output", required=True); item.set_defaults(handler=_verify_routes)
    item = commands.add_parser("site-capability")
    item.add_argument("--scontrol"); item.add_argument("--sacct"); item.set_defaults(handler=_site_capability)
    item = commands.add_parser("operational-fixture")
    item.add_argument("--campaign", required=True); item.add_argument("--campaign-root", required=True)
    item.add_argument("--output-root", required=True); item.set_defaults(handler=_operational_fixture)
    item = commands.add_parser("profile-gate")
    item.add_argument("--profile", required=True); item.set_defaults(handler=_profile_gate)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
        result = args.handler(args)
    except (AttributeError, OSError, ValidationError, ValueError) as error:
        print(json.dumps({"schema": _CLI_SCHEMA, "status": "error", "error": str(error)}, sort_keys=True, allow_nan=False))
        raise SystemExit(2) from error
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
