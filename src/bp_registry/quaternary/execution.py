"""Bounded, replayable joint-Pauli BP tracer.

This deliberately small Phase 10 facade owns the non-CSS four-state boundary.
It has no dependency on CSS problem or binary kernel types: hidden truth remains
inside sampling/evaluation and the decoder receives only a syndrome and priors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from ..canonical.numerics import boxplus
from ..canonical.budgets import BudgetLimit, BudgetTree
from ..css import CssCode
from .asced import AscedController, AscedSpec, SplitterSearchExhausted, construct_splitter_batch, materialize_asced_batches
from .asced_overcomplete import OvercompleteSearchExhausted, construct_overcomplete_map
from .kernel import ScalarLlrBp4Kernel
from .mbp4 import FixedAlphaMbp4Kernel, Mbp4Spec
from .problems import PauliCode, QuaternaryOriginalProblem, compile_css_artifact
from .qbpgd import QbpgdController, QbpgdSpec


class PauliValue(IntEnum):
    """Persisted Pauli encoding.  Never infer this order from an array index."""

    I = 0
    X = 1
    Y = 2
    Z = 3


_BITS = np.asarray(((0, 0), (1, 0), (1, 1), (0, 1)), dtype=np.uint8)


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _readonly(value: object, *, shape: tuple[int, ...], name: str, values: set[int] | None = None) -> np.ndarray:
    result = np.asarray(value)
    if result.shape != shape or not np.issubdtype(result.dtype, np.integer):
        raise ValueError(f"{name} has an invalid shape")
    if values is not None and np.any(~np.isin(result, tuple(values))):
        raise ValueError(f"{name} contains invalid values")
    copy = np.array(result, dtype=np.uint8, copy=True)
    copy.setflags(write=False)
    return copy


@dataclass(frozen=True, slots=True)
class TracerPauliProblem:
    """Immutable original stabilizer rows and their measured syndrome order."""

    checks: np.ndarray
    syndrome: np.ndarray

    def __post_init__(self) -> None:
        checks = np.asarray(self.checks)
        if checks.ndim != 2 or checks.shape[0] == 0 or checks.shape[1] == 0:
            raise ValueError("quaternary problem requires nonempty checks and qubits")
        object.__setattr__(self, "checks", _readonly(checks, shape=checks.shape, name="checks", values={0, 1, 2, 3}))
        object.__setattr__(self, "syndrome", _readonly(self.syndrome, shape=(checks.shape[0],), name="syndrome", values={0, 1}))

    @property
    def n(self) -> int:
        return int(self.checks.shape[1])


@dataclass(frozen=True, slots=True)
class TracerQbpResult:
    """Decoder-visible output plus evaluator-only terminal classification."""

    candidate: np.ndarray
    marginals: np.ndarray
    work: dict[str, int]
    termination: str
    outcome: str
    logical_action_agrees: bool | None


def _commutes(left: int, right: int) -> bool:
    x1, z1 = _BITS[left]
    x2, z2 = _BITS[right]
    return bool((int(x1) * int(z2) + int(z1) * int(x2)) % 2 == 0)


def syndrome_for(problem: TracerPauliProblem, error: np.ndarray) -> np.ndarray:
    """Compute immutable-original stabilizer syndrome in declared check order."""
    candidate = _readonly(error, shape=(problem.n,), name="candidate", values={0, 1, 2, 3})
    answer = np.zeros(problem.checks.shape[0], dtype=np.uint8)
    for check in range(problem.checks.shape[0]):
        parity = 0
        for qubit, label in enumerate(problem.checks[check]):
            parity ^= int(not _commutes(int(label), int(candidate[qubit])))
        answer[check] = parity
    answer.setflags(write=False)
    return answer


def _validated_channel(probabilities: object, n: int) -> np.ndarray:
    table = np.asarray(probabilities, dtype=np.float64)
    if table.shape != (n, 4) or not np.all(np.isfinite(table)) or np.any(table < 0.0):
        raise ValueError("joint Pauli channel must be a finite nonnegative (n,4) table")
    if not np.allclose(table.sum(axis=1), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("joint Pauli channel rows must sum to one")
    return np.array(table, dtype=np.float64, copy=True)


def _sample(channel: np.ndarray, *, seed_identity: str) -> np.ndarray:
    seed = int.from_bytes(sha256(seed_identity.encode("utf-8")).digest()[:16], "big")
    rng = np.random.Generator(np.random.PCG64(seed))
    values = np.asarray([rng.choice(4, p=row) for row in channel], dtype=np.uint8)
    values.setflags(write=False)
    return values


def _llrs(channel: np.ndarray, epsilon: float) -> tuple[np.ndarray, np.ndarray]:
    if not 0.0 < epsilon < 0.25:
        raise ValueError("decoder smoothing epsilon must lie in (0, 0.25)")
    smoothed = np.maximum(channel, epsilon)
    smoothed /= smoothed.sum(axis=1, keepdims=True)
    values = np.log(smoothed[:, [0]] / smoothed[:, 1:])
    return values.astype(np.float64), smoothed


def _posterior(prior: np.ndarray, incoming: np.ndarray, checks: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    beliefs = np.array(prior, dtype=np.float64, copy=True)
    for edge, (check, qubit) in enumerate(_edges(checks)):
        label = int(checks[check, qubit])
        for state in (1, 2, 3):
            if not _commutes(state, label):
                beliefs[qubit, state - 1] += incoming[edge]
    log_weights = np.concatenate((np.zeros((beliefs.shape[0], 1)), -beliefs), axis=1)
    log_weights -= log_weights.max(axis=1, keepdims=True)
    probabilities = np.exp(log_weights)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    candidate = np.zeros(beliefs.shape[0], dtype=np.uint8)
    for qubit, row in enumerate(beliefs):
        if not np.all(row > 0.0):
            candidate[qubit] = np.uint8(1 + int(np.argmin(row)))
    return candidate, probabilities


def _edges(checks: np.ndarray) -> tuple[tuple[int, int], ...]:
    return tuple((check, qubit) for check in range(checks.shape[0]) for qubit in range(checks.shape[1]) if checks[check, qubit] != PauliValue.I)


def _decode(problem: TracerPauliProblem, *, channel: np.ndarray, max_iterations: int, max_work: int, epsilon: float) -> tuple[np.ndarray, np.ndarray, dict[str, int], str]:
    """Run scalar commutation-message flooding using decoder-visible inputs only."""
    prior, _ = _llrs(channel, epsilon)
    edges = _edges(problem.checks)
    if not edges:
        raise ValueError("quaternary problem needs at least one nonidentity edge")
    by_check = tuple(tuple(index for index, (check, _q) in enumerate(edges) if check == row) for row in range(problem.checks.shape[0]))
    v2c = np.empty((len(edges), 3), dtype=np.float64)
    for edge, (_check, qubit) in enumerate(edges):
        v2c[edge] = prior[qubit]
    work = {"check_to_variable_updates": 0, "variable_to_check_updates": 0, "belief_assemblies": 0, "candidate_checks": 0}
    candidate, marginals = _posterior(prior, np.zeros(len(edges), dtype=np.float64), problem.checks)
    for iteration in range(max_iterations):
        c2v = np.empty(len(edges), dtype=np.float64)
        for check, indexes in enumerate(by_check):
            for edge in indexes:
                factors: list[float] = []
                for other in indexes:
                    if other == edge:
                        continue
                    _other_check, qubit = edges[other]
                    label = int(problem.checks[check, qubit])
                    row = v2c[other]
                    weights = np.exp(np.asarray((0.0, -row[0], -row[1], -row[2])) - max(0.0, -row.min()))
                    commute = sum(weights[state] for state in range(4) if _commutes(state, label))
                    anticommute = sum(weights[state] for state in range(4) if not _commutes(state, label))
                    factors.append(float(np.log(commute / anticommute)))
                c2v[edge] = (-1.0 if problem.syndrome[check] else 1.0) * boxplus(np.asarray(factors, dtype=np.float64))
        work["check_to_variable_updates"] += len(edges)
        candidate, marginals = _posterior(prior, c2v, problem.checks)
        work["belief_assemblies"] += problem.n
        work["candidate_checks"] += problem.n
        if sum(work.values()) > max_work:
            return candidate, marginals, work, "work_budget_exhausted"
        if np.array_equal(syndrome_for(problem, candidate), problem.syndrome):
            return candidate, marginals, work, "completed"
        new_v2c = np.empty_like(v2c)
        for edge, (check, qubit) in enumerate(edges):
            for state in (1, 2, 3):
                new_v2c[edge, state - 1] = prior[qubit, state - 1] + sum(
                    c2v[other] for other, (other_check, other_qubit) in enumerate(edges)
                    if other_qubit == qubit and other != edge and not _commutes(state, int(problem.checks[other_check, qubit]))
                )
        v2c = np.clip(new_v2c, -50.0, 50.0)
        work["variable_to_check_updates"] += len(edges)
    return candidate, marginals, work, "max_iterations"


def _evaluate(problem: TracerPauliProblem, hidden: np.ndarray, candidate: np.ndarray) -> tuple[str, bool | None]:
    if not np.array_equal(syndrome_for(problem, candidate), problem.syndrome):
        return "invalid_syndrome", None
    if np.array_equal(hidden, candidate):
        return "exact", None
    # A general non-CSS logical basis is intentionally absent from this tracer.
    return "logical_failure", None


def _event(kind: str, data: Mapping[str, Any]) -> dict[str, Any]:
    plain = {"kind": kind, "data": dict(data)}
    return {**plain, "event_id": "qbp-" + _digest(plain)[:20]}


def _write_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")


def _manifest_parts(manifest: Any) -> tuple[TracerPauliProblem, np.ndarray, str, int, int, float, str]:
    payload = manifest.model_dump(mode="json") if hasattr(manifest, "model_dump") else manifest
    problem = TracerPauliProblem(np.asarray(payload["problem"]["checks"], dtype=np.uint8), np.asarray(payload["problem"]["syndrome"], dtype=np.uint8))
    channel = _validated_channel(payload["channel"]["probabilities"], problem.n)
    return problem, channel, str(payload["run_id"]), int(payload["max_iterations"]), int(payload["max_work"]), float(payload["channel"]["decoder_smoothing"]), _digest(payload)


def run_quaternary_tracer(manifest: Any, output: str | Path, *, shot_id: int = 0) -> TracerQbpResult:
    """Sample, decode, freeze, evaluate, and persist one bounded public shot."""
    problem, channel, run_id, iterations, max_work, epsilon, manifest_sha256 = _manifest_parts(manifest)
    if type(shot_id) is not int or shot_id != 0:
        raise ValueError("the bounded quaternary tracer only admits shot_id 0")
    # Sampling binds immutable physical controls, excluding the observed
    # syndrome itself so preflight does not create a circular seed definition.
    physical_identity = _digest({"checks": problem.checks.tolist(), "channel": channel.tolist(), "run_id": run_id})
    hidden = _sample(channel, seed_identity=f"{physical_identity}:shot:{shot_id}")
    measured = syndrome_for(problem, hidden)
    if not np.array_equal(measured, problem.syndrome):
        raise ValueError("manifest observation does not match its deterministic categorical sample")
    candidate, marginals, work, termination = _decode(problem, channel=channel, max_iterations=iterations, max_work=max_work, epsilon=epsilon)
    candidate = np.array(candidate, dtype=np.uint8, copy=True); candidate.setflags(write=False)
    marginals = np.array(marginals, dtype=np.float64, copy=True); marginals.setflags(write=False)
    outcome, logical = _evaluate(problem, hidden, candidate)
    events = [
        _event("preflight", {"run_id": run_id, "shot_id": shot_id, "manifest_sha256": manifest_sha256, "pauli_encoding": "I=0,X=1,Y=2,Z=3", "observation": problem.syndrome.tolist()}),
        _event("sample", {"sample_identity": _digest({"manifest": manifest_sha256, "shot": shot_id}), "channel": channel.tolist(), "hidden_truth_sealed": True, "sampling": "one_categorical_I_X_Y_Z_value_per_qubit"}),
        _event("decode", {"numerical_profile": "quaternary-llr-f64-v1", "decoder_smoothing": epsilon, "work": work}),
        _event("candidate_freeze", {"candidate": candidate.tolist(), "marginals": marginals.tolist()}),
        _event("evaluation", {"outcome": outcome, "logical_action_agrees": logical, "logical_action_unavailable_reason": "non-CSS tracer has no declared logical basis"}),
        _event("termination", {"termination": termination, "candidate": candidate.tolist(), "outcome": outcome, "assessment_status": "not_assessed"}),
    ]
    output_path = Path(output)
    _write_events(output_path / "events.jsonl", events)
    return TracerQbpResult(candidate, marginals, work, termination, outcome, logical)


def run_quaternary_qbpgd(
    manifest: Any, output: str | Path, *, resolved_composition: Mapping[str, Any], shot_id: int = 0,
) -> dict[str, Any]:
    """Execute resolved Q-BPGD while retaining source components separately from run fidelity."""
    problem, channel, run_id, _iterations, max_work, smoothing, manifest_sha256 = _manifest_parts(manifest)
    payload = manifest.model_dump(mode="json") if hasattr(manifest, "model_dump") else manifest
    config = payload["composition"]["intervention"]["config"]
    if not isinstance(config, Mapping):
        raise ValueError("Q-BPGD public binding requires an explicit configuration")
    iterations, epsilon, rounds, profile = (
        config.get("iterations_per_round"), config.get("epsilon"),
        config.get("round_limit"), config.get("prior_profile"),
    )
    if isinstance(iterations, bool) or not isinstance(iterations, int) or isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)):
        raise ValueError("Q-BPGD public binding requires numeric iterations_per_round and epsilon")
    if rounds is not None and (isinstance(rounds, bool) or not isinstance(rounds, int)):
        raise ValueError("Q-BPGD public round_limit must be an integer when supplied")
    if profile not in {"depolarizing", "general_joint"}:
        raise ValueError("Q-BPGD public binding requires depolarizing or general_joint prior_profile")
    physical_identity = _digest({"checks": problem.checks.tolist(), "channel": channel.tolist(), "run_id": run_id})
    hidden = _sample(channel, seed_identity=f"{physical_identity}:shot:{shot_id}")
    if not np.array_equal(syndrome_for(problem, hidden), problem.syndrome):
        raise ValueError("manifest observation does not match its deterministic categorical sample")
    priors = np.maximum(channel, smoothing)
    priors /= priors.sum(axis=1, keepdims=True)
    original = QuaternaryOriginalProblem(
        lineage_id=f"original-qbpgd-{manifest_sha256[:16]}",
        code=PauliCode(checks=problem.checks, source_artifact_identity=f"public-manifest:{manifest_sha256}"),
        syndrome=problem.syndrome,
    )
    decoded = QbpgdController(QbpgdSpec(
        iterations_per_round=iterations, epsilon=float(epsilon), round_limit=rounds, prior_profile=str(profile),
    )).run(ScalarLlrBp4Kernel().new_session(
        original, priors, budgets=BudgetTree(limits=(BudgetLimit("attempt", "bp_calls", max_work),), parents={}),
    ))
    candidate = np.asarray(decoded.candidate, dtype=np.uint8)
    outcome, logical = _evaluate(problem, hidden, candidate)
    events = [
        _event("preflight", {
            "run_id": run_id, "shot_id": shot_id, "manifest_sha256": manifest_sha256,
            "pauli_encoding": "I=0,X=1,Y=2,Z=3", "observation": problem.syndrome.tolist(),
            "public_schema": "quaternary_experiment_v2", "resolved_composition": dict(resolved_composition),
        }),
        _event("sample", {
            "sample_identity": _digest({"manifest": manifest_sha256, "shot": shot_id}), "channel": channel.tolist(),
            "decoder_priors": priors.tolist(), "decoder_smoothing": smoothing, "hidden_truth_sealed": True,
            "sampling": "one_categorical_I_X_Y_Z_value_per_qubit",
        }),
    ]
    for round_ in decoded.rounds:
        events.append(_event("qbpgd_round", {
            "index": round_.index, "eligibility_set": list(round_.eligibility_set),
            "selected_target": round_.selected_target, "selected_pauli": round_.selected_pauli,
            "reliability": round_.reliability, "target_ties": list(round_.target_ties),
            "pauli_ties": list(round_.pauli_ties), "raw_prior": None if round_.raw_prior is None else list(round_.raw_prior),
            "resolved_prior": None if round_.resolved_prior is None else list(round_.resolved_prior),
            "message_digest_before": round_.message_digest_before, "message_digest_after": round_.message_digest_after,
            "original_syndrome_valid": round_.original_syndrome_valid, "terminal_reason": round_.terminal_reason,
            "work": round_.sweeps[-1].work.as_evidence(structural_event_version=4) if round_.sweeps else {},
        }))
    events.extend((
        _event("candidate_freeze", {"candidate": candidate.tolist(), "marginals": []}),
        _event("evaluation", {"outcome": outcome, "logical_action_agrees": logical, "logical_action_unavailable_reason": "non-CSS tracer has no declared logical basis"}),
        _event("termination", {"termination": decoded.termination, "candidate": candidate.tolist(), "outcome": outcome, "assessment_status": "not_assessed"}),
    ))
    _write_events(Path(output) / "events.jsonl", events)
    return {
        "termination": decoded.termination, "outcome": outcome, "run_fidelity": decoded.run_fidelity,
        "component_fidelity": dict(decoded.component_fidelity), "component_ids": dict(decoded.component_ids),
        "interpretation_ids": dict(decoded.interpretation_ids), "source_author_code_identity": decoded.source_author_code_identity,
        "work": decoded.work.as_evidence(structural_event_version=4),
    }


def run_quaternary_mbp4(
    manifest: Any, output: str | Path, *, resolved_composition: Mapping[str, Any], shot_id: int = 0,
) -> dict[str, Any]:
    """Run the closed fixed-alpha MBP4 recurrence with replay-complete evidence."""
    problem, channel, run_id, iterations, max_work, smoothing, manifest_sha256 = _manifest_parts(manifest)
    payload = manifest.model_dump(mode="json") if hasattr(manifest, "model_dump") else manifest
    composition = payload["composition"]
    kernel_config = composition["kernel"].get("config")
    if not isinstance(kernel_config, Mapping):
        raise ValueError("public fixed-alpha MBP4 requires an explicit kernel configuration")
    spec = Mbp4Spec(alpha=kernel_config.get("alpha"), schedule=composition["schedule"]["kind"], max_iterations=iterations)
    physical_identity = _digest({"checks": problem.checks.tolist(), "channel": channel.tolist(), "run_id": run_id})
    hidden = _sample(channel, seed_identity=f"{physical_identity}:shot:{shot_id}")
    if not np.array_equal(syndrome_for(problem, hidden), problem.syndrome):
        raise ValueError("manifest observation does not match its deterministic categorical sample")
    priors = np.maximum(channel, smoothing)
    priors /= priors.sum(axis=1, keepdims=True)
    original = QuaternaryOriginalProblem(
        lineage_id=f"original-mbp4-{manifest_sha256[:16]}",
        code=PauliCode(checks=problem.checks, source_artifact_identity=f"public-manifest:{manifest_sha256}"),
        syndrome=problem.syndrome,
    )
    session = FixedAlphaMbp4Kernel(spec).new_session(
        original, priors, budgets=BudgetTree(limits=(BudgetLimit("attempt", "bp_calls", max_work),), parents={}),
    )
    decoded = session.run()
    candidate = np.asarray(decoded.candidate, dtype=np.uint8)
    outcome, logical = _evaluate(problem, hidden, candidate)
    events = [
        _event("preflight", {
            "run_id": run_id, "shot_id": shot_id, "manifest_sha256": manifest_sha256,
            "pauli_encoding": "I=0,X=1,Y=2,Z=3", "observation": problem.syndrome.tolist(),
            "public_schema": "quaternary_experiment_v2", "resolved_composition": dict(resolved_composition),
        }),
        _event("sample", {
            "sample_identity": _digest({"manifest": manifest_sha256, "shot": shot_id}), "channel": channel.tolist(),
            "decoder_priors": priors.tolist(), "decoder_smoothing": smoothing, "hidden_truth_sealed": True,
            "sampling": "one_categorical_I_X_Y_Z_value_per_qubit",
        }),
        _event("mbp4_decode", {
            "alpha": spec.alpha, "equation_identity": spec.equation_identity, "source_revision": spec.source_revision,
            "schedule": spec.schedule, "schedule_freshness": decoded.schedule_freshness,
            "initial_state_digest": decoded.initial_state_digest, "state_digest": decoded.state_digest,
            "work": decoded.work.as_evidence(structural_event_version=4), "sweeps": decoded.as_evidence()["sweep_digests"],
        }),
        _event("candidate_freeze", {"candidate": candidate.tolist(), "marginals": session._marginals.tolist()}),
        _event("evaluation", {"outcome": outcome, "logical_action_agrees": logical, "logical_action_unavailable_reason": "non-CSS tracer has no declared logical basis"}),
        _event("termination", {"termination": decoded.termination, "candidate": candidate.tolist(), "outcome": outcome, "assessment_status": "not_assessed"}),
    ]
    _write_events(Path(output) / "events.jsonl", events)
    return {
        "termination": decoded.termination, "outcome": outcome, "run_fidelity": resolved_composition["run_fidelity"],
        "component_fidelity": resolved_composition["component_fidelity"], "component_ids": {"kernel": spec.equation_identity},
        "interpretation_ids": {"fixed_alpha": "declared_manifest_alpha"}, "source_author_code_identity": "unverified",
        "work": decoded.work.as_evidence(structural_event_version=4),
    }


def _css_from_public_problem(problem: TracerPauliProblem) -> CssCode:
    """Recover the strict ordered CSS artifact required at the aSCED boundary."""
    rows = np.asarray(problem.checks, dtype=np.uint8)
    x_rows: list[np.ndarray] = []
    z_rows: list[np.ndarray] = []
    seen_z = False
    for row in rows:
        labels = set(int(item) for item in row.tolist())
        if labels <= {0, int(PauliValue.X)} and int(np.count_nonzero(row)):
            if seen_z:
                raise ValueError("CSS aSCED requires all X checks before all Z checks")
            x_rows.append((row == PauliValue.X).astype(np.uint8))
        elif labels <= {0, int(PauliValue.Z)} and int(np.count_nonzero(row)):
            seen_z = True
            z_rows.append((row == PauliValue.Z).astype(np.uint8))
        else:
            raise ValueError("non-CSS aSCED is unsupported without a separate splitter derivation")
    if not x_rows or not z_rows:
        raise ValueError("CSS aSCED requires nonempty ordered X and Z check blocks")
    return CssCode(np.vstack(x_rows), np.vstack(z_rows)).validate()


def run_quaternary_asced(
    manifest: Any, output: str | Path, *, resolved_composition: Mapping[str, Any], shot_id: int = 0,
) -> dict[str, Any]:
    """Execute the complete receipt-bound CSS aSCED ensemble through the public ledger."""
    problem, channel, run_id, iterations, max_work, smoothing, manifest_sha256 = _manifest_parts(manifest)
    payload = manifest.model_dump(mode="json") if hasattr(manifest, "model_dump") else manifest
    intervention = payload["composition"]["intervention"]
    config = intervention.get("config", {})
    if not isinstance(config, Mapping) or config.get("css_only") is not True:
        raise ValueError("public aSCED requires an explicit css_only=true configuration")
    delta, row_weight, attempt_cap, path_cap = (config.get(name) for name in ("delta", "row_weight", "attempt_cap", "path_cap"))
    if not all(type(value) is int for value in (delta, row_weight, attempt_cap, path_cap)):
        raise ValueError("public aSCED requires integer delta, row_weight, attempt_cap, and path_cap")
    css = _css_from_public_problem(problem)
    constructed = construct_splitter_batch(css, delta=delta, row_weight=row_weight, attempt_cap=attempt_cap)
    if isinstance(constructed, SplitterSearchExhausted):
        raise ValueError("public aSCED splitter construction exhausted before sampling")
    original = QuaternaryOriginalProblem(
        lineage_id=f"original-asced-{manifest_sha256[:16]}",
        code=compile_css_artifact(css, source_artifact_identity=f"public-manifest:{manifest_sha256}"),
        syndrome=problem.syndrome,
    )
    batches = materialize_asced_batches(original, (constructed,), path_cap=path_cap)
    use_overcomplete = intervention["kind"] == "asced_overcomplete" or config.get("overcomplete") is True
    maps = None
    if use_overcomplete:
        made = construct_overcomplete_map(constructed, pair_cap=config.get("pair_cap", 1000))
        if isinstance(made, OvercompleteSearchExhausted):
            raise ValueError("public aSCED overcomplete construction exhausted before sampling")
        maps = {batches[0].batch_id: made}
    physical_identity = _digest({"checks": problem.checks.tolist(), "channel": channel.tolist(), "run_id": run_id})
    hidden = _sample(channel, seed_identity=f"{physical_identity}:shot:{shot_id}")
    if not np.array_equal(syndrome_for(problem, hidden), problem.syndrome):
        raise ValueError("manifest observation does not match its deterministic categorical sample")
    priors = np.maximum(channel, smoothing)
    priors /= priors.sum(axis=1, keepdims=True)
    kernel_config = payload["composition"]["kernel"].get("config", {})
    if payload["composition"]["kernel"]["kind"] == "qbp_mbp4_fixed_alpha":
        kernel = FixedAlphaMbp4Kernel(Mbp4Spec(alpha=kernel_config.get("alpha"), schedule=payload["composition"]["schedule"]["kind"], max_iterations=iterations))
    else:
        kernel = ScalarLlrBp4Kernel()
    result = AscedController(AscedSpec(
        max_iterations=iterations, path_cap=path_cap, max_total_bp_calls=max_work,
    )).run(
        original, batches, priors, kernel=kernel, overcomplete=maps,
    )
    candidate = None if result.selected_candidate is None else np.asarray(result.selected_candidate, dtype=np.uint8)
    outcome, logical = ("invalid_syndrome", None) if candidate is None else _evaluate(problem, hidden, candidate)
    events = [
        _event("preflight", {
            "run_id": run_id, "shot_id": shot_id, "manifest_sha256": manifest_sha256,
            "public_schema": "quaternary_experiment_v2", "observation": problem.syndrome.tolist(),
            "resolved_composition": dict(resolved_composition), "run_fidelity": "canonical_adaptation",
            "splitter_receipt": constructed.receipt.receipt_sha256, "h_ext_sha256": constructed.receipt.h_ext_sha256,
            "path_count": sum(batch.path_count for batch in batches), "overcomplete": use_overcomplete,
            "overcomplete_map_receipt": None if maps is None else maps[batches[0].batch_id][1].receipt_sha256,
            "graph_identity": result.paths[0].graph_identity,
        }),
        _event("sample", {"sample_identity": _digest({"manifest": manifest_sha256, "shot": shot_id}), "channel": channel.tolist(), "decoder_priors": priors.tolist(), "decoder_smoothing": smoothing, "hidden_truth_sealed": True}),
    ]
    events.extend(_event("asced_path", {
        "batch_index": path.batch_index, "path_index": path.path_index, "graph_identity": path.graph_identity,
        "virtual_bits_lsb_first": list(path.virtual_bits), "extended_syndrome": list(path.extended_syndrome),
        "candidate": list(path.candidate), "extended_valid": path.extended_valid, "original_valid": path.original_valid,
        "pauli_weight": path.pauli_weight, "terminal": path.terminal, "work": path.work.as_evidence(structural_event_version=4),
        "overcomplete_map_receipt": path.overcomplete_map_receipt,
    }) for path in result.paths)
    events.extend((
        _event("selection", {"original_valid_pool": [list(item) for item in result.original_valid_pool], "selected_origin": None if result.selected_origin is None else list(result.selected_origin), "selected_candidate": None if candidate is None else candidate.tolist(), "tie_rule": "batch_index_then_path_index"}),
        _event("evaluation", {"outcome": outcome, "logical_action_agrees": logical, "original_observation": problem.syndrome.tolist()}),
        _event("termination", {"termination": result.termination, "candidate": None if candidate is None else candidate.tolist(), "outcome": outcome, "assessment_status": "not_assessed", "work": result.work.as_evidence(structural_event_version=4)}),
    ))
    _write_events(Path(output) / "events.jsonl", events)
    return {"termination": result.termination, "outcome": outcome, "run_fidelity": result.run_fidelity, "component_fidelity": dict(resolved_composition["component_fidelity"]), "component_ids": dict(result.component_ids), "interpretation_ids": dict(result.interpretation_ids), "source_author_code_identity": "unverified", "work": result.work.as_evidence(structural_event_version=4)}


def verify_quaternary_tracer(manifest: Any, output: str | Path, *, shot_id: int = 0) -> dict[str, Any]:
    """Reconstruct exact deterministic evidence and reject any event tampering."""
    path = Path(output) / "events.jsonl"
    actual = path.read_text(encoding="utf-8") if path.is_file() else ""
    scratch = Path(output) / ".verify-replay"
    result = run_quaternary_tracer(manifest, scratch, shot_id=shot_id)
    expected = (scratch / "events.jsonl").read_text(encoding="utf-8")
    (scratch / "events.jsonl").unlink(); scratch.rmdir()
    if actual != expected:
        raise ValueError("quaternary tracer ledger differs from deterministic replay")
    return {"run_id": _manifest_parts(manifest)[2], "shot_id": shot_id, "termination": result.termination, "verified": True}
