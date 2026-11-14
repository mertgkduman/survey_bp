"""Tune Roffe min-sum damping, then confirm on independent samples at T=n."""
import argparse
from collections import defaultdict
import gzip
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bp_study_runtime as rt

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.with_name('roffe-2005-07016-bp')
SELECTOR = ROOT.with_name('mackay-0304161-damping-t100') / 'run.py'
spec = importlib.util.spec_from_file_location('_roffe_damping_selector', SELECTOR)
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)
choose_damping = selector.choose_damping
DAMPING = (0., .1, .3, .5, .7, .85, .95)
TUNING_SHOTS = 1024
TUNING_SEED = 2026111411
CONFIRMATION_SEED = 2026111413
CONCURRENCY = 392


def design():
    original = rt.load(ORIGINAL)
    jobs = []
    for job in original['jobs']:
        for damping in DAMPING:
            family = job['arm']
            arm = f'{family}_d{round(100*damping):03d}'
            jobs.append({**job, 'id': f'{job["id"]}-d{round(100*damping):03d}',
                         'arm': arm, 'base_arm': family, 'seed': TUNING_SEED,
                         'decoder': {**job['decoder'], 'v2c_damping': damping},
                         'source_target': None, 'workers': 1,
                         'max_shots': TUNING_SHOTS, 'target_block_failures': TUNING_SHOTS+1})
    return {**{k: v for k, v in original.items() if k not in ('schema', 'software', 'implementation_sha256')},
            'study_id': 'roffe-damping-tuning', 'label': 'Roffe Figure 3 min-sum damping tuning',
            'stage': 'tuning', 'jobs': jobs, 'damping_grid': list(DAMPING),
            'original_plan_sha256': rt.sha(ORIGINAL / 'plan.json'),
            'instruction_path': str((ROOT / 'README.md').relative_to(rt.REPO)),
            'tuning_shots_per_rate': TUNING_SHOTS,
            'selection': {
                'primary': 'mean block LER over each code\'s equally weighted Figure 3 rates; one damping per code/family',
                'similarity_margin': '10% of empirical-best mean LER; no positive absolute floor',
                'tie_guard': 'simultaneous one-sided paired risk-regret upper bounds from exact per-rate discordance tails; alpha=.05 over all code/family/candidate/reference/rate/tail comparisons',
                'secondary': 'minimum mean actual executed iterations among guard-qualified candidates',
                'fallback': 'empirical lowest LER; selection provisional until independent confirmation',
                'confirmation_seed': CONFIRMATION_SEED,
                'confirmation_stop': '20 block failures or 100000000 shots',
                'baseline_damping': {'binary_ms': 0., 'qbp_ms': 0.}},
            'claim_limit': 'Controlled damping adaptation of Roffe Figure 3; source code artifacts, rate grids, flooding min-sum alpha_t=1-2^-t and T=n preserved. Damping is a new policy. Training is never pooled with fresh confirmation. Ordinary BP is X-only; Q-BP is joint-Pauli depolarizing at p_dep=1.5*p_X, a different channel and not an isolated Q-BP effect. No OSD, source-faithful numerical or superiority claim.'}


def extra():
    original = rt.load(ORIGINAL)
    return [Path(__file__).resolve(), ROOT / 'README.md', SELECTOR,
            rt.REPO / 'data/reproductions/bp_study_publish.py', ORIGINAL / 'plan.json',
            *[rt.REPO / path for path in original['implementation_sha256']]]


def read_events(root, row):
    events = []
    for path in sorted((root / 'results' / row['id']).glob('shots-*.jsonl.gz')):
        with gzip.open(path, 'rt') as stream:
            events.extend(json.loads(line) for line in stream)
    if len(events) != TUNING_SHOTS or [e['shot'] for e in events] != list(range(TUNING_SHOTS)):
        raise ValueError('incomplete or unordered fixed tuning cohort')
    return events


def select_rows(plan, rows, root):
    expected = defaultdict(set)
    groups = defaultdict(list)
    for job in plan['jobs']:
        expected[job['code'], job['base_arm']].add(job['matched_x_rate'])
    for row in rows:
        groups[row['code'], row['base_arm']].append(row)
    if set(groups) != set(expected):
        raise ValueError('missing tuning code/family groups')
    # Cover both discordance tails, all ordered candidate/reference pairs and
    # every rate in every code/family, including the unequal 25/28-point grids.
    tail = .05 / (2*len(DAMPING)*(len(DAMPING)-1)*sum(map(len, expected.values())))
    selected = []
    for (code, family), points in sorted(groups.items()):
        candidates = defaultdict(list)
        for row in points:
            candidates[row['decoder']['v2c_damping']].append(row)
        if set(candidates) != set(DAMPING):
            raise ValueError('missing damping candidates')
        values, identities, means = {}, {}, {}
        for damping, candidate in candidates.items():
            ordered = sorted(candidate, key=lambda row: row['matched_x_rate'])
            if [r['matched_x_rate'] for r in ordered] != sorted(expected[code, family]):
                raise ValueError('damping candidates differ from the exact source rate grid')
            events = [read_events(root, row) for row in ordered]
            values[damping] = np.array([[e['outcome'] in rt.parent.base.FAILURES for e in batch]
                                        for batch in events], dtype=np.int8)
            identities[damping] = [[e['error_sha256'] for e in batch] for batch in events]
            means[damping] = sum(r['iterations'] for r in ordered)/(TUNING_SHOTS*len(ordered))
        reference = identities[DAMPING[0]]
        if any(hashes != reference for hashes in identities.values()):
            raise ValueError('damping candidates do not share identical physical samples')
        selected.append({'code': code, 'base_arm': family, 'rates': sorted(expected[code, family]),
                         **choose_damping(values, means, tail)})
    return selected, tail


def select():
    plan = rt.load(ROOT)
    receipt = rt.collect(ROOT, require_complete=True)
    selected, tail = select_rows(plan, receipt['points'], ROOT)
    result = {'schema': 'bp-damping-selection-v1', 'plan_sha256': rt.sha(ROOT / 'plan.json'),
              'tuning_receipt_sha256': rt.sha(ROOT / 'verified.json'),
              'discordance_tail_probability': tail, 'selected': selected,
              'status': 'provisional selection; confirmation required; no equivalence inferred from overlapping intervals'}
    path = ROOT / 'selection.json'
    if path.exists() and json.loads(path.read_text()) != result:
        raise ValueError('refusing to change frozen damping selection')
    if not path.exists():
        rt.write_json(path, result)
    return result


def confirmation_design(plan, selection, selection_sha):
    groups = {(j['code'], j['base_arm']) for j in plan['jobs']}
    entries = selection['selected']
    if {(e['code'], e['base_arm']) for e in entries} != groups or len(entries) != len(groups):
        raise ValueError('confirmation selection does not cover every code/family once')
    jobs = []
    for entry in entries:
        code, family, damping = entry['code'], entry['base_arm'], entry['damping']
        if damping not in DAMPING:
            raise ValueError('unmeasured selected damping')
        choices = [('selected', damping)]
        if damping != 0.:
            choices.append(('baseline', 0.))
        for role, value in choices:
            for job in plan['jobs']:
                if job['code'] == code and job['base_arm'] == family and job['decoder']['v2c_damping'] == value:
                    jobs.append({**job, 'id': f'{role}-{job["id"]}', 'arm': f'{family}_{role}',
                                 'role': role, 'seed': CONFIRMATION_SEED, 'workers': 1,
                                 'max_shots': 100_000_000, 'target_block_failures': 20,
                                 'selection_sha256': selection_sha})
    return {**{k: v for k, v in plan.items() if k not in ('implementation_sha256', 'software', 'schema')},
            'study_id': 'roffe-damping-confirmation', 'stage': 'confirmation', 'jobs': jobs,
            'label': 'Roffe Figure 3: independently confirmed tuned min-sum damping'}


def confirmation(selection):
    plan = rt.load(ROOT)
    if selection['plan_sha256'] != rt.sha(ROOT / 'plan.json'):
        raise ValueError('selection belongs to a different tuning plan')
    return rt.freeze(ROOT / 'confirmation', confirmation_design(plan, selection, rt.sha(ROOT / 'selection.json')),
                     [*extra(), ROOT / 'selection.json', ROOT / 'plan.json'])


def submit(stage='tuning', test_only=False):
    root = ROOT if stage == 'tuning' else ROOT / 'confirmation'
    with rt.dispatch_lock(root):
        return _submit(stage, test_only)


def _submit(stage='tuning', test_only=False):
    root = ROOT if stage == 'tuning' else ROOT / 'confirmation'
    plan = rt.load(root)
    (root / 'results').mkdir(exist_ok=True)
    path = root / 'dispatch.json'
    receipt = json.loads(path.read_text()) if path.exists() else {}
    base = ['sbatch', '--parsable', '--partition=common,scavenger', '--account=pfisterlab',
            '--nodes=1', '--ntasks=1', '--cpus-per-task=1', '--mem=2G', '--requeue',
            '--time=4-00:00:00', f'--chdir={rt.REPO}',
            f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
    command = shlex.join([sys.executable, str(Path(__file__).resolve()), '--stage', stage])

    def queue(name, options):
        if name in receipt and not test_only:
            return receipt[name]['id']
        argv = [*base, *(['--test-only'] if test_only else []), *options]
        result = subprocess.run(argv, check=True, capture_output=True, text=True)
        if test_only:
            print(result.stderr + result.stdout)
            return None
        jid = result.stdout.strip().split(';')[0]
        if not jid.isdigit():
            raise ValueError('invalid scheduler receipt')
        receipt[name] = {'id': jid, 'argv': argv}
        rt.write_json(path, receipt)
        print(stage, name, jid, flush=True)
        return jid

    array = queue('array', ['--job-name=roffe-damp-' + stage,
                           f'--array=0-{len(plan["jobs"])-1}%{CONCURRENCY}',
                           f'--output={root/"results/slurm-%A_%a.log"}',
                           f'--wrap=exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
    if not test_only:
        queue('advance', ['--job-name=roffe-damp-advance', f'--dependency=afterok:{array}',
                          f'--output={root/"results/advance-%j.log"}', f'--wrap={command} --advance'])
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['tuning', 'confirmation'], default='tuning')
    group = parser.add_mutually_exclusive_group(required=True)
    for name in ('freeze', 'submit', 'test-only', 'collect', 'advance'):
        group.add_argument('--' + name, action='store_true')
    group.add_argument('--index', type=int)
    args = parser.parse_args()
    root = ROOT if args.stage == 'tuning' else ROOT / 'confirmation'
    if args.freeze:
        if args.stage != 'tuning':
            parser.error('confirmation freezes automatically from the audited selection')
        rt.freeze(ROOT, design(), extra())
    elif args.submit or args.test_only:
        submit(args.stage, args.test_only)
    elif args.index is not None:
        print(json.dumps(rt.execute(root, args.index)), flush=True)
    elif args.collect:
        print(len(rt.collect(root)['points']))
    elif args.stage == 'tuning':
        confirmation(select())
        submit('confirmation')
    else:
        rt.collect(root, require_complete=True)
        from bp_study_publish import publish, refresh
        publish(root)
        refresh(root)


if __name__ == '__main__':
    main()
