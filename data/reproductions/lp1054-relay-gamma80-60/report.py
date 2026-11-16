"""Publish only fully audited fresh gamma policies; preserve all tuning history."""
from collections import defaultdict
import csv
import gzip
import json
from pathlib import Path

from _lp1054_gamma_engine import module,ROOT,VERSION
run=module('_lp1054_gamma_campaign',ROOT/'run.py')
rt=run.rt


def flat(row):
    n=row['shots'];c=row['controls'];s=c.get('search',{})
    return {'background':row['job']['background'],'p':row['job']['physical_p'],'stage':row['stage'],
        'roles':','.join(row.get('roles',[])),'damping':c['damping'],'alpha':c['alpha'],'offset':c['beta'],
        'first_gamma':s.get('first_gamma'),'gamma_low':s.get('gamma_low'),'gamma_high':s.get('gamma_high'),
        'first_cap':s.get('initial'),'second_cap':s.get('per_unit'),'additional_legs':s.get('units'),
        'shots':n,'failures':row['failures'],'block_ler':row['rate'],'ci95_low':row['ci95_low'],
        'ci95_high':row['ci95_high'],'mean_iterations':row['iterations']/n,
        'mean_directed_edge_updates':row['directed_edge_updates']/n,'mean_seconds':row['decode_ns']/n/1e9,
        'mean_gamma_bias_updates':row['gamma_bias_updates']/n,'mean_disorder_draws':row['disorder_draws']/n,
        'memory_clips':row['memory_clips'],
        'p50_seconds':row['latency_quantiles_seconds']['0.5'],'p95_seconds':row['latency_quantiles_seconds']['0.95'],
        'p99_seconds':row['latency_quantiles_seconds']['0.99'],'controls':json.dumps(c,sort_keys=True,separators=(',',':')),
        'source_directory':row['directory'],'summary_sha256':rt.sha(rt.REPO/row['directory']/'summary.json')}


def write_csv(path,rows,compressed=False):
    with (gzip.open(path,'wt',newline='') if compressed else path.open('w',newline='')) as f:
        if rows:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def publish(plan,rows):
    relative=str(ROOT.relative_to(rt.REPO));dataset=plan['study_id'];groups=defaultdict(list)
    for row in rows:groups[run.identity(row['controls'])].append(row)
    series=[];decoders=[]
    for token,values in sorted(groups.items()):
        c=values[0]['controls'];identifier=dataset+':'+token[:20];s=c.get('search')
        label=('RelayBP80/60' if s else 'Continuous BP140')+f', d={c["damping"]:g}, alpha={c["alpha"]:g}, beta={c["beta"]:g}'
        config={'family':'binary_css','decoding_scope':'separate_xz','check_rule':'min_sum',
            'message_resolution':'float64','v2c_damping':c['damping'],'alpha':c['alpha'],'beta':c['beta'],
            'alpha_schedule':'constant','max_iterations':c['cap'],'noise_model':'depolarizing',
            'prior':'2p/3','check_cap':None,'execution_backend':VERSION}
        if s:config['search']=s
        points=[]
        for row in sorted(values,key=lambda x:x['job']['physical_p']):
            n=row['shots'];points.append({'x':row['job']['physical_p'],'y':row['rate'],'n':n,'failures':row['failures'],
                'ci_low':row['ci95_low'],'ci_high':row['ci95_high'],'status':'complete' if row['failures'] else 'upper_bound',
                'mean_iterations':row['iterations']/n,'iteration_unit':'all component/relay sweeps',
                'mean_directed_edge_updates':row['directed_edge_updates']/n,'mean_work':row['iterations']/n,
                'work_unit':'iterations','mean_seconds':row['decode_ns']/n/1e9,
                'runtime_scope':'warm complete controller; includes gamma draws and solver path-state storage; excludes external hashing/serialization/sampling/evaluation',
                'type_i':row['counts'].get('type_i',0),'type_ii':row['counts'].get('type_ii',0),
                'metadata':{'cohort_kind':'relay_gamma_fresh_confirmation','roles':row['roles'],
                    'seed':run.SEEDS['confirmation'],'memory_seed':run.memory_seed(row['job'],'confirmation'),
                    'sampling_method':'iid_failure_target_or_shot_cap','stop_reason':row['stop_reason'],
                    'uncertainty_method':row['uncertainty_method'],'denominator_definition':'all iid shots; either original syndrome mismatch or either nontrivial logical residual',
                    'mean_gamma_bias_updates':row['gamma_bias_updates']/n,
                    'mean_disorder_draws':row['disorder_draws']/n,'memory_clips':row['memory_clips'],
                    'source_evidence_path':row['directory']+'/summary.json','summary_sha256':rt.sha(rt.REPO/row['directory']/'summary.json'),
                    'latency_quantiles_seconds':row['latency_quantiles_seconds']}})
        series.append({'series_id':identifier,'dataset_id':dataset,'code_id':'lp1054','decoder_id':identifier,
            'source_decoder_id':identifier,'channel_kind':'depolarizing','label':label,'points':points})
        decoders.append({'decoder_id':identifier,'label':label,'evidence_status':'canonical_adaptation',
            'asset':{'path':relative+'/plan.json','kind':'decoder_source','label':'Frozen80/60 gamma protocol'},
            'configuration':{'settings_status':'exact_campaign_arm','source_path':relative+'/plan.json','effective_configuration':config}})
    rt.write_json(ROOT/'catalog.json',{'schema':'research-catalog-extension-v1','papers':[],
        'datasets':[{'dataset_id':dataset,'label':plan['label'],'paper_id':plan['paper_id'],
            'source_path':relative+'/verified.json.gz','evidence_status':'canonical_adaptation','caveat':plan['claim_limit'],
            'points':[p for s in series for p in s['points']],
            'assets':[{'path':relative+'/'+name,'kind':kind,'label':name} for name,kind in
                [('RESULTS.md','markdown'),('results-table.csv','csv'),('tuning-results.csv.gz','gzip'),('verified.json.gz','gzip')]]}],
        'decoders':decoders,'result_series':series,'experiments':[{'experiment_id':dataset,'dataset_id':dataset,
            'dataset_ids':[dataset],'paper_ids':[plan['paper_id']],'code_ids':['lp1054'],
            'decoder_ids':[d['decoder_id'] for d in decoders],'description':plan['claim_limit'],'evidence_status':'canonical_adaptation',
            'reproduction_recipe':{'kind':'source_command','study_path':relative+'/plan.json','decoder_path':None,
                'commands':['PYTHONPATH=src .venv/bin/python '+relative+'/run.py --collect'],
                'original_instruction_path':relative+'/README.md','budget_note':'Collection audits retained cohorts; simulations use frozen point indices and must not overwrite completed evidence.'}}]})


def collect():
    plan=rt.load(ROOT);points=[];training=[];finished=[];(ROOT/'results').mkdir(exist_ok=True)
    for job in plan['jobs']:
        point=ROOT/'results'/job['id'];path=point/'audit.json'
        if not path.exists():continue
        value=json.loads(path.read_text())
        if (value!=json.loads((point/'complete.json').read_text()) or value['job']!=job
                or value['plan_sha256']!=rt.sha(ROOT/'plan.json') or value['selection_sha256']!=rt.sha(point/'selection.json')):
            raise ValueError('audit identity mismatch')
        for row in value['points']+value['training']:
            d=rt.REPO/row['directory'];raw={k:v for k,v in row.items() if k!='roles'}
            if json.loads((d/'summary.json').read_text())!=raw:raise ValueError('audited summary changed')
            if rt.sha(d/'manifest.json')!=row['manifest_sha256']:raise ValueError('audited manifest changed')
            if {p.name:rt.sha(p) for p in sorted(d.glob('chunk-*.jsonl.gz'))}!=row['chunks']:raise ValueError('audited chunks changed')
        points.extend(value['points']);training.extend(value['training']);finished.append(job['id'])
    receipt={'plan_sha256':rt.sha(ROOT/'plan.json'),'finished_strata':finished,'planned_strata':len(plan['jobs']),
             'points':points,'training':training}
    with gzip.open(ROOT/'verified.json.gz','wt') as f:json.dump(receipt,f,sort_keys=True,allow_nan=False)
    write_csv(ROOT/'results-table.csv',[flat(row) for row in points])
    write_csv(ROOT/'tuning-results.csv.gz',[flat(row) for row in training],True)
    lines=['# LP1054 uniform80/disordered60 gamma tuning','',
        f'{len(finished)}/{len(plan["jobs"])} background/rate workers fully audited; {len(points)} distinct fresh policies.',
        '',plan['claim_limit'],'',
        'The first leg uses one scalar gamma for all variables, with80 sweeps maximum. If needed, one further60-sweep leg uses a quenched independent gamma per variable. Each leg stops at syndrome convergence; S=1. Gamma changes the prior-memory equation, not the separately fixed V2C damping coefficient. Zero-width intervals are exact fixed-gamma ablations.',
        '', 'Fresh roles: selected full gamma, first phase only, disordered phase only, zero-memory80/60 reset and continuous BP140. Roles sharing the same exact policy reuse one cohort; no duplicate shot counts. Tuning uses three separate training stages; none is pooled into fresh confirmation. Work includes both components and every attempted segment. New latency excludes external hashes and cannot be directly ranked against old provenance-instrumented times.',
        '', '| Background | p | Roles | gamma0 | Gamma interval | Block LER | 95% CI | Shots | Mean sweeps | Mean edges | Mean µs |',
        '| --- | ---: | --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: |']
    for row in sorted(points,key=lambda r:(r['job']['physical_p'],r['job']['background'],r['roles'])):
        f=flat(row);interval=f'[{f["gamma_low"]},{f["gamma_high"]}]' if f['gamma_low'] is not None else 'continuous BP'
        lines.append(f'| {f["background"]} | {f["p"]:g} | {f["roles"]} | {f["first_gamma"]} | {interval} | {f["block_ler"]:.6g} | [{f["ci95_low"]:.6g},{f["ci95_high"]:.6g}] | {f["shots"]} | {f["mean_iterations"]:.3f} | {f["mean_directed_edge_updates"]:.1f} | {f["mean_seconds"]*1e6:.2f} |')
    if not points:lines+=['','No fresh audited results yet; workers are pending or tuning.']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n');publish(plan,points)
    from bp_study_publish import refresh
    refresh(ROOT);print(len(finished),'/',len(plan['jobs']),'gamma workers audited',flush=True)
