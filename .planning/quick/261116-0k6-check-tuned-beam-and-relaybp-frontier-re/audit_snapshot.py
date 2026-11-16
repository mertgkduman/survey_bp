"""Parallel completed-worker audit using the unchanged frozen study auditors."""
from concurrent.futures import ProcessPoolExecutor
import datetime
import gzip
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[3]
ROOT=REPO/'data/reproductions/roffe-2005-07016-search-frontier'
PARENT=ROOT.with_name('roffe-2005-07016-search')
spec=importlib.util.spec_from_file_location('_frontier_completed_snapshot',ROOT/'run.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
r,rt=run.r,run.rt


def pin_worker():
    available=sorted(os.sched_getaffinity(0))
    index=multiprocessing.current_process()._identity[0]-1
    os.sched_setaffinity(0,{available[index%len(available)]})
    os.environ['NUMBA_CACHE_DIR']=f'/tmp/frontier-check-{os.environ.get("SLURM_JOB_ID","local")}-{os.getpid()}'


def audit_point(item):
    job,protocol,plan_sha=item
    point=ROOT/'results'/job['id'];path=point/'selection.json';digest=rt.sha(path)
    if json.loads((point/'complete.json').read_text())!={'selection_sha256':digest}:
        raise ValueError('completion receipt differs from sealed selection')
    value=json.loads(path.read_text());run.validate_parent_link(job,value);r.validate_selection(ROOT,job,value)
    base=r.base_state(job);references=r.audit_references(point,job,protocol)
    tuning=[];rows=[]
    for stored in value['coarse']+value['finalists']:
        child=r.child_job(job,r.engine.Controls(**stored['controls']),stored['job']['stage'],protocol)
        if child!=stored['job']:raise ValueError('finalist differs from frozen job/protocol')
        summary=r.audit_child(ROOT,point,base,child,references)
        if any(stored.get(k)!=v for k,v in summary.items()):raise ValueError('finalist ledger differs from selection')
        tuning.append(stored)
    for setting in value['confirmations']:
        child=r.child_job(job,r.engine.Controls(**setting['controls']),'confirmation',protocol)
        directory=point/'confirmation'/child['id'];summary=r.audit_child(ROOT,point,base,child,references)
        rows.append({**summary,'job':child,'point':job['id'],'budgets':setting['budgets'],
                     'directory':str(directory.relative_to(REPO)),'summary_sha256':rt.sha(directory/'summary.json'),
                     'selection_sha256':digest})
    return job['id'],rows,tuning


def main():
    plan=rt.load(ROOT);parent_plan=rt.load(PARENT)
    with gzip.open(PARENT/'verified.json.gz','rt') as stream:parent=json.load(stream)
    if (parent['plan_sha256']!=rt.sha(PARENT/'plan.json') or
            set(parent['finished_strata'])!={j['id'] for j in parent_plan['jobs']}):
        raise ValueError('complete parent audit is required')
    jobs=[j for j in plan['jobs'] if (ROOT/'results'/j['id']/'complete.json').exists()]
    plan_sha=rt.sha(ROOT/'plan.json');started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    requested=int(os.environ.get('SLURM_CPUS_PER_TASK','1'))
    workers=min(requested,len(os.sched_getaffinity(0)))
    items=[(j,plan['protocol'],plan_sha) for j in jobs]
    finished=[];points=[];tuning=[]
    with ProcessPoolExecutor(max_workers=workers,initializer=pin_worker) as pool:
        for name,rows,training in pool.map(audit_point,items,chunksize=1):
            finished.append(name);points.extend(rows);tuning.extend(training)
            print('audited',len(finished),'/',len(jobs),name,'measurements',len(points),flush=True)
    if rt.sha(ROOT/'plan.json')!=plan_sha:raise ValueError('source plan changed during audit')
    receipt={'schema':'canonical-css-search-verification-v1','plan_sha256':plan_sha,
             'parent_full_audit_sha256':rt.sha(PARENT/'verified.json.gz'),
             'planned_strata':len(plan['jobs']),'finished_strata':finished,'points':points,'tuning':tuning,
             'collection_scope':'snapshot of sealed completed workers; active workers excluded',
             'snapshot_started_utc':started,'collector_source_sha256':rt.sha(Path(__file__)),
             'audit_cpus':workers,'audit_all_finalist_and_confirmation_ledgers':True}
    tmp=ROOT/'results/check-261116-verified.json.gz'
    with gzip.open(tmp,'wt',compresslevel=6) as stream:json.dump(receipt,stream,sort_keys=True,allow_nan=False)
    os.replace(tmp,ROOT/'verified.json.gz')
    report=r.module('_frontier_completed_report',PARENT/'report.py');print(report.report(ROOT,receipt),flush=True)
    from bp_study_publish import refresh
    refresh(ROOT)


if __name__=='__main__':main()
