"""One-shot source-linked tracer for the project CSS smoke fixture."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
from typing import Any

from .ledger import Writer, read_canonical_events
from .canonical.metrics import unavailable_metric
from .canonical.execution import run_canonical_structural_shot
from .canonical.verification import PublicShotContext
from .canonical.numerics import MIN_SUM_CPU_F64, REFERENCE_CPU_F64
from .canonical.schedules import EdgeTable
from .manifests import (
    CanonicalExperimentV2,
    CanonicalExperimentV3,
    ManifestV1,
    executable_canonical_policy_effects,
    manifest_digest,
    preflight,
    validate_executable_canonical_baseline,
)
from . import evaluator, sampling


def _native_reference():
    """Load the optional native adapter only for explicit native execution."""
    from . import reference

    return reference


def __getattr__(name: str):
    """Retain lazy compatibility for callers using runner.reference."""
    if name == "reference":
        return _native_reference()
    raise AttributeError(name)


@dataclass(frozen=True)
class ShotResult:
    run_id: str
    shot_id: int
    outcome: str
    converged: bool
    iterations: int


def _unavailable_native_metric_facts(stage: str) -> list[dict[str, int | float | str | None]]:
    """Retain missing native instrumentation after an unsuccessful terminal."""
    reason = f"native instrumentation unavailable because {stage} raised before a native result was retained"
    return [
        unavailable_metric(
            metric, method="runner.run_one", scope="native_decoder_call", unit=unit,
            qualification="terminal_not_observed", reason=reason,
        ).as_evidence()
        for metric, unit in (
            ("native_iterations", "native_iterations"),
            ("native_edge_updates", "edge_messages"),
            ("native_control_flow_events", "events"),
        )
    ]


_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SELECTED_PROVENANCE = _REPOSITORY_ROOT / "data/artifacts/selected-css.provenance.json"


def preflight_pilot(manifest_path: str | Path) -> dict[str, Any]:
    """Resolve the one Phase 1 selected-artifact pilot before native execution."""

    manifest = preflight(manifest_path).manifest
    if not isinstance(manifest, ManifestV1):
        raise ValueError("selected artifact pilot requires a complete ManifestV1")
    provenance = json.loads(_SELECTED_PROVENANCE.read_text(encoding="utf-8"))
    artifact = provenance["artifact"]
    source = provenance["source"]
    expected_path = _REPOSITORY_ROOT / artifact["path"]
    actual_path = (Path(manifest.artifact.root) / manifest.artifact.path).resolve()
    if (
        manifest.run_id != "gross-bb144-pilot"
        or manifest.artifact.code_id != provenance["code_id"]
        or actual_path != expected_path.resolve()
        or manifest.artifact.raw_sha256 != artifact["raw_sha256"]
        or manifest.artifact.semantic_sha256 != artifact["semantic_sha256"]
        or manifest.paper.uri != "https://arxiv.org/html/2606.18240v1"
        or manifest.paper.revision != "v1"
        or manifest.implementation.repository_uri != source["repository"]
        or manifest.implementation.revision != source["revision"]
        or manifest.implementation.source_path != source["source_file"]
        or manifest.implementation.source_artifact_sha256 != source["source_file_sha256"]
    ):
        raise ValueError("manifest is not bound to the selected artifact provenance")
    if manifest.paper.relation != "pilot_adaptation":
        raise ValueError("selected artifact run must remain a pilot_adaptation")
    if manifest.expected_output.status != "not_assessed":
        raise ValueError("selected artifact run must remain not_assessed")
    return {
        "run_id": manifest.run_id,
        "code_id": manifest.artifact.code_id,
        "relation": manifest.paper.relation,
        "assessment_status": manifest.expected_output.status,
        "assessment_reason": manifest.expected_output.reason,
        "paper_revision": manifest.paper.revision,
        "paper_uri": manifest.paper.uri,
        "implementation_revision": manifest.implementation.revision,
        "implementation_uri": manifest.implementation.repository_uri,
        "artifact_raw_sha256": manifest.artifact.raw_sha256,
        "artifact_semantic_sha256": manifest.artifact.semantic_sha256,
        "shot_budget": manifest.budget.max_shots,
        "max_iter": manifest.budget.max_iter,
    }


def preflight_canonical(manifest_path: str | Path) -> dict[str, Any]:
    """Resolve all canonical external facts before sampling or durable evidence."""
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    if not isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3)):
        raise ValueError("canonical execution requires a strict CanonicalExperimentV2 or V3 manifest")
    composition = validate_executable_canonical_baseline(manifest.policies)
    return {
        "run_id": manifest.run_id,
        "code_id": manifest.artifact.code_id,
        "manifest_sha256": manifest_digest(manifest),
        "numerical_profile": manifest.numerical_profile,
        "resolved_numerical_profile": (MIN_SUM_CPU_F64 if manifest.numerical_profile == "cpu-float64-min-sum-v1" else REFERENCE_CPU_F64).as_evidence(),
        "policies": manifest.policies.model_dump(mode="json"),
        "policy_identity": composition.semantic_identity,
        "policy_effects": _canonical_policy_effects(manifest, resolved.code),
        "shot_budget": manifest.budgets.max_shots,
        "max_iterations": manifest.budgets.attempt.max_iterations,
        "work_limits": {
            scope: getattr(manifest.budgets, scope).work_limits.as_evidence()
            for scope in ("shot", "search", "attempt")
        },
        "relation": manifest.evidence.relation,
        "fixture": manifest.evidence.fixture,
        "assessment_status": manifest.evidence.assessment_status,
        "profile_plan": manifest.profile_plan.model_dump(mode="json"),
        "trace_plan": manifest.trace_plan.model_dump(mode="json"),
    }


def _canonical_kernel_manifest(manifest: CanonicalExperimentV2 | CanonicalExperimentV3) -> dict[str, object]:
    """Project-owned kernel receives only its compact execution policy contract."""
    return {
        "schema_version": manifest.schema_version,
        "run_id": manifest.run_id,
        "numerical_profile": manifest.numerical_profile,
        "max_iterations": manifest.budgets.attempt.max_iterations,
        "error_rate": manifest.error_rate,
        "policies": manifest.policies.model_dump(mode="json"),
    }


def _canonical_policy_effects(manifest: CanonicalExperimentV2 | CanonicalExperimentV3, code) -> dict[str, dict[str, Any]]:
    """Bind declared NMS assignments to the code's canonical edge identities once."""
    effects: dict[str, dict[str, Any]] = executable_canonical_policy_effects(manifest.policies)
    assignment = getattr(manifest.policies.update, "parameter_assignment", None)
    generation = None
    if assignment is None and isinstance(manifest, CanonicalExperimentV3) and manifest.policies.update.parameter_generator is not None:
        from .canonical.updates import resolve_generated_configuration_assignment

        table = EdgeTable.from_check_matrix(code.hz)
        assignment, generation = resolve_generated_configuration_assignment(
            manifest.policies.update.model_dump(mode="json"), _canonical_kernel_manifest(manifest),
            graph_sha256=table.graph_sha256, check_count=table.check_count,
            edge_count=table.edge_count,
        )
    if assignment is not None:
        table = EdgeTable.from_check_matrix(code.hz)
        resolved = assignment.resolve(
            graph_sha256=table.graph_sha256, check_count=table.check_count, edge_count=table.edge_count,
            source_iteration=0, edge_checks=tuple(check for check, _variable in table.edges),
        )
        effects["update"] = {
            **effects["update"], "parameter_assignment": assignment.as_evidence(resolved),
            **({"parameter_generation": generation} if generation is not None else {}),
        }
    return effects


def _canonical_execution_controls(manifest: CanonicalExperimentV2 | CanonicalExperimentV3, code) -> dict[str, object]:
    """Keep preflighted public limits and handler classifications beside the compact kernel input."""
    return {
        "work_limits": {
            scope: getattr(manifest.budgets, scope).work_limits.as_evidence()
            for scope in ("shot", "search", "attempt")
        },
        "policy_effects": _canonical_policy_effects(manifest, code),
        "profile_plan": manifest.profile_plan.model_dump(mode="json"),
    }


def canonical_public_shot_context(manifest_path: str | Path, *, shot_id: int) -> PublicShotContext:
    """Resolve a deterministic public shot without opening a durable ledger."""
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    if not isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3)):
        raise ValueError("canonical execution requires a strict CanonicalExperimentV2 or V3 manifest")
    if type(shot_id) is not int or not 0 <= shot_id < manifest.budgets.max_shots:
        raise ValueError("shot_id is outside the canonical manifest budget")
    digest = manifest_digest(manifest)
    sample = sampling.sample_shot(
        resolved.code, manifest_identity=manifest.randomness.physical_sample_identity or digest,
        seed=manifest.randomness.sample_seed,
        shot_id=shot_id, x_error_rate=manifest.error_rate,
    )
    composition = validate_executable_canonical_baseline(manifest.policies)
    compact_manifest = _canonical_kernel_manifest(manifest)
    return PublicShotContext(
        manifest_sha256=digest,
        artifact_raw_sha256=manifest.artifact.raw_sha256,
        artifact_semantic_sha256=manifest.artifact.semantic_sha256,
        compact_manifest=compact_manifest,
        sample_seed_identity=sample.sample_identity,
        run_id=manifest.run_id,
        shot_id=shot_id,
        check_type=sample.observation.check_type,
        syndrome=tuple(int(value) for value in sample.observation.syndrome.tolist()),
        code_id=manifest.artifact.code_id,
        evidence_relation=manifest.evidence.relation,
        fixture=manifest.evidence.fixture,
        assessment_status=manifest.evidence.assessment_status,
        decoder_seed_identity=manifest.randomness.decoder_seed_identity,
        code=resolved.code,
        hidden_truth=sample.hidden,
        error_rate=manifest.error_rate,
        max_iterations=manifest.budgets.attempt.max_iterations,
        work_limits={
            scope: getattr(manifest.budgets, scope).work_limits.as_evidence()
            for scope in ("shot", "search", "attempt")
        },
        composition_identity=composition.semantic_identity,
        policy_effects=_canonical_policy_effects(manifest, resolved.code),
        profile_plan=manifest.profile_plan.model_dump(mode="json"),
        update_kind=manifest.policies.update.kind,
        schedule_kind=manifest.policies.schedule.kind,
    )


def run_canonical_one(manifest_path: str | Path, *, shot_id: int, ledger_path: str | Path):
    """Sample outside the engine, then evaluate only a frozen original-space candidate."""
    verification_context = canonical_public_shot_context(manifest_path, shot_id=shot_id)
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    assert isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3))
    digest = verification_context.manifest_sha256
    sample = sampling.sample_shot(
        resolved.code, manifest_identity=manifest.randomness.physical_sample_identity or digest,
        seed=manifest.randomness.sample_seed,
        shot_id=shot_id, x_error_rate=manifest.error_rate,
    )
    composition = validate_executable_canonical_baseline(manifest.policies)
    compact_manifest = _canonical_kernel_manifest(manifest)
    return run_canonical_structural_shot(
        compact_manifest, code=resolved.code, observation=sample.observation,
        hidden_truth=sample.hidden, shot_id=shot_id, ledger_path=ledger_path,
        sample_seed_identity=sample.sample_identity,
        verification_context=verification_context,
        execution_controls=_canonical_execution_controls(manifest, resolved.code),
        context={
            "manifest_sha256": digest,
            "artifact_raw_sha256": manifest.artifact.raw_sha256,
            "artifact_semantic_sha256": manifest.artifact.semantic_sha256,
            "code_id": manifest.artifact.code_id,
            "evidence_relation": manifest.evidence.relation,
            "fixture": manifest.evidence.fixture,
            "assessment_status": manifest.evidence.assessment_status,
            "decoder_seed_identity": manifest.randomness.decoder_seed_identity,
            "composition_identity": composition.semantic_identity,
            "execution_identity": verification_context.execution_identity,
        },
    )


def canonical_terminal_rows(ledger_path: str | Path, run_id: str) -> list[dict[str, Any]]:
    """Return only terminal structural evidence for one canonical run."""
    return sorted(
        (event for event in read_canonical_events(ledger_path)
         if event["run_id"] == run_id and event["kind"] == "termination"),
        key=lambda event: event["shot_id"],
    )


def run_one(manifest_path: str | Path, *, shot_id: int, ledger_path: str | Path) -> ShotResult:
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    if not isinstance(manifest, ManifestV1):
        raise ValueError("legacy manifests are read-only and cannot execute")
    if not 0 <= shot_id < manifest.budget.max_shots:
        raise ValueError("shot_id is outside the manifest budget")
    code = resolved.code
    digest = manifest_digest(manifest)
    source_uri = manifest.implementation.repository_uri
    source_revision = manifest.implementation.revision
    source_anchor = manifest.implementation.source_path
    code_id = manifest.artifact.code_id
    experiment_relation = manifest.paper.relation
    expected_output_status = manifest.expected_output.status
    x_error_rate = manifest.noise.x_error_rates[0]
    seed = manifest.seed_policy.root_seed
    max_iter = manifest.budget.max_iter
    bp_method = manifest.decoder.bp_method
    schedule = manifest.decoder.schedule
    input_vector_type = manifest.decoder.input_vector_type
    decoder_version = manifest.decoder.version
    artifact_raw_sha256 = manifest.artifact.raw_sha256
    artifact_semantic_sha256 = manifest.artifact.semantic_sha256
    artifact_path = str(Path(manifest.artifact.root) / manifest.artifact.path)
    common = {
        "manifest_sha256": digest,
        "source_uri": source_uri,
        "source_revision": source_revision,
        "source_anchor": source_anchor,
        "paper_uri": manifest.paper.uri,
        "paper_revision": manifest.paper.revision,
        "paper_anchor": manifest.paper.experiment_anchor,
        "implementation_source_artifact_sha256": manifest.implementation.source_artifact_sha256,
        "code_id": code_id,
        "experiment_relation": experiment_relation,
        "expected_output_status": expected_output_status,
        "decoder_config": {
            "bp_method": bp_method,
            "schedule": schedule,
            "input_vector_type": input_vector_type,
            "error_rate": x_error_rate,
            "max_iter": max_iter,
        },
        "decoder_version": decoder_version,
        "artifact_raw_sha256": artifact_raw_sha256,
        "artifact_semantic_sha256": artifact_semantic_sha256,
        "artifact_path": artifact_path,
    }
    sample_seed_identity = sha256(
        f"bp-registry-sample-v1\0{digest}\0{shot_id}".encode()
    ).hexdigest()
    with Writer(ledger_path) as ledger:
        ledger.begin(
            run_id=manifest.run_id, shot_id=shot_id,
            sample_seed_identity=sample_seed_identity, **common,
        )
        stage = "sampling"
        try:
            sample = sampling.sample_shot(
                code, manifest_identity=digest, seed=seed, shot_id=shot_id,
                x_error_rate=x_error_rate,
            )
            stage = "decoding"
            native = _native_reference().decode(
                code.hz, sample.observation.syndrome, error_rate=x_error_rate,
                max_iter=max_iter, bp_method=bp_method,
                schedule=schedule, input_vector_type=input_vector_type,
            )
            stage = "evaluation"
            evaluation = evaluator.evaluate_candidate(
                code, true_x=sample.hidden.x, true_z=sample.hidden.z,
                candidate_x=native.candidate,
            )
            ledger.terminal(
                run_id=manifest.run_id, shot_id=shot_id, **common,
                termination="completed", observation_check_type="Z",
                syndrome=sample.observation.syndrome.tolist(), sample_identity=sample.sample_identity,
                hidden_x=sample.hidden.x.tolist(), hidden_z=sample.hidden.z.tolist(),
                candidate=native.candidate.tolist(), native_converged=native.converged,
                native_iterations=native.iterations, native_edge_updates=None,
                native_metric_facts=[fact.as_evidence() for fact in native.metric_facts],
                native_edge_updates_missing_reason=native.edge_updates_missing_reason,
                native_internals_unavailable_reason=native.edge_updates_missing_reason,
                outcome=evaluation.outcome, logical_action_agrees=evaluation.logical_action_agrees,
                selected_output=native.candidate.tolist(), selection_status="native_bp_candidate",
                postselection="none", postselection_status="not_requested",
            )
            return ShotResult(
                manifest.run_id, shot_id, evaluation.outcome, native.converged, native.iterations
            )
        except Exception as exc:
            ledger.terminal(
                run_id=manifest.run_id, shot_id=shot_id, **common,
                termination="exception", exception_stage=stage,
                exception_type=type(exc).__name__, exception_message=str(exc),
                native_converged=None, native_iterations=None, native_edge_updates=None,
                native_metric_facts=_unavailable_native_metric_facts(stage),
                native_internals_unavailable_reason=(
                    f"native internals unavailable because {stage} raised before terminal evaluation"
                ),
                outcome=None, outcome_unavailable_reason=(
                    f"independent outcome unavailable because {stage} raised"
                ),
                selected_output=None, selection_status="unavailable_due_to_exception",
                postselection="unavailable",
            )
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--shot-id", type=int, default=0)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    result = run_one(args.manifest, shot_id=args.shot_id, ledger_path=args.ledger)
    print(f"{result.run_id} shot={result.shot_id} outcome={result.outcome} ",
          f"native_converged={result.converged} native_iterations={result.iterations}")


if __name__ == "__main__":
    main()
