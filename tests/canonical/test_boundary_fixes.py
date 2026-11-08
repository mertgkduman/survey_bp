"""Independent regressions for boundary audit B01–B03."""
from dataclasses import replace
import numpy as np
import pytest
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64
from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V3
from bp_registry.quaternary.problems import PauliCode

H = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)

def graphs():
    return (CompiledBinaryFlooding.from_check_matrix(H),
            CompiledBp4Graph.from_code(PauliCode(checks=H), np.tile([.7,.1,.1,.1],(3,1))))

def test_replacement_cannot_bypass_semantic_admission():
    binary, pauli = graphs()
    with pytest.raises(ValueError):
        replace(binary, numerical_profile=MIN_SUM_CPU_F64)
    with pytest.raises(ValueError):
        replace(pauli, profile=replace(QBP4_F64_V3, check_rule='boxplus'))
    with pytest.raises(ValueError):
        FloodingSchedule(binary.table, kernel=BinarySpaKernel(), profile=MIN_SUM_CPU_F64)

@pytest.mark.parametrize('family', [0, 1])
@pytest.mark.parametrize('field,value', [
    ('row_ptr', np.array([0,3,2])), ('row_ptr', np.array([0,2,5])),
    ('variables', np.array([0,1,1,3])), ('variables', np.array([0.,1.,1.,2.])),
])
def test_malformed_csr_is_rejected_before_native_execution(family, field, value):
    with pytest.raises(ValueError):
        replace(graphs()[family], **{field:value})

@pytest.mark.parametrize('field,value', [
    ('variable_ptr', np.array([0,1,2,4])),
    ('variable_edges', np.array([0,1,1,3])),
    ('labels', np.array([1,0,1,1])),
    ('prior_llrs', np.ones((3,2))),
])
def test_pauli_graph_cross_indexes_are_validated(field,value):
    with pytest.raises(ValueError):
        replace(graphs()[1], **{field:value})

@pytest.mark.parametrize('family', [0,1])
def test_graph_takes_immutable_ownership_of_raw_buffers(family):
    original = graphs()[family]
    raw = original.variables.copy()
    graph = replace(original, variables=raw)
    raw[0] = 2
    assert graph.variables[0] == 0
    with pytest.raises(ValueError):
        graph.variables.setflags(write=True)
