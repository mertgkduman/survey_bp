"""Independent finalist study retaining accuracy/latency diversity after coarse ties."""
import argparse
import fcntl
import gzip
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
PARENT=ROOT.with_name('roffe-2005-07016-search')
spec=importlib.util.spec_from_file_location('_roffe_frontier_event_protocol',PARENT/'runtime.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
rt=r.rt
r.SEEDS={'coarse':2026111551,'finalist':2026111562,'confirmation':2026111563}


def proposals(selection):
    """Training-only proposals; zero-count ties also retain budget-filling arms."""
    rows=selection['coarse'];chosen={}
    def add(row):chosen.setdefault(r.identity(row['controls']),row['controls'])
    for previous in selection['confirmations']:
        chosen.setdefault(r.identity(previous['controls']),previous['controls'])
    for budget in r.BUDGETS:
        eligible=[row for row in rows if row['runtime_ratio']<=1.25*budget]
        eligible=eligible or rows
        # Keep the prior fast LER objective as well as stronger search arms.
        add(r.choose(rows,budget))
        def diversity_key(row):
            return (row['rate'],abs(row['runtime_ratio']-budget),row['iterations']/row['shots'],r.identity(row['controls']))
        for row in sorted(eligible,key=diversity_key)[:2]:add(row)
        for solutions in (1,4):
            group=[row for row in eligible if row['controls']['solutions']==solutions]
            if group:add(min(group,key=diversity_key))
    return list(chosen.values())


def parent_selection(job):
    original=rt.load(PARENT);parent=next(j for j in original['jobs'] if j['id']==job['parent_job_id'])
    point=PARENT/'results'/parent['id'];path=point/'selection.json'
    value=json.loads(path.read_text());r.validate_selection(PARENT,parent,value)
    if json.loads((point/'complete.json').read_text())!={'selection_sha256':rt.sha(path)}:
        raise ValueError('parent worker not complete or lock changed')
    return parent,value,rt.sha(path)


def design():
    source=rt.load(PARENT)
    jobs=[{**j,'parent_job_id':j['id'],'id':j['id']+'-frontier'} for j in source['jobs']]
    return {**{k:v for k,v in source.items() if k not in ('schema','software','implementation_sha256')},
            'study_id':'roffe-beam-relay-frontier-finalists',
            'label':'Roffe X-only: beam/RelayBP finalists spanning latency budgets',
            'jobs':jobs,'parent_plan_sha256':rt.sha(PARENT/'plan.json'),
            'instruction_path':str((ROOT/'README.md').relative_to(rt.REPO)),
            'protocol':{**source['protocol'],'seeds':r.SEEDS},
            'claim_limit':source['claim_limit']+' Separate prospective finalist refinement: parent coarse zero-count ties retain both previous fast arms and budget-spanning/multiple-solution candidates. Parent confirmation outcomes are never read for proposal or selection. New finalist seed2026111562 and fresh confirmation seed2026111563; prior runs remain separate. Parent full audit and all new full-ledger/endpoint checks gate final publication.'}


def extra():
    source=rt.load(PARENT)
    return [ROOT/'run.py',ROOT/'README.md',PARENT/'plan.json',
            *[rt.REPO/p for p in source['implementation_sha256']]]


def execute(index):
    plan=rt.load(ROOT)
    if type(index) is not int or not 0<=index<len(plan['jobs']):raise ValueError('invalid frontier index')
    job=plan['jobs'][index];protocol=plan['protocol'];point=ROOT/'results'/job['id'];point.mkdir(parents=True,exist_ok=True)
    with (point/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        _,parent,parent_sha=parent_selection(job);proposed=proposals(parent);base=r.base_state(job)
        path=point/'selection.json'
        if not path.exists():
            ref=r.reference(point,job,protocol,'finalist')
            finalists=[r.evaluate(ROOT,point,base,r.engine.Controls(**c),'finalist',ref,protocol) for c in proposed]
            chosen={}
            for budget in r.BUDGETS:
                row=r.choose(finalists,budget);key=r.identity(row['controls'])
                chosen.setdefault(key,{'controls':row['controls'],'budgets':[]})['budgets'].append(budget)
            value={'schema':'css-search-frontier-selection-v1','campaign_plan_sha256':rt.sha(ROOT/'plan.json'),
                   'job_id':job['id'],'parent_selection_sha256':parent_sha,'parent_plan_sha256':rt.sha(PARENT/'plan.json'),
                   'proposed_controls':proposed,'coarse':[],'finalists':finalists,'confirmations':list(chosen.values()),
                   'objective':'minimum independent finalist LER under110% of budget, ties iterations/runtime/digest; fastest if none fit'}
            rt.write_json(path,value)
        value=json.loads(path.read_text());validate_parent_link(job,value)
        r.validate_selection(ROOT,job,value)
        ref=r.reference(point,job,protocol,'confirmation')
        for setting in value['confirmations']:
            r.evaluate(ROOT,point,base,r.engine.Controls(**setting['controls']),'confirmation',ref,protocol)
        rt.write_json(point/'complete.json',{'selection_sha256':rt.sha(path)})


def validate_parent_link(job,value):
    _,parent,digest=parent_selection(job)
    if (value['parent_selection_sha256']!=digest or value['parent_plan_sha256']!=rt.sha(PARENT/'plan.json')
            or value['proposed_controls']!=proposals(parent)):
        raise ValueError('frontier proposals differ from immutable parent training')
    if [r.identity(row['controls']) for row in value['finalists']]!=[r.identity(c) for c in value['proposed_controls']]:
        raise ValueError('missing or substituted finalist')


def collect(complete):
    plan=rt.load(ROOT)
    with gzip.open(PARENT/'verified.json.gz','rt') as stream:parent=json.load(stream)
    parent_plan=rt.load(PARENT)
    if (parent['plan_sha256']!=rt.sha(PARENT/'plan.json') or
            set(parent['finished_strata'])!={j['id'] for j in parent_plan['jobs']}):
        raise ValueError('frontier publication requires the complete parent training audit')
    for job in plan['jobs']:
        path=ROOT/'results'/job['id']/'selection.json'
        if path.exists():validate_parent_link(job,json.loads(path.read_text()))
    receipt=r.collect(ROOT,complete)
    receipt['parent_full_audit_sha256']=rt.sha(PARENT/'verified.json.gz')
    with gzip.open(ROOT/'verified.json.gz','wt',compresslevel=6) as stream:json.dump(receipt,stream,sort_keys=True,allow_nan=False)
    report=r.module('_roffe_frontier_report',PARENT/'report.py');report.report(ROOT,receipt)
    from bp_study_publish import refresh
    refresh(ROOT)
    print(len(receipt['finished_strata']),'/',receipt['planned_strata'],'frontier workers audited',flush=True)


def submit(test_only=False):
    with rt.dispatch_lock(ROOT):
        plan=rt.load(ROOT);(ROOT/'results').mkdir(exist_ok=True)
        source=json.loads((PARENT/'dispatch.json').read_text());path=ROOT/'dispatch.json'
        receipt=json.loads(path.read_text()) if path.exists() else {}
        command=shlex.join([sys.executable,str(Path(__file__).resolve())])
        base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1',
              '--cpus-per-task=1','--mem=2G','--time=4-00:00:00','--requeue',f'--chdir={rt.REPO}',
              f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
        def queue(name,options):
            if name in receipt and not test_only:return receipt[name]['id']
            argv=[*base,*(['--test-only'] if test_only else []),*options]
            if name=='collect':argv=['--mem=16G' if v=='--mem=2G' else v for v in argv]
            value=subprocess.run(argv,check=True,capture_output=True,text=True)
            if test_only:print(value.stdout+value.stderr);return
            jid=value.stdout.strip().split(';')[0]
            if not jid.isdigit():raise ValueError('invalid scheduler receipt')
            receipt[name]={'id':jid,'argv':argv,'plan_sha256':rt.sha(ROOT/'plan.json')};rt.write_json(path,receipt);print(name,jid,flush=True);return jid
        setup='export NUMBA_CACHE_DIR="/tmp/roffe-frontier-${SLURM_JOB_ID}"; mkdir -p "$NUMBA_CACHE_DIR"; '
        array=queue('array',['--job-name=roffe-search-frontier',f'--array=0-{len(plan["jobs"])-1}%218',
                             '--dependency=aftercorr:'+source['array']['id'],f'--output={ROOT/"results/slurm-%A_%a.log"}',
                             '--wrap='+setup+f'exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        if not test_only:
            queue('collect',['--job-name=roffe-frontier-audit',f'--dependency=afterok:{array}:'+source['collect']['id'],
                             f'--output={ROOT/"results/collect-%j.log"}','--wrap='+setup+f'{command} --collect --complete'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('freeze','submit','test-only','collect'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--index',type=int);parser.add_argument('--complete',action='store_true');a=parser.parse_args()
    if a.freeze:rt.freeze(ROOT,design(),extra())
    elif a.submit or a.test_only:submit(a.test_only)
    elif a.index is not None:execute(a.index)
    else:collect(a.complete)


if __name__=='__main__':main()
