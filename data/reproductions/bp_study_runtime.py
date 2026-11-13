"""Frozen BP-study orchestration; all message updates use existing canonical kernels."""
from __future__ import annotations
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
import fcntl
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time
import numba
import numpy as np
import scipy
from bp_registry.artifacts import load_artifact
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy

REPO = Path(__file__).resolve().parents[2]
PARENT = REPO / 'data/reproductions/mackay-0304161-unicycle'
spec = importlib.util.spec_from_file_location('_bp_study_original', PARENT / 'run.py')
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
sha, write_json = parent.sha, parent.write_json
BATCH = 64


@contextmanager
def dispatch_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'dispatch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def freeze(root: Path, design: dict, extra: list[Path]) -> dict:
    """Pin source, kernels, code bytes and software before any study sampling."""
    inherited = json.loads((PARENT / 'plan.json').read_text())['implementation_sha256']
    root.mkdir(parents=True, exist_ok=True)
    design_path = root / 'design.json'
    if design_path.exists():
        if json.loads(design_path.read_text()) != design:
            raise ValueError('refusing to change the frozen design')
    else:
        with design_path.open('x') as stream:
            json.dump(design, stream, sort_keys=True, indent=2); stream.write('\n')
    paths = [REPO / x for x in inherited] + [Path(__file__), design_path, *extra]
    paths += [REPO / x['artifact'] for x in design['codes'].values()]
    plan = {**design, 'schema': 'canonical-bp-study-v1',
            'implementation_sha256': {str(p.relative_to(REPO)): sha(p) for p in paths},
            'software': {'python': platform.python_version(), 'numpy': np.__version__,
                         'scipy': scipy.__version__, 'numba': numba.__version__}}
    root.mkdir(parents=True, exist_ok=True)
    destination = root / 'plan.json'
    if destination.exists():
        if json.loads(destination.read_text()) != plan:
            raise ValueError('refusing to change a frozen study plan')
    else:
        with destination.open('x') as stream:
            json.dump(plan, stream, sort_keys=True, indent=2); stream.write('\n')
    return plan


def load(root: Path) -> dict:
    plan = json.loads((root / 'plan.json').read_text())
    if plan['schema'] != 'canonical-bp-study-v1':
        raise ValueError('unknown study plan')
    design = json.loads((root / 'design.json').read_text())
    for field, value in design.items():
        if plan.get(field) != value:
            raise ValueError(f'frozen design differs from plan: {field}')
    for path, expected in plan['implementation_sha256'].items():
        if sha(REPO / path) != expected:
            raise ValueError(f'frozen study implementation changed: {path}')
    actual = {'python': platform.python_version(), 'numpy': np.__version__,
              'scipy': scipy.__version__, 'numba': numba.__version__}
    if plan['software'] != actual:
        raise ValueError('frozen study software changed')
    return plan


def state(job: dict):
    code = load_artifact(REPO, job['code_artifact'],
                         expected_semantic_sha256=job['code_semantic_sha256']).code
    settings = job['decoder']; joint = settings['family'] == 'bp4'
    if settings['check_rule'] == 'sum_product':
        if joint:
            graph = replace(CompiledBp4Graph.from_css(code, job['physical_p']),
                            profile=replace(QBP4_F64_V2, v2c_damping=settings['v2c_damping'], check_cap=None))
        else:
            graph = CompiledBinaryFlooding.from_check_matrix(
                code.hz, profile=replace(BINARY_SPA_F64_V2, v2c_damping=settings['v2c_damping'], check_cap=None))
        graphs = [graph]
    elif settings['check_rule'] == 'min_sum' and settings['alpha_schedule'] == '1-2**(-iteration)':
        # alpha rounds to one after iteration 54 in float64; no modified kernel.
        policy = BpFloodingPolicy(check_rule='min_sum', resolution=ResolutionPolicy('float64'),
                                 damping=settings['v2c_damping'], alpha=.5,
                                 hard_decision='map_pauli' if joint else 'min_llr',
                                 zero_syndrome_shortcut=False, version='bp-flooding-policy-v2',
                                 check_stabilization='exact_unity', product_epsilon=1e-10)
        graph = (CompiledBp4Graph.from_css(code, job['physical_p'], rule='min_sum', policy=policy) if joint
                 else CompiledBinaryFlooding.from_check_matrix(code.hz, rule='min_sum', profile=BINARY_SPA_F64_V2, policy=policy))
        graphs = [replace(graph, policy=replace(policy, alpha=1.0 - 2.0 ** -t))
                  for t in range(1, min(54, settings['max_iterations']) + 1)]
    else:
        raise ValueError('unsupported study check rule or schedule')
    packed = tuple(np.packbits(matrix, axis=1, bitorder='little') for matrix in (code.hx, code.hz, code.lx, code.lz))
    return job, code.n, packed, graphs


def decode(state, syndrome):
    job, n, packed, graphs = state
    s = job['decoder']; joint = s['family'] == 'bp4'
    if s['check_rule'] == 'sum_product':
        result = graphs[0].run(syndrome, max_iterations=s['max_iterations'],
                               **({} if joint else {'error_rate': job['physical_p']}))
        return result.candidate, result.converged, result.iterations
    prior = math.log((1 - job['physical_p']) / job['physical_p'])
    old = graphs[0].initial_v2c() if joint else np.full(graphs[0].table.edge_count, prior)
    for iteration in range(1, s['max_iterations'] + 1):
        graph = graphs[min(iteration, len(graphs)) - 1]
        sweep = graph.sweep(old, syndrome, **({} if joint else {'error_rate': job['physical_p']}))
        candidate = sweep.candidate
        if joint:
            bits = parent.base.PAULI_BITS[candidate]
            observed = np.concatenate((parent.base._syndrome(packed[0], bits[:, 1]), parent.base._syndrome(packed[1], bits[:, 0])))
            old = sweep.v2c
        else:
            observed = parent.base._syndrome(packed[1], candidate)
            old = sweep.new_v2c
        if np.array_equal(observed, syndrome):
            return candidate, True, iteration
    return candidate, False, s['max_iterations']


def event(state, shot):
    job, n, packed, graphs = state
    joint = job['decoder']['family'] == 'bp4'; p = job['physical_p']
    truth = parent.base._sample(job['seed'], round(p * 100000), shot, n, depolarizing=joint)
    bits = parent.base.PAULI_BITS[truth] if joint else truth
    syndrome = (np.concatenate((parent.base._syndrome(packed[0], bits[:, 1]), parent.base._syndrome(packed[1], bits[:, 0])))
                if joint else parent.base._syndrome(packed[1], truth))
    start = time.perf_counter_ns(); candidate, converged, iterations = decode(state, syndrome)
    elapsed = time.perf_counter_ns() - start
    label, _ = parent.outcome(*packed, truth, candidate, joint=joint)
    if converged != (label != 'type_i'):
        raise ValueError('canonical convergence disagrees with independent original-code evaluation')
    return {'shot': shot, 'outcome': label, 'iterations': iterations, 'branch_iterations': [iterations],
            'directed_edge_updates': 2 * job['graph_edges'] * iterations, 'decode_ns': elapsed,
            'error_sha256': sha256(truth.tobytes()).hexdigest(), 'syndrome_sha256': sha256(syndrome.tobytes()).hexdigest(),
            'candidate_sha256': sha256(candidate.tobytes()).hexdigest()}


class Ledger(parent.Ledger):
    def summary(self):
        result = super().summary()
        classical = result['failures'] + result['counts']['stabilizer_success']
        return {**result, 'classical_block_errors': classical, 'classical_block_error_rate': classical / result['shots']}


def manifest(root, job):
    return {'schema': 'canonical-bp-study-run-v1', 'plan_sha256': sha(root / 'plan.json'), 'job': job}


def _set_worker(value):
    global WORKER_STATE
    WORKER_STATE = value


def _batch(offset):
    job = WORKER_STATE[0]; rows = []; failures = 0
    for shot in range(offset, min(offset + BATCH, job['max_shots'])):
        row = event(WORKER_STATE, shot); rows.append(row)
        failures += row['outcome'] in parent.base.FAILURES
        if failures == job['target_block_failures']:
            break
    return rows


def batches(job, start):
    value = state(job); workers = job['workers']
    _set_worker(value)
    offsets = iter(range(start, job['max_shots'], BATCH))
    if workers == 1:
        for offset in offsets:
            yield _batch(offset)
        return
    event(value, start)  # warm qualified JIT functions before fork
    with ProcessPoolExecutor(max_workers=workers, initializer=_set_worker, initargs=(value,)) as pool:
        pending = deque()
        for _ in range(workers):
            offset = next(offsets, None)
            if offset is not None: pending.append(pool.submit(_batch, offset))
        while pending:
            yield pending.popleft().result()
            offset = next(offsets, None)
            if offset is not None: pending.append(pool.submit(_batch, offset))


def execute(root, index):
    plan = load(root)
    if type(index) is not int or not 0 <= index < len(plan['jobs']):
        raise ValueError('index outside frozen study jobs')
    job = plan['jobs'][index]
    directory = root / 'results' / job['id']; directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = directory / 'manifest.json'; expected = manifest(root, job)
        if path.exists():
            if json.loads(path.read_text()) != expected: raise ValueError('checkpoint manifest mismatch')
        else: write_json(path, expected)
        ledger = Ledger(directory, job)
        stream = batches(job, ledger.shots) if not ledger.complete else iter(())
        try:
            for rows in stream:
                ledger.commit(rows)
                print(job['id'], ledger.shots, ledger.failures, flush=True)
                if ledger.complete: break
        finally:
            if hasattr(stream, 'close'): stream.close()
        summary = {**ledger.summary(), 'manifest_sha256': sha(path)}
        path = directory / 'summary.json'
        if path.exists() and json.loads(path.read_text()) != summary: raise ValueError('terminal summary mismatch')
        write_json(path, summary)
        return summary


def collect(root, require_complete=False):
    plan = load(root); rows = []
    for job in plan['jobs']:
        directory = root / 'results' / job['id']; path = directory / 'summary.json'
        if not path.exists(): continue
        ledger = Ledger(directory, job); m = directory / 'manifest.json'
        summary = {**ledger.summary(), 'manifest_sha256': sha(m)}
        if json.loads(m.read_text()) != manifest(root, job) or json.loads(path.read_text()) != summary:
            raise ValueError('terminal ledger/manifest/summary conflict')
        value = state(job)
        for stored in (ledger.first, ledger.last):
            replay = event(value, stored['shot'])
            if {k:v for k,v in replay.items() if k!='decode_ns'} != {k:v for k,v in stored.items() if k!='decode_ns'}:
                raise ValueError('endpoint replay mismatch')
        rows.append({**job, **summary, 'summary_sha256': sha(path)})
    if require_complete and len(rows) != len(plan['jobs']):
        raise ValueError(f'only {len(rows)}/{len(plan["jobs"])} terminal points; cannot advance pipeline')
    result = {'schema': 'canonical-bp-study-verification-v1', 'plan_sha256': sha(root / 'plan.json'),
              'planned_points': len(plan['jobs']), 'points': rows}
    write_json(root / 'verified.json', result)
    return result
