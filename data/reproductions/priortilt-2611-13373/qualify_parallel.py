"""Ten-process resource qualification on separate, full-budget pilot streams."""
import csv
import json
from pathlib import Path
import shutil
import tempfile
import numpy as np
import run
import parallel


def science(root,job,basis):
    records=[parallel.arrays(p) for p in sorted((root/'results'/job['id']/basis).glob('chunk-*.npz'))]
    return {k:np.concatenate([d[k] for d in records]) for k in ('candidate','prediction','stats','trace')}


def main():
    original=run.ROOT;plan=run.load();original_load=run.load;out=[]
    with tempfile.TemporaryDirectory(prefix='priortilt-ten-cpu-') as temp:
        temp=Path(temp)
        for code,method in [('BB144','priortilt'),('BB70','relay'),('GB102','beam')]:
            parent=next(j for j in plan['jobs'] if j['code']==code and j['method']==method and j['p']==max(x['p'] for x in plan['jobs'] if x['code']==code))
            local={**plan,'jobs':[parent],'protocol':{**plan['protocol'],'batch':8,'max_shots':80,'target_errors':20,'noise_seed':2026111791,'policy_seed':2026111792,'minimum_free_bytes':0}}
            seq=temp/(code+'-seq');par=temp/(code+'-par')
            for root in (seq,par):
                root.mkdir();(root/'circuits').symlink_to(original/'circuits',target_is_directory=True)
                for name in ('source.json','phase-schedules.json'):shutil.copy2(original/name,root/name)
                run.write_json(root/'plan.json',local);run.write_json(root/'resource-amendment.json',{'qualification_only':True})
            run.load=lambda:local;run.ROOT=seq;run.execute(0)
            saved={b:science(seq,parent,b) for b in run.BASES}
            dest=par/'results'/parent['id'];dest.mkdir(parents=True)
            shutil.copy2(seq/'results'/parent['id']/'manifest.json',dest/'manifest.json')
            (par/'results/noise').symlink_to(seq/'results/noise',target_is_directory=True)
            inherited={}
            for b in run.BASES:
                (dest/b).mkdir();first=sorted((seq/'results'/parent['id']/b).glob('chunk-*.json'))[0]
                for p in (first,first.with_suffix('.npz')):shutil.copy2(p,dest/b/p.name)
                inherited[b]=run.sha(dest/b/first.name)
            run.ROOT=par;parallel.execute(0,10);parallel.execute(0,10,audit=True)
            actual={b:science(par,parent,b) for b in run.BASES}
            for b in run.BASES:
                for k in saved[b]:np.testing.assert_array_equal(saved[b][k],actual[b][k])
                assert run.sha(sorted((dest/b).glob('chunk-*.json'))[0])==inherited[b]
            # A resumed parallel point consumes sealed stages and keeps its receipt identical.
            receipt=(dest/'complete.json').read_bytes();parallel.execute(0,10);parallel.execute(0,10,audit=True)
            assert receipt==(dest/'complete.json').read_bytes()
            out.append({'code':code,'method':method,'workers':10,'events':sum(len(v['candidate']) for v in actual.values()),
                        'science_arrays':'candidate,prediction,stats,trace bitwise equal to frozen sequential worker',
                        'inherited_markers':inherited,'full_fresh_process_audit':True,'resume_receipt_unchanged':True})
            print('QUALIFIED',code,method,flush=True)
    run.ROOT=original;run.load=original_load
    run.write_json(original/'parallel-qualification.json',{'controller':parallel.VERSION,'cases':out,'events':sum(x['events'] for x in out),
        'scope':'separate qualification seeds;10 spawned process workers, full paper budgets, inherited prefix, full audits, resume; timings excluded from bitwise comparison',
        'parent_plan_sha256':run.sha(original/'plan.json'),'parallel_source_sha256':run.sha(original/'parallel.py')})


if __name__=='__main__':main()
