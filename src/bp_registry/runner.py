"""One-shot source-linked tracer for the project CSS smoke fixture."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
from typing import Any

from .ledger import Writer
from .manifests import ManifestV1, manifest_digest, preflight
from . import evaluator, reference, sampling


@dataclass(frozen=True)
class ShotResult:
    run_id: str
    shot_id: int
    outcome: str
    converged: bool
    iterations: int


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
    artifact_path = str((Path(manifest.artifact.root) / manifest.artifact.path).resolve())
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
            native = reference.decode(
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
