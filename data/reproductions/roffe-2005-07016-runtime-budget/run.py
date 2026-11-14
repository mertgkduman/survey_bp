"""Joint damping/scale/offset tuning and iteration curves at BP+OSD0 runtime."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('_roffe_runtime_budget', ROOT / 'runtime.py')
execution = importlib.util.module_from_spec(spec); spec.loader.exec_module(execution)
rt = execution.rt
QUALIFICATION = rt.REPO / '.planning/quick/261114-lhw-run-runtime-matched-iteration-sweeps-wit/qualification.json'


def design():
    original, reference = rt.load(execution.ORIGINAL), rt.load(execution.OSD_ROOT)
    qualification = json.loads(QUALIFICATION.read_text())
    if (qualification.get('status') != 'passed' or qualification['engine_sha256'] != rt.sha(ROOT / 'engine.py')
            or qualification['exact_terminal_comparisons'] < 128):
        raise ValueError('no matching qualified joint-control traversal')
    jobs = [{**j, 'id': j['id']+'-runtime-budget', 'n': original['codes'][j['code']]['n'],
             'workers': 1, 'source_target': None} for j in original['jobs']]
    return {**{k: v for k, v in original.items() if k not in ('schema', 'software', 'implementation_sha256')},
            'study_id': 'roffe-joint-controls-runtime-budget', 'label': 'Roffe: joint BP controls versus iteration cap and BP+OSD0 runtime',
            'jobs': jobs, 'instruction_path': str((ROOT / 'README.md').relative_to(rt.REPO)),
            'reference_plan_sha256': rt.sha(execution.OSD_ROOT / 'plan.json'),
            'qualification_sha256': rt.sha(QUALIFICATION),
            'protocol': {'reference_shots': 1024, 'reference_repeats': 5, 'tuning_shots': 256,
                         'finalist_shots': 4096, 'finalist_candidates': 5,
                         'runtime_tolerance': .10, 'max_cap_factor': 256, 'cap_refinements': 4,
                         'refine_candidates': 2, 'coarse_controls': execution.coarse_grid(),
                         'target_failures': 20, 'max_shots': 100000000,
                         'tuning_seed': execution.TUNING_SEED, 'finalist_seed': execution.VALIDATION_SEED,
                         'confirmation_seed': execution.CONFIRMATION_SEED},
            'claim_limit': 'Prospective controlled adaptation. Same-host warmed decoder mean time versus undamped canonical BP+OSD0, not campaign elapsed time. Joint damping/constant-or-paper scaling/offset search; alpha*max(0,min_abs-beta), old-V2C damping. Every tested control/cap retained. Training never pooled with fresh confirmation. Preserve full cap progression for previous damping and selected joint settings. Runtime tolerance10%, explicit saturation/search ceilings and over-budget starting points. Binary BP X-only; Q-BP joint depolarizing at1.5p_X, distinct channels. Timings are host/cohort dependent; report actual ratios, not assumed equality. No source-reproduction or global-optimality claim.'}


def extra():
    original, reference = rt.load(execution.ORIGINAL), rt.load(execution.OSD_ROOT)
    return [ROOT / name for name in ('engine.py', 'runtime.py', 'run.py', 'report.py', 'README.md')] + [
        QUALIFICATION, execution.ORIGINAL / 'plan.json', execution.OSD_ROOT / 'plan.json',
        *[rt.REPO / p for p in original['implementation_sha256']],
        *[rt.REPO / p for p in reference['implementation_sha256']]]


def collect(root=ROOT, complete=False):
    plan = rt.load(root); points = []; tuning = []; finished = []
    for job in plan['jobs']:
        point = root / 'results' / job['id']; selection_path = point / 'point-plan.json'
        if not selection_path.exists(): continue
        selection = json.loads(selection_path.read_text())
        if selection['campaign_plan_sha256'] != rt.sha(root / 'plan.json'):
            raise ValueError('selection/plan mismatch')
        if execution.choose(selection['finalists'], plan['protocol']['runtime_tolerance']) != selection['winner']:
            raise ValueError('selected controls do not follow the frozen LER/work objective')
        for row in selection['history']:
            directory = rt.REPO / row['directory']
            if rt.sha(directory / 'summary.json') != row['summary_sha256']:
                raise ValueError('calibration summary changed after selection')
        tuning += [{**r, 'point': job['id']} for r in selection['history']]
        checked = 0
        for spec in selection['confirmations']:
            child = execution.configured(job, spec['controls'], spec['cap'], execution.CONFIRMATION_SEED,
                                         plan['protocol']['max_shots'], plan['protocol']['target_failures'], 'confirmation')
            directory = point / 'confirmation' / child['id']
            if not (directory / 'summary.json').exists(): continue
            stored = json.loads((directory / 'summary.json').read_text())
            row = {**stored, 'job': child, 'summary_sha256': rt.sha(directory / 'summary.json'),
                   'directory': str(directory.relative_to(rt.REPO)), 'roles': spec['roles'],
                   'point_plan_sha256': rt.sha(selection_path)}
            ledger = execution.Ledger(directory, child)
            summary = {**ledger.summary(), 'manifest_sha256': rt.sha(directory / 'manifest.json')}
            if summary != json.loads((directory / 'summary.json').read_text()) or row['summary_sha256'] != rt.sha(directory / 'summary.json'):
                raise ValueError('independent complete-ledger audit mismatch')
            manifest = json.loads((directory / 'manifest.json').read_text())
            if manifest != {'schema': 'runtime-budget-arm-v1', 'campaign_plan_sha256': rt.sha(root / 'plan.json'), 'job': child,
                            'point_plan_sha256': rt.sha(selection_path)}:
                raise ValueError('child manifest mismatch')
            references = {rt.sha(p): p for p in (point / 'references').glob('*.json')}
            if not set(ledger.references).issubset(references): raise ValueError('missing referenced timing receipt')
            prepared = execution.engine.Prepared(rt.state(job), child['controls'])
            for stored in (ledger.first, ledger.last):
                path = point / 'references' / (stored['timing_reference_sha256']+'.json')
                # Reference filenames use a receipt-content ID. Resolve stored file SHA explicitly.
                if not path.exists():
                    path = next((p for p in (point / 'references').glob('*.json') if rt.sha(p) == stored['timing_reference_sha256']), None)
                if path is None or not path.exists(): raise ValueError('missing timing reference')
                ref = {**json.loads(path.read_text()), 'sha256': rt.sha(path)}
                replay = execution.event(prepared, child, stored['shot'], ref)
                if {k: v for k, v in replay.items() if k not in execution.TIMING_FIELDS} != {k: v for k, v in stored.items() if k not in execution.TIMING_FIELDS}:
                    raise ValueError('confirmation endpoint replay mismatch')
            points.append({**row, 'point': job['id']})
            checked += 1
        if checked == len(selection['confirmations']): finished.append(job['id'])
    if complete and len(finished) != len(plan['jobs']): raise ValueError('not all point workers have completed')
    result = {'schema': 'runtime-budget-study-verification-v1', 'plan_sha256': rt.sha(root / 'plan.json'),
              'planned_strata': len(plan['jobs']), 'finished_strata': finished, 'points': points, 'tuning': tuning}
    rt.write_json(root / 'verified.json', result)
    return result


def submit(test_only=False):
    with rt.dispatch_lock(ROOT):
        plan = rt.load(ROOT); (ROOT / 'results').mkdir(exist_ok=True)
        path = ROOT / 'dispatch.json'; receipt = json.loads(path.read_text()) if path.exists() else {}
        command = shlex.join([sys.executable, str(Path(__file__).resolve())])
        base = ['sbatch', '--parsable', '--partition=common,scavenger', '--account=pfisterlab', '--nodes=1', '--ntasks=1',
                '--cpus-per-task=1', '--mem=2G', '--requeue', '--time=4-00:00:00', f'--chdir={rt.REPO}',
                f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
        def queue(name, options):
            if name in receipt and not test_only: return receipt[name]['id']
            argv = [*base, *(['--test-only'] if test_only else []), *options]
            result = subprocess.run(argv, check=True, capture_output=True, text=True)
            if test_only: print(result.stdout+result.stderr); return None
            jid = result.stdout.strip().split(';')[0]
            if not jid.isdigit(): raise ValueError('invalid scheduler receipt')
            receipt[name] = {'id': jid, 'argv': argv}; rt.write_json(path, receipt); print(name, jid, flush=True); return jid
        setup = 'export NUMBA_CACHE_DIR="/tmp/roffe-budget-${SLURM_JOB_ID}"; mkdir -p "$NUMBA_CACHE_DIR"; '
        array = queue('array', ['--job-name=roffe-runtime-controls', f'--array=0-{len(plan["jobs"])-1}%218',
                                f'--output={ROOT/"results/slurm-%A_%a.log"}',
                                '--wrap='+setup+f'exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        if not test_only:
            queue('collect', ['--job-name=roffe-runtime-audit', f'--dependency=afterok:{array}',
                              f'--output={ROOT/"results/collect-%j.log"}', '--wrap='+setup+f'{command} --collect --complete'])
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__); group = parser.add_mutually_exclusive_group(required=True)
    for name in ('freeze', 'submit', 'test-only', 'collect'): group.add_argument('--'+name, action='store_true')
    group.add_argument('--index', type=int); parser.add_argument('--complete', action='store_true'); args = parser.parse_args()
    if args.freeze: rt.freeze(ROOT, design(), extra())
    elif args.submit or args.test_only: submit(args.test_only)
    elif args.index is not None: execution.execute(ROOT, args.index)
    else:
        result = collect(complete=args.complete)
        from report import report
        report(ROOT)
        from bp_study_publish import refresh
        refresh(ROOT)
        print(len(result['finished_strata']), '/', result['planned_strata'], 'strata independently audited', flush=True)


if __name__ == '__main__': main()
