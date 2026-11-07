"""Independent invariants from audit 008–011 and explicit historical migration."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import json
import numpy as np
import pytest
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2, BINARY_SPA_F64_V3, probability_to_llr, prior_llr
from bp_registry.canonical.updates import MinSumUpdate
from bp_registry.canonical.budgets import BudgetTree, BudgetLimit
from bp_registry.quaternary.numerics import QBP4_F64_V1, QBP4_F64_V2, QBP4_F64_V3, pauli_hard_decision
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem
from bp_registry.quaternary.schedules import QbpFloodingSchedule, QbpVariableSerialSchedule, QuaternaryCheckTransform


def fixture(profile=QBP4_F64_V3, cap=10):
    code = PauliCode(checks=np.array([[1,1,0],[0,1,1]], dtype=np.uint8), source_artifact_identity='audit-test')
    problem = QuaternaryOriginalProblem(lineage_id='original-audit', code=code, syndrome=np.array([1,0], dtype=np.uint8))
    priors = np.array([[.45,.05,.2,.3],[.6,.15,.1,.15],[.55,.2,.1,.15]])
    session = ScalarLlrBp4Kernel(profile=profile).new_session(problem, priors, budgets=BudgetTree(limits=(BudgetLimit('attempt','bp_calls',cap),), parents={}))
    return code, problem, priors, session


def test_map_all_equalities():
    for llrs in product((-2.,0.,2.), repeat=3):
        scores = np.array([0., *llrs])
        candidate = int(pauli_hard_decision(llrs))
        assert scores[candidate] == scores.min()
        assert candidate == np.argmin(scores)
    assert int(pauli_hard_decision([-2.,0.,-2.], profile=QBP4_F64_V2)) == 2


@pytest.mark.parametrize('profile',[QBP4_F64_V1,QBP4_F64_V2,QBP4_F64_V3])
@pytest.mark.parametrize('kind',['plain','transform','serial'])
def test_cap_retains_committed_work(profile,kind):
    _,_,_,session=fixture(profile,1)
    schedule = (QbpVariableSerialSchedule(session) if kind=='serial' else
                QbpFloodingSchedule(session, transforms=[QuaternaryCheckTransform.normalization(1.)]) if kind=='transform' else None)
    if schedule:
        schedule.sweep()
        # A new bounded request is exercised even if the fixture converged.
        session._terminal='running'
        result=schedule.sweep().result
    else:
        session.sweep(stop_on_convergence=False)
        result=session.sweep()
    assert result.terminal=='capped'
    assert result.work.bp_calls==1
    assert result.work==session.budgets.summary('attempt')
    assert result.iteration==1


def test_failed_sweep_retains_work_and_buffers(monkeypatch):
    _,_,_,session=fixture()
    before=session.sweep(stop_on_convergence=False)
    def fail(*args,**kwargs): raise ArithmeticError('injected')
    monkeypatch.setattr(session.kernel,'check_message',fail)
    with pytest.raises(ArithmeticError): session.sweep()
    assert session.last.work==before.work
    np.testing.assert_array_equal(session.last.v2c,before.v2c)


def test_identity_transform_preserves_damping():
    _,_,_,a=fixture(); _,_,_,b=fixture()
    plain=a.sweep()
    transformed=QbpFloodingSchedule(b,transforms=[QuaternaryCheckTransform.normalization(1.)]).sweep().result
    np.testing.assert_allclose(plain.v2c,transformed.v2c,rtol=0,atol=2e-14)


def test_stable_subnormal_prior_and_update_admission():
    p=np.nextafter(0.,1.)
    assert prior_llr(p)==pytest.approx(-np.log(p))
    assert float(probability_to_llr(p))==pytest.approx(-np.log(p))
    kernel=BinarySpaKernel(update_rule=MinSumUpdate())
    assert kernel.profile==kernel.update_rule.profile
    with pytest.raises(ValueError,match='profiles must agree'):
        BinarySpaKernel(profile=BINARY_SPA_F64_V3,update_rule=MinSumUpdate())


@pytest.mark.parametrize('edges',[True,False])
@pytest.mark.parametrize('p',[.2,.8])
def test_binary_initial_candidate(edges,p):
    h=np.array([[1,1,0] if edges else [0,0,0]],dtype=np.uint8)
    for syndrome in [np.array([0],dtype=np.uint8),np.array([1],dtype=np.uint8)]:
        expected=BinarySpaKernel().run(h,syndrome,error_rate=p,max_iterations=0)
        graph=CompiledBinaryFlooding.from_check_matrix(h)
        for actual in (graph.run(syndrome,error_rate=p,max_iterations=0),graph.bind_error_rate(p).run(syndrome,max_iterations=0)):
            np.testing.assert_array_equal(actual.candidate,expected.candidate)
            assert actual.converged==expected.converged


def test_bp4_initial_and_sweep_parity():
    code,problem,priors,session=fixture()
    graph=CompiledBp4Graph.from_code(code,priors)
    initial=graph.run(problem.syndrome,max_iterations=0)
    np.testing.assert_array_equal(initial.candidate,session.last.candidate)
    assert initial.converged==session.last.converged
    old=graph.initial_v2c()
    for _ in range(3):
        scalar=session.sweep(stop_on_convergence=False)
        compiled=graph.sweep(old,problem.syndrome)
        for attr in ('c2v','v2c','beliefs','marginals','candidate'):
            np.testing.assert_allclose(getattr(compiled,attr),getattr(scalar,attr),rtol=0,atol=2e-12)
        old=compiled.v2c


def test_public_new_accounting_and_historical_replay(tmp_path):
    from bp_registry.runner import run_quaternary, verify_quaternary_run
    for schema in ('quaternary_experiment_v2','quaternary_experiment_v3'):
        root=Path('.planning/spikes/011-execution-consistency')/(schema+'-budget-counterexample')
        assert verify_quaternary_run(root)['verified']
        out=tmp_path/schema
        result=run_quaternary(root/'input.json',out)
        assert result['work_accounting_version']=='cumulative-v2'
        assert result['work']['bp_calls']==1
        assert verify_quaternary_run(out)['verified']


def test_serial_damping_against_probability_domain_oracle():
    # Enumerate local four-state factors; never call production LLR updates.
    code,problem,priors,session=fixture(replace(QBP4_F64_V3,v2c_damping=.6))
    old=session.last.v2c.copy()
    checks,variables=np.nonzero(code.checks)
    labels=code.checks[checks,variables]
    states=np.arange(4)
    anti=lambda label: (states != 0) & (states != label)
    c2v=np.zeros(len(labels)); beliefs=np.zeros((code.n,3))
    for variable in range(code.n):
        incident=np.flatnonzero(variables==variable)
        for edge in incident:
            bias=1.
            for other in np.flatnonzero(checks==checks[edge]):
                if edge==other: continue
                mass=np.exp(np.r_[0.,-old[other]]); mass/=mass.sum()
                bias *= mass[~anti(labels[other])].sum()-mass[anti(labels[other])].sum()
            bias *= (-1.)**int(problem.syndrome[checks[edge]])
            c2v[edge]=np.log((1+bias)/(1-bias))
        mass=priors[variable].copy()
        for edge in incident:
            mass[anti(labels[edge])] *= np.exp(-c2v[edge])
        beliefs[variable]=np.log(mass[0]/mass[1:])
        for edge in incident:
            proposal=beliefs[variable].copy()
            proposal[anti(labels[edge])[1:]]-=c2v[edge]
            old[edge]=.6*old[edge]+.4*proposal
    actual=QbpVariableSerialSchedule(session).sweep().result
    np.testing.assert_allclose(actual.v2c,old,atol=2e-12,rtol=0)
    np.testing.assert_allclose(actual.beliefs,beliefs,atol=2e-12,rtol=0)
    _,_,_,undamped=fixture(replace(QBP4_F64_V3,v2c_damping=0.))
    assert not np.allclose(actual.v2c,QbpVariableSerialSchedule(undamped).sweep().result.v2c)


def test_policy_stabilization_neutral_equivalence():
    from bp_registry.resolution import BpFloodingPolicy,ResolutionPolicy
    policy=BpFloodingPolicy(check_rule='sum_product',resolution=ResolutionPolicy(),damping=.1,
        hard_decision='map_pauli',zero_syndrome_shortcut=False,version='bp-flooding-policy-v2',
        check_stabilization='exact_unity',product_epsilon=1e-10)
    assert BpFloodingPolicy.from_spec(policy.as_spec())==policy
    h=np.array([[1,1]],dtype=np.uint8); syndrome=np.array([1],dtype=np.uint8)
    plain=CompiledBinaryFlooding.from_check_matrix(h)
    adapted=CompiledBinaryFlooding.from_check_matrix(h,policy=policy)
    for value in (0.,30.,38.,40.,100.):
        old=np.full(2,value)
        a=plain.sweep(old,syndrome,error_rate=.2); b=adapted.sweep(old,syndrome,error_rate=.2)
        for field in ('check_to_variable','beliefs','new_v2c','candidate'):
            np.testing.assert_allclose(getattr(a,field),getattr(b,field),atol=1e-13,rtol=0)
    code,problem,priors,_=fixture()
    a=CompiledBp4Graph.from_code(code,priors);b=CompiledBp4Graph.from_code(code,priors,policy=policy)
    old=a.initial_v2c()
    for _ in range(4):
        x=a.sweep(old,problem.syndrome); y=b.sweep(old,problem.syndrome)
        for field in ('c2v','beliefs','v2c','candidate'):
            np.testing.assert_allclose(getattr(x,field),getattr(y,field),atol=2e-12,rtol=0)
        old=x.v2c


@pytest.mark.parametrize('family',['binary','pauli'])
@pytest.mark.parametrize('policy_kind',[None,'sum_product','min_sum','normalized_offset'])
def test_cpu_batch_matches_single_shot(family,policy_kind,tmp_path):
    from numba import get_num_threads
    from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy
    policy=None if policy_kind is None else BpFloodingPolicy(
        check_rule='sum_product' if policy_kind=='sum_product' else 'min_sum',
        resolution=ResolutionPolicy('float64') if policy_kind=='sum_product' else ResolutionPolicy('int8',16,'all_messages'),
        damping=.1,alpha=.8 if policy_kind=='normalized_offset' else 1.,beta=.2 if policy_kind=='normalized_offset' else 0.,
        hard_decision='map_pauli',zero_syndrome_shortcut=True,version='bp-flooding-policy-v2',
        check_stabilization='exact_unity',product_epsilon=1e-10)
    code,problem,priors,_=fixture()
    syndromes=np.array(list(product((0,1),repeat=2))*8,dtype=np.uint8)
    if family=='binary':
        graph=CompiledBinaryFlooding.from_check_matrix((code.checks!=0).astype(np.uint8),
            rule='min_sum' if policy and policy.check_rule=='min_sum' else 'spa',policy=policy)
        kwargs={'error_rate':.8}
    else:
        graph=CompiledBp4Graph.from_code(code,priors,policy=policy);kwargs={}
    previous=get_num_threads()
    for limit in (0,3):
        expected=[graph.run(s,max_iterations=limit,**kwargs) for s in syndromes]
        for workers in (1,2):
            batch=graph.run_batch(syndromes,max_iterations=limit,workers=workers,**kwargs)
            np.testing.assert_array_equal(batch.candidates,[x.candidate for x in expected])
            np.testing.assert_array_equal(batch.iterations,[x.iterations for x in expected])
            np.testing.assert_array_equal(batch.converged,[x.converged for x in expected])
            assert get_num_threads()==previous
            assert not batch.candidates.flags.writeable
        ledger=tmp_path/'events.jsonl';batch.write_ledger(ledger)
        rows=[json.loads(line) for line in ledger.read_text().splitlines()]
        assert len(rows)==len(syndromes)
        assert [r['work']['bp_calls'] for r in rows]==batch.iterations.tolist()
    with pytest.raises(ValueError): graph.run_batch(syndromes,max_iterations=3,workers=0,**kwargs)
    with pytest.raises(ValueError): graph.run_batch(syndromes.astype(float),max_iterations=3,**kwargs)
    empty=graph.run_batch(np.empty((0,2),dtype=np.uint8),max_iterations=3,**kwargs)
    assert empty.candidates.shape==(0,code.n)


def test_compiled_map_all_equalities_with_disconnected_variable():
    code=PauliCode(checks=np.array([[1,1,0]],dtype=np.uint8),source_artifact_identity='map-ties')
    for llrs in product((-2.,0.,2.),repeat=3):
        masses=np.exp(-np.array([0.,*llrs]));masses/=masses.sum()
        priors=np.array([[.7,.1,.1,.1],[.7,.1,.1,.1],masses])
        graph=CompiledBp4Graph.from_code(code,priors)
        expected=int(pauli_hard_decision(graph.prior_llrs[2]))
        for limit in (0,1):
            result=graph.run(np.array([0],dtype=np.uint8),max_iterations=limit)
            assert result.candidate[2]==expected
            # Ranking uses the actually represented prior (logs may round ties).
            assert np.r_[0.,graph.prior_llrs[2]][result.candidate[2]]==np.r_[0.,graph.prior_llrs[2]].min()


def test_new_public_profile_roundtrips(tmp_path):
    from bp_registry.manifests import parse_manifest
    from bp_registry.runner import run_quaternary,verify_quaternary_run,preflight_canonical
    from bp_registry.cli import run_canonical,verify_run
    source=Path('.planning/spikes/011-execution-consistency/quaternary_experiment_v3-budget-counterexample/input.json')
    q=json.loads(source.read_text());q['schema_version']='quaternary_experiment_v4';q.pop('numerical_profile',None)
    assert parse_manifest(q).numerical_profile==QBP4_F64_V3.profile_id
    path=tmp_path/'q.json';path.write_text(json.dumps(q))
    out=tmp_path/'q';result=run_quaternary(path,out)
    assert result['work']['bp_calls']==1
    assert verify_quaternary_run(out)['verified']
    b=json.loads(Path('data/manifests/canonical-three-qubit-development.json').read_text())
    b['schema_version']=10;b.pop('numerical_profile')
    path=tmp_path/'b.json';path.write_text(json.dumps(b))
    assert preflight_canonical(path)['resolved_numerical_profile']['profile_id']==BINARY_SPA_F64_V3.profile_id
    out=tmp_path/'b';run_canonical(path,out)
    assert verify_run(out)['final_row_count']==2


def test_min_sum_linear_scan_matches_independent_exclusion():
    from bp_registry.check_numerics import minsum_summary
    # Repeated minima, zero signs, degree one and fixed point saturation bounds.
    for values in ([0.],[-2.,-2.,3.],[0.,-0.,1.],[-5.,4.,3.,2.],[-1.,1.,1.,-1.]):
        a=np.array(values);first,second,index,negatives=minsum_summary(a,0,len(a))
        for edge in range(len(a)):
            excluded=np.delete(a,edge)
            expected=np.min(np.abs(excluded)) if excluded.size else np.inf
            assert (second if edge==index else first)==expected
            assert (negatives-int(a[edge]<0))%2==np.count_nonzero(excluded<0)%2


@pytest.mark.parametrize('family',['binary','pauli'])
@pytest.mark.parametrize('format',['float16','float32','float64','int8','int16','int32'])
@pytest.mark.parametrize('scope',['scalar_edges','all_messages','all_state'])
def test_batch_resolution_matrix(family,format,scope):
    from bp_registry.resolution import BpFloodingPolicy,ResolutionPolicy
    policy=BpFloodingPolicy(check_rule='min_sum',resolution=ResolutionPolicy(format,16 if format.startswith('int') else None,scope,'same'),
        damping=.2,alpha=.8,beta=.1,hard_decision='map_pauli',zero_syndrome_shortcut=False,
        version='bp-flooding-policy-v2',check_stabilization='epsilon_band',product_epsilon=1e-9)
    code,_,priors,_=fixture()
    syndromes=np.array([[0,0],[1,0],[1,1]],dtype=np.uint8)
    if family=='binary':
        graph=CompiledBinaryFlooding.from_check_matrix((code.checks!=0).astype(np.uint8),rule='min_sum',policy=policy)
        kwargs={'error_rate':.2}
    else:
        graph=CompiledBp4Graph.from_code(code,priors,policy=policy);kwargs={'stop_on_convergence':False}
    batch=graph.run_batch(syndromes,max_iterations=5,workers=2,**kwargs)
    reference=[graph.run(s,max_iterations=5,**kwargs) for s in syndromes]
    np.testing.assert_array_equal(batch.candidates,[r.candidate for r in reference])
    np.testing.assert_array_equal(batch.iterations,[r.iterations for r in reference])
    np.testing.assert_array_equal(batch.converged,[r.converged for r in reference])


@pytest.mark.parametrize('schedule',['qbp_flooding','qbp_variable_serial'])
def test_v4_public_transformed_schedules(schedule,tmp_path):
    from bp_registry.runner import run_quaternary,verify_quaternary_run
    source=Path('.planning/spikes/011-execution-consistency/quaternary_experiment_v3-budget-counterexample/input.json')
    spec=json.loads(source.read_text());spec['schema_version']='quaternary_experiment_v4';spec.pop('numerical_profile',None)
    spec['composition']['schedule']={'kind':schedule,'binding_id':'schedule'}
    spec['composition']['transforms']=[{'kind':'qbp_c2v_normalization','binding_id':'normalization','config':{'alpha_c':1.2}}]
    manifest=tmp_path/'input.json';manifest.write_text(json.dumps(spec))
    out=tmp_path/'out';result=run_quaternary(manifest,out)
    assert result['numerical_profile']==QBP4_F64_V3.profile_id
    assert result['work']['bp_calls']==result['committed_sweeps']
    assert verify_quaternary_run(out)['verified']


def test_capped_v3_keeps_candidate_validity_separate_from_termination():
    code=PauliCode(checks=np.array([[1,1]],dtype=np.uint8),source_artifact_identity='cap-validity')
    problem=QuaternaryOriginalProblem('original-cap-validity',code,np.array([0],dtype=np.uint8))
    session=ScalarLlrBp4Kernel().new_session(problem,np.tile([.7,.1,.1,.1],(2,1)),
        budgets=BudgetTree(limits=(BudgetLimit('attempt','bp_calls',1),),parents={}))
    first=session.sweep(stop_on_convergence=False)
    assert first.converged
    capped=session.sweep()
    assert capped.terminal=='capped' and capped.converged
    assert capped.work==first.work


def test_cumulative_receipt_tamper_is_rejected_and_replay_scratch_cleaned(tmp_path):
    from bp_registry.runner import run_quaternary, verify_quaternary_run
    source=Path('.planning/spikes/011-execution-consistency/quaternary_experiment_v3-budget-counterexample/input.json')
    out=tmp_path/'out';result=run_quaternary(source,out)
    result['work']['bp_calls']=0
    (out/'result.json').write_text(json.dumps(result))
    with pytest.raises(ValueError,match='cumulative result work'):
        verify_quaternary_run(out)
    assert not list(out.glob('qbp-replay-*'))


def test_frozen_v1_has_no_extra_damping_arithmetic():
    proposal=np.array([-0.,0.,-0.])
    result=ScalarLlrBp4Kernel(profile=QBP4_F64_V1).damp_variable_messages(np.ones(3),proposal)
    np.testing.assert_array_equal(np.signbit(result),np.signbit(proposal))
