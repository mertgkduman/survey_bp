"""Select damping by LER first, then confirm on independent data."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import sys
import numpy as np
from scipy.stats import beta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bp_study_runtime as rt

ROOT = Path(__file__).resolve().parent
DAMPING = (0., .1, .3, .5, .7, .85, .95)
RATES = (.010, .013, .020, .030, .040)
TUNING_SHOTS = 1024
NEXT = ROOT.with_name('roffe-2005-07016-bp')


def design():
    codes = json.loads((rt.PARENT / 'codes.json').read_text())
    for code in codes.values():
        code['artifact'] = str((rt.PARENT / code['artifact']).relative_to(rt.REPO))
    jobs = []
    for code, receipt in sorted(codes.items()):
        for family in ('binary_sp', 'qbp'):
            for damping in DAMPING:
                for marginal in RATES:
                    p = 1.5 * marginal if family == 'qbp' else marginal
                    arm = f'{family}_d{round(100*damping):03d}'
                    settings = {'family': 'bp4' if family == 'qbp' else 'binary_css',
                                'check_rule': 'sum_product', 'schedule': 'flooding',
                                'v2c_damping': damping, 'max_iterations': 88200,
                                'branch_count': 1, 'iterations_per_branch': 88200,
                                'message_resolution': 'float64', 'prior': 'p', 'check_cap': None,
                                'product_epsilon': 1e-10,
                                'noise_model': 'depolarizing' if family == 'qbp' else 'x_only'}
                    jobs.append({'id': f'{code}-{arm}-p{round(p*100000):05d}', 'code': code, 'arm': arm,
                                 'base_arm': family, 'physical_p': p, 'matched_x_rate': marginal,
                                 'decoder': settings, 'seed': 2026111307, 'workers': 1,
                                 'target_block_failures': TUNING_SHOTS+1, 'max_shots': TUNING_SHOTS,
                                 'code_artifact': receipt['artifact'], 'code_semantic_sha256': receipt['semantic_sha256'],
                                 'graph_edges': receipt['edges_per_component'] * (2 if family=='qbp' else 1)})
    return {'study_id': 'mackay-damping-tuning', 'stage': 'tuning', 'codes': codes, 'jobs': jobs,
            'paper_url': 'https://arxiv.org/abs/quant-ph/0304161v3', 'paper_id': 'mackay-0304161-v3',
            'paper_title': 'Sparse Graph Codes for Quantum Error-Correction',
            'damping_grid': list(DAMPING), 'tuning_shots_per_rate': TUNING_SHOTS,
            'selection': {'primary': 'mean block LER across five equally weighted rates; one damping per code/family',
                          'similarity_margin': '10% of empirical-best mean LER; no positive absolute floor',
                          'tie_guard': 'simultaneous one-sided paired risk-regret upper bounds from per-rate exact discordance bounds; alpha=.05 across all code/family/candidate/rate comparisons',
                          'secondary': 'minimum mean actual executed iterations among guard-qualified candidates',
                          'fallback': 'empirical lowest LER; selection remains provisional until independent confirmation',
                          'confirmation_seed': 2026111309, 'confirmation_stop': '20 block failures or 100000000 shots',
                          'baseline_damping': {'binary_sp': 0., 'qbp': .1}},
            'claim_limit': 'Exploratory damping selection; fixed tuning cohorts never pooled into independent confirmation. No source-faithful numerical or superiority claim.'}


def extra():
    return [Path(__file__), ROOT / 'README.md', rt.REPO / 'data/reproductions/bp_study_publish.py',
            NEXT / 'run.py', NEXT / 'plan.json']


def choose_damping(values, means, tail):
    scores={d:float(v.mean()) for d,v in values.items()}
    best=min(scores,key=lambda d:(scores[d],d));margin=.1*scores[best]
    bounds={best:0.}
    for d,value in values.items():
        if d==best:continue
        upper=[]
        for v,b in zip(value,values[best],strict=True):
            pos=int(np.sum((v==1)&(b==0)));neg=int(np.sum((v==0)&(b==1)));n=len(v)
            hi=1. if pos==n else float(beta.ppf(1-tail,pos+1,n-pos))
            lo=0. if neg==0 else float(beta.ppf(tail,neg,n-neg+1))
            upper.append(hi-lo)
        bounds[d]=float(np.mean(upper))
    eligible=[d for d in values if bounds[d]<=margin]
    choice=min(eligible,key=lambda d:(means[d],scores[d],d))
    return {'damping':choice,'empirical_best_damping':best,'mean_ler':scores[choice],
            'mean_iterations':means[choice],'similarity_margin':margin,'paired_regret_upper':bounds[choice],
            'speed_tie_certified':choice!=best,
            'candidates':[{'damping':d,'mean_ler':scores[d],'mean_iterations':means[d],
                           'paired_regret_upper':bounds[d],'eligible':d in eligible} for d in sorted(values)]}


def select():
    plan=rt.load(ROOT); receipt=rt.collect(ROOT, require_complete=True)
    groups=defaultdict(list)
    for row in receipt['points']: groups[(row['code'],row['base_arm'])].append(row)
    selected=[]
    tail=.05/(2*len(groups)*len(DAMPING)*(len(DAMPING)-1)*len(RATES))
    for (code,family),rows in sorted(groups.items()):
        candidates=defaultdict(list)
        for row in rows: candidates[row['decoder']['v2c_damping']].append(row)
        values={}; identities={}
        for damping,points in candidates.items():
            labels=[]; hashes=[]
            for row in sorted(points,key=lambda x:x['matched_x_rate']):
                events=[]
                for path in sorted((ROOT/'results'/row['id']).glob('shots-*.jsonl.gz')):
                    with gzip.open(path,'rt') as f: events.extend(json.loads(line) for line in f)
                assert len(events)==TUNING_SHOTS
                labels.append(np.array([e['outcome'] in rt.parent.base.FAILURES for e in events],dtype=np.int8))
                hashes.append([e['error_sha256'] for e in events])
            values[damping]=np.array(labels);identities[damping]=hashes
        first=next(iter(identities.values()))
        if any(h!=first for h in identities.values()): raise ValueError('damping candidates do not share identical physical samples')
        means={d:sum(r['iterations'] for r in points)/(TUNING_SHOTS*len(RATES)) for d,points in candidates.items()}
        selected.append({'code':code,'base_arm':family,**choose_damping(values,means,tail)})
    result={'schema':'bp-damping-selection-v1','plan_sha256':rt.sha(ROOT/'plan.json'),
            'tuning_receipt_sha256':rt.sha(ROOT/'verified.json'),'selected':selected,
            'status':'provisional selection; confirmation required; no equivalence inferred from overlapping intervals'}
    p=ROOT/'selection.json'
    if p.exists() and json.loads(p.read_text())!=result:raise ValueError('refusing to change frozen selection')
    if not p.exists():rt.write_json(p,result)
    return result


def confirmation(selection):
    plan=rt.load(ROOT);jobs=[]
    for entry in selection['selected']:
        family=entry['base_arm'];baseline=plan['selection']['baseline_damping'][family]
        choices=[('selected',entry['damping'])]
        if baseline!=entry['damping']:choices.append(('baseline',baseline))
        for role,damping in choices:
            for job in plan['jobs']:
                if job['code']==entry['code'] and job['base_arm']==family and job['decoder']['v2c_damping']==damping:
                    jobs.append({**job,'id':f'{role}-{job["id"]}','arm':f'{family}_{role}',
                                 'role':role,'seed':2026111309,'workers':4,
                                 'max_shots':100_000_000,'target_block_failures':20,
                                 'selection_sha256':rt.sha(ROOT/'selection.json')})
    design={**{k:v for k,v in plan.items() if k not in ('implementation_sha256','software')},
            'study_id':'mackay-damping-confirmation','stage':'confirmation','jobs':jobs}
    return rt.freeze(ROOT/'confirmation',design,[*extra(),ROOT/'selection.json',ROOT/'plan.json'])


def submit(stage='tuning',test_only=False):
    root=ROOT if stage=='tuning' else ROOT/'confirmation'
    with rt.dispatch_lock(root):
        return _submit(stage,test_only)


def _submit(stage='tuning',test_only=False):
    root=ROOT if stage=='tuning' else ROOT/'confirmation';plan=rt.load(root)
    (root/'results').mkdir(exist_ok=True)
    receipt_path=root/'dispatch.json';receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    workers=1 if stage=='tuning' else 4; concurrency=16 if stage=='tuning' else 8
    base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1','--requeue',
          '--time=4-00:00:00',f'--chdir={rt.REPO}',
          f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
    command=shlex.join([sys.executable,str(Path(__file__).resolve()),'--stage',stage])
    def queue(name,opts):
        if name in receipt and not test_only:return receipt[name]['id']
        argv=[*base,*(['--test-only'] if test_only else []),*opts]
        result=subprocess.run(argv,check=True,capture_output=True,text=True)
        if test_only:print(result.stderr+result.stdout);return None
        jid=result.stdout.strip().split(';')[0]
        if not jid.isdigit():raise ValueError('invalid scheduler receipt')
        receipt[name]={'id':jid,'argv':argv};rt.write_json(receipt_path,receipt);print(stage,name,jid,flush=True);return jid
    array=queue('array',[f'--job-name=bp-damp-{stage}',f'--cpus-per-task={workers}','--mem=4G',
                          f'--array=0-{len(plan["jobs"])-1}%{concurrency}',f'--output={root/"results/slurm-%A_%a.log"}',
                          f'--wrap=exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
    if not test_only:
        queue('advance',['--job-name=bp-damp-advance','--cpus-per-task=1','--mem=4G',
                         f'--dependency=afterok:{array}',f'--output={root/"results/advance-%j.log"}',f'--wrap={command} --advance'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['tuning','confirmation'],default='tuning')
    g=p.add_mutually_exclusive_group(required=True)
    for name in ('freeze','submit','test-only','collect','advance'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--index',type=int);args=p.parse_args();root=ROOT if args.stage=='tuning' else ROOT/'confirmation'
    if args.freeze:rt.freeze(ROOT,design(),extra())
    elif args.submit or args.test_only:submit(args.stage,args.test_only)
    elif args.index is not None:print(json.dumps(rt.execute(root,args.index)),flush=True)
    elif args.collect:print(len(rt.collect(root)['points']))
    elif args.advance:
        if args.stage=='tuning':confirmation(select());submit('confirmation')
        else:
            rt.collect(root,require_complete=True)
            from bp_study_publish import publish,refresh
            publish(root);refresh(root)
            subprocess.run([sys.executable,str(NEXT/'run.py'),'--submit'],check=True)

if __name__=='__main__':main()
