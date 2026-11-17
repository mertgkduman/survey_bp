"""Original-DEM logical evaluation and resumable paired-memory evidence checks."""
import copy
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest
import stim
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.memory_benchmark import audit_candidates,source_masks,validate_trace
from bp_registry.canonical.prior_tilt import PriorTiltSpec
from bp_registry.circuit.paper_decoders import PaperDecoderSpec

STUDY=Path(__file__).resolve().parents[1]/'data/reproductions/priortilt-2611-13373'


def module():
    spec=importlib.util.spec_from_file_location('priortilt_campaign_test',STUDY/'run.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_original_dem_evaluation_separates_nonconvergence_from_observable_error():
    dem=stim.DetectorErrorModel('error(0.1) D0 L0\nerror(0.2) D1\ndetector D2')
    d,o=source_masks(dem)
    candidates=np.array([[0],[1],[2],[3]],np.uint8)
    det=np.array([[4],[1],[2],[3]],np.uint8) # first equation is impossible
    obs=np.array([[0],[0],[0],[1]],np.uint8);pred=np.array([[0],[1],[0],[1]],np.uint8)
    stats=np.zeros((4,6),np.uint64);stats[:,2]=[0,1,1,1]
    # 1 logical failure; the nonconverged but correct shot is a separate count.
    np.testing.assert_array_equal(audit_candidates(candidates,det,obs,pred,stats,d,o),[4,1,2,1,1,0])
    with pytest.raises(ValueError,match='prediction'):
        audit_candidates(candidates,det,obs,np.zeros_like(pred),stats,d,o)
    changed=stats.copy();changed[0,2]=1
    with pytest.raises(ValueError,match='convergence'):audit_candidates(candidates,det,obs,pred,changed,d,o)
    candidates[0]=128
    with pytest.raises(ValueError,match='padding'):audit_candidates(candidates,det,obs,pred,stats,d,o)


@pytest.mark.parametrize('p',[0.,.5,1.])
def test_original_dem_evaluator_rejects_bias_folding_or_dropped_columns(p):
    with pytest.raises(ValueError):source_masks(stim.DetectorErrorModel(f'error({p}) D0'))


@pytest.fixture
def campaign(tmp_path,monkeypatch):
    run=module();monkeypatch.setattr(run,'ROOT',tmp_path)
    (tmp_path/'circuits').mkdir()
    c=stim.Circuit.generated('repetition_code:memory',distance=3,rounds=3,after_clifford_depolarization=.03,
                             before_round_data_depolarization=.03,before_measure_flip_probability=.03,after_reset_flip_probability=.03)
    c.to_file(str(tmp_path/'circuits/memory.stim'));case={'file':'memory.stim','sha256':run.sha(tmp_path/'circuits/memory.stim')}
    jobs=[{'id':'fixture-'+method,'code':'fixture','p':.03,'cycles':3,'method':method,'bases':{'x':case,'z':case}} for method in run.METHODS]
    plan={'jobs':jobs,'software':run.software(),'protocol':{'batch':7,'target_errors':2,'max_shots':21,'noise_seed':100,'policy_seed':200,'minimum_free_bytes':0}}
    run.write_json(tmp_path/'plan.json',plan);monkeypatch.setattr(run,'load',lambda:plan)
    def policy(j):
        if j['method']=='priortilt':return PriorTiltSpec(initial=2,round_len=1,rounds=2)
        return PaperDecoderSpec(method=j['method'],initial=2,per_leg=1,**({'additional':2} if j['method']=='relay' else {'width':2,'rounds':2}))
    monkeypatch.setattr(run,'spec_for',policy)
    return run,plan,c


@pytest.mark.parametrize('index',range(3))
def test_worker_complete_resume_fresh_audit_and_tamper(campaign,index):
    run,plan,c=campaign;job=plan['jobs'][index];root=run.ROOT/'results'/job['id']
    run.execute(index);complete=(root/'complete.json').read_bytes()
    run.execute(index);assert (root/'complete.json').read_bytes()==complete
    run.execute(index,audit=True);receipt=json.loads((root/'audit.json').read_text())
    for s in receipt['bases'].values():
        assert s['errors']==2 or s['shots']==21
        assert s['shots']==sum(s['joint_counts'])
        assert s['ci975'][0]<=s['rate']<=s['ci975'][1]
    marker=next((root/'x').glob('chunk-*.json'));meta=json.loads(marker.read_text())
    meta['noise_offset']+=1;run.write_json(marker,meta)
    with pytest.raises(ValueError,match='sample identity'):run.execute(index,audit=True)


def test_worker_resumes_only_committed_contiguous_prefix(campaign):
    run,plan,c=campaign;job=plan['jobs'][0];root=run.ROOT/'results'/job['id']
    run.execute(0);completed=json.loads((root/'complete.json').read_text())
    marker=sorted((root/'x').glob('chunk-*.json'))[-1];original=json.loads(marker.read_text());data=marker.with_suffix('.npz')
    marker.unlink();(root/'complete.json').unlink()
    data.write_bytes(b'uncommitted crash output')
    run.execute(0);run.execute(0,audit=True)
    restored=json.loads((root/'complete.json').read_text())
    # Wall-clock timing is new, but logical outcomes/work/random identity match.
    for b in ('x','z'):
        for k in ('shots','errors','iterations','directed_edge_updates','joint_counts','random_draws','biased_node_updates'):
            assert completed['bases'][b][k]==restored['bases'][b][k]
    assert json.loads(marker.read_text())['start']==original['start']


def test_samples_are_shared_across_methods_and_seed_changes_are_rejected(campaign):
    run,plan,c=campaign
    a,ma,aa=run.noise(plan,plan['jobs'][0],'x',0,c);b,mb,bb=run.noise(plan,plan['jobs'][1],'x',0,c)
    assert a==b and ma==mb
    np.testing.assert_array_equal(aa['detectors'],bb['detectors'])
    assert run.seed(plan,plan['jobs'][0],'x','policy')!=run.seed(plan,plan['jobs'][1],'x','policy')
    changed=copy.deepcopy(plan);changed['protocol']['noise_seed']+=1
    with pytest.raises(ValueError,match='sealed noise'):run.noise(changed,plan['jobs'][0],'x',0,c)


def test_frozen_design_has_39_points_and_exact_source_rates():
    d=module().design();assert len(d['jobs'])==39
    assert {j['p'] for j in d['jobs'] if j['code']=='BB144'}=={.001,.002,.003,.004,.005}
    assert {j['p'] for j in d['jobs'] if j['code']=='GB102'}=={.0005,.0008,.001,.002}
    assert all(j['bases']['x']['syndrome_rounds']==j['bases']['z']['syndrome_rounds']==j['cycles'] for j in d['jobs'])


def test_intervals_include_valid_zero_error_upper_bound():
    run=module();lo,hi=run.interval(100,0,20)
    assert lo==0 and 0<hi<1
    assert hi==pytest.approx(1-(.025/2)**.01)
    assert run.interval(20,20,20)[1]==1.


def test_exact_failure_target_prefix_and_reject_poststop_chunks(campaign):
    run,plan,c=campaign;plan['protocol']['target_errors']=1;run.write_json(run.ROOT/'plan.json',plan)
    run.execute(0);run.execute(0,audit=True)
    root=run.ROOT/'results'/plan['jobs'][0]['id'];a=json.loads((root/'audit.json').read_text())
    assert a['bases']['x']['errors']==1 and a['bases']['x']['shots']<=7
    # Even a self-consistent repeated marker cannot extend a terminal prefix.
    old=next((root/'x').glob('chunk-*.json'));new=old.with_name('chunk-99999999.json');new.write_bytes(old.read_bytes())
    with pytest.raises(ValueError,match='after stopping'):run.execute(0,audit=True)


def report_module(run,monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules,'run',run)
    spec=importlib.util.spec_from_file_location('priortilt_report_test',STUDY/'report.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_report_empty_and_audited_only_with_original_denominators(campaign,monkeypatch):
    import csv
    run,plan,c=campaign;report=report_module(run,monkeypatch)
    (run.ROOT/'source-figure1.csv').write_text('code,p,method,ler_per_cycle,published_1sigma\nfixture,0.03,PriorTilt_3phase,0.01,0.001\n')
    assert report.rows(plan)==[]
    run.execute(0);assert report.rows(plan)==[] # a completed worker alone is insufficient
    run.execute(0,audit=True);rows=report.rows(plan);assert len(rows)==1
    r=rows[0];assert r['ler_per_cycle']==pytest.approx((r['x_errors']/r['x_shots']+r['z_errors']/r['z_shots'])/3)
    assert r['ci95_low']<=r['ler_per_cycle']<=r['ci95_high']
    path=next((run.ROOT/'results'/plan['jobs'][0]['id']/'x').glob('chunk-*.npz'));path.write_bytes(b'tamper')
    with pytest.raises(ValueError,match='event ledger'):report.rows(plan)
