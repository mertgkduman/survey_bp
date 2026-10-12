"""Deterministic Phase 9 CSS evidence inventory from retained receipts."""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from ..literature import qualify_phase9_source_inventory
from .contracts import canonical_json_bytes


PHASE = "09-css-reproduction-and-controlled-comparisons"
STUDIES = {
    "schedule": "data/studies/phase9-update-schedule-control-v1.json",
    "relay_beam": "data/studies/phase9-relay-beam-control-v2.json",
    "mbbp_list_vote": "data/studies/phase9-mbbp-list-vote-control-v1.json",
}


def _regular(root: Path, relative: str, *, digest: str | None = None) -> tuple[Path, bytes, str]:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("evidence reference must be a relative workspace path")
    path = root / relative
    if path.is_symlink() or not path.is_file() or not path.resolve(strict=True).is_relative_to(root):
        raise ValueError(f"evidence reference is absent or outside workspace: {relative}")
    raw = path.read_bytes()
    actual = sha256(raw).hexdigest()
    if digest is not None and actual != digest:
        raise ValueError(f"evidence digest differs from retained bytes: {relative}")
    return path, raw, actual


def _json(root: Path, relative: str, *, digest: str | None = None) -> tuple[dict[str, Any], str]:
    _path, raw, actual = _regular(root, relative, digest=digest)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"evidence JSON object is required: {relative}")
    return value, actual


def _reference(root: Path, relative: str, *, digest: str | None = None) -> dict[str, str]:
    return {"path": relative, "sha256": _regular(root, relative, digest=digest)[2]}


def _typed_coverage(components: list[dict[str, Any]]) -> dict[str, Any]:
    if not components:
        raise ValueError("controlled evidence lacks typed components")
    fields = ("convergence_status", "iterations", "runtime_ns", "peak_rss_bytes",
              "events", "evidence_bytes", "storage_bytes", "interruption")
    status = {field: dict(sorted(Counter(component[field]["status"] for component in components).items()))
              for field in fields}
    for component in components:
        for field in fields:
            value = component[field]
            if value["status"] in {"unavailable", "not_applicable"} and not value.get("reason"):
                raise ValueError("controlled typed missingness lacks a reason")
        if not component["actual_work"] or not component["configured_limits"]:
            raise ValueError("controlled component lacks configured or actual work")
    return {"component_count": len(components), "field_status_counts": status,
            "actual_work_totals": dict(sorted((name, sum(item["actual_work"].get(name, 0) for item in components))
                                              for name in {key for item in components for key in item["actual_work"]}))}


def _control(root: Path, family_id: str, study_path: str, design: dict[str, Any]) -> dict[str, Any]:
    study, study_sha = _json(root, study_path)
    contract = design["families"][family_id]
    if (study.get("family_id") != family_id or study.get("source_label") != "controlled_canonical_adaptation"
            or study.get("claim_status") != "bounded_exploratory_no_superiority_claim"
            or study.get("verified") is not True
            or study.get("evaluation_namespace") != contract["paired_design"]["evaluation_namespace"]
            or study.get("campaign_plan_digest") != contract["ordered_plan_digest"]
            or study.get("frozen_bounded_n") != contract["bounded_evaluative_n"]
            or study.get("arm_order") != contract["arm_order"]
            or study.get("primary_contrasts") != contract["primary_contrasts"]):
        raise ValueError(f"{family_id} study differs from frozen design")
    plan, _ = _json(root, study["plan_path"], digest=study["plan_sha256"])
    merge, _ = _json(root, study["merge_path"], digest=study["merge_sha256"])
    report, _ = _json(root, study["report_path"], digest=study["report_sha256"])
    if (plan.get("campaign_plan_digest") != contract["ordered_plan_digest"]
            or report["family"]["status"] != "complete"
            or report["family"]["missing_unit_keys"]
            or len(report["family"]["complete_sample_identities"]) != study["completed_matched_n"]
            or study["completed_matched_n"] != study["frozen_bounded_n"]
            or report["family"]["comparisons"] != study["primary_contrasts"]
            or report["family"]["paired_tables"] != study["paired_tables"]
            or report["report_sha256"] != study["report_content_digest"]):
        raise ValueError(f"{family_id} controlled assessment differs from frozen matched work")
    for item in study["run_receipts"]:
        _regular(root, item["path"], digest=item["sha256"])
    components: list[dict[str, Any]] = []
    if family_id == "schedule":
        if len(merge["verified_attempts"]) != 2 * study["frozen_bounded_n"]:
            raise ValueError("schedule control lacks all sealed matched arms")
        components = [item["component"] for item in report["cost_projections"]]
        diagnostic, _ = _json(root, study["adapter_diagnostic_path"], digest=study["adapter_diagnostic_sha256"])
        if diagnostic["campaign_credit"] != 0:
            raise ValueError("schedule adapter diagnostic entered the evaluative denominator")
    else:
        if len(merge["verified_units"]) != len(study["arm_order"]) * study["frozen_bounded_n"]:
            raise ValueError("shared controlled family lacks all sealed arms")
        run_root = (root / study["run_receipts"][0]["path"]).parent
        shared_paths = sorted((run_root / "shared").glob("*.json"))
        unit_paths = sorted((run_root / "units").glob("*.json"))
        if (len(shared_paths) != study["frozen_bounded_n"]
                or len(unit_paths) != len(merge["verified_units"])):
            raise ValueError("shared controlled family has missing or duplicate receipt files")
        by_sample: dict[str, set[str]] = defaultdict(set)
        for path in shared_paths:
            shared = json.loads(path.read_bytes())
            components.extend(([shared["component"]] if family_id == "relay_beam" else shared["components"]))
        for path in unit_paths:
            receipt = json.loads(path.read_bytes())
            by_sample[receipt["physical_sample_identity"]].add(receipt["shared_input_receipt_sha256"])
            if receipt["component"] is not None:
                components.append(receipt["component"])
            components.append(receipt["validation_component"])
            if receipt["candidate"] is None and receipt["validation_component"]["actual_work"].get("original_checks") != 0:
                raise ValueError("no-candidate arm charged an original candidate check")
        if len(by_sample) != study["frozen_bounded_n"] or any(len(values) != 1 for values in by_sample.values()):
            raise ValueError("shared controlled arms differ in member or initial receipt identity")
    profile_refs = []
    for name, profile in sorted(contract["calibration_profiles"].items()):
        profile_refs.append({"mechanism": name, **_reference(root, profile["path"], digest=profile["sha256"])})
    return {
        "family_id": family_id, "source_label": study["source_label"],
        "claim_status": study["claim_status"], "evaluation_namespace": study["evaluation_namespace"],
        "profile_sample_role": study["profile_sample_role"], "profiles": profile_refs,
        "frozen_bounded_n": study["frozen_bounded_n"], "completed_matched_n": study["completed_matched_n"],
        "arm_order": study["arm_order"], "primary_contrasts": study["primary_contrasts"],
        "denominator_views": study["denominator_views"],
        "paired_tables": report["family"]["paired_tables"],
        "holm_result": report["family"]["holm_result"],
        "typed_components": _typed_coverage(components),
        "study": {"path": study_path, "sha256": study_sha},
        "plan": _reference(root, study["plan_path"], digest=study["plan_sha256"]),
        "merge": _reference(root, study["merge_path"], digest=study["merge_sha256"]),
        "report": _reference(root, study["report_path"], digest=study["report_sha256"]),
        "run_receipts": study["run_receipts"],
        "publication_slurm_authorization": "deny",
    }


def _public_verify(root: Path, *, plan: str, merge: str, report: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "bp_registry.campaigns.cli", "verify", "--plan", str(root / plan),
         "--merge", str(root / merge), "--report", str(root / report), "--campaign-root", str(root)],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0 or json.loads(result.stdout).get("verified") is not True:
        raise ValueError("public receipt replay failed: " + result.stdout[-500:])


def build_phase9_css_evidence_index(root: str | Path, *, deep_verify: bool = False) -> bytes:
    """Reconstruct the complete index; optional public replay runs no decoder."""
    workspace = Path(root).resolve(strict=True)
    inventory_path = "literature_policies/qualification-phase9-v1.json"
    inventory, inventory_sha = _json(workspace, inventory_path)
    if qualify_phase9_source_inventory(workspace) != (workspace / inventory_path).read_bytes():
        raise ValueError("Phase 9 source inventory differs from deterministic compiler")
    source_records = inventory["records"]
    if len(source_records) != 14 or len({item["identity"] for item in source_records}) != 14:
        raise ValueError("Phase 9 evidence index requires fourteen unique source variants")
    variants = []
    for item in source_records:
        _regular(workspace, item["source_spec"], digest=item["source_spec_sha256"])
        _regular(workspace, item["receipt"]["path"], digest=item["receipt"]["sha256"])
        if item["runnable_counterpart"] is not None:
            ref = item["runnable_counterpart"]
            _regular(workspace, ref["path"], digest=ref["sha256"])
        if item["source_faithful"] is not False or item["assessment_eligibility"] != "not_eligible":
            raise ValueError("source status was promoted without an author identity gate")
        selected = item.get("canonical_assessment")
        if selected is not None:
            _regular(workspace, selected["path"], digest=selected["sha256"])
        variants.append({"identity": item["identity"], "source_spec": _reference(workspace, item["source_spec"]),
                         "source_qualification": item["receipt"], "source_revision": item["source_revision"],
                         "source_faithful": False, "native_status": item["native_status"],
                         "target_status": item["target_status"], "blockers": item["blockers"],
                         "canonical_assessment": selected or {"status": "not_assessed"}})
    b1_path = "data/studies/phase9-yao-b1-t001-p010-v4-assessment.json"
    b1, b1_sha = _json(workspace, b1_path)
    report_ref = b1["artifacts"]["report"]
    b1_report, _ = _json(workspace, report_ref["path"], digest=report_ref["sha256"])
    if (b1["verified"] is not True or b1["source_label"] != "canonical_adaptation"
            or b1_report["assessment_status"] != "inconclusive_cap_censored"
            or b1_report["terminal_state"] != "cap_censored"
            or b1_report["target_decision"]["verdict"] != "inconclusive"
            or b1_report["terminal_failure_ordinal"] is not None
            or b1_report["inverse_binomial_rate"] is not None):
        raise ValueError("B1 adaptation censor differs from verified terminal evidence")
    for item in b1["artifacts"].values():
        _regular(workspace, item["path"], digest=item["sha256"])
    for item in b1["sealed_attempts"]:
        _regular(workspace, item["path"], digest=item["sha256"])
    design_path = "data/studies/phase9-controlled-design-v2.json"
    design, design_sha = _json(workspace, design_path)
    controls = [_control(workspace, family_id, STUDIES[family_id], design)
                for family_id in ("schedule", "relay_beam", "mbbp_list_vote")]
    if deep_verify:
        _public_verify(workspace, plan=b1["artifacts"]["plan"]["path"],
                       merge=b1["artifacts"]["merge"]["path"], report=report_ref["path"])
        for item in controls:
            _public_verify(workspace, plan=item["plan"]["path"],
                           merge=item["merge"]["path"], report=item["report"]["path"])
    phase_root = f".planning/phases/{PHASE}"
    coverage = []
    for number in range(1, 21):
        label = f"09-{number:02d}"
        plan_path = f"{phase_root}/{label}-PLAN.md"
        summary_path = f"{phase_root}/{label}-SUMMARY.md"
        plan_ref = _reference(workspace, plan_path)
        summary_ref = _reference(workspace, summary_path)
        if number == 15:
            summary_ref["sha256"] = None  # The index is Plan 15's own output.
        coverage.append({"plan": label, "plan_ref": plan_ref, "summary_ref": summary_ref,
                         "status": "complete"})
    gap_closure = {
        "plan_16_prospective_terminal": [b1["artifacts"][name] for name in ("plan", "cap_censor", "report")],
        "plan_17_dynamic_cap": [b1["artifacts"][name] for name in ("cap_censor", "merge")],
        "plan_18_ordered_partial_terminal": [controls[0]["plan"], controls[0]["merge"],
                                               *controls[0]["run_receipts"]],
        "plan_19_typed_shared_input": [controls[1]["study"], controls[1]["merge"],
                                       controls[2]["study"], controls[2]["merge"]],
        "plan_20_guarded_serializer": [_reference(workspace, "data/manifests/phase9-yao-b1-t001-p010-v4.json")],
    }
    for refs in gap_closure.values():
        for ref in refs:
            _regular(workspace, ref["path"], digest=ref["sha256"])
    eval03_complete = all(item["frozen_bounded_n"] > 0 and
                          item["completed_matched_n"] == item["frozen_bounded_n"] and
                          item["profiles"] for item in controls)
    blockers = [] if eval03_complete else ["one or more frozen controlled families lack complete positive matched evidence"]
    payload = {
        "schema": "phase9_css_evidence_index_v1", "phase": PHASE,
        "phase_status": "complete" if eval03_complete else "incomplete",
        "eval03_complete": eval03_complete, "completion_blockers": blockers,
        "source_inventory": {"path": inventory_path, "sha256": inventory_sha},
        "source_variant_count": 14, "source_variants": variants,
        "yao_b1": {"study": {"path": b1_path, "sha256": b1_sha},
                   "assessment_status": b1["assessment_status"],
                   "source_label": b1["source_label"],
                   "target_failures": b1["frozen_target_failures"],
                   "completed_shots": b1["completed_shots"],
                   "terminal_failure_ordinal": b1_report["terminal_failure_ordinal"],
                   "inferential_prefix": b1["inferential_prefix"],
                   "inverse_binomial_interval": b1["inverse_binomial_interval"],
                   "target_verdict": b1_report["target_decision"]["verdict"],
                   "first_exhausted_cap": b1["first_exhausted_cap"],
                   "actual_resources": b1["actual_resources"],
                   "artifacts": b1["artifacts"]},
        "controlled_design": {"path": design_path, "sha256": design_sha},
        "controls": controls, "coverage": coverage, "gap_closure": gap_closure,
        "requirements": {"EVAL-01": "source_gaps_explicit", "EVAL-02": "bounded_censored_adaptation",
                         "EVAL-03": "complete" if eval03_complete else "incomplete",
                         "CAN-02": "shared_member_vote_replayed"},
        "external_unknowns": {
            "author_experiment_artifacts": "unverified; later digest-bound qualification required",
            "journal_reproduction_tolerance": "unavailable; factor 1.5 applies to the one bounded Yao tracer only",
            "site_limits_and_accounting": "unavailable; local measurement only",
        },
        "publication_slurm_authorization": "deny",
    }
    return canonical_json_bytes(payload) + b"\n"
