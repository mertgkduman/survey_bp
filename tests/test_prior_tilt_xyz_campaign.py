"""XYZ campaign resume, stopping and parallel ordering use separate immutable evidence."""
import importlib.util
import json
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pytest
import stim
from bp_registry.canonical.prior_tilt import PriorTiltSpec
from bp_registry.circuit.relay_list import RelayListSpec

STUDY=Path(__file__).resolve().parents[1]/'data/reproductions/priortilt-2611-13373-xyz'


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


@pytest.fixture
def xyz(tmp_path,monkeypatch):
    run=load('xyz_run_test',STUDY/'run.py');run.ROOT=tmp_path
    (tmp_path/'circuits').mkdir()
    c=stim.Circuit.generated('repetition_code:memory',distance=3,rounds=3,after_clifford_depolarization=.03,before_round_data_depolarization=.03,before_measure_flip_probability=.03,after_reset_flip_probability=.03)
    c.to_file(str(tmp_path/'circuits/memory.stim'));case={'file':'memory.stim','sha256':run.sha(tmp_path/'circuits/memory.stim')}
    jobs=[{'id':'fixture-'+m,'code':'fixture','p':.03,'cycles':3,'method':m,'bases':{'x':case,'z':case}} for m in run.METHODS]
    plan={'jobs':jobs,'software':run.software(),'protocol':{'batch':3,'target_errors':1,'max_shots':12,'noise_seed':100,'policy_seed':200,'minimum_free_bytes':0}}
    run.write_json(tmp_path/'plan.json',plan);monkeypatch.setattr(run,'load',lambda:plan)
    monkeypatch.setattr(run,'spec_for',lambda j:PriorTiltSpec(initial=2,round_len=1,rounds=2) if j['method']=='priortilt' else RelayListSpec(initial=2,per_leg=1,additional=3,results=2))
    monkeypatch.setitem(sys.modules,'run',run);parallel=load('xyz_parallel_test',STUDY/'parallel.py')
    return run,parallel,plan


def science(parallel,folder,basis):
    arrays=[parallel.arrays(p) for p in sorted((folder/basis).glob('chunk-*.npz'))]
    return {k:np.concatenate([a[k] for a in arrays]) for k in ('candidate','prediction','stats','trace')}


@pytest.mark.parametrize('index',(0,1))
def test_sequential_parallel_same_prefix_resume_and_tamper(xyz,index):
    run,p,plan=xyz;job=plan['jobs'][index];old=run.ROOT
    run.execute(index);run.execute(index,audit=True)
    expected={b:science(p,old/'results'/job['id'],b) for b in run.BASES}
    new=old/'parallel';new.mkdir();(new/'circuits').symlink_to(old/'circuits',target_is_directory=True)
    (new/'results').mkdir();(new/'results/noise').symlink_to(old/'results/noise',target_is_directory=True)
    models={b:run.case_model(job,b) for b in run.BASES};run.ROOT=new;run.write_json(new/'plan.json',plan)
    p.initialize(plan,job,{b:m.execution_sha256 for b,(c,m) in models.items()},str(new))
    summaries={b:run.empty_summary() for b in run.BASES}
    with ThreadPoolExecutor(max_workers=4) as pool:
        p.continue_point(pool,plan,job,summaries,models,'fixture',4)
        assert p.scan(pool,plan,job)==summaries
    for b in run.BASES:
        actual=science(p,new/'results'/job['id'],b)
        for k in expected[b]:np.testing.assert_array_equal(actual[k],expected[b][k])
    cost=p.expenditure(plan,job,summaries)
    assert cost['computed']['shots']==cost['retained']['shots']+cost['speculative']['shots']
    marker=next((new/'results'/job['id']/'x').glob('chunk-*.json'));m=json.loads(marker.read_text());m['noise_offset']+=1;run.write_json(marker,m)
    with pytest.raises(ValueError):p.checked_unit('x',str(marker))


def test_source_grids_and_paper_budget():
    run=load('xyz_design_test',STUDY/'run.py');plan=run.design()
    assert len(plan['jobs'])==2 and {j['method'] for j in plan['jobs']}=={'priortilt','relay5'}
    assert run.spec_for(plan['jobs'][0]).rounds==6000
    r=run.spec_for(plan['jobs'][1]);assert r.initial+r.per_leg*r.additional==36080 and r.results==5
    assert all('xyz_memory_' in c['file'] for j in plan['jobs'] for c in j['bases'].values())


def test_empty_and_completed_but_unaudited_points_are_not_published(xyz,monkeypatch):
    run,p,plan=xyz
    (run.ROOT/'source-table4.csv').write_bytes((STUDY/'source-table4.csv').read_bytes())
    monkeypatch.setitem(sys.modules,'parallel',p);monkeypatch.setattr(p,'load_amendment',lambda:{})
    report=load('xyz_report_test',STUDY/'report.py');report.collect()
    import csv
    assert not list(csv.DictReader((run.ROOT/'comparison.csv').open()))
    assert 'No completed local measurements yet' in (run.ROOT/'RESULTS.md').read_text()
    run.execute(0);report.collect()
    assert not list(csv.DictReader((run.ROOT/'comparison.csv').open()))


def test_report_rejects_changed_audited_manifest(xyz,monkeypatch):
    run,p,plan=xyz
    (run.ROOT/'source-table4.csv').write_bytes((STUDY/'source-table4.csv').read_bytes())
    monkeypatch.setitem(sys.modules,'parallel',p);monkeypatch.setattr(p,'load_amendment',lambda:{})
    report=load('xyz_report_tamper_test',STUDY/'report.py')
    run.execute(0);run.execute(0,audit=True)
    path=run.ROOT/'results'/plan['jobs'][0]['id']/'manifest.json';path.write_text('{}')
    with pytest.raises(ValueError,match='manifest'):report.collect()


def test_frozen_production_cannot_use_sequential_or_wrong_cpu_worker(xyz,monkeypatch):
    run,p,plan=xyz;plan['implementation_sha256']={}
    with pytest.raises(ValueError,match='50-process'):run.execute(0)
    monkeypatch.setenv('SLURM_CPUS_PER_TASK','1')
    with pytest.raises(ValueError,match='50 workers'):p.execute(0,50)
    monkeypatch.setenv('SLURM_CPUS_PER_TASK','50')
    with pytest.raises(ValueError,match='50 workers'):p.execute(0,10)
