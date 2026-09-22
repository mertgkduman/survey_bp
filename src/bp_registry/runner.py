"""One-shot source-linked tracer for the project CSS smoke fixture."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .css import fixture_code
from .ledger import Writer
from .manifests import manifest_digest, preflight
from . import evaluator, reference, sampling


@dataclass(frozen=True)
class ShotResult:
    run_id: str
    shot_id: int
    outcome: str
    converged: bool
    iterations: int


def run_one(manifest_path: str | Path, *, shot_id: int, ledger_path: str | Path) -> ShotResult:
    manifest = preflight(manifest_path)
    code = fixture_code()
    digest = manifest_digest(manifest)
    common = {
        "manifest_sha256": digest,
        "source_uri": manifest.source_uri,
        "source_revision": manifest.source_revision,
        "source_anchor": manifest.source_anchor,
        "code_id": manifest.code_id,
        "experiment_relation": manifest.experiment_relation,
        "expected_output_status": manifest.expected_output_status,
    }
    with Writer(ledger_path) as ledger:
        ledger.begin(run_id=manifest.run_id, shot_id=shot_id, **common)
        try:
            sample = sampling.sample_shot(
                code, manifest_identity=digest, seed=manifest.seed, shot_id=shot_id,
                x_error_rate=manifest.x_error_rate,
            )
            native = reference.decode(
                code.hz, sample.observation.syndrome, error_rate=manifest.x_error_rate,
                max_iter=manifest.max_iter, bp_method=manifest.bp_method,
                schedule=manifest.schedule, input_vector_type=manifest.input_vector_type,
            )
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
                outcome=evaluation.outcome, logical_action_agrees=evaluation.logical_action_agrees,
                postselection="none",
            )
            return ShotResult(
                manifest.run_id, shot_id, evaluation.outcome, native.converged, native.iterations
            )
        except Exception as exc:
            ledger.terminal(run_id=manifest.run_id, shot_id=shot_id, **common,
                            termination="exception", exception_type=type(exc).__name__,
                            exception_message=str(exc), outcome=None)
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
