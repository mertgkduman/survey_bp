"""Independent probability recurrences and boundary probes for the stabilized v3."""
from dataclasses import replace
from importlib.util import spec_from_file_location,module_from_spec
from itertools import product
from pathlib import Path
import math
import numpy as np
from audit_support import Audit,ROOT
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import BINARY_SPA_F64_V3,prior_llr,probability_to_llr,check_to_variable
from bp_registry.canonical.schedules import EdgeTable,FloodingSchedule
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import QBP4_F64_V3,pauli_hard_decision,check_message
from bp_registry.quaternary.problems import PauliCode,QuaternaryOriginalProblem
from bp_registry.resolution import ResolutionPolicy

HERE=Path(__file__).parent
spec=spec_from_file_location('independent_oracle',HERE.parent/'008-mathematical-correctness/probe.py')
oracle=module_from_spec(spec);spec.loader.exec_module(oracle)


def recurrences(quaternary):
    rng=np.random.default_rng(12007+int(quaternary)); worst=0.; count=0; exact=0
    matrices=[np.array([[1,1,0,0,0,0],[0,1,1,0,0,0],[0,0,1,1,1,0]],dtype=np.uint8),
              np.array([[1,1,0,1,0],[0,1,1,1,0],[1,0,1,0,0]],dtype=np.uint8)]
    for index,h in enumerate(matrices):
        if quaternary: h=h*np.resize(np.array([1,3,2,1,3,2],dtype=np.uint8),h.shape[1])
        edges=list(zip(*np.nonzero(h)))
        for bits in product((0,1),repeat=len(h)):
            s=np.array(bits,dtype=np.uint8)
            if quaternary: priors=rng.dirichlet(np.ones(4)*4,size=h.shape[1])
            else:
                p=rng.uniform(.08,.85,h.shape[1]);priors=np.column_stack([1-p,p])
            for damping in (0.,.1,.65,.95):
                old={edge:priors[edge[1]].copy() for edge in edges}
                if quaternary:
                    profile=replace(QBP4_F64_V3,v2c_damping=damping)
                    session=ScalarLlrBp4Kernel(profile=profile).new_session(QuaternaryOriginalProblem('original-v3-oracle',PauliCode(checks=h),s),priors)
                else:
                    profile=replace(BINARY_SPA_F64_V3,v2c_damping=damping)
                    kernel=BinarySpaKernel(profile=profile)
                    schedule=FloodingSchedule(EdgeTable.from_check_matrix(h),kernel=kernel,profile=profile)
                    prior=np.log(priors[:,0])-np.log(priors[:,1]);v2c=np.array([prior[j] for i,j in edges])
                for _ in range(6):
                    expected,new=oracle.probability_sweep(h,s,priors,old,quaternary)
                    if quaternary:
                        actual=session.sweep(stop_on_convergence=False);marginals=actual.marginals
                        actual_edges=actual.v2c
                    else:
                        actual=schedule.sweep(v2c,s,error_rate=.1,prior_llrs=prior)
                        one=1/(1+np.exp(actual.beliefs));marginals=np.column_stack([1-one,one])
                        v2c=actual.new_v2c;actual_edges=v2c
                    delta=float(np.max(np.abs(marginals-expected)));worst=max(worst,delta)
                    assert delta<2e-12,(quaternary,index,bits,damping,delta)
                    for edge_index,edge in enumerate(edges):
                        mixed=old[edge]**damping*new[edge]**(1-damping);old[edge]=mixed/mixed.sum()
                        expected_llr=np.log(old[edge][0])-np.log(old[edge][1:])
                        np.testing.assert_allclose(actual_edges[edge_index],expected_llr if quaternary else expected_llr[0],atol=2e-11,rtol=0)
                    count+=1
                if index==0 and damping==0:
                    np.testing.assert_allclose(marginals,oracle.exact_marginals(h,s,priors,quaternary),atol=2e-12,rtol=0);exact+=1
    return dict(sweeps=count,exact_tree_cases=exact,max_probability_error=worst,nonuniform_priors=True,isolated_variables=True)


def ties():
    cases=0
    for values in product((-1e5,-2.,-0.,0.,2.,1e5),repeat=3):
        scores=np.array([0.,*values]);chosen=int(pauli_hard_decision(values))
        assert chosen==np.argmin(scores),(values,chosen);cases+=1
    return dict(cases=cases,decision='MAP with I<X<Y<Z ties')


def finite_priors():
    rng=np.random.default_rng(12009)
    values=np.r_[np.nextafter(0.,1.),np.nextafter(1.,0.),.5,np.exp(rng.uniform(-740,-.7,1000))]
    worst=0.
    for p in values:
        expected=math.log1p(-float(p))-math.log(float(p))
        for actual in (prior_llr(float(p)),float(probability_to_llr(p))):
            assert math.isfinite(actual);worst=max(worst,abs(actual-expected))
            assert abs(actual-expected)<2e-12
    return dict(probabilities=len(values),max_log_odds_error=worst)


def float16_boundaries():
    representable=np.arange(65536,dtype=np.uint16).view(np.float16)
    representable=np.unique(representable[np.isfinite(representable)].astype(float))
    midpoint=(representable[:-1]+representable[1:])/2
    values=np.r_[representable,midpoint,np.nextafter(midpoint,-np.inf),np.nextafter(midpoint,np.inf)]
    policy=ResolutionPolicy('float16')
    expected=np.clip(values,-65504,65504).astype(np.float16).astype(float)
    actual=np.array([policy.quantize(float(x)) for x in values])
    different=np.flatnonzero(actual!=expected)
    assert not len(different),dict(count=len(different),inputs=values[different[:8]].tolist(),actual=actual[different[:8]].tolist(),expected=expected[different[:8]].tolist())
    return dict(cases=len(values),reference='NumPy float16 conversion after finite saturation')


def safeguard_characterization():
    rows=[]
    for value in (0.,1.,20.,30.,38.,40.,100.):
        binary=check_to_variable(np.array([value]));pauli=check_message([value],syndrome=0)
        assert binary==pauli
        rows.append(dict(input=value,output=binary,exact_SPA=value,error=binary-value))
    assert rows[5]['output']<rows[4]['output']
    return dict(rows=rows,interpretation='known declared exact-unity adaptation; not exact SPA over all finite inputs')


if __name__=='__main__':
    a=Audit(HERE)
    a.probe('binary_v3_nonuniform_probability_oracle',lambda:recurrences(False))
    a.probe('pauli_v3_probability_oracle',lambda:recurrences(True))
    a.probe('v3_MAP_equality_patterns',ties)
    a.probe('stable_finite_binary_priors',finite_priors)
    a.probe('float16_rounding_boundary_exhaustion',float16_boundaries)
    a.probe('declared_safeguard_domain_limit',safeguard_characterization)
    a.finish()
