"""Release only completed-parent task dependencies lost from Slurm's live cache."""
import datetime
import json
from pathlib import Path
import subprocess

REPO=Path(__file__).resolve().parents[3]
PARENT=REPO/'data/reproductions/roffe-2005-07016-search'
ROOT=PARENT.with_name('roffe-2005-07016-search-frontier')
source=json.loads((PARENT/'plan.json').read_text());plan=json.loads((ROOT/'plan.json').read_text())
parent_array=json.loads((PARENT/'dispatch.json').read_text())['array']['id']
array=json.loads((ROOT/'dispatch.json').read_text())['array']['id']
raw=subprocess.check_output(['sacct','-j',parent_array,'-X','--parsable2','--noheader','--format=JobID%40,State,ExitCode'],text=True)
completed=set()
for line in raw.splitlines():
    job,state,exit_code=line.split('|')[:3]
    if job.startswith(parent_array+'_') and job[len(parent_array)+1:].isdigit() and state=='COMPLETED' and exit_code=='0:0':
        completed.add(int(job[len(parent_array)+1:]))
queue=subprocess.check_output(['squeue','-r','-j',array,'-h','-o','%F_%K|%T'],text=True)
pending={int(line.split('|')[0].split('_')[1]) for line in queue.splitlines()
         if line.split('|')[1]=='PENDING' and line.split('|')[0].split('_')[1].isdigit()}
released=[];parents=[]
for index in sorted(completed & pending):
    a,b=source['jobs'][index],plan['jobs'][index]
    if b['parent_job_id']!=a['id']:raise ValueError('array correspondence mismatch')
    path=PARENT/'results'/a['id']/'selection.json'
    import hashlib
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if json.loads(path.with_name('complete.json').read_text())!={'selection_sha256':digest}:
        raise ValueError('source completion receipt mismatch')
    released.append(array+'_'+str(index));parents.append({'index':index,'parent_job_id':a['id'],'selection_sha256':digest})
receipt={'schema':'verified-parent-scheduler-dependency-release-v1','array':array,'parent_array':parent_array,
         'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verified_completed_parents':parents,
         'reason':'Old individual tasks are absent from Slurm live cache; aftercorr remains unfulfilled despite successful sacct records and immutable complete receipts. Scientific settings and collector dependencies unchanged.',
         'reference':'https://slurm.schedmd.com/scontrol.html#OPT_Dependency'}
if released:
    argv=['scontrol','update','JobId='+','.join(released),'Dependency=']
    result=subprocess.run(argv,capture_output=True,text=True)
    receipt.update(argv=argv,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
else:receipt.update(returncode=0,stdout='No eligible pending tasks',stderr='')
path=ROOT/'dependency-release.json'
if path.exists():path=ROOT/('dependency-release-'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S')+'.json')
path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print('verified completed parents released',len(released),'exit',receipt['returncode'],receipt.get('stderr',''))
if receipt['returncode']:raise SystemExit(receipt['returncode'])
