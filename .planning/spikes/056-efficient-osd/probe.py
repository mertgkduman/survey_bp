"""Run native/full-candidate qualification and alternating warmed benchmarks."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys
import time

import numpy as np

import native
from bp_registry.postprocessing.osd import UniformOsd

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / 'data/reproductions'))
import bp_study_runtime as rt


def terminal(job, syndrome):
    _, _, _, graphs = rt.state(job)
    old = np.full(graphs[0].table.edge_count, np.log((1-job['physical_p'])/job['physical_p']))
    code = rt.load_artifact(REPO, job['code_artifact']).code
    for iteration in range(1, job['decoder']['max_iterations']+1):
        sweep = graphs[min(iteration, len(graphs))-1].sweep(old, syndrome, error_rate=job['physical_p'])
        if np.array_equal((code.hz @ sweep.candidate) % 2, syndrome):
            break
        old = sweep.new_v2c
    return sweep.beliefs.copy()


def qualify():
    build = native.build()
    spec = importlib.util.spec_from_file_location('_osd_oracle_test', REPO / 'tests/test_uniform_osd.py')
    oracle = importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle)
    rng = np.random.default_rng(2026111407)
    failures, checked, cases = [], 0, []
    for i in range(160):
        m, n = int(rng.integers(1, 9)), int(rng.integers(2, 11))
        h = rng.integers(0, 2, (m, n), dtype=np.uint8)
        s = h @ rng.integers(0, 2, n, dtype=np.uint8) % 2
        llr = rng.integers(-2, 3, n).astype(float) if i % 2 else rng.normal(size=n)
        _, free = oracle.oracle(h, s, llr, 0)
        for depth in sorted({0, min(3, free)}):
            ref = native.Native(h, depth)
            expected, candidates = ref.decode(s, llr)
            value = UniformOsd(h, method='OSD_CS' if depth else 'OSD_0', order=depth).decode(s, llr, error_rate=.1)
            independent, _ = oracle.oracle(h, s, llr, depth)
            if not (np.array_equal(value.candidate, expected) and np.array_equal(value.candidates(), candidates)
                    and np.array_equal(value.candidates(), independent)):
                failures.append({'tiny_fixture': i, 'depth': depth, 'h': h.tolist(), 's': s.tolist(), 'llr': llr.tolist()})
            checked += 1; ref.close()
    print('Tiny source/oracle comparisons', checked, 'failures', len(failures), flush=True)
    plan = rt.load(REPO / 'data/reproductions/roffe-2005-07016-bp')
    benchmarks = []
    affinity = sorted(os.sched_getaffinity(0)); os.sched_setaffinity(0, {affinity[0]})
    try:
        for code in sorted(plan['codes'], key=lambda c: plan['codes'][c]['n']):
            job = next(j for j in plan['jobs'] if j['code'] == code and j['arm'] == 'binary_ms' and j['physical_p'] == .04)
            h = rt.load_artifact(REPO, job['code_artifact']).code.hz
            fixtures = []
            for i in range(16):
                s = h @ (rng.random(h.shape[1]) < .04).astype(np.uint8) % 2
                posterior = terminal(job, s)
                # Both timed interfaces consume the same unique, order-equivalent
                # ranks. This controls source qsort ties outside timing.
                order = np.argsort(posterior, kind='stable')
                ranks = np.empty(h.shape[1]); ranks[order] = np.arange(h.shape[1])
                fixtures.append((s, ranks))
                cases.append({'code': code, 'syndrome': s.tolist(), 'terminal_llr': posterior.tolist(),
                              'iteration_cap': job['decoder']['max_iterations']})
            for depth in (0, 10):
                ref = native.Native(h, depth)
                processor = UniformOsd(h, method='OSD_CS' if depth else 'OSD_0', order=depth)
                for s, posterior in fixtures:
                    expected, candidates = ref.decode(s, posterior)
                    value = processor.decode(s, posterior, error_rate=.04)
                    if not np.array_equal(value.candidate, expected) or not np.array_equal(value.candidates(), candidates):
                        failures.append({'toric': code, 'depth': depth, 'syndrome': s.tolist()})
                    if not np.all((h.astype(int) @ value.candidates().T.astype(int)) % 2 == s[:, None]):
                        failures.append({'invalid_candidate': code, 'depth': depth})
                    checked += 1
                native_times, optimized_times = [], []
                for repeat in range(6):
                    routines = ('native', 'optimized') if repeat % 2 == 0 else ('optimized', 'native')
                    for routine in routines:
                        start = time.perf_counter_ns()
                        for s, posterior in fixtures:
                            if routine == 'native':
                                ref.decode(s, posterior, trace=False, control_ties=False)
                            else:
                                processor.decode(s, posterior, error_rate=.04)
                        elapsed = (time.perf_counter_ns()-start)/len(fixtures)
                        (native_times if routine == 'native' else optimized_times).append(elapsed)
                benchmarks.append({'code': code, 'method': 'CS10' if depth else 'OSD0',
                                   'native_ns_per_call': statistics.median(native_times),
                                   'optimized_ns_per_call': statistics.median(optimized_times),
                                   'speed_ratio': statistics.median(native_times)/statistics.median(optimized_times),
                                   'native_trials': native_times, 'optimized_trials': optimized_times})
                ref.close()
            print('Validated/benchmarked', code, flush=True)
    finally:
        os.sched_setaffinity(0, affinity)
    result = {'status': 'failed' if failures else 'passed', 'checked_complete_candidate_sets': checked,
              'failures': failures, 'native_build': build, 'benchmarks': benchmarks,
              'affinity_during_benchmark': [affinity[0]], 'affinity_before': affinity,
              'timing_scope': 'warm standalone decoder calls, matched ordered inputs; native final-only vs optimized full candidates/digest/check; constructor/JIT excluded',
              'tie_convention': 'signed ascending; original-column ties controlled before native call',
              'primary_ldpc_version': __import__('ldpc').__version__,
              'implementation_sha256': sha256((REPO / 'src/bp_registry/postprocessing/osd.py').read_bytes()).hexdigest()}
    (ROOT / 'qualification.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    (ROOT / 'terminal-fixtures.json').write_text(json.dumps(cases, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'candidate_sets': checked, 'failures': len(failures),
                      'timings': [{k: r[k] for k in ('code', 'method', 'native_ns_per_call', 'optimized_ns_per_call', 'speed_ratio')} for r in benchmarks]}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    qualify()
