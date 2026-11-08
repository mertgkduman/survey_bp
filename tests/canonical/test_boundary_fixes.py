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

from bp_registry.canonical.numerics import BINARY_SPA_F64_V3, REFERENCE_CPU_F64
from bp_registry.canonical.schedules import CheckNodeSerialSchedule, VariableNodeSerialSchedule, LayeredSchedule
from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
from bp_registry.canonical.budgets import BudgetTree

@pytest.mark.parametrize('kind', [CheckNodeSerialSchedule, VariableNodeSerialSchedule, LayeredSchedule])
@pytest.mark.parametrize('damping', [0., .1, .6])
def test_local_damping_matches_independent_degree_two_recurrence(kind, damping):
    # Degree-two checks send precisely the other incoming LLR, with syndrome sign.
    old=np.array([.3,-.6,1.2,.9]); syndrome=np.array([1,0],dtype=np.uint8)
    kernel=BinarySpaKernel(profile=replace(BINARY_SPA_F64_V3,v2c_damping=damping))
    kwargs={'partitions':((0,),(1,)), 'provenance':'explicit'} if kind is LayeredSchedule else {}
    schedule=kind(EdgeTable.from_check_matrix(H),kernel=kernel,**kwargs)
    selected=[0] if kind is VariableNodeSerialSchedule else [0,1,2]
    c2v=np.array([.6,0.,0.,0.]) if kind is VariableNodeSerialSchedule else np.array([.6,-.3,0.,0.])
    beliefs=np.full(3,np.log(4.))
    for edge, variable in enumerate([0,1,1,2]): beliefs[variable]+=c2v[edge]
    expected=old.copy()
    for edge in selected:
        expected[edge]=damping*old[edge]+(1-damping)*(beliefs[[0,1,1,2][edge]]-c2v[edge])
    executor=CanonicalLocalStepExecutor(BudgetTree(limits=(),parents={}),scope='attempt')
    schedule.execute_local_step(executor,old,syndrome,error_rate=.2,
        progress=ScheduleProgress(iteration=0,local_steps=0,cursor=(0,)),is_converged=lambda _:False)
    np.testing.assert_allclose(old,expected,rtol=0,atol=2e-14)

@pytest.mark.parametrize('kind', [CheckNodeSerialSchedule, VariableNodeSerialSchedule, LayeredSchedule])
def test_local_entry_clipping_uses_active_v1_cap(kind):
    kernel=BinarySpaKernel(profile=replace(REFERENCE_CPU_F64,saturation=1.))
    kwargs={'partitions':((0,),(1,)), 'provenance':'explicit'} if kind is LayeredSchedule else {}
    schedule=kind(EdgeTable.from_check_matrix(H),kernel=kernel,**kwargs)
    old=np.full(4,20.); syndrome=np.array([1,0],dtype=np.uint8)
    executor=CanonicalLocalStepExecutor(BudgetTree(limits=(),parents={}),scope='attempt')
    schedule.execute_local_step(executor,old,syndrome,error_rate=.2,
        progress=ScheduleProgress(iteration=0,local_steps=0,cursor=(0,)),is_converged=lambda _:False)
    assert np.max(np.abs(old))<=1.

from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import QBP4_F64_V1
from bp_registry.quaternary.problems import QuaternaryOriginalProblem

@pytest.mark.parametrize('cap', [.1,1.,5.,25.,40.])
@pytest.mark.parametrize('syndrome', [[0,0],[1,0],[1,1]])
def test_compiled_bp4_respects_active_legacy_cap(cap,syndrome):
    s=np.array(syndrome,dtype=np.uint8); code=PauliCode(checks=H)
    priors=np.tile([.97,.01,.01,.01],(3,1)); profile=replace(QBP4_F64_V1,saturation=cap)
    kernel=ScalarLlrBp4Kernel(profile=profile)
    problem=QuaternaryOriginalProblem('original-cap-regression',code,s)
    session=kernel.new_session(problem,priors)
    graph=CompiledBp4Graph.from_code(code,priors,profile=profile)
    old=graph.initial_v2c()
    for _ in range(4):
        expected=session.sweep(stop_on_convergence=False); actual=graph.sweep(old,s)
        for field in ('c2v','v2c','beliefs','marginals'):
            np.testing.assert_allclose(getattr(actual,field),getattr(expected,field),atol=2e-12,rtol=0)
        np.testing.assert_array_equal(actual.candidate,expected.candidate)
        old=actual.v2c
    for limit in (0,1,4):
        expected=kernel.new_session(problem,priors).run(max_iterations=limit)
        actual=graph.run(s,max_iterations=limit)
        np.testing.assert_array_equal(actual.candidate,expected.candidate)
        assert (actual.iterations,actual.converged)==(expected.iteration,expected.converged)
