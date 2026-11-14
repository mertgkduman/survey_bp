"""Prospective joint-control search, independent confirmation and typed ledgers."""
from collections import Counter
from dataclasses import replace
import fcntl
from hashlib import sha256
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import bp_study_runtime as rt


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


engine = module('_runtime_budget_engine', ROOT / 'engine.py')
osd = module('_runtime_budget_reference', ROOT.with_name('roffe-2005-07016-osd-fast') / 'runtime.py')
OSD_ROOT = ROOT.with_name('roffe-2005-07016-osd-fast')
ORIGINAL = ROOT.with_name('roffe-2005-07016-bp')
TUNING_SEED, VALIDATION_SEED, CONFIRMATION_SEED = 2026111421, 2026111422, 2026111423
TIMING_FIELDS = {'decode_ns', 'reference_ns', 'timing_reference_sha256'}
BATCH = 4096


def identity(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def coarse_grid():
    return [{'damping': d, 'alpha_mode': mode, 'alpha': alpha, 'beta': beta}
            for d, (mode, alpha), beta in itertools.product(
                (0., .3, .5, .7, .85), [('paper', 1.), ('constant', .5), ('constant', .75), ('constant', 1.)], (0., .25, .5, 1.))]


def baseline(job):
    return {'damping': .3 if job['decoder']['family'] == 'bp4' else .5,
            'alpha_mode': 'paper', 'alpha': 1., 'beta': 0.}


def neighbors(controls):
    ds = {round(min(.95, max(0., controls['damping']+v)), 6) for v in (-.1, 0., .1)}
    alphas = {round(min(1., max(.1, controls['alpha']+v)), 6) for v in (-.1, 0., .1)}
    betas = {round(min(1.5, max(0., controls['beta']+v)), 6) for v in (-.125, 0., .125)}
    return [{'damping': d, 'alpha_mode': controls['alpha_mode'], 'alpha': a, 'beta': b}
            for d, a, b in itertools.product(sorted(ds), sorted(alphas), sorted(betas))]


def configured(job, controls, cap, seed, shots, target, stage):
    c = controls
    return {**job, 'id': f'{job["id"]}-{stage}-{identity(c)[:16]}-t{cap}',
            'seed': seed, 'max_shots': shots, 'target_block_failures': target,
            'controls': c, 'stage': stage, 'workers': 1,
            'decoder': {**job['decoder'], 'max_iterations': cap, 'iterations_per_branch': cap,
                        'v2c_damping': c['damping'], 'alpha': c['alpha'], 'beta': c['beta'],
                        'alpha_schedule': '1-2**(-iteration)' if c['alpha_mode'] == 'paper' else 'constant',
                        'execution_backend': engine.VERSION}}


def sample(base, seed, shot):
    job, n, packed, _ = base; joint = job['decoder']['family'] == 'bp4'
    truth = rt.parent.base._sample(seed, round(job['physical_p']*100000), shot, n, depolarizing=joint)
    bits = rt.parent.base.PAULI_BITS[truth] if joint else truth
    syndrome = (np.concatenate((rt.parent.base._syndrome(packed[0], bits[:, 1]),
                                rt.parent.base._syndrome(packed[1], bits[:, 0]))) if joint else
                rt.parent.base._syndrome(packed[1], truth))
    return truth, syndrome


def event(prepared, job, shot, reference):
    base = (job, prepared.n, prepared.packed, [prepared.graph])
    truth, syndrome = sample(base, job['seed'], shot)
    start = time.perf_counter_ns()
    candidate, posterior, converged, iterations = prepared.decode(syndrome, job['decoder']['max_iterations'])
    ns = time.perf_counter_ns()-start
    outcome, _ = rt.parent.outcome(*prepared.packed, truth, candidate, joint=prepared.joint)
    if converged != (outcome != 'type_i'):
        raise ValueError('canonical stopping disagrees with original independent evaluation')
    return {'shot': shot, 'outcome': outcome, 'iterations': int(iterations), 'branch_iterations': [int(iterations)],
            'directed_edge_updates': 2*job['graph_edges']*int(iterations), 'decode_ns': ns,
            'reference_ns': reference['mean_ns'], 'timing_reference_sha256': reference['sha256'],
            'converged': bool(converged), 'error_sha256': sha256(truth.tobytes()).hexdigest(),
            'syndrome_sha256': sha256(syndrome.tobytes()).hexdigest(), 'candidate_sha256': sha256(candidate.tobytes()).hexdigest(),
            'terminal_posterior_sha256': sha256(np.ascontiguousarray(posterior, dtype='<f8').tobytes()).hexdigest()}


class Ledger(rt.Ledger):
    def __init__(self, directory, job):
        self.reference_ns = 0.
        self.references = Counter()
        super().__init__(directory, job)

    def add(self, row, line):
        if (type(row.get('converged')) is not bool or row['converged'] != (row['outcome'] != 'type_i')
                or not isinstance(row.get('reference_ns'), (float, int)) or not math.isfinite(row['reference_ns']) or row['reference_ns'] <= 0):
            raise ValueError('invalid runtime/control event')
        for field in ('error_sha256', 'syndrome_sha256', 'candidate_sha256', 'terminal_posterior_sha256', 'timing_reference_sha256'):
            value = row.get(field)
            if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('invalid event provenance hash')
        super().add(row, line)
        self.reference_ns += row['reference_ns']; self.references[row['timing_reference_sha256']] += 1

    def commit(self, rows):
        space = os.statvfs(ROOT)
        if space.f_bavail*space.f_frsize < 50*1024**3:
            raise RuntimeError('less than50GiB free; retain checkpoint for exact resume')
        return super().commit(rows)

    def summary(self):
        return {**super().summary(), 'reference_ns': self.reference_ns,
                'reference_receipts': dict(self.references), 'runtime_ratio': self.decode_ns/self.reference_ns}


def reference(point, job, protocol, seed=TUNING_SEED):
    import gzip
    plan = rt.load(OSD_ROOT)
    source = next(j for j in plan['jobs'] if j['code'] == job['code'] and j['matched_x_rate'] == job['matched_x_rate'] and j['arm'] == 'bp_osd0')
    source = {**source, 'seed': seed}
    state = osd.state(source); osd.warm(state)
    repeats, shots = protocol['reference_repeats'], protocol['reference_shots']
    trials, rows = [], []
    for repeat in range(repeats):
        events = [osd.event(state, shot) for shot in range(shots)]
        trials.append(sum(e['decode_ns'] for e in events)/shots)
        rows += [{**e, 'repeat': repeat, 'purpose': 'repeated timing of fixed calibration shots; not independent LER evidence'} for e in events]
    receipt = {'kind': 'same_cpu_warm_bp_osd0_reference_v1', 'mean_ns': statistics.median(trials),
               'block_mean_ns': trials, 'shots_per_repeat': shots, 'repeats': repeats,
               'seed': seed, 'host': platform.node(), 'affinity': sorted(os.sched_getaffinity(0)),
               'reference_plan_sha256': rt.sha(OSD_ROOT / 'plan.json'), 'job': source,
               'timing_scope': 'warmed canonical BP plus complete qualified OSD0 API after nonconvergence; no sampling/evaluation/JIT/I/O'}
    value = identity(receipt); directory = point / 'references'; directory.mkdir(exist_ok=True)
    path = directory / (value+'.json'); rt.write_json(path, receipt)
    with gzip.open(directory / (value+'.jsonl.gz'), 'wt', compresslevel=3) as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True)+'\n')
    return {**receipt, 'sha256': rt.sha(path)}


def evaluate(point, base, controls, cap, stage, reference_value, protocol):
    training = stage in ('tuning', 'validation')
    shots = protocol['tuning_shots'] if stage == 'tuning' else protocol['finalist_shots'] if stage == 'validation' else protocol['max_shots']
    target = shots+1 if training else protocol['target_failures']
    seed = TUNING_SEED if stage == 'tuning' else VALIDATION_SEED if stage == 'validation' else CONFIRMATION_SEED
    job = configured(base[0], controls, cap, seed, shots, target, stage)
    directory = point / stage / job['id']; directory.mkdir(parents=True, exist_ok=True)
    manifest = {'schema': 'runtime-budget-arm-v1', 'campaign_plan_sha256': rt.sha(point.parents[1] / 'plan.json'), 'job': job,
                'point_plan_sha256': None if training else rt.sha(point / 'point-plan.json')}
    path = directory / 'manifest.json'
    if path.exists() and json.loads(path.read_text()) != manifest:
        raise ValueError('frozen per-cap child manifest changed')
    if not path.exists(): rt.write_json(path, manifest)
    ledger = Ledger(directory, job)
    prepared = engine.Prepared(base, controls)
    prepared.decode(np.zeros(len(prepared.graph.row_ptr)-1, dtype=np.uint8), cap)
    if not ledger.complete:
        while not ledger.complete:
            rows, failures = [], ledger.failures
            for shot in range(ledger.shots, min(ledger.shots+BATCH, shots)):
                row = event(prepared, job, shot, reference_value); rows.append(row)
                failures += row['outcome'] in rt.parent.base.FAILURES
                if failures == target: break
            ledger.commit(rows)
            if not training: print(job['id'], ledger.shots, ledger.failures, flush=True)
    summary = {**ledger.summary(), 'manifest_sha256': rt.sha(path)}
    path = directory / 'summary.json'
    if path.exists() and json.loads(path.read_text()) != summary:
        raise ValueError('terminal child summary differs from retained ledger')
    rt.write_json(path, summary)
    for stored in (ledger.first, ledger.last):
        replay = event(prepared, job, stored['shot'], reference_value)
        if {k: v for k, v in replay.items() if k not in TIMING_FIELDS} != {k: v for k, v in stored.items() if k not in TIMING_FIELDS}:
            raise ValueError('runtime-budget endpoint replay mismatch')
    return {**summary, 'job': job, 'summary_sha256': rt.sha(path), 'directory': str(directory.relative_to(rt.REPO))}


def search_caps(n, evaluate_cap, protocol):
    """Retain the whole bracket; a noisy tolerance never hides over-budget runs."""
    seen = {}
    def measure(cap):
        cap = int(cap)
        if cap not in seen: seen[cap] = evaluate_cap(cap)
        return seen[cap]
    value = measure(n); tolerance = protocol['runtime_tolerance']
    if value['runtime_ratio'] > 1+tolerance:
        for cap in sorted({1, max(1, n//8), max(1, n//4), max(1, n//2)}): measure(cap)
    else:
        cap = n
        while value['runtime_ratio'] < 1-tolerance and cap < protocol['max_cap_factor']*n:
            if value.get('nonconverged', 1) == 0: break
            cap *= 2; value = measure(cap)
            if value['runtime_ratio'] > 1+tolerance: break
    # Refine the integer iteration cap using only calibration samples/times.
    for _ in range(protocol['cap_refinements']):
        below = [cap for cap, r in seen.items() if r['runtime_ratio'] <= 1]
        above = [cap for cap, r in seen.items() if r['runtime_ratio'] > 1]
        if not below or not above: break
        low, high = max(below), min(c for c in above if c > min(below)) if any(c > min(below) for c in above) else min(above)
        if high-low <= 1: break
        candidate = (low+high)//2
        if candidate in seen: break
        measure(candidate)
    eligible = [r for r in seen.values() if r['runtime_ratio'] <= 1+tolerance]
    matched = min(eligible, key=lambda r: (abs(r['runtime_ratio']-1), r['job']['decoder']['max_iterations'])) if eligible else min(seen.values(), key=lambda r: r['runtime_ratio'])
    return matched, list(seen.values())


def choose(candidates, tolerance):
    eligible = [c for c in candidates if c['runtime_ratio'] <= 1+tolerance]
    if not eligible:
        return min(candidates, key=lambda c: (c['runtime_ratio'], c['failures']/c['shots'], c['iterations']/c['shots']))
    return min(eligible, key=lambda c: (c['failures']/c['shots'], c['iterations']/c['shots'],
                                      c['runtime_ratio'], identity(c['job']['controls'])))


def confirmation_specs(job, baseline_match, winner, histories):
    n = job['n']; entries = {}
    for role, match in [('previous_damping', baseline_match), ('joint_selected', winner)]:
        controls = match['job']['controls']; target = match['job']['decoder']['max_iterations']
        caps = {n, target}
        if target < n:
            caps |= {max(1, n//8), max(1, n//4), max(1, n//2)}
        else:
            cap = n
            while cap <= target:
                caps.add(cap); cap *= 2
            # Retain the first over-budget ladder point as context, never call it matched.
            caps.add(cap)
        for cap in sorted(caps):
            key = (identity(controls), cap)
            if key not in entries: entries[key] = {'controls': controls, 'cap': cap, 'roles': []}
            entries[key]['roles'].append(role)
    return list(entries.values())


def execute(root, index):
    plan = rt.load(root); job = plan['jobs'][index]; protocol = plan['protocol']
    point = root / 'results' / job['id']; point.mkdir(parents=True, exist_ok=True)
    with (point / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        base = rt.state(job); ref = reference(point, job, protocol)
        selection_path = point / 'point-plan.json'
        if selection_path.exists():
            selection = json.loads(selection_path.read_text())
            if selection['campaign_plan_sha256'] != rt.sha(root / 'plan.json'): raise ValueError('point plan belongs to another campaign')
        else:
            matches, histories = [], []
            tested = set()
            def tune(controls):
                key = identity(controls)
                if key in tested: return
                tested.add(key)
                def measure(cap):
                    r = evaluate(point, base, controls, cap, 'tuning', ref, protocol)
                    r['nonconverged'] = r['counts']['type_i']
                    return r
                match, history = search_caps(job['n'], measure, protocol)
                matches.append(match); histories.extend(history)
                rt.write_json(point / 'progress.json', {'stage': 'tuning', 'tested_controls': len(matches),
                    'tested_control_caps': len(histories), 'last_controls': controls,
                    'last_cap': match['job']['decoder']['max_iterations'], 'last_runtime_ratio': match['runtime_ratio'],
                    'last_training_ler': match['rate'], 'reference_sha256': ref['sha256']})
                print('tuned', job['id'], len(matches), controls, match['job']['decoder']['max_iterations'], match['runtime_ratio'], match['failures'], flush=True)
            tune(baseline(job))
            for controls in protocol['coarse_controls']: tune(controls)
            ordered = sorted(matches, key=lambda c: (c['runtime_ratio'] > 1+protocol['runtime_tolerance'], c['rate'], c['iterations']/c['shots']))
            for candidate in ordered[:protocol['refine_candidates']]:
                for controls in neighbors(candidate['job']['controls']): tune(controls)
            finalists = sorted(matches, key=lambda c: (c['runtime_ratio'] > 1+protocol['runtime_tolerance'], c['rate'], c['iterations']/c['shots']))[:protocol['finalist_candidates']]
            controls_to_check = {identity(c['job']['controls']): c['job']['controls'] for c in finalists}
            controls_to_check[identity(baseline(job))] = baseline(job)
            finalist_matches = []
            ref = reference(point, job, protocol, seed=VALIDATION_SEED)
            for controls in controls_to_check.values():
                def measure(cap):
                    value = evaluate(point, base, controls, cap, 'validation', ref, protocol)
                    value['nonconverged'] = value['counts']['type_i']
                    return value
                match, history = search_caps(job['n'], measure, protocol)
                finalist_matches.append(match); histories.extend(history)
            winner = choose(finalist_matches, protocol['runtime_tolerance'])
            base_match = next(r for r in finalist_matches if r['job']['controls'] == baseline(job))
            specs = confirmation_specs(job, base_match, winner, histories)
            selection = {'schema': 'runtime-budget-point-plan-v1', 'campaign_plan_sha256': rt.sha(root / 'plan.json'),
                         'point': job, 'reference': ref, 'candidates': matches, 'finalists': finalist_matches, 'history': histories,
                         'winner': winner, 'baseline_match': base_match, 'confirmations': specs,
                         'selection': 'minimum empirical training LER within runtime tolerance; exact ties prefer fewer mean sweeps; fresh confirmation required'}
            rt.write_json(selection_path, selection)
        rows = []
        for spec in selection['confirmations']:
            row = evaluate(point, base, spec['controls'], spec['cap'], 'confirmation', ref, protocol)
            rows.append({**row, 'roles': spec['roles'], 'point_plan_sha256': rt.sha(selection_path)})
        receipt = {'schema': 'runtime-budget-point-verification-v1', 'campaign_plan_sha256': rt.sha(root / 'plan.json'),
                   'point_plan_sha256': rt.sha(selection_path), 'points': rows,
                   'audit_scope': 'complete retained ledgers validated during generation/resume; exact endpoint replay; collector independently re-reads all ledgers'}
        rt.write_json(point / 'verified.json', receipt)
        return receipt
