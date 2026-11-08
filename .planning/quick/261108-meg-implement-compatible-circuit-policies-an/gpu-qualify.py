"""Bounded hardware qualification; no publication LER claims."""
from dataclasses import replace
from pathlib import Path
import json
import time
import sys
from hashlib import sha256
import numpy as np
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
from bp_registry.resolution import STABLE_SPA_F64, BpFloodingPolicy, ResolutionPolicy
from bp_registry.gpu import CudaFlooding

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261108)
ms = BpFloodingPolicy(check_rule="min_sum", resolution=ResolutionPolicy("float64"),
    version="bp-flooding-policy-v2", check_stabilization="exact_unity",
    product_epsilon=1e-10, hard_decision="map_pauli", alpha=.8, damping=.1)
bb = json.loads(Path("data/artifacts/bb72-css.json").read_text())
code = PauliCode(np.concatenate((np.asarray(bb["hx"], np.uint8), 3*np.asarray(bb["hz"], np.uint8))))
h = np.load("data/artifacts/b1-panteleev-kalachev-v3.npz")["hx"].astype(np.uint8)
records = []
for family in ("binary", "pauli"):
    if family == "binary":
        errors = (rng.random((1024, h.shape[1])) < .04).astype(np.uint8)
        syndromes = (errors @ h.T) % 2
    else:
        errors = rng.choice(4, size=(1024, code.n), p=[.88, .04, .04, .04]).astype(np.uint8)
        syndromes = np.asarray([code.syndrome(error) for error in errors], np.uint8)
    for name, policy in (("spa", STABLE_SPA_F64), ("nms", ms)):
        if family == "binary":
            graph = CompiledBinaryFlooding.from_check_matrix(h, policy=policy,
                rule="spa" if name == "spa" else "min_sum")
            kwargs = {"error_rate": .04}
            gpu = CudaFlooding.from_binary(graph, error_rate=.04)
        else:
            graph = CompiledBp4Graph.from_code(code, np.tile([.88, .04, .04, .04], (code.n, 1)), policy=policy)
            kwargs = {}
            gpu = CudaFlooding.from_pauli(graph)
        start = time.perf_counter()
        graph.run_batch(syndromes[:2], max_iterations=20, **kwargs)
        cpu_first = time.perf_counter() - start
        start = time.perf_counter()
        gpu.run_batch(syndromes[:2], max_iterations=20)
        gpu_first = time.perf_counter() - start
        graph.run_batch(syndromes[:2], max_iterations=20, workers=2, **kwargs)
        cpu_times, cpu_two_times, gpu_times = [], [], []
        for _ in range(3):
            start = time.perf_counter()
            expected = graph.run_batch(syndromes, max_iterations=20, **kwargs)
            cpu_times.append(time.perf_counter() - start)
            start = time.perf_counter()
            expected_two = graph.run_batch(syndromes, max_iterations=20, workers=2, **kwargs)
            cpu_two_times.append(time.perf_counter() - start)
            np.testing.assert_array_equal(expected_two.candidates, expected.candidates)
            start = time.perf_counter()
            actual = gpu.run_batch(syndromes, max_iterations=20)
            gpu_times.append(time.perf_counter() - start)
            np.testing.assert_array_equal(actual.candidates, expected.candidates)
            np.testing.assert_array_equal(actual.iterations, expected.iterations)
            np.testing.assert_array_equal(actual.converged, expected.converged)
        ledger = ROOT / f"gpu-{family}-{name}.jsonl"
        start = time.perf_counter()
        actual.write_ledger(ledger)
        ledger_export = time.perf_counter() - start
        replay = gpu.verify_ledger(ledger)
        record = {"family": family, "policy": name, "shots": len(syndromes), "max_iterations": 20,
                  "cpu_workers": 1, "cpu_first_call_seconds": cpu_first, "gpu_first_call_seconds": gpu_first,
                  "cpu_warm_seconds": cpu_times, "gpu_warm_seconds": gpu_times,
                  "cpu_two_worker_seconds": cpu_two_times,
                  "ledger_export_seconds": ledger_export,
                  "end_to_end_speedup": float(np.median(cpu_times)/np.median(gpu_times)),
                  "speedup_vs_two_cpu_workers": float(np.median(cpu_two_times)/np.median(gpu_times)),
                  "gpu_runtime": actual.metadata["runtime"],
                  "gpu_last_compute_transfer_seconds": actual.metadata["elapsed_seconds_including_transfers_and_any_jit"],
                  "parity": "all_candidates_iterations_convergence_exact", "stored_cpu_replay": replay}
        records.append(record)
        print(json.dumps(record), flush=True)
(ROOT / "gpu-qualification.json").write_text(json.dumps(records, indent=2) + "\n")
(ROOT / "source-sha256.json").write_text(json.dumps({
    str(path): sha256(path.read_bytes()).hexdigest()
    for path in [Path("src/bp_registry/gpu.py"), Path("src/bp_registry/cuda_kernels.py"),
                 Path("src/bp_registry/batch_records.py"), Path(__file__)]
}, indent=2) + "\n")

# CPU circuit timing on the same isolated allocation, using a pinned paper circuit.
import stim
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder
circuit = stim.Circuit.from_file("data/circuits/relay-v0.2.2/bicycle_bivariate_18_4_3_memory_X.stim")
dem = circuit.detector_error_model(decompose_errors=False)
events, _ = circuit.compile_detector_sampler(seed=20261108).sample(shots=4, separate_observables=True)
base = CircuitPolicy(rule="normalized_min_sum", parameter=.8, max_iterations=3)
scalar = PolicyBpSinterDecoder(base.model_copy(update={"backend": "scalar"})).compile_decoder_for_dem(dem=dem)
compiled = PolicyBpSinterDecoder(base.model_copy(update={"backend": "compiled"})).compile_decoder_for_dem(dem=dem)
compiled.decode_detailed(events[:1])
circuit_times = {"scalar": [], "compiled": []}
for _ in range(2):
    start = time.perf_counter()
    expected = scalar.decode_detailed(events)
    circuit_times["scalar"].append(time.perf_counter() - start)
    start = time.perf_counter()
    actual = compiled.decode_detailed(events)
    circuit_times["compiled"].append(time.perf_counter() - start)
    np.testing.assert_array_equal(actual.faults, expected.faults)
    np.testing.assert_array_equal(actual.predictions, expected.predictions)
    np.testing.assert_array_equal(actual.iterations, expected.iterations)
actual.write_ledger(ROOT / "circuit-compiled.jsonl")
circuit_receipt = {"shots": 4, "max_iterations": 3, "detectors": compiled.model.table.check_count,
                   "faults": compiled.model.table.variable_count, "edges": compiled.model.table.edge_count,
                   "times_seconds": circuit_times, "parity": "faults_observables_iterations_exact",
                   "speedup": float(np.median(circuit_times["scalar"])/np.median(circuit_times["compiled"])),
                   "replay": compiled.verify_ledger(ROOT / "circuit-compiled.jsonl")}
(ROOT / "circuit-qualification.json").write_text(json.dumps(circuit_receipt, indent=2) + "\n")
print(json.dumps(circuit_receipt), flush=True)
