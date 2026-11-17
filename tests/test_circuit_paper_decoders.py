"""Independent subproblem/branch oracles for source-configured circuit search."""
import itertools
import numpy as np
import pytest
import stim
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.paper_decoders import CircuitPaperDecoder,PaperDecoderSpec
from test_prior_tilt import oracle_step,uniform


def model_from_h(h,prior):
    lines=[]
    for v in range(h.shape[1]):
        targets=' '.join(f'D{r}' for r in range(h.shape[0]) if h[r,v])
        lines.append(f'error({1/(1+np.exp(prior[v])):.17g}) {targets} L0')
    return DemBinaryModel.from_dem(stim.DetectorErrorModel('\n'.join(lines)))


def oracle_segment(h,prior,syn,fixed,messages,posterior,cap,gamma=None):
    edges=list(zip(*np.nonzero(h)));active=np.flatnonzero(fixed<0)
    free=[e for e,(r,v) in enumerate(edges) if fixed[v]<0]
    target=(syn+h[:,fixed>=0]@fixed[fixed>=0])%2
    old=messages[free].copy();post=posterior.copy();sums=np.zeros(len(prior));bias=0
    for t in range(1,cap+1):
        effective=prior.copy() if gamma is None else (1-gamma)*prior+gamma*post
        bias+=0 if gamma is None else np.count_nonzero(effective!=prior)
        c,p,old,_=oracle_step(h[:,active],effective[active],old,target)
        post=effective.copy();post[active]=p
        candidate=np.where(fixed>=0,fixed,0).astype(np.uint8);candidate[active]=c
        sums[active]+=p
        valid=np.array_equal(h@candidate%2,syn)
        if valid:break
    out=messages.copy();out[free]=old
    return candidate,post,sums,out,valid,t,len(free),bias


def beam_oracle(h,prior,syn,spec):
    edges=list(zip(*np.nonzero(h)));root=oracle_segment(h,prior,syn,np.full(len(prior),-1),np.array([prior[v] for r,v in edges]),prior,spec.initial)
    trace=[[-1,-1,-1,root[5],root[6],int(root[4]),0,0]];steps=root[5];work=2*root[5]*root[6]
    if root[4]:return root[0],steps,work,trace
    nodes=[(root,np.full(len(prior),-1))];front=[0]
    for depth in range(spec.rounds):
        children=[]
        for parent in front:
            state,fixed=nodes[parent]
            v=0 if depth==0 else -1;score=abs(state[2][0]) if depth==0 else float('inf')
            for j in range(len(prior)):
                if fixed[j]<0 and h[:,j].sum()>2 and abs(state[2][j])<score:v=j;score=abs(state[2][j])
            if v<0:continue
            for bit in (0,1):
                mask=fixed.copy();mask[v]=bit
                state2=oracle_segment(h,prior,syn,mask,state[3],state[1],spec.per_leg)
                index=len(nodes);nodes.append((state2,mask));steps+=state2[5];work+=2*state2[5]*state2[6]
                trace.append([parent,v,bit,state2[5],state2[6],int(state2[4]),0,0])
                if state2[4]:return state2[0],steps,work,trace
                reliability=sum(abs(state2[2][j]) for j in range(len(prior)) if mask[j]<0)/state2[5]
                children.append((reliability,index))
        children.sort(reverse=True);front=[i for score,i in children[:spec.width]]
        for score,i in children[spec.width:]:trace[i][6]=1
        if not front:break
    return root[0],steps,work,trace


@pytest.mark.parametrize('syndrome',list(itertools.product((0,1),repeat=3)))
def test_beam_full_branch_lineage_work_and_fallback_against_independent_oracle(syndrome):
    h=np.ones((3,4),np.uint8);m=model_from_h(h,np.array([1.,2.,3.,4.]))
    # Source model uses its canonical log1p prior; feed the same bytes to oracle.
    c=PaperDecoderSpec(method='beam',initial=4,per_leg=2,width=2,rounds=2)
    syn=np.array(syndrome,np.uint8)
    actual=CircuitPaperDecoder(m,c).decode(syn,shot=3);expected=beam_oracle(h,m.prior_llrs,syn,c)
    np.testing.assert_array_equal(actual.candidate,expected[0])
    assert (actual.iterations,actual.directed_edge_updates)==expected[1:3]
    assert actual.trace.tolist()==expected[3]


def test_relay_resets_messages_carries_posterior_and_counts_all_legs():
    h=np.array([[1,1,1],[1,1,1]],np.uint8);m=model_from_h(h,np.array([1.,2.,3.]))
    c=PaperDecoderSpec(method='relay',initial=4,per_leg=2,additional=3,first_gamma=.25,gamma_low=-.25,gamma_high=.5)
    syn=np.array([0,1],np.uint8);seed=9;shot=11
    actual=CircuitPaperDecoder(m,c,seed).decode(syn,shot=shot)
    post=m.prior_llrs.copy();prior=m.prior_llrs;edges=list(zip(*np.nonzero(h)));steps=0;work=0;bias=0
    for leg in range(4):
        gamma=np.full(3,.25) if leg==0 else np.array([-.25+.75*uniform(seed,shot,leg,v) for v in range(3)])
        state=oracle_segment(h,prior,syn,np.full(3,-1),np.array([prior[v] for r,v in edges]),post,4 if leg==0 else 2,gamma)
        if leg==0:fallback=state[0].copy();fallback_post=state[1].copy()
        post=state[1];steps+=state[5];work+=2*state[5]*state[6];bias+=state[7]
    np.testing.assert_array_equal(actual.candidate,fallback)
    np.testing.assert_allclose(actual.posterior,fallback_post,atol=1e-12)
    assert actual.iterations==steps==10 and actual.directed_edge_updates==work and actual.biased_node_updates==bias
    assert actual.random_draws==9 and len(actual.trace)==4 and not actual.converged


def test_zero_syndrome_uses_one_sweep_and_no_extra_path_work():
    h=np.ones((3,4),np.uint8);m=model_from_h(h,np.array([1.,2.,3.,4.]))
    for method in ('relay','beam'):
        a=CircuitPaperDecoder(m,PaperDecoderSpec(method=method)).decode(np.zeros(3,np.uint8),shot=2)
        assert a.converged and a.iterations==1 and len(a.trace)==1 and a.random_draws==0


def test_controller_specific_and_input_controls_are_not_silently_ignored():
    with pytest.raises(ValueError):PaperDecoderSpec(method='beam',first_gamma=.5)
    with pytest.raises(ValueError):PaperDecoderSpec(method='relay',width=5)
    with pytest.raises(ValueError):PaperDecoderSpec(method='relay',gamma_low=1.,gamma_high=0.)
