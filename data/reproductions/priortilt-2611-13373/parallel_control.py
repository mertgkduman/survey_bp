"""Pin and deploy the user-requested resource-only continuation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
import run
import parallel


def freeze():
    run.load();q=json.loads((run.ROOT/'parallel-qualification.json').read_text())
    if len(q['cases'])!=3 or q['events']!=480 or q['parallel_source_sha256']!=run.sha(run.ROOT/'parallel.py'):raise ValueError('final parallel qualification missing or stale')
    paths=[run.ROOT/n for n in ('parallel.py','parallel-worker.sh','parallel_report.py','parallel_control.py','PARALLEL.md','parallel-qualification.json','qualify_parallel.py')]
    paths+=[run.REPO/'tests/test_prior_tilt_parallel.py']
    a={'schema':'priortilt-resource-amendment-v1','controller':parallel.VERSION,'workers':10,'cpus_per_point':10,
       'authorization':'User: use 10 processors per remaining points','parent_plan_sha256':run.sha(run.ROOT/'plan.json'),
       'science':'unchanged decoder, circuit, samples, RNG, point identity and per-basis20-error/100M prefix',
       'ordering':'concurrent sealed batches; commit in each basis global-shot order; speculative work separate',
       'timing':'new concurrent timing cohort; original per-shot fields retained; no standalone latency equivalence claim',
       'implementation_sha256':{str(p.relative_to(run.REPO)):run.sha(p) for p in paths}}
    path=run.ROOT/'resource-amendment.json'
    if path.exists():
        if json.loads(path.read_text())!=a:raise ValueError('refusing to alter frozen resource amendment')
    else:run.write_json(path,a)
    return a


def active_old():
    output=subprocess.check_output(['squeue','--array','-h','-j','61946754','-o','%i %T'],text=True)
    return [line.split()[0] for line in output.splitlines() if line.startswith('61946754_') and line.split()[1] in ('RUNNING','PENDING','COMPLETING','CONFIGURING')]


def submit():
    parallel.load_amendment();plan=run.load();path=run.ROOT/'parallel-dispatch.json'
    with run.lock(run.ROOT/'parallel-dispatch.lock',True):
        record=json.loads(path.read_text()) if path.exists() else {'resource_amendment_sha256':run.sha(run.ROOT/'resource-amendment.json'),'created_utc':datetime.now(timezone.utc).isoformat()}
        if record['resource_amendment_sha256']!=run.sha(run.ROOT/'resource-amendment.json'):raise ValueError('dispatch amendment changed')
        base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1','--time=4-00:00:00',f'--chdir={run.REPO}',
              f'--export=ALL,PYTHONPATH={run.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1,NUMBA_NUM_THREADS=1']
        if 'array' not in record:
            indices=[i for i,j in enumerate(plan['jobs']) if not (run.ROOT/'results'/j['id']/'audit.json').exists()]
            if not indices:raise ValueError('no remaining points')
            argv=base+['--cpus-per-task=10','--mem=24G','--requeue','--signal=B:USR1@180','--job-name=priortilt-10cpu',
                 '--dependency=afterany:61946754','--array='+','.join(map(str,indices))+f'%{len(indices)}',
                 f'--output={run.ROOT}/results/parallel-%A_%a.log',str(run.ROOT/'parallel-worker.sh')]
            jid=subprocess.check_output(argv,text=True).strip().split(';')[0];assert jid.isdigit()
            record['array']={'id':jid,'indices':indices,'argv':argv};run.write_json(path,record)
        if 'collector' not in record:
            argv=base+['--cpus-per-task=1','--mem=12G','--job-name=priortilt-par-collect','--dependency=afterok:'+record['array']['id'],
                      f'--output={run.ROOT}/results/parallel-collect-%j.log','--wrap='+f'exec {sys.executable} {run.ROOT}/parallel_report.py']
            jid=subprocess.check_output(argv,text=True).strip().split(';')[0];assert jid.isdigit()
            record['collector']={'id':jid,'argv':argv};run.write_json(path,record)
        if 'superseded_collector' not in record:
            result=subprocess.run(['scancel','61946755'],capture_output=True,text=True)
            record['superseded_collector']={'id':'61946755','returncode':result.returncode,'stderr':result.stderr};run.write_json(path,record)
        if 'superseded_workers' not in record:
            ids=active_old();record['cancel_requested']=ids;run.write_json(path,record)
            result=subprocess.run(['scancel',*ids],capture_output=True,text=True) if ids else None
            record['superseded_workers']={'ids':ids,'returncode':result.returncode if result else 0,'stderr':result.stderr if result else ''};run.write_json(path,record)
            if result and result.returncode:raise RuntimeError('old worker cancellation needs inspection')
        print(json.dumps(record),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','submit'));a=p.parse_args()
    if a.action=='freeze':freeze()
    else:submit()
