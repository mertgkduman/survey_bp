"""Independent dense per-candidate solves: no production GF2/scoring helpers."""
from hashlib import sha256
from itertools import combinations
import copy
import math

import numpy as np
import pytest
from scipy import sparse

from bp_registry.postprocessing.osd import UniformOsd
from bp_registry.postprocessing.osd_v2 import (
    Osd, AffineBasisCache, SCORE_SOURCE, SCORE_ML, VERSION, WORK_VERSION,
)
from bp_registry.postprocessing.bp_osd_v2 import CanonicalBpOsd


def independent_candidates(h, s, llr, depth, *, full_basis=False):
    """Select pivots by forward dense elimination, solve each fresh residual.

    OSD0 stops at the first prefix spanning s. CS uses a full independent basis.
    Each candidate solves H_p*x = s + H_f*f anew; no affine reuse or packing.
    """
    order = sorted(range(h.shape[1]), key=lambda col: (llr[col], col))
    a, b = h.astype(np.int64).copy(), s.astype(np.int64).copy()
    pivots = []
    for col in order:
        rank = len(pivots)
        if rank == min(h.shape) or (depth == 0 and not full_basis and not np.any(b[rank:])):
            break
        rows = [r for r in range(rank, len(a)) if a[r, col]]
        if not rows:
            continue
        pivot = rows[0]
        a[[rank, pivot]], b[[rank, pivot]] = a[[pivot, rank]], b[[pivot, rank]]
        for row in range(rank+1, len(a)):
            if a[row, col]:
                a[row] = (a[row]+a[rank]) % 2
                b[row] = (b[row]+b[rank]) % 2
        pivots.append(col)
    if np.any(b[len(pivots):]):
        raise ValueError('inconsistent')
    free = [col for col in order if col not in pivots]
    if depth > len(free):
        raise ValueError('depth')
    patterns = [()]+([(i,) for i in range(len(free))]+list(combinations(range(depth), 2)) if depth else [])
    candidates = []
    for pattern in patterns:
        candidate = np.zeros(h.shape[1], dtype=np.uint8)
        for j in pattern:
            candidate[free[j]] = 1
        residual = (s.astype(int)+h.astype(int) @ candidate.astype(int)) % 2
        matrix = h[:, pivots].astype(int).copy()
        # Fresh Gauss-Jordan of only independent pivot columns.
        for col in range(len(pivots)):
            pivot = next(row for row in range(col, len(matrix)) if matrix[row, col])
            matrix[[col, pivot]], residual[[col, pivot]] = matrix[[pivot, col]], residual[[pivot, col]]
            for row in range(len(matrix)):
                if row != col and matrix[row, col]:
                    matrix[row] = (matrix[row]+matrix[col]) % 2
                    residual[row] = (residual[row]+residual[col]) % 2
        candidate[pivots] = residual[:len(pivots)]
        assert np.array_equal(h.astype(int) @ candidate.astype(int) % 2, s)
        candidates.append(candidate)
    return np.asarray(candidates), np.asarray(pivots), np.asarray(free)


def independent_weights(candidates, probabilities, score):
    bits = [math.log(1/float(p)) if score == SCORE_SOURCE else math.log1p(-float(p))-math.log(float(p)) for p in probabilities]
    # Original bit order and a scalar left fold, not dot/matmul/reassociation.
    output = []
    for row in candidates:
        total = 0.
        for j in range(len(bits)):
            if row[j]:
                total += bits[j]
        output.append(total)
    return np.array(output)


def manual_digest(candidates, weights):
    n = candidates.shape[1]
    padded = np.zeros((len(candidates), ((n+63)//64)*8), dtype=np.uint8)
    data = np.packbits(candidates, axis=1, bitorder='little')
    padded[:, :data.shape[1]] = data
    dtype = '<i8' if weights.dtype == np.int64 else '<f8'
    return sha256(padded.tobytes()+weights.astype(dtype).tobytes()).hexdigest()


@pytest.mark.parametrize('seed', range(16))
def test_weighted_complete_sequence_and_exact_first_winner(seed):
    rng = np.random.default_rng(seed)
    for m, n in ((1, 5), (4, 9), (9, 7), (4, 65)):
        h = rng.integers(0, 2, (m, n), dtype=np.uint8)
        s = h @ rng.integers(0, 2, n, dtype=np.uint8) % 2
        llr = rng.integers(-2, 3, n).astype(float)
        _, _, free = independent_candidates(h, s, llr, 0, full_basis=True)
        for depth in sorted({0, min(4, len(free))}):
            expected, pivots, free = independent_candidates(h, s, llr, depth)
            probabilities = rng.uniform(.001, .999, n)
            for score in (SCORE_SOURCE, SCORE_ML):
                weights = independent_weights(expected, probabilities, score)
                decoder = Osd(sparse.csc_matrix(h) if seed % 2 else h,
                              method='OSD_CS' if depth else 'OSD_0', order=depth,
                              channel_probabilities=probabilities, score=score,
                              affine_reuse=bool(seed % 2), block_size=3)
                result = decoder.decode(s, llr, evidence_mode='full', materialize_candidates=True)
                assert np.array_equal(result.candidates(), expected)
                assert np.array_equal(result.pivot_columns, pivots)
                assert np.array_equal(result.free_columns, free)
                assert np.array_equal(result.candidate_weights, weights)
                assert result.selected_index == int(np.argmin(weights))
                assert np.array_equal(result.candidate, expected[np.argmin(weights)])
                assert result.candidate_set_sha256 == manual_digest(expected, weights)


@pytest.mark.parametrize('n', [2, 63, 64, 65, 127, 128, 129, 450])
@pytest.mark.parametrize('depth', [0, 1, 10, 60])
def test_uniform_v1_exact_compatibility_word_boundaries(n, depth):
    if n < depth+4:
        pytest.skip('insufficient free columns')
    rng = np.random.default_rng(n)
    h = rng.integers(0, 2, (min(4, n-1), n), dtype=np.uint8)
    s = h @ rng.integers(0, 2, n, dtype=np.uint8) % 2
    llr = rng.integers(-2, 3, n).astype(float)
    method = 'OSD_CS' if depth else 'OSD_0'
    old = UniformOsd(h, method=method, order=depth).decode(s, llr, error_rate=.1)
    new = Osd(h, method=method, order=depth, channel_probabilities=.1).decode(s, llr, materialize_candidates=True)
    assert np.array_equal(new.candidates(), old.candidates())
    assert np.array_equal(new.candidate_weights, old.candidate_weights)
    assert new.selected_index == old.selected_index
    assert new.candidate_set_sha256 == old.candidate_set_sha256


def test_full_fast_materialization_and_chunk_sizes_preserve_digest_and_replay():
    rng = np.random.default_rng(55)
    h = rng.integers(0, 2, (5, 130), dtype=np.uint8)
    s = np.ones(5, dtype=np.uint8)
    llr = rng.normal(size=130)
    all_results = []
    for score in (SCORE_SOURCE, SCORE_ML):
        probabilities = rng.uniform(.01, .2, 130)
        for storage in ('packed', 'sparse'):
            for mode in ('fast', 'full'):
                for materialize in (True, False):
                    for chunk in (1, 17, 5000):
                        decoder = Osd(h, method='OSD_CS', order=10, channel_probabilities=probabilities,
                                      score=score, matrix_storage=storage, block_size=chunk)
                        result = decoder.decode(s, llr, evidence_mode=mode, materialize_candidates=materialize)
                        all_results.append((score, result))
                        assert result.work['original_syndrome_checks'] == (len(result.candidate_weights) if mode == 'full' else 1)
                        assert result.work['schema'] == WORK_VERSION
                        assert result.ledger['semantic']['version'] == VERSION
                        replay = decoder.replay(s, llr, result.ledger, materialize_candidates=True)
                        assert replay.candidate_set_sha256 == result.candidate_set_sha256
                        if not materialize:
                            assert result.candidates_packed is None
                            with pytest.raises(ValueError, match='streamed'):
                                result.candidates()
        assert len({r.candidate_set_sha256 for sc, r in all_results if sc == score}) == 1


def test_exact_cache_reuses_transform_for_new_syndromes_and_channel_weights():
    rng = np.random.default_rng(156)
    h = rng.integers(0, 2, (8, 70), dtype=np.uint8)
    llr = rng.integers(-2, 3, 70).astype(float)
    cache = AffineBasisCache(max_bytes=100_000, max_entries=2)
    decoder = Osd(h, method='OSD_CS', order=10, channel_probabilities=.1, cache=cache, matrix_storage='sparse')
    cold = decoder.decode(np.zeros(8, dtype=np.uint8), llr)
    assert cold.work['cache_stored'] == 1 and cold.work['cache_hit'] == 0
    for _ in range(5):
        s = h @ rng.integers(0, 2, 70, dtype=np.uint8) % 2
        warm = decoder.decode(s, llr, evidence_mode='full', materialize_candidates=True)
        expected, _, _ = independent_candidates(h, s, llr, 10)
        assert np.array_equal(warm.candidates(), expected)
        assert warm.work['cache_hit'] == 1
        assert warm.work['row_xor_words'] == warm.work['response_scan_words'] == 0
        assert warm.work['transform_apply_words'] == 8
    # Priors, syndrome and depth are deliberately absent from a matrix/order basis key.
    other = Osd(sparse.csr_matrix(h), method='OSD_CS', order=1,
                channel_probabilities=rng.uniform(.01, .3, 70), cache=cache)
    result = other.decode(s, llr, materialize_candidates=True)
    assert result.work['cache_hit'] == 1
    assert np.array_equal(result.candidates(), independent_candidates(h, s, llr, 1)[0])
    decoder.decode(s, -llr)
    assert cache.info()['misses'] == 2
    h2 = h.copy(); h2[0, 0] ^= 1
    changed = Osd(h2, method='OSD_CS', order=10, channel_probabilities=.1, cache=cache)
    changed.decode(h2 @ np.ones(70, dtype=np.uint8) % 2, llr)
    info = cache.info()
    assert info['evictions'] == 1 and info['entries'] == 2 and info['bytes'] <= 100_000


def test_cache_rejection_osd0_bypass_and_redundant_row_inconsistency():
    h = np.array([[1, 1, 0], [1, 1, 0]], dtype=np.uint8)
    llr = np.zeros(3)
    cache = AffineBasisCache(max_bytes=1)
    decoder = Osd(h, method='OSD_CS', order=1, channel_probabilities=.1, cache=cache)
    result = decoder.decode(np.zeros(2, dtype=np.uint8), llr)
    assert result.work['cache_stored'] == 0 and cache.info()['bytes'] == 0
    cache = AffineBasisCache()
    decoder = Osd(h, method='OSD_CS', order=1, channel_probabilities=.1, cache=cache)
    decoder.decode(np.zeros(2, dtype=np.uint8), llr)
    with pytest.raises(ValueError, match='inconsistent'):
        decoder.decode(np.array([1, 0], dtype=np.uint8), llr)
    decoder = Osd(h, method='OSD_0', order=0, channel_probabilities=.1, cache=cache)
    zero = decoder.decode(np.zeros(2, dtype=np.uint8), llr)
    assert len(zero.pivot_columns) == 0 and zero.work['cache_lookup'] == 0


def test_llr_ties_and_first_equal_minimum_stay_first():
    h = np.array([[1, 1, 1]], dtype=np.uint8)
    for score in (SCORE_SOURCE, SCORE_ML):
        for affine in (True, False):
            result = Osd(h, method='OSD_CS', order=2, channel_probabilities=[.1]*3,
                         score=score, affine_reuse=affine, block_size=1).decode(np.ones(1, dtype=np.uint8), [1., 1., 1.])
            assert result.ordering.tolist() == [0, 1, 2]
            assert result.selected_index == 0 and result.candidate.tolist() == [1, 0, 0]


def test_score_conventions_can_choose_different_winners_and_half_or_high_priors():
    rng = np.random.default_rng(77)
    found = False
    for _ in range(100):
        h = rng.integers(0, 2, (3, 8), dtype=np.uint8)
        s = h @ rng.integers(0, 2, 8, dtype=np.uint8) % 2
        p = rng.uniform(.01, .99, 8)
        values = [Osd(h, method='OSD_CS', order=3, channel_probabilities=p, score=score).decode(s, np.zeros(8)) for score in (SCORE_SOURCE, SCORE_ML)]
        found |= values[0].selected_index != values[1].selected_index
    assert found
    for p in (.5, .9):
        result = Osd(np.array([[1, 1, 1]], dtype=np.uint8), method='OSD_CS', order=2,
                     channel_probabilities=p, score=SCORE_ML).decode(np.ones(1, dtype=np.uint8), [0., 0., 0.])
        assert result.selected_index == (0 if p == .5 else 3)


def test_sparse_input_never_densifies_and_input_snapshots_owned(monkeypatch):
    h = sparse.csr_matrix(np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8))
    monkeypatch.setattr(sparse.csr_matrix, 'toarray', lambda *a, **kw: pytest.fail('densified'))
    p = np.array([.1, .2, .3])
    decoder = Osd(h, method='OSD_CS', order=1, channel_probabilities=p, matrix_storage='sparse')
    h.data[:] = 0; p[:] = .4
    assert decoder.packed_matrix is None and not hasattr(decoder, 'check_matrix')
    result = decoder.decode(np.array([1, 0], dtype=np.uint8), [0., 1., 2.], materialize_candidates=True)
    assert decoder.probabilities.tolist() == [.1, .2, .3]
    for value in (decoder.row_ptr, decoder.columns, decoder.probabilities, decoder.bit_weights,
                  result.candidate, result.candidates_packed, result.candidate_weights, result.ordering):
        with pytest.raises(ValueError):
            value.setflags(write=True)


def test_replay_rejects_tampering_and_changed_inputs():
    h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    decoder = Osd(h, method='OSD_CS', order=1, channel_probabilities=.1)
    s = np.array([1, 0], dtype=np.uint8); llr = np.arange(3.)
    result = decoder.decode(s, llr)
    for field in ('semantic', 'work', 'execution'):
        ledger = copy.deepcopy(result.ledger)
        ledger[field]['tampered'] = True
        with pytest.raises(ValueError, match='ledger digest'):
            decoder.replay(s, llr, ledger)
    with pytest.raises(ValueError, match='semantic replay'):
        decoder.replay(s, -llr, result.ledger)


@pytest.mark.parametrize('p', [True, 0, 1, np.nan, np.nextafter(0., 1.), [.1], [.1, np.inf], ['x', 'y'], [.1+.1j, .2]])
def test_invalid_probabilities_rejected(p):
    with pytest.raises(ValueError):
        Osd(np.eye(2, dtype=np.uint8), method='OSD_0', order=0, channel_probabilities=p)


def test_invalid_controls_and_sparse_data_rejected():
    h = np.eye(2, dtype=np.uint8)
    for kwargs in ({'method':'bad'}, {'order':True}, {'order':1}, {'matrix_storage':'bad'},
                   {'block_size':0}, {'score':'bad'}, {'cache':{}}, {'affine_reuse':1}):
        settings = dict(method='OSD_0', order=0, channel_probabilities=.1); settings.update(kwargs)
        with pytest.raises(ValueError):
            Osd(h, **settings)
    for bad in (sparse.csr_matrix([[2, 0], [0, 1]]), sparse.csr_matrix([[.5, 0], [0, 1.]])):
        with pytest.raises(ValueError, match='binary'):
            Osd(bad, method='OSD_0', order=0, channel_probabilities=.1)
    decoder = Osd(h, method='OSD_CS', order=1, channel_probabilities=.1)
    with pytest.raises(ValueError, match='non-pivot'):
        decoder.decode(np.zeros(2, dtype=np.uint8), np.zeros(2))


def test_typed_work_counts_streaming_bound_and_packing_ablation():
    h = np.array([[1, 1, 1]], dtype=np.uint8); s = np.ones(1, dtype=np.uint8)
    kwargs = dict(method='OSD_CS', order=2, channel_probabilities=.1, block_size=1)
    packed = Osd(h, **kwargs).decode(s, [0., 0., 0.], evidence_mode='full')
    w = packed.work
    assert (w['candidate_evaluations'], w['candidate_xor_words'], w['score_popcount_words']) == (4, 4, 4)
    assert (w['response_scan_words'], w['response_coefficients'], w['validation_words']) == (1, 2, 4)
    assert w['candidate_hash_bytes'] == w['weight_hash_bytes'] == 32
    assert w['candidate_materialized_bytes'] == 0 and w['candidate_block_peak_bytes'] == 16
    byte = Osd(h, **kwargs, candidate_representation='bytes', packed_scoring=False).decode(s, [0., 0., 0.])
    assert byte.work['candidate_xor_bytes'] == 12 and byte.work['byte_score_bit_tests'] == 12
    assert byte.candidate_set_sha256 == packed.candidate_set_sha256
    assert not any(value < 0 for value in packed.timings_ns.values())
    assert sum(v for k, v in packed.timings_ns.items() if k != 'total') <= packed.timings_ns['total']


def independent_bp(h, syndrome, probabilities, cap, alpha):
    rows, cols = np.nonzero(h)
    initial = np.array([math.log((1-p)/p) for p in probabilities])
    prior = np.array([math.log1p(-p)-math.log(p) for p in probabilities])
    old = initial[cols].copy()
    for iteration in range(1, cap+1):
        c2v = np.zeros(len(old)); coefficient = 1-2**(-iteration) if alpha == 'roffe' else alpha
        for edge, (row, col) in enumerate(zip(rows, cols, strict=True)):
            others = [old[j] for j, r in enumerate(rows) if r == row and j != edge]
            magnitude = min(map(abs, others)) if others else 23.7189981105
            sign = -1 if (int(syndrome[row])+sum(v < 0 for v in others)) % 2 else 1
            c2v[edge] = sign*coefficient*magnitude
        beliefs = prior.copy()
        for col, message in zip(cols, c2v, strict=True):
            beliefs[col] += message
        candidate = np.asarray(beliefs < 0, dtype=np.uint8)
        if np.array_equal(h @ candidate % 2, syndrome):
            return candidate, beliefs, True, iteration
        old = np.array([beliefs[col]-c2v[j] for j, col in enumerate(cols)])
    return candidate, beliefs, False, iteration


@pytest.mark.parametrize('alpha', ['roffe', .625])
def test_pipeline_uses_canonical_sweep_and_preserves_both_activation_paths(alpha):
    rng = np.random.default_rng(881)
    h = np.array([[1, 1, 0, 1, 0], [0, 1, 1, 0, 1], [1, 0, 1, 1, 1]], dtype=np.uint8)
    paths = set()
    for probabilities in (np.full(5, .1), np.array([.05, .2, .15, .1, .3])):
        processor = Osd(h, method='OSD_CS', order=1, channel_probabilities=probabilities)
        pipeline = CanonicalBpOsd(processor, max_iterations=2, alpha=alpha)
        for _ in range(32):
            syndrome = h @ rng.integers(0, 2, 5, dtype=np.uint8) % 2
            expected = independent_bp(h, syndrome, probabilities, 2, alpha)
            result = pipeline.decode(syndrome, evidence_mode='full', materialize_candidates=True)
            assert np.array_equal(result.bp_candidate, expected[0])
            assert np.array_equal(result.posterior_llr, expected[1])
            assert result.converged == expected[2] and result.iterations == expected[3]
            assert result.ledger['bp_directed_edge_updates'] == 2*int(h.sum())*result.iterations
            assert np.array_equal(h @ result.candidate % 2, syndrome)
            paths.add(result.osd is not None)
            if result.osd is not None:
                processor.replay(syndrome, result.posterior_llr, result.osd.ledger)
    assert paths == {True, False}
