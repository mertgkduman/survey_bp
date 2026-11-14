"""Qualified canonical min-sum BP plus OSD0/CS10 at Roffe Figure3 budgets."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runtime as execution

rt = execution.rt
ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.with_name('roffe-2005-07016-bp')
QUALIFICATION = rt.REPO / '.planning/spikes/056-efficient-osd/qualification.json'
OSD_SOURCE = rt.REPO / 'src/bp_registry/postprocessing/osd.py'
SEED = 2026111413


def design():
    original = rt.load(ORIGINAL)
    qualification = json.loads(QUALIFICATION.read_text())
    if (qualification['status'] != 'passed' or qualification['failures']
            or qualification['checked_complete_candidate_sets'] < 404
            or qualification['implementation_sha256'] != rt.sha(OSD_SOURCE)):
        raise ValueError('OSD source has no matching passed native/oracle qualification')
    jobs = []
    for source in original['jobs']:
        if source['arm'] != 'binary_ms':
            continue
        code = original['codes'][source['code']]
        for arm, method, order in [('bp_osd0', 'OSD_0', 0), ('bp_osd_cs10', 'OSD_CS', 10)]:
            processor = {'method': method, 'order': order, 'implementation': execution.VERSION,
                         'activation': 'original_syndrome_nonconvergence_only',
                         'reliability': 'signed_log_p0_over_p1_ascending', 'reliability_ties': 'original_column_id_ascending',
                         'score': 'uniform_original_channel_hamming_weight', 'score_ties': 'first_enumerated',
                         'evidence': 'complete_candidate_API; per-shot set digest and deterministic replay'}
            jobs.append({**source, 'id': f'{source["id"]}-{arm}', 'arm': arm, 'base_arm': 'binary_ms',
                         'decoder': {**source['decoder'], 'postprocessing': processor}, 'seed': SEED,
                         'n': code['n'], 'non_pivot_count': code['n']-code['rank_per_component'],
                         'source_target': None, 'workers': 1})
    return {**{k: v for k, v in original.items() if k not in ('schema', 'software', 'implementation_sha256')},
            'study_id': 'roffe-canonical-bp-osd', 'label': 'Roffe paper-budget canonical BP + OSD-0 / CS-10',
            'stage': 'osd_validation', 'jobs': jobs,
            'qualification_sha256': rt.sha(QUALIFICATION), 'original_plan_sha256': rt.sha(ORIGINAL / 'plan.json'),
            'instruction_path': str((ROOT / 'README.md').relative_to(rt.REPO)),
            'sampling': 'same deterministic physical stream as prior undamped confirmation; fixed methods, no tuning or pooling',
            'warmup': 'zero-syndrome algebraic warmup excluded from sampled work/time; JIT excluded',
            'ledger_chunk_size': execution.BATCH,
            'comparison_inputs': {
                'paper_cs60': str((ROOT.with_name('roffe-2005-07016-osd-comparison') / 'source_points.json').relative_to(rt.REPO)),
                'prior_confirmation': str((ROOT.with_name('roffe-2005-07016-damping') / 'confirmation/verified.json').relative_to(rt.REPO))},
            'claim_limit': 'Canonical adaptation: original toric codes/grids, X-only, undamped canonical min-sum alpha_t=1-2^-t and T=n; separately qualified source-derived OSD0/CS10 after nonconvergence. Signed LLR reliability; original-column tie order explicit. Source paper CS60 is context, not a claimed reproduced CS10 curve. BP iterations/edge work exclude elimination/search; separate OSD work and stage times are retained. Historical failed Phase7 admission is not relabeled.20 logical failures or1e8 shots; no superiority claim without uncertainty.'}


def extra():
    original = rt.load(ORIGINAL)
    return [ROOT / name for name in ('run.py', 'runtime.py', 'publish.py', 'report.py', 'README.md')] + [
        OSD_SOURCE, OSD_SOURCE.with_name('UPSTREAM-LICENSE.txt'), QUALIFICATION, ORIGINAL / 'plan.json',
        ROOT.with_name('roffe-2005-07016-damping') / 'confirmation/verified.json',
        ROOT.with_name('roffe-2005-07016-osd-comparison') / 'source_points.json',
        rt.REPO / '.planning/spikes/056-efficient-osd/reference.cpp',
        *[rt.REPO / path for path in original['implementation_sha256']]]


def submit(test_only=False):
    with rt.dispatch_lock(ROOT):
        plan = rt.load(ROOT); (ROOT / 'results').mkdir(exist_ok=True)
        path = ROOT / 'dispatch.json'; receipt = json.loads(path.read_text()) if path.exists() else {}
        base = ['sbatch', '--parsable', '--partition=common,scavenger', '--account=pfisterlab',
                '--nodes=1', '--ntasks=1', '--cpus-per-task=1', '--mem=2G', '--requeue', '--time=4-00:00:00',
                f'--chdir={rt.REPO}', f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
        command = shlex.join([sys.executable, str(Path(__file__).resolve())])

        def queue(name, arguments):
            if name in receipt and not test_only:
                return receipt[name]['id']
            argv = [*base, *(['--test-only'] if test_only else []), *arguments]
            response = subprocess.run(argv, check=True, capture_output=True, text=True)
            if test_only:
                print(response.stdout+response.stderr); return None
            jid = response.stdout.strip().split(';')[0]
            if not jid.isdigit():
                raise ValueError('invalid scheduler receipt')
            receipt[name] = {'id': jid, 'argv': argv}; rt.write_json(path, receipt)
            print(name, jid, flush=True); return jid

        array = queue('array', ['--job-name=roffe-osd', f'--array=0-{len(plan["jobs"])-1}%218',
                                f'--output={ROOT/"results/slurm-%A_%a.log"}',
                                f'--wrap=exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        if not test_only:
            queue('collect', ['--job-name=roffe-osd-audit', f'--dependency=afterok:{array}',
                              f'--output={ROOT/"results/collect-%j.log"}', f'--wrap={command} --collect --complete'])
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__); group = parser.add_mutually_exclusive_group(required=True)
    for name in ('freeze', 'submit', 'test-only', 'collect'):
        group.add_argument('--'+name, action='store_true')
    group.add_argument('--index', type=int); parser.add_argument('--complete', action='store_true'); args = parser.parse_args()
    if args.freeze:
        rt.freeze(ROOT, design(), extra())
    elif args.submit or args.test_only:
        submit(args.test_only)
    elif args.index is not None:
        print(json.dumps(execution.execute(ROOT, args.index)), flush=True)
    else:
        receipt = execution.collect(ROOT, require_complete=args.complete)
        from publish import publish
        from report import report
        publish(ROOT); report(ROOT)
        from bp_study_publish import refresh
        refresh(ROOT)
        print(f'{len(receipt["points"])}/{receipt["planned_points"]} audited BP/OSD points', flush=True)


if __name__ == '__main__':
    main()
