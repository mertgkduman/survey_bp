"""Exact canonical public-sweep correspondence and initial runtime pilot."""
import importlib.util
import json
from pathlib import Path
import time

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-runtime-budget'
spec = importlib.util.spec_from_file_location('_joint_runtime_qualification', ROOT / 'runtime.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)


def main():
    plan = r.rt.load(r.ORIGINAL); failures, checked, states = [], 0, {'converged': 0, 'capped': 0}
    settings = [
        {'damping': .5, 'alpha_mode': 'paper', 'alpha': 1., 'beta': 0.},
        {'damping': .3, 'alpha_mode': 'paper', 'alpha': .9, 'beta': .25},
        {'damping': .7, 'alpha_mode': 'constant', 'alpha': .75, 'beta': .5},
        {'damping': 0., 'alpha_mode': 'constant', 'alpha': 1., 'beta': 1.}]
    pilots = []
    for code in plan['codes']:
        for arm in ('binary_ms', 'qbp_ms'):
            for p in (.02, .08):
                job = next(j for j in plan['jobs'] if j['code'] == code and j['arm'] == arm and j['matched_x_rate'] == p)
                base = r.rt.state(job)
                for controls in settings:
                    prepared = r.engine.Prepared(base, controls)
                    for shot in (0, 7):
                        _, syndrome = r.sample(base, r.TUNING_SEED, shot)
                        actual = prepared.decode(syndrome, 11)
                        expected = prepared.public_reference(syndrome, 11)
                        if any(not np.array_equal(a, b) for a, b in zip(actual, expected)):
                            failures.append({'job': job['id'], 'controls': controls, 'shot': shot})
                        checked += 1; states['converged' if actual[2] else 'capped'] += 1
                    zero = np.zeros(len(prepared.graph.row_ptr)-1, dtype=np.uint8)
                    assert prepared.decode(zero, 11)[3] == 1
                controls = r.baseline(job); prepared = r.engine.Prepared(base, controls)
                _, syndrome = r.sample(base, r.TUNING_SEED, 3)
                actual = prepared.decode(syndrome, job['decoder']['max_iterations'])
                expected = prepared.public_reference(syndrome, job['decoder']['max_iterations'])
                assert all(np.array_equal(a, b) for a, b in zip(actual, expected))
                checked += 1
                start = time.perf_counter_ns()
                for shot in range(32):
                    _, syndrome = r.sample(base, r.TUNING_SEED, shot)
                    prepared.decode(syndrome, job['decoder']['max_iterations'])
                pilots.append({'code': code, 'family': arm, 'matched_p': p,
                               'complete_sample_plus_decode_ns': (time.perf_counter_ns()-start)/32})
                print(code, arm, p, 'checked', checked, flush=True)
    result = {'status': 'failed' if failures else 'passed', 'failures': failures,
              'exact_terminal_comparisons': checked, 'stopping_cases': states,
              'engine_sha256': r.rt.sha(ROOT / 'engine.py'), 'pilot': pilots,
              'scope': 'binary and joint-Pauli min-sum; both scaling schedules; damping/scale/offset combined; exact candidate/belief/stopping correspondence; no shortcut on zero syndrome; final n-cap checks on each code/family/rate'}
    r.rt.write_json(HERE / 'qualification.json', result)
    assert not failures


if __name__ == '__main__': main()
