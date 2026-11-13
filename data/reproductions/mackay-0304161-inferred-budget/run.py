"""Independent MacKay reference at a curve-inferred 100-iteration decode cap."""
from copy import deepcopy
import importlib.util
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from bp_unicycle_runtime import rt
from bp_study_publish import publish,refresh
ROOT=Path(__file__).resolve().parent
NEXT=ROOT.with_name('mackay-0304161-damping-t100')


def design():
    budget=json.loads((ROOT/'budget.json').read_text())
    limit=budget['bp_iterations']
    if limit!=100 or budget['status']!='curve_inferred_not_source_specified':raise ValueError('unexpected inferred-budget qualification')
    s=importlib.util.spec_from_file_location('_baseline_template',ROOT.with_name('mackay-0304161-damping')/'run.py')
    template=importlib.util.module_from_spec(s);s.loader.exec_module(template)
    d=template.design();jobs=[]
    targets=json.loads((ROOT.with_name('mackay-0304161-paper-rates')/'source_points.json').read_text())['points']
    for j in d['jobs']:
        if j['decoder']['v2c_damping']!=(.1 if j['base_arm']=='qbp' else 0.):continue
        j=deepcopy(j);family=j['base_arm'];j.update(arm=family,id=f'{j["code"]}-{family}-p{round(j["physical_p"]*100000):05d}',
                    seed=2026111317,workers=1,target_block_failures=20,max_shots=100_000_000,
                    budget_status='curve_inferred_not_source_specified')
        j['decoder'].update(max_iterations=limit,iterations_per_branch=limit,budget_status='curve_inferred_not_source_specified',
             numerical_profile='quaternary-bp4-f64-v2' if family=='qbp' else 'binary-spa-flooding-f64-v2')
        jobs.append(j)
        if family=='binary_sp':
            k=deepcopy(j);k.update(arm='unicycle_sp',id=j['id'].replace('-binary_sp-','-unicycle_sp-'),
                    workers=16 if j['code']=='unicycle274' and j['physical_p']<=.013 else 4,
                    graph_edges=j['graph_edges']-(d['codes'][j['code']]['n']-1))
            k['decoder'].update(branch_count=2,max_iterations=2*limit,iterations_per_branch=limit,
                 mechanism='unicycle_extra_bit_hypotheses',
                 controller={'kind':'unicycle_extra_bit_hypotheses','branch_count':2,'iterations_per_branch':limit,
                      'selection':'valid_maximum_likelihood','tie_break':'extra_bit_zero',
                      'certified_pruning':'skip_unique_lighter_candidate',
                      'minimum_distance_bounds':{'unicycle74':10,'unicycle274':18}})
            if j['code']=='unicycle274':k['source_classical_target']=targets[f'{j["physical_p"]:.3f}']['total_error_approx']
            jobs.append(k)
    return {**{key:value for key,value in d.items() if key not in ('selection','damping_grid','tuning_shots_per_rate')},
       'study_id':'mackay-inferred-t100-baseline','label':'MacKay: inferred T=100 reference and controlled BP/Q-BP',
       'stage':'paper','jobs':jobs,'budget':budget,
       'claim_limit':'100 iterations per BP/Q-BP decode, inferred from retained curve alignment, not specified in the paper. Source unicycle uses 100 per hypothesis (maximum 200 total), explicitly distinct from 100-iteration plain decoders. Fresh seed; retain old 88200 curves separately. Classical source error and quantum block failure are separately recorded; no source-faithful cap claim.'}


def publish_baseline():
    out=publish(ROOT);receipt=json.loads((ROOT/'verified.json').read_text());by_id={(x['code'],x['arm'],x['physical_p']):x for x in receipt['points']}
    for s in out['result_series']:
        if s['source_decoder_id']=='unicycle_sp':
            s['label']='Unicycle two-hypothesis BP, SP, inferred 100 iterations per hypothesis'
            next(d for d in out['decoders'] if d['decoder_id']==s['decoder_id'])['label']=s['label']
        for p in s['points']:
            row=by_id[(s['code_id'],s['source_decoder_id'],p['x'])]
            p['metadata']['budget_status']='curve_inferred_not_source_specified'
            if s['source_decoder_id']=='unicycle_sp':p['iteration_unit']='branch sweeps'
            if 'source_classical_target' in row:p['source_value']=row['source_classical_target']
    rt.write_json(ROOT/'catalog.json',out)
    comparison=json.loads((ROOT/'comparison.json').read_text());comparison['source_points']=[]
    for r in receipt['points']:
        if 'source_classical_target' not in r:continue
        comparable=r['classical_block_errors']==r['failures']
        comparison['source_points'].append({'id':r['id'],'p':r['physical_p'],'quantum_rate':r['rate'],
             'classical_rate':r['classical_block_error_rate'],'source_approx':r['source_classical_target'],
             'counts_coincide':comparable,
             'source_inside_pointwise_interval':r['ci95_low']<=r['source_classical_target']<=r['ci95_high'] if comparable else None,
             'interval_scope':'quantum stopping interval; no classical interval borrowed when counts differ'})
    rt.write_json(ROOT/'comparison.json',comparison)


def submit(test_only=False):
    with rt.dispatch_lock(ROOT):return _submit(test_only)


def _submit(test_only):
    plan=rt.load(ROOT);(ROOT/'results').mkdir(exist_ok=True)
    path=ROOT/'dispatch.json';receipt=json.loads(path.read_text()) if path.exists() else {}
    base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1','--requeue',
       '--time=4-00:00:00',f'--chdir={rt.REPO}',f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
    command=shlex.join([sys.executable,str(Path(__file__).resolve())])
    def queue(name,opts):
        if name in receipt and not test_only:return receipt[name]['id']
        argv=[*base,*(['--test-only'] if test_only else []),*opts];r=subprocess.run(argv,check=True,capture_output=True,text=True)
        if test_only:print(r.stderr+r.stdout);return None
        jid=r.stdout.strip().split(';')[0]
        if not jid.isdigit():raise ValueError('invalid Slurm receipt')
        receipt[name]={'id':jid,'argv':argv};rt.write_json(path,receipt);print(name,jid,flush=True);return jid
    arrays=[]
    for workers,concurrency in [(1,12),(4,4),(16,2)]:
        indexes=[str(i) for i,j in enumerate(plan['jobs']) if j['workers']==workers]
        if not indexes:continue
        jid=queue(f'workers_{workers}',[f'--job-name=mackay-infer-{workers}c',f'--cpus-per-task={workers}','--mem=4G',
             f'--array={",".join(indexes)}%{concurrency}',f'--output={ROOT/"results/slurm-%A_%a.log"}',
             f'--wrap=exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        if jid:arrays.append(jid)
    if not test_only:queue('advance',['--job-name=mackay-infer-audit','--cpus-per-task=1','--mem=4G',
        '--dependency=afterok:'+':'.join(arrays),f'--output={ROOT/"results/advance-%j.log"}',f'--wrap={command} --advance'])


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('freeze','submit','test-only','collect','advance'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--index',type=int);a=p.parse_args()
    if a.freeze:
        rt.freeze(ROOT,design(),[Path(__file__),ROOT/'budget.json',ROOT/'README.md',rt.REPO/'data/reproductions/bp_unicycle_runtime.py',
          rt.REPO/'data/reproductions/bp_study_publish.py',ROOT.with_name('mackay-0304161-damping')/'run.py',
          ROOT.with_name('mackay-0304161-paper-rates')/'run.py',ROOT.with_name('mackay-0304161-budget-calibration')/'infer.py',
          ROOT.with_name('mackay-0304161-budget-calibration')/'inference.json',NEXT/'run.py',NEXT/'plan.json'])
    elif a.submit or a.test_only:submit(a.test_only)
    elif a.index is not None:print(json.dumps(rt.execute(ROOT,a.index)),flush=True)
    else:
        v=rt.collect(ROOT,require_complete=a.advance);publish_baseline();refresh(ROOT);print(len(v['points']),flush=True)
        if a.advance:subprocess.run([sys.executable,str(NEXT/'run.py'),'--submit'],check=True)

if __name__=='__main__':main()
