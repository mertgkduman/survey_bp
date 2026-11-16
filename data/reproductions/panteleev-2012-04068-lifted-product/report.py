"""Audited full-stack tables; exact concrete configurations form catalog curves."""
from collections import defaultdict
import csv
import gzip
import json
import re

from _lp1054_engine import module, ROOT
run = module('_lp1054_run',ROOT/'run.py')
rt = run.rt


def write_csv(path,rows,compressed=False):
    with (gzip.open(path,'wt',newline='') if compressed else path.open('w',newline='')) as stream:
        if rows:
            w = csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def flatten(row):
    n = row['shots']; f = row['failures']; c = row['controls']
    return {'arm':row['job']['arm'],'p':row['job']['physical_p'],'stage':row['stage'],'shots':n,
        'failures':f,'block_ler':row['rate'],'ci95_low':row['ci95_low'],'ci95_high':row['ci95_high'],
        'word_error_rate':1-(1-row['rate'])**(1/140),
        'mean_iterations':row['iterations']/n,'mean_directed_edge_updates':row['directed_edge_updates']/n,
        'mean_seconds':row['decode_ns']/n/1e9,
        'p50_seconds':row['latency_quantiles_seconds']['0.5'],
        'p95_seconds':row['latency_quantiles_seconds']['0.95'],
        'p99_seconds':row['latency_quantiles_seconds']['0.99'],
        'configuration':json.dumps(c,sort_keys=True,separators=(',',':')),
        'stop_reason':row['stop_reason'],'source_directory':row['directory'],
        'summary_sha256':rt.sha(rt.REPO/row['directory']/'summary.json')}


def publish(plan,rows):
    relative = str(ROOT.relative_to(rt.REPO));dataset = plan['study_id'];groups = defaultdict(list)
    for row in rows:groups[run.identity(row['controls'])].append(row)
    series = [];decoders = []
    for token,values in sorted(groups.items()):
        c = values[0]['controls'];identifier = dataset+':'+token[:20]
        family = 'Q-BP' if c['family']=='qbp' else 'BP'
        label = family+('+'+c['osd'] if c.get('osd') else '')
        if c.get('search'):label = 'RelayBP' if c['search']['method']=='relay' else 'Beam search'
        label += f', MS, d={c["damping"]:g}, alpha={c["alpha"]:g}, beta={c["beta"]:g}, T={c["cap"]}'
        config = {'family':'bp4' if c['family']=='qbp' else 'bp','check_rule':'min_sum',
            'v2c_damping':c['damping'],'alpha':c['alpha'],'beta':c['beta'],'alpha_schedule':'constant',
            'max_iterations':c['cap'],'noise_model':'depolarizing','precision':'float64',
            'execution_backend':'lp1054-canonical-stack-v1','study_controls':c}
        if c.get('search'):config['search'] = c['search']
        if c.get('osd'):config['postprocessing'] = {'method':c['osd'],'order':0 if c['osd']=='OSD_0' else 10}
        points = []
        for row in sorted(values,key=lambda r:r['job']['physical_p']):
            n = row['shots']
            points.append({'x':row['job']['physical_p'],'y':row['rate'],'n':n,'failures':row['failures'],
                'ci_low':row['ci95_low'],'ci_high':row['ci95_high'],'status':'complete' if row['failures'] else 'upper_bound',
                'mean_iterations':row['iterations']/n,'iteration_unit':'all component and search sweeps',
                'mean_directed_edge_updates':row['directed_edge_updates']/n,'mean_work':row['iterations']/n,
                'work_unit':'iterations','mean_seconds':row['decode_ns']/n/1e9,
                'type_i':row['counts'].get('type_i',0),'type_ii':row['counts'].get('type_ii',0),
                'metadata':{'cohort_kind':'lp1054_fresh_confirmation','seed':run.SEEDS['confirmation'],
                    'sampling_method':'iid_failure_target_or_shot_cap','stop_reason':row['stop_reason'],
                    'uncertainty_method':row['uncertainty_method'],'denominator_definition':'all iid shots; original syndrome mismatch or either nontrivial logical residual',
                    'latency_quantiles_seconds':row['latency_quantiles_seconds'],
                    'source_evidence_path':row['directory']+'/summary.json',
                    'summary_sha256':rt.sha(rt.REPO/row['directory']/'summary.json')}})
        series.append({'series_id':identifier,'dataset_id':dataset,'code_id':'lp1054','decoder_id':identifier,
            'source_decoder_id':identifier,'channel_kind':'depolarizing','label':label,'points':points})
        decoders.append({'decoder_id':identifier,'label':label,'evidence_status':'canonical_adaptation',
            'asset':{'path':relative+'/plan.json','kind':'decoder_source','label':'Frozen LP1054 stack'},
            'configuration':{'settings_status':'exact_campaign_arm','source_path':relative+'/plan.json',
                             'effective_configuration':config}})
    rt.write_json(ROOT/'catalog.json',{'schema':'research-catalog-extension-v1','papers':[],
        'datasets':[{'dataset_id':dataset,'label':plan['label'],'paper_id':plan['paper_id'],
            'source_path':relative+'/verified.json.gz','evidence_status':'canonical_adaptation',
            'caveat':plan['claim_limit'],'points':[p for s in series for p in s['points']],
            'assets':[{'path':relative+'/'+name,'kind':kind,'label':name} for name,kind in
                [('RESULTS.md','markdown'),('results-table.csv','csv'),
                 ('tuning-results.csv.gz','gzip'),('verified.json.gz','gzip')]]}],
        'decoders':decoders,'result_series':series,'experiments':[{
            'experiment_id':dataset,'dataset_id':dataset,'dataset_ids':[dataset],
            'paper_ids':[plan['paper_id']],'code_ids':['lp1054'],
            'decoder_ids':[d['decoder_id'] for d in decoders],
            'description':plan['claim_limit'],'evidence_status':'canonical_adaptation',
            'reproduction_recipe':{'kind':'source_command','study_path':relative+'/plan.json',
                'decoder_path':None,'commands':['PYTHONPATH=src .venv/bin/python '+relative+'/run.py --collect'],
                'original_instruction_path':relative+'/README.md',
                'budget_note':'Collection audits retained evidence. Frozen single-CPU workers use run.py --index INDEX; never overwrite a completed cohort.'}}]})


def collect():
    plan = rt.load(ROOT);points = [];training = [];finished = []
    for job in plan['jobs']:
        point = ROOT/'results'/job['id'];path = point/'audit.json'
        if not path.exists():continue
        value = json.loads(path.read_text())
        if (value['job']!=job or value['plan_sha256']!=rt.sha(ROOT/'plan.json') or
                value['selection_sha256']!=rt.sha(point/'selection.json') or
                value!=json.loads((point/'complete.json').read_text())):
            raise ValueError('audit identity or frozen selection differs')
        for row in [value['confirmation'],*value['training']]:
            directory = rt.REPO/row['directory']
            if json.loads((directory/'summary.json').read_text())!=row:raise ValueError('audited summary changed')
            if row['manifest_sha256']!=rt.sha(directory/'manifest.json'):raise ValueError('manifest changed after audit')
            if row['chunks']!={p.name:rt.sha(p) for p in sorted(directory.glob('chunk-*.jsonl.gz'))}:
                raise ValueError('ledger changed after audit')
        points.append(value['confirmation']);training.extend(value['training']);finished.append(job['id'])
    receipt = {'plan_sha256':rt.sha(ROOT/'plan.json'),'finished_strata':finished,'planned_strata':len(plan['jobs']),
        'points':points,'training':training}
    with gzip.open(ROOT/'verified.json.gz','wt') as stream:json.dump(receipt,stream,sort_keys=True,allow_nan=False)
    write_csv(ROOT/'results-table.csv',[flatten(row) for row in points])
    write_csv(ROOT/'tuning-results.csv.gz',[flatten(row) for row in training],True)
    lines = ['# Lifted-product [[1054,140]] full decoder stack','',
        f'{len(finished)}/{len(plan["jobs"])} arm/rate workers independently audited. Fresh confirmation only below.',
        '',plan['claim_limit'],'',
        'Noise: independent I/X/Y/Z, probabilities1-p,p/3,p/3,p/3. Both X/Z residuals count. Block LER and derived word error rate are different: WER=1-(1-LER)^(1/140). Means include both CSS components, or all joint edges for Q-BP, plus every search branch/relay. OSD elimination/candidates are included in latency. Latency excludes JIT/sampling/evaluation and uses1%-wide bins for quantiles. Tuning and confirmation seeds are disjoint. Fixed settings use32 BP sweeps per component/joint graph. Search128 has an explicit4x aggregate per-component ceiling.',
        '', '| Arm | p | Shots | Block LER | 95% CI | Word error rate | Mean sweeps | Mean edge updates | Mean µs |',
        '| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |']
    for r in sorted([flatten(x) for x in points],key=lambda r:(r['p'],r['arm'])):
        lines.append(f'| {r["arm"]} | {r["p"]:g} | {r["shots"]} | {r["block_ler"]:.6g} | [{r["ci95_low"]:.6g}, {r["ci95_high"]:.6g}] | {r["word_error_rate"]:.6g} | {r["mean_iterations"]:.3f} | {r["mean_directed_edge_updates"]:.1f} | {r["mean_seconds"]*1e6:.2f} |')
    lines += ['', 'The original paper gives no LER curves for this code; paper-ordinate comparison is not applicable.']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    publish(plan,points)
    from bp_study_publish import refresh
    refresh(ROOT)
    print(len(finished),'/',len(plan['jobs']),'LP1054 workers audited',flush=True)
