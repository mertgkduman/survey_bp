"""Audit only completed workers while the immutable production array runs.

The frozen collector is safe after array completion. During a live partial
collection, a point can create its confirmation reference after references
were enumerated. Snapshot complete workers first to avoid that read race.
All frozen selection/reference/full-ledger/endpoint checks remain mandatory.
"""
import gzip
import importlib.util
import json
from pathlib import Path
import os
import sys

REPO=Path(__file__).resolve().parents[3]
ROOT=REPO/'data/reproductions/roffe-2005-07016-search'
spec=importlib.util.spec_from_file_location('_completed_search_snapshot',ROOT/'runtime.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
plan=r.rt.load(ROOT)
snapshot=[j for j in plan['jobs'] if (ROOT/'results'/j['id']/'complete.json').exists()]
rows=[];tuning=[];finished=[]
for job in snapshot:
    point=ROOT/'results'/job['id'];path=point/'selection.json';digest=r.rt.sha(path)
    if json.loads((point/'complete.json').read_text())!={'selection_sha256':digest}:
        raise ValueError('worker completion receipt differs from selection lock')
    selection=json.loads(path.read_text());r.validate_selection(ROOT,job,selection)
    references=r.audit_references(point,job,plan['protocol']);base=r.base_state(job)
    for stored in selection['coarse']+selection['finalists']:
        child=r.child_job(job,r.engine.Controls(**stored['controls']),stored['job']['stage'],plan['protocol'])
        if child!=stored['job']:raise ValueError('tuning job differs from locked protocol')
        summary=r.audit_child(ROOT,point,base,child,references)
        if any(stored.get(k)!=v for k,v in summary.items()):raise ValueError('training ledger/selection conflict')
        tuning.append(stored)
    for setting in selection['confirmations']:
        child=r.child_job(job,r.engine.Controls(**setting['controls']),'confirmation',plan['protocol'])
        directory=point/'confirmation'/child['id'];summary=r.audit_child(ROOT,point,base,child,references)
        rows.append({**summary,'job':child,'point':job['id'],'budgets':setting['budgets'],
                     'directory':str(directory.relative_to(REPO)),'summary_sha256':r.rt.sha(directory/'summary.json'),
                     'selection_sha256':digest})
    finished.append(job['id'])
    print('audited',len(finished),'/',len(snapshot),job['id'],'measurements',len(rows),flush=True)
receipt={'schema':'canonical-css-search-verification-v1','plan_sha256':r.rt.sha(ROOT/'plan.json'),
         'planned_strata':len(plan['jobs']),'finished_strata':finished,'points':rows,'tuning':tuning,
         'collection_scope':'snapshot of completed immutable workers; active points excluded to avoid live-reference race',
         'collector_source_sha256':r.rt.sha(Path(__file__))}
temporary=ROOT/'results/snapshot-verified.json.gz'
with gzip.open(temporary,'wt',compresslevel=6) as stream:json.dump(receipt,stream,sort_keys=True,allow_nan=False)
os.replace(temporary,ROOT/'verified.json.gz')
report=r.module('_completed_search_snapshot_report',ROOT/'report.py');print(report.report(ROOT,receipt),flush=True)
from bp_study_publish import refresh
refresh(ROOT)
