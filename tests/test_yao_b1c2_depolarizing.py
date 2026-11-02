"""Depolarizing priors and independent logical outcome semantics."""
import importlib.util
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]/'data/reproductions/yao-2312-10950-cross-code/depolarizing'
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('depolarizing_test_study',ROOT/'study.py')
study=importlib.util.module_from_spec(spec);sys.modules[spec.name]=study;spec.loader.exec_module(study)


def test_joint_and_marginal_priors_match_depolarizing_channel():
    code=study.source._code('b1');p=.06
    graphs=study.graphs(code,p)
    np.testing.assert_allclose(graphs['qbp_v2'].prior_llrs,np.log(3*(1-p)/p))
    for bound in graphs['binary_v2']:
        assert abs(bound.prior-np.log((1-2*p/3)/(2*p/3)))<1e-14
    assert graphs['qbp_v2'].profile.v2c_damping==0
    assert graphs['qbp_v2'].profile.check_cap is None


def test_independent_evaluator_distinguishes_logical_y_and_stabilizer():
    code=study.source._code('b1');ev=study.vanilla._syndrome_evaluator(code)
    zero=np.zeros(code.n,dtype=np.uint8)
    logical_y=study.vanilla.BITS_TO_PAULI[code.lx[0],code.lz[0]]
    s=study.vanilla._original_syndrome(ev,logical_y)
    assert not np.any(s)
    flags=study.outcome(code,ev,logical_y,s,zero)
    assert flags['type_ii'] and not flags['stabilizer_success']
    stabilizer=code.hx[0].astype(np.uint8)
    flags=study.outcome(code,ev,stabilizer,study.vanilla._original_syndrome(ev,stabilizer),zero)
    assert flags['stabilizer_success'] and not flags['type_ii']


def test_sparse_independent_syndrome_matches_original_pauli_algebra():
    spec=importlib.util.spec_from_file_location('depolarizing_test_assessment',ROOT/'assess.py')
    assessment=importlib.util.module_from_spec(spec);sys.modules[spec.name]=assessment;spec.loader.exec_module(assessment)
    code=study.source._code('b1');sparse=assessment.evaluator(code)
    dense=study.vanilla._syndrome_evaluator(code)
    rng=np.random.default_rng(41)
    for _ in range(20):
        pauli=rng.integers(0,4,size=code.n,dtype=np.uint8)
        np.testing.assert_array_equal(assessment.independent_syndrome(pauli,*sparse),
                                      study.vanilla._original_syndrome(dense,pauli))
