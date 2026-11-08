from pathlib import Path
from dataclasses import replace
from itertools import product
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from audit_support import Audit
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
from bp_registry.resolution import STABLE_SPA_F64, ResolutionPolicy, BpFloodingPolicy
HERE=Path(__file__).parent
POLICY=replace(STABLE_SPA_F64,damping=0.,zero_syndrome_shortcut=False)


def randomized_trees():
    rng=np.random.default_rng(3401);assignments=np.array(list(product(range(4),repeat=5)),dtype=np.uint8)
    worst=0.;cases=0
    for _ in range(12):
        labels=rng.integers(1,4,5,dtype=np.uint8);h=np.zeros((4,5),dtype=np.uint8)
        for c in range(4):h[c,c:c+2]=labels[c:c+2]
        priors=rng.dirichlet(np.full(4,.7),5)
        code=PauliCode(checks=h);g=CompiledBp4Graph.from_code(code,priors,policy=POLICY)
        # Independent local parity tests, no production syndrome helper.
        syn=np.sum((h[None,:,:]!=0)&(assignments[:,None,:]!=0)&(assignments[:,None,:]!=h[None,:,:]),axis=2)%2
        mass=np.prod(priors[np.arange(5)[None,:],assignments],axis=1)
        for bits in product((0,1),repeat=4):
            s=np.array(bits,dtype=np.uint8);w=mass*np.all(syn==s,axis=1);w/=w.sum()
            expected=np.array([[w[assignments[:,v]==a].sum() for a in range(4)] for v in range(5)])
            old=g.initial_v2c()
            for step in range(4):r=g.sweep(old,s);old=r.v2c
            err=float(abs(r.marginals-expected).max());worst=max(worst,err)
            assert err<2e-12,(cases,err)
            cases+=1
    return dict(cases=cases,seed=3401,assignments=1024,sweeps=4,max_error=worst,tolerance=2e-12)


def graph_covariance():
    rng=np.random.default_rng(3402);h=np.array([[1,2,3,0,0],[0,0,3,1,2],[1,2,0,1,2]],dtype=np.uint8)
    cases=0;worst=0.
    for _ in range(20):
        p=rng.dirichlet(np.ones(4),5);s=rng.integers(0,2,3,dtype=np.uint8);v=rng.permutation(5);c=rng.permutation(3)
        a=CompiledBp4Graph.from_code(PauliCode(checks=h),p,policy=POLICY)
        b=CompiledBp4Graph.from_code(PauliCode(checks=h[c][:,v]),p[v],policy=POLICY)
        olda=a.initial_v2c();oldb=b.initial_v2c()
        for _ in range(5):
            ra=a.sweep(olda,s);rb=b.sweep(oldb,s[c]);olda=ra.v2c;oldb=rb.v2c
            err=float(abs(rb.marginals-ra.marginals[v]).max());worst=max(worst,err);assert err<2e-12
            cases+=1
    return dict(cases=cases,max_error=worst,tolerance=2e-12,scope='loopy graph covariance, not exact loopy inference')


def deterministic_prior_boundary():
    code=PauliCode(checks=np.array([[1,1]],dtype=np.uint8));rejected=[]
    for p in ([1.,0.,0.,0.],[.5,.5,0.,0.]):
        try:CompiledBp4Graph.from_code(code,np.tile(p,(2,1)),policy=POLICY)
        except ValueError as e:rejected.append(str(e))
        else:raise AssertionError('zero probabilities silently accepted')
    return dict(rejected=rejected,classification='explicit domain exclusion: strictly positive joint probabilities; deterministic/erasure channels need a separately qualified representation')

if __name__=='__main__':
    a=Audit(HERE)
    for name,fn in [('random_nonuniform_four_check_tree_exact_inference',randomized_trees),('joint_graph_relabeling',graph_covariance),('deterministic_prior_domain',deterministic_prior_boundary)]:a.probe(name,fn)
    a.finish()
