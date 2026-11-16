"""Real-code oracle checks and warm serial timing pilot, separate from tuning."""
import importlib.util
import json
import gzip
from hashlib import sha256
from pathlib import Path
import sys
import time
from dataclasses import replace
from collections import Counter

import numpy as np

REPO=Path(__file__).resolve().parents[3]
ROOT=REPO/'data/reproductions/roffe-2005-07016-search'
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('_qualify_search_runtime',ROOT/'runtime.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
oracle=r.module('_qualify_search_oracle',ROOT/'reference.py')

proof={'status':'passed','engine_sha256':r.rt.sha(ROOT/'engine.py'),'exact_real_code_comparisons':0,
       'independent_oracle':'separate scalar min-sum equations, masking/tree orchestration and indexed RNG',
       'paths':Counter(),'pilot':[],'failures':[]}
oracle_events=[];pilot_events=[];reference_events=[]
original=r.rt.load(r.ORIGINAL)
for code in ('toric9','toric11','toric13','toric15'):
    job=next(j for j in original['jobs'] if j['code']==code and j['decoder']['family']=='binary_css' and j['physical_p']==.06)
    base=r.base_state(job);artifact=r.rt.load_artifact(REPO,job['code_artifact'],expected_semantic_sha256=job['code_semantic_sha256']).code
    h=artifact.hz
    for method in ('beam','relay'):
        for setting in range(4):
            c=r.engine.Controls(method,initial=4,per_unit=4,units=8,width=1 if setting==2 else 2,rounds=4,
                                damping=(0.,.3,.5,.7)[setting],alpha=.75 if setting%2 else 1.,
                                paper_scale=bool(setting%2),beta=.25 if setting%2 else 0.,solutions=4 if setting%2 else 1,
                                first_gamma=.35 if setting%2 else 0.,gamma_low=-.5,gamma_high=.95)
            p=r.engine.Prepared(base[3][0],job['physical_p'],c,7391)
            for shot in range(4):
                truth=r.rt.parent.base._sample(7391,6000,shot,base[1],depolarizing=False)
                syndrome=r.rt.parent.base._syndrome(base[2][1],truth)
                a=p.decode(syndrome,shot);b=oracle.decode(h,syndrome,p.initial,p.prior,c,7391,shot)
                assert a[2:4]==b[2:4]
                for index in (0,1,4,5,6,7):np.testing.assert_array_equal(a[index],b[index])
                assert bool(a[2])==np.array_equal((h@a[0])%2,syndrome)
                oracle_events.append({'code':code,'method':method,'controls':c.evidence(),'seed':7391,'shot':shot,
                                      'truth':truth.tolist(),'syndrome':syndrome.tolist(),'candidate':a[0].tolist(),
                                      'converged':a[2],'selected':a[3],'units':a[4].tolist(),'scores':a[5].tolist(),
                                      'posterior_sha256':sha256(a[6].tobytes()).hexdigest(),
                                      'messages_sha256':sha256(a[7].tobytes()).hexdigest(),'scalar_oracle_exact':True})
                proof['exact_real_code_comparisons']+=1
                proof['paths']['converged' if a[2] else 'capped']+=1
                proof['paths'][method+'_extra']+=max(0,len(a[4])-1)
                proof['paths']['pruned']+=int(a[4][:,6].sum())
        print('exact',code,method,proof['exact_real_code_comparisons'],flush=True)
    # Pilot uses a separate seed and is never a confirmation point.
    source=next(j for j in r.rt.load(r.OSD_ROOT)['jobs'] if j['code']==code and j['physical_p']==.02 and j['arm']=='bp_osd0')
    ref=r.osd.state({**source,'seed':7392});r.osd.warm(ref)
    events=[r.osd.event(ref,i) for i in range(512)]
    times=[e['decode_ns'] for e in events]
    reference_events.extend({'code':code,'seed':7392,'job':{**source,'seed':7392},'event':e} for e in events)
    job={**job,'seed':7392,'physical_p':.02};base=r.base_state(job)
    for method in ('beam','relay'):
        c=r.engine.Controls(method,initial=20,per_unit=20,units=32,width=4,rounds=8,first_gamma=.125)
        p=r.engine.Prepared(base[3][0],.02,c,7392);p.decode(np.zeros(len(p.graph.row_ptr)-1,dtype=np.uint8))
        counts=Counter();ns=iterations=0
        for shot in range(512):
            row=r.event(base,p,job,shot,{'mean_ns':sum(times)/len(times),'sha256':'0'*64})
            pilot_events.append({'code':code,'method':method,'controls':c.evidence(),'event':row})
            counts[row['outcome']]+=1;ns+=row['decode_ns'];iterations+=row['iterations']
        result={'code':code,'method':method,'p':.02,'shots':512,'counts':dict(counts),'mean_us':ns/512/1e3,
                'mean_iterations':iterations/512,'reference_us':sum(times)/512/1e3,'ratio':ns/sum(times),
                'controls':c.evidence(),'cohort':'qualification pilot only, seed7392'}
        proof['pilot'].append(result);print(result,flush=True)
assert proof['exact_real_code_comparisons']==128
assert proof['paths']['beam_extra'] and proof['paths']['relay_extra'] and proof['paths']['pruned']
for name,events in [('oracle-events',oracle_events),('pilot-events',pilot_events),('reference-events',reference_events)]:
    path=Path(__file__).with_name(name+'.jsonl.gz')
    with gzip.open(path,'wt',compresslevel=6) as stream:
        for row in events:stream.write(json.dumps(row,sort_keys=True)+'\n')
    proof[name]={'path':str(path.relative_to(REPO)),'sha256':r.rt.sha(path),'rows':len(events)}
r.rt.write_json(Path(__file__).with_name('qualification.json'),proof)
