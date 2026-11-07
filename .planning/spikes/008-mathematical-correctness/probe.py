"""Independent probability-domain and exhaustive-enumeration kernel probes.

Run: PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/008-mathematical-correctness/probe.py
Findings are retained in results.json; process success means the audit ran.
"""
from dataclasses import replace
from itertools import product
from pathlib import Path
import math
import numpy as np
from audit_support import Audit
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import (BINARY_SPA_F64_V2, REFERENCE_CPU_F64,
    check_to_variable, probability_to_llr, prior_llr)
from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import (QBP4_F64_V1, QBP4_F64_V2,
    check_message, pauli_hard_decision, probabilities_to_llrs, llrs_to_probabilities,
    commutation_llr)
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem

def anti(a,b):
    # Independent Pauli commutation truth table, in I/X/Y/Z order.
    return int(a != 0 and b != 0 and a != b)

def exact_marginals(checks, syndrome, priors, quaternary=False):
    n, q = priors.shape
    masses=np.zeros((n,q)); total=0.
    for state in product(range(q), repeat=n):
        observed=[sum(anti(int(label), state[j]) if quaternary else int(label)*state[j]
                      for j,label in enumerate(row))%2 for row in checks]
        if observed != list(syndrome): continue
        weight=math.prod(priors[j,x] for j,x in enumerate(state))
        total+=weight
        for j,x in enumerate(state): masses[j,x]+=weight
    assert total>0
    return masses/total

def probability_sweep(checks, syndrome, priors, old, quaternary=False):
    """Enumerate local parity assignments, with no production LLR helpers."""
    edges=list(zip(*np.nonzero(checks))); q=priors.shape[1]
    c2v={}
    for i,j in edges:
        others=[k for row,k in edges if row==i and k!=j]
        msg=np.zeros(q)
        for x in range(q):
            for state in product(range(q), repeat=len(others)):
                parity=anti(int(checks[i,j]),x) if quaternary else x
                weight=1.
                for k,y in zip(others,state):
                    parity ^= anti(int(checks[i,k]),y) if quaternary else y
                    weight *= old[(i,k)][y]
                if parity==syndrome[i]: msg[x]+=weight
        c2v[(i,j)]=msg/msg.sum()
    beliefs=[]; new={}
    for j in range(priors.shape[0]):
        incident=[i for i,k in edges if k==j]
        p=priors[j].copy()
        for i in incident: p*=c2v[(i,j)]
        beliefs.append(p/p.sum())
        for excluded in incident:
            p=priors[j].copy()
            for i in incident:
                if i!=excluded: p*=c2v[(i,j)]
            new[(excluded,j)]=p/p.sum()
    return np.array(beliefs), new

def binary_oracles():
    rng=np.random.default_rng(110608); cases=0; max_error=0.
    tree=np.array([[1,1,0,0,0],[0,1,1,0,0],[0,0,1,1,1]],dtype=np.uint8)
    loop=np.array([[1,1,0,1],[0,1,1,1],[1,0,1,0]],dtype=np.uint8)
    for h in (tree,loop):
        for profile in (REFERENCE_CPU_F64, replace(BINARY_SPA_F64_V2,v2c_damping=0)):
            kernel=BinarySpaKernel(profile=profile); schedule=FloodingSchedule(EdgeTable.from_check_matrix(h),kernel=kernel,profile=profile)
            for s in product(range(2),repeat=len(h)):
                p=float(rng.uniform(.07,.43)); priors=np.tile([1-p,p],(h.shape[1],1))
                old={e:priors[e[1]].copy() for e in zip(*np.nonzero(h))}
                v2c=schedule.initialize(p)
                for step in range(6):
                    expected,old=probability_sweep(h,s,priors,old)
                    actual=schedule.sweep(v2c,np.array(s,dtype=np.uint8),error_rate=p)
                    actual_p=1/(1+np.exp(actual.beliefs))
                    delta=float(np.max(abs(actual_p-expected[:,1]))); max_error=max(delta,max_error)
                    assert delta<2e-12, (profile.profile_id,s,step,delta)
                    v2c=actual.new_v2c; cases+=1
                if h is tree:
                    np.testing.assert_allclose(actual_p,exact_marginals(h,s,priors)[:,1],atol=2e-12,rtol=0)
    return dict(sweeps=cases,max_absolute_error=max_error,seed=110608)

def pauli_oracles():
    rng=np.random.default_rng(110609); cases=0; max_error=0.
    # Commuting trees: common label on each shared qubit, varying across qubits.
    tree=np.array([[1,3,0,0,0],[0,3,2,0,0],[0,0,2,1,3]],dtype=np.uint8)
    loop=np.array([[1,3,0,1],[0,3,2,1],[1,0,2,0]],dtype=np.uint8)
    for h in (tree,loop):
        code=PauliCode(checks=h)
        for profile in (QBP4_F64_V1,replace(QBP4_F64_V2,v2c_damping=0)):
            for s in product(range(2),repeat=len(h)):
                priors=rng.dirichlet(np.ones(4)*3,size=code.n)
                session=ScalarLlrBp4Kernel(profile=profile).new_session(QuaternaryOriginalProblem('original-oracle',code,np.array(s,dtype=np.uint8)),priors)
                old={e:priors[e[1]].copy() for e in zip(*np.nonzero(h))}
                for step in range(6):
                    expected,old=probability_sweep(h,s,priors,old,True)
                    actual=session.sweep(stop_on_convergence=False)
                    delta=float(np.max(abs(actual.marginals-expected))); max_error=max(max_error,delta)
                    assert delta<2e-12,(profile.profile_id,s,step,delta)
                    cases+=1
                if h is tree:
                    np.testing.assert_allclose(actual.marginals,exact_marginals(h,s,priors,True),atol=2e-12,rtol=0)
    return dict(sweeps=cases,max_absolute_error=max_error,seed=110609)

def damped_oracles():
    # Independently damp vector probability messages by geometric mixing.
    h=np.array([[1,3,0],[0,3,2]],dtype=np.uint8); code=PauliCode(checks=h)
    priors=np.array([[.7,.1,.15,.05],[.5,.2,.1,.2],[.4,.1,.3,.2]])
    results=[]
    for damping in (0.,.1,.5,.95):
        profile=replace(QBP4_F64_V2,v2c_damping=damping)
        session=ScalarLlrBp4Kernel(profile=profile).new_session(QuaternaryOriginalProblem('original-damping',code,np.array([1,0],dtype=np.uint8)),priors)
        old={e:priors[e[1]].copy() for e in zip(*np.nonzero(h))}
        for _ in range(12):
            expected,new=probability_sweep(h,[1,0],priors,old,True)
            actual=session.sweep(stop_on_convergence=False)
            np.testing.assert_allclose(actual.marginals,expected,rtol=0,atol=2e-12)
            for e in old:
                value=old[e]**damping*new[e]**(1-damping)
                old[e]=value/value.sum()
        results.append(damping)
    return dict(damping_values=results,sweeps=48)

def maximum_posterior():
    failures=[]; count=0
    for values in product((-2.,0.,2.),repeat=3):
        logweights=np.array([0.,*[-v for v in values]])
        for profile in (QBP4_F64_V1,QBP4_F64_V2):
            selected=int(pauli_hard_decision(values,profile=profile)); count+=1
            if logweights[selected]<logweights.max():
                failures.append(dict(llrs=values,profile=profile.profile_id,selected=selected,
                                     maximizers=np.flatnonzero(logweights==logweights.max()).tolist()))
    return count,failures

if __name__=='__main__':
    audit=Audit(Path(__file__).parent)
    audit.probe('binary_probability_and_exact_tree_oracles',binary_oracles)
    audit.probe('pauli_probability_and_exact_tree_oracles',pauli_oracles)
    audit.probe('geometric_probability_damping_oracle',damped_oracles)
    count,failures=maximum_posterior()
    audit.record('hard_decision_always_selects_a_maximizer',not failures,cases=count,counterexamples=failures)
    for p in (1e-12,1e-300,float(np.nextafter(0.,1.))):
        expected=float(np.log1p(-p)-np.log(p))
        for name,fn in [('prior_llr',prior_llr),('probability_to_llr',probability_to_llr)]:
            def probe(fn=fn,p=p,expected=expected):
                actual=float(fn(p,profile=BINARY_SPA_F64_V2))
                assert abs(actual-expected)<1e-12
                return dict(p=p,expected=expected,actual=actual)
            audit.probe(f'finite_positive_prior:{name}:{p}',probe)
    for name,fn,profile in [('binary',check_to_variable,BINARY_SPA_F64_V2),('pauli',check_message,QBP4_F64_V2)]:
        incoming=[30.,35.,37.,38.,40.,100.]
        values=[fn([x],syndrome=0,profile=profile) for x in incoming]
        audit.record(f'{name}_degree_two_check_monotonicity',all(a<=b for a,b in zip(values,values[1:])),
                     incoming=incoming,outgoing=values,classification='declared_numerical_policy_tradeoff')
        audit.record(f'{name}_degree_one_finite_safeguard',math.isfinite(fn([],syndrome=1,profile=profile)),
                     outgoing=fn([],syndrome=1,profile=profile))
        audit.record(f'{name}_zero_input_erases_check_information',fn([2.,0.,-3.],syndrome=1,profile=profile)==0.)
    audit.finish()
