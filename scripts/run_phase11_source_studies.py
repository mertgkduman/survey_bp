#!/usr/bin/env python3
"""Preflight and preserve aSCED source-study evidence without dispatching compute."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np

from bp_registry.campaigns.targets import QuaternarySourceTargetV1


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASCED_NATIVE_QUALIFICATION = ROOT / "data/native/phase11-asced-matched-input-qualification.json"
DEFAULT_SOURCE_AUTHORIZATION = ROOT / "data/results/phase11-production-authorization.json"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _load(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON input {path}: {error}") from error
    if not isinstance(loaded, dict):
        raise ValueError(f"JSON input {path} must be an object")
    return loaded


_A5_SETTINGS = {
    "qbpgd": {"iterations_per_round": 10, "epsilon": 1e-10, "maximum_decimation_rounds": 180, "early_syndrome_stop": True},
    "ordinary_qbp": {"iterations": 100},
}
_A5_BLOCKERS = {
    "continued_message_lifecycle_unresolved", "tie_rule_unresolved",
    "normalization_interface_unresolved", "figure_coordinates_unreviewed",
    "author_implementation_identity_unverified",
}
_A5_COMPONENTS = {
    "algorithm": "yao-2023-qbpgd-algorithm-3-v2",
    "fixation": "yao-2023-qbpgd-literal-fixation-v2",
    "depolarizing_setup": "yao-2023-qbpgd-depolarizing-setup-v2",
}


def _receipt_digest(payload: dict[str, Any]) -> str:
    frozen = dict(payload)
    frozen.pop("target_receipt_sha256", None)
    return sha256(_canonical_bytes(frozen)).hexdigest()


def _asced_native_reference(path: Path | None) -> dict[str, Any]:
    """Return only the independently qualified native matched-input state."""
    if path is None:
        return {
            "eligibility": "unavailable",
            "terminal": "unavailable_receipt_missing",
            "source_fidelity_claim": "none",
            "qualification_sha256": None,
            "paired_values": None,
            "failed_gates": ["native_qualification_receipt_missing"],
        }
    qualification = _load(path)
    if qualification.get("schema") != "phase11-asced-matched-input-qualification-v1":
        raise ValueError("native aSCED qualification schema is not admitted")
    digest = sha256(path.read_bytes()).hexdigest()
    if (
        qualification.get("terminal") == "declined_unavailable"
        and qualification.get("matched_input_status") == "unavailable"
        and qualification.get("source_fidelity_claim") == "none"
        and qualification.get("source_operations") == []
    ):
        return {
            "eligibility": "unavailable",
            "terminal": "declined_unavailable",
            "source_fidelity_claim": "none",
            "qualification_sha256": digest,
            "paired_values": None,
            "failed_gates": ["matched_native_route_declined_unavailable"],
        }
    return {
        "eligibility": "blocked",
        "terminal": "qualification_not_admitted",
        "source_fidelity_claim": "none",
        "qualification_sha256": digest,
        "paired_values": None,
        "failed_gates": ["native_qualification_not_successful"],
    }


def _source_dispatch_authorization(path: Path | None) -> dict[str, Any]:
    """Read the sealed publication decision and fail closed for source dispatch."""
    if path is None:
        return {
            "decision": "deny",
            "receipt_sha256": None,
            "dispatch_attempted": False,
            "failed_gates": ["production_authorization_receipt_missing"],
        }
    package = _load(path)
    receipt = package.get("receipt")
    if not isinstance(receipt, dict) or receipt.get("schema") != "phase11_authorization_receipt_v1":
        raise ValueError("Phase 11 source dispatch needs a sealed authorization receipt")
    if receipt.get("decision") != "deny" or receipt.get("dispatch_token") is not None:
        raise ValueError("Phase 11 source dispatch is not admitted without an exact source-lane allow receipt")
    expected = dict(receipt)
    claimed_digest = expected.pop("receipt_sha256", None)
    if claimed_digest != sha256(_canonical_bytes(expected)).hexdigest():
        raise ValueError("Phase 11 authorization receipt digest differs from sealed evidence")
    return {
        "decision": "deny",
        "receipt_sha256": claimed_digest,
        "dispatch_attempted": False,
        "failed_gates": ["production_authorization_denied"],
    }


def _validated_qbpgd(target_path: Path, manifest_path: Path | None) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    target_bytes = target_path.read_bytes()
    target = _load(target_path)
    if target.get("schema") != "phase11-qbpgd-source-target-v1":
        raise ValueError("Q-BPGD source target schema is not admitted")
    if target.get("paper") != {"figure": "Figure 7", "code": "A5", "channel": "depolarizing"}:
        raise ValueError("Q-BPGD target must freeze Figure 7 A5 depolarizing evidence")
    if target.get("settings") != _A5_SETTINGS:
        raise ValueError("Q-BPGD target settings differ from Figure 7")
    if target.get("source_stopping") != {"error_cases": 100, "denominator": "trials_until_100_error_cases"}:
        raise ValueError("Q-BPGD target source stopping must retain 100 error cases")
    if target.get("run_fidelity") != "canonical_adaptation" or target.get("source_author_code_identity") != "unverified":
        raise ValueError("Q-BPGD target cannot promote source or author-code fidelity")
    if target.get("source_components") != _A5_COMPONENTS or target.get("canonical_interpretations") != {"continued_messages": "D-14", "normalization": "D-15", "ties": "D-16"}:
        raise ValueError("Q-BPGD source components and canonical interpretations must remain separately bound")
    blockers = target.get("qualification_blockers")
    if not isinstance(blockers, list) or len(blockers) != len(set(blockers)) or not _A5_BLOCKERS.issubset(blockers):
        raise ValueError("Q-BPGD target must preserve every named fidelity blocker")
    if target.get("target_receipt_sha256") != _receipt_digest(target):
        raise ValueError("Q-BPGD target receipt digest differs from frozen content")
    root = Path(__file__).resolve().parents[1]
    artifact = target.get("artifact")
    if not isinstance(artifact, dict) or artifact.get("path") != "data/artifacts/quaternary-a5.json" or artifact.get("provenance_path") != "data/artifacts/quaternary-a5.provenance.json":
        raise ValueError("Q-BPGD target must bind only the frozen A5 artifact and provenance")
    artifact_path = root / str(artifact["path"])
    provenance_path = root / str(artifact["provenance_path"])
    if artifact.get("raw_sha256") != sha256(artifact_path.read_bytes()).hexdigest() or artifact.get("provenance_sha256") != sha256(provenance_path.read_bytes()).hexdigest():
        raise ValueError("A5 artifact or provenance digest differs from the Q-BPGD target")
    provenance = _load(provenance_path)
    if provenance.get("artifact", {}).get("raw_sha256") != artifact.get("raw_sha256") or provenance.get("distance", {}).get("independently_verified") is not False:
        raise ValueError("A5 provenance does not retain the checked artifact and source-reported distance boundary")
    qualification = target.get("bounded_qualification")
    if qualification != {"shot_id": 0, "depolarizing_p": 0.03, "canonical_iterations_per_round": 1, "round_limit": 1, "max_bp_calls": 1, "max_events": 32, "max_storage_bytes": 1_000_000, "max_wall_seconds": 30, "limitation": "one-sweep canonical-adaptation qualification probe; not a Figure 7 performance point"}:
        raise ValueError("Q-BPGD bounded qualification limits are incomplete or drifted")
    if manifest_path is None:
        return target, None, sha256(target_bytes).hexdigest()
    manifest = _load(manifest_path)
    if manifest.get("schema") != "phase11-qbpgd-source-manifest-v1":
        raise ValueError("Q-BPGD source manifest schema is not admitted")
    if manifest.get("target_document_sha256") != sha256(target_bytes).hexdigest() or manifest.get("target_receipt_sha256") != _receipt_digest(target):
        raise ValueError("Q-BPGD source manifest target digest differs")
    if manifest.get("artifact") != artifact or manifest.get("source_only") is not True or manifest.get("controlled_comparison") is not False or manifest.get("run_fidelity") != "canonical_adaptation":
        raise ValueError("Q-BPGD source manifest cannot alter source identity or fidelity")
    return target, manifest, sha256(target_bytes).hexdigest()


def _validated(target_path: Path, manifest_path: Path | None) -> tuple[Any, dict[str, Any] | None, str]:
    target_bytes = target_path.read_bytes()
    schema = _load(target_path).get("schema")
    if schema == "phase11-qbpgd-source-target-v1":
        return _validated_qbpgd(target_path, manifest_path)
    if schema == "phase11-mbp4-figures8-9-five-qubit-target-v1":
        return _validated_mbp4(target_path, manifest_path)
    target = QuaternarySourceTargetV1.model_validate_json(target_bytes)
    if manifest_path is None:
        return target, None, sha256(target_bytes).hexdigest()
    manifest = _load(manifest_path)
    if manifest.get("schema") != "phase11-asced-source-manifest-v1":
        raise ValueError("source manifest schema is not admitted")
    if manifest.get("target_document_sha256") != sha256(target_bytes).hexdigest():
        raise ValueError("target document digest differs from the frozen source manifest")
    if manifest.get("target_receipt_sha256") != target.digest():
        raise ValueError("target receipt digest differs from the frozen source manifest")
    if manifest.get("source_only") is not True or manifest.get("controlled_comparison") is not False:
        raise ValueError("source manifest cannot be reused for a controlled comparison")
    if manifest.get("run_fidelity") != "canonical_adaptation":
        raise ValueError("source target cannot promote canonical adaptation fidelity")
    return target, manifest, sha256(target_bytes).hexdigest()


_MBP4_SCHEMA = "phase11-mbp4-figures8-9-five-qubit-target-v1"
_MBP4_MANIFEST_SCHEMA = "phase11-mbp4-figures8-9-five-qubit-manifest-v1"
_MBP4_SCOPE = "deterministic_mechanism_only_not_a_curve_or_ranking"
_FIGURE6_MISSING = ["iteration_cap", "denominator", "stopping_rule", "exact_coordinates", "interval_method"]


def _validated_mbp4(target_path: Path, manifest_path: Path | None) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    target_bytes = target_path.read_bytes()
    target = _load(target_path)
    if target.get("schema") != _MBP4_SCHEMA or target.get("target_id") != "mbp4-figures8-9-five-qubit":
        raise ValueError("MBP4 target schema or identity is not admitted")
    if target.get("paper") != {"figures": ["Figure 8", "Figure 9"], "source": "https://arxiv.org/html/2104.13659"}:
        raise ValueError("MBP4 target must bind the Figures 8-9 source")
    if target.get("source_settings") != {"beta": 0.0, "epsilon": 0.003, "error": [0, 0, 0, 2, 0], "schedule": "qbp_flooding"}:
        raise ValueError("MBP4 target settings differ from the selected source mechanism")
    if target.get("alpha_only_contrast") != {"varying_field": "alpha", "held_constant": ["five_qubit_checks", "IIIYI_error", "epsilon", "schedule", "beta", "numerical_profile", "observation_horizon"]}:
        raise ValueError("MBP4 target must freeze every setting except alpha")
    if target.get("observation_horizon", {}).get("kind") != "frozen_sweeps" or target["observation_horizon"].get("sweeps") != 20:
        raise ValueError("MBP4 target requires the frozen 20-sweep observation horizon")
    if target.get("claim_scope") != _MBP4_SCOPE or target.get("source_author_code_identity") != "unverified":
        raise ValueError("MBP4 target cannot promote a curve, ranking, or author-code claim")
    if target.get("target_receipt_sha256") != _receipt_digest(target):
        raise ValueError("MBP4 target receipt digest differs from frozen content")
    paths = target.get("paths")
    if not isinstance(paths, dict) or paths.get("alpha_one", {}).get("alpha") != 1.0 or paths.get("alpha_one_point_five", {}).get("alpha") != 1.5:
        raise ValueError("MBP4 target must compare only the frozen alpha=1 and alpha=1.5 paths")
    if paths["alpha_one"].get("expected_relation") != "oscillatory" or paths["alpha_one_point_five"].get("expected_relation") != "correct_convergence":
        raise ValueError("MBP4 target relation drifted")
    if len(paths["alpha_one"].get("expected_trajectory", [])) != 20 or not paths["alpha_one_point_five"].get("expected_trajectory"):
        raise ValueError("MBP4 target must retain both independent finite trajectories")
    if manifest_path is None:
        return target, None, sha256(target_bytes).hexdigest()
    manifest = _load(manifest_path)
    if manifest.get("schema") != _MBP4_MANIFEST_SCHEMA or manifest.get("target_document_sha256") != sha256(target_bytes).hexdigest():
        raise ValueError("MBP4 manifest target digest differs")
    if manifest.get("target_receipt_sha256") != _receipt_digest(target) or manifest.get("source_only") is not True or manifest.get("controlled_comparison") is not False:
        raise ValueError("MBP4 manifest cannot alter the source-only target")
    if manifest.get("claim_scope") != _MBP4_SCOPE or manifest.get("figure6") != {"assessment": "not_admitted", "missing_metadata": _FIGURE6_MISSING, "status": "blocked_metadata"}:
        raise ValueError("MBP4 manifest must retain Figure 6 metadata gaps and mechanism-only scope")
    return target, manifest, sha256(target_bytes).hexdigest()


def _mbp4_evidence(target: dict[str, Any]) -> dict[str, Any]:
    """Run the declared finite mechanism and bind each sweep to source evidence."""
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.lineage import LineageEdge, LineageId
    from bp_registry.quaternary.evaluator import evaluate_pauli_candidate
    from bp_registry.quaternary.mbp4 import FixedAlphaMbp4Kernel, Mbp4Spec
    from bp_registry.quaternary.problems import PauliCandidate, PauliCode, QuaternaryOriginalProblem, QuaternaryWorkingProblem

    problem_data, settings = target["problem"], target["source_settings"]
    hidden = np.asarray(settings["error"], dtype=np.uint8)
    code = PauliCode(checks=np.asarray(problem_data["checks"], dtype=np.uint8), source_artifact_identity="kuo-lai-2021-five-qubit-figures8-9")
    original = QuaternaryOriginalProblem("original-phase11-mbp4-five-qubit", code, np.asarray(problem_data["syndrome"], dtype=np.uint8))
    if not np.array_equal(code.syndrome(hidden), original.syndrome):
        raise ValueError("MBP4 source error does not produce the frozen syndrome")
    priors = np.repeat(np.asarray([[1.0 - settings["epsilon"], settings["epsilon"] / 3.0, settings["epsilon"] / 3.0, settings["epsilon"] / 3.0]], dtype=np.float64), code.n, axis=0)
    working = QuaternaryWorkingProblem(
        "working-phase11-mbp4-five-qubit", original,
        LineageEdge("identity", LineageId("original", original.lineage_id), LineageId("working", "working-phase11-mbp4-five-qubit")),
    )
    paths: dict[str, Any] = {}
    for name, declared in target["paths"].items():
        alpha = float(declared["alpha"])
        result = FixedAlphaMbp4Kernel(Mbp4Spec(alpha=alpha, schedule=settings["schedule"], max_iterations=int(target["observation_horizon"]["sweeps"]))).new_session(
            original, priors, budgets=BudgetTree(limits=(BudgetLimit("attempt", "bp_calls", int(target["observation_horizon"]["sweeps"])),), parents={}),
        ).run()
        sweeps = [
            {"iteration": sweep.iteration, "candidate": sweep.candidate.tolist(), "beliefs_sha256": sha256(_canonical_bytes(sweep.beliefs.tolist())).hexdigest(), "syndrome": code.syndrome(sweep.candidate).tolist(), "work": sweep.work.as_evidence(structural_event_version=4)}
            for sweep in result.sweeps
        ]
        expected = declared["expected_trajectory"]
        if [{key: step[key] for key in ("iteration", "candidate", "beliefs_sha256")} for step in sweeps] != expected:
            raise ValueError(f"MBP4 {name} trajectory differs from independent frozen oracle")
        frozen = PauliCandidate(f"candidate-phase11-mbp4-{name}", working, result.candidate, 0)
        evaluation = evaluate_pauli_candidate(frozen, hidden_truth=hidden)
        paths[name] = {
            "alpha": alpha, "relation": declared["expected_relation"], "termination": result.termination,
            "candidate": result.candidate.tolist(), "sweeps": sweeps, "work": result.work.as_evidence(structural_event_version=4),
            "original_problem_evaluation": {"outcome": evaluation.outcome, "logical_action": evaluation.logical_action, "logical_action_unavailable_reason": evaluation.logical_action_unavailable_reason},
        }
    if paths["alpha_one"]["termination"] != "max_iterations" or paths["alpha_one_point_five"]["termination"] != "converged":
        raise ValueError("MBP4 paths do not preserve the frozen oscillation/convergence contrast")
    if paths["alpha_one_point_five"]["original_problem_evaluation"]["outcome"] != "exact":
        raise ValueError("MBP4 alpha=1.5 did not recover the source error under independent evaluation")
    return {"paths": paths, "source_settings": settings, "problem": problem_data}


def _mbp4_assessment(target: dict[str, Any], target_document_sha256: str) -> dict[str, Any]:
    ledger = _mbp4_evidence(target)
    replay = _mbp4_evidence(target)
    ledger_bytes, replay_bytes = _canonical_bytes(ledger), _canonical_bytes(replay)
    if ledger_bytes != replay_bytes:
        raise ValueError("MBP4 deterministic replay ledger bytes differ")
    payload = {
        "schema": "phase11-mbp4-figures8-9-five-qubit-assessment-v1", "status": "deterministic_mechanism_assessed",
        "target_receipt_sha256": target["target_receipt_sha256"], "target_document_sha256": target_document_sha256,
        "run_fidelity": "canonical_adaptation", "source_fidelity": "not_promoted", "admitted_shots": 2,
        "claim_scope": _MBP4_SCOPE, "ledger": ledger,
        "evidence_kind": "deterministic_mechanism",
        "source_denominator": {
            "status": "not_applicable",
            "reason": "finite deterministic trace has no stochastic trial denominator",
        },
        "stopping": {"kind": "frozen_sweeps", "sweeps": int(target["observation_horizon"]["sweeps"])},
        "claim_limits": {
            "curve": "ineligible",
            "decoder_ranking": "ineligible",
            "paper_performance": "ineligible",
            "threshold": "ineligible",
        },
        "alpha_only_contrast": target["alpha_only_contrast"],
        "blocked_targets": {"figure6": {"status": "blocked_metadata", "missing_metadata": _FIGURE6_MISSING, "assessment": "not_admitted"}},
        "deterministic_replay": {"ledger_sha256": sha256(ledger_bytes).hexdigest(), "replay_ledger_sha256": sha256(replay_bytes).hexdigest()},
    }
    payload["assessment_sha256"] = sha256(_canonical_bytes(payload)).hexdigest()
    return payload


def _blocked_assessment(
    target: QuaternarySourceTargetV1,
    target_document_sha256: str,
    *,
    native_qualification_path: Path | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any]:
    native_reference = _asced_native_reference(native_qualification_path)
    authorization = _source_dispatch_authorization(authorization_path)
    members = []
    for member in target.members:
        if member.eligibility != "blocked_metadata":
            raise ValueError("non-blocked execution is not authorized by this source-study entry point")
        members.append({
            "member_id": member.member_id,
            "target_slot": member.target_slot,
            "status": "blocked_metadata",
            "admitted_shots": 0,
            "blockers": list(member.blockers),
            "discrepancy": "not_assessed_due_to_blocked_source_metadata",
            "canonical_adaptation": {
                "eligibility": "blocked",
                "fidelity": "canonical_adaptation",
                "dispatch_attempted": False,
                "failed_gates": [*member.blockers, *authorization["failed_gates"]],
            },
            "matched_native": native_reference,
        })
    payload = {
        "schema": "phase11-asced-source-assessment-v1",
        "status": "blocked_metadata",
        "target_receipt_sha256": target.digest(),
        "target_document_sha256": target_document_sha256,
        "run_fidelity": "canonical_adaptation",
        "source_fidelity": "not_promoted",
        "admitted_shots": 0,
        "authorization": authorization,
        "members": members,
    }
    payload["assessment_sha256"] = sha256(_canonical_bytes(payload)).hexdigest()
    return payload


def _qbpgd_assessment(
    target: dict[str, Any],
    target_document_sha256: str,
    *,
    authorization_path: Path | None = None,
) -> dict[str, Any]:
    payload = {
        "schema": "phase11-qbpgd-source-assessment-v1",
        "status": "inconclusive",
        "target_receipt_sha256": _receipt_digest(target),
        "target_document_sha256": target_document_sha256,
        "run_fidelity": "canonical_adaptation",
        "source_fidelity": "not_promoted",
        "admitted_shots": 0,
        "qualification_blockers": list(target["qualification_blockers"]),
        "discrepancy": "not_assessed_due_to_unresolved_figure_coordinates_and_author_identity",
    }
    if authorization_path is not None:
        authorization = _source_dispatch_authorization(authorization_path)
        payload["authorization"] = authorization
        payload["source_stopping"] = target["source_stopping"]
        payload["canonical_adaptation"] = {
            "eligibility": "blocked",
            "fidelity": "canonical_adaptation",
            "dispatch_attempted": False,
            "failed_gates": [*target["qualification_blockers"], *authorization["failed_gates"]],
        }
    payload["assessment_sha256"] = sha256(_canonical_bytes(payload)).hexdigest()
    return payload


def _run_qbpgd_qualification(target: dict[str, Any]) -> dict[str, Any]:
    """Run one bounded deterministic canonical shot without creating a curve verdict."""
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.quaternary.problems import QuaternaryOriginalProblem, construct_qbpgd_a5_css
    from bp_registry.quaternary.qbpgd import QbpgdController, QbpgdSpec, ScalarLlrBp4Kernel, reconstruct_qbpgd

    limits = target["bounded_qualification"]
    started = time.monotonic()
    code, _receipt = construct_qbpgd_a5_css()
    p = float(limits["depolarizing_p"])
    rng = np.random.default_rng(np.random.SeedSequence([11, 2, int(limits["shot_id"])]))
    hidden = rng.choice(4, size=code.n, p=[1.0 - p, p / 3.0, p / 3.0, p / 3.0]).astype(np.uint8)
    problem = QuaternaryOriginalProblem(
        lineage_id="original-phase11-qbpgd-a5-qualification-000",
        code=code,
        syndrome=code.syndrome(hidden),
    )
    priors = np.repeat(np.asarray([[1.0 - p, p / 3.0, p / 3.0, p / 3.0]], dtype=np.float64), code.n, axis=0)
    spec = QbpgdSpec(iterations_per_round=int(limits["canonical_iterations_per_round"]), epsilon=1e-10, round_limit=1)
    budgets = (BudgetLimit("attempt", "bp_calls", int(limits["max_bp_calls"])),)
    result = QbpgdController(spec).run(ScalarLlrBp4Kernel().new_session(problem, priors, budgets=BudgetTree(limits=budgets, parents={})))
    elapsed = time.monotonic() - started
    if elapsed > float(limits["max_wall_seconds"]):
        raise ValueError("Q-BPGD qualification exceeded frozen wall-time cap")
    # ``reconstruct_qbpgd`` performs the complete evidence comparison and
    # raises on any transition, fidelity, or typed-work disagreement.
    reconstruct_qbpgd(spec, problem, priors, result, budget_limits=budgets)
    rounds = [
        {
            "index": round_.index,
            "sweeps": len(round_.sweeps),
            "ranking_scan_count": len(round_.eligibility_set) if round_.selection_leaf is not None else 0,
            "selection_leaf": round_.selection_leaf,
            "fixation_leaf": round_.fixation_leaf,
            "original_check_leaf": round_.original_check_leaf,
            "terminal_reason": round_.terminal_reason,
        }
        for round_ in result.rounds
    ]
    evidence = {
        "shot_id": limits["shot_id"],
        "execution_kind": "one-sweep_canonical_adaptation_qualification_probe",
        "limitation": limits["limitation"],
        "hidden_truth_sha256": sha256(hidden.tobytes()).hexdigest(),
        "termination": result.termination,
        "rounds": rounds,
        "work": result.work.as_evidence(structural_event_version=4),
        "elapsed_seconds": elapsed,
        "replay": "passed",
        "performance_verdict": "not_assessed",
    }
    if len(rounds) > int(limits["max_events"]) or len(_canonical_bytes(evidence)) > int(limits["max_storage_bytes"]):
        raise ValueError("Q-BPGD qualification exceeded frozen event or storage cap")
    return evidence


def preflight(
    target_path: Path,
    manifest_path: Path | None,
    assessment_path: Path,
    *,
    native_qualification_path: Path | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any]:
    target, _manifest, document_digest = _validated(target_path, manifest_path)
    if isinstance(target, dict) and target.get("schema") == _MBP4_SCHEMA:
        assessment = _mbp4_assessment(target, document_digest)
    else:
        assessment = _qbpgd_assessment(target, document_digest, authorization_path=authorization_path) if isinstance(target, dict) else _blocked_assessment(
            target, document_digest,
            native_qualification_path=native_qualification_path,
            authorization_path=authorization_path,
        )
    assessment_path.parent.mkdir(parents=True, exist_ok=True)
    assessment_path.write_bytes(_canonical_bytes(assessment) + b"\n")
    return assessment


def verify(
    target_path: Path,
    manifest_path: Path | None,
    assessment_path: Path,
    *,
    native_qualification_path: Path | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any]:
    target, _manifest, document_digest = _validated(target_path, manifest_path)
    assessment = _load(assessment_path)
    if isinstance(target, dict) and target.get("schema") == _MBP4_SCHEMA:
        expected = _mbp4_assessment(target, document_digest)
    else:
        expected = _qbpgd_assessment(target, document_digest, authorization_path=authorization_path) if isinstance(target, dict) else _blocked_assessment(
            target, document_digest,
            native_qualification_path=native_qualification_path,
            authorization_path=authorization_path,
        )
    if assessment == expected:
        return assessment
    if not isinstance(target, dict) or assessment.get("preflight") != expected:
        raise ValueError("assessment digest or blocked source evidence drifted")
    return assessment


def run(
    target_path: Path,
    manifest_path: Path | None,
    assessment_path: Path,
    *,
    native_qualification_path: Path | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any]:
    target, _manifest, document_digest = _validated(target_path, manifest_path)
    if isinstance(target, dict) and target.get("schema") == _MBP4_SCHEMA:
        result = _mbp4_assessment(target, document_digest)
        assessment_path.parent.mkdir(parents=True, exist_ok=True)
        assessment_path.write_bytes(_canonical_bytes(result) + b"\n")
        return result
    if isinstance(target, dict):
        preflight_receipt = _qbpgd_assessment(target, document_digest, authorization_path=authorization_path)
        if authorization_path is not None:
            assessment_path.parent.mkdir(parents=True, exist_ok=True)
            assessment_path.write_bytes(_canonical_bytes(preflight_receipt) + b"\n")
            return preflight_receipt
        evidence = _run_qbpgd_qualification(target)
        result = {**preflight_receipt, "admitted_shots": 1, "qualification": evidence, "preflight": preflight_receipt}
        result["assessment_sha256"] = sha256(_canonical_bytes({key: value for key, value in result.items() if key != "assessment_sha256"})).hexdigest()
        assessment_path.parent.mkdir(parents=True, exist_ok=True)
        assessment_path.write_bytes(_canonical_bytes(result) + b"\n")
        return result
    assessment = _blocked_assessment(
        target, document_digest,
        native_qualification_path=native_qualification_path,
        authorization_path=authorization_path,
    )
    if assessment["status"] == "blocked_metadata":
        raise ValueError("source assessment is blocked_metadata; sampling is not admitted")
    raise ValueError("unreachable source-study execution state")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "assess", "verify"))
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--native-qualification", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--assessment", type=Path, required=True)
    args = parser.parse_args()
    try:
        # aSCED's checked-in receipt is an assessment of its source lane, so
        # its default lifecycle must bind the independently retained native
        # terminal and sealed dispatch decision rather than silently dropping
        # them when an older caller omits the optional CLI paths.
        is_asced_target = _load(args.target).get("schema") == "campaign_quaternary_source_target_v1"
        native_qualification = args.native_qualification
        authorization = args.authorization
        if is_asced_target:
            native_qualification = native_qualification or DEFAULT_ASCED_NATIVE_QUALIFICATION
            authorization = authorization or DEFAULT_SOURCE_AUTHORIZATION
        if args.command in {"preflight", "assess"}:
            result = preflight(
                args.target, args.manifest, args.assessment,
                native_qualification_path=native_qualification,
                authorization_path=authorization,
            )
        elif args.command == "verify":
            result = verify(
                args.target, args.manifest, args.assessment,
                native_qualification_path=native_qualification,
                authorization_path=authorization,
            )
        else:
            result = run(
                args.target, args.manifest, args.assessment,
                native_qualification_path=native_qualification,
                authorization_path=authorization,
            )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error
    print(json.dumps({"status": result["status"], "admitted_shots": result["admitted_shots"]}, sort_keys=True))


if __name__ == "__main__":
    main()
