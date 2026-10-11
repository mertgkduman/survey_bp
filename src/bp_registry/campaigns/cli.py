"""Strict, JSON-only lifecycle command for bounded campaign evidence.

The command deliberately owns only input validation, artifact publication, and
route selection.  Campaign identities, execution, shard verification, and
statistical reconstruction stay in the modules that define their scientific
contracts.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import sys
import tempfile
from typing import Any, Callable, Mapping

from pydantic import ValidationError

from ..manifests import preflight as preflight_manifest
from .contracts import CampaignSpecV1, build_one_unit_plan, canonical_json_bytes
from .execution import run_one_unit
from .planning import CampaignCoordinateV1, freeze_work_plan
from .shards import reconstruct_fixed_shot, verify_shard
from .slurm import SlurmAllocation, build_sbatch_argv, parse_site_capabilities


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
    if set(document) != {"campaign_spec", "target_receipts"} or not isinstance(document["campaign_spec"], Mapping):
        raise ValueError("campaign document must contain campaign_spec and target_receipts")
    spec = CampaignSpecV1.model_validate(document["campaign_spec"])
    manifest = _confined_file(campaign_root, spec.inner_manifest_path, name="inner_manifest_path")
    if sha256(manifest.read_bytes()).hexdigest() != spec.inner_manifest_sha256:
        raise ValueError("inner manifest SHA-256 differs from frozen campaign specification")
    preflight_manifest(manifest)
    target_receipts = _validated_target_receipts(spec, document["target_receipts"], campaign_root)
    return spec, target_receipts


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
    spec, target_receipts = _campaign_spec(args.campaign, root)
    payload = _plan_payload(spec, target_receipts)
    output = _output_root(args.output_root)
    artifact = _publish_json(output / "campaign-plan.json", payload)
    return _artifact(status="ok", plan=payload, phase="plan", artifact_path=str(artifact), artifact_sha256=sha256(artifact.read_bytes()).hexdigest())


def _run(args: argparse.Namespace, *, route: str) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    spec, plan = _load_plan(args.plan, root)
    output = _output_root(args.output_root)
    if route == "slurm" and args.array_task_id != "0":
        raise ValueError("one-unit campaign plans expose only frozen Slurm array task 0")
    run = run_one_unit(spec, campaign_root=root, output_root=output, worker_label=route)
    return _artifact(
        status="ok", plan=plan, phase="run_shard" if route == "slurm" else "run_local",
        executor_route=route, receipt_path=run["receipt_path"], receipt_sha256=sha256(Path(run["receipt_path"]).read_bytes()).hexdigest(),
        unit_key=run["unit_key"], shard_id=run["shard_id"], terminal_fact=run["terminal_fact"],
    )


def _verify(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
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


def _merge(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
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
    payload = {
        "schema": _MERGE_SCHEMA, "campaign_spec_digest": spec_digest, "campaign_plan_digest": plan_digest,
        "members": sorted(members, key=lambda member: str(member["unit_key"])),
    }
    output = _output_root(args.output_root)
    artifact = _publish_json(output / "campaign-merge.json", payload)
    return {"schema": _CLI_SCHEMA, "status": "ok", "phase": "merge", "campaign_spec_digest": spec_digest,
            "campaign_plan_digest": plan_digest, "artifact_path": str(artifact),
            "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(), "member_count": len(members)}


def _resume(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
    _spec, plan = _load_plan(args.plan, root)
    merge = _read_json(args.merge)
    if merge.get("schema") != _MERGE_SCHEMA or merge.get("campaign_spec_digest") != plan["campaign_spec_digest"] or merge.get("campaign_plan_digest") != plan["campaign_plan_digest"]:
        raise ValueError("merge receipt differs from the frozen campaign plan")
    units = [member.get("unit_key") for member in merge.get("members", [])]
    if units != [plan["unit_key"]]:
        raise ValueError("merge receipt has incomplete or unexpected frozen unit coverage")
    return _artifact(status="ok", plan=plan, phase="resume", resumable_unit_keys=[], exact_missing_set=[])


def _assess(args: argparse.Namespace) -> dict[str, Any]:
    merge = _read_json(args.merge)
    if merge.get("schema") != _MERGE_SCHEMA or not isinstance(merge.get("members"), list) or not merge["members"]:
        raise ValueError("assessment requires a nonempty verified campaign merge")
    first = merge["members"][0]
    if not isinstance(first, Mapping) or not isinstance(first.get("report"), Mapping):
        raise ValueError("merge record lacks verified report evidence")
    reports = [member.get("report") for member in merge["members"]]
    if any(not isinstance(report, Mapping) for report in reports):
        raise ValueError("merge member report is malformed")
    failures = sum(int(report["failures"]) for report in reports)
    completed = sum(int(report["completed"]) for report in reports)
    return {"schema": _CLI_SCHEMA, "status": "ok", "phase": "assess",
            "campaign_spec_digest": merge["campaign_spec_digest"], "campaign_plan_digest": merge["campaign_plan_digest"],
            "completed": completed, "failures": failures, "assessment_status": "evidence_reconstructed"}


def _emit_slurm(args: argparse.Namespace) -> dict[str, Any]:
    root = _existing_root(args.campaign_root, name="campaign_root")
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
    return _artifact(status="ok", plan=plan, phase="emit_slurm", sbatch_argv=list(argv), shard_count=1)


def _site_capability(args: argparse.Namespace) -> dict[str, Any]:
    scontrol = None if args.scontrol is None else _json_bytes(Path(args.scontrol)).decode("utf-8")
    sacct = None if args.sacct is None else _json_bytes(Path(args.sacct)).decode("utf-8")
    return {"schema": _CLI_SCHEMA, "status": "ok", "phase": "site_capability",
            "capabilities": parse_site_capabilities(scontrol_text=scontrol, sacct_text=sacct)}


def _profile_gate(args: argparse.Namespace) -> dict[str, Any]:
    profile = _read_json(args.profile)
    required = {"measured", "limit", "unit"}
    if set(profile) != required or not isinstance(profile["measured"], (int, float)) or not isinstance(profile["limit"], (int, float)) or not isinstance(profile["unit"], str):
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
        item.set_defaults(handler=lambda args, selected=route: _run(args, route=selected))
    item = commands.add_parser("emit-slurm")
    item.add_argument("--plan", required=True); item.add_argument("--campaign-root", required=True)
    item.add_argument("--allocation", required=True); item.add_argument("--site-allowlists", required=True)
    item.set_defaults(handler=_emit_slurm)
    item = commands.add_parser("verify")
    item.add_argument("--receipt", required=True); item.add_argument("--campaign-root", required=True); item.set_defaults(handler=_verify)
    item = commands.add_parser("merge")
    item.add_argument("--receipt", action="append", required=True); item.add_argument("--campaign-root", required=True); item.add_argument("--output-root", required=True); item.set_defaults(handler=_merge)
    item = commands.add_parser("resume")
    item.add_argument("--plan", required=True); item.add_argument("--merge", required=True); item.add_argument("--campaign-root", required=True); item.set_defaults(handler=_resume)
    item = commands.add_parser("assess")
    item.add_argument("--merge", required=True); item.set_defaults(handler=_assess)
    item = commands.add_parser("site-capability")
    item.add_argument("--scontrol"); item.add_argument("--sacct"); item.set_defaults(handler=_site_capability)
    item = commands.add_parser("profile-gate")
    item.add_argument("--profile", required=True); item.set_defaults(handler=_profile_gate)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
        result = args.handler(args)
    except (AttributeError, OSError, ValidationError, ValueError) as error:
        print(json.dumps({"schema": _CLI_SCHEMA, "status": "error", "error": str(error)}, sort_keys=True))
        raise SystemExit(2) from error
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
