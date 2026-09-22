"""One-shot source-linked tracer for the project CSS smoke fixture."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .css import classify, fixture_code, sample_x, syndrome_x
from .ledger import Writer
from .manifests import manifest_digest, preflight
from . import reference


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
            truth = sample_x(code, seed=manifest.seed, shot_id=shot_id, rate=manifest.x_error_rate)
            syndrome = syndrome_x(code, truth)
            native = reference.decode(
                code.hz, syndrome, error_rate=manifest.x_error_rate,
                max_iter=manifest.max_iter, bp_method=manifest.bp_method,
                schedule=manifest.schedule, input_vector_type=manifest.input_vector_type,
            )
            outcome = classify(code, true_error=truth, candidate=native.candidate)
            ledger.terminal(
                run_id=manifest.run_id, shot_id=shot_id, **common,
                termination="completed", observation_check_type="Z",
                syndrome=syndrome.tolist(), hidden_x=truth.tolist(),
                candidate=native.candidate.tolist(), native_converged=native.converged,
                native_iterations=native.iterations, native_edge_updates=None,
                native_edge_updates_missing_reason=native.edge_updates_missing_reason,
                outcome=outcome, postselection="none",
            )
            return ShotResult(manifest.run_id, shot_id, outcome, native.converged, native.iterations)
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
