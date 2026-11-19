"""Read-only freeze, qualification, allocation and real decoder-process verification."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
STUDY=ROOT/'data/reproductions/priortilt-2611-13373-xyz'
sys.path.insert(0,str(STUDY));import run,parallel
plan=run.load();amendment=parallel.load_amendment();q=json.loads((STUDY/'qualification.json').read_text());dispatch=json.loads((STUDY/'dispatch.json').read_text())
assert q['passed'] and q['cpus']==50 and len(q['native_relay5']['cases'])==24
assert len(q['process_pilot'])==2 and all(p['events']==64 and p['full_original_dem_audit'] and p['all_pilot_shots_sequential_replay'] and p['resume_receipt_unchanged'] for p in q['process_pilot'])
assert dispatch['plan_sha256']==run.sha(STUDY/'plan.json')
assert plan['protocol']['target_errors']==20 and plan['protocol']['max_shots']==100000000
assert plan['protocol']['noise_seed'] not in (2026111891,2026111892) and plan['protocol']['policy_seed'] not in (2026111891,2026111892)
source=json.loads((STUDY/'source-contract.json').read_text());expected={b:next(c['execution_sha256'] for c in source['circuits'] if f'_memory_{b.upper()},' in c['file']) for b in run.BASES}
points=[]
for i,j in enumerate(plan['jobs']):
    job_id=dispatch['array']['id']+'_'+str(i)
    scheduler=subprocess.check_output(['scontrol','show','job','-o',job_id],text=True)
    assert 'JobState=RUNNING' in scheduler and 'NumCPUs=50 ' in scheduler and 'CPUs/Task=50 ' in scheduler
    (HERE/f'scontrol-{job_id}.txt').write_text(scheduler)
    root=STUDY/'results'/j['id'];processes=[json.loads(p.read_text()) for p in (root/'processes').glob('*.json')]
    assert len(processes)==50, f'{j["method"]}: waiting for50 initialized decoder processes, currently{len(processes)}'
    assert all(p['models']==expected for p in processes)
    hardware=json.loads((root/'parallel-hardware.json').read_text())
    assert hardware['cpus']==50 and hardware['slurm_cpus_per_task']=='50'
    assert hardware['resource_amendment_sha256']==run.sha(STUDY/'resource-amendment.json')
    stages=[]
    for p in sorted((root/'parallel-stages'/parallel.VERSION).glob('*.json')):
        m=json.loads(p.read_text());assert m['plan_sha256']==run.sha(STUDY/'plan.json')
        stages.append({'file':p.name,'sha256':run.sha(p),'worker':m['worker'],'summary':m['summary']})
    points.append({'point':j['id'],'job_id':job_id,'state':'RUNNING','allocated_cpus':50,'initialized_decoder_processes':processes,'hardware':hardware,'sealed_stages_at_snapshot':stages})
parent=json.loads((ROOT/'data/reproductions/priortilt-2611-13373/plan.json').read_text())
assert all(run.sha(ROOT/p)==h for p,h in parent['implementation_sha256'].items())
rows=list(csv.DictReader((STUDY/'comparison.csv').open()));assert not rows
out={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':run.sha(STUDY/'plan.json'),
     'resource_amendment_sha256':run.sha(STUDY/'resource-amendment.json'),'frozen_implementation_files':len(plan['implementation_sha256']),
     'all_parent_frozen_files_unchanged':len(parent['implementation_sha256']),'source_joint_DEM_execution':expected,
     'qualified_pilot_events':128,'native_relay_cases':24,'regression_cases_passed':95,'empty_publication_excludes_pilot_and_unfinished_points':True,
     'paper_source_ler_per_cycle':{r['method']:float(r['ler_per_cycle']) for r in csv.DictReader((STUDY/'source-table4.csv').open())},
     'point_cpus':100,'collector':dispatch['collector']['id'],'points':points,
     'scope':'Production startup/allocation/source-identity verification. Zero completed production measurements; no pilot outcomes pooled and no paper-agreement claim yet.'}
run.write_json(HERE/'launch-verification.json',out)
print('Verified two RUNNING50-CPU points,100 initialized decoder processes, frozen/source identities and empty audited-only report')
