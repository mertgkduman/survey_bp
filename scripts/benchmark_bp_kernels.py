"""Bounded, reproducible local timing of project and native BP kernels.

Run with .venv/bin/python scripts/benchmark_bp_kernels.py --output PATH.
The C++ driver is built separately from scripts/benchmark_asced_bp4.cpp.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time

import numpy as np

from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64
from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule
from bp_registry.canonical.updates import MinSumUpdate
from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.problems import QuaternaryOriginalProblem, compile_css_artifact
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel


ROOT = Path(__file__).resolve().parents[1]
AS_SOURCE = Path('/tmp/phase10-asced-native/source/quantum_asced')
AS_BUILD = Path('/tmp/phase10-asced-native/build')


def ns_per_shot(fn, samples, repeats=3):
    rows = []
    for repeat in range(repeats):
        start = time.perf_counter_ns()
        outputs = [fn(sample) for sample in samples]
        elapsed = time.perf_counter_ns() - start
        row = {'ns_per_shot': elapsed / len(samples), 'iterations': [int(x[1]) for x in outputs],
                     'success': [bool(x[2]) for x in outputs],
                     'candidate_sha256': sha256(b''.join(x[0].tobytes() for x in outputs)).hexdigest()}
        if repeat == 0:
            row['candidates'] = [x[0].tolist() for x in outputs]
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import ldpc
    import relay_bp

    rng = np.random.default_rng(11019)
    binary = json.loads((ROOT / 'data/artifacts/bb72-css.json').read_text())
    h = np.asarray(binary['hz'], dtype=np.uint8)
    p = 0.08
    errors = (rng.random((24, h.shape[1])) < p).astype(np.uint8)
    syndromes = np.asarray((errors @ h.T) % 2, dtype=np.uint8)
    # Warm each implementation before timed calls. Decoder setup stays outside timing.
    spa = BinarySpaKernel()
    ms = BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
    table = EdgeTable.from_check_matrix(h)
    spa_schedule = FloodingSchedule(table, kernel=spa)
    ms_schedule = FloodingSchedule(table, kernel=ms, profile=MIN_SUM_CPU_F64)
    ld_spa = ldpc.BpDecoder(h, error_rate=p, max_iter=10, bp_method='product_sum', schedule='parallel', omp_thread_count=1)
    ld_ms = ldpc.BpDecoder(h, error_rate=p, max_iter=10, bp_method='minimum_sum', ms_scaling_factor=1.0, schedule='parallel', omp_thread_count=1)
    relay = relay_bp.MinSumBPDecoderTraceF64(h, error_priors=np.full(h.shape[1], p), max_iter=10, alpha=None, gamma0=None)

    def canonical(kernel, s):
        out = kernel.run(h, s, error_rate=p, max_iterations=10)
        return out.candidate, out.iterations, out.converged

    def cached(schedule, s):
        v2c = schedule.initialize(p)
        for iteration in range(1, 11):
            sweep = schedule.sweep(v2c, s, error_rate=p)
            if np.array_equal((h.astype(np.int64) @ sweep.candidate) % 2, s):
                return sweep.candidate, iteration, True
            v2c = sweep.new_v2c
        return sweep.candidate, 10, False

    def ldpc_run(decoder, s):
        candidate = np.asarray(decoder.decode(s), dtype=np.uint8)
        return candidate, int(decoder.iter), bool(decoder.converge)

    def relay_run(s):
        out = relay.decode_detailed(s)
        return np.asarray(out.decoding, dtype=np.uint8), int(out.iterations), bool(out.success)

    implementations = {
        'canonical_spa': lambda s: canonical(spa, s),
        'canonical_spa_cached_graph': lambda s: cached(spa_schedule, s),
        'ldpc_spa': lambda s: ldpc_run(ld_spa, s),
        'canonical_min_sum': lambda s: canonical(ms, s),
        'canonical_min_sum_cached_graph': lambda s: cached(ms_schedule, s),
        'ldpc_min_sum': lambda s: ldpc_run(ld_ms, s),
        'relay_min_sum_trace': relay_run,
    }
    binary_rows = {}
    for name, fn in implementations.items():
        fn(syndromes[0])
        binary_rows[name] = ns_per_shot(fn, syndromes)

    css = parse_pinned_gb46_css((ROOT / 'data/artifacts/gb46-h44.alist').read_bytes())
    code = compile_css_artifact(css, source_artifact_identity='gb46-h44-pinned-alist')
    qh = code.checks
    qerrors = np.zeros((8, code.n), dtype=np.uint8)
    for i in range(8):
        hit = rng.random(code.n) < 0.08
        qerrors[i, hit] = rng.choice(np.array([1, 2, 3], dtype=np.uint8), size=int(hit.sum()))
    qsyndromes = np.asarray([code.syndrome(e) for e in qerrors], dtype=np.uint8)
    priors = np.tile(np.array([1-.08, .08/3, .08/3, .08/3]), (code.n, 1))
    qkernel = ScalarLlrBp4Kernel()

    def canonical_bp4(s):
        problem = QuaternaryOriginalProblem('original-benchmark', code, s)
        out = qkernel.new_session(problem, priors).run(max_iterations=8)
        return out.candidate, out.iteration, out.converged

    def canonical_bp4_fixed(s):
        problem = QuaternaryOriginalProblem('original-benchmark-fixed', code, s)
        session = qkernel.new_session(problem, priors)
        for _ in range(8):
            out = session.sweep(stop_on_convergence=False)
        return out.candidate, out.iteration, out.converged

    qrows = {}
    for name, fn in {'canonical_bp4_early': canonical_bp4, 'canonical_bp4_fixed8': canonical_bp4_fixed}.items():
        fn(qsyndromes[0])
        qrows[name] = ns_per_shot(fn, qsyndromes)

    cpp_path = ROOT / 'scripts/benchmark_asced_bp4.cpp'
    flags = (AS_BUILD / 'CMakeFiles/QEC_lib.dir/flags.make').read_text().splitlines()
    includes = next(line.split(' = ', 1)[1].split() for line in flags if line.startswith('CXX_INCLUDES = '))
    with tempfile.TemporaryDirectory(prefix='bp-kernel-benchmark-') as directory:
        work = Path(directory)
        driver = work / 'asced_bp4'
        compile_cmd = ['g++', '-O3', '-DNDEBUG', '-std=c++20', '-fopenmp', *includes,
                       str(cpp_path), str(AS_BUILD / 'libQEC_lib.a'), '-o', str(driver)]
        subprocess.run(compile_cmd, check=True)
        input_path = work / 'workload.txt'
        # Author native uses I=0,X=1,Z=2,Y=3; canonical uses I=0,X=1,Y=2,Z=3.
        native_h = qh.copy()
        native_h[qh == 2], native_h[qh == 3] = 3, 2
        with input_path.open('w') as file:
            file.write(f'{qh.shape[0]} {qh.shape[1]} {len(qsyndromes)} 8 0.08\n')
            for row in native_h:
                file.write(' '.join(map(str, row)) + '\n')
            for row in qsyndromes:
                file.write(' '.join(map(str, row)) + '\n')
        native = json.loads(subprocess.check_output([str(driver), str(input_path)], text=True))
        for mode, canonical_name in [('early', 'canonical_bp4_early'), ('fixed8', 'canonical_bp4_fixed8')]:
            native_candidates = native['timings'][mode][0]['candidates_native_ixzy']
            canonical_candidates = qrows[canonical_name][0]['candidates']
            converted = [[{0: 0, 1: 1, 2: 3, 3: 2}[int(digit)] for digit in shot]
                         for shot in native_candidates]
            native['timings'][mode][0]['candidate_agreement_count'] = sum(
                left == right for left, right in zip(converted, canonical_candidates, strict=True))

    result = {
        'schema': 'bp-kernel-benchmark-v1', 'date': '2026-10-19',
        'host': {'node': platform.node(), 'processor': platform.processor(), 'python': platform.python_version(),
                 'cpu_affinity': sorted(os.sched_getaffinity(0)), 'omp_num_threads': os.environ.get('OMP_NUM_THREADS')},
        'sources': {'binary_artifact_sha256': sha256((ROOT/'data/artifacts/bb72-css.json').read_bytes()).hexdigest(),
                    'gb46_alist_sha256': sha256((ROOT/'data/artifacts/gb46-h44.alist').read_bytes()).hexdigest(),
                    'asced_source': str(AS_SOURCE), 'asced_build': str(AS_BUILD),
                    'ldpc_version': __import__('importlib.metadata', fromlist=['version']).version('ldpc'),
                    'relay_source': str(Path(relay_bp.__file__).resolve())},
        'binary': {'code': 'BB72 hz', 'shape': list(h.shape), 'edges': int(h.sum()), 'p': p, 'shots': len(syndromes),
                   'max_iterations': 10, 'syndrome_sha256': sha256(syndromes.tobytes()).hexdigest(),
                   'timings': binary_rows},
        'quaternary': {'code': 'GB46 H44', 'shape': list(qh.shape), 'edges': int(np.count_nonzero(qh)), 'p': 0.08,
                       'shots': len(qsyndromes), 'max_iterations': 8,
                       'syndrome_sha256': sha256(qsyndromes.tobytes()).hexdigest(),
                       'timings': qrows, 'native_asced_bp4': native},
        'scope': 'preconstructed decoders; per-shot decode includes message initialization and termination; canonical BP4 includes per-shot immutable problem and session construction; C++ excludes graph construction',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    for family in ('binary', 'quaternary'):
        for name, rows in result[family]['timings'].items():
            print(f'{family} {name}: {statistics.median(row["ns_per_shot"] for row in rows)/1e6:.3f} ms/shot')
    for name, rows in native['timings'].items():
        print(f'quaternary native_{name}: {statistics.median(row["ns_per_shot"] for row in rows)/1e6:.3f} ms/shot')


if __name__ == '__main__':
    main()
