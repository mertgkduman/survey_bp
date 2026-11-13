"""Inference provenance, short budgets, and isolated two-hypothesis execution."""
from copy import deepcopy
import gzip
import importlib.util
import json
from pathlib import Path
from hashlib import sha256
import numpy as np
import pytest

REPO=Path(__file__).resolve().parents[1]

def module(name,relative):
    s=importlib.util.spec_from_file_location(name,REPO/relative);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

baseline=module('_test_inferred_baseline','data/reproductions/mackay-0304161-inferred-budget/run.py')
tune=module('_test_t100_tune','data/reproductions/mackay-0304161-damping-t100/run.py')
infer=module('_test_cap_infer','data/reproductions/mackay-0304161-budget-calibration/infer.py')


def test_budget_is_explicitly_inferred_and_100_best_tested_fit():
    b=json.loads((baseline.ROOT/'budget.json').read_text())
    x=json.loads((infer.ROOT/'inference.json').read_text())
    assert b['source_numeric_iteration_cap'] is None
    assert b['status']=='curve_inferred_not_source_specified'
    assert b['inference_sha256']==sha256((infer.ROOT/'inference.json').read_bytes()).hexdigest()
    assert min(x['alignment_scores'],key=lambda s:s['sum_squared_log_relative_total_error'])['iterations_per_hypothesis']==100
    assert len(x['alignment_scores'])==11
    assert 'Original bank stopped' in x['sampling_caveat'] and 'descriptive' in x['sampling_caveat']
    assert max(r['cap'] for r in x['replays'])<=1000


def test_baseline_and_tuning_caps_and_seeds_cannot_inherit_88200():
    d=baseline.design();assert len(d['jobs'])==30
    assert len({j['id'] for j in d['jobs']})==30
    for j in d['jobs']:
        assert j['seed']==2026111317 and j['target_block_failures']==20
        if j['arm']=='unicycle_sp':
            assert j['decoder']['max_iterations']==200
            assert j['decoder']['iterations_per_branch']==100 and j['decoder']['branch_count']==2
        else:assert j['decoder']['max_iterations']==100 and j['decoder']['branch_count']==1
    t=tune.design();assert len(t['jobs'])==140
    assert {j['decoder']['max_iterations'] for j in t['jobs']}=={100}
    assert {j['seed'] for j in t['jobs']}=={2026111321}
    assert all(j['max_shots']==1024 and j['target_block_failures']>1024 for j in t['jobs'])
    assert t['selection']['confirmation_seed']==2026111323


def direct(graph,syndrome,p,cap):
    rows=[]
    for extra in (0,1):
        r=graph.run(syndrome^extra,error_rate=p,max_iterations=cap)
        rows.append((np.append(r.candidate,np.uint8(extra)).astype(np.uint8),r.converged,r.iterations))
    return rows


def test_first_convergence_projection_agrees_with_independent_short_runs():
    j=next(j for j in baseline.design()['jobs'] if j['code']=='unicycle74' and j['arm']=='unicycle_sp')
    value=baseline.rt.state(j);graph=value[3][0];packed=value[2]
    rng=np.random.default_rng(637);success=failures=0
    for p in (.02,.1,.2):
        for _ in range(12):
            truth=(rng.random(74)<p).astype(np.uint8);syndrome=baseline.rt.parent.base._syndrome(packed[1],truth)
            long=direct(graph,syndrome,p,20);winner=infer.selected(long,20)
            for cap in (2,5,10):
                observed=infer.selected(direct(graph,syndrome,p,cap),cap)
                projected=infer.selected(long,cap)
                assert (observed is None)==(projected is None)
                if observed is not None:assert np.array_equal(observed,projected)
                if winner is not None and np.array_equal(winner,truth):
                    correct=int(truth[-1]);should_succeed=long[correct][2]<=cap
                    assert should_succeed==(observed is not None and np.array_equal(observed,truth))
            success+=winner is not None and np.array_equal(winner,truth)
            failures+=winner is None or not np.array_equal(winner,truth)
    assert success and failures


def test_canonical_controller_caps_both_branches_and_counts_executed_work():
    j=next(j for j in baseline.design()['jobs'] if j['code']=='unicycle74' and j['arm']=='unicycle_sp')
    value=baseline.rt.state(j);graph=value[3][0]
    for shot in range(12):
        row=baseline.rt.event(value,shot)
        assert all(0<=i<=100 for i in row['branch_iterations'])
        assert row['iterations']==sum(row['branch_iterations'])<=200
        assert row['directed_edge_updates']==2*j['graph_edges']*row['iterations']
        truth=baseline.rt.parent.base._sample(j['seed'],round(j['physical_p']*100000),shot,74,depolarizing=False)
        syndrome=baseline.rt.parent.base._syndrome(value[2][1],truth)
        candidate=infer.selected(direct(graph,syndrome,j['physical_p'],100),100)
        if candidate is None:assert row['outcome']=='type_i'
        else:assert row['candidate_sha256']==sha256(candidate.tobytes()).hexdigest()


def test_short_controller_parallel_records_and_endpoint_replay(tmp_path,monkeypatch):
    rt=baseline.rt
    j=deepcopy(next(j for j in baseline.design()['jobs'] if j['code']=='unicycle74' and j['arm']=='unicycle_sp'))
    j.update(id='serial',workers=1,max_shots=16,target_block_failures=100)
    k={**deepcopy(j),'id':'parallel','workers':2};plan={'jobs':[j,k]}
    (tmp_path/'plan.json').write_text('{}');monkeypatch.setattr(rt,'load',lambda p:plan)
    rt.execute(tmp_path,0);rt.execute(tmp_path,1);v=rt.collect(tmp_path,require_complete=True)
    def records(name):
        out=[]
        for p in sorted((tmp_path/'results'/name).glob('shots-*.jsonl.gz')):
            with gzip.open(p,'rt') as f:out.extend({k:v for k,v in json.loads(line).items() if k!='decode_ns'} for line in f)
        return out
    assert records('serial')==records('parallel')
    assert sum(x['shots'] for x in v['points'])==32


def test_confirmation_stays_at_100_and_keeps_original_settings(monkeypatch):
    d=tune.design();selection={'selected':[{'code':c,'base_arm':f,'damping':.3} for c in d['codes'] for f in ('binary_sp','qbp')]}
    monkeypatch.setattr(tune.rt,'load',lambda p:d);monkeypatch.setattr(tune.rt,'sha',lambda p:'a'*64)
    monkeypatch.setattr(tune.rt,'freeze',lambda root,design,extra:design)
    c=tune.confirmation(selection)
    assert len(c['jobs'])==40
    assert {j['decoder']['max_iterations'] for j in c['jobs']}=={100}
    assert {j['seed'] for j in c['jobs']}=={2026111323}
    assert {j['role'] for j in c['jobs']}=={'selected','baseline'}


def test_classical_source_comparison_does_not_borrow_quantum_interval(tmp_path,monkeypatch):
    monkeypatch.setattr(baseline,'ROOT',tmp_path)
    row={'id':'example','code':'unicycle274','arm':'unicycle_sp','physical_p':.01,'rate':.001,
         'classical_block_errors':4,'failures':1,'classical_block_error_rate':.004,
         'ci95_low':.0001,'ci95_high':.002,'source_classical_target':.0015}
    (tmp_path/'verified.json').write_text(json.dumps({'points':[row]}));(tmp_path/'comparison.json').write_text('{}')
    out={'result_series':[{'code_id':'unicycle274','source_decoder_id':'unicycle_sp','decoder_id':'d','points':[{'x':.01,'metadata':{}}]}],
         'decoders':[{'decoder_id':'d'}]}
    monkeypatch.setattr(baseline,'publish',lambda root:out)
    baseline.publish_baseline()
    x=json.loads((tmp_path/'comparison.json').read_text())['source_points'][0]
    assert x['source_inside_pointwise_interval'] is None and not x['counts_coincide']
    assert x['classical_rate']==.004
