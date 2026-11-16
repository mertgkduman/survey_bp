"""Uniform/disordered gamma semantics, budgets, independent oracle and resume."""
from dataclasses import asdict,replace
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import pytest

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO/'data/reproductions/lp1054-relay-gamma80-60'
spec=importlib.util.spec_from_file_location('_lp1054_gamma_campaign',ROOT/'run.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
e=m.engine
oracle=m.module('_gamma_scalar_oracle',ROOT.with_name('roffe-2005-07016-search')/'reference.py')


def graph(h):
    from bp_registry.canonical.compiled import CompiledBinaryFlooding
    from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
    from bp_registry.resolution import BpFloodingPolicy,ResolutionPolicy
    p=BpFloodingPolicy(check_rule='min_sum',resolution=ResolutionPolicy('float64'),
        zero_syndrome_shortcut=False,check_stabilization='exact_unity',version='bp-flooding-policy-v2',product_epsilon=1e-10)
    return CompiledBinaryFlooding.from_check_matrix(h,rule='min_sum',profile=BINARY_SPA_F64_V2,policy=p)


def invoke(h,syndrome,c,seed=77,shot=3,p=.07):
    g=graph(h);initial=math.log((1-p)/p);prior=np.full(h.shape[1],g.bind_error_rate(p).prior)
    fast=e.search.search(g.row_ptr,g.variables,h.shape[1],syndrome,initial,prior,1,
        c.initial,c.per_unit,c.units,c.damping,c.alpha,c.paper_scale,c.beta,c.width,c.rounds,c.solutions,
        c.first_gamma,c.gamma_low,c.gamma_high,seed,shot)
    slow=oracle.decode(h,syndrome,initial,prior,c,seed,shot)
    assert fast[2:4]==slow[2:4]
    for index in (0,1,4,5,6,7):np.testing.assert_array_equal(fast[index],slow[index])
    return fast


@pytest.mark.parametrize('gamma,window',[(0.,(-.24,.66)),(.125,(-.161,.815)),(.35,(-.254,.985)),
    (-.5,(-.5,1.)),(1.,(-.75,.25)),(.5,(0.,0.)),(.25,(.25,.25))])
def test_exact80_60_states_and_lineage_match_independent_scalar(gamma,window):
    h=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1],[0,0,0,1,1,1]],dtype=np.uint8)
    c=e.GammaControls(first_gamma=gamma,gamma_low=window[0],gamma_high=window[1],beta=.2)
    for shot in range(3):
        truth=np.random.default_rng(shot).integers(0,2,h.shape[1],dtype=np.uint8)
        value=invoke(h,(h@truth)%2,c,shot=shot)
        assert len(value[4])<=2 and value[4][:,3].sum()<=140


def test_inconsistent_syndrome_executes_exactly80_then60_and_resets_messages():
    h=np.array([[1,1],[1,1]],dtype=np.uint8);c=e.GammaControls(first_gamma=.35)
    result=invoke(h,np.array([0,1],dtype=np.uint8),c)
    np.testing.assert_array_equal(result[4][:,3],[80,60]);assert not result[2]
    assert result[4][1,0]==0 and result[4][1,1:3].tolist()==[-1,-1]


def test_early_success_skips_the_disordered_leg():
    h=np.array([[1,1,1]],dtype=np.uint8)
    result=invoke(h,np.zeros(1,dtype=np.uint8),e.GammaControls(first_gamma=.35))
    assert result[2] and result[4].shape[0]==1 and result[4][0,3]==1


def test_quenched_gamma_vectors_and_independent_memory_stream():
    c=e.GammaControls(first_gamma=.35,gamma_low=-.161,gamma_high=.815)
    first=e.gamma_vector(c,77,9,0,1054);second=e.gamma_vector(c,77,9,1,1054)
    np.testing.assert_array_equal(first,np.full(1054,.35))
    expected=np.array([-.161+(.815+.161)*oracle.uniform(77,9,1,v) for v in range(1054)])
    np.testing.assert_array_equal(second,expected)
    assert second.min()>=-.161 and second.max()<=.815 and np.ptp(second)>.5
    np.testing.assert_array_equal(second,e.gamma_vector(c,77,9,1,1054))
    assert not np.array_equal(second,e.gamma_vector(c,77,10,1,1054))
    assert set(m.SEEDS.values()).isdisjoint(m.MEMORY_SEEDS.values()) and len(set(m.SEEDS.values()))==4


@pytest.mark.parametrize('changes',[{'units':2},{'initial':79},{'per_unit':61},{'solutions':2},
    {'gamma_low':.5,'gamma_high':-.1},{'first_gamma':1.01}])
def test_user_confirmed_one_leg_budget_is_enforced(changes):
    with pytest.raises(ValueError):e.GammaControls(**changes)


def test_inventory_training_source_and_five_ablation_roles():
    plan=m.design();assert len(plan['jobs'])==12 and len(m.GAMMAS)==11 and len(m.WINDOWS)==18
    for job in plan['jobs']:
        grid=m.proposals(job);assert len(grid)==199 and len({m.identity(c) for c in grid})==199
        assert all(c['cap']==140 and c['search']['units']==1 for c in grid)
        controls=m.confirmations(job,grid[0]);assert set(sum([c['roles'] for c in controls],[]))==set(m.ROLES)
    assert len(plan['parent_training'])==6 and all('selection_sha256' in r for r in plan['parent_training'])
    assert len({m.memory_seed(plan['jobs'][0],stage) for stage in m.SEEDS})==4


def test_zero_count_ties_keep_all_gamma_bands_and_fresh_selection_is_training_only():
    job=m.design()['jobs'][1]
    rows=[{'controls':c,'rate':0.,'iterations':10,'decode_ns':20,'shots':100} for c in m.proposals(job)]
    chosen=m.finalists(rows,job);g=[c['search']['first_gamma'] for c in chosen if m.genuine(c)]
    assert any(x<=0 for x in g) and any(0<x<=.35 for x in g) and any(.35<x<=.625 for x in g) and any(x>.625 for x in g)
    assert m.relay(job,0,0,0) in chosen
    refined=m.refinement([r for r in rows if r['controls'] in chosen])
    assert all(c in refined for c in chosen) and len(refined)>len(chosen)


def test_real_code_events_include_both_components_and_gamma_provenance():
    job=m.design()['jobs'][7];c=m.relay(job,.35,-.24,.66)
    prepared=e.Prepared(m.code(),job['physical_p'],c,m.memory_seed(job,'coarse'))
    for shot in (0,1,3):
        row=m.r.make_event(prepared,job,'coarse',shot);m.validate(row,m.code(),job,'coarse',c)
        assert len(row['components'])==2 and row['iterations']<=280
        tampered=json.loads(json.dumps(row));tampered['components'][0]['gamma_sha256'][0]='0'*64
        with pytest.raises(ValueError,match='gamma provenance'):m.validate(tampered,m.code(),job,'coarse',c)


@pytest.mark.parametrize('gamma,window',[(.125,(-.24,.66)),(.35,(-.5,1.))])
def test_real_lp1054_terminal_states_and_messages_match_independent_oracle(gamma,window):
    job=m.design()['jobs'][7];c=m.relay(job,gamma,*window);seed=m.memory_seed(job,'coarse')
    prepared=e.Prepared(m.code(),job['physical_p'],c,seed)
    truth=e.sample(m.SEEDS['coarse'],round(job['physical_p']*10000),0,m.code().n,job['physical_p'])
    syndrome=e.multiply(m.code().hz,truth[0]);sc=e.GammaControls(**c['search'])
    value=invoke(m.code().hz,syndrome,sc,seed,0,p=2*job['physical_p']/3)
    event=m.r.make_event(prepared,job,'coarse',0);detail=event['components'][0]
    assert event['candidate'][0]==m.r.encode(value[0])
    assert detail['posterior_sha256']==sha256(value[1].tobytes()).hexdigest()
    assert detail['all_message_sha256']==sha256(value[7].tobytes()).hexdigest()
    assert detail['units']==value[4].tolist()


def test_matched_bp140_is_exact_parent_canonical_execution_and_gamma_work_is_typed():
    job=m.design()['jobs'][7];c=m.base_controls(job);qc=m.code();seed=m.memory_seed(job,'coarse')
    old=e.base.Prepared(qc,job['physical_p'],c,seed);new=e.Prepared(qc,job['physical_p'],c,seed)
    truth=e.sample(m.SEEDS['coarse'],round(job['physical_p']*10000),0,qc.n,job['physical_p'])
    s=[e.multiply(qc.hz,truth[0]),e.multiply(qc.hx,truth[1])]
    a,ma=old.decode(s,0);b,mb=new.decode(s,0)
    for x,y in zip(a,b):np.testing.assert_array_equal(x,y)
    assert ma['iterations']==mb['iterations'] and ma['directed_edge_updates']==mb['directed_edge_updates']
    assert [d['posterior_sha256'] for d in ma['components']]==[d['posterior_sha256'] for d in mb['components']]
    assert mb['gamma_bias_updates']==mb['disorder_draws']==mb['memory_clips']==0
    c=m.relay(job,.35,-.24,.66);new=e.Prepared(qc,job['physical_p'],c,seed)
    row=m.r.make_event(new,job,'coarse',0)
    assert row['gamma_bias_updates']==qc.n*row['iterations']
    row['gamma_bias_updates']+=1
    with pytest.raises(ValueError,match='gamma work accounting'):m.validate(row,qc,job,'coarse',c)


def test_real_short_pipeline_resume_full_audit_and_selection_lock(monkeypatch):
    (ROOT/'results').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='qualification-',dir=ROOT/'results') as directory:
        target=Path(directory);(target/'plan.json').write_text('{"qualification_only":true}\n')
        plan=m.design();job=plan['jobs'][5];plan['jobs']=[job]
        plan['protocol'].update(coarse_shots=4,finalist_shots=4,finalist_failures=2,
            refine_shots=4,refine_failures=2,max_shots=6,target_failures=2)
        original=m.proposals(job);subset=[original[2],original[64],original[-1]]
        with monkeypatch.context() as patch:
            patch.setattr(m,'ROOT',target);patch.setattr(m.rt,'load',lambda root:plan);patch.setattr(m,'CHUNK',2)
            patch.setattr(m,'proposals',lambda j:subset);patch.setattr(m,'refinement',lambda rows:[x['controls'] for x in rows])
            m.execute(0);point=target/'results'/job['id']
            before={str(p):m.rt.sha(p) for p in point.rglob('chunk-*.gz')};m.execute(0)
            assert before=={str(p):m.rt.sha(p) for p in point.rglob('chunk-*.gz')}
            m.execute(0,audit=True)
            assert json.loads((point/'audit.json').read_text())==json.loads((point/'complete.json').read_text())
            value=json.loads((point/'selection.json').read_text());value['chosen']['alpha']=.123
            (point/'selection.json').write_text(json.dumps(value))
            with pytest.raises(ValueError,match='selection lock'):m.execute(0,audit=True)


def test_worker_deadline_resume_and_audit_are_in_one_cpu_allocation():
    subprocess.run(['bash','-n',str(ROOT/'worker.sh')],check=True)
    text=(ROOT/'worker.sh').read_text()
    assert 'trap resume_later USR1' in text and 'scontrol requeue' in text
    assert '--audit --index' in text and 'OMP_NUM_THREADS=1' in text
