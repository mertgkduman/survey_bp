"""Audit fixed matched depolarizing samples and compare all four codes."""
from array import array
from collections import defaultdict
import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from numba import njit
from scipy.stats import beta,binomtest

from study import (ROOT,REPO,source,vanilla,ARMS,FIELDS,implementation_hashes,policies,
                   graphs,decode,open_event_ledger)


@njit
def independent_syndrome(truth,xptr,xrows,zptr,zrows,mx,mz):
    result=np.zeros(mx+mz,dtype=np.uint8)
    for v in range(len(truth)):
        state=truth[v]
        if state==2 or state==3:
            for i in range(xptr[v],xptr[v+1]):result[xrows[i]]^=1
        if state==1 or state==2:
            for i in range(zptr[v],zptr[v+1]):result[mx+zrows[i]]^=1
    return result


def evaluator(code):
    indices=[]
    for h in (code.hx,code.hz):
        cols,rows=np.nonzero(h.T)
        ptr=np.r_[0,np.cumsum(np.bincount(cols,minlength=code.n))].astype(np.int64)
        indices.extend((ptr,rows.astype(np.int64)))
    return (*indices,code.hx.shape[0],code.hz.shape[0])


def signature_pair(code,pauli):
    bits=vanilla.PAULI_BITS[pauli]
    return tuple(((code.lz@bits[:,0])%2).tolist()),tuple(((code.lx@bits[:,1])%2).tolist())


def stats():
    return {'counts':{f:0 for f in FIELDS},'iterations':array('d'),'depth':array('H'),
            'elapsed_ns':array('Q'),'edge_updates':array('Q'),'evidence':set()}


def interval(k,n,alpha=.05):
    return (0.0 if k==0 else float(beta.ppf(alpha/2,k,n-k+1)),
            1.0 if k==n else float(beta.ppf(1-alpha/2,k+1,n-k)))


def verify_fixed_design(plan):
    """Check pilot exclusion and the independently frozen denominator rule."""
    if plan['stage']=='pilot':return
    pilot_path=ROOT/'pilot.json';pilot=json.loads(pilot_path.read_text())
    if plan['pilot_sha256']!=sha256(pilot_path.read_bytes()).hexdigest():raise ValueError('pilot plan changed')
    if {j['seed'] for j in pilot['jobs']} & {j['seed'] for j in plan['jobs']}:
        raise ValueError('pilot and follow-up share a seed namespace')
    receipts={(r['code'],r['p']):r for r in plan['sample_size_receipts']}
    observed=defaultdict(int)
    for j in plan['jobs']:observed[j['code'],j['p']]+=j['shots']
    if set(receipts)!=set(observed):raise ValueError('cohort receipts differ from executed points')
    for j in pilot['jobs']:
        key=j['code'],j['p'];s=json.loads((REPO/j['output']/'summary.json').read_text())
        k=min(s['counts'][a]['type_i']+s['counts'][a]['type_ii'] for a in ARMS)
        n=1000000 if k==0 else min(1000000,max(20000,int(np.ceil(400000/k))))
        if (receipts[key]['pilot_smaller_failure_count']!=k or receipts[key]['fixed_followup_shots']!=n
                or observed[key]!=n):raise ValueError('follow-up size differs from the prospective pilot rule')


def audit_plan(path,replay_stride=10007,wait=False):
    payload=path.read_bytes();plan=json.loads(payload)
    if plan['implementation_sha256']!=implementation_hashes():raise ValueError('implementation changed')
    verify_fixed_design(plan)
    cohorts=defaultdict(list)
    for j in plan['jobs']:cohorts[(j['code'],j['p'])].append(j)
    for key,jobs in cohorts.items():
        ordered=sorted(jobs,key=lambda j:j['start_shot'])
        if (ordered[0]['start_shot']!=0 or len({j['seed'] for j in jobs})!=1
                or any(a['start_shot']+a['shots']!=b['start_shot'] for a,b in zip(ordered,ordered[1:]))):
            raise ValueError('shard samples overlap or have a gap')
    result=defaultdict(lambda:defaultdict(stats));pairs=defaultdict(lambda:{'shots':0,'rescues':0,'losses':0})
    receipts=[];codes={c:source._code(c) for c in ('b1','c2')};graph_cache={}
    evals={c:evaluator(code) for c,code in codes.items()}
    for index,job in enumerate(plan['jobs']):
        key=(job['code'],job['p']);code=codes[job['code']];d=REPO/job['output']
        mp,sp=d/'manifest.json',d/'summary.json'
        while wait and (not sp.exists() or not (d/'compression.json').exists() or (d/'events.jsonl').exists()):
            print('Awaiting completed shard:',d.name,flush=True);time.sleep(30)
        m,s=json.loads(mp.read_text()),json.loads(sp.read_text())
        if (any(m[k]!=v for k,v in job.items()) or m['plan_sha256']!=sha256(payload).hexdigest()
                or m['implementation_sha256']!=plan['implementation_sha256'] or m['policies']!=policies()
                or m['code_semantic_sha256']!=source.RECEIPTS['codes'][job['code']]['semantic_sha256']
                or m['joint_prior']!=[1-job['p'],job['p']/3,job['p']/3,job['p']/3]
                or m['binary_marginals']!=[2*job['p']/3,2*job['p']/3]
                or s['manifest_sha256']!=sha256(mp.read_bytes()).hexdigest()
                or s['shots']!=job['shots'] or s['stop_reason']!='fixed_shots_complete'):
            raise ValueError(f'manifest mismatch: {d}')
        rng=np.random.Generator(np.random.PCG64(job['seed']));rng.bit_generator.advance(job['start_shot']*code.n)
        edge_counts={'binary_v2':[int(code.hz.sum()),int(code.hx.sum())],
                     'qbp_v2':[int(code.hx.sum()+code.hz.sum())]}
        totals={a:{f:0 for f in (*FIELDS,'iteration_sum','elapsed_ns_sum')} for a in ARMS}
        count=0;digest=sha256();replayed=0
        with open_event_ledger(d/'events.jsonl') as stream:
            for offset,raw in enumerate(stream):
                digest.update(raw);count+=1;e=json.loads(raw)
                truth=vanilla._sample(rng,code.n,job['p'])
                syndrome=independent_syndrome(truth,*evals[job['code']])
                if (e['schema']!='b1-c2-paired-depolarizing-shot-v1' or e['shot']!=job['start_shot']+offset
                        or e['error_sha256']!=sha256(truth.tobytes()).hexdigest()
                        or e['syndrome_sha256']!=sha256(syndrome.tobytes()).hexdigest() or set(e['arms'])!=set(ARMS)):
                    raise ValueError('sample hash/schema mismatch')
                for arm,rec in e['arms'].items():
                    if (sum(int(rec[f]) for f in FIELDS)!=1 or len(rec['iterations'])!=(2 if arm=='binary_v2' else 1)
                            or any(not 1<=i<=100 for i in rec['iterations'])):
                        raise ValueError('outcome partition or iteration count invalid')
                    for f in FIELDS:totals[arm][f]+=int(rec[f])
                    totals[arm]['iteration_sum']+=sum(rec['iterations']);totals[arm]['elapsed_ns_sum']+=rec['elapsed_ns']
                    if rec['exact_success'] and rec['candidate_sha256']!=sha256(truth.tobytes()).hexdigest():
                        raise ValueError('exact correction digest mismatch')
                    if offset%replay_stride==0 or offset==job['shots']-1 or rec['type_ii']:
                        if key not in graph_cache:graph_cache[key]=graphs(code,job['p'])
                        candidate,its,conv=decode(arm,graph_cache[key][arm],code,syndrome)
                        valid=bool(np.array_equal(independent_syndrome(candidate,*evals[job['code']]),syndrome))
                        logical=bool(valid and signature_pair(code,candidate)!=signature_pair(code,truth))
                        exact=bool(valid and not logical and np.array_equal(candidate,truth))
                        flags=(not valid,logical,exact,bool(valid and not logical and not exact))
                        if (rec['candidate_sha256']!=sha256(candidate.tobytes()).hexdigest() or its!=rec['iterations']
                                or tuple(rec[f] for f in FIELDS)!=flags or valid!=conv):
                            raise ValueError('candidate replay or independent logical outcome mismatch')
                        replayed+=1
                    acc=result[key][arm]
                    for f in FIELDS:acc['counts'][f]+=int(rec[f])
                    acc['iterations'].append(sum(rec['iterations'])/len(rec['iterations']))
                    acc['depth'].append(max(rec['iterations']));acc['elapsed_ns'].append(rec['elapsed_ns'])
                    acc['edge_updates'].append(2*sum(a*b for a,b in zip(edge_counts[arm],rec['iterations'],strict=True)))
                    acc['evidence'].add(str(sp.relative_to(REPO)))
                b,q=e['arms']['binary_v2'],e['arms']['qbp_v2']
                bf,qf=b['type_i'] or b['type_ii'],q['type_i'] or q['type_ii']
                pairs[key]['shots']+=1;pairs[key]['rescues']+=int(bf and not qf);pairs[key]['losses']+=int(qf and not bf)
        if count!=job['shots'] or digest.hexdigest()!=s['events_sha256'] or totals!=s['counts']:
            raise ValueError(f'ledger hash/count mismatch: {d}')
        receipts.append({'output':job['output'],'shots':count,'events_sha256':digest.hexdigest(),
                         'summary_sha256':sha256(sp.read_bytes()).hexdigest(),'candidate_replays':replayed})
        if (index+1)%10==0:print('Verified',index+1,'/',len(plan['jobs']),'shards',flush=True)
    return result,pairs,receipts


def performance_rows(data):
    rows=[]
    for (code,p),arms in sorted(data.items()):
        for arm,a in sorted(arms.items()):
            n=len(a['iterations']);k=a['counts']['type_i']+a['counts']['type_ii'];lo,hi=interval(k,n)
            rows.append({'code':code,'p':p,'channel':'depolarizing','decoder':arm,'T':100,
                'shots':n,'failures':k,**a['counts'],'rate':k/n,'ci95_low':lo,'ci95_high':hi,
                'zero_failure_upper_one_sided95':1-.05**(1/n) if k==0 else '',
                'precision':'100_or_more_failures' if k>=100 else 'zero_failure_bound' if k==0 else 'low_count_estimate',
                'mean_iterations_per_component':float(np.mean(a['iterations'])),
                'p99_iteration_depth':float(np.percentile(a['depth'],99,method='higher')),
                'mean_directed_edge_updates':float(np.mean(a['edge_updates'])),
                'mean_decode_ms':float(np.mean(a['elapsed_ns'])/1e6),
                'p99_decode_ms':float(np.percentile(a['elapsed_ns'],99,method='higher')/1e6),
                'evidence':';'.join(sorted(a['evidence']))})
    return rows


def pair_rows(data):
    rows=[]
    for (c,p),a in sorted(data.items()):
        n,r,l=a['shots'],a['rescues'],a['losses'];ll,lu=interval(l,n,.025);rl,ru=interval(r,n,.025)
        rows.append({'code':c,'p':p,'new':'qbp_v2','old':'binary_v2',**a,
                     'failure_difference_new_minus_old':(l-r)/n,'paired_ci95_low':ll-ru,'paired_ci95_high':lu-rl,
                     'mcnemar_exact_p':float(binomtest(r,r+l).pvalue) if r+l else 1.0})
    return rows


def inherited():
    base=ROOT.parent/'results';proof=json.loads((base/'audit.json').read_text())
    for name,key in [('performance.csv','performance_sha256'),('paired.csv','paired_sha256')]:
        if sha256((base/name).read_bytes()).hexdigest()!=proof[key]:raise ValueError('audited base artifact changed')
    rows=[]
    for x in csv.DictReader((base/'performance.csv').open()):
        if x['code'] not in ('a5','b2') or x['decoder']=='binary_paper':continue
        row={k:v for k,v in x.items() if k!='precision_100_failures'}
        for k in ['T','shots','failures',*FIELDS]:row[k]=int(row[k])
        for k in ['p','rate','ci95_low','ci95_high','mean_iterations_per_component','p99_iteration_depth',
                  'mean_directed_edge_updates','mean_decode_ms','p99_decode_ms']:row[k]=float(row[k])
        row['zero_failure_upper_one_sided95']='';row['precision']='100_or_more_failures';rows.append(row)
    return rows,proof


def write_csv(path,rows):
    with path.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def assess(*,wait=False):
    data,pairs,receipts=audit_plan(ROOT/'campaign.json',wait=wait)
    rows=performance_rows(data);pairdata=pair_rows(pairs);old,proof=inherited()
    allrows=sorted(rows+old,key=lambda r:(r['code'],r['p'],r['decoder']))
    results=ROOT/'results'
    for name,values in [('performance.csv',rows),('paired.csv',pairdata),('all_depolarizing.csv',allrows)]:
        write_csv(results/name,values)
    audit={'complete':len(data)==14,'code_rate_cells':len(data),'fixed_stage_shots':sum(a['shots'] for a in pairdata),
           'pilot_excluded':True,'precision_counts':{s:sum(r['precision']==s for r in rows) for s in
               ['100_or_more_failures','low_count_estimate','zero_failure_bound']},
           'base_audit':proof,'verified_shards':receipts,
           'artifact_sha256':{n:sha256((results/n).read_bytes()).hexdigest() for n in
                              ['performance.csv','paired.csv','all_depolarizing.csv']}}
    (results/'audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    render(allrows,pairdata)
    print('Completed all 14 fixed depolarizing points:',audit['precision_counts'],flush=True)


def render(rows,pairs):
    lookup={(r['code'],r['p'],r['decoder']):r for r in rows}
    lines=['# Plain BP and QBP under depolarizing noise','',
        'All four codes use the same independent code-capacity channel: P(I)=1-p and P(X)=P(Y)=P(Z)=p/3 on every qubit, with perfect syndrome measurements. Binary BP uses separate X/Z marginals 2p/3; QBP uses the joint Pauli prior. Both are plain, undamped float64 flooding sum-product v2 with T=100. B1/C2 depolarizing curves are new controlled results without paper reference points.','',
        'Both kernels start with the same scalar commuting/anticommuting edge LLR, $m_{v\\to c}^{(0)}=\\log[(1-2p/3)/(2p/3)]$. QBP subsequently combines both check types through one four-state qubit belief; separate binary BP retains only the two marginals. A performance difference under these settings therefore is not explained by using the physical p as a binary prior.','',
        'B1/C2 pilot shots choose a fresh fixed sample size and are excluded from every estimate. Fixed cohorts target 200 expected failures using the pilot, with 20,000 minimum and 1,000,000 maximum shots. Low-count estimates remain labeled; zero failures are reported as exact one-sided 95% upper bounds, not observed nonzero rates. A5/B2 points are inherited from the independently audited prior comparison.','',
        '| Code | p | Paired N | Binary BP failures (LER) | QBP failures (LER or 95% upper bound) | QBP precision |',
        '|---|---:|---:|---:|---:|---|']
    fig,axes=plt.subplots(2,4,figsize=(17,8),sharey='row',layout='constrained')
    fig.suptitle('Depolarizing noise: plain BP and QBP, T=100, float64, no damping',fontsize=14)
    for col,c in enumerate(('a5','b2','b1','c2')):
        ps=sorted({r['p'] for r in rows if r['code']==c})
        for arm,color,marker in [('binary_v2','#0072B2','s'),('qbp_v2','#9A348E','o')]:
            rr=[lookup[(c,p,arm)] for p in ps]
            positive=[r for r in rr if r['failures']>0]
            axes[0,col].plot(ps,[r['rate'] if r['failures'] else np.nan for r in rr],color=color,lw=1)
            axes[0,col].errorbar([r['p'] for r in positive],[r['rate'] for r in positive],
                yerr=[[r['rate']-r['ci95_low'] for r in positive],[r['ci95_high']-r['rate'] for r in positive]],
                fmt=marker,color=color,label='Binary BP v2' if arm=='binary_v2' else 'QBP v2',ms=4,capsize=2)
            for r in rr:
                if r['failures']==0:axes[0,col].plot(r['p'],r['zero_failure_upper_one_sided95'],'v',mfc='white',mec=color,ms=7)
            axes[1,col].plot(ps,[r['mean_iterations_per_component'] for r in rr],color=color,marker=marker,ms=4)
        code_info=source.RECEIPTS['codes'][c]
        axes[0,col].set(title=f"{c.upper()} [[{code_info['n']},{code_info['k']}]]",yscale='log',xlabel='Depolarizing probability p')
        axes[1,col].set(xlabel='Depolarizing probability p',ylabel='Mean iterations per component')
        axes[0,col].legend(fontsize=8)
        for ax in axes[:,col]:ax.grid(True,which='both',alpha=.2)
        for p in ps:
            b,q=lookup[(c,p,'binary_v2')],lookup[(c,p,'qbp_v2')]
            qrate=f"{q['failures']:,} ({q['rate']:.6g})" if q['failures'] else f"0 (<{q['zero_failure_upper_one_sided95']:.6g})"
            lines.append(f"| {c.upper()} | {p:.2f} | {q['shots']:,} | {b['failures']:,} ({b['rate']:.6g}) | {qrate} | {q['precision']} |")
    axes[0,0].set_ylabel('Block logical error rate; 95% interval')
    for suffix in ('png','pdf'):fig.savefig(ROOT/f'results/comparison.{suffix}',dpi=170)
    plt.close(fig)
    lines.extend(['','## Paired B1/C2 results','',
        '| Code | p | QBP rescues | QBP losses | Failure difference QBP−BP | Conservative paired 95% interval |',
        '|---|---:|---:|---:|---:|---:|'])
    for r in pairs:
        lines.append(f"| {r['code'].upper()} | {r['p']:.2f} | {r['rescues']} | {r['losses']} | {r['failure_difference_new_minus_old']:.6g} | [{r['paired_ci95_low']:.6g}, {r['paired_ci95_high']:.6g}] |")
    lines.extend(['','## Observed performance',''])
    for c in ('b1','c2'):
        ps=sorted({r['p'] for r in rows if r['code']==c})
        valid=[p for p in ps if lookup[(c,p,'qbp_v2')]['failures']>0]
        ratios=[lookup[(c,p,'binary_v2')]['rate']/lookup[(c,p,'qbp_v2')]['rate'] for p in valid]
        better=sum(lookup[(c,p,'qbp_v2')]['rate']<lookup[(c,p,'binary_v2')]['rate'] for p in ps)
        lines.append(f"On {c.upper()}, QBP has lower observed LER at {better}/{len(ps)} measured rates. Among points with nonzero QBP failures, the binary/QBP rate ratio spans {min(ratios):.2f}–{max(ratios):.2f}.")
        b,q=lookup[(c,.06,'binary_v2')],lookup[(c,.06,'qbp_v2')]
        lines.extend(['',f"At p=0.06, binary BP has {b['failures']}/{b['shots']:,} failures ({b['rate']:.6g}); QBP has {q['failures']}/{q['shots']:,} ({q['rate']:.6g}). Mean iterations per component are {b['mean_iterations_per_component']:.2f} and {q['mean_iterations_per_component']:.2f}, respectively; mean decoding times are {b['mean_decode_ms']:.3f} ms and {q['mean_decode_ms']:.3f} ms.",''])
    lines.extend(['','### Failure types at p=0.06','',
        '| Code | Paired N | BP Type I | BP Type II | QBP Type I | QBP Type II |',
        '|---|---:|---:|---:|---:|---:|'])
    for c in ('a5','b2','b1','c2'):
        b,q=lookup[(c,.06,'binary_v2')],lookup[(c,.06,'qbp_v2')]
        lines.append(f"| {c.upper()} | {b['shots']:,} | {b['type_i']} | {b['type_ii']} | {q['type_i']} | {q['type_ii']} |")
    lines.extend(['','## Channel comparison','',
        'The earlier B1/C2 X-only study has identical QBP/binary-v2 corrections because only I/X states have prior support. Depolarizing noise permits Y/Z and supplies within-qubit correlation to QBP. The numerical value of p has different marginal meaning between the two channels: binary X-flip probability is p in the X-only channel and 2p/3 in the depolarizing channel.','',
        '| Code | p | X-only binary/QBP LER | Depolarizing binary LER | Depolarizing QBP LER or upper bound |',
        '|---|---:|---:|---:|---:|'])
    old=list(csv.DictReader((ROOT.parent/'results/performance.csv').open()))
    xonly={(r['code'],float(r['p'])):float(r['rate']) for r in old if r['code'] in ('b1','c2') and r['decoder']=='qbp_v2'}
    for c in ('b1','c2'):
        for p in sorted({r['p'] for r in rows if r['code']==c}):
            b,q=lookup[(c,p,'binary_v2')],lookup[(c,p,'qbp_v2')]
            qtext=f"{q['rate']:.6g}" if q['failures'] else f"<{q['zero_failure_upper_one_sided95']:.6g}"
            lines.append(f"| {c.upper()} | {p:.2f} | {xonly[c,p]:.6g} | {b['rate']:.6g} | {qtext} |")
    lines.extend(['','## Evidence and interpretation','',
        'All physical draws, syndrome hashes, manifests, event hashes, counts and disjoint shard boundaries are independently verified. Boundary and fixed-stride corrections and all Type II events are replayed. The independent evaluator retains X/Z logical signatures separately, so logical Y errors cannot cancel. Syndrome-inconsistent outputs are Type I failures; syndrome-valid nontrivial logical residuals are Type II. Stabilizer-equivalent corrections count as successes; all samples enter the denominator.','',
        'Rates use fixed-N Clopper–Pearson 95% intervals. Zero-failure triangles show 1−0.05^(1/N). The paired failure-difference interval is formed from simultaneous 97.5% binomial intervals for rescues and losses, with exact McNemar test p-values in paired.csv. A p-value stored as 0 reflects floating-point underflow, not a mathematically zero probability. Low-count QBP points do not establish a precise rate or a measured error floor. No multiple-comparison adjustment is applied to this exploratory analysis.','',
        'Performance CSVs include mean iterations per component, p99 iteration depth, directed edge updates, and mean/p99 decoding time. Separate binary mean iterations are (I_X+I_Z)/2; depth is max(I_X,I_Z); directed work is twice the edge count per executed component sweep. This is not equal arithmetic cost per edge. Historical A5/B2 timings and new B1/C2 timings are from different campaigns.','',
        'Across-code LER differences also involve block length, dimension, Tanner graph and convergence within T=100. These are plain-decoder baselines at a shared iteration cap; comparisons of optimized codes or tuned decoders require their own controls. The paired BP/QBP contrast within a code holds its sampled physical errors fixed.','',
        'Files: [all four-code rates](all_depolarizing.csv), [new B1/C2 performance](performance.csv), [paired differences](paired.csv), [plot PNG](comparison.png), [plot PDF](comparison.pdf), [audit](audit.json).',''])
    (ROOT/'results/REPORT.md').write_text('\n'.join(lines))


def render_saved():
    results=ROOT/'results';proof=json.loads((results/'audit.json').read_text())
    for n,value in proof['artifact_sha256'].items():
        if sha256((results/n).read_bytes()).hexdigest()!=value:raise ValueError('audited artifact changed')
    rows=list(csv.DictReader((results/'all_depolarizing.csv').open()))
    pairs=list(csv.DictReader((results/'paired.csv').open()))
    ints={'T','shots','failures',*FIELDS,'rescues','losses'}
    strings={'code','channel','decoder','precision','evidence','new','old'}
    for row in rows+pairs:
        for k,v in row.items():
            if k not in strings and v!='':row[k]=int(v) if k in ints else float(v)
    render(rows,pairs)


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--wait',action='store_true');ap.add_argument('--render',action='store_true')
    args=ap.parse_args()
    render_saved() if args.render else assess(wait=args.wait)
