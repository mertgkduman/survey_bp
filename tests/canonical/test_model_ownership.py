"""Scientific identity buffers cannot be mutated through aliases or write flags."""
from dataclasses import replace
import numpy as np
import pytest
import stim
from bp_registry.canonical.problems import OriginalProblem
from bp_registry.quaternary.problems import PauliCode,QuaternaryOriginalProblem
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.canonical.memory import V2CDamping
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.schedules import EdgeTable


def assert_immutable(array):
    with pytest.raises(ValueError):array.setflags(write=True)
    with pytest.raises(ValueError):array.flat[0]=0
    parent=array.base
    while isinstance(parent,np.ndarray):
        with pytest.raises(ValueError):parent.setflags(write=True)
        parent=parent.base


@pytest.mark.parametrize('field',['hx','hz','syndrome'])
def test_binary_original_owns_immutable_state(field):
    h=np.ones((1,2),dtype=np.uint8);s=np.ones(1,dtype=np.uint8)
    original=OriginalProblem('original-a',h,h,s)
    h[:]=0;s[:]=0
    np.testing.assert_array_equal(getattr(original,field),np.ones_like(getattr(original,field)))
    assert_immutable(getattr(original,field))
    replacement=replace(original,**{field:np.ones_like(getattr(original,field))})
    assert_immutable(getattr(replacement,field))


@pytest.mark.parametrize('field',['checks','logical_x','logical_z'])
def test_pauli_code_identity_and_logical_maps(field):
    h=np.array([[1,1]],dtype=np.uint8);x=np.array([[1,0]],dtype=np.uint8);z=np.array([[3,3]],dtype=np.uint8)
    code=PauliCode(checks=h,logical_x=x,logical_z=z);digest=code.semantic_sha256
    h[:]=0;x[:]=0;z[:]=0
    assert code.semantic_sha256==digest
    assert_immutable(getattr(code,field))


def test_quaternary_original_syndrome_identity():
    original=QuaternaryOriginalProblem('original-test',PauliCode(checks=np.array([[1,1]],dtype=np.uint8)),np.array([1],dtype=np.uint8))
    assert_immutable(original.syndrome)


@pytest.mark.parametrize('field',['row_ptr','variables','prior_llrs','observable_matrix','syndrome_bias','observable_bias'])
def test_dem_immutable_state(field):
    model=DemBinaryModel.from_dem(stim.DetectorErrorModel('error(.1) D0 L0'))
    assert_immutable(getattr(model,field))


def test_dem_execution_identity_distinguishes_valid_prior_replacement():
    model=DemBinaryModel.from_dem(stim.DetectorErrorModel('error(.1) L0'))
    modified=replace(model,prior_llrs=-model.prior_llrs)
    assert modified.dem_sha256==model.dem_sha256
    assert modified.execution_sha256!=model.execution_sha256
    assert replace(model).execution_sha256==model.execution_sha256


def test_policy_history_and_session_snapshot_ownership():
    state=V2CDamping('damping-test',.5).initial_state(np.array([1.,2.]))
    assert_immutable(state.v2c)
    session=BinarySpaKernel().new_session(EdgeTable.from_check_matrix(np.ones((1,2),dtype=np.uint8)),np.array([1],dtype=np.uint8),error_rate=.2)
    for field in ('prior','v2c','posterior','candidate','c2v'):
        assert_immutable(getattr(session.state,field))
