"""Source semantics, damping priorities and trustworthy new-study evidence."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest

REPO=Path(__file__).resolve().parents[1]

def module(name,path):
    s=importlib.util.spec_from_file_location(name,REPO/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

tune=module('_test_damping_study','data/reproductions/mackay-0304161-damping/run.py')
roffe=module('_test_roffe_study','data/reproductions/roffe-2005-07016-bp/run.py')
prepare=module('_test_roffe_prepare','data/reproductions/roffe-2005-07016-bp/prepare.py')
rt=tune.rt


def test_frozen_design_shared_samples_budget_and_fresh_holdout():
    d=tune.design();assert len(d['jobs'])==140
    assert len({j['id'] for j in d['jobs']})==140
    assert {j['decoder']['max_iterations'] for j in d['jobs']}=={88200}
    assert {j['decoder']['v2c_damping'] for j in d['jobs']}==set(tune.DAMPING)
    assert {j['max_shots'] for j in d['jobs']}=={1024}
    assert all(j['target_block_failures']>j['max_shots'] for j in d['jobs'])
    assert d['selection']['confirmation_seed'] not in {j['seed'] for j in d['jobs']}
    for j in d['jobs']:
        assert j['physical_p']==(1.5*j['matched_x_rate'] if j['base_arm']=='qbp' else j['matched_x_rate'])


def test_ler_beats_large_speed_improvement_and_overlap_is_not_tie():
    best=np.zeros((5,1024),dtype=np.int8);best[:,:100]=1
    faster=best.copy();faster[:,100:130]=1
    x=tune.choose_damping({0.:best,.5:faster},{0.:1000,.5:1},1e-5)
    assert x['damping']==0. and not x['speed_tie_certified']
    assert not next(v for v in x['candidates'] if v['damping']==.5)['eligible']


def test_speed_only_after_simultaneous_paired_regret_guard():
    # Same empirical LER but different outcomes remains uncertain at small N.
    a=np.zeros((5,50),dtype=np.int8);a[:,:10]=1;b=np.roll(a,10,axis=1)
    x=tune.choose_damping({0.:a,.5:b},{0.:100,.5:1},1e-5)
    assert x['damping']==0.
    # Identical failures on a larger paired cohort certify a faster candidate.
    a=np.zeros((5,10000),dtype=np.int8);a[:,:2000]=1
    x=tune.choose_damping({0.:a,.5:a.copy()},{0.:100,.5:1},1e-5)
    assert x['damping']==.5 and x['speed_tie_certified']
    z=np.zeros((5,1024),dtype=np.int8)
    x=tune.choose_damping({0.:z,.5:z.copy()},{0.:100,.5:1},1e-5)
    assert x['damping']==0. and x['similarity_margin']==0.


@pytest.mark.parametrize('family', ['binary_sp','qbp'])
def test_damping_is_old_message_weight_and_preserves_physical_stream(family):
    jobs=tune.design()['jobs']
    a=deepcopy(next(j for j in jobs if j['code']=='unicycle74' and j['base_arm']==family and j['decoder']['v2c_damping']==0.))
    a['decoder'].update(max_iterations=9,iterations_per_branch=9)
    b=deepcopy(a);b['decoder']['v2c_damping']=.5
    va,vb=rt.state(a),rt.state(b)
    ra,rb=rt.event(va,1),rt.event(vb,1)
    assert ra['error_sha256']==rb['error_sha256'] and ra['syndrome_sha256']==rb['syndrome_sha256']
    graph0,graph5=va[3][0],vb[3][0]
    syndrome=np.ones(len(graph0.row_ptr)-1,dtype=np.uint8)
    if family=='qbp':
        old=graph0.initial_v2c();s0=graph0.sweep(old,syndrome);s5=graph5.sweep(old,syndrome)
        assert np.allclose(s5.v2c,.5*old+.5*s0.v2c)
    else:
        p=a['physical_p'];old=np.full(graph0.table.edge_count,np.log((1-p)/p))
        s0=graph0.sweep(old,syndrome,error_rate=p);s5=graph5.sweep(old,syndrome,error_rate=p)
        assert np.allclose(s5.new_v2c,.5*old+.5*s0.new_v2c)
    for j,r in ((a,ra),(b,rb)):
        assert r['directed_edge_updates']==2*j['graph_edges']*r['iterations']


@pytest.mark.parametrize('family,damping', [('binary_sp',0.),('qbp',.1)])
def test_original_undamped_and_qbp_baselines_replay_exactly(family,damping):
    j=deepcopy(next(x for x in tune.design()['jobs'] if x['code']=='unicycle74' and x['base_arm']==family and x['decoder']['v2c_damping']==damping))
    j['seed']=rt.parent.SEED;j['arm']=family
    # Avoid long failure trajectories in a qualification test; same cap both routes.
    j['decoder'].update(max_iterations=9,iterations_per_branch=9)
    new=rt.state(j);old_job=deepcopy(j);old_job['code_artifact']=f"codes/{j['code']}.npz";old=rt.parent.decoder_state(old_job)
    for shot in range(12):
        a=rt.event(new,shot);b=rt.parent.event(old,shot)
        assert {k:v for k,v in a.items() if k!='decode_ns'}=={k:v for k,v in b.items() if k!='decode_ns'}


def test_roffe_exact_grids_and_code_specific_total_iteration_budgets():
    d=roffe.design();assert len(d['jobs'])==218
    assert {j['code']:j['decoder']['max_iterations'] for j in d['jobs']}=={'toric9':162,'toric11':242,'toric13':338,'toric15':450}
    for c,n in [('toric9',25),('toric11',28),('toric13',28),('toric15',28)]:
        assert sum(j['code']==c and j['arm']=='binary_ms' for j in d['jobs'])==n
    assert all(j['decoder']['alpha_schedule']=='1-2**(-iteration)' for j in d['jobs'])
    assert all(j['source_target'] is None for j in d['jobs'] if j['arm']=='qbp_ms')
    assert any(j['physical_p']==.013 for j in d['jobs']) is False
    assert {j['physical_p'] for j in d['jobs'] if j['code']=='toric9' and j['arm']=='binary_ms'} != {j['physical_p'] for j in d['jobs'] if j['code']=='toric11' and j['arm']=='binary_ms'}


@pytest.mark.parametrize('distance',[3,9,11,13,15])
def test_toric_algebra_and_redundant_checks(distance):
    from bp_registry.css import gf2_rank
    c=prepare.toric(distance);assert c.n==2*distance*distance and c.k==2
    assert c.hx.shape==c.hz.shape==(distance*distance,2*distance*distance)
    assert gf2_rank(c.hx)==distance*distance-1
    assert np.all(c.hx.sum(axis=1)==4) and np.all(c.hz.sum(axis=0)==2)
    assert not np.any((c.hx.astype(int)@c.hz.astype(int).T)%2)


def reference_minsum(h,syndrome,p,limit):
    # Independent direct Algorithm 1 loops: no calls to canonical update helpers.
    rows=[list(np.flatnonzero(row)) for row in h];prior=np.log((1-p)/p)
    old={(c,v):prior for c,row in enumerate(rows) for v in row}
    for t in range(1,limit+1):
        check={}
        for c,row in enumerate(rows):
            for v in row:
                incoming=[old[c,u] for u in row if u!=v]
                check[c,v]=(-1 if syndrome[c] else 1)*(1-2.**-t)*np.prod(np.sign(incoming))*min(map(abs,incoming))
        beliefs=np.array([prior+sum(check[c,v] for c,row in enumerate(rows) if v in row) for v in range(h.shape[1])])
        candidate=(beliefs<0).astype(np.uint8)
        if np.array_equal((h.astype(int)@candidate)%2,syndrome):return candidate,t
        old={(c,v):beliefs[v]-check[c,v] for c,row in enumerate(rows) for v in row}
    return candidate,limit


def test_roffe_controller_matches_independent_source_algorithm():
    job=deepcopy(next(j for j in roffe.design()['jobs'] if j['code']=='toric9' and j['arm']=='binary_ms'))
    job['decoder'].update(max_iterations=5,iterations_per_branch=5)
    value=rt.state(job);c=rt.load_artifact(rt.REPO,job['code_artifact']).code
    rng=np.random.default_rng(472)
    for _ in range(6):
        truth=(rng.random(c.n)<.06).astype(np.uint8);syndrome=(c.hz.astype(int)@truth%2).astype(np.uint8)
        observed,converged,it=rt.decode(value,syndrome)
        expected,t=reference_minsum(c.hz,syndrome,job['physical_p'],5)
        assert np.array_equal(observed,expected) and it==t
    zero=np.zeros(c.hz.shape[0],dtype=np.uint8)
    assert rt.decode(value,zero)[2]==1


def test_terminal_prefix_resume_hash_replay_and_empty_collection(tmp_path,monkeypatch):
    job=deepcopy(tune.design()['jobs'][0]);job.update(id='qualification',max_shots=8,target_block_failures=2,workers=1)
    job['decoder'].update(max_iterations=3,iterations_per_branch=3)
    root=tmp_path;plan={'jobs':[job]};(root/'plan.json').write_text('{}')
    monkeypatch.setattr(rt,'load',lambda _:plan)
    labels=['exact_success','type_i','type_ii']
    def fake_event(value,shot):
        return {'shot':shot,'outcome':labels[shot],'iterations':3 if shot else 1,
                'branch_iterations':[3 if shot else 1], 'directed_edge_updates':2*job['graph_edges']*(3 if shot else 1),'decode_ns':5}
    monkeypatch.setattr(rt,'state',lambda j:(j,));monkeypatch.setattr(rt,'event',fake_event)
    assert rt.collect(root)['points']==[]
    with pytest.raises(ValueError,match='cannot advance'):rt.collect(root,require_complete=True)
    a=rt.execute(root,0);assert a['shots']==3 and a['failures']==2
    before=(root/'results/qualification/shots-000000000.jsonl.gz').read_bytes()
    assert rt.execute(root,0)==a
    assert (root/'results/qualification/shots-000000000.jsonl.gz').read_bytes()==before
    assert len(rt.collect(root,require_complete=True)['points'])==1
    path=root/'results/qualification/summary.json';bad=json.loads(path.read_text());bad['iterations']+=1;path.write_text(json.dumps(bad))
    with pytest.raises(ValueError,match='conflict'):rt.collect(root)
    with pytest.raises(ValueError,match='index'):rt.execute(root,-1)


@pytest.mark.parametrize('same_as_baseline',[False,True])
def test_confirmation_uses_fresh_seed_and_keeps_original_comparators(monkeypatch,same_as_baseline):
    d=tune.design();selected=[]
    for code in d['codes']:
        for family in ('binary_sp','qbp'):
            selected.append({'code':code,'base_arm':family,'damping':d['selection']['baseline_damping'][family] if same_as_baseline else .3})
    monkeypatch.setattr(rt,'load',lambda root:d)
    monkeypatch.setattr(rt,'sha',lambda path:'a'*64)
    monkeypatch.setattr(rt,'freeze',lambda root,design,extra:design)
    c=tune.confirmation({'selected':selected})
    assert len(c['jobs'])==(20 if same_as_baseline else 40)
    assert len({j['id'] for j in c['jobs']})==len(c['jobs'])
    assert all(j['seed']==2026111309 and j['max_shots']==100_000_000 and j['target_block_failures']==20 for j in c['jobs'])
    assert all(j['decoder']['max_iterations']==88200 for j in c['jobs'])
    assert {j['role'] for j in c['jobs']}==({'selected'} if same_as_baseline else {'selected','baseline'})


def test_changed_budget_cannot_be_substituted_into_a_frozen_plan(tmp_path):
    import platform,numba,scipy
    design={'jobs':[{'decoder':{'max_iterations':88200}}]}
    plan={**deepcopy(design),'schema':'canonical-bp-study-v1','implementation_sha256':{},
          'software':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'numba':numba.__version__}}
    (tmp_path/'design.json').write_text(json.dumps(design));(tmp_path/'plan.json').write_text(json.dumps(plan))
    assert rt.load(tmp_path)['jobs'][0]['decoder']['max_iterations']==88200
    plan['jobs'][0]['decoder']['max_iterations']=99;(tmp_path/'plan.json').write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='design differs'):rt.load(tmp_path)
