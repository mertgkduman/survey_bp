"""Portable bounded runner for the custom research-experiment-v1 contract."""

from __future__ import annotations

import csv
from hashlib import sha256, file_digest
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import subprocess
import time
import platform
import os
from typing import Any, Mapping

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2, REFERENCE_CPU_F64, MIN_SUM_CPU_F64
from bp_registry.canonical.lineage import LineageEdge, LineageId
from bp_registry.css import CssCode, semantic_sha256
from bp_registry.evaluator import evaluate_candidate
from bp_registry.quaternary.algebra import to_symplectic
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.evaluator import evaluate_pauli_candidate
from bp_registry.quaternary.numerics import QBP4_F64_V1, QBP4_F64_V2
from bp_registry.quaternary.problems import PauliCandidate, QuaternaryWorkingProblem, compile_css_artifact
from bp_registry.quaternary.sampling import JointPauliChannel, sample_joint_pauli
from bp_registry.resolution import BpFloodingPolicy

from .evidence import timing_boundaries
from .contracts import _repository_value, interface_contract, materialize_experiment, resolved_sampling, sweep_stim_text, validate_experiment


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _code(spec: Mapping[str, object], repository: Mapping[str, object] | object | None) -> CssCode:
    ref = spec["problem"]["code"]  # type: ignore[index]
    assert isinstance(ref, Mapping)
    if ref["kind"] == "registered":
        if repository is None: raise ValueError("registered code execution requires repository")
        item = _repository_value(repository, str(ref["id"]))
        if isinstance(item, Mapping):
            item = item.get("code", item.get("value"))
        if not isinstance(item, CssCode):
            raise ValueError("registered code must resolve to CssCode or {'code': CssCode}")
        return item.validate()
    return CssCode(
        hx=np.asarray(ref["hx"], dtype=np.uint8), hz=np.asarray(ref["hz"], dtype=np.uint8),
        lx=None if "lx" not in ref else np.asarray(ref["lx"], dtype=np.uint8),
        lz=None if "lz" not in ref else np.asarray(ref["lz"], dtype=np.uint8),
    ).validate()


def _policy(decoder: Mapping[str, object]) -> BpFloodingPolicy | None:
    return None if decoder["policy"] is None else BpFloodingPolicy.from_spec(decoder["policy"])  # type: ignore[arg-type]


def _append(records: list[dict[str, object]] | None, emit, record: dict[str, object]) -> None:
    if records is not None:
        records.append(record)
    if emit is not None:
        emit(record)


_STOP_FIELDS = ("stop_failures", "stop_type_i", "stop_type_ii")


def _adaptive_sampling(limits: Mapping[str, object]) -> bool:
    return any(limits.get(field) is not None for field in _STOP_FIELDS)


def _stopping_reason(limits: Mapping[str, object], *, shots: int, failures: int, type_i: int,
                     type_ii: int) -> str | None:
    """Resolve the declared first/all stopping rule for one rate point."""
    counters = {"stop_failures": failures, "stop_type_i": type_i, "stop_type_ii": type_ii}
    reached = [field for field in _STOP_FIELDS if limits.get(field) is not None and counters[field] >= int(limits[field])]
    selected = [field for field in _STOP_FIELDS if limits.get(field) is not None]
    shot_target = limits.get("shots")
    if limits["stop_mode"] == "all":
        targets = selected + (["shots"] if shot_target is not None else [])
        if all((shots >= int(shot_target) if field == "shots" else field in reached) for field in targets):
            return "all_targets"
        return None
    for field in _STOP_FIELDS:
        if field in reached:
            return field
    if shot_target is not None and shots >= int(shot_target):
        return "shots_cap"
    return None


def _point_limits(spec: Mapping[str, object], point_index: int) -> dict[str, object]:
    sampling = spec["sampling"]
    assert isinstance(sampling, Mapping)
    return resolved_sampling(sampling, point_index, len(spec["rate_points"]))


def _wilson(failures: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    z = 1.959963984540054
    rate = failures / n
    denom = 1.0 + z * z / n
    center = (rate + z * z / (2 * n)) / denom
    radius = z * ((rate * (1 - rate) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return max(0.0, center - radius), min(1.0, center + radius)


def _pauli_code(code: CssCode):
    identity = _css_identity(code, None)
    return compile_css_artifact(code, source_artifact_identity=
        f"{identity['semantic_identity_format']}:{identity['semantic_sha256']}")


def _sample_pauli(code: CssCode, point: Mapping[str, object], channel: Mapping[str, object], *, seed: int, shot_id: int, point_index: int, prepared_code=None, code_identity: str | None = None):
    pauli = _pauli_code(code) if prepared_code is None else prepared_code
    zero = np.zeros(pauli.checks.shape[0], dtype=np.uint8)
    from bp_registry.quaternary.problems import QuaternaryOriginalProblem
    original = QuaternaryOriginalProblem("original-portable-input", pauli, zero)
    anchor = f"research-experiment-v1:{code_identity or pauli.semantic_sha256}:{seed}:{point_index}"
    if channel["kind"] == "depolarizing":
        physical = JointPauliChannel.depolarizing(point["physical_p"], n=code.n)
    elif channel["kind"] == "x_only":
        p = float(point["physical_p"])
        physical = JointPauliChannel.explicit((1.0 - p, p, 0.0, 0.0), n=code.n)
    else:
        physical = JointPauliChannel.explicit(channel["probabilities"], n=code.n)
    return sample_joint_pauli(original, channel=physical, shot_id=shot_id, manifest_identity=anchor)


def _binary_rows(spec: Mapping[str, object], code: CssCode, *, emit=None, collect: bool = True) -> tuple[list[dict[str, object]], dict[str, object]]:
    decoder, channel, sampling, budget = (spec[key] for key in ("decoder", "channel", "sampling", "budgets"))
    assert isinstance(decoder, Mapping) and isinstance(channel, Mapping) and isinstance(sampling, Mapping) and isinstance(budget, Mapping)
    policy = _policy(decoder)
    profile = REFERENCE_CPU_F64 if decoder["numerical_profile"] == "binary-spa-flooding-f64-v1" else BINARY_SPA_F64_V2
    rule = "spa" if decoder["rule"] == "sum_product" else "min_sum"
    pauli_code = _pauli_code(code)
    pauli_identity = pauli_code.semantic_sha256
    records: list[dict[str, object]] | None = [] if collect else None
    effective: dict[str, object] | None = None
    total_used = 0
    for point_index, point in enumerate(spec["rate_points"]):
        assert isinstance(point, Mapping)
        limits = _point_limits(spec, point_index)
        p0 = float(point["decoder_p0"])
        prior = 2.0 * p0 / 3.0 if channel["kind"] in {"depolarizing", "explicit"} else p0
        x_graph = CompiledBinaryFlooding.from_check_matrix(code.hz, rule=rule, profile=profile, policy=policy)
        z_graph = CompiledBinaryFlooding.from_check_matrix(code.hx, rule=rule, profile=profile, policy=policy)
        if effective is None:
            effective = {"x_component": x_graph.effective_numerics,
                         "z_component": z_graph.effective_numerics, "resolved_rate_points": []}
        effective["resolved_rate_points"].append({"physical_p": point.get("physical_p"),
            "decoder_p0": p0, "decoder_prior_kind": "separate_bernoulli_components",
            "x_bernoulli_probability": prior, "z_bernoulli_probability": prior,
            "physical_channel": dict(channel)})
        failures = type_i = type_ii = 0
        offset = 0
        while True:
            if budget["max_shots"] is not None and total_used >= int(budget["max_shots"]):
                raise RuntimeError("legacy total max_shots reached before all rate-point stopping targets")
            shot_id = int(sampling["shot_start"]) + offset
            started = time.perf_counter()
            sample = _sample_pauli(code, point, channel, seed=int(sampling["seed"]), shot_id=shot_id, point_index=point_index, prepared_code=pauli_code, code_identity=pauli_identity)
            sampled_at = time.perf_counter()
            x = x_graph.run(sample.observation.syndrome[len(code.hx):], error_rate=prior, max_iterations=int(budget["max_iterations"]))
            z = z_graph.run(sample.observation.syndrome[:len(code.hx)], error_rate=prior, max_iterations=int(budget["max_iterations"]))
            decoded_at = time.perf_counter()
            truth = sample.hidden
            ev = evaluate_candidate(code, true_x=truth.x, true_z=truth.z, candidate_x=x.candidate, candidate_z=z.candidate)
            failures += ev.outcome not in {"exact", "stabilizer_equivalent"}
            type_i += ev.outcome == "invalid_syndrome"
            type_ii += ev.outcome == "logical_failure"
            stop_reason = _stopping_reason(limits, shots=offset + 1, failures=failures, type_i=type_i, type_ii=type_ii)
            _append(records, emit, {"kind": "shot", "family": "binary_css", "rate_index": point_index,
                "p": point.get("physical_p"), "decoder_p0": p0, "shot_id": shot_id, "sample_identity": sample.sample_identity,
                "physical_channel_identity": sample.ledger["channel_identity"], "physical_pauli_order": sample.ledger["pauli_order"],
                "candidate_x": x.candidate.tolist(), "candidate_z": z.candidate.tolist(), "outcome": ev.outcome,
                "logical_action_agrees": ev.logical_action_agrees, "converged": bool(x.converged and z.converged),
                "termination_reason": "all_components_syndrome_match" if x.converged and z.converged else "iteration_cap",
                "component_termination": {"x": "zero_syndrome_shortcut" if x.iterations == 0 else "syndrome_match" if x.converged else "iteration_cap",
                                          "z": "zero_syndrome_shortcut" if z.iterations == 0 else "syndrome_match" if z.converged else "iteration_cap"},
                "lineage": {"sample": sample.sample_identity, "original_problem": sample.observation.lineage_id,
                            "candidate": sha256(_canonical({"sample": sample.sample_identity,
                                "x": x.candidate.tolist(), "z": z.candidate.tolist()})).hexdigest()},
                "iterations": {"x": x.iterations, "z": z.iterations}, "work_units": {"unit": "binary_component_sweeps", "x": x.iterations, "z": z.iterations},
                "decode_seconds": decoded_at - sampled_at, "end_to_end_seconds": time.perf_counter() - started,
                "sampling_mode": "adaptive_stopping" if _adaptive_sampling(limits) else "fixed_shots", "sampling_stop_mode": limits["stop_mode"],
                "sampling_stop_reason": stop_reason})
            total_used += 1
            if stop_reason is not None:
                break
            offset += 1
    return records or [], effective or {}


def _bp4_rows(spec: Mapping[str, object], code: CssCode, *, emit=None, collect: bool = True) -> tuple[list[dict[str, object]], dict[str, object]]:
    decoder, channel, sampling, budget = (spec[key] for key in ("decoder", "channel", "sampling", "budgets"))
    assert isinstance(decoder, Mapping) and isinstance(channel, Mapping) and isinstance(sampling, Mapping) and isinstance(budget, Mapping)
    policy = _policy(decoder)
    profile = QBP4_F64_V1 if decoder["numerical_profile"] == "quaternary-bp4-f64-v1" else QBP4_F64_V2
    pauli_code = _pauli_code(code)
    pauli_identity = pauli_code.semantic_sha256
    records: list[dict[str, object]] | None = [] if collect else None
    effective: dict[str, object] | None = None
    total_used = 0
    for point_index, point in enumerate(spec["rate_points"]):
        assert isinstance(point, Mapping)
        limits = _point_limits(spec, point_index)
        p0 = float(point["decoder_p0"])
        if profile is QBP4_F64_V1:
            priors = np.tile((1.0 - p0, p0 / 3.0, p0 / 3.0, p0 / 3.0), (code.n, 1))
            graph = CompiledBp4Graph.from_code(pauli_code, priors, profile=profile, rule=decoder["rule"], policy=policy)
        else:
            graph = CompiledBp4Graph.from_css(code, p0, rule=decoder["rule"], policy=policy)
        if effective is None:
            effective = {**graph.effective_numerics, "resolved_rate_points": []}
        effective["resolved_rate_points"].append({"physical_p": point.get("physical_p"),
            "decoder_p0": p0, "decoder_prior_kind": "depolarizing_joint",
            "decoder_prior_pauli_order": "I,X,Y,Z",
            "decoder_prior_probabilities": [1 - p0, p0 / 3, p0 / 3, p0 / 3],
            "physical_channel": dict(channel)})
        failures = type_i = type_ii = 0
        offset = 0
        while True:
            if budget["max_shots"] is not None and total_used >= int(budget["max_shots"]):
                raise RuntimeError("legacy total max_shots reached before all rate-point stopping targets")
            shot_id = int(sampling["shot_start"]) + offset
            started = time.perf_counter()
            sample = _sample_pauli(code, point, channel, seed=int(sampling["seed"]), shot_id=shot_id, point_index=point_index, prepared_code=pauli_code, code_identity=pauli_identity)
            sampled_at = time.perf_counter()
            if decoder["variant"] == "qbpgd":
                knobs = decoder["qbpgd"]
                assert isinstance(knobs, Mapping)
                result = graph.run_qbpgd(sample.observation.syndrome, iterations_per_round=int(knobs["iterations_per_round"]), epsilon=float(knobs["epsilon"]), round_limit=knobs["round_limit"])
                iterations, converged, extra = result.iterations, result.converged, {"rounds": result.rounds, "fixations": result.fixations}
            else:
                result = graph.run(sample.observation.syndrome, max_iterations=int(budget["max_iterations"]), stop_on_convergence=bool(decoder["stop_on_convergence"]))
                iterations, converged, extra = result.iterations, result.converged, {}
            decoded_at = time.perf_counter()
            original = sample.observation
            working_id = "working-" + sample.sample_identity
            working = QuaternaryWorkingProblem(working_id, original, LineageEdge("identity", LineageId("original", original.lineage_id), LineageId("working", working_id)))
            candidate_id = "candidate-" + sha256(_canonical({"sample": sample.sample_identity,
                "candidate": result.candidate.tolist()})).hexdigest()
            candidate = PauliCandidate(candidate_id, working, result.candidate, 0)
            ev = evaluate_pauli_candidate(candidate, hidden_truth=sample.hidden.paulis)
            failures += ev.outcome not in {"exact", "stabilizer_equivalent"}
            type_i += ev.outcome == "invalid_syndrome"
            type_ii += ev.outcome == "logical_failure"
            stop_reason = _stopping_reason(limits, shots=offset + 1, failures=failures, type_i=type_i, type_ii=type_ii)
            _append(records, emit, {"kind": "shot", "family": "bp4", "rate_index": point_index, "p": point.get("physical_p"), "decoder_p0": p0,
                "shot_id": shot_id, "sample_identity": sample.sample_identity,
                "physical_channel_identity": sample.ledger["channel_identity"], "physical_pauli_order": sample.ledger["pauli_order"], "candidate": result.candidate.tolist(), "outcome": ev.outcome,
                "logical_action": None if ev.logical_action is None else [list(row) for row in ev.logical_action], "converged": bool(converged),
                "termination_reason": ("round_cap" if not converged else "first_valid") if decoder["variant"] == "qbpgd" else
                    "iteration_cap" if not decoder["stop_on_convergence"] or not converged else
                    "zero_syndrome_shortcut" if iterations == 0 else "first_valid",
                "lineage": {"sample": sample.sample_identity, "original_problem": original.lineage_id,
                            "working_problem": working_id, "candidate": candidate_id},
                "iterations": iterations, "work_units": {"unit": "bp4_joint_sweeps", "value": iterations, **extra}, "decode_seconds": decoded_at - sampled_at, "end_to_end_seconds": time.perf_counter() - started,
                "sampling_mode": "adaptive_stopping" if _adaptive_sampling(limits) else "fixed_shots", "sampling_stop_mode": limits["stop_mode"],
                "sampling_stop_reason": stop_reason})
            total_used += 1
            if stop_reason is not None:
                break
            offset += 1
    return records or [], effective or {}


def _circuit_rows(spec: Mapping[str, object], repository: Mapping[str, object] | object | None, *, emit=None) -> tuple[list[dict[str, object]], dict[str, object]]:
    started_all = time.perf_counter()
    problem, decoder, sampling = (spec[key] for key in ("problem", "decoder", "sampling"))
    assert isinstance(problem, Mapping) and isinstance(decoder, Mapping) and isinstance(sampling, Mapping)
    circuit_ref = problem["circuit"]
    assert isinstance(circuit_ref, Mapping)
    if circuit_ref["kind"] == "inline_stim": text = circuit_ref["text"]
    else:
        if repository is None: raise ValueError("registered circuit execution requires repository")
        text = _repository_value(repository, str(circuit_ref["id"]))
    if isinstance(text, Mapping): text = text.get("text", text.get("circuit"))
    if not isinstance(text, str): raise ValueError("registered circuit must resolve to Stim text")
    try:
        import sinter
        import stim
        from bp_registry.circuit import CanonicalBpSinterDecoder
    except ImportError as error:
        raise RuntimeError("circuit execution requires the optional stim and sinter dependencies") from error
    adapter = CanonicalBpSinterDecoder(max_iterations=int(decoder["max_iterations"]), rule=str(decoder["rule"]), tie_break=str(decoder["tie_break"]))
    rows: list[dict[str, object]] = []
    total_used = 0
    sweep = spec["channel"].get("noise_sweep")
    resolved: list[dict[str, object]] = []
    for point_index, point in enumerate(spec["rate_points"]):
        assert isinstance(point, Mapping)
        current_text = text if sweep is None else sweep_stim_text(text, source_probability=float(sweep["source_probability"]), physical_p=float(point["physical_p"]))
        circuit = stim.Circuit(current_text)
        dem = circuit.detector_error_model(decompose_errors=False)
        detailed = adapter.compile_decoder_for_dem(dem=dem)
        sampler = circuit.compile_detector_sampler(seed=int(sampling["seed"]) + point_index)
        start = int(sampling["shot_start"])
        # Stim's stream is batch-shape dependent.  Advance the skipped prefix
        # in the same one-shot chunks used for retained evidence, so shot k is
        # invariant under choosing it as a prefix or a retained decode.
        budget = spec["budgets"]
        assert isinstance(budget, Mapping)
        if budget["max_shots"] is not None and total_used + start > int(budget["max_shots"]):
            raise RuntimeError("legacy total max_shots reached while drawing the circuit shot prefix")
        for _ in range(start):
            sampler.sample(shots=1, separate_observables=True)
        total_used += start
        limits = _point_limits(spec, point_index)
        failures = type_i = type_ii = 0
        index = 0
        while True:
            if budget["max_shots"] is not None and total_used >= int(budget["max_shots"]):
                raise RuntimeError("legacy total max_shots reached before all rate-point stopping targets")
            detector, truth = sampler.sample(shots=1, separate_observables=True)
            shot_started = time.perf_counter()
            prediction = sinter.predict_observables(dem=dem, dets=detector.astype(np.bool_), decoder="portable_canonical_bp", custom_decoders={"portable_canonical_bp": adapter})
            predicted_at = time.perf_counter()
            detailed_prediction, converged, iterations = detailed.decode_detailed(detector)
            if not np.array_equal(prediction, detailed_prediction.astype(bool)):
                raise RuntimeError("Sinter custom-decoder predictions disagree with the detailed canonical adapter")
            failure = bool(np.any(prediction[0] != truth[0]))
            flagged = failure and not bool(converged[0])
            unflagged = failure and bool(converged[0])
            failures += failure; type_i += flagged; type_ii += unflagged
            stop_reason = _stopping_reason(limits, shots=index + 1, failures=failures, type_i=type_i, type_ii=type_ii)
            row = {"kind": "shot", "family": "circuit_dem_bp", "rate_index": point_index, "p": point.get("physical_p"), "decoder_p0": None,
                   "setting_label": point["label"], "shot_id": start + index,
                   "detector_events": detector[0].astype(int).tolist(), "observable_truth": truth[0].astype(int).tolist(), "observable_prediction": prediction[0].astype(int).tolist(),
                   "detector_fit": bool(converged[0]), "observable_failure": failure, "type_i": flagged, "type_ii": unflagged,
                   "outcome": "observable_failure" if failure else "observable_success",
                   "termination_reason": "initial_candidate_fit" if int(iterations[0]) == 0 and converged[0] else "detector_fit" if converged[0] else "iteration_cap",
                   "converged": bool(converged[0]), "iterations": int(iterations[0]), "work_units": {"unit": "circuit_dem_bp_sweeps", "value": int(iterations[0])}, "decode_seconds": predicted_at - shot_started, "end_to_end_seconds": time.perf_counter() - shot_started,
                   "sampling_mode": "adaptive_stopping" if _adaptive_sampling(limits) else "fixed_shots", "sampling_stop_mode": limits["stop_mode"], "sampling_stop_reason": stop_reason}
            rows.append(row)
            total_used += 1
            if emit is not None: emit(row)
            if stop_reason is not None: break
            index += 1
        resolved.append({"label": point["label"], "physical_p": point.get("physical_p"), "stim_sha256": sha256(current_text.encode()).hexdigest(), "dem_sha256": sha256(str(dem).encode()).hexdigest()})
    numerics = REFERENCE_CPU_F64 if decoder["rule"] == "spa" else MIN_SUM_CPU_F64
    return rows, {"dem_sha256": [item["dem_sha256"] for item in resolved], "adapter": dict(decoder),
        "numerical_profile": {**numerics.as_evidence(), "backend": "cpu-numba-circuit-adapter", "exact_zero_decision": int(decoder["tie_break"] == "one")}, "sinter_prediction": True,
        "detectors": circuit.num_detectors, "observables": circuit.num_observables,
        "dem_projection": "independent_mechanisms; logical-only and detector-free faults follow the existing adapter bias/projection contract",
        "observable_evaluation": "any declared observable prediction differs from sampled truth; type_i is an observable failure without detector fit and type_ii is an observable failure with detector fit",
        "resolved_circuit_rate_points": resolved, "sampling_prefix_drawn": int(sampling["shot_start"])}


def _provenance(repository: Mapping[str, object] | object | None) -> dict[str, object]:
    source_root = Path(__file__).resolve().parents[3]
    repo_root = Path(repository).expanduser().resolve() if isinstance(repository, (str, Path)) else source_root
    try: head = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError): head = None
    packages = {}
    for name in ("bp-registry", "numpy", "scipy", "pydantic", "numba", "stim", "sinter"):
        try: packages[name] = version(name)
        except PackageNotFoundError: packages[name] = None
    package_root = Path(__file__).resolve().parents[1]
    sources = {path.relative_to(package_root).as_posix(): sha256(path.read_bytes()).hexdigest()
               for path in sorted(package_root.rglob("*.py"))}
    implementation_sha256 = sha256(_canonical({"sources": sources, "packages": packages,
                                               "python": platform.python_version()})).hexdigest()
    return {"repository_root": str(repo_root), "implementation_source_root": str(package_root),
            "git_head": head, "python": platform.python_version(), "packages": packages,
            "implementation_sources": sources, "implementation_sha256": implementation_sha256,
            "timing_environment": {"platform": platform.platform(), "architecture": platform.machine(),
                "processor": platform.processor() or "unavailable", "host": platform.node(), "cpu_count": os.cpu_count(),
                "thread_settings": {key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS")},
                "clock": "time.perf_counter", "clock_implementation": time.get_clock_info("perf_counter").implementation,
                "clock_resolution_seconds": time.get_clock_info("perf_counter").resolution},
            "runner_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}


def _summary_rows(event_path: Path, *, points: list[object], kind: str, sampling: Mapping[str, object], budgets: Mapping[str, object]) -> list[dict[str, object]]:
    """Aggregate the durable JSONL ledger in one pass without retaining shot rows."""
    buckets = [{"n": 0, "failures": 0, "invalid": 0, "logical": 0, "exact": 0, "equivalent": 0, "circuit_type_i": 0, "circuit_type_ii": 0, "extended": False, "iterations": 0.0, "decode_seconds": 0.0, "timed": 0, "converged": 0, "terminations": {}, "sampling_termination": None} for _ in points]
    with event_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line); bucket = buckets[row["rate_index"]]
            bucket["n"] += 1
            outcome = row["outcome"]
            bucket["failures"] += outcome not in {"exact", "stabilizer_equivalent", "observable_success"}
            bucket["invalid"] += outcome == "invalid_syndrome"; bucket["logical"] += outcome == "logical_failure"
            bucket["exact"] += outcome == "exact"; bucket["equivalent"] += outcome == "stabilizer_equivalent"
            bucket["circuit_type_i"] += bool(row.get("type_i")); bucket["circuit_type_ii"] += bool(row.get("type_ii"))
            bucket["extended"] |= "sampling_stop_mode" in row
            bucket["converged"] += bool(row["converged"])
            reason = row["termination_reason"]
            bucket["terminations"][reason] = bucket["terminations"].get(reason, 0) + 1
            if row.get("sampling_stop_reason") is not None:
                bucket["sampling_termination"] = row["sampling_stop_reason"]
            iteration = row["iterations"]; bucket["iterations"] += sum(iteration.values()) if isinstance(iteration, dict) else iteration
            if row["decode_seconds"] is not None: bucket["decode_seconds"] += row["decode_seconds"]; bucket["timed"] += 1
    unit = {"css_code_capacity": "binary_component_sweeps", "pauli_code_capacity": "bp4_joint_sweeps", "circuit": "circuit_dem_bp_sweeps"}[kind]
    result = []
    for index, (point, bucket) in enumerate(zip(points, buckets, strict=True)):
        assert isinstance(point, Mapping)
        limits = resolved_sampling(sampling, index, len(points))
        adaptive = _adaptive_sampling(limits)
        low, high = _wilson(bucket["failures"], bucket["n"])
        rate = bucket["failures"] / bucket["n"] if bucket["n"] else None
        result.append({"rate_index": index, "p": point.get("physical_p"), "decoder_p0": point.get("decoder_p0"), "n": bucket["n"], "failures": bucket["failures"], "failure_rate": rate, "ler": rate if kind != "circuit" else None, "ci_low": None if adaptive else low, "ci_high": None if adaptive else high, "ci_method": "unavailable_optional_stopping" if adaptive else "wilson_score_95", "ci_status": "not_reported_optional_stopping" if adaptive else ("zero_failures_upper_bound" if bucket["failures"] == 0 else "two_sided"), "sampling_mode": "adaptive_stopping" if adaptive else "fixed_shots", "sampling_stop_mode": limits["stop_mode"], "sampling_stop_semantics": "all configured targets" if limits["stop_mode"] == "all" else "first configured target", "sampling_termination_reason": bucket["sampling_termination"] or "shots_cap", "type_i": bucket["invalid"] if kind != "circuit" else bucket["circuit_type_i"], "type_ii": bucket["logical"] if kind != "circuit" else bucket["circuit_type_ii"], "exact_successes": bucket["exact"] if kind != "circuit" else None, "stabilizer_equivalent_successes": bucket["equivalent"] if kind != "circuit" else None, "observable_successes": bucket["n"] - bucket["failures"] if kind == "circuit" else None, "converged_shots": bucket["converged"], "unconverged_shots": bucket["n"] - bucket["converged"], "convergence_rate": bucket["converged"] / bucket["n"] if bucket["n"] else None, "termination_reason_counts": bucket["terminations"], "mean_iterations": bucket["iterations"] / bucket["n"] if bucket["n"] else None, "work_unit": unit, "mean_decode_seconds": bucket["decode_seconds"] / bucket["timed"] if bucket["timed"] else None, "requested_shots_per_point": limits["shots"], "total_max_shots": budgets["max_shots"]})
        result[-1]["setting_label"] = point.get("label")
        if not bucket["extended"]:
            # Replaying a manifest-bound v1 ledger must regenerate its original
            # summary shape.  New runs always write the extension marker.
            result[-1].pop("sampling_stop_mode"); result[-1].pop("sampling_stop_semantics")
            if kind == "circuit":
                result[-1]["type_i"] = None; result[-1]["type_ii"] = None
    return result


def _css_identity(code: CssCode, request: object) -> dict[str, object]:
    matrices = {"hx": code.hx.tolist(), "hz": code.hz.tolist(),
                "lx": None if code.lx is None else code.lx.tolist(),
                "lz": None if code.lz is None else code.lz.tolist()}
    has_logicals = code.lx is not None and code.lz is not None
    return {"raw_sha256": sha256(_canonical(request)).hexdigest(),
            "semantic_sha256": semantic_sha256(code) if has_logicals else sha256(_canonical(matrices)).hexdigest(),
            "semantic_identity_format": "bp-registry-css-v1" if has_logicals else "ordered-css-matrices-json-v1",
            "logical_basis_available": has_logicals}


def run_experiment(spec: object, *, output: str | Path, repository: Mapping[str, object] | object | None = None) -> dict[str, object]:
    """Run a bounded custom experiment once, producing immutable local evidence files."""
    normalized = validate_experiment(spec, repository=repository)
    problem_ref = normalized["problem"]
    if (problem_ref["kind"] in {"css_code_capacity", "pauli_code_capacity"} and problem_ref["code"]["kind"] == "registered") or (problem_ref["kind"] == "circuit" and problem_ref["circuit"]["kind"] == "registered"):
        normalized = materialize_experiment(normalized, repository)
    destination = Path(output)
    if destination.exists():
        raise FileExistsError("portable experiment output must not already exist")
    provenance = _provenance(repository)
    configuration_sha256 = sha256(_canonical(normalized)).hexdigest()
    experiment_id = sha256(_canonical({"configuration_sha256": configuration_sha256, "implementation_sha256": provenance["implementation_sha256"]})).hexdigest()
    destination.mkdir(parents=True)
    (destination / "requested-spec.json").write_bytes(_canonical(normalized))
    event_path = destination / "events.jsonl"
    event_path.touch(exist_ok=False)
    (destination / "run-manifest.json").write_bytes(_canonical({"schema": "research-run-manifest-v1",
        "experiment_id": experiment_id, "configuration_sha256": configuration_sha256,
        "provenance": provenance, "requested_spec_sha256": sha256(_canonical(normalized)).hexdigest()}))
    (destination / "status.json").write_bytes(_canonical({"status": "running", "experiment_id": experiment_id}))
    def emit(record: dict[str, object]) -> None:
        with event_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
    kind = normalized["problem"]["kind"]
    try:
        if kind == "css_code_capacity":
            code = _code(normalized, repository); _records, effective = _binary_rows(normalized, code, emit=emit, collect=False)
            input_identity = _css_identity(code, normalized["problem"]["code"])
        elif kind == "pauli_code_capacity":
            code = _code(normalized, repository); _records, effective = _bp4_rows(normalized, code, emit=emit, collect=False)
            input_identity = _css_identity(code, normalized["problem"]["code"])
        else:
            _records, effective = _circuit_rows(normalized, repository, emit=emit)
            circuit = normalized["problem"]["circuit"]
            text = circuit["text"] if circuit["kind"] == "inline_stim" else _repository_value(repository, circuit["id"])
            input_identity = {"raw_sha256": sha256(str(text).encode()).hexdigest(), "semantic_sha256": effective["dem_sha256"], "dem_decompose_errors": False}
        rows = _summary_rows(event_path, points=normalized["rate_points"], kind=kind, sampling=normalized["sampling"], budgets=normalized["budgets"])
        summary: dict[str, object] = {"schema": "research-run-summary-v1", "experiment_id": experiment_id, "user_label": normalized["id"], "configuration_sha256": configuration_sha256, "input_identity": input_identity, "rows": rows,
            "effective_configuration": effective, "timing_note": "decode wall time measures decoder invocation, includes lazy Numba JIT compilation when not warmed; see timing_boundaries for exact per-shot setup and audit scope", "provenance": provenance,
            "timing_boundaries": timing_boundaries(kind)}
        (destination / "effective-spec.json").write_bytes(_canonical({"schema": "research-effective-spec-v1",
            "experiment": normalized, "numerical_settings": effective, "input_identity": input_identity,
            "implementation_sha256": provenance["implementation_sha256"]}))
        (destination / "summary.json").write_bytes(_canonical(summary))
        with (destination / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows({key: json.dumps(value, sort_keys=True) if isinstance(value, dict) else value for key, value in row.items()} for row in rows)
        (destination / "status.json").write_bytes(_canonical({"status": "completed", "experiment_id": experiment_id}))
        hashes = {}
        for name in ("run-manifest.json", "status.json", "requested-spec.json", "effective-spec.json", "events.jsonl", "summary.json", "summary.csv"):
            with (destination / name).open("rb") as handle:
                hashes[name] = file_digest(handle, "sha256").hexdigest()
        (destination / "result-manifest.json").write_bytes(_canonical({"schema": "research-result-manifest-v1", "experiment_id": experiment_id, "files": hashes}))
        # Deliberately derived and read-only: it is not part of the input/result
        # hash set, so a browser can validate the seven bound files first and
        # then compare this convenience catalog entry semantically.
        from .results import normalize_result_directory
        (destination / "catalog-entry.json").write_bytes(_canonical(normalize_result_directory(destination)))
        return summary
    except BaseException as error:
        try:
            (destination / "status.json").write_bytes(_canonical({"schema": "research-run-status-v1", "status": "failed_partial", "experiment_id": experiment_id, "configuration_sha256": configuration_sha256, "error_type": type(error).__name__, "error": str(error)}))
        except OSError:
            pass  # Preserve the original failure if storage itself is unavailable.
        raise



__all__ = ["interface_contract", "materialize_experiment", "run_experiment", "validate_experiment"]
