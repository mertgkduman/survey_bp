"""Exact controller correspondence and alternating complete-event timings."""
from collections import defaultdict
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import statistics
import time

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    slow = load('_slow_osd_campaign_probe', REPO / 'data/reproductions/roffe-2005-07016-osd/run.py')
    fast = load('_fast_osd_campaign_probe', REPO / 'data/reproductions/roffe-2005-07016-osd-fast/runtime.py')
    jobs = [j for j in slow.design()['jobs'] if j['arm'] == 'bp_osd_cs10']
    failures, timings, count, events = [], [], 0, 0
    stopping = defaultdict(int)
    affinity = sorted(os.sched_getaffinity(0)); os.sched_setaffinity(0, {affinity[0]})
    try:
        for job in jobs:
            a, b = slow.execution.state(job), fast.state(job)
            fast.warm(b)
            for shot in (0, 1, 3, 7):
                truth = slow.rt.parent.base._sample(job['seed'], round(job['physical_p']*100000), shot, job['n'], depolarizing=False)
                syndrome = slow.rt.parent.base._syndrome(a[0][2][1], truth)
                expected = slow.execution.decode_bp(a[0], syndrome)
                actual = fast.decode_bp(b[0], syndrome)
                if any(not np.array_equal(x, y) for x, y in zip(expected, actual)):
                    failures.append({'job': job['id'], 'shot': shot})
                stopping[str(actual[2])] += 1; count += 1
            if job['physical_p'] not in (.01, .04, .1):
                continue
            trials = {'slow': [], 'fast': []}
            saved = {}
            for repeat in range(4):
                for name in (('slow', 'fast') if repeat % 2 == 0 else ('fast', 'slow')):
                    runtime, state = (slow.execution, a) if name == 'slow' else (fast, b)
                    start = time.perf_counter_ns()
                    rows = [runtime.event(state, shot) for shot in range(16)]
                    trials[name].append((time.perf_counter_ns()-start)/16)
                    saved[name] = [{k: v for k, v in row.items() if k not in slow.execution.TIMING_FIELDS} for row in rows]
            if saved['slow'] != saved['fast']:
                failures.append({'event_provenance': job['id']})
            events += 16
            med = {k: statistics.median(v) for k, v in trials.items()}
            timings.append({'code': job['code'], 'p': job['physical_p'], 'ns_per_complete_event': med,
                            'speed_ratio': med['slow']/med['fast'], 'trials': trials,
                            'forecast_100M_seconds': med['fast']*.1})
            print(job['code'], job['physical_p'], med, flush=True)
    finally:
        os.sched_setaffinity(0, affinity)
    result = {'status': 'failed' if failures else 'passed', 'failures': failures,
              'exact_terminal_state_comparisons': count, 'complete_event_comparisons': events,
              'stopping': dict(stopping), 'benchmarks': timings, 'affinity': [affinity[0]],
              'scope': 'all 109 code/rate strata; exact terminal candidate and float64 beliefs, stopping and work; event provenance includes complete OSD set hash; warm complete-event wall time includes sampling, BP, optional CS10, evaluation and hashes, excludes ledger I/O/JIT',
              'implementation_sha256': sha256((REPO / 'src/bp_registry/postprocessing/canonical_bp.py').read_bytes()).hexdigest()}
    (HERE / 'compiled-loop.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('terminal states', count, 'events', events, 'failures', failures, flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
