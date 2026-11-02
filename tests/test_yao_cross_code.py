"""The X-only full-graph QBP control must preserve its known support."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1] / 'data/reproductions/yao-2312-10950-cross-code'
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('cross_common_test', ROOT/'common.py')
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)


@pytest.mark.parametrize('p', [.04, .10])
def test_full_quaternary_active_sweep_reduces_to_binary(p):
    code = common.source._code('b1')
    graphs, guard = common.bit_flip_graphs(code, p)
    q, b = graphs['qbp_v2'], graphs['binary_v2']
    truth = common.sample(20261102, code, p, 17)
    s = common.vanilla._original_syndrome(common.vanilla._syndrome_evaluator(code), truth)
    qo = q.initial_v2c()
    bo = np.full(b.table.edge_count, np.log((1-p)/p))
    zstart = q.row_ptr[code.hx.shape[0]]
    for _ in range(10):
        qs = q.sweep(qo, s)
        bs = b.sweep(bo, s[code.hx.shape[0]:], error_rate=p)
        np.testing.assert_allclose(qs.c2v[zstart:], bs.check_to_variable, atol=1e-11)
        np.testing.assert_allclose(qs.beliefs[:, 0], bs.beliefs, atol=1e-11)
        assert np.all(qs.beliefs[:, 1:] > 1024)
        assert np.all(qs.marginals[:, 2:] == 0)
        assert np.all(qs.candidate <= 1)
        qo, bo = qs.v2c, bs.new_v2c
    assert guard > 1024


def test_logical_x_and_z_signatures_cannot_cancel():
    spec = importlib.util.spec_from_file_location('cross_assessment_test', ROOT/'assess.py')
    assessment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assessment)
    code = common.source._code('a5')
    zero = np.zeros(code.n, dtype=np.uint8)
    logical_y = common.vanilla.BITS_TO_PAULI[code.lx[0], code.lz[0]]
    masks = common.vanilla._logical_masks(code)
    assert common.vanilla._logical_signature(logical_y, masks) == 0
    assert assessment.signature_pair(code, logical_y) != assessment.signature_pair(code, zero)
