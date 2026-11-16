"""Prospective80+60 Relay gamma sweep with phase ablations, one CPU per point."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import fcntl
from functools import lru_cache
import gzip
from hashlib import sha256
import importlib.util
import itertools
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.with_name('panteleev-2012-04068-lifted-product')


def module(name,path):
    if name in sys.modules:return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m


engine = module('_lp1054_gamma_engine',ROOT/'engine.py')
# An isolated module instance supplies the qualified event/evaluation helpers.
# No parent file or original module instance is modified.
r = module('_lp1054_gamma_event_protocol',PARENT/'run.py')
rt = r.rt
SEEDS = {'coarse':2026111661,'finalist':2026111662,'refine':2026111663,'confirmation':2026111664}
MEMORY_SEEDS = {'coarse':2026111671,'finalist':2026111672,'refine':2026111673,'confirmation':2026111674}
CHUNK = 1024
GAMMAS = (-.5,-.25,0.,.125,.25,.35,.5,.625,.75,.875,1.)
WINDOWS = sorted(set([(round(center-half,6),round(center+half,6))
    for center,half in itertools.product((-.25,0.,.25,.5,.75),(.125,.25,.5))
    if -.75<=center-half<center+half<=1.]+[(-.24,.66),(-.161,.815),(-.254,.985),(-.5,1.)]))
BACKGROUNDS = ('source_numerics','prior_tuned_numerics')
ROLES = ('gamma_selected','uniform_phase_only','disordered_phase_only','reset_zero_gamma','continuous_bp140')


@lru_cache(maxsize=1)
def code():
    source=json.loads((PARENT/'source.json').read_text())
    return r.load_artifact(rt.REPO,(PARENT/'code.npz').relative_to(rt.REPO),
        expected_semantic_sha256=source['semantic_sha256']).code


r.ROOT=ROOT;r.SEEDS=SEEDS;r.engine=engine;r.code=code
identity=r.identity


def parent_training():
    plan=rt.load(PARENT);rows=[]
    for p in plan['source']['rates']:
        job=next(j for j in plan['jobs'] if j['arm']=='tuned_bp' and j['physical_p']==p)
        path=PARENT/'results'/job['id']/'selection.json';selection=json.loads(path.read_text())
        assert selection['plan_sha256']==rt.sha(PARENT/'plan.json') and selection['job']==job
        for stage in ('coarse','finalists'):
            for row in selection[stage]:
                prefix='coarse' if stage=='coarse' else 'finalist'
                summary=PARENT/'results'/job['id']/prefix/identity(row['controls'])[:24]/'summary.json'
                assert rt.sha(summary)==row['summary_sha256']
        c=selection['chosen']
        rows.append({'physical_p':p,'numeric_controls':{k:c[k] for k in ('damping','alpha','beta')},
                     'selection_path':str(path.relative_to(rt.REPO)),'selection_sha256':rt.sha(path)})
    return rows


def design():
    parent=rt.load(PARENT);training=parent_training()
    jobs=[]
    for p,bg in itertools.product(parent['source']['rates'],BACKGROUNDS):
        numeric=({'damping':0.,'alpha':.625,'beta':0.} if bg=='source_numerics' else
                 next(t['numeric_controls'] for t in training if t['physical_p']==p))
        jobs.append({'id':f'{bg}-p{round(p*10000):04d}','arm':bg,'background':bg,
                     'physical_p':p,'numeric_controls':numeric})
    return {'study_id':'lp1054-relay-gamma80-60','paper_id':parent['paper_id'],
        'label':'LP1054 RelayBP: tuned uniform80 and disordered60 gamma',
        'codes':parent['codes'],'parent_plan_sha256':rt.sha(PARENT/'plan.json'),
        'parent_training':training,'source':parent['source'],'jobs':jobs,
        'protocol':{'seeds':SEEDS,'memory_seeds':MEMORY_SEEDS,'chunk_size':CHUNK,
            'coarse_shots':1024,'finalist_shots':32768,'finalist_failures':40,
            'refine_shots':131072,'refine_failures':60,'max_shots':100_000_000,'target_failures':20,
            'first_gamma_grid':list(GAMMAS),'disorder_windows':[list(w) for w in WINDOWS],
            'roles':list(ROLES),'uniform_iterations':80,'disordered_iterations':60,'additional_legs':1,
            'selection':'minimum refinement-cohort block LER among genuine disorder settings; ties mean total sweeps, decode ns, control hash',
            'early_stop':'S=1; original-syndrome convergence ends each leg and skips the second leg if the first succeeds',
            'finalists':'top4 genuine-disorder controls plus best in each first-gamma band(negative/zero,small,medium,large), plus reset-zero control',
            'refinement':'all finalists plus coordinate neighbors of best genuine-disorder finalist on a new independent refinement cohort'},
        'claim_limit':'User-confirmed one80-sweep uniform-memory leg plus one60-sweep disordered-memory leg,140 maximum per CSS component. Code-capacity adaptation of Relay Eq4, not circuit-paper reproduction. Both logical components count. Numerical backgrounds are fixed source NMS or parent training-only selected BP settings; no parent fresh outcome enters selection. Independent noise/memory streams and four disjoint stage seeds. All selected and ablation confirmations remain separate. This140 budget differs from prior32/128 studies. New latency excludes provenance hashing and is not directly comparable to older instrumented timings.'}


def base_controls(job):
    return {'family':'bp','cap':140,**job['numeric_controls']}


def relay(job,gamma,low,high):
    c=base_controls(job)
    sc=engine.GammaControls(first_gamma=float(gamma),gamma_low=float(low),gamma_high=float(high),**job['numeric_controls'])
    return {**c,'search':asdict(sc)}


def proposals(job):
    return [relay(job,g,lo,hi) for g,(lo,hi) in itertools.product(GAMMAS,WINDOWS)]+[relay(job,0,0,0)]


def genuine(c):return c['search']['gamma_low']<c['search']['gamma_high']


def finalists(rows,job):
    chosen={}
    def add(row):chosen.setdefault(identity(row['controls']),row['controls'])
    eligible=[row for row in rows if genuine(row['controls'])]
    for row in sorted(eligible,key=r.rank)[:4]:add(row)
    bands=[lambda g:g<=0,lambda g:0<g<=.35,lambda g:.35<g<=.625,lambda g:g>.625]
    for band in bands:
        group=[row for row in eligible if band(row['controls']['search']['first_gamma'])]
        if group:add(min(group,key=r.rank))
    chosen.setdefault(identity(relay(job,0,0,0)),relay(job,0,0,0))
    return list(chosen.values())


def refinement(rows):
    best=min((row for row in rows if genuine(row['controls'])),key=r.rank)['controls']
    result={identity(row['controls']):row['controls'] for row in rows}
    for field,step in (('first_gamma',.0625),('gamma_low',.125),('gamma_high',.125)):
        for sign in (-1,1):
            sc={**best['search'],field:round(best['search'][field]+sign*step,6)}
            try:engine.GammaControls(**sc)
            except ValueError:continue
            c={**best,'search':sc}
            if genuine(c):result.setdefault(identity(c),c)
    return list(result.values())


def confirmations(job,chosen):
    s=chosen['search'];pairs=[('gamma_selected',chosen),
        ('uniform_phase_only',relay(job,s['first_gamma'],0,0)),
        ('disordered_phase_only',relay(job,0,s['gamma_low'],s['gamma_high'])),
        ('reset_zero_gamma',relay(job,0,0,0)),('continuous_bp140',base_controls(job))]
    values={}
    for role,c in pairs:values.setdefault(identity(c),{'controls':c,'roles':[]})['roles'].append(role)
    return list(values.values())


def memory_seed(job,stage):return MEMORY_SEEDS[stage]+round(job['physical_p']*10000)*1009


def limits(stage,p):
    if stage=='coarse':return p['coarse_shots'],p['coarse_shots']+1
    if stage=='finalist':return p['finalist_shots'],p['finalist_failures']
    if stage=='refine':return p['refine_shots'],p['refine_failures']
    return p['max_shots'],p['target_failures']


def validate(row,qcode,job,stage,c):
    r.validate_event(row,qcode,job,stage,c)
    if c.get('search'):
        sc=engine.GammaControls(**c['search'])
        for component,detail in enumerate(row['components']):
            expected=[sha256(engine.gamma_vector(sc,memory_seed(job,stage)+component,row['shot'],leg,qcode.n).tobytes()).hexdigest()
                      for leg in range(len(detail['units']))]
            if detail.get('gamma_sha256')!=expected:raise ValueError('uniform/disordered gamma provenance mismatch')
        updates=qcode.n*row['iterations']
        draws=qcode.n*sum(len(d['units'])-1 for d in row['components'])
        clips=sum(sum(u[7] for u in d['units']) for d in row['components'])
    else:updates=draws=clips=0
    if (row.get('gamma_bias_updates'),row.get('disorder_draws'),row.get('memory_clips'))!=(updates,draws,clips):
        raise ValueError('gamma work accounting mismatch')
    if not 0<=clips<=updates:raise ValueError('invalid memory clipping count')


class Reduction(r.Reduction):
    def append(self,row):
        super().append(row)
        for key in ('gamma_bias_updates','disorder_draws','memory_clips'):self.totals[key]+=row[key]


def manifest_for(plan,job,stage,c):
    maximum,target=limits(stage,plan['protocol'])
    return {'schema':'lp1054-relay-gamma-ledger-v1','plan_sha256':rt.sha(ROOT/'plan.json'),
        'job':job,'stage':stage,'controls':c,'seed':SEEDS[stage],'memory_seed':memory_seed(job,stage),
        'max_shots':maximum,'target_failures':target,'chunk_size':CHUNK}


def read_rows(directory,manifest,job,stage,c,audit):
    if json.loads((directory/'manifest.json').read_text())!=manifest:raise ValueError('manifest changed')
    rows=Reduction();failures=0;qc=code()
    prepared=engine.Prepared(qc,job['physical_p'],c,memory_seed(job,stage)) if audit else None
    paths=sorted(directory.glob('chunk-*.jsonl.gz'))
    for path in paths:
        if path.name!=f'chunk-{len(rows)//CHUNK:09d}.jsonl.gz':raise ValueError('ledger gap')
        with gzip.open(path,'rt') as stream:batch=[json.loads(line) for line in stream]
        if not 1<=len(batch)<=CHUNK:raise ValueError('invalid immutable chunk')
        for row in batch:
            if row['shot']!=len(rows) or len(rows)>=manifest['max_shots'] or failures>=manifest['target_failures']:
                raise ValueError('shot order or exact stopping violated')
            validate(row,qc,job,stage,c);rows.append(row);failures += row['outcome']!='success'
        if audit:
            for row in (batch[0],batch[-1]):
                actual=r.make_event(prepared,job,stage,row['shot'])
                if {k:v for k,v in actual.items() if k!='decode_ns'}!={k:v for k,v in row.items() if k!='decode_ns'}:
                    raise ValueError('canonical endpoint replay mismatch')
    return rows


def evaluate(plan,job,stage,c,audit=False):
    directory=ROOT/'results'/job['id']/stage/identity(c)[:24]
    manifest=manifest_for(plan,job,stage,c)
    if audit and not directory.exists():raise ValueError('missing required cohort')
    directory.mkdir(parents=True,exist_ok=True);path=directory/'manifest.json'
    if not path.exists():
        if audit:raise ValueError('missing frozen manifest')
        rt.write_json(path,manifest)
    rows=read_rows(directory,manifest,job,stage,c,audit)
    if not audit:
        prepared=engine.Prepared(code(),job['physical_p'],c,memory_seed(job,stage))
        r.make_event(prepared,job,stage,manifest['max_shots']+1)
        failures=len(rows)-rows.counts['success']
        while len(rows)<manifest['max_shots'] and failures<manifest['target_failures']:
            offset=len(rows);batch=[]
            for shot in range(offset,min(offset+CHUNK,manifest['max_shots'])):
                row=r.make_event(prepared,job,stage,shot);validate(row,code(),job,stage,c)
                batch.append(row);failures += row['outcome']!='success'
                if failures>=manifest['target_failures']:break
            path=directory/f'chunk-{offset//CHUNK:09d}.jsonl.gz';tmp=path.with_suffix('.tmp')
            with gzip.open(tmp,'wt') as stream:
                for row in batch:stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
            tmp.replace(path);rows.extend(batch)
    if not rows:raise ValueError('empty cohort')
    value={**r.summary(rows,manifest['target_failures']),'job':job,'stage':stage,'controls':c,
        'directory':str(directory.relative_to(rt.REPO)),'manifest_sha256':rt.sha(directory/'manifest.json'),
        'chunks':{p.name:rt.sha(p) for p in sorted(directory.glob('chunk-*.jsonl.gz'))}}
    if value['shots']!=manifest['max_shots'] and value['failures']!=manifest['target_failures']:raise ValueError('unfinished cohort')
    path=directory/'summary.json'
    if audit:
        if json.loads(path.read_text())!=value:raise ValueError('summary differs from full ledger')
    else:rt.write_json(path,value)
    return value


def execute(index,audit=False):
    plan=rt.load(ROOT)
    if not 0<=index<len(plan['jobs']):raise ValueError('invalid point index')
    job=plan['jobs'][index];point=ROOT/'results'/job['id'];point.mkdir(parents=True,exist_ok=True)
    with (point/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        coarse=[evaluate(plan,job,'coarse',c,audit) for c in proposals(job)]
        final=[evaluate(plan,job,'finalist',c,audit) for c in finalists(coarse,job)]
        refined=[evaluate(plan,job,'refine',c,audit) for c in refinement(final)]
        chosen=min((row for row in refined if genuine(row['controls'])),key=r.rank)['controls']
        selected={'schema':'lp1054-gamma-selection-v1','plan_sha256':rt.sha(ROOT/'plan.json'),'job':job,
            'chosen':chosen,'confirmations':confirmations(job,chosen),
            'training':[{'stage':row['stage'],'controls':row['controls'],
                         'summary_sha256':rt.sha(rt.REPO/row['directory']/'summary.json')} for row in coarse+final+refined]}
        path=point/'selection.json'
        if path.exists():
            if json.loads(path.read_text())!=selected:raise ValueError('training selection lock differs')
        elif audit:raise ValueError('missing selection lock')
        else:rt.write_json(path,selected)
        points=[{**evaluate(plan,job,'confirmation',s['controls'],audit),'roles':s['roles']} for s in selected['confirmations']]
        receipt={'job':job,'plan_sha256':rt.sha(ROOT/'plan.json'),'selection_sha256':rt.sha(path),
                 'points':points,'training':coarse+final+refined}
        rt.write_json(point/('audit.json' if audit else 'complete.json'),receipt)
        print(job['id'],'audited' if audit else 'finished',len(points),'fresh policies',flush=True)


def freeze():
    parent=rt.load(PARENT)
    extra=list(ROOT.glob('*.py'))+[ROOT/'README.md',ROOT/'worker.sh',ROOT/'qualification.json',PARENT/'plan.json']
    extra += [rt.REPO/p for p in parent['implementation_sha256']]
    extra += [rt.REPO/t['selection_path'] for t in parent_training()]
    rt.freeze(ROOT,design(),extra)


def submit():
    with rt.dispatch_lock(ROOT):
        plan=rt.load(ROOT);(ROOT/'results').mkdir(exist_ok=True)
        path=ROOT/'dispatch.json';receipt=json.loads(path.read_text()) if path.exists() else {}
        base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab',
            '--nodes=1','--ntasks=1','--cpus-per-task=1','--mem=3G','--time=4-00:00:00',
            '--requeue',f'--chdir={rt.REPO}',
            f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1,NUMBA_NUM_THREADS=1']
        def queue(name,options):
            if name in receipt:return receipt[name]['id']
            argv=[*base,*options];out=subprocess.run(argv,check=True,capture_output=True,text=True)
            jid=out.stdout.strip().split(';')[0]
            if not jid.isdigit():raise ValueError('invalid scheduler receipt')
            receipt[name]={'id':jid,'argv':argv,'plan_sha256':rt.sha(ROOT/'plan.json')}
            rt.write_json(path,receipt);print(name,jid,flush=True);return jid
        array=queue('array',['--job-name=lp1054-gamma80-60',f'--array=0-{len(plan["jobs"])-1}%12',
            '--signal=B:USR1@180',f'--output={ROOT}/results/point-%A_%a.log',str(ROOT/'worker.sh')])
        command=shlex.join([sys.executable,str(Path(__file__).resolve()),'--collect'])
        queue('collect',['--job-name=lp1054-gamma-collect','--dependency=afterok:'+array,'--mem=16G',
            f'--output={ROOT}/results/collect-%j.log','--wrap='+
            'export NUMBA_CACHE_DIR="/tmp/lp1054-gamma-collect-${SLURM_JOB_ID}"; '+f'exec {command}'])


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for name in ('freeze','submit','collect'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--index',type=int);p.add_argument('--audit',action='store_true');a=p.parse_args()
    if a.freeze:freeze()
    elif a.submit:submit()
    elif a.collect:module('_lp1054_gamma_report',ROOT/'report.py').collect()
    else:execute(a.index,a.audit)


if __name__=='__main__':main()
