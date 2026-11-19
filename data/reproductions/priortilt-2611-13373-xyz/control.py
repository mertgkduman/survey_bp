"""Idempotent frozen XYZ campaign submission;50 CPUs per paired decoder point."""
import argparse
from datetime import datetime,timezone
import json
import subprocess
import sys
import run,parallel


def submit():
    plan=run.load();parallel.load_amendment();qualification=json.loads((run.ROOT/'qualification.json').read_text())
    if not qualification['passed'] or qualification['cpus']!=50:raise ValueError('qualified50-process execution required')
    with run.lock(run.ROOT/'dispatch.lock',True):
        path=run.ROOT/'dispatch.json';digest=run.sha(run.ROOT/'plan.json')
        record=json.loads(path.read_text()) if path.exists() else {'created_utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':digest,'qualification_job_id':qualification['slurm_job_id']}
        if record['plan_sha256']!=digest:raise ValueError('dispatch plan changed')
        base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1','--time=4-00:00:00',f'--chdir={run.REPO}',
              f'--export=ALL,PYTHONPATH={run.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1,NUMBA_NUM_THREADS=1']
        if 'array' not in record:
            indices=[i for i,j in enumerate(plan['jobs']) if not (run.ROOT/'results'/j['id']/'audit.json').exists()]
            if not indices:raise ValueError('all XYZ points already audited')
            argv=base+['--cpus-per-task=50','--mem=96G','--requeue','--signal=B:USR1@180','--job-name=priortilt-xyz-50',
                       '--array='+','.join(map(str,indices))+'%2','--dependency=afterok:'+qualification['slurm_job_id'],
                       f'--output={run.ROOT}/results/worker-%A_%a.log',str(run.ROOT/'worker.sh')]
            jid=subprocess.check_output(argv,text=True).strip().split(';')[0];assert jid.isdigit()
            record['array']={'id':jid,'indices':indices,'argv':argv};run.write_json(path,record)
        if 'collector' not in record:
            argv=base+['--cpus-per-task=1','--mem=12G','--job-name=priortilt-xyz-collect','--dependency=afterok:'+record['array']['id'],
                       f'--output={run.ROOT}/results/collect-%j.log','--wrap='+f'exec {sys.executable} {run.ROOT}/report.py']
            jid=subprocess.check_output(argv,text=True).strip().split(';')[0];assert jid.isdigit()
            record['collector']={'id':jid,'argv':argv};run.write_json(path,record)
        return record


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','submit'));args=parser.parse_args()
    if args.action=='freeze':
        run.freeze();import report;report.collect()
    else:print(json.dumps(submit(),indent=2))
