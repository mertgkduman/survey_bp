"""Counterexamples and adjacent contracts from freeze audit C03/C01/C02."""
from dataclasses import replace
import numpy as np
import pytest
from bp_registry.canonical.compiled import CompiledBinaryFlooding,BoundBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
from bp_registry.resolution import STABLE_SPA_F64


def binary():
    return CompiledBinaryFlooding.from_check_matrix(np.ones((1,2),dtype=np.uint8),policy=STABLE_SPA_F64)

def pauli():
    return CompiledBp4Graph.from_code(PauliCode(checks=np.ones((1,2),dtype=np.uint8)),np.tile([.7,.1,.1,.1],(2,1)),policy=STABLE_SPA_F64)

@pytest.mark.parametrize('prior',[np.nan,np.inf,-np.inf,np.longdouble('1e400'),True,'0.2',1j,[.2]])
@pytest.mark.parametrize('construction',['direct','replace'])
def test_bound_prior_rejects_invalid_state_before_shortcuts(prior,construction):
    graph=binary()
    with pytest.raises(ValueError):
        if construction=='direct':BoundBinaryFlooding(graph,prior)
        else:replace(graph.bind_error_rate(.2),prior=prior)

@pytest.mark.parametrize('prior',[0.,-.2,np.float32(.5),np.nextafter(0.,1.),1e308,-1e308])
def test_bound_prior_normalizes_finite_values_once(prior):
    bound=BoundBinaryFlooding(binary(),prior)
    assert type(bound.prior) is float
    assert bound.prior==float(prior)
    result=bound.run(np.array([0],dtype=np.uint8),max_iterations=0)
    np.testing.assert_array_equal(result.candidate,np.full(2,int(prior<0)))
    assert result.converged and result.iterations==0


def test_bound_prior_requires_compiled_graph():
    with pytest.raises(ValueError):BoundBinaryFlooding(object(),.2)

@pytest.mark.parametrize('value',[np.longdouble('1e400'),np.longdouble('-1e400'),np.longdouble('nan'),np.longdouble('inf')])
def test_pauli_stored_prior_is_validated_in_float64(value):
    with pytest.raises(ValueError):replace(pauli(),prior_llrs=np.full((2,3),value,dtype=np.longdouble))


def test_pauli_finite_cast_owns_immutable_normalized_prior():
    raw=np.full((2,3),np.longdouble(.123456789012345678))
    graph=replace(pauli(),prior_llrs=raw)
    expected=raw.astype(np.float64)
    raw[:]=9
    assert graph.prior_llrs.dtype==np.float64
    np.testing.assert_array_equal(graph.prior_llrs,expected)
    with pytest.raises(ValueError):graph.prior_llrs.setflags(write=True)
