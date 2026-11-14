"""Audited canonical BP -> qualified standalone OSD; no hidden truth handoff."""
from collections import Counter
import fcntl
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bp_study_runtime as rt
from bp_registry.postprocessing.osd import UniformOsd, VERSION

BATCH = 4096
TIMING_FIELDS = {'decode_ns', 'bp_decode_ns', 'osd_decode_ns'}
WORK_KEYS = ('sort_items', 'pivot_probes', 'row_xor_words', 'row_swaps', 'pivots',
             'candidate_evaluations', 'candidate_score_words', 'original_syndrome_checks',
             'matrix_words_copied', 'back_substitution_words', 'affine_single_pivot_probes',
             'affine_pair_xor_words', 'original_check_words')


def state(job):
    base = rt.state(job)
    code = rt.load_artifact(rt.REPO, job['code_artifact'], expected_semantic_sha256=job['code_semantic_sha256']).code
    settings = job['decoder']['postprocessing']
    if job['decoder']['family'] != 'binary_css' or job['decoder']['noise_model'] != 'x_only':
        raise ValueError('qualified OSD study requires binary X-only canonical BP')
    return base, UniformOsd(code.hz, method=settings['method'], order=settings['order'])


def decode_bp(base, syndrome):
    """Identical canonical sweeps/stopping to the frozen Roffe controller."""
    job, _, packed, graphs = base
    prior = math.log((1-job['physical_p'])/job['physical_p'])
    old = np.full(graphs[0].table.edge_count, prior)
    for iteration in range(1, job['decoder']['max_iterations']+1):
        sweep = graphs[min(iteration, len(graphs))-1].sweep(old, syndrome, error_rate=job['physical_p'])
        if np.array_equal(rt.parent.base._syndrome(packed[1], sweep.candidate), syndrome):
            return sweep.candidate, sweep.beliefs, True, iteration
        old = sweep.new_v2c
    return sweep.candidate, sweep.beliefs, False, iteration


def warm(value):
    base, processor = value
    syndrome = np.zeros(processor.check_matrix.shape[0], dtype=np.uint8)
    _, posterior, _, _ = decode_bp(base, syndrome)
    processor.decode(syndrome, posterior, error_rate=base[0]['physical_p'])


def event(value, shot):
    base, processor = value
    job, n, packed, _ = base
    truth = rt.parent.base._sample(job['seed'], round(job['physical_p']*100000), shot, n, depolarizing=False)
    syndrome = rt.parent.base._syndrome(packed[1], truth)
    start = time.perf_counter_ns()
    bp_candidate, posterior, converged, iterations = decode_bp(base, syndrome)
    bp_ns = time.perf_counter_ns()-start
    result, osd_ns = None, 0
    candidate = bp_candidate
    if not converged:
        # Only observed syndrome, canonical terminal beliefs and original prior
        # reach OSD. Evaluation truth is consumed strictly after final selection.
        start = time.perf_counter_ns()
        result = processor.decode(syndrome, posterior, error_rate=job['physical_p'])
        osd_ns = time.perf_counter_ns()-start
        candidate = result.candidate
    outcome, _ = rt.parent.outcome(*packed, truth, candidate, joint=False)
    if outcome == 'type_i':
        raise RuntimeError('qualified BP/OSD output fails independent original-code evaluation')
    return {'schema': 'canonical-bp-osd-shot-v1', 'shot': shot, 'outcome': outcome,
            'iterations': iterations, 'branch_iterations': [iterations],
            'directed_edge_updates': 2*job['graph_edges']*iterations,
            'bp_converged': bool(converged), 'osd_invoked': not bool(converged),
            'decode_ns': bp_ns+osd_ns, 'bp_decode_ns': bp_ns, 'osd_decode_ns': osd_ns,
            'error_sha256': sha256(truth.tobytes()).hexdigest(),
            'syndrome_sha256': sha256(syndrome.tobytes()).hexdigest(),
            'bp_candidate_sha256': sha256(bp_candidate.tobytes()).hexdigest(),
            'terminal_posterior_sha256': sha256(np.ascontiguousarray(posterior, dtype='<f8').tobytes()).hexdigest(),
            'candidate_sha256': sha256(candidate.tobytes()).hexdigest(),
            'osd_candidate_set_sha256': result.candidate_set_sha256 if result else None,
            'osd_selected_index': result.selected_index if result else None,
            'osd_work': {key: int(result.work[key]) if result else 0 for key in WORK_KEYS}}


class Ledger(rt.Ledger):
    def __init__(self, directory, job):
        self.osd_calls = self.bp_ns = self.osd_ns = 0
        self.osd_work = Counter({k: 0 for k in WORK_KEYS})
        super().__init__(directory, job)

    def add(self, row, line):
        settings = self.job['decoder']['postprocessing']
        if (row.get('schema') != 'canonical-bp-osd-shot-v1'
                or type(row.get('osd_invoked')) is not bool or type(row.get('bp_converged')) is not bool
                or row['osd_invoked'] == row['bp_converged'] or set(row.get('osd_work', {})) != set(WORK_KEYS)
                or any(type(v) is not int or v < 0 for v in row['osd_work'].values())
                or any(type(row.get(k)) is not int or row[k] < 0 for k in TIMING_FIELDS)
                or row['decode_ns'] != row['bp_decode_ns']+row['osd_decode_ns'] or row['outcome'] == 'type_i'):
            raise ValueError('invalid canonical BP/OSD event or work/timing counters')
        for name in ('error_sha256', 'syndrome_sha256', 'bp_candidate_sha256', 'terminal_posterior_sha256', 'candidate_sha256'):
            value = row.get(name)
            if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('invalid original-coordinate BP/OSD provenance digest')
        if row['osd_invoked']:
            expected = (1 if settings['method'] == 'OSD_0' else
                        1+self.job['non_pivot_count']+settings['order']*(settings['order']-1)//2)
            if (row['iterations'] != self.job['decoder']['max_iterations']
                    or row['osd_work']['candidate_evaluations'] != expected
                    or row['osd_work']['sort_items'] != self.job['n']
                    or row['osd_work']['original_syndrome_checks'] != 1
                    or type(row['osd_selected_index']) is not int or not 0 <= row['osd_selected_index'] < expected
                    or not isinstance(row['osd_candidate_set_sha256'], str) or len(row['osd_candidate_set_sha256']) != 64):
                raise ValueError('invalid fallback activation/candidate enumeration')
        elif (row['osd_decode_ns'] != 0 or any(row['osd_work'].values())
              or row['osd_selected_index'] is not None or row['osd_candidate_set_sha256'] is not None
              or row['bp_candidate_sha256'] != row['candidate_sha256']):
            raise ValueError('converged BP must bypass OSD without changing its candidate')
        super().add(row, line)
        self.osd_calls += int(row['osd_invoked'])
        self.bp_ns += row['bp_decode_ns']; self.osd_ns += row['osd_decode_ns']
        self.osd_work.update(row['osd_work'])

    def summary(self):
        return {**super().summary(), 'osd_calls': self.osd_calls, 'bp_decode_ns': self.bp_ns,
                'osd_decode_ns': self.osd_ns, 'osd_work': dict(self.osd_work)}


def execute(root, index):
    plan = rt.load(root)
    if type(index) is not int or not 0 <= index < len(plan['jobs']):
        raise ValueError('index outside frozen OSD campaign')
    job = plan['jobs'][index]
    directory = root / 'results' / job['id']; directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = directory / 'manifest.json'; expected = rt.manifest(root, job)
        if path.exists() and json.loads(path.read_text()) != expected:
            raise ValueError('frozen BP/OSD checkpoint manifest mismatch')
        if not path.exists():
            rt.write_json(path, expected)
        ledger = Ledger(directory, job)
        if not ledger.complete:
            value = state(job); warm(value)
            while not ledger.complete:
                rows, failures = [], ledger.failures
                for shot in range(ledger.shots, min(ledger.shots+BATCH, job['max_shots'])):
                    row = event(value, shot); rows.append(row)
                    failures += row['outcome'] in rt.parent.base.FAILURES
                    if failures == job['target_block_failures']:
                        break
                ledger.commit(rows)
                print(job['id'], ledger.shots, ledger.failures, 'OSD calls', ledger.osd_calls, flush=True)
        result = {**ledger.summary(), 'manifest_sha256': rt.sha(path)}
        path = directory / 'summary.json'
        if path.exists() and json.loads(path.read_text()) != result:
            raise ValueError('terminal OSD ledger/summary conflict')
        rt.write_json(path, result)
        return result


def collect(root, require_complete=False):
    plan = rt.load(root); points = []
    for job in plan['jobs']:
        directory = root / 'results' / job['id']; path = directory / 'summary.json'
        if not path.exists():
            continue
        ledger = Ledger(directory, job)
        summary = {**ledger.summary(), 'manifest_sha256': rt.sha(directory / 'manifest.json')}
        if (summary != json.loads(path.read_text())
                or json.loads((directory / 'manifest.json').read_text()) != rt.manifest(root, job)):
            raise ValueError('BP/OSD terminal summary/manifest differs from full ledger')
        value = state(job); warm(value)
        for stored in (ledger.first, ledger.last):
            replay = event(value, stored['shot'])
            if {k: v for k, v in replay.items() if k not in TIMING_FIELDS} != {k: v for k, v in stored.items() if k not in TIMING_FIELDS}:
                raise ValueError('BP/OSD endpoint candidate/work/provenance replay mismatch')
        points.append({**job, **summary, 'summary_sha256': rt.sha(path)})
    if require_complete and len(points) != len(plan['jobs']):
        raise ValueError(f'only {len(points)}/{len(plan["jobs"])} terminal OSD points; cannot publish complete campaign')
    result = {'schema': 'canonical-bp-osd-verification-v1', 'plan_sha256': rt.sha(root / 'plan.json'),
              'planned_points': len(plan['jobs']), 'points': points}
    rt.write_json(root / 'verified.json', result)
    return result
