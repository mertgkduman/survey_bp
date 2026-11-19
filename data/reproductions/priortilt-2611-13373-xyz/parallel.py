"""Ordered50-process execution for the separately qualified XYZ campaign."""
import argparse
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from dataclasses import asdict
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import shutil
import time
import numpy as np
import run

VERSION='xyz-ordered-processes-v1'
STATE={}


def initialize(plan,job,expected_models,root):
    global STATE
    run.ROOT=Path(root)
    STATE={'plan':plan,'job':job,'models':{}}
    for basis in run.BASES:
        c,m=run.case_model(job,basis)
        if expected_models[basis]!=m.execution_sha256:raise ValueError('child resolved model bytes differ')
        decoder=run.prepared(plan,job,basis,m)
        decoder.decode(np.zeros(m.table.check_count,np.uint8),shot=0)
        STATE['models'][basis]=(c,m,decoder,run.source_masks(c.detector_error_model()))
    run.write_json(run.ROOT/'results'/job['id']/'processes'/f'{os.getpid()}.json',{'pid':os.getpid(),'host':platform.node(),'affinity':sorted(os.sched_getaffinity(0)),'models':expected_models})


def arrays(path):
    with np.load(path,allow_pickle=False) as f:return {k:f[k] for k in f.files}


def checked_unit(basis,marker,replay=True):
    plan,job=STATE['plan'],STATE['job'];c,m,decoder,masks=STATE['models'][basis]
    marker=Path(marker);meta=json.loads(marker.read_text());path=marker.with_suffix('.npz')
    if meta['plan_sha256']!=run.sha(run.ROOT/'plan.json') or run.sha(path)!=meta['sha256']:raise ValueError('event binding changed')
    noise_path=run.verify_noise_binding(plan,job,basis,meta['start'],meta);raw=arrays(noise_path);data=arrays(path)
    n=len(data['candidate']);off=meta['noise_offset'];det=raw['detectors'][off:off+n];obs=raw['observables'][off:off+n]
    if n>plan['protocol']['batch']-off or meta['start']+n>plan['protocol']['max_shots']:raise ValueError('invalid sample extent')
    row=run.chunk_summary(data,det,obs,m,*masks,job['method'],run.spec_for(job))
    if row!=meta['summary']:raise ValueError('event summary changed')
    if replay:
        for i in sorted({0,n-1}):
            syn=np.unpackbits(det[i],bitorder='little',count=m.table.check_count)
            r=decoder.decode(syn if job['method']!='priortilt' else syn^m.syndrome_bias,shot=int(meta['start']+i))
            st=np.asarray([r.iterations,r.directed_edge_updates,int(r.converged),r.random_draws,r.biased_node_updates,r.lineage],np.uint64)
            if not np.array_equal(np.packbits(r.candidate,bitorder='little'),data['candidate'][i]) or not np.array_equal(st,data['stats'][i]):raise ValueError('endpoint candidate/work replay changed')
            if not np.array_equal(r.trace,data['trace'][data['trace_ptr'][i]:data['trace_ptr'][i+1]]):raise ValueError('endpoint lineage replay changed')
    return {'basis':basis,'marker':str(marker),'marker_sha256':run.sha(marker),'meta':meta,'last_bad':bool(np.any(data['prediction'][-1]!=obs[-1]))}


def audit_task(task):return checked_unit(*task)


def scan(pool,plan,job):
    summaries={b:run.empty_summary() for b in run.BASES};directory=run.ROOT/'results'/job['id']
    tasks=[(b,str(p)) for b in run.BASES for p in sorted((directory/b).glob('chunk-*.json'))]
    for r in pool.map(audit_task,tasks,chunksize=1):
        s=summaries[r['basis']];v=r['meta'];row=v['summary']
        if run.finished(s,plan) or v['start']!=s['shots']:raise ValueError('noncontiguous or post-stop prefix')
        if s['errors']+row['errors']>=plan['protocol']['target_errors']:
            if s['errors']+row['errors']!=plan['protocol']['target_errors'] or not r['last_bad']:raise ValueError('invalid error target prefix')
        run.add(s,row);s['chunks'][Path(r['marker']).name]=r['marker_sha256']
    return summaries


def unit(basis,start):
    plan,job=STATE['plan'],STATE['job'];c,m,decoder,masks=STATE['models'][basis]
    folder=run.ROOT/'results'/job['id']/'parallel-stages'/VERSION;folder.mkdir(parents=True,exist_ok=True)
    marker=folder/f'{basis}-{start:012d}.json';path=marker.with_suffix('.npz')
    if marker.exists():
        r=checked_unit(basis,marker)
        if r['meta'].get('controller')!=VERSION:raise ValueError('stage controller differs')
        return basis,start,str(marker)
    if shutil.disk_usage(run.ROOT).free<plan['protocol']['minimum_free_bytes']:raise RuntimeError('storage checkpoint: less than 10GiB free')
    rawpath,noisemeta,raw=run.noise(plan,job,basis,start//plan['protocol']['batch'],c)
    off=start%plan['protocol']['batch'];det=np.unpackbits(raw['detectors'][off:],axis=1,bitorder='little',count=m.table.check_count)
    obs=raw['observables'][off:];nmax=len(det);candidate=np.empty((nmax,(m.table.variable_count+7)//8),np.uint8)
    pred=np.empty_like(obs);stats=np.empty((nmax,6),np.uint64);ns=np.empty(nmax,np.uint64);ptr=[0];traces=[];errors=0
    for i,syn in enumerate(det):
        begin=time.perf_counter_ns();r=decoder.decode(syn if job['method']!='priortilt' else syn^m.syndrome_bias,shot=int(start+i));ns[i]=time.perf_counter_ns()-begin
        candidate[i]=np.packbits(r.candidate,bitorder='little');pred[i]=np.packbits(m.observable_matrix@r.candidate%2^m.observable_bias,bitorder='little')
        stats[i]=[r.iterations,r.directed_edge_updates,int(r.converged),r.random_draws,r.biased_node_updates,r.lineage]
        traces.append(r.trace);ptr.append(ptr[-1]+len(r.trace));errors+=int(np.any(pred[i]!=obs[i]));n=i+1
        if errors==plan['protocol']['target_errors']:break
    data={'candidate':candidate[:n],'prediction':pred[:n],'stats':stats[:n],'decode_ns':ns[:n],
          'trace_ptr':np.asarray(ptr,np.int64),'trace':np.concatenate(traces) if ptr[-1] else np.empty((0,8),np.int64)}
    row=run.chunk_summary(data,raw['detectors'][off:off+n],obs[:n],m,*masks,job['method'],run.spec_for(job))
    run.write_npz(path,data)
    meta={'start':start,'plan_sha256':run.sha(run.ROOT/'plan.json'),'sha256':run.sha(path),'noise_path':str(rawpath.relative_to(run.ROOT)),
          'noise_sha256':noisemeta['sha256'],'noise_offset':off,'summary':row,'controller':VERSION,
          'worker':{'host':platform.node(),'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0))}}
    run.write_json(marker,meta);return basis,start,str(marker)


def retained_length(prediction,observables,remaining):
    bad=np.flatnonzero(np.any(prediction!=observables,axis=1))
    return int(bad[remaining-1])+1 if len(bad)>=remaining else len(prediction)


def prefix(data,n):
    return {k:(v[:n+1] if k=='trace_ptr' else v[:int(data['trace_ptr'][n])] if k=='trace' else v[:n]) for k,v in data.items()}


def commit(plan,job,basis,stage,summary,models,amendment):
    meta=json.loads(Path(stage).read_text());data=arrays(Path(stage).with_suffix('.npz'))
    if meta['start']!=summary['shots'] or meta['sha256']!=run.sha(Path(stage).with_suffix('.npz')):raise ValueError('stage start/binding changed')
    raw=arrays(run.verify_noise_binding(plan,job,basis,meta['start'],meta));off=meta['noise_offset']
    n=retained_length(data['prediction'],raw['observables'][off:off+len(data['prediction'])],plan['protocol']['target_errors']-summary['errors'])
    whole=n==len(data['candidate']);data=prefix(data,n)
    if whole:row=meta['summary']
    else:
        c,m=models[basis];row=run.chunk_summary(data,raw['detectors'][off:off+n],raw['observables'][off:off+n],m,*run.source_masks(c.detector_error_model()),job['method'],run.spec_for(job))
    folder=run.ROOT/'results'/job['id']/basis;folder.mkdir(exist_ok=True);marker=folder/f'chunk-{len(summary["chunks"]):08d}.json';path=marker.with_suffix('.npz')
    if whole:
        tmp=path.with_name(path.name+'.link-'+str(os.getpid()))
        if tmp.exists():tmp.unlink()
        os.link(Path(stage).with_suffix('.npz'),tmp);os.replace(tmp,path)
    else:run.write_npz(path,data)
    out={**{k:meta[k] for k in ('start','plan_sha256','noise_path','noise_sha256','noise_offset')},'sha256':run.sha(path),'summary':row,
         'parallel_execution':{'controller':VERSION,'resource_amendment_sha256':amendment,'stage':str(Path(stage).relative_to(run.ROOT))}}
    run.write_json(marker,out);run.add(summary,row);summary['chunks'][marker.name]=run.sha(marker)


def advance(start,plan):return min(plan['protocol']['max_shots'],(start//plan['protocol']['batch']+1)*plan['protocol']['batch'])


def continue_point(pool,plan,job,summaries,models,amendment,workers):
    cursor={b:s['shots'] for b,s in summaries.items()};pending={};ready={b:{} for b in run.BASES};turn=0
    while True:
        while len(pending)+sum(len(x) for x in ready.values())<workers:
            choices=[b for b in run.BASES if not run.finished(summaries[b],plan) and cursor[b]<plan['protocol']['max_shots']]
            if not choices:break
            basis=choices[turn%len(choices)];turn+=1;start=cursor[basis];cursor[basis]=advance(start,plan)
            pending[pool.submit(unit,basis,start)]=(basis,start)
        if not pending:break
        done,_=wait(pending,return_when=FIRST_COMPLETED)
        for f in done:
            basis,start,stage=f.result();pending.pop(f)
            if not run.finished(summaries[basis],plan):ready[basis][start]=stage
        for basis,s in summaries.items():
            while not run.finished(s,plan) and s['shots'] in ready[basis]:
                stage=ready[basis].pop(s['shots']);commit(plan,job,basis,stage,s,models,amendment)
                print(job['id'],basis,s['shots'],s['errors'],flush=True)
                run.write_json(run.ROOT/'results'/job['id']/'progress.json',{'job':job['id'],'bases':{b:{k:v for k,v in v.items() if k!='chunks'} for b,v in summaries.items()}})
            if run.finished(s,plan):ready[basis].clear()
    if not all(run.finished(s,plan) for s in summaries.values()):raise ValueError('parallel continuation ended before stopping')


def expenditure(plan,job,summaries):
    folder=run.ROOT/'results'/job['id'];computed=run.empty_summary();retained=run.empty_summary();stages={}
    for p in (folder/'parallel-stages'/VERSION).glob('*.json'):
        m=json.loads(p.read_text())
        if run.sha(p.with_suffix('.npz'))!=m['sha256']:raise ValueError('speculative stage binding changed')
        run.add(computed,m['summary']);stages[p.name]=run.sha(p)
    for basis,s in summaries.items():
        for name in s['chunks']:
            m=json.loads((folder/basis/name).read_text())
            if 'parallel_execution' in m:run.add(retained,m['summary'])
    keys=('shots','errors','iterations','directed_edge_updates','decode_ns','nonconvergence','random_draws','biased_node_updates')
    return {'computed':{k:computed[k] for k in keys},'retained':{k:retained[k] for k in keys},
            'speculative':{k:computed[k]-retained[k] for k in keys},'stages':stages,
            'scope':'sealed unique stages only; interruptions before a sealed stage have unmeasured work; speculative outcomes never enter LER or retained-shot work means'}


def execute(index,workers=50,audit=False):
    plan=run.load()
    if workers!=50 or ('implementation_sha256' in plan and os.environ.get('SLURM_CPUS_PER_TASK')!='50'):
        raise ValueError('frozen XYZ production requires50 workers and50 Slurm CPUs')
    job=plan['jobs'][index];root=run.ROOT/'results'/job['id'];root.mkdir(parents=True,exist_ok=True)
    amendment=run.sha(run.ROOT/'resource-amendment.json')
    with run.lock(root/'run.lock',True):
        manifest={'plan_sha256':run.sha(run.ROOT/'plan.json'),'job':job,'resolved_policy':json.loads(json.dumps(asdict(run.spec_for(job))))}
        path=root/'manifest.json'
        if path.exists():
            if json.loads(path.read_text())!=manifest:raise ValueError('original manifest changed')
        else:run.write_json(path,manifest)
        models={b:run.case_model(job,b) for b in run.BASES};expected={b:m.execution_sha256 for b,(c,m) in models.items()}
        # Warm disk caches once before spawned workers load the same functions.
        for b,(c,m) in models.items():run.prepared(plan,job,b,m).decode(np.zeros(m.table.check_count,np.uint8),shot=0)
        with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn'),initializer=initialize,initargs=(plan,job,expected,str(run.ROOT))) as pool:
            summaries=scan(pool,plan,job)
            if not audit:
                inherited=root/'inherited-prefix.json'
                if not inherited.exists():run.write_json(inherited,{'plan_sha256':manifest['plan_sha256'],'resource_amendment_sha256':amendment,'bases':summaries})
                run.write_json(root/'parallel-hardware.json',{'host':platform.node(),'cpus':workers,'slurm_cpus_per_task':os.environ.get('SLURM_CPUS_PER_TASK'),
                    'affinity':sorted(os.sched_getaffinity(0)),'controller':VERSION,'resource_amendment_sha256':amendment,
                    'timing_scope':'concurrent XYZ50-process instrumented cohort; no standalone single-core runtime claim'})
                continue_point(pool,plan,job,summaries,models,amendment,workers)
                run.write_json(root/'parallel-work.json',expenditure(plan,job,summaries))
            else:
                # Audit all sealed speculative work as well as canonical rows.
                tasks=[(p.name[0],str(p)) for p in sorted((root/'parallel-stages'/VERSION).glob('*.json'))]
                for _ in pool.map(audit_task,tasks,chunksize=1):pass
        receipt={**manifest,'bases':{b:run.terminal(s,plan) for b,s in summaries.items()},'manifest_sha256':run.sha(path)}
        if audit:
            if json.loads((root/'complete.json').read_text())!=receipt:raise ValueError('complete receipt differs from parallel full audit')
            if json.loads((root/'parallel-work.json').read_text())!=expenditure(plan,job,summaries):raise ValueError('speculative work changed')
            run.write_json(root/'audit.json',receipt);print('Audited',job['id'],flush=True)
        else:run.write_json(root/'complete.json',receipt)


def load_amendment():
    a=json.loads((run.ROOT/'resource-amendment.json').read_text())
    if a['parent_plan_sha256']!=run.sha(run.ROOT/'plan.json') or a['controller']!=VERSION or a['workers']!=50:raise ValueError('resource amendment changed')
    for p,h in a['implementation_sha256'].items():
        if run.sha(run.REPO/p)!=h:raise ValueError('parallel source changed: '+p)
    return a


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',type=int,required=True);p.add_argument('--audit',action='store_true');a=p.parse_args()
    load_amendment();execute(a.index,50,a.audit)
