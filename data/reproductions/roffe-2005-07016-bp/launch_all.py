"""Execution-only user override: one CPU for each frozen Roffe point."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import bp_study_runtime as rt

ROOT=Path(__file__).resolve().parent


def submit(test_only=False):
    with rt.dispatch_lock(ROOT):
        plan=rt.load(ROOT);count=len(plan['jobs'])
        if count!=218 or any(j['workers']!=1 for j in plan['jobs']):
            raise ValueError('expected218 frozen one-worker points')
        (ROOT/'results').mkdir(exist_ok=True)
        path=ROOT/'dispatch.json';receipt=json.loads(path.read_text()) if path.exists() else {}
        array_option=f'--array=0-{count-1}%{count}'
        if receipt.get('array') and array_option not in receipt['array']['argv']:
            raise ValueError('existing array has different resources; refusing duplicate dispatch')
        base=['sbatch','--parsable','--partition=common,scavenger','--account=pfisterlab',
              '--nodes=1','--ntasks=1','--cpus-per-task=1','--mem=4G','--requeue',
              '--time=4-00:00:00',f'--chdir={rt.REPO}',
              f'--export=ALL,PYTHONPATH={rt.REPO/"src"},OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1']
        command=shlex.join([sys.executable,str(ROOT/'run.py')])
        def queue(name,opts):
            if name in receipt and not test_only:return receipt[name]['id']
            argv=[*base,*(['--test-only'] if test_only else []),*opts]
            result=subprocess.run(argv,check=True,capture_output=True,text=True)
            if test_only:print(result.stdout+result.stderr);return None
            jid=result.stdout.strip().split(';')[0]
            if not jid.isdigit():raise ValueError('invalid scheduler receipt')
            receipt[name]={'id':jid,'argv':argv};rt.write_json(path,receipt);print(name,jid,flush=True);return jid
        array=queue('array',['--job-name=roffe-bp',array_option,
             f'--output={ROOT/"results/slurm-%A_%a.log"}',f'--wrap=exec {command} --index "$SLURM_ARRAY_TASK_ID"'])
        if not test_only:
            collector=queue('collect',['--job-name=roffe-bp-audit',f'--dependency=afterok:{array}',
                 f'--output={ROOT/"results/collect-%j.log"}',f'--wrap={command} --collect --complete'])
            evidence={'schema':'roffe-execution-override-v1',
                 'authorization':'User: Move to Roffe with a CPU for every point',
                 'plan_sha256':rt.sha(ROOT/'plan.json'),'launcher_sha256':rt.sha(Path(__file__)),
                 'points':count,'cpus_per_point':1,'maximum_concurrent_points':count,
                 'array':array,'collector':collector,'macKay_continues':True,
                 'frozen_scientific_files_changed':False,
                 'continuation':'Original submit() reads the same dispatch receipt and reuses these jobs.'}
            target=ROOT/'launch-all.json'
            if target.exists() and json.loads(target.read_text())!=evidence:
                raise ValueError('execution receipt conflict')
            if not target.exists():rt.write_json(target,evidence)
        return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--submit',action='store_true');g.add_argument('--test-only',action='store_true')
    a=p.parse_args();submit(a.test_only)
