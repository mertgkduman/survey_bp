"""Truth-sealed canonical CSS shot orchestration and durable terminal evidence."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Callable

import numpy as np

from .. import evaluator
from ..css import CssCode
from ..ledger import LedgerWriter, ShotOwnershipError, reconcile
from ..sampling import DecoderObservation, HiddenTruth
from .contracts import CanonicalManifestV2, parse_canonical_manifest
from .kernel import BinarySpaKernel
from .numerics import NumericalFailure


class CanonicalConflictError(ValueError):
    """A stable run/shot key was reused with different canonical content."""


@dataclass(frozen=True)
class CanonicalExecutionResult:
    run_id: str
    shot_id: int
    termination: str
    evaluation: evaluator.Evaluation | None
    candidate: np.ndarray | None


def _identity(manifest: CanonicalManifestV2, observation: DecoderObservation) -> str:
    payload = {"manifest": manifest.model_dump(mode="json"), "check_type": observation.check_type,
               "syndrome": np.asarray(observation.syndrome, dtype=np.uint8).tolist()}
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _existing(path: Path, run_id: str, shot_id: int, identity: str) -> CanonicalExecutionResult | None:
    if not path.exists():
        return None
    for row in reconcile(path):
        if row["run_id"] == run_id and row["shot_id"] == shot_id:
            if row.get("canonical_identity") != identity:
                raise CanonicalConflictError("conflicting canonical content for run/shot identity")
            outcome = row.get("outcome")
            evaluation = evaluator.Evaluation(outcome, row.get("logical_action_agrees")) if outcome else None
            candidate = row.get("candidate")
            return CanonicalExecutionResult(run_id, shot_id, row["termination"], evaluation,
                                            None if candidate is None else np.asarray(candidate, dtype=np.uint8))
    return None


def run_canonical_shot(manifest: CanonicalManifestV2 | dict[str, object] | str, *, code: CssCode,
                       observation: DecoderObservation, hidden_truth: HiddenTruth, shot_id: int,
                       ledger_path: str | Path, evaluate: Callable[..., evaluator.Evaluation] = evaluator.evaluate_candidate) -> CanonicalExecutionResult:
    """Run decoder-visible work first; only this outer function receives hidden truth."""
    parsed = parse_canonical_manifest(manifest)
    if type(shot_id) is not int or shot_id < 0 or observation.check_type != "Z":
        raise ValueError("canonical tracer accepts a nonnegative Z-check shot")
    validated = code.validate()
    identity = _identity(parsed, observation)
    path = Path(ledger_path)
    existing = _existing(path, parsed.run_id, shot_id, identity)
    if existing is not None:
        return existing
    for attempt in range(30):
        try:
            with LedgerWriter(path) as ledger:
                ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=identity,
                             canonical_identity=identity, decoder_config=parsed.model_dump(mode="json"))
                try:
                    kernel_result = BinarySpaKernel().run(validated.hz, observation.syndrome,
                                                          error_rate=parsed.error_rate, max_iterations=parsed.max_iterations)
                except NumericalFailure as error:
                    ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, canonical_identity=identity,
                                    termination="numerical_failure", numerical_failure=str(error),
                                    selection_status="unavailable_due_to_numerical_failure", outcome=None)
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "numerical_failure", None, None)
                frozen_candidate = np.array(kernel_result.candidate, dtype=np.uint8, copy=True)
                frozen_candidate.setflags(write=False)
                evaluation_result = evaluate(validated, true_x=hidden_truth.x, true_z=hidden_truth.z,
                                             candidate_x=frozen_candidate)
                ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, canonical_identity=identity,
                                termination="completed", candidate=frozen_candidate.tolist(),
                                iterations=kernel_result.iterations, converged=kernel_result.converged,
                                selection_status="frozen_decoder_visible_candidate", outcome=evaluation_result.outcome,
                                logical_action_agrees=evaluation_result.logical_action_agrees)
                return CanonicalExecutionResult(parsed.run_id, shot_id, "completed", evaluation_result, frozen_candidate)
        except ShotOwnershipError:
            time.sleep(0.01)
            existing = _existing(path, parsed.run_id, shot_id, identity)
            if existing is not None:
                return existing
    raise ShotOwnershipError("canonical shot remained owned beyond bounded retry window")
