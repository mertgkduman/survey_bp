"""Independent fixed two-arm B2 follow-up with separate logical signatures."""
import argparse
from hashlib import sha256
import json
import time
import platform

import numpy as np
from common import ROOT, REPO, source, vanilla, compress, source_hashes


def signature(code, pauli):
    b=vanilla.PAULI_BITS[pauli]
    return ((code.lz@b[:,0])%2).tobytes(), ((code.lx@b[:,1])%2).tobytes()


def run(index):
    pp=ROOT/'b2-p004-followup.json'
    plan=json.loads(pp.read_text());job=plan['jobs'][index]
    if (plan['implementation_sha256'] != source_hashes()
            or plan['runner_sha256'] != sha256(__file_path().read_bytes()).hexdigest()):
        raise ValueError('follow-up implementation changed')
    code=source._code('b2');ev=vanilla._syndrome_evaluator(code)
    allgraphs=vanilla._graphs(code,.04)
    graphs={'qbp_v2':allgraphs['bp4_v2'],'binary_v2':allgraphs['binary_v2']}
    zero=np.zeros(code.hx.shape[0]+code.hz.shape[0],dtype=np.uint8)
    graphs['qbp_v2'].run(zero,max_iterations=1)
    graphs['binary_v2'][0].run(zero[code.hx.shape[0]:],max_iterations=1)
    graphs['binary_v2'][1].run(zero[:code.hx.shape[0]],max_iterations=1)
    output=REPO/job['output']
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True)
    manifest={'schema':'yao-cross-depolarizing-v1',**job,'campaign_sha256':sha256(pp.read_bytes()).hexdigest(),
              'implementation_sha256':source_hashes(),'host':platform.node(),
              'max_iterations':100,'physical_noise':'depolarizing','binary_prior':2*.04/3,
              'qbp_prior':[.96,.04/3,.04/3,.04/3], 'logical_evaluator':'separate_X_Z_signatures',
              'stop_rule':'fixed_shots','arm_timing_order':'rotate with shot parity'}
    mp=output/'manifest.json';mp.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    fields=('type_i','type_ii','exact_success','stabilizer_success')
    totals={a:{f:0 for f in (*fields,'iteration_sum','elapsed_ns_sum')} for a in graphs}
    rng=np.random.Generator(np.random.PCG64(job['seed']))
    rng.bit_generator.advance(job['start_shot']*code.n)
    digest=sha256()
    with (output/'events.jsonl').open('x',buffering=1) as stream:
        for offset in range(job['shots']):
            shot=job['start_shot']+offset
            truth=vanilla._sample(rng,code.n,.04);s=vanilla._original_syndrome(ev,truth)
            truthsig=signature(code,truth);records={}
            for arm in (('qbp_v2','binary_v2') if shot%2==0 else ('binary_v2','qbp_v2')):
                begin=time.perf_counter_ns()
                if arm=='qbp_v2':
                    r=graphs[arm].run(s,max_iterations=100)
                    candidate=r.candidate;its=[r.iterations];converged=r.converged
                else:
                    x=graphs[arm][0].run(s[code.hx.shape[0]:],max_iterations=100)
                    z=graphs[arm][1].run(s[:code.hx.shape[0]],max_iterations=100)
                    candidate=vanilla.BITS_TO_PAULI[x.candidate,z.candidate]
                    its=[x.iterations,z.iterations];converged=x.converged and z.converged
                elapsed=time.perf_counter_ns()-begin
                valid=bool(np.array_equal(vanilla._original_syndrome(ev,candidate),s))
                if valid!=converged:raise ValueError('syndrome mismatch')
                logical=valid and signature(code,candidate)!=truthsig
                exact=bool(valid and not logical and np.array_equal(candidate,truth))
                rec={'type_i':not valid,'type_ii':logical,'exact_success':exact,
                     'stabilizer_success':bool(valid and not logical and not exact),'iterations':its,
                     'elapsed_ns':elapsed,'candidate_sha256':sha256(candidate.tobytes()).hexdigest()}
                records[arm]=rec
                for f in fields:totals[arm][f]+=int(rec[f])
                totals[arm]['iteration_sum']+=sum(its);totals[arm]['elapsed_ns_sum']+=elapsed
            row={'schema':'yao-cross-depolarizing-shot-v1','shot':shot,
                 'error_sha256':sha256(truth.tobytes()).hexdigest(),'arms':records}
            line=json.dumps(row,sort_keys=True,separators=(',',':'))+'\n'
            stream.write(line);digest.update(line.encode())
            if (offset+1)%10000==0:print(index,offset+1,{a:t['type_i']+t['type_ii'] for a,t in totals.items()},flush=True)
    summary={'shots':job['shots'],'counts':totals,'stop_reason':'fixed_shots_complete',
             'manifest_sha256':sha256(mp.read_bytes()).hexdigest(),'events_sha256':digest.hexdigest()}
    (output/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    compress(output)


def __file_path():
    from pathlib import Path
    return Path(__file__)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--index',type=int,required=True)
    run(ap.parse_args().index)
