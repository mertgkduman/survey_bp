"""One immutable, fixed-shot paired depolarizing shard."""
import argparse
from hashlib import sha256
import json
import platform
from pathlib import Path

import numpy as np
from study import (ROOT,REPO,source,vanilla,ARMS,FIELDS,policies,implementation_hashes,
                   graphs,record,decode,compress)


def run(plan_path,index):
    payload=plan_path.read_bytes();plan=json.loads(payload)
    if plan['implementation_sha256']!=implementation_hashes():raise ValueError('frozen implementation changed')
    job=plan['jobs'][index];p=job['p']
    if job['code'] not in ('b1','c2') or p not in [.04,.05,.06,.07,.08,.09,.10]:
        raise ValueError('unsupported code or p')
    output=REPO/job['output']
    if output.exists():raise FileExistsError(output)
    code=source._code(job['code']);evaluator=vanilla._syndrome_evaluator(code)
    gs=graphs(code,p);zero=np.zeros(code.hx.shape[0]+code.hz.shape[0],dtype=np.uint8)
    for a in ARMS:decode(a,gs[a],code,zero)
    manifest={'schema':'b1-c2-paired-depolarizing-run-v1',**job,'stage':plan['stage'],
              'plan_path':str(plan_path.relative_to(REPO)),'plan_sha256':sha256(payload).hexdigest(),
              'code_semantic_sha256':source.RECEIPTS['codes'][job['code']]['semantic_sha256'],
              'implementation_sha256':implementation_hashes(),'policies':policies(),
              'joint_prior':[1-p,p/3,p/3,p/3],'binary_marginals':[2*p/3,2*p/3],
              'host':platform.node(),'platform':platform.platform(),
              'rng':'PCG64(seed); exactly n draws per global shot; disjoint advance(start_shot*n)',
              'stop_rule':'fixed_shots','arm_timing_order':'rotate by global shot parity'}
    output.mkdir(parents=True)
    mp=output/'manifest.json';mp.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    counts={a:{f:0 for f in (*FIELDS,'iteration_sum','elapsed_ns_sum')} for a in ARMS}
    rng=np.random.Generator(np.random.PCG64(job['seed']))
    rng.bit_generator.advance(job['start_shot']*code.n)
    digest=sha256()
    with (output/'events.jsonl').open('x',buffering=1) as stream:
        for offset in range(job['shots']):
            shot=job['start_shot']+offset;truth=vanilla._sample(rng,code.n,p)
            syndrome=vanilla._original_syndrome(evaluator,truth)
            records={a:record(a,gs[a],code,evaluator,truth,syndrome) for a in (ARMS if shot%2==0 else ARMS[::-1])}
            for arm,rec in records.items():
                for f in FIELDS:counts[arm][f]+=int(rec[f])
                counts[arm]['iteration_sum']+=sum(rec['iterations'])
                counts[arm]['elapsed_ns_sum']+=rec['elapsed_ns']
            row={'schema':'b1-c2-paired-depolarizing-shot-v1','shot':shot,
                 'error_sha256':sha256(truth.tobytes()).hexdigest(),
                 'syndrome_sha256':sha256(syndrome.tobytes()).hexdigest(),'arms':records}
            line=json.dumps(row,sort_keys=True,separators=(',',':'))+'\n'
            stream.write(line);digest.update(line.encode())
            if (offset+1)%10000==0:print(job['code'],p,offset+1,{a:counts[a]['type_i']+counts[a]['type_ii'] for a in ARMS},flush=True)
    summary={'schema':'b1-c2-paired-depolarizing-summary-v1','shots':job['shots'],
             'counts':counts,'events_sha256':digest.hexdigest(),
             'manifest_sha256':sha256(mp.read_bytes()).hexdigest(),'stop_reason':'fixed_shots_complete'}
    (output/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    compress(output)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True)
    ap.add_argument('--index',type=int,required=True);a=ap.parse_args()
    run(a.plan.resolve(),a.index)
