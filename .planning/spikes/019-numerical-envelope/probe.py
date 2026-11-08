"""High-precision parity partition oracle over a deliberately expanded envelope."""
from decimal import Decimal, localcontext
from pathlib import Path
from dataclasses import replace
import numpy as np
import math
from audit_support import Audit
from bp_registry.canonical.numerics import check_to_variable, boxplus, BINARY_SPA_F64_V3
from bp_registry.quaternary.numerics import check_message, QBP4_F64_V3
from bp_registry.canonical.compiled import CompiledBinaryFlooding


def parity_llr(values):
    # Independent sum over parity states, not a production tanh/boxplus helper.
    with localcontext() as context:
        context.prec = 600
        even, odd = Decimal(1), Decimal(0)
        for value in values:
            odds = (-Decimal(str(float(value)))).exp()
            p0 = 1 / (1 + odds); p1 = odds / (1 + odds)
            even, odd = even * p0 + odd * p1, odd * p0 + even * p1
        return float((even / odd).ln())


def sweep(a):
    rows=[]
    for degree in (1,2,4,16,64):
        for magnitude in (1e-12, .1, 1., 10., 20., 30., 38., 40., 100., 1000.):
            for negative in (False, True):
                values=np.full(degree,magnitude);values[0]*=-1 if negative else 1
                reference=parity_llr(values)
                actual=check_to_variable(values)
                pauli=check_message(values,syndrome=0)
                stable=boxplus(values,profile=BINARY_SPA_F64_V3)
                qstable=check_message(values,syndrome=0,profile=replace(QBP4_F64_V3,check_rule='boxplus'))
                assert actual==pauli
                assert abs(stable-reference)<2e-11 and abs(qstable-reference)<2e-11
                rows.append(dict(degree=degree,magnitude=magnitude,negative=negative,reference=reference,
                                 canonical=actual,error=abs(actual-reference),stable_boxplus=stable))
    a.record('stable_log_domain_matches_independent_parity_oracle',True,cases=len(rows),precision=600,tolerance=2e-11)
    bad=[row for row in rows if row['error']>2e-11]
    graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,3),dtype=np.uint8))
    posterior=graph.sweep(np.full(3,40.),np.array([1],dtype=np.uint8),error_rate=math.exp(-40.)/(1+math.exp(-40.))).beliefs
    exact_posterior=40.-parity_llr([40.,40.])
    a.record('known_default_approximation_not_global_exact_SPA',not bad,cases=len(rows),outside_tolerance=len(bad),
             max_error=max(row['error'] for row in rows),rows=rows,
             tree_example=dict(checks=[[1,1,1]],syndrome=[1],prior_llr=40.,canonical_beliefs=posterior,exact_beliefs=[exact_posterior]*3),
             classification='known exact-unity/tanh finite-precision limitation, expanded envelope; not a new regression')
    zero_cases=[]
    for values in ([0.,1.,2.],[0.,0.,100.],[-0.,-100.,100.],[1e-12,-1e-12,1e-12]):
        expected=parity_llr(values);actual=check_to_variable(np.array(values))
        assert abs(expected-actual)<2e-11
        zero_cases.append(dict(input=values,reference=expected,actual=actual))
    a.record('zero_and_near_zero_parity_cases',True,rows=zero_cases)


if __name__=='__main__':
    a=Audit(Path(__file__).parent);sweep(a);a.finish()
