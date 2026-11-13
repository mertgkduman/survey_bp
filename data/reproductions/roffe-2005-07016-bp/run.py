"""Regular BP from Roffe Figure 3 and a matched-budget canonical Q-BP comparison."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import bp_study_runtime as rt
ROOT=Path(__file__).resolve().parent


def design():
    codes=json.loads((ROOT/'codes.json').read_text());source=json.loads((ROOT/'source_points.json').read_text());jobs=[]
    for code,c in sorted(codes.items()):
        for family in ('binary_ms','qbp_ms'):
            for point in source['curves'][str(c['d'])]:
                joint=family=='qbp_ms';p=1.5*point['p'] if joint else point['p'];limit=c['n']
                settings={'family':'bp4' if joint else 'binary_css','check_rule':'min_sum','schedule':'flooding',
                    'alpha_schedule':'1-2**(-iteration)','first_iteration':1,'v2c_damping':0.,
                    'max_iterations':limit,'branch_count':1,'iterations_per_branch':limit,
                    'message_resolution':'float64','prior':'p','check_cap':None,
                    'noise_model':'depolarizing' if joint else 'x_only',
                    'hard_decision':'map_pauli' if joint else 'min_llr','zero_syndrome_shortcut':False,
                    'numerical_profile':'bp-flooding-policy-v2; float64; exact_unity'}
                jobs.append({'id':f'{code}-{family}-p{round(p*100000):05d}','code':code,'arm':family,
                    'physical_p':p,'matched_x_rate':point['p'],'decoder':settings,'seed':2026111311,'workers':1,
                    'target_block_failures':20,'max_shots':100_000_000,'code_artifact':c['artifact'],
                    'code_semantic_sha256':c['semantic_sha256'],'graph_edges':c['edges_per_component']*(2 if joint else 1),
                    'source_target':None if joint else point['block_ler_approx']})
    return {'study_id':'roffe-2020-figure3-canonical-bp','label':'Roffe 2020 Figure 3: regular BP and canonical Q-BP',
        'stage':'paper','codes':codes,'jobs':jobs,'paper_id':'roffe-2005-07016-v2',
        'paper_title':'Decoding Across the Quantum LDPC Code Landscape','paper_url':source['paper'],
        'catalog_papers':[{'paper_id':'roffe-2005-07016-v2','title':'Decoding Across the Quantum LDPC Code Landscape',
            'identity':'arXiv:2005.07016v2; Phys. Rev. Research 2, 043423 (2020)','kind':'paper',
            'source_url':source['paper'],'evidence_path':str((ROOT/'source.json').relative_to(rt.REPO)),
            'registered_scope':'Figure 3 toric regular min-sum BP; Q-BP is a controlled comparison'}],
        'claim_limit':'Source-matched regular binary BP: Figure 3 toric codes, measured p grid, flooding min-sum, alpha_t=1-2^-t, T=n. Exact author floating-point/row ordering is not available; canonical adaptation pending statistical comparison. Q-BP uses joint min-sum at T=n on matched-marginal depolarizing noise (p_dep=1.5*p_X), not the paper channel. No OSD executes in either arm.'}


def submit(test_only=False):
    with rt.dispatch_lock(ROOT):
        return _submit(test_only)


def _submit(test_only=False):
    plan=rt.load(ROOT);(ROOT/'results').mkdir(exist_ok=True)
    path=ROOT/'dispatch.json';receipt=json.loads(path.read_text()) if path.exists() else {}
    base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab','--nodes=1','--ntasks=1',
          '--cpus-per-task=1','--mem=4G','--requeue','--time=4-00:00:00',f'--chdir={rt.REPO}',
          f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
    command=shlex.join([sys.executable,str(Path(__file__).resolve())])
    def queue(name,opts):
        if name in receipt and not test_only:return receipt[name]['id']
        argv=[*base,*(['--test-only'] if test_only else []),*opts]
        result=subprocess.run(argv,check=True,capture_output=True,text=True)
        if test_only:print(result.stderr+result.stdout);return None
        jid=result.stdout.strip().split(';')[0]
        if not jid.isdigit():raise ValueError('invalid scheduler receipt')
        receipt[name]={'id':jid,'argv':argv};rt.write_json(path,receipt);print(name,jid,flush=True);return jid
    array=queue('array',['--job-name=roffe-bp',f'--array=0-{len(plan["jobs"])-1}%16',
                        f'--output={ROOT/"results/slurm-%A_%a.log"}',f'--wrap=exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
    if not test_only:queue('collect',['--job-name=roffe-bp-audit',f'--dependency=afterok:{array}',
                       f'--output={ROOT/"results/collect-%j.log"}',f'--wrap={command} --collect --complete'])


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('freeze','submit','test-only','collect'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--index',type=int);p.add_argument('--complete',action='store_true');a=p.parse_args()
    if a.freeze:rt.freeze(ROOT,design(),[Path(__file__),ROOT/'prepare.py',ROOT/'codes.json',ROOT/'source_points.json',ROOT/'source.json',ROOT/'README.md',rt.REPO/'data/reproductions/bp_study_publish.py'])
    elif a.submit or a.test_only:submit(a.test_only)
    elif a.index is not None:print(json.dumps(rt.execute(ROOT,a.index)),flush=True)
    else:
        result=rt.collect(ROOT,require_complete=a.complete)
        from bp_study_publish import publish,refresh
        publish(ROOT);refresh(ROOT);print(f'{len(result["points"])}/{result["planned_points"]} audited',flush=True)

if __name__=='__main__':main()
