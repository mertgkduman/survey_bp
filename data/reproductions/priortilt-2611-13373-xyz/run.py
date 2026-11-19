"""Frozen 50-CPU XYZ Table4 campaign with joint DEMs and paired memories."""
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
from bp_registry.circuit.relay_list import CircuitRelayListDecoder,RelayListSpec,validate_relay_list_trace
from bp_registry.canonical.prior_tilt import PriorTiltDecoder,PriorTiltSpec,VERSION
from bp_registry.circuit.paper_decoders import CircuitPaperDecoder,PaperDecoderSpec

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
BATCH=64;METHODS=('priortilt','relay5');BASES=('x','z')


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
    source=json.loads((ROOT/'source.json').read_text())
    bases={c['basis']:c for c in source['circuits']}
    jobs=[{'id':'bb144-p003000-xyz-'+m,'code':'BB144','p':.003,'method':m,'cycles':12,'bases':bases} for m in METHODS]
    return {'schema':'priortilt-xyz-table4-campaign-v1','study_id':'priortilt-2611-13373-xyz-table4','jobs':jobs,
        'protocol':{'batch':BATCH,'target_errors':20,'max_shots':100_000_000,'noise_seed':2026111881,'policy_seed':2026111882,
        'metric':'(X-memory observable error rate + Z-memory observable error rate)/12; nonconvergence recorded separately',
        'decoding':'full undecomposed joint X/Z detector DEM for each memory experiment; no split into detector sectors',
        'stopping':'20 observable errors or100M shots per memory basis, exact ordered prefix',
        'resources':'50 process workers per paired decoder/code/rate point, shared across X/Z memories',
        'sampling':'sealed shared Stim detector/observable bytes per code/rate/basis; persisted bytes authoritative across SIMD producers',
        'uncertainty':'97.5% exact capped component intervals summed/cycles; at least95% pointwise X/Z coverage',
        'numeric_profile':'canonical float64 total-minus min-sum, alpha1 offset0, hard tie1; native arithmetic/RNG separate',
        'minimum_free_bytes':20*1024**3}}


def freeze():
    qualification=json.loads((ROOT/'qualification.json').read_text())
    if not qualification['passed']:raise ValueError('XYZ source/controller/process qualification required')
    d=design()
    paths=list(ROOT.glob('*.py'))+list(ROOT.glob('*.sh'))+list(ROOT.glob('*.csv'))+[ROOT/n for n in ('source.json','source-contract.json','qualification.json','README.md','SOURCE-LICENSE','reference-manifest.json','reference-qualification.tar.gz')]+list((ROOT/'circuits').glob('*.stim'))+list((ROOT/'source-data').glob('*.csv'))
    parent=json.loads((REPO/'data/reproductions/priortilt-2611-13373/plan.json').read_text())
    files={p:sha(REPO/p) for p in parent['implementation_sha256']}
    files.update({str(p.relative_to(REPO)):sha(p) for p in paths})
    for rel in ('src/bp_registry/circuit/relay_list.py','tests/test_circuit_relay_list.py','tests/test_prior_tilt_xyz_campaign.py'):
        files[rel]=sha(REPO/rel)
    plan={**d,'software':software(),'implementation_sha256':files,'qualification_sha256':sha(ROOT/'qualification.json')}
    for name,value in (('design.json',d),('plan.json',plan)):
        path=ROOT/name
        if path.exists():
            if json.loads(path.read_text())!=value:raise ValueError('refusing frozen XYZ change: '+name)
        else:write_json(path,value)
    resource={'schema':'priortilt-xyz-resources-v1','controller':'xyz-ordered-processes-v1','workers':50,'cpus_per_point':50,
        'authorization':'User: Reproduce XYZ results as well, using50 processors per data point.',
        'parent_plan_sha256':sha(ROOT/'plan.json'),'implementation_sha256':files,
        'ordering':'ordered sealed stages, exact stopping prefix, all speculative work separately retained and audited'}
    path=ROOT/'resource-amendment.json'
    if path.exists():
        if json.loads(path.read_text())!=resource:raise ValueError('resource identity changed')
    else:write_json(path,resource)
    return plan


def load():
    p=json.loads((ROOT/'plan.json').read_text());d=json.loads((ROOT/'design.json').read_text())
    if p['schema']!='priortilt-xyz-table4-campaign-v1' or p['software']!=software() or any(p.get(k)!=v for k,v in d.items()):raise ValueError('XYZ plan/software changed')
    for name,digest in p['implementation_sha256'].items():
        if sha(REPO/name)!=digest:raise ValueError('frozen source changed: '+name)
    return p


def seed(plan,job,basis,kind,index=0):
    value=[plan['protocol'][kind+'_seed'],job['code'],job['p'],basis,index]
    if kind=='policy':value.append(job['method'])
    return int(identity(value)[:15],16)


def case_model(job,basis):
    case=job['bases'][basis];c=stim.Circuit.from_file(str(ROOT/'circuits'/case['file']));return c,DemBinaryModel.from_dem(c.detector_error_model())


def spec_for(job):
    source=json.loads((ROOT/'source.json').read_text())
    return PriorTiltSpec(**source['prior_schedule']) if job['method']=='priortilt' else RelayListSpec(**source['relay_spec'])


def prepared(plan,job,basis,model):
    spec=spec_for(job);value=seed(plan,job,basis,'policy')
    return PriorTiltDecoder(model.table,model.prior_llrs,spec,value) if job['method']=='priortilt' else CircuitRelayListDecoder(model,spec,value)


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
    for i in range(n):
        if method=='relay5':validate_relay_list_trace(trace[ptr[i]:ptr[i+1]],st[i],model,spec,np.unpackbits(data['candidate'][i],bitorder='little',count=model.table.variable_count))
        else:validate_trace(method,trace[ptr[i]:ptr[i+1]],st[i],model,spec)
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
    plan=load()
    if 'implementation_sha256' in plan:raise ValueError('frozen XYZ production must use the50-process worker')
    job=plan['jobs'][index];directory=ROOT/'results'/job['id'];directory.mkdir(parents=True,exist_ok=True)
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


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--index',type=int);p.add_argument('--audit',action='store_true');args=p.parse_args()
    if args.freeze:freeze()
    elif args.index is not None:execute(args.index,args.audit)
    else:p.error('freeze or index required')
