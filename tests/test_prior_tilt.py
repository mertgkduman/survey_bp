"""Independent recurrence and source-contract checks for canonical prior tilts."""
from dataclasses import replace
import itertools
import math
import numpy as np
import pytest
from bp_registry.canonical.prior_tilt import PriorTiltDecoder,PriorTiltSpec,sweep,indexed_uniform
from bp_registry.canonical.schedules import EdgeTable


def uniform(seed,shot,stage,node):
    mask=(1<<64)-1
    x=seed ^ ((shot+1)*0x9e3779b97f4a7c15&mask) ^ ((stage+1)*0xd1b54a32d192ed03&mask) ^ ((node+1)*0x94d049bb133111eb&mask)
    x=((x^(x>>30))*0xbf58476d1ce4e5b9)&mask
    x=((x^(x>>27))*0x94d049bb133111eb)&mask;x^=x>>31
    return (x>>11)/2**53


def oracle_step(h,prior,old,syn):
    edges=list(zip(*np.nonzero(h)));checks=[[i for i,(c,v) in enumerate(edges) if c==r] for r in range(len(h))]
    c2v=np.zeros(len(edges));post=prior.copy()
    for r,es in enumerate(checks):
        for e in es:
            others=[old[k] for k in es if k!=e]
            magnitude=min(map(abs,others)) if others else 23.7189981105
            sign=(-1)**(int(syn[r])+sum(x<=0 for x in others))
            c2v[e]=sign*magnitude
    for e,(r,v) in enumerate(edges):post[v]+=c2v[e]
    new=np.array([prior[v]+sum(c2v[k] for k,(r2,v2) in enumerate(edges) if v2==v and k!=e) for e,(r,v) in enumerate(edges)])
    return (post<=0).astype(np.uint8),post,new,c2v


def oracle(h,prior,syn,spec,seed,shot):
    edges=list(zip(*np.nonzero(h)));old=np.array([prior[v] for r,v in edges]);steps=0;trace=[];draws=0;bias=0
    post=prior.copy();sums=np.zeros(len(prior));lo=np.zeros(len(prior));hi=np.zeros(len(prior))
    def stats(post,old):
        for v in range(len(prior)):
            sums[v]+=post[v]
            values=[post[v],*(old[e] for e,(r,v2) in enumerate(edges) if v2==v)]
            lo[v]=min(lo[v],*values);hi[v]=max(hi[v],*values)
    def valid(c):return np.array_equal(h@c%2,syn)
    for t in range(spec.initial):
        c,post,old,_=oracle_step(h,prior,old,syn);steps+=1
        if t>=spec.initial-spec.round_len:stats(post,old)
        if valid(c):return c,post,steps,trace,draws,bias
    for r in range(1,spec.rounds+1):
        phase=sum(r>end for end in spec.ends);pi,c1,c2,theta=spec.phases[phase]
        offsets=np.zeros(len(prior));eligible=positive=0
        for v in range(len(prior)):
            if sums[v]<theta*prior[v]:
                eligible+=1;draws+=1
                choose=uniform(seed,shot,r,v)<pi;positive+=int(choose)
                offsets[v]=-c1*lo[v] if choose else -c2*hi[v]
        sums[:]=0;lo[:]=0;hi[:]=0;count=0
        for k in range(spec.round_len):
            c,post,old,_=oracle_step(h,prior+offsets,old,syn);steps+=1;count+=1
            stats(post,old);bias+=np.count_nonzero(offsets)
            if valid(c):break
        trace.append([r,phase,count,eligible,positive,np.count_nonzero(offsets),steps,int(valid(c))])
        if valid(c):break
    return c,post,steps,trace,draws,bias


def table(h):return EdgeTable.from_edges(*h.shape,zip(*np.nonzero(h)))


@pytest.mark.parametrize('syn',list(itertools.product((0,1),repeat=3)))
def test_full_tilt_matches_independent_scalar_recurrence(syn):
    h=np.array([[1,1,0,1],[0,1,1,1],[1,0,1,1]],np.uint8)
    prior=np.array([1.,2.,3.,1.]);syn=np.array(syn,np.uint8)
    p=PriorTiltSpec(initial=8,round_len=2,rounds=6,ends=(2,4),phases=((.5,.5,.25,3.),(.25,.25,.5,2.),(.75,.5,.5,4.)))
    actual=PriorTiltDecoder(table(h),prior,p,seed=121).decode(syn,shot=8)
    expected=oracle(h,prior,syn,p,121,8)
    np.testing.assert_array_equal(actual.candidate,expected[0]);np.testing.assert_allclose(actual.posterior,expected[1],atol=1e-12)
    assert actual.iterations==expected[2]
    assert actual.trace.tolist()==expected[3]
    assert (actual.random_draws,actual.biased_node_updates)==expected[4:]
    assert actual.directed_edge_updates==2*np.count_nonzero(h)*actual.iterations


def test_last_initial_window_offsets_replace_instead_of_accumulating():
    # An isolated variable and impossible empty parity check never converge.
    # Its first statistics must cover only two of six initial sweeps.
    h=np.zeros((1,1),np.uint8);syn=np.ones(1,np.uint8)
    spec=PriorTiltSpec(initial=6,round_len=2,rounds=3,phases=((0.,.5,.5,3.),))
    result=PriorTiltDecoder(table(h),np.array([2.]),spec).decode(syn,shot=0)
    assert result.trace[:,3].tolist()==[1,1,1]
    assert result.posterior[0]==1.25 and result.biased_node_updates==6
    assert result.iterations==12 and not result.converged


def test_exact_full_paper_budget_and_zero_syndrome_early_stop():
    h=np.zeros((1,1),np.uint8);dec=PriorTiltDecoder(table(h),np.array([2.]),PriorTiltSpec())
    a=dec.decode(np.array([1],np.uint8),shot=1)
    assert a.iterations==18060 and len(a.trace)==3000
    b=dec.decode(np.array([0],np.uint8),shot=2)
    assert b.iterations==1 and b.converged and b.random_draws==0 and not len(b.trace)


def test_phase_boundaries_and_transport_order_preserve_random_identity():
    h=np.zeros((1,2),np.uint8);spec=PriorTiltSpec(initial=4,round_len=2,rounds=5,ends=(1,3),phases=((.5,.5,.5,3.),)*3)
    dec=PriorTiltDecoder(table(h),np.array([2.,3.]),spec,seed=18);syn=np.ones(1,np.uint8)
    a={i:dec.decode(syn,shot=i) for i in range(6)}
    assert a[0].trace[:,1].tolist()==[0,1,1,2,2]
    assert len({v.lineage for v in a.values()})>1
    for i in reversed(range(6)):
        b=dec.decode(syn,shot=i);assert a[i].lineage==b.lineage
        np.testing.assert_array_equal(a[i].trace,b.trace)
    for i in range(20):assert indexed_uniform(18,i,4,7)==uniform(18,i,4,7)


def test_no_prior_modification_is_continuous_bp_without_message_reset():
    h=np.array([[1,1,0],[1,1,0]],np.uint8);syn=np.array([0,1],np.uint8);prior=np.array([1.,2.,4.])
    spec=PriorTiltSpec(initial=6,round_len=2,rounds=4,phases=((.5,0.,0.,3.),))
    a=PriorTiltDecoder(table(h),prior,spec).decode(syn,shot=0)
    c,p,steps,_,_,_=oracle(h,prior,syn,PriorTiltSpec(initial=14,round_len=2,rounds=0),0,0)
    np.testing.assert_allclose(a.posterior,p);np.testing.assert_array_equal(a.candidate,c)
    assert a.iterations==steps and a.biased_node_updates==0


@pytest.mark.parametrize('changes',[{'initial':0},{'round_len':0},{'rounds':-1},{'ends':(3,2),'phases':((.2,.5,.5,2.),)*3},
 {'phases':((1.1,.5,.5,2.),)},{'phases':((.2,-1.,.5,2.),)},{'phases':((.2,.5,float('nan'),2.),)}])
def test_invalid_policies_rejected(changes):
    with pytest.raises(ValueError):PriorTiltSpec(**changes)


def test_graph_prior_and_shot_admission_owns_arrays():
    h=np.array([[1,1]],np.uint8);prior=np.array([1.,2.]);dec=PriorTiltDecoder(table(h),prior,PriorTiltSpec())
    prior[:]=8;assert dec.prior.tolist()==[1.,2.]
    with pytest.raises(ValueError):dec.prior.setflags(write=True)
    with pytest.raises(ValueError):dec.decode(np.array([2]),shot=0)
    with pytest.raises(ValueError):dec.decode(np.array([1]),shot=True)
    with pytest.raises(ValueError):PriorTiltDecoder(table(h),[float('inf'),1],PriorTiltSpec())
