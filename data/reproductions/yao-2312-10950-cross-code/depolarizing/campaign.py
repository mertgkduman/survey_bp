"""Freeze pilot and independent follow-up cohorts and dispatch Slurm shards."""
import argparse
from hashlib import sha256
import json
import importlib.util
import math
from pathlib import Path
import subprocess
import sys

from study import ROOT,REPO,implementation_hashes


def freeze_pilot():
    p=ROOT/'pilot.json'
    if p.exists():raise FileExistsError(p)
    jobs=[]
    for ci,c in enumerate(('b1','c2')):
        for pi in range(4,11):
            prob=pi/100
            jobs.append({'code':c,'p':prob,'seed':20261104+ci*100+pi,'start_shot':0,'shots':2000,
                         'output':str((ROOT/'results'/f'pilot-{c}-p{pi:02d}').relative_to(REPO))})
    p.write_text(json.dumps({'schema':'b1-c2-fixed-depolarizing-campaign-v1','stage':'pilot',
        'implementation_sha256':implementation_hashes(),'jobs':jobs,
        'followup_rule':'min(1000000,max(20000,ceil(400000/min_failures))); zero selects 1000000',
        'pilot_excluded_from_followup_estimates':True},indent=2,sort_keys=True)+'\n')
    return p


def freeze_followup():
    spec=importlib.util.spec_from_file_location('depolarizing_campaign_assessment',ROOT/'assess.py')
    assessment=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=assessment;spec.loader.exec_module(assessment)
    p=ROOT/'campaign.json'
    if p.exists():raise FileExistsError(p)
    pilot=ROOT/'pilot.json';totals,_,_=assessment.audit_plan(pilot,replay_stride=97)
    jobs=[];receipts=[]
    for ci,c in enumerate(('b1','c2')):
        for pi in range(4,11):
            prob=pi/100;arms=totals[(c,prob)]
            k=min(sum(arms[a]['counts'][f] for f in ('type_i','type_ii')) for a in arms)
            n=1000000 if k==0 else min(1000000,max(20000,math.ceil(400000/k)))
            receipts.append({'code':c,'p':prob,'pilot_smaller_failure_count':k,'fixed_followup_shots':n})
            for start in range(0,n,50000):
                jobs.append({'code':c,'p':prob,'seed':20262105+ci*100+pi,'start_shot':start,
                             'shots':min(50000,n-start),
                             'output':str((ROOT/'results'/f'fixed-{c}-p{pi:02d}-s{start:07d}').relative_to(REPO))})
    p.write_text(json.dumps({'schema':'b1-c2-fixed-depolarizing-campaign-v1','stage':'independent_followup',
        'implementation_sha256':implementation_hashes(),'pilot_sha256':sha256(pilot.read_bytes()).hexdigest(),
        'pilot_excluded_from_estimate':True,'sample_size_receipts':receipts,'jobs':jobs},indent=2,sort_keys=True)+'\n')
    return p


def submit(path,max_parallel=24):
    plan=json.loads(path.read_text())
    command=['sbatch','--parsable','-J','b1-c2-depolarizing','-p','common','--account=pfisterlab',
             '-c','1','--mem=4G','-t','03:00:00',f'--array=0-{len(plan["jobs"])-1}%{max_parallel}',
             '-o',str(ROOT/'results'/f'{plan["stage"]}-%A_%a.log'),
             '--export=ALL,PYTHONPATH='+str(REPO/'src')+',OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1',
             '--wrap',f'{sys.executable} {ROOT/"run.py"} --plan {path} --index $SLURM_ARRAY_TASK_ID']
    receipt={'job_id':subprocess.run(command,check=True,capture_output=True,text=True).stdout.strip(),
             'plan':path.name,'tasks':len(plan['jobs']),'max_parallel':max_parallel,'command':command}
    (ROOT/f'{plan["stage"]}-dispatch.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['pilot','followup']);a=ap.parse_args()
    (ROOT/'results').mkdir(exist_ok=True)
    submit(freeze_pilot() if a.stage=='pilot' else freeze_followup())
