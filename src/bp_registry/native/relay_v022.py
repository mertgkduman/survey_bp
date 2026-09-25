"""Strict translation envelope for the approved Relay-BP v0.2.2 source.

This module never imports ``relay_bp`` by name.  The editable local fork has
that import name, so importing it here would silently substitute a different
implementation for the approved author revision.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np


AUTHOR_REPOSITORY = "https://github.com/trmue/relay.git"
AUTHOR_TAG = "v0.2.2"
AUTHOR_COMMIT = "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
AUTHOR_TREE = "5f6f112429e62112ba71fbff45f4e16247725fbc"
_PROFILES = {"f32": "RelayDecoderF32", "f64": "RelayDecoderF64"}
_SETTINGS = {
    "alpha", "alpha_iteration_scaling_factor", "gamma0", "data_scale_value",
    "max_data_value", "pre_iter", "num_sets", "set_max_iter",
    "gamma_dist_interval", "explicit_gammas", "stop_nconv",
    "stopping_criterion", "logging",
}
_TERMINAL_FIELDS = (
    "candidate", "success", "score", "aggregate_iterations", "final_posterior", "log_output",
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _binary(value: object, *, name: str, dimensions: int) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != dimensions or not np.all((array == 0) | (array == 1)):
        raise ValueError(f"{name} must be a {dimensions}-dimensional binary array")
    return np.ascontiguousarray(array, dtype=np.uint8)


@dataclass(frozen=True)
class RelayV022Result:
    """Only terminal facts observed through the approved native call."""

    candidate: np.ndarray
    success: bool
    score: float | None
    aggregate_iterations: int | None
    final_posterior: np.ndarray | None
    log_output: str


class RelayV022Adapter:
    """Translate decoder-visible CSS inputs to the pinned author API.

    ``native_runner`` is deliberately injected by the isolated build runner.
    This blocks an accidental import of the installed mg551-duke fork.
    """

    def __init__(
        self,
        *,
        source_record: str | Path | None = None,
        native_runner: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None,
    ) -> None:
        self.source_record = Path(source_record) if source_record else _repository_root() / "data/evidence/relay-v0.2.2-source.json"
        self.native_runner = native_runner

    @staticmethod
    def verify_source_identity(record: Mapping[str, object]) -> None:
        if record.get("author_repository") != AUTHOR_REPOSITORY:
            raise ValueError("author repository does not match the approved Relay source")
        if record.get("author_tag") != AUTHOR_TAG or record.get("author_commit") != AUTHOR_COMMIT:
            raise ValueError("author commit does not match approved v0.2.2 pin")
        if record.get("author_tree") != AUTHOR_TREE:
            raise ValueError("author tree does not match approved v0.2.2 pin")
        identities = record.get("identities")
        if not isinstance(identities, Mapping):
            raise ValueError("source record omits separate author/main/fork identities")
        author = identities.get("author_release")
        fork = identities.get("installed_fork")
        moving = identities.get("author_moving_main")
        if not isinstance(author, Mapping) or author.get("commit") != AUTHOR_COMMIT:
            raise ValueError("source record does not identify the author release")
        if not isinstance(fork, Mapping) or not isinstance(moving, Mapping):
            raise ValueError("source record omits fork or moving-main identity")

    def translate(
        self,
        *,
        check_matrix: object,
        syndrome: object,
        error_priors: object,
        relay_settings: Mapping[str, object],
        seed: int,
        numerical_profile: str,
    ) -> dict[str, object]:
        matrix = _binary(check_matrix, name="check_matrix", dimensions=2)
        observed = _binary(syndrome, name="syndrome", dimensions=1)
        priors = np.asarray(error_priors, dtype=np.float64)
        if matrix.shape[0] != observed.shape[0] or matrix.shape[1] != priors.shape[0]:
            raise ValueError("check matrix, syndrome, and priors dimensions disagree")
        if priors.ndim != 1 or not np.isfinite(priors).all() or np.any((priors <= 0) | (priors >= 1)):
            raise ValueError("error_priors must be finite probabilities strictly between zero and one")
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        if numerical_profile not in _PROFILES:
            raise ValueError("numerical_profile must be explicit f32 or f64; paper-faithful is unspecified")
        unknown = set(relay_settings).difference(_SETTINGS)
        if unknown:
            raise ValueError(f"unsupported Relay v0.2.2 settings: {sorted(unknown)}")
        settings = dict(relay_settings)
        settings.setdefault("logging", False)
        settings["seed"] = seed
        return {
            "decoder_class": _PROFILES[numerical_profile],
            "check_matrix": matrix,
            "syndrome": observed,
            "error_priors": np.ascontiguousarray(priors),
            "relay_settings": settings,
            "seed": seed,
            "numerical_profile": numerical_profile,
        }

    def run(self, **visible_inputs: object) -> RelayV022Result:
        if not self.source_record.is_file():
            raise RuntimeError("native qualification record is unavailable")
        record = json.loads(self.source_record.read_text(encoding="utf-8"))
        self.verify_source_identity(record)
        qualification = record.get("qualification")
        if not isinstance(qualification, Mapping) or qualification.get("passed") is not True:
            raise RuntimeError("native qualification has not passed")
        if self.native_runner is None:
            raise RuntimeError("an isolated exact-author native runner is required")
        translated = self.translate(**visible_inputs)
        raw = self.native_runner(translated)
        candidate = _binary(raw.get("candidate"), name="candidate", dimensions=1)
        posterior = raw.get("final_posterior")
        return RelayV022Result(
            candidate=candidate,
            success=bool(raw.get("success")),
            score=None if raw.get("score") is None else float(raw["score"]),
            aggregate_iterations=None if raw.get("aggregate_iterations") is None else int(raw["aggregate_iterations"]),
            final_posterior=None if posterior is None else np.asarray(posterior, dtype=np.float64),
            log_output=str(raw.get("log_output", "")),
        )


def observer_patch_identity(path: str | Path | None = None) -> dict[str, str]:
    patch = Path(path) if path else _repository_root() / "native/relay-v0.2.2-observer.patch"
    payload = patch.read_bytes()
    if b"Base-Commit: 14cb31a18f9b9d7d099791b793e35b8a2951f8f3" not in payload:
        raise ValueError("observer patch is not bound to the approved author commit")
    return {"base_commit": AUTHOR_COMMIT, "patch_sha256": sha256(payload).hexdigest()}


def assert_terminal_equivalence(unmodified: Mapping[str, object], patched: Mapping[str, object]) -> bool:
    for field in _TERMINAL_FIELDS:
        if field not in unmodified or field not in patched:
            raise ValueError(f"terminal field {field} is absent")
        left, right = unmodified[field], patched[field]
        if isinstance(left, (list, tuple, np.ndarray)) or isinstance(right, (list, tuple, np.ndarray)):
            equal = np.array_equal(np.asarray(left), np.asarray(right), equal_nan=True)
        else:
            equal = left == right
        if not equal:
            raise ValueError(f"terminal field differs: {field}")
    return True


def unavailable_native_facts() -> dict[str, str]:
    return {
        "gamma": "unavailable: observer would change decoder behavior",
        "edge_work": "unavailable: observer would change decoder behavior",
        "resource": "unavailable: observer would change decoder behavior",
    }
