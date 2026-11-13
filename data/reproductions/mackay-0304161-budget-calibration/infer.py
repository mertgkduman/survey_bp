"""Retrospective cutoff inference from retained outcomes, with short-only replays.

This is adaptive-bank calibration, not an independent curve reproduction.
"""
from collections import Counter
from hashlib import sha256
import gzip
import importlib.util
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
SOURCE=ROOT.with_name('mackay-0304161-paper-rates')
s=importlib.util.spec_from_file_location('_cutoff_source_runner',SOURCE/'run.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
LIMITS=(2,3,5,10,20,25,50,100,200,500,1000)


def selected(candidates,cap):
    valid=[(int(c.sum()),extra,c) for extra,(c,ok,it) in enumerate(candidates) if ok and it<=cap]
    return min(valid,key=lambda x:x[:2])[2] if valid else None


def infer():
    plan=m.load_plan();receipt=json.loads((SOURCE/'verified.json').read_text())
    by_id={r['id']:r for r in receipt['points']};rows=[];replays=[]
    for job in [j for j in m.jobs(plan) if j['code']=='unicycle274' and j['arm']=='unicycle_sp']:
        directory=SOURCE/'results'/job['id'];source=by_id[job['id']]
        state=m.decoder_state(job);_,n,packed,graph=state
        exact=Counter();errors={t:Counter() for t in LIMITS};digest=sha256();shots=0;replayed=0
        for path in sorted(directory.glob('shots-*.jsonl.gz')):
            with gzip.open(path,'rb') as stream:
                for line in stream:
                    digest.update(line);r=json.loads(line);assert r['shot']==shots;shots+=1
                    branches=r['branch_iterations'];positive=[i for i in branches if i>0]
                    if r['outcome']=='exact_success':
                        truth=None
                        if len(positive)==1:
                            correct=branches.index(positive[0]);convergence=positive[0]
                        elif len(set(positive))==1:
                            convergence=positive[0];correct=None
                        else:
                            truth=m.original.base._sample(job['seed'],round(job['physical_p']*100000),r['shot'],n,depolarizing=False)
                            assert sha256(truth.tobytes()).hexdigest()==r['error_sha256']
                            correct=int(truth[-1]);convergence=branches[correct]
                        assert convergence>0
                        exact[convergence]+=1
                        if convergence<=min(LIMITS):continue
                        other_time=branches[1-correct] if correct is not None else convergence
                        if other_time==0:
                            # Skipped full-budget competitor matters only before
                            # the successful branch first converges.
                            if truth is None:
                                truth=m.original.base._sample(job['seed'],round(job['physical_p']*100000),r['shot'],n,depolarizing=False)
                            syndrome=m.original.base._syndrome(packed[1],truth)
                            limit=min(max(LIMITS),convergence-1)
                            decoded=graph.run(syndrome^(1-correct),error_rate=job['physical_p'],max_iterations=limit)
                            other_time=decoded.iterations if decoded.converged else math.inf
                            replayed+=1
                            replays.append({'source':job['id'],'shot':r['shot'],'kind':'skipped_competitor_before_correct_convergence',
                                            'cap':limit,'iterations':decoded.iterations,'converged':decoded.converged,
                                            'candidate_sha256':sha256(decoded.candidate.tobytes()).hexdigest()})
                        for t in LIMITS:
                            if t<convergence:errors[t]['undetected' if 0<other_time<=t else 'detected']+=1
                    elif r['outcome']=='type_i':
                        for t in LIMITS:errors[t]['detected']+=1
                    else:
                        # Original valid wrong candidates can change selection at
                        # shorter caps; recover both independent first candidates.
                        truth=m.original.base._sample(job['seed'],round(job['physical_p']*100000),r['shot'],n,depolarizing=False)
                        assert sha256(truth.tobytes()).hexdigest()==r['error_sha256']
                        syndrome=m.original.base._syndrome(packed[1],truth);candidates=[]
                        for extra in (0,1):
                            decoded=graph.run(syndrome^extra,error_rate=job['physical_p'],max_iterations=max(LIMITS))
                            candidate=m.np.append(decoded.candidate,m.np.uint8(extra)).astype(m.np.uint8)
                            candidates.append((candidate,decoded.converged,decoded.iterations));replayed+=1
                            replays.append({'source':job['id'],'shot':r['shot'],'kind':'original_classical_error',
                                            'extra':extra,'cap':max(LIMITS),'iterations':decoded.iterations,
                                            'converged':decoded.converged,'candidate_sha256':sha256(candidate.tobytes()).hexdigest()})
                        for t in LIMITS:
                            candidate=selected(candidates,t)
                            if candidate is None:errors[t]['detected']+=1
                            elif not m.np.array_equal(candidate,truth):errors[t]['undetected']+=1
        assert shots==source['shots'] and digest.hexdigest()==source['ledger_sha256']
        targets=source['source_target']
        output={'p':job['physical_p'],'shots':shots,'source_ledger_sha256':digest.hexdigest(),
                'correct_first_convergence_histogram':dict(sorted(exact.items())),
                'actual_short_branch_replays':replayed,'paper_approx':targets,
                'cutoffs':[{'iterations_per_hypothesis':t,'total_controller_ceiling':2*t,
                            'detected':errors[t]['detected'],'undetected':errors[t]['undetected'],
                            'classical_errors':sum(errors[t].values()),'classical_rate':sum(errors[t].values())/shots,
                            'detected_rate':errors[t]['detected']/shots,'undetected_rate':errors[t]['undetected']/shots}
                           for t in LIMITS]}
        rows.append(output);print(json.dumps(output),flush=True)
    scores=[]
    for index,t in enumerate(LIMITS):
        score=sum(math.log(r['cutoffs'][index]['classical_rate']/r['paper_approx']['total_error_approx'])**2 for r in rows)
        scores.append({'iterations_per_hypothesis':t,'sum_squared_log_relative_total_error':score})
    result={'schema':'retrospective-unicycle-cutoff-inference-v1','status':'exploratory_retrospective_calibration',
            'source_receipt_sha256':m.sha(SOURCE/'verified.json'),'source_plan_sha256':m.sha(SOURCE/'plan.json'),
            'implementation_sha256':m.sha(Path(__file__)),
            'method':'Exact-success branches retain first convergence; before it no candidate with the wrong extra bit can equal the transmitted word. Original errors and skipped-competitor ambiguities are replayed only with shorter limits.',
            'sampling_caveat':'Original bank stopped at 20 large-budget quantum failures. These projected counts are descriptive; original stopping intervals cannot be transferred to a different cutoff.',
            'claim_limit':'Curve alignment may constrain but cannot identify an undocumented historical cap. New independent validation is required; no explicit paper-budget claim.',
            'rates':rows,'alignment_scores':scores,'replays':replays}
    m.write_json(ROOT/'inference.json',result)
    print(json.dumps({'alignment_scores':scores}),flush=True)
    return result

if __name__=='__main__':infer()
