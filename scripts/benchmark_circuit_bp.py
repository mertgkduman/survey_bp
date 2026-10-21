"""Bounded matched-input CPU timing for the pinned Relay circuit fixtures."""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time

import numpy as np
from scipy.sparse import csr_matrix
import stim

from bp_registry.circuit import CanonicalBpSinterDecoder


FIXTURES = (
    ("relay", "rotated_surface_code_memory_X", 4096),
    ("relay", "superdense_color_code_memory_Z", 2048),
    ("relay", "bicycle_bivariate_18_4_3_memory_X", 1024),
    ("relay", "bicycle_bivariate_144_12_12_memory_Z", 128),
    ("beamsearch", "bb144-memory-z-p005", 512),
)


def native_identity() -> dict[str, object] | None:
    try:
        import relay_bp
    except ImportError:
        return None
    path = Path(relay_bp.__file__).resolve()
    commit = subprocess.run(
        ["git", "-C", str(path.parent), "rev-parse", "HEAD"],
        check=False, capture_output=True, text=True,
    )
    try:
        version = importlib.metadata.version("relay-bp")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {"module_path": str(path), "git_commit": commit.stdout.strip() if commit.returncode == 0 else None, "package_version": version}


def benchmark_one(path: Path, shots: int, iterations: int) -> dict[str, object]:
    circuit = stim.Circuit.from_file(path)
    start = time.perf_counter()
    dem = circuit.detector_error_model(decompose_errors=False)
    decoder = CanonicalBpSinterDecoder(iterations, rule="min_sum", tie_break="one").compile_decoder_for_dem(dem=dem)
    canonical_setup = time.perf_counter() - start
    detectors, truth = circuit.compile_detector_sampler(seed=20261021).sample(
        shots=shots, separate_observables=True,
    )
    decoder.decode_detailed(detectors[:1])  # Exclude one-time JIT compilation.
    start = time.perf_counter()
    predictions, converged, sweeps = decoder.decode_detailed(detectors)
    canonical_seconds = time.perf_counter() - start
    record: dict[str, object] = {
        "circuit": path.name, "circuit_sha256": sha256(path.read_bytes()).hexdigest(),
        "dem_sha256": decoder.model.dem_sha256,
        "detectors": dem.num_detectors, "observables": dem.num_observables,
        "dem_error_instructions": decoder.model.source_error_count,
        "active_fault_variables": decoder.model.table.variable_count,
        "parity_edges": decoder.model.table.edge_count,
        "shots": shots, "max_iterations": iterations,
        "canonical_setup_seconds": canonical_setup,
        "canonical_decode_seconds": canonical_seconds,
        "canonical_converged": int(np.count_nonzero(converged)),
        "canonical_mean_sweeps": float(np.mean(sweeps)),
        "canonical_observable_errors": int(np.count_nonzero(np.any(predictions != truth, axis=1))),
    }
    try:
        import relay_bp
    except ImportError:
        record["native_status"] = "unavailable"
        return record
    model = decoder.model
    h = csr_matrix(
        (np.ones(len(model.variables), dtype=np.uint8), model.variables, model.row_ptr),
        shape=(model.table.check_count, model.table.variable_count),
    ).tocsc()
    probabilities = 1.0 / (1.0 + np.exp(model.prior_llrs))
    start = time.perf_counter()
    native = relay_bp.MinSumBPDecoderF64(h, error_priors=probabilities, max_iter=iterations, alpha=None, gamma0=None)
    runner = relay_bp.ObservableDecoderRunner(native, model.observable_matrix, include_decode_result=False)
    record["native_setup_seconds"] = time.perf_counter() - start
    runner.decode_observables_batch(detectors[:1].astype(np.uint8), parallel=False)
    start = time.perf_counter()
    native_predictions = np.asarray(runner.decode_observables_batch(detectors.astype(np.uint8), parallel=False), dtype=np.uint8)
    record["native_decode_seconds"] = time.perf_counter() - start
    record["native_observable_errors"] = int(np.count_nonzero(np.any(native_predictions != truth, axis=1)))
    disagreement_indices = np.flatnonzero(np.any(native_predictions != predictions, axis=1))
    record["native_canonical_prediction_disagreements"] = int(len(disagreement_indices))
    record["disagreement_examples"] = [
        {
            "shot_index": int(index),
            "detectors": detectors[index].astype(np.uint8).tolist(),
            "truth_observables": truth[index].astype(np.uint8).tolist(),
            "canonical_observables": predictions[index].tolist(),
            "native_observables": native_predictions[index].tolist(),
            "canonical_converged": bool(converged[index]),
            "canonical_sweeps": int(sweeps[index]),
        }
        for index in disagreement_indices[:8]
    ]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relay-root", type=Path, default=Path("data/circuits/relay-v0.2.2"))
    parser.add_argument("--beamsearch-root", type=Path, default=Path("data/circuits/beamsearch-084a475b"))
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--native-source-commit", type=str, default=None)
    parser.add_argument("--native-wheel", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    roots = {"relay": args.relay_root, "beamsearch": args.beamsearch_root}
    records = [
        {"source": source, **benchmark_one(roots[source] / f"{name}.stim", shots, args.iterations)}
        for source, name, shots in FIXTURES
    ]
    result = {
        "schema": "circuit_bp_cpu_profile_v1", "stim_version": stim.__version__,
        "sampling_seed": 20261021, "rule": "min_sum", "tie_break": "one",
        "sinter_interface": "compiled_decoder_bit_packed_v1",
        "native_identity": native_identity(), "records": records,
        "claim_limit": "bounded CPU mechanism and throughput profile; no paper-curve reproduction or equal-algorithm claim",
    }
    if args.native_source_commit is not None:
        result["native_source_commit_declared"] = args.native_source_commit
    if args.native_wheel is not None:
        result["native_wheel_sha256"] = sha256(args.native_wheel.read_bytes()).hexdigest()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    else:
        print(payload)


if __name__ == "__main__":
    main()
