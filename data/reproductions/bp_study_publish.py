"""Normalize audited study evidence and refresh the shared multi-rate workbench."""
from collections import defaultdict
import json
import os
import subprocess
from pathlib import Path
import bp_study_runtime as rt


def publish(root):
    plan=rt.load(root);receipt=json.loads((root/'verified.json').read_text())
    if receipt.get('schema')!='canonical-bp-study-verification-v1' or receipt['plan_sha256']!=rt.sha(root/'plan.json'):
        raise ValueError('receipt differs from frozen study')
    dataset=plan['study_id'];relative=root.relative_to(rt.REPO).as_posix()
    grouped=defaultdict(list);configs={}
    for row in receipt['points']:
        n=row['shots'];key=(row['code'],row['arm']);configs[key]=row['decoder']
        source=row.get('source_target')
        grouped[key].append({'x':row['physical_p'],'y':row['rate'],'n':n,'failures':row['failures'],
           'ci_low':row['ci95_low'],'ci_high':row['ci95_high'],'status':'complete' if row['failures'] else 'upper_bound',
           'mean_work':row['iterations']/n,'work_unit':'iterations','mean_iterations':row['iterations']/n,
           'mean_directed_edge_updates':row['directed_edge_updates']/n,'iteration_unit':'sweeps',
           'mean_seconds':row['decode_ns']/n/1e9,'type_i':row['counts']['type_i'],'type_ii':row['counts']['type_ii'],
           'source_value':source,
           'metadata':{'matched_x_rate':row['matched_x_rate'],'channel':row['decoder']['noise_model'],
               'cohort_kind':'heldout_damping_validation' if plan['stage']=='confirmation' else 'paper_rate_validation',
               'stop_reason':row['stop_reason'],'target_failures':row['target_block_failures'],'max_shots':row['max_shots'],
               'sampling_method':'iid_failure_target_or_shot_cap','seed':row['seed'],
               'uncertainty_method':'exact_negative_binomial_interval' if row['stop_reason']=='target_block_failures' else 'exact_binomial_interval_at_shot_cap',
               'denominator_definition':'all retained iid shots; syndrome mismatch or either nontrivial logical residual',
               'ledger_sha256':row['ledger_sha256'],'summary_sha256':row['summary_sha256'],
               'source_evidence_path':f'{relative}/results/{row["id"]}/summary.json'}})
    series=[];decoders=[]
    for (code,arm),points in sorted(grouped.items()):
        settings=configs[(code,arm)];identifier=f'{dataset}:{code}:{arm}'
        label=('Q-BP' if settings['family']=='bp4' else 'Ordinary binary BP')+(', MS' if settings['check_rule']=='min_sum' else ', SP')
        label+=f', d = {settings["v2c_damping"]}, '+('depolarizing' if settings['family']=='bp4' else 'X-only')
        if plan['stage']=='confirmation':label+='; '+('selected damping' if arm.endswith('_selected') else 'original damping holdout')
        series.append({'series_id':identifier,'dataset_id':dataset,'code_id':code,'decoder_id':identifier,
                       'source_decoder_id':arm,'label':label,'channel_kind':settings['noise_model'],
                       'points':sorted(points,key=lambda p:p['x'])})
        decoders.append({'decoder_id':identifier,'label':label,'evidence_status':'canonical_adaptation',
                         'asset':{'path':f'{relative}/plan.json','label':'Frozen study configuration','kind':'decoder_source'},
                         'configuration':{'settings_status':'exact_campaign_arm','source_path':f'{relative}/plan.json',
                                          'source_arm_id':arm,'effective_configuration':settings}})
    dataset_record={'dataset_id':dataset,'label':plan.get('label',dataset),'paper_id':plan['paper_id'],
        'source_path':f'{relative}/verified.json','evidence_status':'canonical_adaptation','caveat':plan['claim_limit'],
        'points':[p for s in series for p in s['points']],
        'assets':[{'path':f'{relative}/{name}','kind':'json','label':label}
                  for name,label in [('plan.json','Frozen configuration'),('verified.json','Audited terminal results')]]}
    comparison={'schema':'canonical-bp-study-comparison-v1','verified_sha256':rt.sha(root/'verified.json'),
        'scope':'Pointwise descriptive assessment; no simultaneous source-reproduction or decoder-superiority claim.',
        'source_points':[{'id':r['id'],'p':r['physical_p'],'rate':r['rate'],
                          'ci95_low':r['ci95_low'],'ci95_high':r['ci95_high'],
                          'source_approx':r['source_target'],
                          'source_inside_pointwise_interval':r['ci95_low']<=r['source_target']<=r['ci95_high']}
                         for r in receipt['points'] if r.get('source_target') is not None]}
    if plan['stage']=='confirmation':
        comparison['holdout_groups']=[]
        groups=defaultdict(list)
        for r in receipt['points']:groups[(r['code'],r['base_arm'],r['role'])].append(r)
        for (code,family,role),rows in sorted(groups.items()):
            comparison['holdout_groups'].append({'code':code,'base_arm':family,'role':role,
                'damping':rows[0]['decoder']['v2c_damping'],'rates':len(rows),
                'mean_ler_across_rates':sum(r['rate'] for r in rows)/len(rows),
                'mean_iterations_across_rates':sum(r['iterations']/r['shots'] for r in rows)/len(rows),
                'points':[{'p':r['physical_p'],'shots':r['shots'],'failures':r['failures'],'ler':r['rate'],
                           'ci95_low':r['ci95_low'],'ci95_high':r['ci95_high'],
                           'mean_iterations':r['iterations']/r['shots'],
                           'mean_directed_edge_updates':r['directed_edge_updates']/r['shots']} for r in sorted(rows,key=lambda x:x['physical_p'])]})
    rt.write_json(root/'comparison.json',comparison)
    dataset_record['assets'].append({'path':f'{relative}/comparison.json','kind':'json','label':'Source or holdout assessment'})
    result={'schema':'research-catalog-extension-v1','papers':plan.get('catalog_papers',[]),
            'datasets':[dataset_record],'decoders':decoders,'result_series':series,
            'experiments':[{'experiment_id':dataset,'dataset_id':dataset,'dataset_ids':[dataset],
                'paper_ids':[plan['paper_id']],'code_ids':sorted({c for c,a in grouped}),
                'decoder_ids':[x['decoder_id'] for x in decoders], 'description':plan['claim_limit'],
                'evidence_status':'canonical_adaptation','reproduction_recipe':{'kind':'source_command',
                    'study_path':f'{relative}/plan.json','decoder_path':f'{relative}/plan.json',
                    'commands':[f'PYTHONPATH=src .venv/bin/python {relative}/../run.py --stage confirmation --collect'] if plan['stage']=='confirmation' else [f'PYTHONPATH=src .venv/bin/python {relative}/run.py --collect'],
                    'original_instruction_path':plan.get('instruction_path',f'{relative}/README.md'),
                    'budget_note':'Collection audits existing results; simulations use the immutable plan.'}}]}
    rt.write_json(root/'catalog.json',result)
    return result


def refresh(root):
    from bp_registry.research.catalog import build_catalog
    destination=rt.REPO/'web/research/catalog.json';before=destination.read_bytes()
    clean=subprocess.run(['git','diff','--quiet','HEAD','--',str(destination)],cwd=rt.REPO).returncode==0
    catalog=build_catalog(rt.REPO)
    assets={r['code_id']:r['matrix_asset'] for r in json.loads(before)['codes'] if 'matrix_asset' in r}
    for row in catalog['codes']:
        if row['code_id'] in assets:row['matrix_asset']=assets[row['code_id']]
    rendered=(json.dumps(catalog,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    (root/'results/catalog.json').write_bytes(rendered)
    if clean and destination.read_bytes()==before:
        tmp=destination.with_suffix('.study.tmp');tmp.write_bytes(rendered);os.replace(tmp,destination)
        print('Updated workbench',flush=True)
    else:print('Workbench has local edits; complete refresh saved in study results/catalog.json',flush=True)
