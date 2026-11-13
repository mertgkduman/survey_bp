"""Isolate joint Q-BP at d=0 on the same depolarizing samples as binary BP."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shlex
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bp_isolation_runtime import rt
from bp_study_publish import publish, refresh

ROOT = Path(__file__).resolve().parent
CONFIRMATION = ROOT.with_name('mackay-0304161-damping-t100')/'confirmation'
NEXT = ROOT.with_name('roffe-2005-07016-bp')


def design():
    prior = rt.load(CONFIRMATION)
    jobs = []
    for source in prior['jobs']:
        if source['base_arm'] != 'qbp' or source['role'] != 'baseline':
            continue
        for arm in ('qbp_undamped', 'binary_separate'):
            j = deepcopy(source)
            j.update(id=f'{source["code"]}-{arm}-p{round(source["physical_p"]*100000):05d}',
                     arm=arm, base_arm='qbp' if arm=='qbp_undamped' else 'binary_sp',
                     role='undamped_control', workers=1,
                     component_graph_edges=prior['codes'][j['code']]['edges_per_component'])
            j.pop('selection_sha256', None)
            j['decoder'].update(v2c_damping=0., family='bp4' if arm=='qbp_undamped' else 'binary_css',
                                prior='p' if arm=='qbp_undamped' else '2p/3',
                                numerical_profile='quaternary-bp4-f64-v2' if arm=='qbp_undamped' else 'binary-spa-flooding-f64-v2',
                                decoding_scope='joint_pauli' if arm=='qbp_undamped' else 'separate_xz',
                                iteration_semantics='joint_full_graph_sweeps' if arm=='qbp_undamped' else 'paired_component_rounds')
            jobs.append(j)
    return {'schema':'canonical-bp-study-v1', 'study_id':'mackay-qbp-isolation-t100',
            'label':'MacKay: undamped Q-BP and matched depolarizing separate-X/Z BP',
            'stage':'isolation', 'paper_id':prior['paper_id'], 'paper_title':prior['paper_title'],
            'paper_url':prior['paper_url'], 'codes':prior['codes'], 'budget':prior['budget'],
            'instruction_path':str((ROOT/'README.md').relative_to(rt.REPO)), 'jobs':jobs,
            'claim_limit':'Independent d=0 controls on identical depolarizing samples; T=100 inferred, not source-specified. Separate BP has max100 paired X/Z rounds, actual component sweeps and directed updates separately recorded. Classical paper ordinates for length74 at these five rates are unavailable. No superiority or recovered historical-specification claim.'}


def extra():
    return [Path(__file__), ROOT/'README.md', ROOT/'paper-evidence.json',
            ROOT/'extract_paper_evidence.py', ROOT/'PAPER-EVIDENCE.md',
            rt.REPO/'data/reproductions/bp_isolation_runtime.py',
            rt.REPO/'data/reproductions/bp_study_publish.py', CONFIRMATION/'plan.json',
            ROOT.with_name('mackay-0304161-inferred-budget')/'budget.json', NEXT/'run.py', NEXT/'plan.json']


def publish_controls():
    result = publish(ROOT)
    for s in result['result_series']:
        separate = s['source_decoder_id']=='binary_separate'
        s['label'] = ('Separate X/Z binary BP' if separate else 'Q-BP')+', SP, d = 0, depolarizing, inferred T=100'
        next(d for d in result['decoders'] if d['decoder_id']==s['decoder_id'])['label']=s['label']
        for p in s['points']:
            p['iteration_unit'] = 'paired X/Z rounds' if separate else 'joint sweeps'
            p['metadata'].update(cohort_kind='independent_matched_channel_control',
                                 iteration_definition='max(X sweeps,Z sweeps)' if separate else 'joint full-graph sweeps',
                                 shared_sample_policy='same Pauli realization for matching seed, physical rate and shot index')
    rt.write_json(ROOT/'catalog.json',result)
    verified=json.loads((ROOT/'verified.json').read_text())
    comparison=json.loads((ROOT/'comparison.json').read_text())
    comparison['method_contrasts']=[]
    for code in verified['points']:
        if code['arm']!='qbp_undamped':continue
        binary=next(r for r in verified['points'] if r['arm']=='binary_separate' and r['code']==code['code'] and r['physical_p']==code['physical_p'])
        comparison['method_contrasts'].append({'code':code['code'],'p':code['physical_p'],
           'channel':'depolarizing','damping':0,'same_sample_seed':code['seed'],
           'joint':{'ler':code['rate'],'mean_rounds':code['iterations']/code['shots'],'mean_directed_edge_updates':code['directed_edge_updates']/code['shots']},
           'separate':{'ler':binary['rate'],'mean_rounds':binary['iterations']/binary['shots'],'mean_component_sweeps':binary['component_iterations']/binary['shots'],'mean_directed_edge_updates':binary['directed_edge_updates']/binary['shots']},
           'scope':'Descriptive per-point comparison; common random prefixes, separate stopping; no pooled or simultaneous superiority claim.'})
    rt.write_json(ROOT/'comparison.json',comparison)
    return result


def advance():
    rt.collect(ROOT,require_complete=True)
    # Uses the unmodified original runtime for old confirmation, including its
    # ledger/work semantics. An incomplete old point prevents every next step.
    import bp_study_runtime as original
    original.collect(CONFIRMATION,require_complete=True)
    publish_controls()
    publish(CONFIRMATION)
    refresh(ROOT)
    subprocess.run([sys.executable,str(NEXT/'run.py'),'--submit'],check=True)


def submit(test_only=False):
    with rt.dispatch_lock(ROOT):
        plan=rt.load(ROOT);(ROOT/'results').mkdir(exist_ok=True)
        old=json.loads((CONFIRMATION/'dispatch.json').read_text())['array']['id']
        p=ROOT/'dispatch.json';receipt=json.loads(p.read_text()) if p.exists() else {}
        base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1','--requeue','--time=4-00:00:00',f'--chdir={rt.REPO}',f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
        command=shlex.join([sys.executable,str(Path(__file__).resolve())])
        def queue(name,opts):
            if name in receipt and not test_only:return receipt[name]['id']
            argv=[*base,*(['--test-only'] if test_only else []),*opts]
            r=subprocess.run(argv,check=True,capture_output=True,text=True)
            if test_only:print(r.stdout+r.stderr);return None
            jid=r.stdout.strip().split(';')[0]
            if not jid.isdigit():raise ValueError('invalid Slurm receipt')
            receipt[name]={'id':jid,'argv':argv};rt.write_json(p,receipt);print(name,jid,flush=True);return jid
        array=queue('array',['--job-name=mackay-qbp-isolate','--cpus-per-task=1','--mem=4G',f'--array=0-{len(plan["jobs"])-1}%8',f'--output={ROOT/"results/slurm-%A_%a.log"}',f'--wrap=exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        if not test_only:
            collect=queue('collect',['--job-name=mackay-isolate-audit','--cpus-per-task=1','--mem=4G',f'--dependency=afterok:{array}',f'--output={ROOT/"results/collect-%j.log"}',f'--wrap={command} --collect'])
            queue('advance',['--job-name=mackay-isolate-next','--cpus-per-task=1','--mem=4G',f'--dependency=afterok:{collect}:{old}',f'--output={ROOT/"results/advance-%j.log"}',f'--wrap={command} --advance'])


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('freeze','submit','test-only','collect','advance'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--index',type=int);a=p.parse_args()
    if a.freeze:rt.freeze(ROOT,design(),extra())
    elif a.submit or a.test_only:submit(a.test_only)
    elif a.index is not None:print(json.dumps(rt.execute(ROOT,a.index)),flush=True)
    elif a.advance:advance()
    else:
        rt.collect(ROOT,require_complete=True);publish_controls();refresh(ROOT)

if __name__=='__main__':main()
