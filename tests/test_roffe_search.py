"""Numerical, controller and prospective-study qualification."""
import importlib.util
from pathlib import Path
import sys
from dataclasses import replace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'data/reproductions/roffe-2005-07016-search'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); sys.modules[name] = value; spec.loader.exec_module(value)
    return value


engine = module('_roffe_search_engine', STUDY / 'engine.py')
reference = module('_search_test_reference', STUDY / 'reference.py')


def graph(h):
    from bp_registry.canonical.compiled import CompiledBinaryFlooding
    from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
    from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy
    policy = BpFloodingPolicy(check_rule='min_sum', resolution=ResolutionPolicy('float64'),
                             zero_syndrome_shortcut=False, check_stabilization='exact_unity',
                             version='bp-flooding-policy-v2', product_epsilon=1e-10)
    return CompiledBinaryFlooding.from_check_matrix(h, rule='min_sum', profile=BINARY_SPA_F64_V2, policy=policy)


@pytest.mark.parametrize('method', ['beam', 'relay'])
@pytest.mark.parametrize('settings', [dict(), dict(damping=0., alpha=.75, paper_scale=False, beta=.25, solutions=4),
                                      dict(damping=.7, width=1, first_gamma=.35, gamma_low=-.5, gamma_high=.95)])
def test_independent_algebra_and_complete_search(method, settings):
    h = np.array([[1,1,0,1,0,0], [0,1,1,0,1,0], [1,0,1,0,0,1], [0,0,0,1,1,1]], dtype=np.uint8)
    c = engine.Controls(method, initial=3, per_unit=3, units=16, rounds=4, **settings)
    prepared = engine.Prepared(graph(h), .07, c, 2026111551)
    for shot in range(12):
        truth = np.random.default_rng(shot).integers(0, 2, h.shape[1], dtype=np.uint8)
        syndrome = (h @ truth) % 2
        fast = prepared.decode(syndrome, shot)
        slow = reference.decode(h, syndrome, prepared.initial, prepared.prior, c, prepared.seed, shot)
        assert fast[2:4] == slow[2:4]
        for index in (0, 1, 4, 5, 6, 7):
            np.testing.assert_array_equal(fast[index], slow[index])
        assert fast[2] == np.array_equal((h @ fast[0]) % 2, syndrome)
        assert np.all(np.isfinite(fast[6])) and np.all(np.isfinite(fast[7]))


@pytest.mark.parametrize('method', ['beam', 'relay'])
def test_real_toric_source_code(method):
    data = np.load(ROOT / 'data/reproductions/roffe-2005-07016-bp/codes/toric9.npz')
    h = data['hz']
    c = engine.Controls(method, initial=5, per_unit=5, units=12, width=2, rounds=4,
                        solutions=2, first_gamma=.125)
    prepared = engine.Prepared(graph(h), .03, c, 2026111551)
    for shot in range(8):
        truth = (np.random.default_rng(shot+17).random(h.shape[1]) < .03).astype(np.uint8)
        s = (h @ truth) % 2
        a = prepared.decode(s, shot)
        b = reference.decode(h, s, prepared.initial, prepared.prior, c, prepared.seed, shot)
        assert a[2:4] == b[2:4]
        for index in (0,1,4,5,6,7):
            np.testing.assert_array_equal(a[index], b[index])


def test_degree_one_empty_checks_and_all_fixed():
    h = np.array([[1,0], [0,1], [0,0]], dtype=np.uint8)
    c = engine.Controls('beam', initial=1, per_unit=1, units=4, damping=0., paper_scale=False)
    p = engine.Prepared(graph(h), .1, c, 27)
    for s in (np.array([1,0,0], dtype=np.uint8), np.array([0,0,1], dtype=np.uint8)):
        a = p.decode(s); b = reference.decode(h, s, p.initial, p.prior, c, 27, 0)
        assert a[2:4] == b[2:4]
        for i in (0,1,4,5,6,7): np.testing.assert_array_equal(a[i], b[i])


def test_random_stream_control_independent_and_exact():
    for shot in (0, 999, 100000000):
        for leg in (1, 30, 128):
            for v in (0, 161):
                assert engine.uniform(2026111551, shot, leg, v) == reference.uniform(2026111551, shot, leg, v)


@pytest.mark.parametrize('kwargs', [dict(method='x'), dict(method='beam', damping=1.),
                                    dict(method='relay', gamma_low=.7, gamma_high=.6),
                                    dict(method='beam', units=0)])
def test_reject_invalid_controls(kwargs):
    with pytest.raises(ValueError): engine.Controls(**kwargs)


def campaign_module():
    return module('_test_roffe_search_campaign',STUDY/'run.py')


def test_tuning_grid_covers_numerics_memory_and_topology():
    run=campaign_module();r=run.execution;plan=run.design()
    assert len(plan['jobs'])==218
    assert len({(j['code'],j['physical_p']) for j in plan['jobs']})==109
    assert {j['method'] for j in plan['jobs']}=={'beam','relay'}
    assert all(j['workers']==1 and j['decoder']['noise_model']=='x_only' for j in plan['jobs'])
    assert len(set(r.SEEDS.values()))==3 and set(r.BUDGETS)=={.5,1.,2.,4.}
    assert len(r.numeric_grid('beam'))==24
    for method in ('beam','relay'):
        grid=r.architecture_grid(r.numeric_grid(method)[0])
        assert {c.solutions for c in grid}=={1,4}
        assert len({c.initial for c in grid})==3
    assert any(c.gamma_low<0 for c in r.memory_grid(r.numeric_grid('relay')[0]))


def test_ler_first_latency_budget_and_stable_ties():
    r=campaign_module().execution
    def row(rate,ratio,iterations):
        return {'rate':rate,'runtime_ratio':ratio,'iterations':iterations,'shots':100,'controls':{'a':iterations}}
    a,b,c=row(.1,.9,100),row(.05,1.05,200),row(0.,1.5,1)
    assert r.choose([a,b,c],1.) is b
    b['rate']=.1
    assert r.choose([a,b,c],1.) is a
    assert r.choose([a,b,c],.5) is a
    assert r.choose([a,b,c],2.) is c


def test_real_pipeline_resume_selection_audit_catalog_and_tamper(monkeypatch):
    import tempfile,json
    run=campaign_module();r=run.execution;rt=run.rt
    with tempfile.TemporaryDirectory(prefix='search-pipeline-',dir=ROOT/'.git') as directory:
        root=Path(directory);plan=run.design()
        plan['jobs']=[j for j in plan['jobs'] if j['code']=='toric9' and j['method']=='beam' and j['physical_p'] in (.04,.05)]
        plan['protocol'].update(reference_shots=4,reference_repeats=1,coarse_shots=4,
                                finalist_shots=4,finalist_failures=20,max_shots=8,target_failures=20)
        rt.freeze(root,plan,run.extra())
        c=engine.Controls('beam',initial=2,per_unit=2,units=2,width=1,rounds=1)
        monkeypatch.setattr(r,'numeric_grid',lambda _: [c])
        monkeypatch.setattr(r,'architecture_grid',lambda _: [c])
        monkeypatch.setattr(r,'neighbors',lambda _: [c])
        for index,job in enumerate(plan['jobs']):
            r.execute(root,index)
            point=root/'results'/job['id'];before=(point/'selection.json').read_bytes()
            r.execute(root,index)
            assert (point/'selection.json').read_bytes()==before
        receipt=r.collect(root,True)
        assert len(receipt['finished_strata'])==2 and len(receipt['points'])==2
        assert all(row['shots']==8 for row in receipt['points'])
        report=module('_search_pipeline_report',STUDY/'report.py');assessment=report.report(root,receipt)
        assert assessment['confirmed_shots']==16
        extension=json.loads((root/'catalog.json').read_text())
        assert len(extension['result_series'])==1 and len(extension['result_series'][0]['points'])==2
        assert 'width=1' in extension['decoders'][0]['label']
        row=receipt['points'][0];path=rt.REPO/row['directory']/'summary.json'
        altered=json.loads(path.read_text());altered['iterations']+=1;path.write_text(json.dumps(altered))
        with pytest.raises(ValueError,match='summary mismatch'):r.collect(root)


def test_ledger_rejects_hidden_pruned_work_bad_reference_and_selection(tmp_path):
    from copy import deepcopy
    r=campaign_module().execution;rt=r.rt
    source=next(j for j in rt.load(r.ORIGINAL)['jobs'] if j['code']=='toric9' and j['arm']=='binary_ms' and j['physical_p']==.06)
    source={**source,'method':'beam','n':162}
    c=engine.Controls('beam',initial=2,per_unit=2,units=4)
    protocol={'coarse_shots':8,'finalist_shots':8,'max_shots':8,'finalist_failures':20,'target_failures':20}
    job=r.child_job(source,c,'confirmation',protocol);base=r.base_state(source)
    p=engine.Prepared(base[3][0],.06,c,job['seed'])
    ref={'mean_ns':100.,'sha256':'0'*64,'stage':'confirmation'}
    row=r.event(base,p,job,0,ref)
    assert len(row['units'])>1
    for field,value in [('iterations',row['units'][0][3]),('directed_edge_updates',0),('selected_unit',999),('reference_ns',101.)]:
        altered=deepcopy(row);altered[field]=value
        ledger=r.Ledger(tmp_path,job,{'0'*64:ref})
        with pytest.raises(ValueError):ledger.add(altered,b'x')


def test_dispatch_one_cpu_per_point_idempotent_and_full_audit(tmp_path,monkeypatch):
    from types import SimpleNamespace
    run=campaign_module();plan=run.design();calls=[]
    monkeypatch.setattr(run,'ROOT',tmp_path);monkeypatch.setattr(run.rt,'load',lambda _:plan)
    (tmp_path/'plan.json').write_text('{}')
    def queue(argv,**kwargs):
        calls.append(argv);return SimpleNamespace(stdout=f'{9900+len(calls)}\n',stderr='')
    monkeypatch.setattr(run.subprocess,'run',queue)
    run.submit();run.submit()
    assert len(calls)==2 and '--array=0-217%218' in calls[0] and '--cpus-per-task=1' in calls[0]
    assert '--mem=2G' in calls[0] and '--mem=16G' in calls[1] and '--dependency=afterok:9901' in calls[1]
    assert calls[1][-1].endswith('--collect --complete') and 'NUMBA_CACHE_DIR' in calls[0][-1]


def test_cache_reloads_across_fresh_processes(tmp_path):
    import os,subprocess
    script="""import importlib.util,numpy as np
from pathlib import Path
p=Path('data/reproductions/roffe-2005-07016-search/runtime.py')
s=importlib.util.spec_from_file_location('_search_cache_test',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
j=next(j for j in m.rt.load(m.ORIGINAL)['jobs'] if j['arm']=='binary_ms')
b=m.base_state(j);p=m.engine.Prepared(b[3][0],j['physical_p'],m.engine.Controls('beam'),11)
assert p.decode(np.zeros(len(p.graph.row_ptr)-1,dtype=np.uint8))[2]
"""
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'NUMBA_CACHE_DIR':str(tmp_path/'cache'),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
    for _ in range(2):subprocess.run([sys.executable,'-c',script],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
