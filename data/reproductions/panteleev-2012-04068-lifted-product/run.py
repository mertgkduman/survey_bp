"""One CPU per LP1054 arm/rate; frozen tuning, fresh iid ledgers and audit."""
import argparse
from collections import Counter
from dataclasses import asdict
import fcntl
from functools import lru_cache
import gzip
from hashlib import sha256
import importlib.util
import itertools
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys

import numpy as np
from scipy.stats import beta
from bp_registry.artifacts import load_artifact

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import bp_study_runtime as rt
spec = importlib.util.spec_from_file_location('_lp1054_engine',ROOT/'engine.py')
engine = importlib.util.module_from_spec(spec);sys.modules[spec.name]=engine;spec.loader.exec_module(engine)
SEEDS = {'coarse':2026111601,'finalist':2026111602,'confirmation':2026111603}
ARMS = ('bp','qbp','osd0','cs10','qbp_osd0','qbp_cs10','tuned_bp','tuned_qbp',
        'relay32','relay128','beam32','beam128')


def identity(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


@lru_cache(maxsize=1)
def code():
    source = json.loads((ROOT/'source.json').read_text())
    return load_artifact(rt.REPO,(ROOT/'code.npz').relative_to(rt.REPO),
                         expected_semantic_sha256=source['semantic_sha256']).code


def design():
    source = json.loads((ROOT/'source.json').read_text())
    return {'study_id':'panteleev-lp1054-full-stack','paper_id':'panteleev-2012-04068-v2',
        'label':'Panteleev-Kalachev lifted product [[1054,140]]: full canonical decoder stack',
        'codes':{'lp1054':{'artifact':str((ROOT/'code.npz').relative_to(rt.REPO)),
                         'semantic_sha256':source['semantic_sha256']}},
        'source':source,'protocol':{'target_failures':20,'max_shots':100_000_000,
            'coarse_shots':512,'finalist_shots':8192,'finalist_failures':40,'seeds':SEEDS,
            'selection':'minimum finalist block LER; exact ties total BP sweeps, warmed decode ns, configuration hash',
            'jobs':'one single-threaded CPU per arm/physical-rate point, both components counted',
            'search_budgets':'32 or128 cumulative sweeps per CSS component; complete branch/relay work included'},
        'claim_limit':source['settings_limit']+' Original LP Example4, depolarizing code capacity. Q-BP, tuning, Relay and beam are canonical adaptations. Search128 is explicitly4x the documented BP cap. No native runtime or statistical paper agreement is claimed before confirmation.',
        'jobs':[{'id':f'{arm}-p{round(p*10000):04d}','arm':arm,'physical_p':p}
                for p,arm in itertools.product(source['rates'],ARMS)]}


def fixed(arm):
    c = {'family':'qbp' if 'qbp' in arm else 'bp','cap':32,'damping':0.,'alpha':.625,'beta':0.}
    if arm in ('osd0','cs10','qbp_osd0','qbp_cs10'):
        c['osd'] = 'OSD_0' if arm.endswith('osd0') else 'OSD_CS'
    return c


def proposals(arm):
    if arm not in ('tuned_bp','tuned_qbp') and not arm.startswith(('relay','beam')):
        return [fixed(arm)]
    values = []
    for damping,alpha,offset in itertools.product((0.,.3,.5,.7),(.5,.625,.8,1.),(0.,.2)):
        c = {**fixed(arm),'damping':damping,'alpha':alpha,'beta':offset}
        if arm.startswith(('relay','beam')):
            cap = 128 if arm.endswith('128') else 32
            c['cap'] = cap
            for architecture in (0,1):
                initial = 5 if cap==32 else 20
                units = (4 if architecture==0 else 8) if cap==32 else (12 if architecture==0 else 24)
                step = (cap-initial)//units
                method = 'relay' if arm.startswith('relay') else 'beam'
                sc = engine.search.Controls(method,initial=initial,per_unit=step,units=units,
                    damping=damping,alpha=alpha,paper_scale=False,beta=offset,
                    width=1 if architecture==0 else 2,rounds=units,
                    solutions=1 if architecture==0 else 4,first_gamma=0.,
                    gamma_low=-.24 if architecture==0 else -.5,
                    gamma_high=.66 if architecture==0 else 1.)
                values.append({**c,'search':asdict(sc)})
        else:
            values.append(c)
    return values


def encode(v):
    return np.packbits(v,bitorder='little').tobytes().hex()


def decode(s,n):
    raw = bytes.fromhex(s)
    if len(raw)!=(n+7)//8:raise ValueError('invalid candidate byte count')
    bits = np.unpackbits(np.frombuffer(raw,dtype=np.uint8),bitorder='little')
    if bits[n:].any():raise ValueError('nonzero packed candidate padding')
    return bits[:n]


def make_event(prepared,job,stage,shot):
    p = job['physical_p']; qcode = prepared.code
    truth = engine.sample(SEEDS[stage],round(p*10000),shot,qcode.n,p)
    syndromes = [engine.multiply(qcode.hz,truth[0]),engine.multiply(qcode.hx,truth[1])]
    candidates,row = prepared.decode(syndromes,shot)
    row.update(shot=shot,outcome=engine.outcome(qcode,truth,candidates),
               truth=[encode(x) for x in truth],candidate=[encode(x) for x in candidates],
               syndrome=[encode(x) for x in syndromes])
    return row


def validate_event(row,qcode,job,stage,c):
    shot = row['shot']; truth = engine.sample(SEEDS[stage],round(job['physical_p']*10000),shot,qcode.n,job['physical_p'])
    if row['truth'] != [encode(x) for x in truth]:
        raise ValueError('sample provenance mismatch')
    candidates = [decode(x,qcode.n) for x in row['candidate']]
    syndrome = [engine.multiply(qcode.hz,truth[0]),engine.multiply(qcode.hx,truth[1])]
    if row['syndrome'] != [encode(x) for x in syndrome] or row['outcome']!=engine.outcome(qcode,truth,candidates):
        raise ValueError('independent original-problem outcome mismatch')
    iterations = edges = 0
    expected_edges = [int(qcode.hz.sum()),int(qcode.hx.sum())]
    if c['family']=='qbp':expected_edges = [sum(expected_edges)]
    if len(row['components']) != len(expected_edges):raise ValueError('missing component work')
    for component,e in zip(row['components'],expected_edges):
        if component['edges']!=e:raise ValueError('graph identity differs')
        if c.get('search'):
            trace = component['units']; sc = c['search']
            if not 1<=len(trace)<=sc['units']+1:raise ValueError('invalid search unit count')
            for i,u in enumerate(trace):
                if (len(u)!=8 or not 1<=u[3]<=(sc['initial'] if i==0 else sc['per_unit'])
                        or not 0<=u[4]<=e or (i and not 0<=u[0]<i)):
                    raise ValueError('invalid search lineage or work')
            it = sum(u[3] for u in trace); work = 2*sum(u[3]*u[4] for u in trace)
        else:
            it = component['iterations']; work = 2*it*e
        if it!=component['iterations'] or not 1<=it<=c['cap']:raise ValueError('iteration ceiling exceeded')
        iterations += it;edges += work
    if row['iterations']!=iterations or row['directed_edge_updates']!=edges or row['decode_ns']<=0:
        raise ValueError('cumulative work mismatch')


class Reduction:
    """Bounded-memory ledger reduction, including up to100M-shot cohorts."""
    def __init__(self):
        self.n = 0; self.counts = Counter();self.totals = Counter();self.latency = Counter()
    def __len__(self):return self.n
    def append(self,row):
        self.n += 1; self.counts[row['outcome']] += 1
        for key in ('iterations','directed_edge_updates','decode_ns'):self.totals[key] += row[key]
        self.latency[math.floor(math.log(row['decode_ns'])/math.log(1.01))] += 1
    def extend(self,rows):
        for row in rows:self.append(row)
    def quantile(self,q):
        count = 0
        for bucket,n in sorted(self.latency.items()):
            count += n
            if count>=math.ceil(q*self.n):return 1.01**(bucket+1)/1e9


def summary(rows,target):
    counts = rows.counts; n = len(rows); k = n-counts['success']
    if not n:raise ValueError('empty cohort cannot be summarized')
    low = 0. if k==0 else float(beta.ppf(.025,k,n-k+1))
    failure_stop = k==target
    high = 1. if k==n else float(beta.ppf(.975,k if failure_stop else k+1,n-k))
    return {'shots':n,'failures':k,'rate':k/n,'ci95_low':low,'ci95_high':high,'counts':dict(counts),
        'stop_reason':'target_failures' if failure_stop else 'shot_cap',
        'uncertainty_method':'exact_negative_binomial_interval' if failure_stop else 'exact_binomial_interval_at_shot_cap',
        **dict(rows.totals),'latency_quantiles_seconds':{str(q):rows.quantile(q) for q in (.5,.95,.99)}}


def stage_limits(stage,protocol):
    if stage=='coarse':return protocol['coarse_shots'],protocol['coarse_shots']+1
    if stage=='finalist':return protocol['finalist_shots'],protocol['finalist_failures']
    return protocol['max_shots'],protocol['target_failures']


def read_rows(directory,manifest,qcode,job,stage,c,replay=False):
    if json.loads((directory/'manifest.json').read_text())!=manifest:raise ValueError('manifest changed')
    rows = Reduction(); prepared = engine.Prepared(qcode,job['physical_p'],c,SEEDS[stage]) if replay else None
    maximum,target = manifest['max_shots'],manifest['target_failures']; failures = 0
    for chunk in sorted(directory.glob('chunk-*.jsonl.gz')):
        if chunk.name!=f'chunk-{len(rows)//64:09d}.jsonl.gz':raise ValueError('ledger gap')
        with gzip.open(chunk,'rt') as stream:batch = [json.loads(line) for line in stream]
        if not 1<=len(batch)<=64:raise ValueError('invalid ledger chunk')
        for row in batch:
            if len(rows)>=maximum or failures>=target or row['shot']!=len(rows):raise ValueError('shot sequence or stopping violated')
            validate_event(row,qcode,job,stage,c);rows.append(row);failures += row['outcome']!='success'
        if replay:
            for row in (batch[0],batch[-1]):
                actual = make_event(prepared,job,stage,row['shot'])
                if {k:v for k,v in actual.items() if k!='decode_ns'}!={k:v for k,v in row.items() if k!='decode_ns'}:
                    raise ValueError('canonical endpoint replay differs')
    return rows


def evaluate(plan,job,stage,c,audit=False):
    directory = ROOT/'results'/job['id']/stage/identity(c)[:24]
    qcode = code();maximum,target = stage_limits(stage,plan['protocol'])
    manifest = {'schema':'lp1054-iid-ledger-v1','plan_sha256':rt.sha(ROOT/'plan.json'),'job':job,'stage':stage,
        'controls':c,'seed':SEEDS[stage],'max_shots':maximum,'target_failures':target}
    if audit and not directory.exists():raise ValueError('missing expected cohort')
    directory.mkdir(parents=True,exist_ok=True)
    if not (directory/'manifest.json').exists():
        if audit:raise ValueError('missing manifest')
        rt.write_json(directory/'manifest.json',manifest)
    rows = read_rows(directory,manifest,qcode,job,stage,c,replay=audit)
    if not audit:
        prepared = engine.Prepared(qcode,job['physical_p'],c,SEEDS[stage])
        # JIT and allocation warm-up excluded; deterministic throwaway shot.
        make_event(prepared,job,stage,maximum+1)
        failures = len(rows)-rows.counts['success']
        while len(rows)<maximum and failures<target:
            batch = []; offset = len(rows)
            for shot in range(offset,min(maximum,offset+64)):
                row = make_event(prepared,job,stage,shot);validate_event(row,qcode,job,stage,c)
                batch.append(row);failures += row['outcome']!='success'
                if failures>=target:break
            path = directory/f'chunk-{offset//64:09d}.jsonl.gz';temporary = path.with_suffix('.tmp')
            with gzip.open(temporary,'wt') as stream:
                for row in batch:stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
            temporary.replace(path);rows.extend(batch)
    if not rows:raise ValueError('empty cohort cannot be summarized')
    result = {**summary(rows,target),'controls':c,'stage':stage,'job':job,
        'directory':str(directory.relative_to(rt.REPO)),
        'manifest_sha256':rt.sha(directory/'manifest.json'),
        'chunks':{p.name:rt.sha(p) for p in sorted(directory.glob('chunk-*.jsonl.gz'))}}
    if result['shots']!=maximum and result['failures']!=target:raise ValueError('unfinished cohort')
    if audit:
        if json.loads((directory/'summary.json').read_text())!=result:raise ValueError('summary differs from full ledger')
    else:rt.write_json(directory/'summary.json',result)
    return result


def rank(row):
    return row['rate'],row['iterations']/row['shots'],row['decode_ns']/row['shots'],identity(row['controls'])


def execute(index,audit=False):
    plan = rt.load(ROOT)
    if not 0<=index<len(plan['jobs']):raise ValueError('invalid point index')
    job = plan['jobs'][index]; point = ROOT/'results'/job['id'];point.mkdir(parents=True,exist_ok=True)
    with (point/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        controls = proposals(job['arm']); coarse = []
        if len(controls)>1:
            coarse = [evaluate(plan,job,'coarse',c,audit) for c in controls]
            controls = [row['controls'] for row in sorted(coarse,key=rank)[:4]]
            finalists = [evaluate(plan,job,'finalist',c,audit) for c in controls]
            chosen = min(finalists,key=rank)['controls']
        else:
            finalists = [];chosen = controls[0]
        selection = {'plan_sha256':rt.sha(ROOT/'plan.json'),'job':job,'chosen':chosen,
            'coarse':[{'controls':r['controls'],'summary_sha256':rt.sha(rt.REPO/r['directory']/'summary.json')} for r in coarse],
            'finalists':[{'controls':r['controls'],'summary_sha256':rt.sha(rt.REPO/r['directory']/'summary.json')} for r in finalists]}
        path = point/'selection.json'
        if path.exists():
            if json.loads(path.read_text())!=selection:raise ValueError('frozen selection differs')
        elif audit:raise ValueError('missing selection lock')
        else:rt.write_json(path,selection)
        confirmation = evaluate(plan,job,'confirmation',chosen,audit)
        receipt = {'job':job,'selection_sha256':rt.sha(path),'plan_sha256':rt.sha(ROOT/'plan.json'),
            'confirmation':confirmation,'training':coarse+finalists}
        rt.write_json(point/('audit.json' if audit else 'complete.json'),receipt)
        print(job['id'],'audited' if audit else 'finished',confirmation['shots'],confirmation['rate'],flush=True)


def freeze():
    extra = list(ROOT.glob('*.py'))+[ROOT/'README.md',ROOT/'source.json',ROOT/'qualification.json']
    extra += [ROOT.with_name('roffe-2005-07016-runtime-budget')/'engine.py',
              ROOT.with_name('roffe-2005-07016-search')/'engine.py',
              rt.REPO/'src/bp_registry/postprocessing/osd.py']
    rt.freeze(ROOT,design(),extra)


def submit():
    with rt.dispatch_lock(ROOT):
        plan = rt.load(ROOT);(ROOT/'results').mkdir(exist_ok=True)
        path = ROOT/'dispatch.json';receipt = json.loads(path.read_text()) if path.exists() else {}
        base = ['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1',
            '--cpus-per-task=1','--mem=3G','--time=4-00:00:00','--requeue',f'--chdir={rt.REPO}',
            f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1,NUMBA_NUM_THREADS=1']
        command = shlex.join([sys.executable,str(Path(__file__).resolve())])
        setup = 'export NUMBA_CACHE_DIR="/tmp/lp1054-${SLURM_JOB_ID}"; mkdir -p "$NUMBA_CACHE_DIR"; '
        def queue(name,options):
            if name in receipt:return receipt[name]['id']
            argv = [*base,*options];out = subprocess.run(argv,check=True,capture_output=True,text=True)
            jid = out.stdout.strip().split(';')[0]
            if not jid.isdigit():raise ValueError('invalid scheduler receipt')
            receipt[name] = {'id':jid,'argv':argv,'plan_sha256':rt.sha(ROOT/'plan.json')}
            rt.write_json(path,receipt);print(name,jid,flush=True);return jid
        array = queue('array',['--job-name=lp1054-stack',f'--array=0-{len(plan["jobs"])-1}%72',
            f'--output={ROOT}/results/worker-%A_%a.log','--wrap='+setup+f'exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        audit = queue('audit',['--job-name=lp1054-audit',f'--array=0-{len(plan["jobs"])-1}%72',
            '--dependency=aftercorr:'+array,f'--output={ROOT}/results/audit-%A_%a.log',
            '--wrap='+setup+f'exec {command} --audit --index "$SLURM_ARRAY_TASK_ID"'])
        queue('collect',['--job-name=lp1054-collect','--dependency=afterok:'+audit,'--mem=16G',
            f'--output={ROOT}/results/collect-%j.log','--wrap='+setup+f'exec {command} --collect'])


def main():
    p = argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--submit',action='store_true')
    p.add_argument('--index',type=int);p.add_argument('--audit',action='store_true');p.add_argument('--collect',action='store_true')
    args = p.parse_args()
    if args.freeze:freeze()
    elif args.submit:submit()
    elif args.collect:
        report = engine.module('_lp1054_report',ROOT/'report.py');report.collect()
    elif args.index is not None:execute(args.index,args.audit)
    else:p.error('choose freeze, submit, collect or index')


if __name__=='__main__':main()
