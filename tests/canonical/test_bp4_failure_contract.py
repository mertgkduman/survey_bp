"""BP4 finite-state and parallel failure contracts from C01."""
from dataclasses import replace
import numpy as np
import pytest
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
from bp_registry.resolution import STABLE_SPA_F64, ResolutionPolicy
from numba import get_num_threads

@pytest.mark.parametrize('scope',['scalar_edges','all_messages','all_state'])
def test_bp4_overflow_rejected_across_sweep_single_and_batch(scope):
    policy=replace(STABLE_SPA_F64,damping=0.,zero_syndrome_shortcut=False,resolution=ResolutionPolicy('float64',scope=scope))
    graph=CompiledBp4Graph.from_code(PauliCode(checks=np.ones((3,2),dtype=np.uint8)),np.tile([.7,.1,.1,.1],(2,1)),policy=policy)
    graph=replace(graph,prior_llrs=np.full((2,3),1e308));syndrome=np.ones(3,dtype=np.uint8)
    old=graph.initial_v2c();snapshot=old.copy();prior=graph.prior_llrs.copy();threads=get_num_threads()
    with pytest.raises(ValueError,match='nonfinite'):
        graph.sweep(old,syndrome)
    with pytest.raises(ValueError,match='nonfinite'):
        graph.run(syndrome,max_iterations=1)
    for workers in (1,2):
        with pytest.raises(ValueError,match='BP4.*failed'):
            graph.run_batch(np.array([syndrome,syndrome]),max_iterations=1,workers=workers)
        assert get_num_threads()==threads
    np.testing.assert_array_equal(old,snapshot)
    np.testing.assert_array_equal(graph.prior_llrs,prior)


def test_bp4_batch_failure_has_no_partial_result_or_ledger(tmp_path):
    policy=replace(STABLE_SPA_F64,damping=0.,resolution=ResolutionPolicy('float64',scope='scalar_edges'))
    graph=CompiledBp4Graph.from_code(PauliCode(checks=np.ones((3,2),dtype=np.uint8)),np.tile([.7,.1,.1,.1],(2,1)),policy=policy)
    graph=replace(graph,prior_llrs=np.full((2,3),1e308))
    # First row converges initially; only the second row overflows.
    path=tmp_path/'events.jsonl';path.write_text('retained ledger\n')
    with pytest.raises(ValueError,match=r'indices \[1\]'):
        graph.run_batch(np.array([[0,0,0],[1,1,1]],dtype=np.uint8),max_iterations=1,workers=2).write_ledger(path)
    assert path.read_text()=='retained ledger\n'

@pytest.mark.parametrize('bad',[np.nan,np.inf,-np.inf])
def test_marginal_normalization_rejects_nonfinite_beliefs(bad):
    from bp_registry.quaternary.compiled import _normalize_marginals
    with pytest.raises(ValueError,match='nonfinite'):
        _normalize_marginals(np.array([[0.,bad,1.]]),np.empty((1,4)))


def test_marginal_normalization_allows_underflow_for_extreme_finite_beliefs():
    from bp_registry.quaternary.compiled import _normalize_marginals
    out=np.empty((1,4))
    _normalize_marginals(np.array([[1e308,-1e308,0.]]),out)
    np.testing.assert_array_equal(out,[[0,0,1,0]])
