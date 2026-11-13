"""Independent channel controls, Pauli outcomes, real execution, and launch gates."""
from copy import deepcopy
from hashlib import sha256
import gzip
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest

REPO=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('_test_isolated_study',REPO/'data/reproductions/mackay-0304161-isolated-qbp/run.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
rt=study.rt

def job(arm='binary_separate'):
    return deepcopy(next(j for j in study.design()['jobs'] if j['code']=='unicycle74' and j['arm']==arm and j['physical_p']==.06))

def test_controls_are_undamped_matched_channel_and_independent_of_training():
    d=study.design();assert len(d['jobs'])==20 and len({j['id'] for j in d['jobs']})==20
    for j in d['jobs']:
        assert j['seed']==2026111323 and j['seed']!=2026111321
        assert j['decoder']['v2c_damping']==0 and j['decoder']['max_iterations']==100
        assert j['decoder']['noise_model']=='depolarizing' and j['target_block_failures']==20 and j['max_shots']==100_000_000
        assert j['graph_edges']==2*j['component_graph_edges']
        assert j['decoder']['prior']==('2p/3' if j['arm']=='binary_separate' else 'p')
    import bp_study_runtime as original
    assert original.event is not rt.event and original.Ledger is not rt.Ledger


def test_real_joint_and_separate_controls_see_identical_full_pauli_samples():
    a,b=rt.state(job()),rt.state(job('qbp_undamped'))
    saw_y=saw_z=False
    for shot in range(24):
        x,y=rt.event(a,shot),rt.event(b,shot)
        assert x['error_sha256']==y['error_sha256'] and x['syndrome_sha256']==y['syndrome_sha256']
        assert max(x['component_iterations'])==x['iterations']<=100
        assert x['directed_edge_updates']==2*a[0]['component_graph_edges']*sum(x['component_iterations'])
        truth=rt.parent.base._sample(a[0]['seed'],6000,shot,74,depolarizing=True)
        saw_y|=bool(np.any(truth==2));saw_z|=bool(np.any(truth==3))
    assert saw_y and saw_z


def test_separate_control_counts_z_logical_failure(monkeypatch):
    value=list(rt.state(job()));code=rt.load_artifact(rt.REPO,value[0]['code_artifact']).code
    x=np.zeros(code.n,dtype=np.uint8);z=np.asarray(code.lz[0],dtype=np.uint8)
    value[3]=[SimpleNamespace(run=lambda *a,**k:SimpleNamespace(candidate=x,converged=True,iterations=1)),
              SimpleNamespace(run=lambda *a,**k:SimpleNamespace(candidate=z,converged=True,iterations=1))]
    monkeypatch.setattr(rt.parent.base,'_sample',lambda *a,**k:np.zeros(code.n,dtype=np.uint8))
    row=rt.event(tuple(value),0)
    assert row['outcome']=='type_ii' and row['component_converged']==[True,True]


def test_component_work_is_actual_and_invalid_round_sum_is_rejected(tmp_path):
    j=job();value=rt.state(j);row=rt.event(value,0)
    ledger=rt.Ledger(tmp_path,j)
    bad=deepcopy(row);bad['directed_edge_updates']+=1
    with pytest.raises(ValueError,match='directed edge'):ledger.add(bad,b'bad')
    bad=deepcopy(row);bad['component_iterations']=[1,1];bad['iterations']=2;bad['branch_iterations']=[2]
    with pytest.raises(ValueError,match='component work'):ledger.add(bad,b'bad')
    assert ledger.shots==0


@pytest.mark.parametrize('arm',['binary_separate','qbp_undamped'])
def test_real_serial_parallel_resume_and_endpoint_collection(tmp_path,monkeypatch,arm):
    outputs=[];template=job(arm)
    for workers in (1,2):
        j=deepcopy(template);j.update(workers=workers,max_shots=16,target_block_failures=100)
        root=tmp_path/str(workers);root.mkdir();(root/'plan.json').write_text(json.dumps({'jobs':[j]}))
        monkeypatch.setattr(rt,'load',lambda _,j=j:{'jobs':[j]})
        first=rt.execute(root,0);second=rt.execute(root,0);assert first==second
        verified=rt.collect(root,require_complete=True);assert verified['points'][0]['shots']==16
        rows=[]
        for p in sorted((root/'results'/j['id']).glob('shots-*.jsonl.gz')):
            with gzip.open(p,'rt') as f:rows.extend(json.loads(line) for line in f)
        outputs.append([{k:v for k,v in row.items() if k!='decode_ns'} for row in rows])
    assert outputs[0]==outputs[1]


def test_advance_cannot_publish_or_dispatch_before_both_complete_audits(monkeypatch):
    import bp_study_runtime as original
    calls=[]
    monkeypatch.setattr(rt,'collect',lambda root,**k:calls.append(('new',k['require_complete'])))
    def missing(root,**kwargs):
        calls.append(('old',kwargs['require_complete']));raise ValueError('only39/40')
    monkeypatch.setattr(original,'collect',missing)
    monkeypatch.setattr(study,'publish_controls',lambda:calls.append('published'))
    monkeypatch.setattr(study.subprocess,'run',lambda *a,**k:calls.append('submitted'))
    with pytest.raises(ValueError,match='39/40'):study.advance()
    assert calls==[('new',True),('old',True)]


def test_scheduler_gate_depends_on_old_array_and_new_audit(tmp_path,monkeypatch):
    d=study.design();calls=[]
    monkeypatch.setattr(study,'ROOT',tmp_path)
    monkeypatch.setattr(rt,'load',lambda _:d)
    def submit(argv,**kwargs):
        calls.append(argv);return SimpleNamespace(stdout=str(8000+len(calls))+'\n',stderr='')
    monkeypatch.setattr(study.subprocess,'run',submit)
    study.submit();study.submit()
    assert len(calls)==3
    assert '--array=0-19%8' in calls[0]
    assert '--dependency=afterok:8001' in calls[1]
    assert '--dependency=afterok:8002:61773602' in calls[2]


def test_paper_requested_ordinates_are_unavailable_not_inferred_from_summary():
    e=json.loads((study.ROOT/'paper-evidence.json').read_text())
    assert [x['version'] for x in e['source_inventory']]==[1,2,3]
    assert [x['p_x'] for x in e['requested_ordinates']]==[.010,.013,.020,.030,.040]
    assert all(x['paper_block_error'] is None and x['status']=='not_reported_in_inspected_sources' for x in e['requested_ordinates'])
    p=e['available_summary_point'];assert p['code_n']==74 and .00681<p['p_x_approx']<.00683
    assert p['source_target_classical_constituent_block_error']==5e-5
    assert 'Figure16' in e['pdf_references']['length274_curve']
