"""Keep full point tables and publish only exact-policy fresh measurements."""
from collections import defaultdict
import csv
import gzip
from hashlib import sha256
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import bp_study_runtime as rt


def flat(row):
    job=row['job'];n=row['shots'];c=job['controls'];q=row['latency_quantiles_seconds']
    return {'code':job['code'],'method':job['method'],'p':job['physical_p'],'budgets':','.join(map(str,row.get('budgets',[]))),
            **c,'stage':job['stage'],'shots':n,'logical_failures':row['failures'],'ler':row['rate'],
            'ci95_low':row['ci95_low'],'ci95_high':row['ci95_high'],'mean_iterations':row['iterations']/n,
            'mean_directed_edge_updates':row['directed_edge_updates']/n,'mean_seconds':row['decode_ns']/n/1e9,
            'reference_seconds':row['reference_ns']/n/1e9,'runtime_ratio':row['runtime_ratio'],
            'p50_seconds':q['0.5'],'p95_seconds':q['0.95'],'p99_seconds':q['0.99'],
            'mean_extra_units':row['extra_units']/n,'memory_prior_clips':row['memory_prior_clips'],
            'source_directory':row['directory'],'summary_sha256':row['summary_sha256']}


def csv_rows(stream,rows):
    if rows:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)


def report(root,receipt=None):
    plan=rt.load(root)
    if receipt is None:
        with gzip.open(root/'verified.json.gz','rt') as stream:receipt=json.load(stream)
    if receipt['plan_sha256']!=rt.sha(root/'plan.json'):raise ValueError('report requires matching full audit')
    rows=[flat(r) for r in receipt['points']]
    with (root/'results-table.csv').open('w',newline='') as stream:csv_rows(stream,rows)
    with gzip.open(root/'tuning-results.csv.gz','wt',newline='') as stream:csv_rows(stream,[flat(r) for r in receipt['tuning']])
    osd_path=Path(__file__).resolve().parent.with_name('roffe-2005-07016-osd-fast')/'verified.json'
    reference={}
    for r in json.loads(osd_path.read_text())['points']:
        if r['arm']=='bp_osd0':reference[r['code'],r['physical_p']]=r
    lines=['# Tuned beam search and RelayBP versus BP+OSD-0','',
           f'Audited {len(receipt["finished_strata"])}/{receipt["planned_strata"]} method/rate workers; {len(rows)} fresh configurations; {sum(r["shots"] for r in rows):,} decoder shots. Tuning and confirmation remain separate.','',
           'X-only channel, original four Roffe toric codes and source rates. Controlled canonical CSS adaptations, not circuit-paper reproduction. LER-first finite tuning targets 0.5/1/2/4 times same-CPU mean warmed BP+OSD-0 time. Actual ratios remain explicit; a point over 1.1 times its target exceeds that budget. OSD LER uses the separate fully audited original OSD cohort; missing rows stay pending. Pointwise intervals and 20-failure precision do not establish simultaneous superiority.','',
           'Mean iterations and directed edge updates include every attempted segment, including pruned branches. p95/p99 use 1%-wide latency bins. Full settings, p50 and provenance are in results-table.csv; every training setting remains in tuning-results.csv.gz. Exact concrete controls form separate catalog curves, and the normal multi-rate eligibility rule remains active.','',
           '| Code | Method | p | Targets ×OSD0 | LER | 95% CI | OSD0 LER | Mean time ×OSD0 | Mean sweeps | Mean edge updates | p95 / p99 µs | Controls |',
           '| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |']
    for r in sorted(rows,key=lambda x:(x['code'],x['p'],x['method'],x['runtime_ratio'])):
        c={k:r[k] for k in ('initial','per_unit','units','damping','alpha','paper_scale','beta','width','rounds','solutions','first_gamma','gamma_low','gamma_high')}
        old=reference.get((r['code'],r['p']));old_text=f'{old["rate"]:.6g}' if old else 'pending'
        lines.append(f'| {r["code"]} | {r["method"]} | {r["p"]:g} | {r["budgets"]} | {r["ler"]:.6g} | [{r["ci95_low"]:.6g}, {r["ci95_high"]:.6g}] | {old_text} | {r["runtime_ratio"]:.3f} | {r["mean_iterations"]:.3f} | {r["mean_directed_edge_updates"]:.1f} | {r["p95_seconds"]*1e6:.2f} / {r["p99_seconds"]*1e6:.2f} | {json.dumps(c,separators=(",",":"))} |')
    if not rows:lines+=['','No fresh audited results yet. Workers may still be tuning; training estimates are not published as confirmation.']
    (root/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    assessment={'schema':'canonical-css-search-assessment-v1','planned_strata':receipt['planned_strata'],
                'finished_strata':len(receipt['finished_strata']),'confirmation_measurements':len(rows),
                'confirmed_shots':sum(r['shots'] for r in rows),'confirmed_failures':sum(r['logical_failures'] for r in rows),
                'tuning_measurements':len(receipt['tuning'])}
    rt.write_json(root/'assessment.json',assessment)
    publish(root,plan,receipt);return assessment


def publish(root,plan,receipt):
    dataset=plan['study_id'];relative=root.relative_to(rt.REPO).as_posix();groups=defaultdict(list)
    for row in receipt['points']:groups[row['job']['code'],json.dumps(row['job']['decoder'],sort_keys=True)].append(row)
    decoders=[];series=[]
    for (code,encoded),values in sorted(groups.items()):
        config=json.loads(encoded);c=config['search'];token=sha256(encoded.encode()).hexdigest()[:16]
        identifier=f'{dataset}:{code}:{token}'
        name='Beam search' if c['method']=='beam' else 'RelayBP'
        label=f'{name}, MS, d={c["damping"]:g}, alpha={c["alpha"]:g}, beta={c["beta"]:g}, T0={c["initial"]}, T={c["per_unit"]}, units={c["units"]}, S={c["solutions"]}'
        label+=f', width={c["width"]}, depth={c["rounds"]}' if c['method']=='beam' else f', gamma0={c["first_gamma"]:g}, gamma=[{c["gamma_low"]:g},{c["gamma_high"]:g}]'
        label+=', scale='+('paper ramp' if c['paper_scale'] else 'constant')+', X-only'
        points=[]
        for row in sorted(values,key=lambda r:r['job']['physical_p']):
            n=row['shots'];j=row['job']
            points.append({'x':j['physical_p'],'y':row['rate'],'n':n,'failures':row['failures'],
                           'ci_low':row['ci95_low'],'ci_high':row['ci95_high'],
                           'status':'upper_bound' if row['failures']==0 else 'complete',
                           'mean_iterations':row['iterations']/n,'iteration_unit':'all BP segment sweeps',
                           'mean_directed_edge_updates':row['directed_edge_updates']/n,
                           'mean_work':row['iterations']/n,'work_unit':'iterations',
                           'mean_seconds':row['decode_ns']/n/1e9,'runtime_scope':'warm full search decoder including all branches/legs and selection',
                           'type_i':row['counts']['type_i'],'type_ii':row['counts']['type_ii'],
                           'metadata':{'cohort_kind':'search_fresh_confirmation','seed':j['seed'],
                                       'sampling_method':'iid_failure_target_or_shot_cap','stop_reason':row['stop_reason'],
                                       'runtime_ratio_to_bp_osd0':row['runtime_ratio'],'budget_targets':row['budgets'],
                                       'latency_quantiles_seconds':row['latency_quantiles_seconds'],
                                       'denominator_definition':'all retained iid shots; original syndrome mismatch or nontrivial logical residual',
                                       'source_evidence_path':row['directory']+'/summary.json','summary_sha256':row['summary_sha256'],
                                       'ledger_sha256':row['ledger_sha256'],'selection_sha256':row['selection_sha256']}})
        series.append({'series_id':identifier,'dataset_id':dataset,'code_id':code,'decoder_id':identifier,
                       'source_decoder_id':identifier,'channel_kind':'x_only','label':label,'points':points})
        decoders.append({'decoder_id':identifier,'label':label,'evidence_status':'canonical_adaptation',
                         'asset':{'path':relative+'/plan.json','kind':'decoder_source','label':'Frozen tuned search protocol'},
                         'configuration':{'settings_status':'exact_campaign_arm','source_path':relative+'/plan.json',
                                          'effective_configuration':config}})
    extension={'schema':'research-catalog-extension-v1','papers':plan.get('catalog_papers',[]),
               'datasets':[{'dataset_id':dataset,'label':plan['label'],'paper_id':plan['paper_id'],
                            'source_path':relative+'/verified.json.gz','evidence_status':'canonical_adaptation',
                            'caveat':plan['claim_limit'],'points':[p for s in series for p in s['points']],
                            'assets':[{'path':relative+'/'+name,'kind':kind,'label':label} for name,kind,label in
                                      [('RESULTS.md','markdown','All search results'),('results-table.csv','csv','Every fresh selected point'),
                                       ('tuning-results.csv.gz','gzip','Separate tuning history'),('verified.json.gz','gzip','Full audit receipt')]]}],
               'decoders':decoders,'result_series':series,'experiments':[]}
    rt.write_json(root/'catalog.json',extension)
