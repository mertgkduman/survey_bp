"""Independent GF2 oracle, candidate coverage and strict standalone OSD inputs."""
from itertools import combinations, product
import numpy as np
import pytest

from bp_registry.postprocessing.osd import UniformOsd, _popcount


def oracle(h, syndrome, llr, depth):
    """Dense independent column-permuted Gauss-Jordan; no production helpers."""
    order = np.lexsort((np.arange(h.shape[1]), llr))
    a = h[:, order].astype(np.int64).copy(); b = syndrome.astype(np.int64).copy()
    pivots = []; row = 0
    for col in range(a.shape[1]):
        candidates = np.flatnonzero(a[row:, col])
        if not len(candidates):
            continue
        pivot = row+int(candidates[0]); a[[row, pivot]] = a[[pivot, row]]; b[[row, pivot]] = b[[pivot, row]]
        for other in range(len(a)):
            if other != row and a[other, col]:
                a[other] = (a[other]+a[row]) % 2; b[other] = (b[other]+b[row]) % 2
        pivots.append(col); row += 1
        if row == len(a):
            break
    if np.any(b[row:]):
        raise ValueError('inconsistent')
    free = [i for i in range(a.shape[1]) if i not in pivots]
    patterns = [()]
    if depth:
        patterns += [(j,) for j in range(len(free))] + list(combinations(range(depth), 2))
    output = []
    for pattern in patterns:
        candidate = np.zeros(a.shape[1], dtype=np.uint8)
        for index in pattern:
            candidate[free[index]] = 1
        for r, col in enumerate(pivots):
            candidate[col] = (b[r]+a[r] @ candidate) % 2
        original = np.empty_like(candidate); original[order] = candidate
        output.append(original)
    return np.array(output), len(free)


@pytest.mark.parametrize('seed', range(12))
def test_complete_candidate_sets_match_dense_independent_oracle(seed):
    rng = np.random.default_rng(seed)
    for m, n in ((1, 4), (3, 7), (6, 8), (8, 6)):
        h = rng.integers(0, 2, (m, n), dtype=np.uint8)
        truth = rng.integers(0, 2, n, dtype=np.uint8); s = (h @ truth) % 2
        llr = rng.integers(-2, 3, n).astype(float)
        _, free = oracle(h, s, llr, 0)
        for depth in (0, min(3, free)):
            expected, _ = oracle(h, s, llr, depth)
            result = UniformOsd(h, method='OSD_CS' if depth else 'OSD_0', order=depth).decode(s, llr, error_rate=.1)
            actual = result.candidates()
            assert np.array_equal(actual, expected)
            assert np.all((h.astype(int) @ actual.T) % 2 == s[:, None])
            weights = expected.sum(axis=1)
            assert np.array_equal(result.candidate, expected[np.argmin(weights)])
            assert np.array_equal(result.candidate_weights, weights)
            assert result.work['candidate_evaluations'] == len(expected)
            assert len(result.candidate_set_sha256) == 64
            if free <= 2 and depth == free:
                exact = [v for v in product((0, 1), repeat=n) if np.array_equal((h @ v) % 2, s)]
                assert int(result.candidate.sum()) == min(sum(v) for v in exact)


@pytest.mark.parametrize('n', [63, 64, 65, 127, 128, 129, 450])
def test_packed_boundaries_and_padding_preserve_original_syndrome(n):
    rng = np.random.default_rng(n)
    h = rng.integers(0, 2, (5, n), dtype=np.uint8); truth = rng.integers(0, 2, n, dtype=np.uint8)
    s = h @ truth % 2; llr = rng.normal(size=n)
    expected, _ = oracle(h, s, llr, 4)
    result = UniformOsd(h, method='OSD_CS', order=4).decode(s, llr, error_rate=.2)
    assert np.array_equal(result.candidates(), expected)
    assert result.candidates_packed.shape[1] == (n+63)//64


def test_popcount_matches_python_at_extremes_and_random_words():
    rng = np.random.default_rng(281)
    words = [0, 1, 2**63, 2**64-1, *map(int, rng.integers(0, 2**64-1, 100, dtype=np.uint64))]
    assert all(_popcount(np.uint64(w)) == w.bit_count() for w in words)


def test_signed_reliability_original_id_ties_and_first_minimum_are_explicit():
    h = np.array([[1, 1]], dtype=np.uint8); s = np.array([1], dtype=np.uint8)
    decoder = UniformOsd(h, method='OSD_0', order=0)
    assert decoder.decode(s, [-.5, .1], error_rate=.1).candidate.tolist() == [1, 0]
    assert decoder.decode(s, [1., 1.], error_rate=.1).ordering.tolist() == [0, 1]
    result = UniformOsd(h, method='OSD_CS', order=1).decode(s, [1., 1.], error_rate=.1)
    assert result.candidate.tolist() == [1, 0] and result.selected_index == 0


def test_inputs_owned_and_returned_candidates_are_immutable_and_replayable():
    h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    decoder = UniformOsd(h, method='OSD_CS', order=1); h[:] = 0
    a = decoder.decode(np.array([1, 0], dtype=np.uint8), [1., -2., 3.], error_rate=.1)
    b = decoder.decode(np.array([1, 0], dtype=np.uint8), [1., -2., 3.], error_rate=.1)
    assert a.candidate_set_sha256 == b.candidate_set_sha256 and a.work == b.work
    for array in (decoder.check_matrix, decoder.packed_matrix, a.candidate, a.candidates_packed, a.candidate_weights):
        with pytest.raises(ValueError):
            array.setflags(write=True)


def test_zero_redundant_and_inconsistent_syndromes():
    h = np.array([[1, 1, 0], [1, 1, 0]], dtype=np.uint8)
    for method, depth in [('OSD_0', 0), ('OSD_CS', 2)]:
        decoder = UniformOsd(h, method=method, order=depth)
        assert not np.any(decoder.decode(np.zeros(2, dtype=np.uint8), [1., 2., 3.], error_rate=.1).candidate)
        with pytest.raises(ValueError, match='inconsistent syndrome'):
            decoder.decode(np.array([1, 0], dtype=np.uint8), [1., 2., 3.], error_rate=.1)


@pytest.mark.parametrize('method,order', [('OSD_0', 1), ('OSD_CS', 0), ('OSD_CS', True), ('bad', 0), ('OSD_CS', -1)])
def test_implicit_or_invalid_controls_rejected(method, order):
    with pytest.raises(ValueError):
        UniformOsd(np.eye(2, dtype=np.uint8), method=method, order=order)


def test_malformed_unqualified_shapes_and_nonuniform_channels_rejected():
    decoder = UniformOsd(np.eye(2, dtype=np.uint8), method='OSD_0', order=0)
    s = np.ones(2, dtype=np.uint8)
    for p in (0, .5, float('nan'), True, np.array([.1, .2])):
        with pytest.raises(ValueError):
            decoder.decode(s, [0., 1.], error_rate=p)
    for llr in ([float('inf'), 1.], [1.]):
        with pytest.raises(ValueError):
            decoder.decode(s, llr, error_rate=.1)
    with pytest.raises(ValueError, match='non-pivot count'):
        UniformOsd(np.eye(2, dtype=np.uint8), method='OSD_CS', order=1).decode(s, [0., 1.], error_rate=.1)
