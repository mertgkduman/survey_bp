"""Independent tree inference, mixed-magnitude messages and finite-state guards."""
from pathlib import Path
from dataclasses import replace
from itertools import product
from importlib.util import spec_from_file_location,module_from_spec
import math
import numpy as np
from audit_support import Audit
from bp_registry.resolution import STABLE_SPA_F64,ResolutionPolicy
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode

HERE=Path(__file__).parent
spec=spec_from_file_location('exact_parity',HERE.parent/'019-numerical-envelope/probe.py');oracle=module_from_spec(spec);spec.loader.exec_module(oracle)
POLICY=replace(STABLE_SPA_F64,damping=0.,zero_syndrome_shortcut=False)
H=np.array([[1,1,1,0,0],[0,0,1,1,1]],dtype=np.uint8)


def tree_inference():
    cases=[];worst=0.
    labels=np.array([[1,2,3,0,0],[0,0,3,1,2]],dtype=np.uint8)
    for family in ('binary','pauli'):
        assignments=np.array(list(product(range(2 if family=='binary' else 4),repeat=5)),dtype=np.uint8)
        for rate in (.01,.2,.49,.8):
            if family=='binary':
                priors=np.tile([1-rate,rate],(5,1)); graph=CompiledBinaryFlooding.from_check_matrix(H,policy=POLICY)
                observed=(assignments@H.T)%2
            else:
                priors=np.array([[1-rate,rate*.2,rate*.3,rate*.5],[.4,.1,.2,.3],[1-rate,rate/3,rate/3,rate/3],[.2,.4,.1,.3],[.5,.2,.2,.1]])
                graph=CompiledBp4Graph.from_code(PauliCode(checks=labels),priors,policy=POLICY)
                observed=np.array([np.sum((labels!=0)&(a[None,:]!=0)&(labels!=a[None,:]),axis=1)%2 for a in assignments])
            masses=np.prod(priors[np.arange(5)[None,:],assignments],axis=1)
            for bits in product((0,1),repeat=2):
                s=np.array(bits,dtype=np.uint8);valid=np.all(observed==s,axis=1);weights=masses*valid
                exact=np.array([[weights[assignments[:,v]==a].sum()/weights.sum() for a in range(priors.shape[1])] for v in range(5)])
                old=np.full(len(graph.variables),math.log1p(-rate)-math.log(rate)) if family=='binary' else graph.initial_v2c()
                for _ in range(2):
                    result=graph.sweep(old,s,**({'error_rate':rate} if family=='binary' else {}));old=result.new_v2c if family=='binary' else result.v2c
                if family=='binary':
                    actual=1/(1+np.exp(result.beliefs));err=float(np.max(abs(actual-exact[:,1])))
                else:err=float(np.max(abs(result.marginals-exact)))
                worst=max(worst,err);assert err<2e-12
                cases.append(dict(family=family,rate=rate,syndrome=s,max_marginal_error=err))
    return dict(cases=cases,max_error=worst,tolerance=2e-12,oracle='enumeration of 32 binary / 1024 Pauli assignments; two checks sharing one variable; two undamped sweeps')


def mixed_envelope():
    rng=np.random.default_rng(2701);worst=0.;cases=0
    for degree in (2,3,7,17,65):
        graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,degree),dtype=np.uint8),policy=POLICY)
        for _ in range(12):
            values=rng.choice([-1.,1.],degree)*np.exp(rng.uniform(np.log(1e-10),np.log(1000.),degree))
            if cases%3==0:values[rng.integers(degree)]=0.
            for bit in (0,1):
                actual=graph.sweep(values,np.array([bit],dtype=np.uint8),error_rate=.2).check_to_variable
                for edge in (0,degree//2,degree-1):
                    expected=(-1)**bit*oracle.parity_llr(np.delete(values,edge));err=abs(actual[edge]-expected)
                    worst=max(worst,float(err));assert err<2e-11
                perm=rng.permutation(degree)
                changed=graph.sweep(values[perm],np.array([bit],dtype=np.uint8),error_rate=.2).check_to_variable
                np.testing.assert_allclose(changed,actual[perm],atol=2e-11,rtol=0)
                cases+=1
    return dict(cases=cases,selected_oracle_edges=cases*3,seed=2701,max_error=worst,tolerance=2e-11,permutation_checks=cases)


def pauli_covariance():
    code=PauliCode(checks=np.array([[1,2,3]],dtype=np.uint8));priors=np.array([[.4,.1,.2,.3],[.1,.5,.15,.25],[.3,.1,.2,.4]])
    rows=[];s=np.array([1],dtype=np.uint8)
    graph=CompiledBp4Graph.from_code(code,priors,policy=POLICY);base=graph.sweep(graph.initial_v2c(),s)
    for permutation in ((0,2,3,1),(0,3,1,2),(0,3,2,1)):
        perm=np.array(permutation);p=np.empty_like(priors);p[:,perm]=priors
        transformed=CompiledBp4Graph.from_code(PauliCode(checks=perm[code.checks]),p,policy=POLICY)
        actual=transformed.sweep(transformed.initial_v2c(),s)
        np.testing.assert_allclose(actual.marginals[:,perm],base.marginals,atol=2e-12,rtol=0)
        rows.append(permutation)
    return dict(nonidentity_label_permutations=rows,tolerance=2e-12)


def overflow(a):
    code=PauliCode(checks=np.ones((2,2),dtype=np.uint8));priors=np.tile([.7,.1,.1,.1],(2,1));s=np.ones(2,dtype=np.uint8)
    rows=[]
    for scope in ('scalar_edges','all_messages','all_state'):
        policy=replace(POLICY,resolution=ResolutionPolicy('float64',scope=scope))
        graph=CompiledBp4Graph.from_code(code,priors,policy=policy)
        try:
            result=graph.sweep(np.full((4,3),1e308),s)
            rows.append(dict(scope=scope,rejected=False,finite_beliefs=bool(np.isfinite(result.beliefs).all()),finite_messages=bool(np.isfinite(result.v2c).all()),finite_marginals=bool(np.isfinite(result.marginals).all()),candidate=result.candidate))
        except (ValueError,ArithmeticError) as exc:rows.append(dict(scope=scope,rejected=True,error=type(exc).__name__))
    a.record('C01_finite_inputs_cannot_return_nonfinite_BP4_state',all(r['rejected'] or (r['finite_beliefs'] and r['finite_messages'] and r['finite_marginals']) for r in rows),
        rows=rows,input_magnitude=1e308,classification='finite-input overflow guard, not ordinary-range accuracy',checks=code.checks,syndrome=s)

if __name__=='__main__':
    a=Audit(HERE);a.probe('multi_check_tree_inference',tree_inference);a.probe('mixed_magnitude_parity_and_permutations',mixed_envelope);a.probe('Pauli_label_covariance',pauli_covariance);overflow(a);a.finish()
