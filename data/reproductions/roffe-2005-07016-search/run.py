"""Tune and confirm beam/RelayBP on the original Roffe X-only paper grid."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_roffe_search_runtime',ROOT/'runtime.py')
execution=importlib.util.module_from_spec(spec);sys.modules[spec.name]=execution;spec.loader.exec_module(execution)
rt=execution.rt
QUALIFICATION=rt.REPO/'.planning/quick/261115-sxj-tune-canonical-beam-search-and-relaybp-a/qualification.json'


def design():
    original=rt.load(execution.ORIGINAL);reference=rt.load(execution.OSD_ROOT)
    qualification=json.loads(QUALIFICATION.read_text())
    if qualification.get('status')!='passed' or qualification['engine_sha256']!=rt.sha(ROOT/'engine.py') or qualification['exact_real_code_comparisons']<128:
        raise ValueError('no matching qualified search controller')
    for key in ('oracle-events','pilot-events','reference-events'):
        if rt.sha(rt.REPO/qualification[key]['path'])!=qualification[key]['sha256']:
            raise ValueError('qualification event ledger changed')
    jobs=[]
    for source in original['jobs']:
        if source['decoder']['family']!='binary_css':continue
        for method in ('beam','relay'):
            jobs.append({**source,'id':source['id']+'-'+method,'method':method,'workers':1,
                         'n':original['codes'][source['code']]['n'],'source_target':None})
    return {**{k:v for k,v in original.items() if k not in ('schema','software','implementation_sha256')},
            'study_id':'roffe-tuned-beam-relay-latency','label':'Roffe X-only: tuned beam search and RelayBP latency tradeoffs',
            'jobs':jobs,'instruction_path':str((ROOT/'README.md').relative_to(rt.REPO)),
            'reference_plan_sha256':rt.sha(execution.OSD_ROOT/'plan.json'),'qualification_sha256':rt.sha(QUALIFICATION),
            'protocol':{'reference_shots':1024,'reference_repeats':5,'coarse_shots':512,
                        'finalist_shots':65536,'finalist_failures':100,'target_failures':20,'max_shots':100000000,
                        'seeds':execution.SEEDS,'budgets':execution.BUDGETS,'tolerance':.1},
            'claim_limit':'Controlled CSS X-only adaptations of BeamSearch and RelayBP on all original Roffe rates; unchanged canonical float64 min-sum sweeps, original-syndrome stopping and independent logical evaluation. No circuit-paper reproduction, Pauli Q-BP result or global-optimum claim. LER-first finite numerical/topology/memory tuning, separate coarse/finalist/fresh cohorts. Mean latency targets0.5/1/2/4 times same-CPU undamped BP+OSD0; actual timing and approximate1%-bin tail quantiles are explicit. All branches, discarded work, masking, random draws and selection included. Different selected controls are never silently pooled.'}


def extra():
    paths=[ROOT/name for name in ('engine.py','reference.py','runtime.py','run.py','report.py','README.md')]
    paths+=[QUALIFICATION,QUALIFICATION.with_name('qualify.py'),execution.ORIGINAL/'plan.json',execution.OSD_ROOT/'plan.json']
    paths += [rt.REPO/row['path'] for key,row in json.loads(QUALIFICATION.read_text()).items() if key.endswith('-events')]
    for source in (execution.ORIGINAL,execution.OSD_ROOT):
        paths += [rt.REPO/p for p in rt.load(source)['implementation_sha256']]
    return paths


def submit(test_only=False):
    with rt.dispatch_lock(ROOT):
        plan=rt.load(ROOT);(ROOT/'results').mkdir(exist_ok=True)
        path=ROOT/'dispatch.json';receipt=json.loads(path.read_text()) if path.exists() else {}
        command=shlex.join([sys.executable,str(Path(__file__).resolve())])
        base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1',
              '--cpus-per-task=1','--mem=2G','--time=4-00:00:00','--requeue',f'--chdir={rt.REPO}',
              f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
        def queue(name,options):
            if name in receipt and not test_only:return receipt[name]['id']
            argv=[*base,*(['--test-only'] if test_only else []),*options]
            if name=='collect':argv=['--mem=16G' if x=='--mem=2G' else x for x in argv]
            result=subprocess.run(argv,check=True,capture_output=True,text=True)
            if test_only:print(result.stdout+result.stderr);return
            jid=result.stdout.strip().split(';')[0]
            if not jid.isdigit():raise ValueError('invalid scheduler receipt')
            receipt[name]={'id':jid,'argv':argv,'plan_sha256':rt.sha(ROOT/'plan.json')};rt.write_json(path,receipt);print(name,jid,flush=True);return jid
        setup='export NUMBA_CACHE_DIR="/tmp/roffe-search-${SLURM_JOB_ID}"; mkdir -p "$NUMBA_CACHE_DIR"; '
        array=queue('array',['--job-name=roffe-beam-relay',f'--array=0-{len(plan["jobs"])-1}%218',
                             f'--output={ROOT/"results/slurm-%A_%a.log"}','--wrap='+setup+f'exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        if not test_only:
            queue('collect',['--job-name=roffe-search-audit',f'--dependency=afterok:{array}',
                             f'--output={ROOT/"results/collect-%j.log"}','--wrap='+setup+f'{command} --collect --complete'])
        return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('freeze','submit','test-only','collect'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--index',type=int);p.add_argument('--complete',action='store_true');a=p.parse_args()
    if a.freeze:rt.freeze(ROOT,design(),extra())
    elif a.submit or a.test_only:submit(a.test_only)
    elif a.index is not None:execution.execute(ROOT,a.index)
    else:
        receipt=execution.collect(ROOT,a.complete)
        from report import report
        report(ROOT,receipt)
        from bp_study_publish import refresh
        refresh(ROOT)
        print(len(receipt['finished_strata']),'/',receipt['planned_strata'],'strata audited',flush=True)


if __name__=='__main__':main()
