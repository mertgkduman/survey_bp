"""Matched warmed GB46 BP4 benchmark for the optional compiled prototype."""

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

from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.problems import QuaternaryOriginalProblem, compile_css_artifact


ROOT = Path(__file__).resolve().parents[1]
AS_BUILD = Path('/tmp/phase10-asced-native/build')


def measure(fn, syndromes: list[np.ndarray], *, batches: int) -> list[dict[str, object]]:
    rows = []
    for _ in range(3):
        start = time.perf_counter_ns()
        outputs = [fn(s) for _ in range(batches) for s in syndromes]
        elapsed = time.perf_counter_ns() - start
        first_batch = outputs[:len(syndromes)]
        rows.append({'ns_per_shot': elapsed / len(outputs),
                     'candidates': [x[0].tolist() for x in first_batch],
                     'candidate_sha256': sha256(b''.join(x[0].tobytes() for x in first_batch)).hexdigest(),
                     'iterations': [int(x[1]) for x in first_batch],
                     'success': [bool(x[2]) for x in first_batch]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = (ROOT / 'data/artifacts/gb46-h44.alist').read_bytes()
    code = compile_css_artifact(parse_pinned_gb46_css(raw), source_artifact_identity='gb46-h44-pinned-alist')
    rng = np.random.default_rng(11019)
    rng.random((24, 72))
    errors = np.zeros((8, code.n), dtype=np.uint8)
    for row in errors:
        selected = rng.random(code.n) < .08
        row[selected] = rng.choice(np.asarray([1, 2, 3], dtype=np.uint8), size=int(selected.sum()))
    syndromes = [code.syndrome(error) for error in errors]
    priors = np.tile([.92, .08/3, .08/3, .08/3], (code.n, 1))
    start = time.perf_counter_ns()
    compiled = CompiledBp4Graph.from_code(code, priors)
    graph_setup_ns = time.perf_counter_ns() - start
    start = time.perf_counter_ns()
    compiled.run(syndromes[0], max_iterations=8)
    first_call_ns = time.perf_counter_ns() - start
    reference = ScalarLlrBp4Kernel()
    result = {'schema': 'compiled-bp4-benchmark-v1', 'host': platform.node(),
              'affinity': sorted(os.sched_getaffinity(0)), 'python': platform.python_version(),
              'numba': __import__('numba').__version__, 'alist_sha256': sha256(raw).hexdigest(),
              'syndrome_sha256': sha256(b''.join(s.tobytes() for s in syndromes)).hexdigest(),
              'shape': list(code.checks.shape), 'edges': int(np.count_nonzero(code.checks)),
              'p': .08, 'cap': 8, 'shots': 8, 'graph_setup_ns': graph_setup_ns,
              'first_call_ns': first_call_ns, 'modes': {}}
    for stop, mode in ((True, 'early'), (False, 'fixed8')):
        def run_reference(s):
            problem = QuaternaryOriginalProblem('original-benchmark', code, s)
            session = reference.new_session(problem, priors)
            if stop:
                out = session.run(max_iterations=8)
            else:
                for _ in range(8):
                    out = session.sweep(stop_on_convergence=False)
            return out.candidate, out.iteration, out.converged
        def run_compiled(s):
            out = compiled.run(s, max_iterations=8, stop_on_convergence=stop)
            return out.candidate, out.iterations, out.converged
        run_reference(syndromes[0])
        run_compiled(syndromes[0])
        reference_rows = measure(run_reference, syndromes, batches=1)
        compiled_rows = measure(run_compiled, syndromes, batches=100)
        assert reference_rows[0]['candidate_sha256'] == compiled_rows[0]['candidate_sha256']
        assert reference_rows[0]['iterations'] == compiled_rows[0]['iterations']
        assert reference_rows[0]['success'] == compiled_rows[0]['success']
        result['modes'][mode] = {'reference': reference_rows, 'compiled': compiled_rows}
        print(f"{mode}: Python {statistics.median(x['ns_per_shot'] for x in reference_rows)/1e6:.3f} ms; "
              f"compiled {statistics.median(x['ns_per_shot'] for x in compiled_rows)/1e6:.4f} ms")

    flags = (AS_BUILD / 'CMakeFiles/QEC_lib.dir/flags.make').read_text().splitlines()
    includes = next(line.split(' = ', 1)[1].split() for line in flags if line.startswith('CXX_INCLUDES = '))
    with tempfile.TemporaryDirectory(prefix='bp4-compiled-benchmark-') as directory:
        work = Path(directory)
        driver = work / 'asced_bp4'
        subprocess.run(['g++', '-O3', '-DNDEBUG', '-std=c++20', '-fopenmp', *includes,
                        str(ROOT / 'scripts/benchmark_asced_bp4.cpp'), str(AS_BUILD / 'libQEC_lib.a'),
                        '-o', str(driver)], check=True)
        h = code.checks.copy()
        h[code.checks == 2], h[code.checks == 3] = 3, 2
        input_path = work / 'workload.txt'
        with input_path.open('w') as file:
            file.write(f'{h.shape[0]} {h.shape[1]} {len(syndromes)} 8 0.08\n')
            for row in h:
                file.write(' '.join(map(str, row)) + '\n')
            for row in syndromes:
                file.write(' '.join(map(str, row)) + '\n')
        native = json.loads(subprocess.check_output([str(driver), str(input_path)], text=True))
        result['native_asced_bp4'] = native
        for mode in ('early', 'fixed8'):
            candidates = [[{0: 0, 1: 1, 2: 3, 3: 2}[int(digit)] for digit in row]
                          for row in native['timings'][mode][0]['candidates_native_ixzy']]
            result['modes'][mode]['native_candidate_agreement'] = sum(
                a == b for a, b in zip(candidates, result['modes'][mode]['compiled'][0]['candidates'], strict=True))
            print(f"{mode}: native C++ {statistics.median(x['ns_per_shot'] for x in native['timings'][mode])/1e6:.4f} ms; "
                  f"candidate agreement {result['modes'][mode]['native_candidate_agreement']}/8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
