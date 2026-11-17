"""Ordered speculative continuation preserves the original stopped prefix."""
import importlib.util
import json
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pytest
from test_memory_benchmark import campaign

STUDY=Path(__file__).resolve().parents[1]/'data/reproductions/priortilt-2611-13373'


def module(run,monkeypatch):
    monkeypatch.setitem(sys.modules,'run',run)
    s=importlib.util.spec_from_file_location('parallel_test',STUDY/'parallel.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def merged(p,root,job,basis):
    a=[p.arrays(f) for f in sorted((root/'results'/job['id']/basis).glob('chunk-*.npz'))]
    return {k:np.concatenate([d[k] for d in a]) for k in ('candidate','prediction','stats','trace')}


@pytest.mark.parametrize('index',range(3))
@pytest.mark.parametrize('target',(1,2))
def test_parallel_order_prefix_and_stage_reuse_matches_sequential(campaign,monkeypatch,index,target):
    import shutil
    run,plan,c=campaign;p=module(run,monkeypatch);job=plan['jobs'][index]
    plan['protocol']['target_errors']=target;run.write_json(run.ROOT/'plan.json',plan)
    run.execute(index);expected={b:merged(p,run.ROOT,job,b) for b in run.BASES};old=run.ROOT
    new=old/'parallel';new.mkdir();(new/'circuits').symlink_to(old/'circuits',target_is_directory=True);run.write_json(new/'plan.json',plan)
    dest=new/'results'/job['id'];dest.mkdir(parents=True);(new/'results/noise').symlink_to(old/'results/noise',target_is_directory=True)
    models={b:run.case_model(job,b) for b in run.BASES};run.ROOT=new
    p.initialize(plan,job,{b:m.execution_sha256 for b,(c,m) in models.items()},str(new))
    summaries={b:run.empty_summary() for b in run.BASES}
    with ThreadPoolExecutor(max_workers=10) as pool:
        p.continue_point(pool,plan,job,summaries,models,'fixture',10)
        audited=p.scan(pool,plan,job)
        assert audited==summaries
        # Cached sealed stage reuse validates and replays endpoints.
        assert p.unit('x',0)[1]==0
    for b in run.BASES:
        actual=merged(p,new,job,b)
        for k in actual:np.testing.assert_array_equal(actual[k],expected[b][k])
    cost=p.expenditure(plan,job,summaries)
    assert cost['computed']['shots']>=cost['retained']['shots']
    assert cost['retained']['shots']==sum(v['shots'] for v in summaries.values())


def test_retained_prefix_first_failure_and_trace_slicing(campaign,monkeypatch):
    run,plan,c=campaign;p=module(run,monkeypatch)
    prediction=np.array([[0],[1],[0],[1],[1]],np.uint8);obs=np.zeros_like(prediction)
    assert p.retained_length(prediction,obs,2)==4
    assert p.retained_length(prediction,obs,5)==5
    data={'candidate':prediction,'trace_ptr':np.array([0,1,1,3,5,7]),'trace':np.zeros((7,8),np.int64)}
    a=p.prefix(data,4);assert len(a['trace_ptr'])==5 and len(a['trace'])==5 and len(a['candidate'])==4
