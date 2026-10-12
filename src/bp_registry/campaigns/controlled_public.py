"""Receipt-first public lifecycle for the frozen shared-initial CSS family."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .contracts import canonical_json_bytes
from .controlled import ControlledComponentEvidenceV1, SharedInitialBPReceiptV1, SharedMBBPMemberSetReceiptV1, project_controlled_costs
from .controlled_execution import run_fair_controlled_unit, verify_fair_controlled_unit
from .controlled_mbbp import run_mbbp_controlled_unit, verify_mbbp_controlled_unit
from .planning import CampaignWorkPlan
from .reporting import reconstruct_controlled_family


def _line(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _publish(path: Path, value: Mapping[str, Any]) -> Path:
    payload = _line(dict(value))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise ValueError("controlled public artifact conflicts with immutable bytes")
        return path
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".controlled-public-", delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        stage = Path(handle.name)
    try:
        os.replace(stage, path)
    finally:
        stage.unlink(missing_ok=True)
    return path


def _read(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("controlled public input must be a regular file")
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or raw != _line(value):
        raise ValueError("controlled public input has noncanonical JSON bytes")
    return value


def _family(plan: CampaignWorkPlan) -> tuple[str, tuple[str, ...], tuple[tuple[str, str], ...]]:
    order = tuple(json.loads(plan.campaign_plan_preimage)["execution_order"]["arm_order"])
    if order == ("initial_bp", "relay", "beam"):
        return "relay_beam", order, (("initial_bp", "relay"), ("initial_bp", "beam"))
    if order == ("list", "vote"):
        return "mbbp_list_vote", order, (("list", "vote"),)
    raise ValueError("controlled public lifecycle requires one declared shared-input family")


def _unit_verifier(plan: CampaignWorkPlan):
    return verify_fair_controlled_unit if _family(plan)[0] == "relay_beam" else verify_mbbp_controlled_unit


def _design(*, root: Path, plan: CampaignWorkPlan) -> tuple[dict[str, Any], str]:
    path = root / "data/studies/phase9-controlled-design-v2.json"
    if path.is_symlink() or not path.is_file():
        raise ValueError("controlled fair design is unavailable")
    design = json.loads(path.read_bytes())
    family_id, order, comparisons = _family(plan)
    family = design["families"][family_id]
    if (family["ordered_plan_digest"] != plan.campaign_plan_digest
            or family["arm_order"] != list(order)
            or family["primary_contrasts"] != [list(item) for item in comparisons]
            or family["paired_design"]["familywise_alpha"] != 0.05
            or family["status"] != "bounded_exploratory"
            or design["evaluation_started"] is not False):
        raise ValueError("controlled fair design differs from frozen plan or primary family")
    return family, sha256(path.read_bytes()).hexdigest()


def _arm_manifest(root: Path, plan: CampaignWorkPlan, arm_id: str) -> dict[str, Any]:
    arm = next((item for item in plan.work_spec.arms if item.arm_id == arm_id), None)
    if arm is None:
        raise ValueError("controlled arm is absent from frozen work")
    path = root / arm.manifest_path
    if path.is_symlink() or not path.is_file() or sha256(path.read_bytes()).hexdigest() != arm.manifest_sha256:
        raise ValueError("controlled arm manifest differs from frozen bytes")
    return json.loads(path.read_bytes())


def _existing_units(*, root: Path, plan: CampaignWorkPlan, run_root: Path) -> list[dict[str, Any]]:
    receipt_root = run_root / "units"
    paths = () if not receipt_root.exists() else tuple(sorted(receipt_root.glob("*.json")))
    by_key = {}
    for path in paths:
        if path.name not in {f"{key}.json" for key in plan.unit_keys}:
            raise ValueError("controlled run contains an undeclared unit receipt")
        unit = next(item for item in plan.units if path.name == f"{item.key}.json")
        receipt = _unit_verifier(plan)(
            plan=plan, unit=unit, arm_manifest=_arm_manifest(root, plan, unit.arm_id),
            campaign_root=root, output_root=run_root,
        )
        by_key[unit.key] = {
            "unit_key": unit.key, "receipt_path": str(path.resolve(strict=True)),
            "receipt_sha256": sha256(path.read_bytes()).hexdigest(),
            "terminal_status": receipt.terminal_status,
        }
    prefix = plan.unit_keys[:len(by_key)]
    if set(by_key) != set(prefix):
        raise ValueError("controlled fair receipts must cover one frozen unit prefix")
    return [by_key[key] for key in prefix]


def run_local(*, root: Path, plan: CampaignWorkPlan, output_root: Path, max_units: int | None) -> dict[str, Any]:
    """Run only the missing frozen prefix, sealing each unit before advancing."""
    _design(root=root, plan=plan)
    if max_units is not None and (type(max_units) is not int or max_units < 1):
        raise ValueError("max-units must be a positive integer")
    before = _existing_units(root=root, plan=plan, run_root=output_root)
    selected = plan.units[len(before):]
    if max_units is not None:
        selected = selected[:max_units]
    if not selected:
        return {"schema": f"controlled_{_family(plan)[0]}_run_result_v1", "complete": True,
                "terminal_unit_keys": list(plan.unit_keys), "missing_unit_keys": [],
                "artifact_path": None}
    for unit in selected:
        try:
            (run_fair_controlled_unit if _family(plan)[0] == "relay_beam" else run_mbbp_controlled_unit)(
                plan=plan, unit=unit, arm_manifest=_arm_manifest(root, plan, unit.arm_id),
                campaign_root=root, output_root=output_root,
            )
        except Exception as exc:
            # Keep a durable, non-sensitive record of a failed dispatch. The
            # missing unit remains eligible for exact-prefix recovery.
            interruption_root = output_root / "interruptions"
            attempt_ordinal = 1 + len(tuple(interruption_root.glob(f"{unit.key}-*.json")))
            _publish(interruption_root / f"{unit.key}-{attempt_ordinal:08d}.json", {
                "schema": "controlled_unit_interruption_v1",
                "campaign_spec_digest": plan.campaign_spec_digest,
                "campaign_plan_digest": plan.campaign_plan_digest,
                "unit_key": unit.key,
                "attempt_ordinal": attempt_ordinal,
                "physical_sample_identity": unit.physical_sample_identity,
                "arm_id": unit.arm_id,
                "exception_type": type(exc).__name__,
            })
            raise
    after = _existing_units(root=root, plan=plan, run_root=output_root)
    first, last = len(before) + 1, len(after)
    envelope = {
        "schema": f"controlled_{_family(plan)[0]}_run_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "run_root": str(output_root.resolve(strict=True)),
        "first_unit_ordinal": first, "last_unit_ordinal": last,
        "units": after[len(before):],
    }
    artifact = _publish(output_root / f"controlled-run-{first:08d}-{last:08d}.json", envelope)
    return {"schema": f"controlled_{_family(plan)[0]}_run_result_v1", "complete": last == len(plan.units),
            "terminal_unit_keys": list(plan.unit_keys[:last]),
            "missing_unit_keys": list(plan.unit_keys[last:]),
            "artifact_path": str(artifact), "artifact_sha256": sha256(artifact.read_bytes()).hexdigest()}


def _verified_run_envelope(*, path: Path, root: Path, plan: CampaignWorkPlan) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    envelope = _read(path)
    run_root = Path(envelope.get("run_root", ""))
    if (envelope.get("schema") != f"controlled_{_family(plan)[0]}_run_v1"
            or envelope.get("campaign_spec_digest") != plan.campaign_spec_digest
            or envelope.get("campaign_plan_digest") != plan.campaign_plan_digest
            or not run_root.is_dir() or run_root.is_symlink()
            or path.parent.resolve(strict=True) != run_root.resolve(strict=True)):
        raise ValueError("controlled run envelope differs from frozen plan or root")
    first, last = envelope.get("first_unit_ordinal"), envelope.get("last_unit_ordinal")
    if type(first) is not int or type(last) is not int or not 1 <= first <= last <= len(plan.units):
        raise ValueError("controlled run ordinals are outside frozen work")
    listed = envelope.get("units")
    if not isinstance(listed, list) or len(listed) != last - first + 1:
        raise ValueError("controlled run envelope has an incomplete unit list")
    verified = []
    for ordinal, listed_item in zip(range(first, last + 1), listed, strict=True):
        unit = plan.units[ordinal - 1]
        receipt_path = run_root / "units" / f"{unit.key}.json"
        receipt = _unit_verifier(plan)(
            plan=plan, unit=unit, arm_manifest=_arm_manifest(root, plan, unit.arm_id),
            campaign_root=root, output_root=run_root,
        )
        item = {"unit_key": unit.key, "receipt_path": str(receipt_path.resolve(strict=True)),
                "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
                "terminal_status": receipt.terminal_status}
        if item != listed_item:
            raise ValueError("controlled run envelope differs from independently verified unit")
        verified.append(item)
    return envelope, verified


def _merge_payload(*, root: Path, plan: CampaignWorkPlan, run_paths: list[Path]) -> dict[str, Any]:
    family_design, design_sha = _design(root=root, plan=plan)
    refs = []
    by_key: dict[str, dict[str, Any]] = {}
    run_root: Path | None = None
    for path in run_paths:
        envelope, items = _verified_run_envelope(path=path, root=root, plan=plan)
        current_root = Path(envelope["run_root"])
        if run_root is not None and current_root != run_root:
            raise ValueError("controlled merge requires one physical run root")
        run_root = current_root
        refs.append({"path": str(path.resolve(strict=True)), "sha256": sha256(path.read_bytes()).hexdigest()})
        for item in items:
            if item["unit_key"] in by_key:
                raise ValueError("controlled merge rejects duplicate unit delivery")
            by_key[item["unit_key"]] = item
    if not by_key or set(by_key) != set(plan.unit_keys[:len(by_key)]):
        raise ValueError("controlled merge requires one nonempty frozen unit prefix")
    assert run_root is not None
    ordered = [by_key[key] for key in plan.unit_keys[:len(by_key)]]
    status_by_key = {item["unit_key"]: item["terminal_status"] for item in ordered}
    family_id, order, _comparisons = _family(plan)
    family = reconstruct_controlled_family(
        plan=plan, family_id=family_id, source_design_sha256=design_sha,
        terminal_status_by_unit=status_by_key,
        alpha=family_design["paired_design"]["familywise_alpha"],
    )
    costs = []
    for start in range(0, len(ordered), len(order)):
        group = plan.units[start:start + len(order)]
        completed = [unit for unit in group if unit.key in by_key]
        if not completed:
            continue
        sample_identity = group[0].physical_sample_identity
        shared_path = run_root / "shared" / f"{sample_identity}.json"
        shared = (SharedInitialBPReceiptV1 if family_id == "relay_beam" else SharedMBBPMemberSetReceiptV1).model_validate_json(shared_path.read_bytes())
        if shared_path.read_bytes() != shared.primitive_bytes() + b"\n":
            raise ValueError("controlled cost projection changed shared receipt bytes")
        receipts = {unit.arm_id: _unit_verifier(plan)(
            plan=plan, unit=unit, arm_manifest=_arm_manifest(root, plan, unit.arm_id),
            campaign_root=root, output_root=run_root,
        ) for unit in completed}
        projection = project_controlled_costs(
            shared=((shared.component,) if family_id == "relay_beam" else shared.components),
            shared_input_receipt_sha256=shared.digest(),
            incremental={name: item.component for name, item in receipts.items() if item.component is not None},
            validation={name: item.validation_component for name, item in receipts.items()},
        )
        costs.append({"sample_identity": sample_identity,
                      "shared_receipt_sha256": shared.digest(),
                      "projection": projection.model_dump(mode="json", by_alias=True)})
    return {
        "schema": f"controlled_{family_id}_merge_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "source_design_sha256": design_sha,
        "run_root": str(run_root.resolve(strict=True)),
        "run_envelopes": sorted(refs, key=lambda item: item["path"]),
        "verified_units": ordered,
        "family": family.model_dump(mode="json", by_alias=True),
        "cost_projections": costs,
        "missing_unit_keys": list(family.missing_unit_keys),
    }


def merge(*, root: Path, plan: CampaignWorkPlan, run_paths: list[Path], output_root: Path) -> dict[str, Any]:
    payload = _merge_payload(root=root, plan=plan, run_paths=run_paths)
    family_id = _family(plan)[0]
    artifact = _publish(output_root / f"controlled-{family_id}-merge.json", payload)
    return {"schema": f"controlled_{family_id}_merge_result_v1", "artifact_path": str(artifact),
            "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
            "complete": not payload["missing_unit_keys"],
            "missing_unit_keys": payload["missing_unit_keys"],
            "verified_unit_count": len(payload["verified_units"])}


def verify_merge(*, root: Path, plan: CampaignWorkPlan, merge_path: Path) -> dict[str, Any]:
    saved = _read(merge_path)
    paths = [Path(item["path"]) for item in saved.get("run_envelopes", [])]
    expected = _merge_payload(root=root, plan=plan, run_paths=paths)
    if saved != expected:
        raise ValueError("controlled merge differs from independent receipt replay")
    return expected


def assess(*, root: Path, plan: CampaignWorkPlan, merge_path: Path, output_root: Path) -> dict[str, Any]:
    merged = verify_merge(root=root, plan=plan, merge_path=merge_path)
    if merged["missing_unit_keys"]:
        raise ValueError("controlled assessment requires every frozen matched group")
    unsigned = {
        "schema": f"controlled_{_family(plan)[0]}_assessment_v1",
        "campaign_plan_digest": plan.campaign_plan_digest,
        "merge_sha256": sha256(merge_path.read_bytes()).hexdigest(),
        "source_design_sha256": merged["source_design_sha256"],
        "family": merged["family"],
        "cost_projections": merged["cost_projections"],
        "claim_status": "bounded_exploratory",
        "publication_slurm_authorization": "deny",
    }
    family_id = _family(plan)[0]
    payload = {**unsigned, "report_sha256": sha256(f"bp-registry-controlled-{family_id}-report-v1\0".encode() + canonical_json_bytes(unsigned)).hexdigest()}
    artifact = _publish(output_root / f"controlled-{family_id}-assessment.json", payload)
    return {"schema": f"controlled_{family_id}_assess_result_v1", "artifact_path": str(artifact),
            "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
            "report_sha256": payload["report_sha256"], "complete": True}


def verify_report(*, root: Path, plan: CampaignWorkPlan, merge_path: Path, report_path: Path) -> dict[str, Any]:
    saved = _read(report_path)
    family_id = _family(plan)[0]
    if saved.get("schema") != f"controlled_{family_id}_assessment_v1":
        raise ValueError("controlled report has an invalid schema")
    merged = verify_merge(root=root, plan=plan, merge_path=merge_path)
    if merged["missing_unit_keys"]:
        raise ValueError("controlled report cannot assess incomplete frozen groups")
    unsigned = {key: value for key, value in saved.items() if key != "report_sha256"}
    if (unsigned.get("campaign_plan_digest") != plan.campaign_plan_digest
            or unsigned.get("merge_sha256") != sha256(merge_path.read_bytes()).hexdigest()
            or unsigned.get("source_design_sha256") != merged["source_design_sha256"]
            or unsigned.get("family") != merged["family"]
            or unsigned.get("cost_projections") != merged["cost_projections"]
            or unsigned.get("claim_status") != "bounded_exploratory"
            or unsigned.get("publication_slurm_authorization") != "deny"
            or saved.get("report_sha256") != sha256(
                f"bp-registry-controlled-{family_id}-report-v1\0".encode() + canonical_json_bytes(unsigned)).hexdigest()):
        raise ValueError("controlled report differs from independent merge reconstruction")
    return saved


def controlled_denominator_views(statuses_by_arm: Mapping[str, list[str]]) -> dict[str, Any]:
    """Keep all-shot, accepted-shot, and acceptance denominators separate."""
    accepted = {"exact", "stabilizer_equivalent", "wrong_logical_action"}
    success = {"exact", "stabilizer_equivalent"}
    views = {}
    for arm, statuses in statuses_by_arm.items():
        total = len(statuses)
        accepted_count = sum(status in accepted for status in statuses)
        failure_count = sum(status not in success for status in statuses)
        accepted_failures = sum(status == "wrong_logical_action" for status in statuses)
        views[arm] = {
            "all_shot": {"denominator": total, "failures": failure_count,
                         "failure_rate": None if total == 0 else failure_count / total},
            "conditional_acceptance": {"denominator": accepted_count,
                                       "failures": accepted_failures,
                                       "failure_rate": None if accepted_count == 0 else accepted_failures / accepted_count,
                                       "missing_reason": None if accepted_count else "no accepted terminal"},
            "acceptance_probability": {"denominator": total, "accepted": accepted_count,
                                        "probability": None if total == 0 else accepted_count / total},
        }
    return views


def ordinary_report_payload(*, root: Path, plan: CampaignWorkPlan, merged: Mapping[str, Any]) -> dict[str, Any]:
    """Assess the ordinary two-arm schedule control over all frozen pairs."""
    design_path = root / "data/studies/phase9-controlled-design-v2.json"
    if design_path.is_symlink() or not design_path.is_file():
        raise ValueError("ordinary controlled design is unavailable")
    design = json.loads(design_path.read_bytes())
    family_design = design["families"]["schedule"]
    if (family_design["ordered_plan_digest"] != plan.campaign_plan_digest
            or family_design["arm_order"] != ["spa_flooding", "spa_check_node_serial"]
            or family_design["primary_contrasts"] != [["spa_flooding", "spa_check_node_serial"]]
            or family_design["paired_design"]["familywise_alpha"] != 0.05
            or not merged["ordered_projection"]["complete"]):
        raise ValueError("ordinary controlled assessment requires its complete frozen schedule family")
    attempts = merged["verified_attempts"]
    statuses = {item["unit_key"]: item["terminal_fact"]["outcome"] for item in attempts}
    if len(statuses) != len(plan.units) or set(statuses) != set(plan.unit_keys):
        raise ValueError("ordinary controlled assessment lacks a complete terminal unit set")
    family = reconstruct_controlled_family(
        plan=plan, family_id="schedule", source_design_sha256=sha256(design_path.read_bytes()).hexdigest(),
        terminal_status_by_unit=statuses,
        alpha=family_design["paired_design"]["familywise_alpha"],
    )
    statuses_by_arm = {arm: [statuses[unit.key] for unit in plan.units if unit.arm_id == arm]
                       for arm in ("spa_flooding", "spa_check_node_serial")}
    costs = []
    for item in attempts:
        ledger = Path(item["canonical_ledger_path"])
        if ledger.is_symlink() or not ledger.is_file() or sha256(ledger.read_bytes()).hexdigest() != item["canonical_ledger_sha256"]:
            raise ValueError("ordinary controlled ledger differs from verified terminal")
        terminal_events = [event for event in item["events"] if event["kind"] == "termination"]
        if len(terminal_events) != 1:
            raise ValueError("ordinary controlled arm lacks one terminal event")
        terminal = terminal_events[0]["data"]
        runtime = terminal.get("decode_runtime", {})
        profile = terminal.get("profile", {})
        rss = profile.get("runtime", {}).get("peak_host_memory", {})
        arm_id = next(unit.arm_id for unit in plan.units if unit.key == item["unit_key"])
        manifest = json.loads(Path(item["arm_manifest_path"]).read_bytes())
        configured = manifest["budgets"]["shot"]
        rss_value = ({"status": "observed", "value": rss["value"]}
                     if type(rss.get("value")) is int else
                     {"status": "unavailable", "reason": rss.get("unavailable_reason") or "process RSS was not recorded"})
        component = ControlledComponentEvidenceV1.model_validate({
            "schema": "controlled_component_evidence_v1", "component_id": arm_id,
            "role": arm_id, "source_status": "controlled_css_adaptation",
            "convergence_status": ({"status": "observed", "value": terminal["converged"]}
                                   if type(terminal.get("converged")) is bool else
                                   {"status": "unavailable", "reason": "canonical terminal lacks convergence"}),
            "iterations": ({"status": "observed", "value": terminal["iterations"]}
                           if type(terminal.get("iterations")) is int else
                           {"status": "unavailable", "reason": "canonical terminal lacks iterations"}),
            "configured_limits": {"max_iterations": configured["max_iterations"],
                                  **configured["work_limits"]},
            "actual_work": item["work_vector"],
            "runtime_ns": ({"status": "observed", "value": runtime["value"]}
                           if type(runtime.get("value")) is int else
                           {"status": "unavailable", "reason": runtime.get("unavailable_reason") or "decode runtime absent"}),
            "peak_rss_bytes": rss_value,
            "events": {"status": "observed", "value": len(item["events"])},
            "evidence_bytes": {"status": "observed", "value": ledger.stat().st_size},
            "storage_bytes": {"status": "observed", "value": ledger.stat().st_size + Path(item["materialized_sample_path"]).stat().st_size},
            "interruption": {"status": "not_applicable", "reason": "arm sealed a terminal"},
            "provenance_sha256": item["arm_manifest_sha256"],
        })
        costs.append({
            "unit_key": item["unit_key"], "arm_id": next(unit.arm_id for unit in plan.units if unit.key == item["unit_key"]),
            "component": component.model_dump(mode="json", by_alias=True),
            "rss_scope": "process_peak",
        })
    unsigned = {
        "schema": "controlled_ordinary_assessment_v1",
        "campaign_plan_digest": plan.campaign_plan_digest,
        "merge_receipt_sha256": merged["receipt_sha256"],
        "source_design_sha256": family.source_design_sha256,
        "family": family.model_dump(mode="json", by_alias=True),
        "denominator_views": controlled_denominator_views(statuses_by_arm),
        "cost_projections": costs,
        "claim_status": "bounded_exploratory",
        "publication_slurm_authorization": "deny",
    }
    return {**unsigned, "report_sha256": sha256(
        b"bp-registry-controlled-ordinary-report-v1\0" + canonical_json_bytes(unsigned)).hexdigest()}


def publish_ordinary_report(*, root: Path, plan: CampaignWorkPlan, merged: Mapping[str, Any], output_root: Path) -> dict[str, Any]:
    report = ordinary_report_payload(root=root, plan=plan, merged=merged)
    artifact = _publish(output_root / "controlled-ordinary-assessment.json", report)
    return {"artifact_path": str(artifact), "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
            "report_sha256": report["report_sha256"], "complete": True}


def verify_ordinary_report(*, root: Path, plan: CampaignWorkPlan, merged: Mapping[str, Any], report_path: Path) -> dict[str, Any]:
    expected = ordinary_report_payload(root=root, plan=plan, merged=merged)
    if _read(report_path) != expected:
        raise ValueError("ordinary controlled report differs from independent reconstruction")
    return expected
