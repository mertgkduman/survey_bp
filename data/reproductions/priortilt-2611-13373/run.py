"""Frozen one-CPU-per-plotted-point Fig1 campaign with sealed paired samples."""
import argparse
from contextlib import contextmanager
from dataclasses import asdict
import fcntl
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
import numpy as np
import numba
import scipy
from scipy.stats import beta
import stim
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.memory_benchmark import audit_candidates,source_masks,validate_trace
from bp_registry.canonical.prior_tilt import PriorTiltDecoder,PriorTiltSpec,VERSION
from bp_registry.circuit.paper_decoders import CircuitPaperDecoder,PaperDecoderSpec

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
BATCH=8192;METHODS=('priortilt','relay','beam');BASES=('x','z')


def sha(path):
    h=sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(4*1024*1024):h.update(block)
    return h.hexdigest()


def identity(value):return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    tmp.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n');os.replace(tmp,path)


def write_npz(path,arrays):
    tmp=Path(path).with_name(Path(path).name+'.tmp-'+uuid.uuid4().hex)
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for name,array in arrays.items():
            with z.open(name+'.npy','w',force_zip64=True) as stream:np.lib.format.write_array(stream,np.asarray(array),allow_pickle=False)
    os.replace(tmp,path)


@contextmanager
def lock(path,nonblocking=False):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|(fcntl.LOCK_NB if nonblocking else 0));yield


def software():return {'python':platform.python_version(),'numpy':np.__version__,'numba':numba.__version__,'scipy':scipy.__version__,'stim':stim.__version__}


def design():
    source=json.loads((ROOT/'source.json').read_text());jobs=[]
    for code in ('BB144','BB70','GB102'):
        for p in sorted({x['p'] for x in source['circuits'] if x['code']==code}):
            bases={b:next(c for c in source['circuits'] if c['code']==code and c['p']==p and c['basis']==b) for b in BASES}
            for method in METHODS:jobs.append({'id':f'{code.lower()}-p{round(p*1e6):06d}-{method}','code':code,'p':p,'method':method,'bases':bases,'cycles':bases['x']['syndrome_rounds']})
    return {'schema':'priortilt-figure1-campaign-v1','study_id':'priortilt-2611-13373-figure1','paper_id':'priortilt-2611-13373-v1','jobs':jobs,
        'protocol':{'batch':BATCH,'target_errors':20,'max_shots':100_000_000,'noise_seed':2026111781,'policy_seed':2026111782,
            'sampling':'immutable shared detector/observable chunks per code/rate/basis; independent of decoder; cache producer CPU may differ, persisted bytes are authoritative',
            'stopping':'20 observable errors or 100M decoded shots, separately per memory basis; retain exact prefix; two bases run sequentially on one CPU',
            'metric':'(P_X observable error + P_Z observable error)/syndrome cycles; nonconvergence is separately recorded and is not automatically an observable failure',
            'uncertainty':'97.5% exact capped inverse-binomial/binomial intervals per basis; sum bounds / cycles gives Bonferroni simultaneous coverage at least95%',
            'numeric_profile':'existing canonical float64 min-sum total-minus-excluded-message order; paper hard-decision tie1; source prefix/suffix is separate reference',
            'minimum_free_bytes':10*1024**3,'execution_backend':VERSION}}


def freeze():
    q=json.loads((ROOT/'qualification.json').read_text())
    assert q['full_budget_pilot']['events']==624 and len(q['prior_native']['cases'])==72 and len(q['baseline_native']['cases'])==72
    d=design();paths=list(ROOT.glob('*.py'))+[ROOT/name for name in ('worker.sh','README.md','source.json','phase-schedules.json','source-contract.json','qualification.json','qualification-events.jsonl.gz','source-figure1.csv','SOURCE-LICENSE','priortilt-source.tar.gz','beam-source.tar.gz')]
    for rel in ['src/bp_registry/canonical/prior_tilt.py','src/bp_registry/circuit/paper_decoders.py','src/bp_registry/circuit/memory_benchmark.py',
                'src/bp_registry/canonical/compiled.py','src/bp_registry/check_numerics.py','src/bp_registry/canonical/schedules.py',
                'src/bp_registry/canonical/kernel.py','src/bp_registry/canonical/numerics.py','src/bp_registry/canonical/update_context.py',
                'src/bp_registry/compiled_contracts.py','src/bp_registry/circuit/dem.py','src/bp_registry/resolution.py']:
        paths.append(REPO/rel)
    paths+=list((ROOT/'circuits').glob('*.stim'))+list((ROOT/'source-data').glob('*.csv'))
    plan={**d,'software':software(),'implementation_sha256':{str(p.relative_to(REPO)):sha(p) for p in paths}}
    for name,value in [('design.json',d),('plan.json',plan)]:
        path=ROOT/name
        if path.exists():
            if json.loads(path.read_text())!=value:raise ValueError('refusing to alter frozen study '+name)
        else:write_json(path,value)
    return plan


def load():
    p=json.loads((ROOT/'plan.json').read_text())
    if p['schema']!='priortilt-figure1-campaign-v1' or p['software']!=software():raise ValueError('frozen schema/software differs')
    d=json.loads((ROOT/'design.json').read_text())
    if any(p.get(k)!=v for k,v in d.items()):raise ValueError('frozen design changed')
    for path,digest in p['implementation_sha256'].items():
        if sha(REPO/path)!=digest:raise ValueError('frozen source changed: '+path)
    return p


def seed(plan,job,basis,kind,index=0):
    value=[plan['protocol'][kind+'_seed'],job['code'],job['p'],basis,index]
    if kind=='policy':value.append(job['method'])
    return int(identity(value)[:15],16)


def case_model(job,basis):
    case=job['bases'][basis];c=stim.Circuit.from_file(str(ROOT/'circuits'/case['file']));return c,DemBinaryModel.from_dem(c.detector_error_model())


def spec_for(job):
    if job['method']=='priortilt':
        s=json.loads((ROOT/'phase-schedules.json').read_text())[job['code']][str(job['p'])]
        return PriorTiltSpec(ends=tuple(s['ends']),phases=tuple(tuple(v) for v in s['phases']))
    if job['method']=='beam':return PaperDecoderSpec(method='beam',initial=40,per_leg=30)
    g0,lo,hi=json.loads((ROOT/'source.json').read_text())['relay_gammas'][job['code']]
    return PaperDecoderSpec(method='relay',first_gamma=g0,gamma_low=lo,gamma_high=hi)


def prepared(plan,job,basis,model):
    spec=spec_for(job);s=seed(plan,job,basis,'policy')
    return PriorTiltDecoder(model.table,model.prior_llrs,spec,s) if job['method']=='priortilt' else CircuitPaperDecoder(model,spec,s)


def noise(plan,job,basis,index,circuit):
    directory=ROOT/'results/noise'/f'{job["code"]}-p{round(job["p"]*1e6):06d}-{basis}';directory.mkdir(parents=True,exist_ok=True)
    path=directory/f'{index:08d}.npz';meta=path.with_suffix('.json')
    expected={'circuit_sha256':job['bases'][basis]['sha256'],'seed':seed(plan,job,basis,'noise',index),
              'start':index*plan['protocol']['batch'],'max_shots':plan['protocol']['max_shots'],'software':plan['software']}
    with lock(directory/'noise.lock'):
        if meta.exists():
            value=json.loads(meta.read_text())
            if value['sampling']!=expected or value['sha256']!=sha(path):raise ValueError('sealed noise chunk changed')
        else:
            n=min(plan['protocol']['batch'],plan['protocol']['max_shots']-expected['start'])
            det,obs=circuit.compile_detector_sampler(seed=expected['seed']).sample(n,separate_observables=True,bit_packed=True)
            write_npz(path,{'detectors':det,'observables':obs});value={'sampling':expected,'sha256':sha(path),'shots':n}
            write_json(meta,value)
    with np.load(path,allow_pickle=False) as f:arrays={k:f[k] for k in f.files}
    return path,value,arrays


def verify_noise_binding(plan,job,basis,start,value):
    index=start//plan['protocol']['batch']
    expected_path=Path('results/noise')/f'{job["code"]}-p{round(job["p"]*1e6):06d}-{basis}'/f'{index:08d}.npz'
    if value['noise_path']!=str(expected_path) or value['noise_offset']!=start%plan['protocol']['batch']:raise ValueError('wrong sample identity')
    path=ROOT/expected_path;meta=json.loads(path.with_suffix('.json').read_text())
    expected={'circuit_sha256':job['bases'][basis]['sha256'],'seed':seed(plan,job,basis,'noise',index),
              'start':index*plan['protocol']['batch'],'max_shots':plan['protocol']['max_shots'],'software':plan['software']}
    if meta['sampling']!=expected or meta['sha256']!=value['noise_sha256'] or sha(path)!=meta['sha256']:raise ValueError('sample binding changed')
    return path


def interval(n,k,target,confidence=.975):
    tail=(1-confidence)/2
    low=0. if k==0 else float(beta.ppf(tail,k,n-k+1))
    if k==n:high=1.
    elif k==target:high=float(beta.ppf(1-tail,k,n-k))
    else:high=float(beta.ppf(1-tail,k+1,n-k))
    return [low,high]


def empty_summary():return {'shots':0,'errors':0,'iterations':0,'directed_edge_updates':0,'decode_ns':0,'nonconvergence':0,'random_draws':0,'biased_node_updates':0,'joint_counts':[0,0,0,0],'chunks':{}}


def chunk_summary(data,det,obs,model,dmasks,omasks,method,spec):
    n=len(data['candidate']);st=data['stats'];ptr=data['trace_ptr'];trace=data['trace']
    if st.dtype!=np.uint64 or st.shape!=(n,6) or ptr.dtype!=np.int64 or ptr.shape!=(n+1,) or ptr[0]!=0 or ptr[-1]!=len(trace) or np.any(np.diff(ptr)<0):raise ValueError('invalid event-ledger shapes')
    if not n or det.dtype!=np.uint8 or det.shape!=(n,(model.table.check_count+7)//8) or obs.dtype!=np.uint8 or obs.shape!=(n,omasks.shape[1]):raise ValueError('invalid source sample dimensions')
    if data['candidate'].dtype!=np.uint8 or data['candidate'].shape!=(n,(model.table.variable_count+7)//8) or data['prediction'].dtype!=np.uint8 or data['prediction'].shape!=obs.shape or data['decode_ns'].dtype!=np.uint64 or data['decode_ns'].shape!=(n,):raise ValueError('invalid candidate/observable event dimensions')
    counts=audit_candidates(data['candidate'],det,obs,data['prediction'],st,dmasks,omasks)
    for i in range(n):validate_trace(method,trace[ptr[i]:ptr[i+1]],st[i],model,spec)
    return {'shots':n,'errors':int(counts[1]),'iterations':int(st[:,0].sum()),'directed_edge_updates':int(st[:,1].sum()),
            'decode_ns':int(data['decode_ns'].sum()),'nonconvergence':int(n-st[:,2].sum()),'random_draws':int(st[:,3].sum()),
            'biased_node_updates':int(st[:,4].sum()),'joint_counts':counts[2:].tolist()}


def add(summary,row):
    for key in ('shots','errors','iterations','directed_edge_updates','decode_ns','nonconvergence','random_draws','biased_node_updates'):summary[key]+=row[key]
    summary['joint_counts']=[a+b for a,b in zip(summary['joint_counts'],row['joint_counts'])]


def finished(summary,plan):return summary['errors']>=plan['protocol']['target_errors'] or summary['shots']>=plan['protocol']['max_shots']


def terminal(summary,plan):
    p=plan['protocol'];n=summary['shots'];k=summary['errors']
    if not finished(summary,plan) or k>p['target_errors']:raise ValueError('not an exact terminal prefix')
    return {**summary,'rate':k/n,'ci975':interval(n,k,p['target_errors']),
            'stop_reason':'target_observable_errors' if k==p['target_errors'] else 'shot_cap'}


def read_chunks(plan,job,basis,model,circuit,replay=False):
    directory=ROOT/'results'/job['id']/basis;summary=empty_summary();spec=spec_for(job)
    dmasks,omasks=source_masks(circuit.detector_error_model());decoder=prepared(plan,job,basis,model) if replay else None
    for marker in sorted(directory.glob('chunk-*.json')):
        if finished(summary,plan):raise ValueError('chunks retained after stopping')
        value=json.loads(marker.read_text());path=marker.with_suffix('.npz')
        if value['start']!=summary['shots'] or value['plan_sha256']!=sha(ROOT/'plan.json') or value['sha256']!=sha(path):raise ValueError('chunk identity or contiguous prefix changed')
        noise_path=verify_noise_binding(plan,job,basis,summary['shots'],value)
        with np.load(noise_path,allow_pickle=False) as f:det=f['detectors'];obs=f['observables']
        with np.load(path,allow_pickle=False) as f:data={k:f[k] for k in f.files}
        n=len(data['candidate']);offset=value['noise_offset'];det=det[offset:offset+n];obs=obs[offset:offset+n]
        if n>plan['protocol']['batch']-offset or summary['shots']+n>plan['protocol']['max_shots']:raise ValueError('invalid retained prefix length')
        row=chunk_summary(data,det,obs,model,dmasks,omasks,job['method'],spec)
        if row!=value['summary']:raise ValueError('chunk counts/work changed')
        if replay:
            for i in sorted({0,n-1}):
                syn=np.unpackbits(det[i],bitorder='little',count=model.table.check_count).astype(np.uint8)
                r=decoder.decode(syn if job['method']!='priortilt' else syn^model.syndrome_bias,shot=summary['shots']+i)
                if not np.array_equal(np.packbits(r.candidate,bitorder='little'),data['candidate'][i]):raise ValueError('endpoint candidate replay failed')
                st=[r.iterations,r.directed_edge_updates,int(r.converged),r.random_draws,r.biased_node_updates,r.lineage]
                if not np.array_equal(np.asarray(st,np.uint64),data['stats'][i]) or not np.array_equal(r.trace,data['trace'][data['trace_ptr'][i]:data['trace_ptr'][i+1]]):raise ValueError('endpoint work/lineage replay failed')
        # The first target crossing must be the final retained event.
        if row['errors'] and summary['errors']+row['errors']>=plan['protocol']['target_errors']:
            if summary['errors']+row['errors']!=plan['protocol']['target_errors'] or not np.any(data['prediction'][-1]!=obs[-1]):raise ValueError('events retained after stopping')
        add(summary,row);summary['chunks'][marker.name]=sha(marker)
    return summary


def execute(index,audit=False):
    plan=load();job=plan['jobs'][index];directory=ROOT/'results'/job['id'];directory.mkdir(parents=True,exist_ok=True)
    with lock(directory/'run.lock',True):
        if not (directory/'hardware.json').exists():
            write_json(directory/'hardware.json',{'host':platform.node(),'machine':platform.machine(),'cpu_affinity':sorted(os.sched_getaffinity(0)),
                'numba_threads':numba.get_num_threads(),'slurm_cpus_per_task':os.environ.get('SLURM_CPUS_PER_TASK'),
                'thread_limits':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS')}})
        manifest={'plan_sha256':sha(ROOT/'plan.json'),'job':job,'resolved_policy':json.loads(json.dumps(asdict(spec_for(job))))}
        path=directory/'manifest.json'
        if path.exists():
            if json.loads(path.read_text())!=manifest:raise ValueError('point manifest changed')
        else:write_json(path,manifest)
        states={}
        for basis in BASES:
            c,m=case_model(job,basis);summary=read_chunks(plan,job,basis,m,c,replay=audit)
            states[basis]=(c,m,summary,prepared(plan,job,basis,m),source_masks(c.detector_error_model()))
        if audit:
            summaries={b:terminal(states[b][2],plan) for b in BASES}
            receipt={'plan_sha256':manifest['plan_sha256'],'job':job,'resolved_policy':manifest['resolved_policy'],'bases':summaries,'manifest_sha256':sha(path)}
            if json.loads((directory/'complete.json').read_text())!=receipt:raise ValueError('complete receipt differs from full audit')
            write_json(directory/'audit.json',receipt);print('Audited',job['id'],flush=True);return
        for c,m,s,decoder,masks in states.values():decoder.decode(np.zeros(m.table.check_count,np.uint8),shot=0)
        while any(not finished(v[2],plan) for v in states.values()):
            for basis,(c,m,summary,decoder,masks) in states.items():
                if finished(summary,plan):continue
                if shutil.disk_usage(ROOT).free<plan['protocol']['minimum_free_bytes']:raise RuntimeError('storage checkpoint: less than 10GiB free; retained prefix is resumable')
                start=summary['shots'];index_noise=start//plan['protocol']['batch'];offset=start%plan['protocol']['batch']
                noise_path,noise_meta,raw=noise(plan,job,basis,index_noise,c)
                det=np.unpackbits(raw['detectors'][offset:],axis=1,bitorder='little',count=m.table.check_count).astype(np.uint8)
                obs=raw['observables'][offset:];nmax=len(det);fault=np.empty((nmax,(m.table.variable_count+7)//8),np.uint8)
                pred=np.empty_like(obs);stats=np.empty((nmax,6),np.uint64);times=np.empty(nmax,np.uint64);ptr=[0];traces=[];errors=0;n=0
                for i,syn in enumerate(det):
                    t=time.perf_counter_ns();r=decoder.decode(syn if job['method']!='priortilt' else syn^m.syndrome_bias,shot=start+i);times[i]=time.perf_counter_ns()-t
                    fault[i]=np.packbits(r.candidate,bitorder='little');pred[i]=np.packbits(m.observable_matrix@r.candidate%2^m.observable_bias,bitorder='little')
                    stats[i]=[r.iterations,r.directed_edge_updates,int(r.converged),r.random_draws,r.biased_node_updates,r.lineage]
                    traces.append(r.trace);ptr.append(ptr[-1]+len(r.trace));n=i+1;errors+=int(np.any(pred[i]!=obs[i]))
                    if summary['errors']+errors==plan['protocol']['target_errors']:break
                data={'candidate':fault[:n],'prediction':pred[:n],'stats':stats[:n],'decode_ns':times[:n],
                      'trace_ptr':np.asarray(ptr,np.int64),'trace':np.concatenate(traces) if ptr[-1] else np.empty((0,8),np.int64)}
                row=chunk_summary(data,raw['detectors'][offset:offset+n],obs[:n],m,*masks,job['method'],spec_for(job))
                folder=directory/basis;folder.mkdir(exist_ok=True);marker=folder/f'chunk-{len(summary["chunks"]):08d}.json';npz=marker.with_suffix('.npz')
                write_npz(npz,data)
                meta={'start':start,'plan_sha256':manifest['plan_sha256'],'sha256':sha(npz),'noise_path':str(noise_path.relative_to(ROOT)),
                      'noise_sha256':noise_meta['sha256'],'noise_offset':offset,'summary':row}
                write_json(marker,meta);add(summary,row);summary['chunks'][marker.name]=sha(marker)
                write_json(directory/'progress.json',{'job':job['id'],'bases':{b:{k:v for k,v in x[2].items() if k!='chunks'} for b,x in states.items()}})
                print(job['id'],basis,summary['shots'],summary['errors'],flush=True)
        receipt={'plan_sha256':manifest['plan_sha256'],'job':job,'resolved_policy':manifest['resolved_policy'],
                 'bases':{b:terminal(x[2],plan) for b,x in states.items()},'manifest_sha256':sha(path)}
        write_json(directory/'complete.json',receipt)


def submit():
    with lock(ROOT/'dispatch.lock',True):
        plan=load();(ROOT/'results').mkdir(exist_ok=True);path=ROOT/'dispatch.json';record=json.loads(path.read_text()) if path.exists() else {}
        base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1','--cpus-per-task=1','--mem=3G','--time=4-00:00:00','--requeue',f'--chdir={REPO}',
              f'--export=ALL,PYTHONPATH={REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1,NUMBA_NUM_THREADS=1']
        if 'array' not in record:
            argv=base+['--job-name=priortilt-fig1','--array=0-38%39','--signal=B:USR1@180',f'--output={ROOT}/results/point-%A_%a.log',str(ROOT/'worker.sh')]
            jid=subprocess.check_output(argv,text=True).strip().split(';')[0];assert jid.isdigit()
            record['array']={'id':jid,'argv':argv,'plan_sha256':sha(ROOT/'plan.json')};write_json(path,record)
        if 'collector' not in record:
            argv=base+['--mem=12G','--job-name=priortilt-collect','--dependency=afterok:'+record['array']['id'],f'--output={ROOT}/results/collect-%j.log',
                       '--wrap='+f'exec {sys.executable} {ROOT}/run.py --collect']
            jid=subprocess.check_output(argv,text=True).strip().split(';')[0];assert jid.isdigit()
            record['collector']={'id':jid,'argv':argv,'plan_sha256':sha(ROOT/'plan.json')};write_json(path,record)
        print(json.dumps({k:v['id'] for k,v in record.items()}),flush=True)


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--index',type=int);g.add_argument('--freeze',action='store_true');g.add_argument('--submit',action='store_true');g.add_argument('--collect',action='store_true')
    p.add_argument('--audit',action='store_true');a=p.parse_args()
    if a.freeze:freeze()
    elif a.submit:submit()
    elif a.collect:
        import report;report.collect()
    else:execute(a.index,a.audit)


if __name__=='__main__':main()
