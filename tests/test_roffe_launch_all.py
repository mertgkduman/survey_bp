"""Execution-only resources, idempotence and compatibility with frozen submitter."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

REPO=Path(__file__).resolve().parents[1]

def module(name,path):
    s=importlib.util.spec_from_file_location(name,REPO/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

launch=module('_test_roffe_launch_all','data/reproductions/roffe-2005-07016-bp/launch_all.py')
old=module('_test_roffe_original_submit','data/reproductions/roffe-2005-07016-bp/run.py')


def setup(tmp_path,monkeypatch):
    plan=launch.rt.load(launch.ROOT)
    (tmp_path/'plan.json').write_text(json.dumps(plan))
    monkeypatch.setattr(launch,'ROOT',tmp_path)
    monkeypatch.setattr(old,'ROOT',tmp_path)
    monkeypatch.setattr(launch.rt,'load',lambda root:plan)
    return plan


def test_one_cpu_per_point_complete_audit_and_no_duplicate_old_continuation(tmp_path,monkeypatch):
    plan=setup(tmp_path,monkeypatch);calls=[]
    def queue(argv,**kwargs):
        calls.append(argv);return SimpleNamespace(stdout=str(9000+len(calls))+'\n',stderr='')
    monkeypatch.setattr(launch.subprocess,'run',queue)
    launch.submit();launch.submit();old.submit()
    assert len(calls)==2 and len(plan['jobs'])==218
    assert '--array=0-217%218' in calls[0] and '--cpus-per-task=1' in calls[0]
    assert '--ntasks=1' in calls[0]
    assert any('OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1' in x for x in calls[0])
    assert '--dependency=afterok:9001' in calls[1]
    assert calls[1][-1].endswith('--collect --complete')
    receipt=json.loads((tmp_path/'launch-all.json').read_text())
    assert receipt['points']==218 and receipt['maximum_concurrent_points']==218
    assert receipt['cpus_per_point']==1 and receipt['macKay_continues']


def test_partial_submission_recovers_collector_without_new_array(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch);calls=[]
    def queue(argv,**kwargs):
        calls.append(argv)
        if len(calls)==2:raise RuntimeError('temporary collector submission failure')
        return SimpleNamespace(stdout=str(9000+len(calls))+'\n',stderr='')
    monkeypatch.setattr(launch.subprocess,'run',queue)
    with pytest.raises(RuntimeError):launch.submit()
    launch.submit()
    assert len(calls)==3 and sum(any(x.startswith('--array=') for x in c) for c in calls)==1
    assert '--dependency=afterok:9001' in calls[-1]


def test_preflight_does_not_record_dispatch_or_launch_collector(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch);calls=[]
    monkeypatch.setattr(launch.subprocess,'run',lambda argv,**kw:(calls.append(argv) or SimpleNamespace(stdout='',stderr='accepted')))
    launch.submit(test_only=True)
    assert len(calls)==1 and '--test-only' in calls[0]
    assert not (tmp_path/'dispatch.json').exists() and not (tmp_path/'launch-all.json').exists()


def test_existing_wrong_resource_dispatch_is_not_duplicated(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch)
    (tmp_path/'dispatch.json').write_text(json.dumps({'array':{'id':'123','argv':['--array=0-217%16']}}))
    monkeypatch.setattr(launch.subprocess,'run',lambda *a,**k:pytest.fail('must not resubmit'))
    with pytest.raises(ValueError,match='different resources'):launch.submit()


def test_scientific_plan_is_unchanged():
    p=launch.rt.load(launch.ROOT)
    assert launch.rt.sha(launch.ROOT/'plan.json')=='eb16126dfa9eef45bb24eeddd70c5b287259e376b52a1531efcbf6126da9dcc3'
    assert all(j['workers']==1 and j['target_block_failures']==20 and j['max_shots']==100_000_000 for j in p['jobs'])
    assert {j['decoder']['max_iterations'] for j in p['jobs']}=={162,242,338,450}
