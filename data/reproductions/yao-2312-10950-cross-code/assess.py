"""Independent ledger and logical-outcome audit for the cross-code baselines."""
from collections import defaultdict
import csv
from hashlib import sha256
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta, binomtest

from common import (ROOT, REPO, SOURCE_ROOT, VANILLA_ROOT, ARMS, FIELDS, source, vanilla,
                    bit_flip_graphs, sample, one_arm, open_event_ledger, source_hashes)


def interval(k, n, alpha=.05):
    return (0.0 if k == 0 else float(beta.ppf(alpha/2, k, n-k+1)),
            1.0 if k == n else float(beta.ppf(1-alpha/2, k+1, n-k)))


def signature_pair(code, paulis):
    """Keep logical X and Z syndromes distinct, including logical Y errors."""
    bits = vanilla.PAULI_BITS[paulis]
    return (tuple(((code.lz @ bits[:, 0]) % 2).tolist()),
            tuple(((code.lx @ bits[:, 1]) % 2).tolist()))


def accumulator():
    return {'counts': {f:0 for f in FIELDS}, 'iterations': [], 'depth': [],
            'elapsed_ns': [], 'edge_updates': [], 'evidence': set()}


def add(stats, record, edge_counts, evidence):
    its = record['iterations']
    if isinstance(its, int):
        its = [its]
    for f in FIELDS:
        stats['counts'][f] += int(record[f])
    stats['iterations'].append(sum(its)/len(its))
    stats['depth'].append(max(its))
    stats['elapsed_ns'].append(record['elapsed_ns'])
    stats['edge_updates'].append(2*sum(e*i for e,i in zip(edge_counts, its, strict=True)))
    stats['evidence'].add(str(evidence.relative_to(REPO)))


def pair_update(pairs, a, b, ra, rb):
    key = (a,b)
    pairs[key]['shots'] += 1
    af, bf = ra['type_i'] or ra['type_ii'], rb['type_i'] or rb['type_ii']
    pairs[key]['rescues'] += int(bf and not af)
    pairs[key]['losses'] += int(af and not bf)
    pairs[key]['candidate_differences'] += int(
        ra.get('candidate_sha256', ra.get('candidate_digest')) !=
        rb.get('candidate_sha256', rb.get('candidate_digest')))


def audit_legacy(plan, aggregates, paired, audits):
    original_path = REPO / plan['reused_vanilla_campaign']
    if sha256(original_path.read_bytes()).hexdigest() != plan['reused_vanilla_campaign_sha256']:
        raise ValueError('historical campaign changed')
    original = json.loads(original_path.read_text())
    tasks = [{**j, 'output': str((VANILLA_ROOT/j['output']).relative_to(REPO)),
              'campaign_sha256': plan['reused_vanilla_campaign_sha256']} for j in original['tasks']]
    if (ROOT/'b2-p004-followup.json').exists():
        tasks = [t for t in tasks if (t['code'],t['p']) != ('b2',.04)]
    # A fresh independently fixed follow-up replaces the old B2 p=.05 cohort.
    # The p=.04 follow-up hit its wall limit and has no complete summary;
    # its interrupted prefix is deliberately excluded.
    follow_path = REPO / plan['reused_b2_followup_plan']
    if sha256(follow_path.read_bytes()).hexdigest() != plan['reused_b2_followup_plan_sha256']:
        raise ValueError('follow-up plan changed')
    follow = json.loads(follow_path.read_text())
    for job in follow['jobs']:
        if job['p'] == .05:
            tasks = [t for t in tasks if (t['code'],t['p']) != (job['code'],job['p'])]
            tasks.append({**job, 'shots': job['fixed_shots'], 'campaign_sha256': None})
    codes = {c: source._code(c) for c in ('a5','b2')}
    graphs_by_key = {}
    specs = vanilla._decoder_specs()
    for task in tasks:
        key = (task['code'],task['p'])
        code = codes[task['code']]
        directory = REPO/task['output']
        mp, sp = directory/'manifest.json', directory/'summary.json'
        manifest, summary = json.loads(mp.read_text()), json.loads(sp.read_text())
        if (summary['manifest_sha256'] != sha256(mp.read_bytes()).hexdigest()
                or manifest['campaign_sha256'] != task['campaign_sha256']
                or manifest['decoder_specs'] != specs
                or summary['stop_reason'] != 'fixed_shard_complete'
                or summary['shots'] != task['shots']):
            raise ValueError(f'bad historical manifest: {directory}')
        for name, value in [('code', task['code']), ('physical_p',task['p']), ('seed',task['seed']),
                            ('start_shot',task['start_shot']), ('max_shots',task['shots'])]:
            if manifest[name] != value:
                raise ValueError(f'bad historical {name}: {directory}')
        if manifest['code_semantic_sha256'] != source.RECEIPTS['codes'][task['code']]['semantic_sha256']:
            raise ValueError('historical code mismatch')
        raw_counts = {a:{f:0 for f in (*FIELDS,'iteration_sum','elapsed_ns_sum')} for a in vanilla.ARMS}
        digest = sha256()
        rng = np.random.Generator(np.random.PCG64(task['seed']))
        rng.bit_generator.advance(task['start_shot']*code.n)
        count = 0
        with open_event_ledger(directory/'events.jsonl') as stream:
            for offset, raw in enumerate(stream):
                digest.update(raw)
                event = json.loads(raw)
                shot = task['start_shot']+offset
                truth = vanilla._sample(rng, code.n, task['p'])
                if (event['shot'] != shot or event['schema'] != 'yao-vanilla-shot-v1'
                        or event['error_sha256'] != sha256(truth.tobytes()).hexdigest()):
                    raise ValueError('historical sample mismatch')
                if set(event['arms']) != set(vanilla.ARMS):
                    raise ValueError('historical arms mismatch')
                records = {}
                for arm, record in event['arms'].items():
                    if sum(int(record[f]) for f in FIELDS) != 1:
                        raise ValueError('historical outcome partition')
                    for f in FIELDS:
                        raw_counts[arm][f] += int(record[f])
                    raw_counts[arm]['iteration_sum'] += sum(record['iterations'])
                    raw_counts[arm]['elapsed_ns_sum'] += record['elapsed_ns']
                    if arm not in ('bp4_v2','binary_v2'):
                        continue
                    rec = dict(record)
                    if rec['exact_success']:
                        if rec['candidate_digest'] != sha256(truth.tobytes()).hexdigest()[:20]:
                            raise ValueError('exact correction digest mismatch')
                    if rec['stabilizer_success'] or rec['type_ii']:
                        # Only nonexact converged shots can hide a logical Y
                        # through the legacy XOR-combined logical signature.
                        if key not in graphs_by_key:
                            graphs_by_key[key] = vanilla._graphs(code, task['p'])
                        graph = graphs_by_key[key][arm]
                        ev = vanilla._syndrome_evaluator(code)
                        syndrome = vanilla._original_syndrome(ev, truth)
                        if arm == 'bp4_v2':
                            result = graph.run(syndrome, max_iterations=100)
                            candidate = result.candidate
                        else:
                            xr = graph[0].run(syndrome[code.hx.shape[0]:], max_iterations=100)
                            zr = graph[1].run(syndrome[:code.hx.shape[0]], max_iterations=100)
                            candidate = vanilla.BITS_TO_PAULI[xr.candidate,zr.candidate]
                        if sha256(candidate.tobytes()).hexdigest()[:20] != rec['candidate_digest']:
                            raise ValueError('historical candidate cannot be replayed')
                        if not np.array_equal(vanilla._original_syndrome(ev,candidate),syndrome):
                            raise ValueError('historical candidate syndrome mismatch')
                        logical = signature_pair(code,candidate) != signature_pair(code,truth)
                        audits.append({'evidence':str(sp.relative_to(REPO)), 'shot':shot, 'arm':arm,
                                       'candidate_sha256':sha256(candidate.tobytes()).hexdigest(),
                                       'legacy_type_ii':rec['type_ii'], 'independent_type_ii':logical})
                        rec['type_ii'],rec['stabilizer_success'] = logical,not logical
                    name = 'qbp_v2' if arm == 'bp4_v2' else arm
                    edges = [int(code.hx.sum()+code.hz.sum())] if arm == 'bp4_v2' else [int(code.hz.sum()),int(code.hx.sum())]
                    add(aggregates[key][name], rec, edges, sp)
                    records[name] = rec
                pair_update(paired[key], 'qbp_v2','binary_v2',records['qbp_v2'],records['binary_v2'])
                count += 1
        if (count != task['shots'] or digest.hexdigest() != summary['events_sha256']
                or raw_counts != summary['counts']):
            raise ValueError(f'historical ledger aggregates differ: {directory}')
    return len(tasks)


def audit_depolarizing(aggregates,paired):
    pp=ROOT/'b2-p004-followup.json';plan=json.loads(pp.read_text())
    if (plan['implementation_sha256'] != source_hashes()
            or plan['runner_sha256'] != sha256((ROOT/'run_depolarizing.py').read_bytes()).hexdigest()):
        raise ValueError('independent follow-up implementation mismatch')
    code=source._code('b2');ev=vanilla._syndrome_evaluator(code)
    graphs=vanilla._graphs(code,.04)
    for job in plan['jobs']:
        d=REPO/job['output'];mp=d/'manifest.json';sp=d/'summary.json'
        m,s=json.loads(mp.read_text()),json.loads(sp.read_text())
        if (m['campaign_sha256']!=sha256(pp.read_bytes()).hexdigest()
                or s['manifest_sha256']!=sha256(mp.read_bytes()).hexdigest()
                or m['implementation_sha256']!=plan['implementation_sha256']
                or any(m[k]!=v for k,v in job.items()) or s['shots']!=job['shots']
                or s['stop_reason']!='fixed_shots_complete'):
            raise ValueError('independent follow-up manifest mismatch')
        totals={a:{f:0 for f in (*FIELDS,'iteration_sum','elapsed_ns_sum')} for a in ('qbp_v2','binary_v2')}
        rng=np.random.Generator(np.random.PCG64(job['seed']))
        rng.bit_generator.advance(job['start_shot']*code.n)
        digest,count=sha256(),0
        with open_event_ledger(d/'events.jsonl') as stream:
            for offset,raw in enumerate(stream):
                count+=1;digest.update(raw);e=json.loads(raw)
                truth=vanilla._sample(rng,code.n,.04)
                if (e['shot']!=job['start_shot']+offset or e['schema']!='yao-cross-depolarizing-shot-v1'
                        or e['error_sha256']!=sha256(truth.tobytes()).hexdigest()
                        or set(e['arms'])!=set(totals)):
                    raise ValueError('independent follow-up sample mismatch')
                for arm,rec in e['arms'].items():
                    if sum(int(rec[f]) for f in FIELDS)!=1:
                        raise ValueError('independent follow-up partition mismatch')
                    for f in FIELDS:totals[arm][f]+=int(rec[f])
                    totals[arm]['iteration_sum']+=sum(rec['iterations'])
                    totals[arm]['elapsed_ns_sum']+=rec['elapsed_ns']
                    if rec['exact_success'] and rec['candidate_sha256']!=sha256(truth.tobytes()).hexdigest():
                        raise ValueError('independent follow-up exact-correction mismatch')
                    if offset%997==0 or offset==job['shots']-1 or rec['stabilizer_success'] or rec['type_ii']:
                        syn=vanilla._original_syndrome(ev,truth)
                        if arm=='qbp_v2':
                            candidate=graphs['bp4_v2'].run(syn,max_iterations=100).candidate
                        else:
                            x=graphs['binary_v2'][0].run(syn[code.hx.shape[0]:],max_iterations=100)
                            z=graphs['binary_v2'][1].run(syn[:code.hx.shape[0]],max_iterations=100)
                            candidate=vanilla.BITS_TO_PAULI[x.candidate,z.candidate]
                        valid=bool(np.array_equal(vanilla._original_syndrome(ev,candidate),syn))
                        logical=bool(valid and signature_pair(code,candidate)!=signature_pair(code,truth))
                        if (sha256(candidate.tobytes()).hexdigest()!=rec['candidate_sha256']
                                or logical!=rec['type_ii'] or (not valid)!=rec['type_i']):
                            raise ValueError('independent follow-up replay mismatch')
                    edges=[int(code.hx.sum()+code.hz.sum())] if arm=='qbp_v2' else [int(code.hz.sum()),int(code.hx.sum())]
                    add(aggregates[('b2',.04)][arm],rec,edges,sp)
                pair_update(paired[('b2',.04)],'qbp_v2','binary_v2',e['arms']['qbp_v2'],e['arms']['binary_v2'])
        if count!=job['shots'] or digest.hexdigest()!=s['events_sha256'] or totals!=s['counts']:
            raise ValueError('independent follow-up aggregate mismatch')


def audit_new(plan, aggregates, paired):
    if plan['implementation_sha256'] != source_hashes():
        raise ValueError('new campaign implementation changed')
    campaign_hash = sha256((ROOT/'campaign.json').read_bytes()).hexdigest()
    codes = {c:source._code(c) for c in ('b1','c2')}
    for job in plan['jobs']:
        key = (job['code'],job['p'])
        code = codes[job['code']]
        directory = REPO/job['output']
        mp,sp = directory/'manifest.json',directory/'summary.json'
        manifest,summary = json.loads(mp.read_text()),json.loads(sp.read_text())
        if (summary['manifest_sha256'] != sha256(mp.read_bytes()).hexdigest()
                or manifest['campaign_sha256'] != campaign_hash
                or manifest['implementation_sha256'] != plan['implementation_sha256']
                or summary['shots'] != job['shots'] or summary['stop_reason'] != 'fixed_shots_complete'
                or any(manifest[k] != v for k,v in job.items())):
            raise ValueError('new campaign manifest mismatch')
        totals = {a:{f:0 for f in (*FIELDS,'iterations','elapsed_ns')} for a in ARMS}
        graphs,guard = bit_flip_graphs(code,job['p'])
        if manifest['excluded_state_guard'] != guard:
            raise ValueError('support guard changed')
        ev = vanilla._syndrome_evaluator(code)
        digest,count = sha256(),0
        with open_event_ledger(directory/'events.jsonl') as stream:
            for shot,raw in enumerate(stream):
                count += 1
                digest.update(raw)
                event=json.loads(raw)
                truth=sample(job['seed'],code,job['p'],shot)
                s=vanilla._original_syndrome(ev,truth)
                if (event['shot'] != shot or event['schema'] != 'yao-cross-code-shot-v1'
                        or event['error_sha256'] != sha256(truth.tobytes()).hexdigest()
                        or event['syndrome_sha256'] != sha256(s.tobytes()).hexdigest()
                        or set(event['arms']) != set(ARMS)):
                    raise ValueError('new sample/arm mismatch')
                for arm,rec in event['arms'].items():
                    if sum(int(rec[f]) for f in FIELDS) != 1 or not 1 <= rec['iterations'] <= 100:
                        raise ValueError('new outcome or iteration invalid')
                    for f in totals[arm]:
                        totals[arm][f] += int(rec[f])
                    # Replay fixed boundary/stride shots, not a chosen outcome.
                    if shot in (0,job['shots']-1) or shot%997 == 0:
                        r=one_arm(arm,graphs[arm],code,job['p'],s)
                        if (sha256(r.candidate.tobytes()).hexdigest() != rec['candidate_sha256']
                                or r.iterations != rec['iterations']):
                            raise ValueError('new candidate replay mismatch')
                        valid=np.array_equal(vanilla._original_syndrome(ev,r.candidate),s)
                        logical=bool(valid and signature_pair(code,r.candidate) != signature_pair(code,truth))
                        exact=bool(valid and not logical and np.array_equal(r.candidate,truth))
                        flags=(not valid,logical,exact,bool(valid and not logical and not exact))
                        if tuple(rec[f] for f in FIELDS) != flags:
                            raise ValueError('independent outcome replay mismatch')
                    edges=[int(code.hx.sum()+code.hz.sum()) if arm=='qbp_v2' else int(code.hz.sum())]
                    add(aggregates[key][arm],rec,edges,sp)
                for other in ('binary_v2','binary_paper'):
                    pair_update(paired[key],'qbp_v2',other,event['arms']['qbp_v2'],event['arms'][other])
        if count != job['shots'] or digest.hexdigest()!=summary['events_sha256'] or totals!=summary['counts']:
            raise ValueError('new ledger aggregate mismatch')


def write():
    plan=json.loads((ROOT/'campaign.json').read_text())
    aggregates=defaultdict(lambda:defaultdict(accumulator))
    paired=defaultdict(lambda:defaultdict(lambda:{'shots':0,'rescues':0,'losses':0,'candidate_differences':0}))
    audits=[]
    legacy_shards=audit_legacy(plan,aggregates,paired,audits)
    audit_depolarizing(aggregates,paired)
    audit_new(plan,aggregates,paired)
    results=ROOT/'results'
    rows=[]
    for (code,p),arms in sorted(aggregates.items()):
        for arm,data in sorted(arms.items()):
            n=len(data['iterations'])
            k=data['counts']['type_i']+data['counts']['type_ii']
            lo,hi=interval(k,n)
            rows.append({'code':code,'p':p,'channel':'X_only' if code in ('b1','c2') else 'depolarizing',
                'decoder':arm,'T':100,'shots':n,'failures':k,**data['counts'],'rate':k/n,
                'ci95_low':lo,'ci95_high':hi,'precision_100_failures':k>=100,
                'mean_iterations_per_component':float(np.mean(data['iterations'])),
                'p99_iteration_depth':float(np.percentile(data['depth'],99,method='higher')),
                'mean_directed_edge_updates':float(np.mean(data['edge_updates'])),
                'mean_decode_ms':float(np.mean(data['elapsed_ns'])/1e6),
                'p99_decode_ms':float(np.percentile(data['elapsed_ns'],99,method='higher')/1e6),
                'evidence':';'.join(sorted(data['evidence']))})
    pairs=[]
    for (code,p),comparisons in sorted(paired.items()):
        for (new,old),counts in comparisons.items():
            n,r,l=counts['shots'],counts['rescues'],counts['losses']
            ll,lu=interval(l,n,alpha=.025)
            rl,ru=interval(r,n,alpha=.025)
            pairs.append({'code':code,'p':p,'new':new,'old':old,**counts,
                          'failure_difference_new_minus_old':(l-r)/n,
                          'paired_ci95_low':ll-ru,'paired_ci95_high':lu-rl,
                          'mcnemar_exact_p':float(binomtest(r,r+l).pvalue) if r+l else 1.0})
    for name,contents in [('performance.csv',rows),('paired.csv',pairs)]:
        with (results/name).open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(contents[0]))
            writer.writeheader();writer.writerows(contents)
    (results/'logical-outcome-audit.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in audits))
    (results/'audit.json').write_text(json.dumps({'complete':len(aggregates)==28,'code_rate_cells':len(aggregates),
        'legacy_shards_verified':legacy_shards,'nonexact_converged_legacy_candidates_replayed':len(audits),
        'logical_outcomes_corrected':sum(r['legacy_type_ii']!=r['independent_type_ii'] for r in audits),
        'campaign_sha256':sha256((ROOT/'campaign.json').read_bytes()).hexdigest(),
        'performance_sha256':sha256((results/'performance.csv').read_bytes()).hexdigest()},indent=2)+'\n')
    make_report(rows,pairs,audits)
    print('Verified',len(aggregates),'cells;',len(audits),'nonexact legacy replays;',
          sum(r['legacy_type_ii']!=r['independent_type_ii'] for r in audits),'logical classifications corrected')


def make_report(rows,pairs,audits):
    lookup={(r['code'],r['p'],r['decoder']):r for r in rows}
    pair_lookup={(r['code'],r['p'],r['old']):r for r in pairs}
    src=source.SOURCE['figures']
    fig,axes=plt.subplots(2,4,figsize=(17,8),layout='constrained')
    lines=['# Plain BP and QBP across four codes','',
        'All plain decoders use flooding sum-product, float64, no damping, and T=100, matching the plain decoder limit for each code in [Yao et al.](https://arxiv.org/pdf/2312.10950v2). Each local comparison uses the same physical errors. These added baselines are controlled experiments; the paper supplies no reference curve for the missing decoder/code combinations.','',
        'A5/B2 retain depolarizing noise, with separate binary priors q_X=q_Z=2p/3 and joint QBP priors (1-p,p/3,p/3,p/3). B1/C2 retain X-only noise, with QBP prior (1-p,p,0,0); they do not use a depolarizing prior. The full quaternary graph is executed. Excluded Y/Z coordinates are held more than 1024 log units below the I/X states by a degree-based guard, so their float64 projection mass is exactly zero. Under this channel the active QBP equations reduce to binary BP; any measured difference comes from numerical details, hard-decision ties, or message clipping.','',
        'A5/B2 use independently audited fixed-shot paired v2 results from the earlier vanilla campaign. The completed independent B2 p=0.05 follow-up replaces its first lower-count cohort. A new independently fixed 500,000-shot two-arm B2 p=0.04 campaign replaces its original 92-failure QBP cohort; the interrupted earlier four-arm follow-up is excluded. B1/C2 use the new prespecified fixed-shot paired campaign. All shots, including zero syndromes and nonconvergence, enter the denominator. Type I is syndrome-inconsistent failure; Type II is a syndrome-valid logical failure. Stabilizer-equivalent corrections count as success.','',
        '## Logical error rates','',
        '| Code | Channel | p | N paired | BP failures (rate) | QBP failures (rate) | BP/QBP LER | QBP rescues/losses | Existing paper curve |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for col,(code,figure) in enumerate([('a5','7'),('b2','8'),('b1','4'),('c2','5')]):
        ps=sorted({r['p'] for r in rows if r['code']==code})
        for arm,color,marker in [('binary_v2','#0072B2','s'),('qbp_v2','#9A348E','o')]:
            rr=[lookup[(code,p,arm)] for p in ps]
            axes[0,col].errorbar(ps,[r['rate'] for r in rr],
                yerr=[[r['rate']-r['ci95_low'] for r in rr],[r['ci95_high']-r['rate'] for r in rr]],
                label='BP v2' if arm=='binary_v2' else 'QBP v2',color=color,marker=marker,ms=4,lw=1,capsize=2)
            axes[1,col].plot(ps,[r['mean_iterations_per_component'] for r in rr],color=color,marker=marker,ms=4,label=arm)
        curve='bp' if code in ('b1','c2') else 'qbp'
        published=src[figure]['curves'][curve]
        axes[0,col].plot(ps,[published[f'{p:.5f}'] for p in ps],'k--',lw=1,label=f'Paper {curve.upper()}')
        axes[0,col].set(title=code.upper(),yscale='log',xlabel='X-flip probability p' if code in ('b1','c2') else 'Depolarizing probability p')
        axes[1,col].set(xlabel='Physical probability p',ylabel='Mean iterations per component')
        for ax in axes[:,col]:ax.grid(True,which='both',alpha=.2)
        axes[0,col].legend(fontsize=8)
        for p in ps:
            b,q=lookup[(code,p,'binary_v2')],lookup[(code,p,'qbp_v2')]
            pair=pair_lookup[(code,p,'binary_v2')]
            lines.append(f"| {code.upper()} | {b['channel']} | {p:.2f} | {b['shots']:,} | {b['failures']:,} ({b['rate']:.6g}) | {q['failures']:,} ({q['rate']:.6g}) | {b['rate']/q['rate']:.3g} | {pair['rescues']}/{pair['losses']} | {curve.upper()}={published[f'{p:.5f}']:.6g} |")
    axes[0,0].set_ylabel('Block logical error rate; 95% interval')
    fig.savefig(ROOT/'results/comparison.png',dpi=170)
    fig.savefig(ROOT/'results/comparison.pdf')
    plt.close(fig)
    lines.extend(['','## X-only numerical controls','',
        'The paper-style binary control clips outgoing V2C messages to ±25 and selects X on an exact zero belief. Binary v2 leaves V2C unbounded and selects I on an exact zero belief. QBP v2 leaves its state coordinates unbounded and selects X on an I/X tie under X-only support. Both v2 kernels apply the same tanh-product check rule and endpoint safeguard. No tuning or decimation is used.','',
        '| Code | p | Paper BP failures | Binary v2 failures | QBP v2 failures | QBP vs binary v2 candidate differences | QBP vs paper BP rescues/losses |',
        '|---|---:|---:|---:|---:|---:|---:|'])
    for code in ('b1','c2'):
        for p in sorted({r['p'] for r in rows if r['code']==code}):
            b,q,old=[lookup[(code,p,a)] for a in ('binary_v2','qbp_v2','binary_paper')]
            pv=pair_lookup[(code,p,'binary_v2')];po=pair_lookup[(code,p,'binary_paper')]
            lines.append(f"| {code.upper()} | {p:.2f} | {old['failures']} | {b['failures']} | {q['failures']} | {pv['candidate_differences']} | {po['rescues']}/{po['losses']} |")
    corrections=sum(r['legacy_type_ii']!=r['independent_type_ii'] for r in audits)
    lines.extend(['','## Audit and interpretation','',
        f'The historical evaluator XOR-combined X and Z logical signatures. A simultaneous identical nonzero X/Z signature can cancel under that expression. This assessment keeps both signatures separately and replays every retained nonexact converged A5/B2 v2 correction: {len(audits):,} candidates audited, {corrections} logical classifications corrected. Raw historical ledgers remain immutable; the replay evidence is [logical-outcome-audit.jsonl](logical-outcome-audit.jsonl). Exact-success hashes, all sampled-error hashes, outcome counts, ledger SHA-256 values, and manifest identities are independently checked. New fixed-stride and boundary shots are replayed through all three kernels with the separate-signature evaluator.','',
        'Each rate has a fixed-N Clopper–Pearson 95% interval in [performance.csv](performance.csv). [paired.csv](paired.csv) reports QBP rescues (BP fails, QBP succeeds), losses (QBP fails, BP succeeds), exact McNemar p-values and conservative paired difference intervals formed from simultaneous 97.5% binomial intervals for the two discordant probabilities. Comparisons are exploratory; p-values are not adjusted across p or code.','',
        'The independent B2 p=0.04 follow-up was sized after inspecting the original pilot, and only its fresh fixed sample enters this comparison. Its ten 50,000-shot shards were frozen together; the assessor rejects incomplete stages and verifies all sample indices. This cross-code study does not close the unfinished earlier BP/BPGD rare-event reproduction task.','',
        'Iteration depth for separate binary decoding is max(I_X,I_Z), while mean iterations per component is (I_X+I_Z)/2. Directed edge updates count 2E per executed component sweep; QBP has more arithmetic per edge, so these counts are not flop equivalence. The CSV includes mean edge updates, p99 iteration depth, mean decoding time and p99 decoding time. A5/B2 timings were measured in the historical four-arm run, whereas B1/C2 timings rotate arm order on the same host. Runtime ratios across those campaigns are not controlled speed comparisons. The X-only QBP graph also processes X checks that add no inference information.','',
        'The two channels differ across code groups. A5/B2 versus B1/C2 LER is not an isolated comparison of code quality.','',
        'Artifacts: [performance.csv](performance.csv), [paired.csv](paired.csv), [comparison.png](comparison.png), [comparison.pdf](comparison.pdf), [audit.json](audit.json).',''])
    (ROOT/'results/REPORT.md').write_text('\n'.join(lines))


if __name__=='__main__':
    write()
