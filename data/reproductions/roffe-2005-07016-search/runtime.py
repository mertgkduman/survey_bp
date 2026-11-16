"""Prespecified tuning, fresh confirmation, replay and latency accounting."""
from collections import Counter
from dataclasses import replace
import fcntl
import gzip
from hashlib import sha256
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import bp_study_runtime as rt


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); sys.modules[name] = value; spec.loader.exec_module(value)
    return value


engine = module('_roffe_search_engine', ROOT / 'engine.py')
OSD_ROOT = ROOT.with_name('roffe-2005-07016-osd-fast')
ORIGINAL = ROOT.with_name('roffe-2005-07016-bp')
osd = module('_roffe_search_reference_osd', OSD_ROOT / 'runtime.py')
SEEDS = {'coarse': 2026111551, 'finalist': 2026111552, 'confirmation': 2026111553}
BUDGETS = (.5, 1., 2., 4.)
BATCH = 2048
TIMING_FIELDS = {'decode_ns', 'reference_ns', 'reference_sha256'}


def identity(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def numeric_grid(method):
    return [engine.Controls(method, initial=20, per_unit=20, units=32, width=2, rounds=8,
                            damping=d, alpha=a, paper_scale=paper, beta=b, first_gamma=.125)
            for d, (paper, a), b in itertools.product((0., .3, .5, .7), ((True, 1.), (False, .75), (False, 1.)), (0., .25))]


def architecture_grid(c):
    if c.method == 'beam':
        return [replace(c, initial=t, per_unit=u, width=w, rounds=r, solutions=s, units=min(512, 2*w*r))
                for t,u,w,r,s in itertools.product((5,20,50), (5,20,40), (1,4,16), (4,12), (1,4))]
    return [replace(c, initial=t, per_unit=u, units=legs, solutions=s)
            for t,u,legs,s in itertools.product((10,40,80), (10,30,60), (4,16,64), (1,4))]


def memory_grid(c):
    return [replace(c, first_gamma=g, gamma_low=low, gamma_high=high)
            for g,(low,high) in itertools.product((0., .125, .35),
                 ((-.24,.66),(-.5,.5),(-.25,1.),(0.,.75),(-.5,1.)))]


def neighbors(c):
    values = [c]
    for name, delta, low, high in [('damping',.1,0.,.9), ('alpha',.1,.25,1.25), ('beta',.125,0.,1.5)]:
        values += [replace(c, **{name: round(min(high,max(low,getattr(c,name)+direction*delta)),6)}) for direction in (-1,1)]
    if c.method == 'relay':
        values += [replace(c, gamma_low=max(-.75,c.gamma_low-.1)), replace(c,gamma_high=min(1.,c.gamma_high+.1))]
    return values


def rank(row):
    return (row['rate'], row['iterations']/row['shots'], row['runtime_ratio'], identity(row['controls']))


def choose(rows, budget):
    eligible = [r for r in rows if r['runtime_ratio'] <= 1.1*budget]
    return min(eligible, key=rank) if eligible else min(rows, key=lambda r:(r['runtime_ratio'], *rank(r)))


def leaders(rows, count=2):
    eligible = [r for r in rows if r['runtime_ratio'] <= 4.4]
    return sorted(eligible or rows, key=rank)[:count]


def child_job(base, c, stage, protocol):
    shots = protocol['coarse_shots'] if stage == 'coarse' else protocol['finalist_shots'] if stage == 'finalist' else protocol['max_shots']
    target = shots+1 if stage == 'coarse' else protocol['finalist_failures'] if stage == 'finalist' else protocol['target_failures']
    return {**base, 'id': base['id']+'-'+stage+'-'+identity(c.evidence())[:20],
            'seed': SEEDS[stage], 'stage': stage, 'controls': c.evidence(), 'max_shots': shots,
            'target_block_failures': target,
            'decoder': {**base['decoder'], 'max_iterations': c.initial+c.units*c.per_unit,
                        'initial_iterations': c.initial, 'iterations_per_unit': c.per_unit,
                        'unit_limit': c.units, 'v2c_damping': c.damping, 'alpha': c.alpha, 'beta': c.beta,
                        'alpha_schedule': '1-2**(-iteration)' if c.paper_scale else 'constant',
                        'search': c.evidence(), 'execution_backend': engine.VERSION}}


def base_state(job):
    # Bind using the unchanged source-compatible graph; the search controller
    # applies its explicit controls after binding.
    return rt.state(job)


def event(base, prepared, job, shot, ref):
    _,n,packed,_ = base
    truth = rt.parent.base._sample(job['seed'], round(job['physical_p']*100000), shot, n, depolarizing=False)
    syndrome = rt.parent.base._syndrome(packed[1], truth)
    start = time.perf_counter_ns()
    candidate,posterior,valid,selected,trace,scores,posts,messages = prepared.decode(syndrome,shot)
    elapsed = time.perf_counter_ns()-start
    outcome,_ = rt.parent.outcome(*packed,truth,candidate,joint=False)
    if bool(valid) != (outcome != 'type_i'):
        raise ValueError('original-problem evaluation disagrees with decoder stopping')
    return {'schema':'canonical-css-search-shot-v1','shot':shot,'outcome':outcome,
            'iterations':int(trace[:,3].sum()),'directed_edge_updates':int(2*np.dot(trace[:,3],trace[:,4])),
            'decode_ns':elapsed,'reference_ns':ref['mean_ns'],'reference_sha256':ref['sha256'],
            'converged':bool(valid),'selected_unit':int(selected),'units':trace.tolist(),'scores':scores.tolist(),
            'error_sha256':sha256(truth.tobytes()).hexdigest(),'syndrome_sha256':sha256(syndrome.tobytes()).hexdigest(),
            'candidate_sha256':sha256(candidate.tobytes()).hexdigest(),
            'terminal_posterior_sha256':sha256(posterior.tobytes()).hexdigest(),
            'all_posterior_sha256':sha256(posts.tobytes()).hexdigest(),
            'all_message_sha256':sha256(messages.tobytes()).hexdigest()}


class Ledger(rt.parent.base.Ledger):
    def __init__(self,directory,job,references_available=None):
        self.references_available=references_available
        self.directed_edges = self.reference_ns = self.extra_units = self.prunes = self.clips = 0
        self.references = Counter(); self.histogram = Counter()
        super().__init__(directory,job)

    def add(self,row,line):
        c = engine.Controls(**self.job['controls']); trace = row.get('units',[])
        if (row.get('schema') != 'canonical-css-search-shot-v1' or not trace or len(trace)>c.units+1
                or len(row.get('scores',[])) != len(trace) or type(row.get('converged')) is not bool
                or row['converged'] != (row['outcome'] != 'type_i')
                or not isinstance(row.get('reference_ns'),(float,int)) or not math.isfinite(row['reference_ns']) or row['reference_ns']<=0
                or type(row.get('decode_ns')) is not int or row['decode_ns']<=0):
            raise ValueError('invalid search shot, convergence or timing')
        for key in ('reference_sha256','error_sha256','syndrome_sha256','candidate_sha256',
                    'terminal_posterior_sha256','all_posterior_sha256','all_message_sha256'):
            digest=row.get(key)
            if not isinstance(digest,str) or len(digest)!=64 or any(x not in '0123456789abcdef' for x in digest):
                raise ValueError('invalid provenance digest')
        if self.references_available is not None:
            ref=self.references_available.get(row['reference_sha256'])
            if ref is None or ref['mean_ns']!=row['reference_ns'] or ref['stage']!=self.job['stage']:
                raise ValueError('event timing differs from original same-stage reference')
        for i,unit in enumerate(trace):
            if (len(unit)!=8 or any(type(v) is not int for v in unit) or not 1<=unit[3]<=(c.initial if i==0 else c.per_unit)
                    or not 0<=unit[4]<=self.job['graph_edges'] or unit[5] not in (0,1) or unit[6] not in (0,1) or unit[7]<0
                    or (i==0 and unit[:3]!=[-1,-1,-1])
                    or (i>0 and not 0<=unit[0]<i)):
                raise ValueError('invalid path lineage/work')
            if i>0 and (c.method=='relay' and (unit[0]!=i-1 or unit[1:3]!=[-1,-1]) or
                        c.method=='beam' and (not 0<=unit[1]<self.job['n'] or unit[2] not in (0,1))):
                raise ValueError('invalid search ancestry')
        selected=row['selected_unit']
        if (row['iterations']!=sum(u[3] for u in trace) or row['directed_edge_updates']!=2*sum(u[3]*u[4] for u in trace)
                or (row['converged'] and (not 0<=selected<len(trace) or not trace[selected][5]))
                or (not row['converged'] and (selected!=-1 or any(u[5] for u in trace)))
                or any(not math.isfinite(s) for s in row['scores'])):
            raise ValueError('invalid cumulative work or candidate selection')
        super().add(row,line)
        self.directed_edges+=row['directed_edge_updates']; self.reference_ns+=row['reference_ns']
        self.references[row['reference_sha256']]+=1; self.extra_units+=len(trace)-1
        self.prunes+=sum(u[6] for u in trace); self.clips+=sum(u[7] for u in trace)
        self.histogram[math.floor(math.log(row['decode_ns'])/math.log(1.01))]+=1

    def commit(self,rows):
        space=os.statvfs(self.directory)
        if space.f_bavail*space.f_frsize<50*1024**3:
            raise RuntimeError('less than50GiB free; preserve exact checkpoint')
        return super().commit(rows)

    def summary(self):
        quantiles={}
        for q in (.5,.95,.99):
            target=math.ceil(q*self.shots); cumulative=0
            for key,count in sorted(self.histogram.items()):
                cumulative+=count
                if cumulative>=target:
                    quantiles[str(q)]=1.01**(key+1)/1e9; break
        return {**super().summary(),'directed_edge_updates':self.directed_edges,
                'reference_ns':self.reference_ns,'runtime_ratio':self.decode_ns/self.reference_ns,
                'reference_receipts':dict(self.references),'extra_units':self.extra_units,'branch_prunes':self.prunes,
                'memory_prior_clips':self.clips,'latency_quantiles_seconds':quantiles,
                'quantile_method':'upper endpoint of 1%-wide logarithmic ns bins; at most1% rounding error'}


def reference(point,job,protocol,stage):
    source=next(j for j in rt.load(OSD_ROOT)['jobs'] if j['code']==job['code'] and j['physical_p']==job['physical_p'] and j['arm']=='bp_osd0')
    source={**source,'seed':SEEDS[stage]}; value=osd.state(source); osd.warm(value)
    blocks,rows=[],[]
    for repeat in range(protocol['reference_repeats']):
        events=[osd.event(value,i) for i in range(protocol['reference_shots'])]
        blocks.append(sum(e['decode_ns'] for e in events)/len(events))
        rows.extend({**e,'repeat':repeat} for e in events)
    receipt={'schema':'same-cpu-osd0-search-reference-v1','stage':stage,'mean_ns':statistics.median(blocks),
             'block_mean_ns':blocks,'job':source,'host':platform.node(),'affinity':sorted(os.sched_getaffinity(0)),
             'reference_plan_sha256':rt.sha(OSD_ROOT/'plan.json'),
             'scope':'warmed canonical BP plus complete qualified OSD0 API; excludes sampling/truth/JIT/provenance serialization'}
    directory=point/'references';directory.mkdir(exist_ok=True)
    path=directory/(identity(receipt)+'.json');rt.write_json(path,receipt)
    with gzip.open(path.with_suffix('.jsonl.gz'),'wt',compresslevel=3) as stream:
        for row in rows: stream.write(json.dumps(row,sort_keys=True)+'\n')
    return {**receipt,'sha256':rt.sha(path)}


def evaluate(root,point,base,c,stage,ref,protocol):
    job=child_job(base[0],c,stage,protocol);directory=point/stage/job['id'];directory.mkdir(parents=True,exist_ok=True)
    manifest={'schema':'css-search-child-v1','campaign_plan_sha256':rt.sha(root/'plan.json'),'job':job,
              'selection_sha256':rt.sha(point/'selection.json') if stage=='confirmation' else None}
    path=directory/'manifest.json'
    if path.exists() and json.loads(path.read_text())!=manifest: raise ValueError('frozen child manifest changed')
    if not path.exists():rt.write_json(path,manifest)
    ledger=Ledger(directory,job)
    p=engine.Prepared(base[3][0],job['physical_p'],c,job['seed']);p.decode(np.zeros(len(p.graph.row_ptr)-1,dtype=np.uint8))
    while not ledger.complete:
        rows=[];failures=ledger.failures
        for shot in range(ledger.shots,min(job['max_shots'],ledger.shots+BATCH)):
            row=event(base,p,job,shot,ref);rows.append(row);failures+=row['outcome'] in rt.parent.base.FAILURES
            if failures==job['target_block_failures']:break
        ledger.commit(rows)
        if stage=='confirmation':print(job['id'],ledger.shots,ledger.failures,flush=True)
    summary={**ledger.summary(),'manifest_sha256':rt.sha(path)}
    destination=directory/'summary.json'
    if destination.exists() and json.loads(destination.read_text())!=summary:raise ValueError('terminal summary changed')
    rt.write_json(destination,summary)
    return {**summary,'controls':c.evidence(),'job':job,'summary_sha256':rt.sha(destination),
            'directory':str(directory.relative_to(rt.REPO))}


def execute(root,index):
    plan=rt.load(root)
    if type(index) is not int or not 0<=index<len(plan['jobs']):raise ValueError('invalid job index')
    job=plan['jobs'][index];protocol=plan['protocol'];point=root/'results'/job['id'];point.mkdir(parents=True,exist_ok=True)
    with (point/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        base=base_state(job);selection_path=point/'selection.json'
        if not selection_path.exists():
            ref=reference(point,job,protocol,'coarse');history={}
            def measure(c):
                key=identity(c.evidence())
                if key not in history:history[key]=evaluate(root,point,base,c,'coarse',ref,protocol)
                return history[key]
            first=[measure(c) for c in numeric_grid(job['method'])]
            numeric=leaders(first)
            if job['method']=='relay':
                memory=[measure(v) for row in numeric for v in memory_grid(engine.Controls(**row['controls']))]
                numeric=leaders(memory)
            for row in numeric:
                for c in architecture_grid(engine.Controls(**row['controls'])):measure(c)
            coarse=list(history.values())
            for budget in BUDGETS:
                c=engine.Controls(**choose(coarse,budget)['controls'])
                for v in neighbors(c):measure(v)
            coarse=list(history.values());finalists={}
            for budget in BUDGETS:
                eligible=[r for r in coarse if r['runtime_ratio']<=budget*1.1]
                for r in sorted(eligible,key=rank)[:3] if eligible else [choose(coarse,budget)]:
                    finalists[identity(r['controls'])]=r['controls']
            ref=reference(point,job,protocol,'finalist')
            final=[evaluate(root,point,base,engine.Controls(**c),'finalist',ref,protocol) for c in finalists.values()]
            chosen={}
            for budget in BUDGETS:
                row=choose(final,budget);key=identity(row['controls'])
                chosen.setdefault(key,{'controls':row['controls'],'budgets':[]})['budgets'].append(budget)
            selection={'schema':'css-search-selection-v1','campaign_plan_sha256':rt.sha(root/'plan.json'),
                       'job_id':job['id'],'coarse':coarse,'finalists':final,'confirmations':list(chosen.values()),
                       'objective':'minimum empirical LER under110% of each mean-time budget, ties mean iterations/runtime/control digest; fastest if none fit'}
            rt.write_json(selection_path,selection)
        selection=json.loads(selection_path.read_text())
        validate_selection(root,job,selection)
        ref=reference(point,job,protocol,'confirmation')
        for setting in selection['confirmations']:
            evaluate(root,point,base,engine.Controls(**setting['controls']),'confirmation',ref,protocol)
        rt.write_json(point/'complete.json',{'selection_sha256':rt.sha(selection_path)})


def validate_selection(root,job,selection):
    if selection['campaign_plan_sha256']!=rt.sha(root/'plan.json') or selection['job_id']!=job['id']:
        raise ValueError('selection belongs to another campaign/point')
    expected={}
    for budget in BUDGETS:
        row=choose(selection['finalists'],budget);key=identity(row['controls'])
        expected.setdefault(key,{'controls':row['controls'],'budgets':[]})['budgets'].append(budget)
    if list(expected.values())!=selection['confirmations']:raise ValueError('selection violates frozen objective')
    for row in selection['coarse']+selection['finalists']:
        directory=rt.REPO/row['directory']
        if rt.sha(directory/'summary.json')!=row['summary_sha256']:raise ValueError('tuning summary changed after lock')


def audit_references(point,job,protocol):
    references={}
    source=next(j for j in rt.load(OSD_ROOT)['jobs'] if j['code']==job['code'] and j['physical_p']==job['physical_p'] and j['arm']=='bp_osd0')
    for path in (point/'references').glob('*.json'):
        value=json.loads(path.read_text());stage=value['stage']
        if (stage not in SEEDS or value['job']!={**source,'seed':SEEDS[stage]}
                or value['reference_plan_sha256']!=rt.sha(OSD_ROOT/'plan.json')
                or not value.get('host') or not value.get('affinity')):
            raise ValueError('reference source identity mismatch')
        totals=[0]*protocol['reference_repeats'];counts=[0]*len(totals)
        with gzip.open(path.with_suffix('.jsonl.gz'),'rt') as stream:
            for line in stream:
                row=json.loads(line);repeat=row['repeat']
                if (not 0<=repeat<len(totals) or row['shot']!=counts[repeat]
                        or counts[repeat]>=protocol['reference_shots']
                        or row['decode_ns']!=row['bp_decode_ns']+row['osd_decode_ns']
                        or row['decode_ns']<=0):
                    raise ValueError('invalid repeated reference event')
                totals[repeat]+=row['decode_ns'];counts[repeat]+=1
        if counts!=[protocol['reference_shots']]*len(totals):raise ValueError('incomplete reference')
        means=[t/n for t,n in zip(totals,counts)]
        if means!=value['block_mean_ns'] or statistics.median(means)!=value['mean_ns']:
            raise ValueError('reference arithmetic mismatch')
        references[rt.sha(path)]=value
    return references


def audit_child(root,point,base,child,references):
    directory=point/child['stage']/child['id'];path=directory/'manifest.json'
    expected={'schema':'css-search-child-v1','campaign_plan_sha256':rt.sha(root/'plan.json'),'job':child,
              'selection_sha256':rt.sha(point/'selection.json') if child['stage']=='confirmation' else None}
    if json.loads(path.read_text())!=expected:raise ValueError('child manifest mismatch')
    ledger=Ledger(directory,child,references);summary={**ledger.summary(),'manifest_sha256':rt.sha(path)}
    if json.loads((directory/'summary.json').read_text())!=summary:raise ValueError('full-ledger summary mismatch')
    c=engine.Controls(**child['controls']);p=engine.Prepared(base[3][0],child['physical_p'],c,child['seed'])
    for stored in (ledger.first,ledger.last):
        ref={**references[stored['reference_sha256']],'sha256':stored['reference_sha256']}
        replay=event(base,p,child,stored['shot'],ref)
        if {k:v for k,v in replay.items() if k not in TIMING_FIELDS}!={k:v for k,v in stored.items() if k not in TIMING_FIELDS}:
            raise ValueError('endpoint replay mismatch')
    return summary


def collect(root,complete=False):
    plan=rt.load(root);rows=[];finished=[];tuning=[]
    for job in plan['jobs']:
        point=root/'results'/job['id'];path=point/'selection.json'
        if not path.exists():continue
        selection=json.loads(path.read_text());validate_selection(root,job,selection)
        tuning.extend(selection['coarse']+selection['finalists']);checked=0
        base=base_state(job)
        references=audit_references(point,job,plan['protocol'])
        for row in selection['coarse']+selection['finalists']:
            child=child_job(job,engine.Controls(**row['controls']),row['job']['stage'],plan['protocol'])
            if child!=row['job']:raise ValueError('tuning row differs from frozen controls/protocol')
            summary=audit_child(root,point,base,child,references)
            if any(row.get(k)!=v for k,v in summary.items()):raise ValueError('selection/tuning ledger mismatch')
        for setting in selection['confirmations']:
            c=engine.Controls(**setting['controls']);child=child_job(job,c,'confirmation',plan['protocol'])
            directory=point/'confirmation'/child['id'];summary_path=directory/'summary.json'
            if not summary_path.exists():continue
            summary=audit_child(root,point,base,child,references)
            rows.append({**summary,'job':child,'point':job['id'],'budgets':setting['budgets'],
                         'directory':str(directory.relative_to(rt.REPO)),'summary_sha256':rt.sha(summary_path),
                         'selection_sha256':rt.sha(path)})
            checked+=1
        if checked==len(selection['confirmations']):finished.append(job['id'])
    if complete and len(finished)!=len(plan['jobs']):raise ValueError('incomplete search campaign')
    receipt={'schema':'canonical-css-search-verification-v1','plan_sha256':rt.sha(root/'plan.json'),
             'planned_strata':len(plan['jobs']),'finished_strata':finished,'points':rows,'tuning':tuning}
    with gzip.open(root/'verified.json.gz','wt',compresslevel=6) as stream:
        json.dump(receipt,stream,sort_keys=True,allow_nan=False)
    return receipt
