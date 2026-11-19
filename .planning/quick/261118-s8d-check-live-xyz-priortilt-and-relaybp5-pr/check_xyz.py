"""Read-only live progress reconciliation; unfinished counts are not LER measurements."""
from dataclasses import asdict
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
STUDY=ROOT/'data/reproductions/priortilt-2611-13373-xyz'
sys.path.insert(0,str(STUDY));import run,parallel
plan=run.load();parallel.load_amendment();dispatch=json.loads((STUDY/'dispatch.json').read_text());points=[]
for i,j in enumerate(plan['jobs']):
    root=STUDY/'results'/j['id'];path=root/'progress.json';data=path.read_bytes();progress=json.loads(data)
    (HERE/(j['method']+'-progress.json')).write_bytes(data)
    manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['plan_sha256']==run.sha(STUDY/'plan.json') and manifest['job']==j
    assert manifest['resolved_policy']==json.loads(json.dumps(asdict(run.spec_for(j))))
    bases={}
    for basis,s in progress['bases'].items():
        total={k:0 for k in ('shots','errors','iterations','directed_edge_updates','decode_ns','nonconvergence','random_draws','biased_node_updates')};joint=[0]*4;markers=[]
        for p in sorted((root/basis).glob('chunk-*.json')):
            raw=p.read_bytes();m=json.loads(raw)
            if m['start']>=s['shots']:break
            assert m['start']==total['shots'] and m['plan_sha256']==run.sha(STUDY/'plan.json')
            assert m['parallel_execution']['controller']==parallel.VERSION and m['parallel_execution']['resource_amendment_sha256']==run.sha(STUDY/'resource-amendment.json')
            for k in total:total[k]+=m['summary'][k]
            joint=[a+b for a,b in zip(joint,m['summary']['joint_counts'])]
            markers.append((p,sha256(raw).hexdigest(),m))
        assert all(total[k]==s[k] for k in total) and joint==s['joint_counts']
        assert sum(joint)==s['shots'] and joint[1]+joint[3]==s['errors'] and joint[2]+joint[3]==s['nonconvergence']
        for index in sorted({0,len(markers)-1}):
            p,h,m=markers[index];assert run.sha(p.with_suffix('.npz'))==m['sha256']
            run.verify_noise_binding(plan,j,basis,m['start'],m)
        bases[basis]={'shots':s['shots'],'errors':s['errors'],'nonconvergence':s['nonconvergence'],'committed_chunks':len(markers),
                      'mean_all_path_iterations_per_shot':s['iterations']/s['shots'],
                      'mean_directed_edge_updates_per_shot':s['directed_edge_updates']/s['shots'],
                      'sampled_bound_chunks':2 if len(markers)>1 else 1}
    job_id=dispatch['array']['id']+'_'+str(i)
    scheduler=subprocess.check_output(['scontrol','show','job','-o',job_id],text=True)
    assert 'JobState=RUNNING' in scheduler and 'NumCPUs=50 ' in scheduler
    (HERE/('scontrol-'+j['method']+'.txt')).write_text(scheduler.rstrip()+'\n')
    points.append({'method':j['method'],'job_id':job_id,'state':'RUNNING','cpus':50,'complete':(root/'complete.json').exists(),'audited':(root/'audit.json').exists(),
                   'progress_sha256':sha256(data).hexdigest(),'manifest_sha256':run.sha(root/'manifest.json'),'bases':bases})
result={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'points':points,'plan_sha256':run.sha(STUDY/'plan.json'),
        'resource_amendment_sha256':run.sha(STUDY/'resource-amendment.json'),'frozen_files_verified':len(plan['implementation_sha256']),
        'scope':'Live canonical-prefix marker arithmetic and first/last NPZ/shared-noise bindings only. Per-stage creation audits retained; no final full worker audit yet, no provisional LER or statistical paper-agreement claim.'}
(HERE/'xyz-progress-check.json').write_text(json.dumps(result,indent=2)+'\n')
for p in points:print(p['method'],{b:(s['shots'],s['errors']) for b,s in p['bases'].items()},'50CPUs','audited',p['audited'])
