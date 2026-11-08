"""All circuit construction routes validate before bounds-unchecked execution."""
from dataclasses import replace, fields
import numpy as np
import pytest
import stim
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.sinter_adapter import CanonicalBpSinterDecoder, CompiledCanonicalBpDecoder


def model():
    return DemBinaryModel.from_dem(stim.DetectorErrorModel('error(.1) D0 L0\nerror(.2) D0 D1 L1'))


@pytest.mark.parametrize('direct',[False,True])
@pytest.mark.parametrize('kwargs',[
    {'max_iterations':-1},{'max_iterations':True},{'max_iterations':1.5},
    {'rule':'unknown'},{'tie_break':'unknown'},{'model':object()},
])
def test_compiled_circuit_admission(direct,kwargs):
    valid=CompiledCanonicalBpDecoder(model(),3,'spa','zero')
    with pytest.raises((TypeError,ValueError)):
        if direct:CompiledCanonicalBpDecoder(**{**{f.name:getattr(valid,f.name) for f in fields(valid)},**kwargs})
        else:replace(valid,**kwargs)


@pytest.mark.parametrize('kwargs',[
    {'row_ptr':np.array([0,99,2])},{'row_ptr':np.array([0,2,3.])},
    {'row_ptr':np.array([0,1,3])},{'variables':np.array([0,1,8])},
    {'variables':np.array([0,1,0])},{'variables':np.array([0.,1.,1.])},
    {'prior_llrs':np.array([np.nan,0.])},{'prior_llrs':np.array([np.inf,0.])},
    {'prior_llrs':np.array([1e400,0.],dtype=np.longdouble)},
    {'prior_llrs':np.array([1j,0.])},{'prior_llrs':np.zeros(3)},
    {'observable_matrix':np.ones((2,3),dtype=np.uint8)},
    {'observable_matrix':np.full((2,2),2,dtype=np.uint8)},
    {'syndrome_bias':np.array([2,0])},{'syndrome_bias':np.zeros(3,dtype=np.uint8)},
    {'observable_bias':np.zeros(3,dtype=np.uint8)},
    {'source_error_count':-1},{'source_error_count':True},{'source_error_count':1},
    {'dem_sha256':'not-a-digest'},{'table':object()},
])
def test_dem_replacement_rejects_invalid_state(kwargs):
    with pytest.raises((TypeError,ValueError)):replace(model(),**kwargs)


@pytest.mark.parametrize('text',['','error(.1) L0','error(1) D0 L0','error(.1) D0','error(.5) D0 L0'])
@pytest.mark.parametrize('rule',['spa','min_sum'])
def test_empty_deterministic_and_tie_routes(text,rule):
    dem=stim.DetectorErrorModel(text)
    decoder=CanonicalBpSinterDecoder(0,rule=rule).compile_decoder_for_dem(dem=dem)
    events=np.zeros((3,dem.num_detectors),dtype=np.uint8)
    detailed,ok,it=decoder.decode_detailed(events)
    packed=decoder.decode_shots_bit_packed(bit_packed_detection_event_data=np.packbits(events,axis=1,bitorder='little'))
    np.testing.assert_array_equal(packed,np.packbits(detailed,axis=1,bitorder='little'))
    assert detailed.shape==(3,dem.num_observables)
    assert (it==0).all()
