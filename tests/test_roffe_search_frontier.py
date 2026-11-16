"""Training-only latency diversity, fresh seed locks and scheduler ordering."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

import pytest

REPO=Path(__file__).resolve().parents[1]
STUDY=REPO/'data/reproductions/roffe-2005-07016-search-frontier'
spec=importlib.util.spec_from_file_location('_test_search_frontier',STUDY/'run.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
r=run.r


def fake(c,ratio,rate=0.,iterations=100):
    return {'controls':c.evidence(),'runtime_ratio':ratio,'rate':rate,'iterations':iterations,'shots':512}


def training():
    c=r.engine.Controls('beam',initial=5,per_unit=5,units=8,width=1,rounds=4)
    from dataclasses import replace
    rows=[fake(c,.1,iterations=1)]
    for ratio,width in ((.5,2),(1.,4),(2.,8),(4.,16)):
        rows += [fake(replace(c,width=width,solutions=s),ratio,iterations=100*width) for s in (1,4)]
    return {'coarse':rows,'confirmations':[{'controls':c.evidence(),'budgets':[.5,1.,2.,4.]}]}


def test_zero_failure_screen_keeps_fast_and_budget_spanning_topologies():
    value=training();chosen=run.proposals(value)
    assert value['coarse'][0]['controls'] in chosen
    assert {c['width'] for c in chosen}=={1,2,4,8,16}
    assert {c['solutions'] for c in chosen}=={1,4}
    assert len(chosen)==len({r.identity(c) for c in chosen})


def test_parent_confirmation_outcomes_do_not_influence_proposals():
    a=training();b=deepcopy(a)
    b['confirmation_outcomes']={'failures':100,'rate':1.}
    b['confirmations'][0]['observed_ler']=1.
    assert run.proposals(a)==run.proposals(b)


def test_frontier_plan_preserves_original_grid_and_uses_two_new_seeds():
    plan=run.design()
    assert len(plan['jobs'])==218
    assert len({(j['code'],j['physical_p']) for j in plan['jobs']})==109
    assert all(j['id']==j['parent_job_id']+'-frontier' and j['workers']==1 for j in plan['jobs'])
    assert plan['protocol']['seeds']['finalist']==2026111562
    assert plan['protocol']['seeds']['confirmation']==2026111563
    assert plan['parent_plan_sha256']==r.rt.sha(run.PARENT/'plan.json')


def test_parent_link_rejects_missing_or_substituted_finalists(monkeypatch):
    parent=training();proposed=run.proposals(parent)
    monkeypatch.setattr(run,'parent_selection',lambda _:({},parent,'a'*64))
    value={'parent_selection_sha256':'a'*64,'parent_plan_sha256':r.rt.sha(run.PARENT/'plan.json'),
           'proposed_controls':proposed,'finalists':[{'controls':c} for c in proposed]}
    run.validate_parent_link({},value)
    value['finalists'].pop()
    with pytest.raises(ValueError,match='missing or substituted'):run.validate_parent_link({},value)


def test_real_new_seed_pipeline_exact_resume_full_ledger_and_parent_lock(monkeypatch):
    with tempfile.TemporaryDirectory(prefix='search-frontier-',dir=REPO/'.git',ignore_cleanup_errors=True) as directory:
        root=Path(directory);plan=run.design()
        plan['jobs']=[j for j in plan['jobs'] if j['code']=='toric9' and j['physical_p']==.04 and j['method']=='beam']
        plan['protocol'].update(reference_shots=4,reference_repeats=1,finalist_shots=4,finalist_failures=20,max_shots=8,target_failures=20)
        r.rt.freeze(root,plan,run.extra());monkeypatch.setattr(run,'ROOT',root)
        c=r.engine.Controls('beam',initial=2,per_unit=2,units=2,width=1,rounds=1)
        parent={'coarse':[fake(c,.5)],'confirmations':[{'controls':c.evidence(),'budgets':[.5,1.,2.,4.]}]}
        monkeypatch.setattr(run,'parent_selection',lambda _:({},parent,'a'*64))
        run.execute(0);point=root/'results'/plan['jobs'][0]['id'];before=(point/'selection.json').read_bytes()
        run.execute(0);assert (point/'selection.json').read_bytes()==before
        value=json.loads(before);assert value['coarse']==[] and len(value['finalists'])==1
        assert value['finalists'][0]['job']['seed']==2026111562
        receipt=r.collect(root,True)
        assert len(receipt['points'])==1 and receipt['points'][0]['job']['seed']==2026111563
        assert receipt['points'][0]['shots']==8
        value['parent_selection_sha256']='b'*64
        with pytest.raises(ValueError,match='immutable parent training'):run.validate_parent_link(plan['jobs'][0],value)


def test_new_collection_requires_complete_parent_audit(tmp_path,monkeypatch):
    import gzip
    plan=run.design();(tmp_path/'plan.json').write_text('{}')
    with gzip.open(tmp_path/'verified.json.gz','wt') as stream:
        json.dump({'plan_sha256':r.rt.sha(tmp_path/'plan.json'),'finished_strata':[]},stream)
    monkeypatch.setattr(run,'PARENT',tmp_path)
    original=r.rt.load
    monkeypatch.setattr(r.rt,'load',lambda path:plan if path==run.ROOT else {'jobs':[{'id':'required'}]})
    with pytest.raises(ValueError,match='complete parent training audit'):run.collect(False)


def test_corresponding_array_and_both_audits_are_required(tmp_path,monkeypatch):
    plan=run.design();parent=tmp_path/'parent';parent.mkdir();root=tmp_path/'study';root.mkdir()
    (parent/'dispatch.json').write_text(json.dumps({'array':{'id':'8801'},'collect':{'id':'8802'}}))
    (root/'plan.json').write_text('{}');calls=[]
    monkeypatch.setattr(run,'ROOT',root);monkeypatch.setattr(run,'PARENT',parent)
    monkeypatch.setattr(r.rt,'load',lambda _:plan)
    def queue(argv,**kwargs):
        calls.append(argv);return SimpleNamespace(stdout=f'{9900+len(calls)}\n',stderr='')
    monkeypatch.setattr(run.subprocess,'run',queue)
    run.submit();run.submit()
    assert len(calls)==2 and '--dependency=aftercorr:8801' in calls[0]
    assert '--dependency=afterok:9901:8802' in calls[1]
    assert '--cpus-per-task=1' in calls[0] and '--mem=2G' in calls[0] and '--mem=16G' in calls[1]
