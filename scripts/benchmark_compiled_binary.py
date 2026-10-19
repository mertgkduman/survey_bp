"""Matched warmed CSS benchmark for the optional compiled binary prototype."""

from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import platform
import statistics
import time

import ldpc
import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64
from bp_registry.canonical.schedules import FloodingSchedule
from bp_registry.canonical.updates import MinSumUpdate


ROOT = Path(__file__).resolve().parents[1]


def measure(fn, syndromes: np.ndarray, *, batches: int) -> list[dict[str, object]]:
    rows = []
    for _ in range(3):
        start = time.perf_counter_ns()
        outputs = [fn(s) for _ in range(batches) for s in syndromes]
        elapsed = time.perf_counter_ns() - start
        first_batch = outputs[:len(syndromes)]
        rows.append({'ns_per_shot': elapsed / len(outputs),
                     'candidate_sha256': sha256(b''.join(x[0].tobytes() for x in first_batch)).hexdigest(),
                     'iterations': [int(x[1]) for x in first_batch],
                     'success': [bool(x[2]) for x in first_batch]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--code', choices=('bb72', 'hgp225'), default='bb72')
    parser.add_argument('--shots', type=int, default=24)
    args = parser.parse_args()
    if args.shots < 1:
        parser.error('--shots must be positive')
    if args.code == 'bb72':
        raw = (ROOT / 'data/artifacts/bb72-css.json').read_bytes()
        h = np.asarray(json.loads(raw)['hz'], dtype=np.uint8)
    else:
        raw = (ROOT / 'data/artifacts/hgp-gallager-3-4-seed-20260923.npz').read_bytes()
        with np.load(BytesIO(raw)) as artifact:
            h = np.asarray(artifact['hz'], dtype=np.uint8)
    rng = np.random.default_rng(11019)
    errors = (rng.random((args.shots, h.shape[1])) < .08).astype(np.uint8)
    syndromes = np.asarray((errors @ h.T) % 2, dtype=np.uint8)
    result = {'schema': 'compiled-binary-benchmark-v1', 'host': platform.node(),
              'affinity': sorted(os.sched_getaffinity(0)), 'python': platform.python_version(),
              'numba': __import__('numba').__version__, 'ldpc': __import__('importlib.metadata', fromlist=['version']).version('ldpc'),
              'artifact_sha256': sha256(raw).hexdigest(), 'syndrome_sha256': sha256(syndromes.tobytes()).hexdigest(),
              'code': args.code, 'shape': list(h.shape), 'edges': int(h.sum()),
              'p': .08, 'cap': 10, 'shots': args.shots, 'rules': {}}
    for rule in ('spa', 'min_sum'):
        reference = BinarySpaKernel() if rule == 'spa' else BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
        start = time.perf_counter_ns()
        compiled = CompiledBinaryFlooding.from_check_matrix(h, rule=rule)
        bound = compiled.bind_error_rate(.08)
        graph_setup_ns = time.perf_counter_ns() - start
        start = time.perf_counter_ns()
        bound.run(syndromes[0], max_iterations=10)
        first_call_ns = time.perf_counter_ns() - start
        schedule = FloodingSchedule(compiled.table, kernel=reference, profile=reference.profile)
        native = ldpc.BpDecoder(h, error_rate=.08, max_iter=10,
                                bp_method='product_sum' if rule == 'spa' else 'minimum_sum',
                                ms_scaling_factor=1.0, schedule='parallel', omp_thread_count=1)
        def run_reference(s):
            v2c = schedule.initialize(.08)
            for iteration in range(1, 11):
                sweep = schedule.sweep(v2c, s, error_rate=.08)
                if np.array_equal((h.astype(np.int64) @ sweep.candidate) % 2, s):
                    return sweep.candidate, iteration, True
                v2c = sweep.new_v2c
            return sweep.candidate, 10, False
        def run_compiled(s):
            out = bound.run(s, max_iterations=10)
            return out.candidate, out.iterations, out.converged
        def run_native(s):
            candidate = np.asarray(native.decode(s), dtype=np.uint8)
            return candidate, int(native.iter), bool(native.converge)
        for fn in (run_reference, run_compiled, run_native):
            fn(syndromes[0])
        reference_rows = measure(run_reference, syndromes, batches=1)
        compiled_rows = measure(run_compiled, syndromes, batches=100)
        native_rows = measure(run_native, syndromes, batches=100)
        assert reference_rows[0]['candidate_sha256'] == compiled_rows[0]['candidate_sha256']
        assert reference_rows[0]['iterations'] == compiled_rows[0]['iterations']
        assert reference_rows[0]['success'] == compiled_rows[0]['success']
        result['rules'][rule] = {'graph_setup_ns': graph_setup_ns, 'first_call_ns': first_call_ns,
                                 'reference': reference_rows, 'compiled': compiled_rows, 'ldpc': native_rows,
                                 'native_candidates_match': native_rows[0]['candidate_sha256'] == reference_rows[0]['candidate_sha256']}
        print(f"{rule}: reference {statistics.median(x['ns_per_shot'] for x in reference_rows)/1e6:.3f} ms; "
              f"compiled {statistics.median(x['ns_per_shot'] for x in compiled_rows)/1e6:.4f} ms; "
              f"ldpc {statistics.median(x['ns_per_shot'] for x in native_rows)/1e6:.4f} ms")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
