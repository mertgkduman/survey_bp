"""Original LP construction, canonical reuse, full Pauli outcomes and provenance."""
import importlib.util
import json
from pathlib import Path
import sys
import shutil
import tempfile

import numpy as np
import pytest
from bp_registry.css import gf2_rank

ROOT = Path(__file__).resolve().parents[1]/'data/reproductions/panteleev-2012-04068-lifted-product'
spec = importlib.util.spec_from_file_location('_lp1054_run',ROOT/'run.py')
r = importlib.util.module_from_spec(spec);sys.modules[spec.name]=r;spec.loader.exec_module(r)
e = r.engine


@pytest.fixture(scope='module')
def code():return r.code()


def test_exact_published_ring_product_independent_coefficient_expansion(code):
    a = np.array([[1,2,4,8,16],[5,10,20,9,18],[25,19,7,14,28]])
    x = np.zeros_like(code.hx);z = np.zeros_like(code.hz)
    for exponent in range(31):
        direct = (a==exponent).astype(np.uint8)
        transposed = (((-a)%31)==exponent).T.astype(np.uint8)
        circ = np.roll(np.eye(31,dtype=np.uint8),exponent,axis=1)
        x ^= np.kron(np.hstack((np.kron(direct,np.eye(5,dtype=np.uint8)),
                              np.kron(np.eye(3,dtype=np.uint8),transposed))),circ)
        z ^= np.kron(np.hstack((np.kron(np.eye(5,dtype=np.uint8),direct),
                              np.kron(transposed,np.eye(3,dtype=np.uint8)))),circ)
    np.testing.assert_array_equal(x,code.hx);np.testing.assert_array_equal(z,code.hz)
    assert code.n==1054 and code.k==140
    assert [gf2_rank(x),gf2_rank(z)]==[457,457]
    assert (x.sum(axis=1)==8).all() and (z.sum(axis=1)==8).all()


def test_inventory_grid_and_cumulative_budget():
    plan = r.design()
    assert len(plan['jobs'])==72 and len(r.ARMS)==12
    assert plan['source']['rates']==[.02,.04,.06,.08,.1,.12]
    assert len(set(r.SEEDS.values()))==3
    for arm in r.ARMS:
        controls = r.proposals(arm)
        assert len({r.identity(c) for c in controls})==len(controls)
        if arm.startswith(('relay','beam')):
            assert len(controls)==64
            for c in controls:
                s = c['search'];assert s['initial']+s['per_unit']*s['units']<=c['cap']
        elif arm.startswith('tuned'):assert len(controls)==32 and r.fixed(arm) in controls
        else:assert len(controls)==1


@pytest.mark.parametrize('arm',r.ARMS)
def test_every_arm_real_pauli_samples_and_all_work(code,arm):
    c = r.proposals(arm)[-1];p = .08;job = {'arm':arm,'physical_p':p}
    prepared = e.Prepared(code,p,c,r.SEEDS['coarse'])
    for shot in (0,1):
        row = r.make_event(prepared,job,'coarse',shot)
        r.validate_event(row,code,job,'coarse',c)
        assert row['iterations']>=1 and row['decode_ns']>0
        assert row['directed_edge_updates']>0
        if c.get('osd') and any('osd' in x for x in row['components']):
            assert row['outcome']!='type_i'


@pytest.mark.parametrize('family',('bp','qbp'))
def test_fused_loop_matches_public_canonical_reference(code,family):
    c = {**r.fixed(family),'damping':.3,'alpha':.8,'beta':.2}
    prepared = e.Prepared(code,.08,c,17)
    truth = e.sample(17,800,2,code.n,.08)
    syndrome = [e.multiply(code.hz,truth[0]),e.multiply(code.hx,truth[1])]
    for i,g in enumerate(prepared.graphs):
        joint = family=='qbp';s = np.concatenate((syndrome[1],syndrome[0])) if joint else syndrome[i]
        old = g.initial_v2c() if joint else np.full(len(g.variables),np.log((1-2*.08/3)/(2*.08/3)))
        for iteration in range(1,6):
            sweep = g.sweep(old,s,**({} if joint else {'error_rate':2*.08/3}))
            old = sweep.v2c if joint else sweep.new_v2c
            valid = (e.loops.pauli_matches(g.row_ptr,g.variables,g.labels,sweep.candidate,s) if joint else
                     e.loops.binary_matches(g.row_ptr,g.variables,sweep.candidate,s))
            if valid:break
        fused = (e.loops.pauli_loop(g.row_ptr,g.variable_ptr,g.variable_edges,g.variables,g.labels,g.prior_llrs,s,5,prepared.coefficients) if joint else
                 e.loops.binary_loop(g.row_ptr,g.variables,code.n,s,np.log((1-2*.08/3)/(2*.08/3)),
                                     g.bind_error_rate(2*.08/3).prior,5,prepared.coefficients))
        np.testing.assert_array_equal(fused[0],sweep.candidate)
        np.testing.assert_array_equal(fused[1],sweep.beliefs)
        assert fused[2:]==(bool(valid),iteration)


def test_x_z_and_invalid_residuals_are_failures(code):
    zero = np.zeros(code.n,dtype=np.uint8);truth = (zero,zero)
    assert e.outcome(code,truth,(zero,zero))=='success'
    assert e.outcome(code,truth,(code.lx[0],zero))=='type_ii'
    assert e.outcome(code,truth,(zero,code.lz[0]))=='type_ii'
    assert e.outcome(code,truth,(code.hx[0],code.hz[0]))=='success'
    bit = zero.copy();bit[0]=1
    assert e.outcome(code,truth,(bit,zero))=='type_i'


def test_sample_stream_and_manifest_tamper(code,tmp_path):
    c = r.fixed('bp');job = {'arm':'bp','physical_p':.08}
    prepared = e.Prepared(code,.08,c,r.SEEDS['coarse'])
    row = r.make_event(prepared,job,'coarse',0)
    corrupted = {**row,'outcome':'invented'}
    with pytest.raises(ValueError,match='outcome mismatch'):r.validate_event(corrupted,code,job,'coarse',c)
    with pytest.raises(ValueError,match='sample provenance'):r.validate_event(row,code,job,'finalist',c)
    path = tmp_path/'manifest.json';path.write_text('{}')
    with pytest.raises(ValueError,match='manifest changed'):r.read_rows(tmp_path,{'changed':True},code,job,'coarse',c)


def test_bounded_reduction_stopping_interval_and_zero_failures():
    rows = r.Reduction()
    for shot in range(100):rows.append({'outcome':'type_ii' if shot>=80 else 'success',
        'iterations':3,'directed_edge_updates':10,'decode_ns':1000})
    summary = r.summary(rows,20)
    assert summary['stop_reason']=='target_failures' and summary['uncertainty_method']=='exact_negative_binomial_interval'
    assert summary['iterations']==300 and summary['ci95_low']<.2<summary['ci95_high']
    empty = r.Reduction()
    with pytest.raises(ValueError,match='empty cohort'):r.summary(empty,20)
    rows = r.Reduction()
    rows.append({'outcome':'success','iterations':1,'directed_edge_updates':2,'decode_ns':1000})
    assert r.summary(rows,20)['ci95_high']>0 and r.summary(rows,20)['rate']==0


def test_real_worker_resume_training_selection_and_full_audit(monkeypatch,code):
    (ROOT/'results').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='qualification-',dir=ROOT/'results') as directory:
        target = Path(directory)
        for name in ('source.json','code.npz'):shutil.copy(ROOT/name,target/name)
        (target/'plan.json').write_text('{"qualification_only":true}\n')
        plan = r.design();job = {'id':'qualification-tuned-bp','arm':'tuned_bp','physical_p':.08}
        plan['jobs'] = [job]
        plan['protocol'].update(coarse_shots=3,finalist_shots=4,finalist_failures=2,max_shots=5,target_failures=2)
        with monkeypatch.context() as m:
            m.setattr(r,'ROOT',target);m.setattr(r.rt,'load',lambda path:plan)
            original = r.proposals;m.setattr(r,'proposals',lambda arm:[original(arm)[0],original(arm)[-1]])
            r.code.cache_clear();r.execute(0)
            point = target/'results'/job['id'];before = {str(p):r.rt.sha(p) for p in point.rglob('chunk-*.gz')}
            r.execute(0)
            assert before=={str(p):r.rt.sha(p) for p in point.rglob('chunk-*.gz')}
            r.execute(0,audit=True)
            assert json.loads((point/'audit.json').read_text())==json.loads((point/'complete.json').read_text())
            selection = json.loads((point/'selection.json').read_text());selection['chosen']['alpha']=.123
            (point/'selection.json').write_text(json.dumps(selection))
            with pytest.raises(ValueError,match='frozen selection differs'):r.execute(0,audit=True)
        r.code.cache_clear()
