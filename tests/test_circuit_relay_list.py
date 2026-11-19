"""Independent candidate-selection oracle for versioned multi-solution Relay-BP."""
from dataclasses import replace
import math
import numpy as np
import pytest
import stim
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.paper_decoders import segment
from bp_registry.canonical.prior_tilt import indexed_uniform
from bp_registry.circuit.relay_list import CircuitRelayListDecoder,RelayListSpec,validate_relay_list_trace


def oracle(model,spec,seed,shot,syndrome):
    n=model.table.variable_count;post=model.prior_llrs.copy();legs=[]
    for leg in range(spec.additional+1):
        gamma=np.full(n,spec.first_gamma) if not leg else np.array([spec.gamma_low+(spec.gamma_high-spec.gamma_low)*indexed_uniform(seed,shot,leg,v) for v in range(n)])
        r=segment(model.row_ptr,model.variables,model.prior_llrs,syndrome,np.full(n,-1,np.int8),model.prior_llrs[model.variables],post,gamma,spec.initial if not leg else spec.per_leg,True)
        post=r[1];legs.append(r)
        if sum(bool(v[4]) for v in legs)>=spec.results:break
    valid=[i for i,v in enumerate(legs) if v[4]]
    # Independent Python summation and stable list minimum; no controller scorer.
    winner=min(valid,key=lambda i:sum(float(w) for b,w in zip(legs[i][0],model.prior_llrs) if b)) if valid else 0
    return legs,winner


def toy():
    return DemBinaryModel.from_dem(stim.DetectorErrorModel('error(.1) D0\nerror(.15) D1\nerror(.2) D2\nerror(.04) D0 D1\nerror(.12) D1 D2\nerror(.08) D0 D2\nerror(.03) D0 D1 D2 L0'))


@pytest.mark.parametrize('seed',range(4))
@pytest.mark.parametrize('shot',range(8))
def test_matches_independent_weighted_candidate_and_all_work_oracle(seed,shot):
    model=toy();spec=RelayListSpec(initial=3,per_leg=2,additional=12,results=5)
    syndrome=np.array([(shot>>i)&1 for i in range(3)],np.uint8)
    result=CircuitRelayListDecoder(model,spec,seed).decode(syndrome,shot=shot)
    legs,winner=oracle(model,spec,seed,shot,syndrome)
    np.testing.assert_array_equal(result.candidate,legs[winner][0]);np.testing.assert_array_equal(result.posterior,legs[winner][1])
    assert result.converged==any(r[4] for r in legs)
    assert result.iterations==sum(r[5] for r in legs)
    stat=[result.iterations,result.directed_edge_updates,int(result.converged),result.random_draws,result.biased_node_updates,result.lineage]
    validate_relay_list_trace(result.trace,np.asarray(stat,np.uint64),model,spec,result.candidate)
    scores=np.array([sum(float(w) for b,w in zip(r[0],model.prior_llrs) if b) if r[4] else math.inf for r in legs])
    np.testing.assert_allclose(result.trace[:,2].view(np.float64),scores,rtol=2e-15,atol=2e-14)


def test_duplicate_convergences_count_and_exact_ties_keep_first():
    model=toy();spec=RelayListSpec(additional=8,results=5)
    result=CircuitRelayListDecoder(model,spec).decode(np.zeros(3,np.uint8),shot=0)
    assert len(result.trace)==5 and result.iterations==5
    np.testing.assert_array_equal(result.trace[:,1],[1,0,0,0,0])
    np.testing.assert_array_equal(result.candidate,np.zeros(model.table.variable_count,np.uint8))
    # Independent unequal-weight fixture: minimize weighted score, not Hamming weight.
    import bp_registry.circuit.relay_list as module
    values=[np.array([1,0,0],np.uint8),np.array([0,1,1],np.uint8),np.array([0,1,1],np.uint8)]
    original=module.segment
    def fake(*args):
        i=fake.i;fake.i+=1;c=values[i]
        return c,np.full(3,i,dtype=float),np.zeros(3),np.zeros(3),True,1,3,0
    fake.i=0
    try:
        module.segment=fake
        with np.errstate(over='ignore'):
            out=module.relay_list.py_func(np.array([0,3]),np.arange(3),np.array([9.,1.,2.]),np.zeros(1,np.uint8),1,1,2,3,.1,-.2,.6,1,0)
    finally:module.segment=original
    np.testing.assert_array_equal(out[0],values[1]);np.testing.assert_array_equal(out[1],np.ones(3))
    np.testing.assert_array_equal(out[5][:,1],[1,1,0])


def test_exhaustion_returns_first_failed_candidate_and_rejects_trace_tampering():
    model=DemBinaryModel.from_dem(stim.DetectorErrorModel('error(.1) D0\nerror(.12) D0 L0\nerror(.2) D0 L1\ndetector D1'))
    spec=RelayListSpec(initial=2,per_leg=1,additional=2,results=5)
    r=CircuitRelayListDecoder(model,spec).decode(np.array([0,1],np.uint8),shot=0)
    assert not r.converged and len(r.trace)==3 and r.iterations==4
    stat=np.array([r.iterations,r.directed_edge_updates,0,r.random_draws,r.biased_node_updates,r.lineage],np.uint64)
    validate_relay_list_trace(r.trace,stat,model,spec)
    bad=r.trace.copy();bad[1,1]=1
    with pytest.raises(ValueError):validate_relay_list_trace(bad,stat,model,spec)


@pytest.mark.parametrize('kwargs',[{'results':True},{'additional':-1},{'gamma_low':1.,'gamma_high':0.}])
def test_invalid_spec(kwargs):
    with pytest.raises(ValueError):RelayListSpec(**kwargs)


def test_returned_winner_must_match_recorded_candidate_hash_and_weight():
    model=toy();spec=RelayListSpec(additional=8,results=5)
    r=CircuitRelayListDecoder(model,spec).decode(np.zeros(3,np.uint8),shot=0)
    stat=np.array([r.iterations,r.directed_edge_updates,1,r.random_draws,r.biased_node_updates,r.lineage],np.uint64)
    wrong=r.candidate.copy();wrong[0]^=1
    with pytest.raises(ValueError,match='winner'):validate_relay_list_trace(r.trace,stat,model,spec,wrong)
