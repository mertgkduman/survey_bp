"""A separately versioned log-domain SPA policy, independently qualified."""
from dataclasses import replace
from decimal import Decimal, localcontext
import math
import numpy as np
import pytest
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode


def stable(**kwargs):
    return BpFloodingPolicy(check_rule='sum_product',resolution=ResolutionPolicy('float64'),
        hard_decision='map_pauli',version='bp-flooding-policy-v3',
        check_stabilization='log_domain',product_epsilon=1e-10,**kwargs)


def parity_llr(values):
    with localcontext() as ctx:
        ctx.prec=600
        even,odd=Decimal(1),Decimal(0)
        for x in values:
            odds=(-Decimal(str(x))).exp(); p0=1/(1+odds); p1=odds/(1+odds)
            even,odd=even*p0+odd*p1,odd*p0+even*p1
        return float((even/odd).ln())


def test_new_policy_roundtrips_without_changing_previous_versions():
    p=stable(); assert BpFloodingPolicy.from_spec(p.as_spec())==p
    assert p.as_evidence()['check_reduction']=='prefix_suffix_boxplus'
    assert p.as_evidence()['unary_check']=='finite_log((2-epsilon)/epsilon)'
    with pytest.raises(ValueError): replace(p,version='bp-flooding-policy-v2')
    with pytest.raises(ValueError): replace(p,check_rule='min_sum')

@pytest.mark.parametrize('degree',[1,2,4,16,64])
@pytest.mark.parametrize('magnitude',[1e-12,.1,1.,10.,20.,30.,38.,40.,100.,1000.])
@pytest.mark.parametrize('negative',[False,True])
def test_binary_stable_check_matches_600_digit_parity_oracle(degree,magnitude,negative):
    incoming=np.full(degree,magnitude); incoming[0]*=-1 if negative else 1
    graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,degree+1),dtype=np.uint8),policy=stable())
    actual=graph.sweep(np.concatenate(([.7],incoming)),np.array([1],dtype=np.uint8),error_rate=.2)
    assert actual.check_to_variable[0]==pytest.approx(-parity_llr(incoming),abs=2e-11,rel=0)


def test_high_confidence_binary_tree_has_exact_posterior():
    graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,3),dtype=np.uint8),policy=stable())
    result=graph.sweep(np.full(3,40.),np.array([1],dtype=np.uint8),error_rate=1/(1+math.exp(40.)))
    np.testing.assert_allclose(result.beliefs,math.log(2),atol=1e-13,rtol=0)

@pytest.mark.parametrize('old',[[-1000.,1000.,0.,40.],[1.,1.,1.,1.],[0.,0.,0.,0.],[38.,40.,100.,1000.]])
def test_every_extrinsic_edge_and_sign(old):
    graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,4),dtype=np.uint8),policy=stable())
    for bit in [0,1]:
        actual=graph.sweep(np.array(old),np.array([bit],dtype=np.uint8),error_rate=.2)
        expected=[(-1)**bit*parity_llr(old[:i]+old[i+1:]) for i in range(4)]
        np.testing.assert_allclose(actual.check_to_variable,expected,atol=2e-11,rtol=0)


def test_unary_finite_convention_and_legacy_high_confidence_are_explicit():
    graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,1),dtype=np.uint8),policy=stable())
    actual=graph.sweep(np.array([1000.]),np.array([1],dtype=np.uint8),error_rate=.2)
    assert actual.check_to_variable[0]==pytest.approx(-math.log((2-1e-10)/1e-10))
    legacy=replace(stable(),version='bp-flooding-policy-v2',check_stabilization='exact_unity')
    graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,2),dtype=np.uint8),policy=legacy)
    actual=graph.sweep(np.full(2,40.),np.array([0],dtype=np.uint8),error_rate=.2)
    assert actual.check_to_variable[0]==pytest.approx(23.718998)

from itertools import product
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import QBP4_F64_V3
from bp_registry.quaternary.problems import QuaternaryOriginalProblem

@pytest.mark.parametrize('confidence',[2.,40.,100.,500.])
@pytest.mark.parametrize('bit',[0,1])
def test_pauli_tree_marginals_match_exhaustive_four_state_inference(confidence,bit):
    labels=np.array([[1,3,2]],dtype=np.uint8); code=PauliCode(checks=labels)
    row=np.array([1.,math.exp(-confidence),math.exp(-confidence),math.exp(-confidence)])
    priors=np.tile(row/row.sum(),(3,1)); syndrome=np.array([bit],dtype=np.uint8)
    graph=CompiledBp4Graph.from_code(code,priors,policy=stable())
    result=graph.sweep(graph.initial_v2c(),syndrome)
    # Scale each admitted joint mass by exp(confidence) for odd parity to avoid
    # underflow in the low-mass normalization; sum log weights directly.
    assignments=list(product(range(4),repeat=3)); logs=[]; accepted=[]
    for assignment in assignments:
        if sum(a!=0 and a!=b for a,b in zip(assignment,labels[0]))%2==bit:
            accepted.append(assignment)
            logs.append(sum(math.log(priors[i,a]) for i,a in enumerate(assignment)))
    weights=np.exp(np.array(logs)-max(logs)); expected=np.zeros((3,4))
    for assignment,weight in zip(accepted,weights):
        for i,a in enumerate(assignment): expected[i,a]+=weight
    expected/=weights.sum()
    np.testing.assert_allclose(result.marginals,expected,rtol=1e-12,atol=1e-14)


def test_pauli_recurrence_matches_existing_scalar_log_domain_implementation():
    code=PauliCode(checks=np.array([[1,1,0],[0,1,1]],dtype=np.uint8))
    priors=np.array([[.45,.05,.2,.3],[.6,.15,.1,.15],[.55,.2,.1,.15]])
    s=np.array([1,0],dtype=np.uint8)
    graph=CompiledBp4Graph.from_code(code,priors,policy=stable(damping=.6))
    profile=replace(QBP4_F64_V3,check_rule='boxplus',v2c_damping=.6)
    session=ScalarLlrBp4Kernel(profile=profile).new_session(QuaternaryOriginalProblem('original-stable',code,s),priors)
    old=graph.initial_v2c()
    for _ in range(8):
        actual=graph.sweep(old,s); expected=session.sweep(stop_on_convergence=False)
        for field in ['c2v','v2c','beliefs','marginals']:
            np.testing.assert_allclose(getattr(actual,field),getattr(expected,field),atol=2e-12,rtol=0)
        np.testing.assert_array_equal(actual.candidate,expected.candidate)
        old=actual.v2c


def q(value, resolution):
    if resolution.format.startswith('int'):
        bits=int(resolution.format[3:]); bound=(2**(bits-1)-1)/resolution.scale
        return float(np.clip(np.rint(value*resolution.scale)/resolution.scale,-bound,bound))
    dtype=np.dtype(resolution.format)
    return float(dtype.type(np.clip(value,-np.finfo(dtype).max,np.finfo(dtype).max)))


def reference_sweep(graph,old,syndrome,family,p):
    """Independent probability-domain projection/parity and boundary rounding."""
    r=p.resolution; n=3; variables=graph.variables
    if family=='binary':
        old=np.array([q(x,r) for x in old]); comm=old
        prior=np.full(n,math.log(4.))
    else:
        if r.scope!='scalar_edges':old=np.array([[q(x,r) for x in row] for row in old])
        comm=[]
        for row,label in zip(old,graph.labels):
            weights=np.exp(-np.array([0.,*row])); commute=weights[0]+weights[label]
            anti=sum(weights[a] for a in range(1,4) if a!=label)
            comm.append(q(math.log(commute/anti),r))
        prior=graph.prior_llrs.copy()
    c2v=np.empty(len(variables))
    for i in range(len(variables)):
        incoming=[comm[j] for j in range(len(variables)) if j!=i]
        c2v[i]=q((-1)**int(syndrome[0])*parity_llr(incoming),r)
    beliefs=prior.copy()
    for i,v in enumerate(variables):
        if family=='binary':beliefs[v]+=c2v[i]
        else:
            for a in range(1,4):
                if a!=graph.labels[i]:beliefs[v,a-1]+=c2v[i]
    if r.scope=='all_state':beliefs=np.array([q(x,r) for x in beliefs.flat]).reshape(beliefs.shape)
    candidate=(beliefs<0).astype(np.uint8) if family=='binary' else np.argmin(np.column_stack((np.zeros(n),beliefs)),axis=1).astype(np.uint8)
    proposal=beliefs[variables].copy()
    for i in range(len(variables)):
        if family=='binary':proposal[i]-=c2v[i]
        else:
            for a in range(1,4):
                if a!=graph.labels[i]:proposal[i,a-1]-=c2v[i]
    quantize=family=='binary' or r.scope!='scalar_edges'
    if quantize:proposal=np.array([q(x,r) for x in proposal.flat]).reshape(proposal.shape)
    ow,fw=(q(p.damping,r),q(1-p.damping,r)) if r.coefficients=='same' else (p.damping,1-p.damping)
    new=ow*old+fw*proposal
    if quantize:new=np.array([q(x,r) for x in new.flat]).reshape(new.shape)
    return c2v,beliefs,candidate,new

@pytest.mark.parametrize('family',['binary','pauli'])
@pytest.mark.parametrize('format',['float64','float32','float16','int8','int16','int32'])
@pytest.mark.parametrize('scope',['scalar_edges','all_messages','all_state'])
def test_resolution_and_cpu_batches_match_independent_recurrence(family,format,scope,tmp_path):
    r=ResolutionPolicy(format,16 if format.startswith('int') else None,scope,'same')
    p=replace(stable(damping=.2,zero_syndrome_shortcut=False),resolution=r)
    if family=='binary':graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,3),dtype=np.uint8),policy=p)
    else:graph=CompiledBp4Graph.from_code(PauliCode(checks=np.array([[1,3,2]],dtype=np.uint8)),np.array([[.45,.05,.2,.3],[.6,.15,.1,.15],[.55,.2,.1,.15]]),policy=p)
    extra={'error_rate':.2} if family=='binary' else {}
    syndromes=np.array([[0],[1],[1],[0]],dtype=np.uint8)
    for s in syndromes[:2]:
        old=np.full(3,math.log(4.)) if family=='binary' else graph.initial_v2c()
        for _ in range(3):
            expected=reference_sweep(graph,old,s,family,p)
            actual=graph.sweep(old,s,**extra)
            fields=['check_to_variable','beliefs','candidate','new_v2c'] if family=='binary' else ['c2v','beliefs','candidate','v2c']
            for field,wanted in zip(fields,expected):
                np.testing.assert_allclose(getattr(actual,field),wanted,atol=3e-12,rtol=0)
            old=expected[-1]
    for limit in (0,1,4):
        for workers in (1,2):
            batch=graph.run_batch(syndromes,max_iterations=limit,workers=workers,**extra)
            for i,s in enumerate(syndromes):
                single=graph.run(s,max_iterations=limit,**extra)
                np.testing.assert_array_equal(batch.candidates[i],single.candidate)
                assert (batch.iterations[i],batch.converged[i])==(single.iterations,single.converged)
            batch.write_ledger(tmp_path/'events.jsonl')
            import json
            rows=[json.loads(line) for line in (tmp_path/'events.jsonl').read_text().splitlines()]
            assert all(row['numerics']['version']=='bp-flooding-policy-v3' for row in rows)
            assert all(row['work']['check_to_variable_updates']==3*row['iterations'] for row in rows)

@pytest.mark.parametrize('values',[[1e-12,1e-12],[1e-100,1e-100],[1e-12,1000.],[-1e-12,1e-12]])
def test_small_llr_relative_accuracy(values):
    from bp_registry.check_numerics import stable_boxplus
    expected=parity_llr(values)
    assert stable_boxplus(*values)==pytest.approx(expected,rel=5e-15,abs=0)
    graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,3),dtype=np.uint8),policy=stable())
    result=graph.sweep(np.array([.7,*values]),np.array([0],dtype=np.uint8),error_rate=.2)
    assert result.check_to_variable[0]==pytest.approx(expected,rel=5e-15,abs=0)
