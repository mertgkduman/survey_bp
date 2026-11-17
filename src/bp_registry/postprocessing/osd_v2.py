"""Versioned weighted OSD-CS; frozen uniform-osd-packed-v1 is unchanged.

Source algorithm: quantumgizmos/ldpc d3429964/src_cpp/osd.hpp (MIT).
See docs/osd-v2.md for score, enumeration, evidence and work contracts.
No decoder policy receives simulation truth. Numba fastmath is deliberately off.
"""
from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
import json
from threading import RLock
from time import perf_counter_ns

from numba import njit
import numpy as np
from scipy import sparse

from bp_registry.compiled_contracts import immutable_snapshot
from bp_registry.postprocessing.osd import _popcount, _binary

VERSION = 'weighted-streaming-osd-v2'
WORK_VERSION = 'osd-work-v2'
EVIDENCE_VERSION = 'osd-evidence-v2'
SCORE_SOURCE = 'source_log_inverse_p'
SCORE_ML = 'bernoulli_log_odds'
COUNTERS = (
    'pivot_bit_tests', 'row_xor_words', 'syndrome_row_xors',
    'row_swap_words', 'transform_xor_words', 'transform_swap_words',
    'back_substitution_words', 'response_scan_words', 'response_coefficients',
    'response_pivot_bit_tests', 'candidate_xor_words', 'score_popcount_words',
    'score_bit_tests', 'score_additions', 'validation_words', 'validation_edges',
    'transform_apply_words',
)


def _digest(array, dtype):
    return sha256(np.ascontiguousarray(array, dtype=dtype).view(np.uint8)).hexdigest()


def _json_digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@njit(cache=True)
def _pack_csr(row_ptr, columns, n):
    result = np.zeros((len(row_ptr)-1, (n+63)//64), dtype=np.uint64)
    for row in range(len(row_ptr)-1):
        for edge in range(row_ptr[row], row_ptr[row+1]):
            col = columns[edge]
            result[row, col//64] |= np.uint64(1) << np.uint64(col % 64)
    return result


@njit(cache=True)
def _factor(matrix, syndrome, ordering, n, cs, affine, track_transform, counters):
    m, width = matrix.shape
    a, b = matrix.copy(), syndrome.copy()
    transform = np.zeros((m if track_transform else 0, (m+63)//64 if track_transform else 0), dtype=np.uint64)
    if track_transform:
        for i in range(m):
            transform[i, i//64] = np.uint64(1) << np.uint64(i % 64)
    pivots = np.empty(min(m, n), dtype=np.int64)
    flags = np.zeros(n, dtype=np.uint8)
    rank = 0
    for col in ordering:
        if rank == min(m, n) or (not cs and not np.any(b[rank:])):
            break
        word, mask = col//64, np.uint64(1) << np.uint64(col % 64)
        pivot = -1
        for row in range(rank, m):
            counters[0] += 1
            if a[row, word] & mask:
                pivot = row
                break
        if pivot < 0:
            continue
        if pivot != rank:
            for w in range(width):
                a[pivot, w], a[rank, w] = a[rank, w], a[pivot, w]
            b[pivot], b[rank] = b[rank], b[pivot]
            counters[3] += width
            for w in range(transform.shape[1]):
                transform[pivot, w], transform[rank, w] = transform[rank, w], transform[pivot, w]
                counters[5] += 1
        pivots[rank], flags[col] = col, 1
        for row in range(rank+1, m):
            counters[0] += 1
            if a[row, word] & mask:
                for w in range(width):
                    a[row, w] ^= a[rank, w]
                counters[1] += width
                b[row] ^= b[rank]
                counters[2] += 1
                for w in range(transform.shape[1]):
                    transform[row, w] ^= transform[rank, w]
                counters[4] += transform.shape[1]
        rank += 1
    if cs and affine:
        for i in range(rank-1, -1, -1):
            col = pivots[i]
            word, mask = col//64, np.uint64(1) << np.uint64(col % 64)
            for row in range(i):
                counters[0] += 1
                if a[row, word] & mask:
                    for w in range(width):
                        a[row, w] ^= a[i, w]
                    counters[1] += width
                    b[row] ^= b[i]
                    counters[2] += 1
                    for w in range(transform.shape[1]):
                        transform[row, w] ^= transform[i, w]
                    counters[4] += transform.shape[1]
    free = np.empty(n-rank, dtype=np.int64)
    j = 0
    for col in ordering:
        if not flags[col]:
            free[j] = col
            j += 1
    return a, b, pivots[:rank], free, transform


@njit(cache=True)
def _transform_syndrome(transform, syndrome, counters):
    packed = np.zeros((len(syndrome)+63)//64, dtype=np.uint64)
    for i in range(len(syndrome)):
        if syndrome[i]:
            packed[i//64] |= np.uint64(1) << np.uint64(i % 64)
    b = np.zeros(len(syndrome), dtype=np.uint8)
    for row in range(len(b)):
        for w in range(len(packed)):
            b[row] ^= _popcount(transform[row, w] & packed[w]) & 1
            counters[16] += 1
    return b


@njit(cache=True)
def _responses(a, pivots, free, n, scan, counters):
    directions = np.zeros((len(free), a.shape[1]), dtype=np.uint64)
    lookup = np.full(n, -1, dtype=np.int64)
    for j in range(len(free)):
        col = free[j]
        lookup[col] = j
        directions[j, col//64] = np.uint64(1) << np.uint64(col % 64)
    for row in range(len(pivots)):
        pivot = pivots[row]
        if scan:
            for j in range(len(free)):
                col = free[j]
                counters[9] += 1
                if a[row, col//64] & (np.uint64(1) << np.uint64(col % 64)):
                    directions[j, pivot//64] ^= np.uint64(1) << np.uint64(pivot % 64)
                    counters[8] += 1
        else:
            for w in range(a.shape[1]):
                remaining = a[row, w]
                counters[7] += 1
                while remaining:
                    low = remaining & (np.uint64(0)-remaining)
                    col = w*64+_popcount(low-np.uint64(1))
                    j = lookup[col]
                    if j >= 0:
                        directions[j, pivot//64] ^= np.uint64(1) << np.uint64(pivot % 64)
                        counters[8] += 1
                    remaining ^= low
    return directions


@njit(cache=True)
def _base(a, b, pivots, triangular, counters):
    result = np.zeros(a.shape[1], dtype=np.uint64)
    for row in range(len(pivots)-1, -1, -1):
        value = int(b[row])
        if triangular:
            for w in range(a.shape[1]):
                value ^= _popcount(a[row, w] & result[w]) & 1
            counters[6] += a.shape[1]
        if value:
            col = pivots[row]
            result[col//64] |= np.uint64(1) << np.uint64(col % 64)
    return result


@njit(cache=True)
def _block(start, stop, base, directions, a, b, pivots, free, depth,
           affine, uniform, bit_weights, n, packed_scoring, counters):
    width, q = len(base), len(free)
    values = np.zeros((stop-start, width), dtype=np.uint64)
    scores = np.zeros(stop-start, dtype=np.float64)
    for index in range(start, stop):
        first, second = -1, -1
        if 0 < index <= q:
            first = index-1
        elif index > q:
            offset, first = index-q-1, 0
            while offset >= depth-first-1:
                offset -= depth-first-1
                first += 1
            second = first+1+offset
        candidate = values[index-start]
        if affine:
            for w in range(width):
                candidate[w] = base[w]
                if first >= 0:
                    candidate[w] ^= directions[first, w]
                if second >= 0:
                    candidate[w] ^= directions[second, w]
            counters[10] += width*(int(first >= 0)+int(second >= 0))
        elif index == 0:
            candidate[:] = base
        else:
            for j in (first, second):
                if j >= 0:
                    col = free[j]
                    candidate[col//64] |= np.uint64(1) << np.uint64(col % 64)
            for row in range(len(pivots)-1, -1, -1):
                value = int(b[row])
                for w in range(width):
                    value ^= _popcount(a[row, w] & candidate[w]) & 1
                counters[6] += width
                if value:
                    col = pivots[row]
                    candidate[col//64] |= np.uint64(1) << np.uint64(col % 64)
        if packed_scoring and uniform:
            for w in range(width):
                scores[index-start] += _popcount(candidate[w])
            counters[11] += width
        elif packed_scoring:
            # Visit set bits in original-column order: exactly the reference's
            # accumulation order, including negative weights in ML mode.
            for w in range(width):
                remaining = candidate[w]
                while remaining:
                    low = remaining & (np.uint64(0)-remaining)
                    col = w*64+_popcount(low-np.uint64(1))
                    scores[index-start] += bit_weights[col]
                    counters[13] += 1
                    remaining ^= low
        else:
            for col in range(n):
                counters[12] += 1
                if candidate[col//64] & (np.uint64(1) << np.uint64(col % 64)):
                    scores[index-start] += 1.0 if uniform else bit_weights[col]
                    counters[13] += 1
    return values, scores


@njit(cache=True)
def _byte_block(start, stop, base, directions, q, depth, uniform, bit_weights, counters):
    """Candidate-storage ablation: one byte/bit XOR, same affine sequence."""
    values = np.empty((stop-start, len(base)), dtype=np.uint8)
    scores = np.zeros(stop-start, dtype=np.float64)
    for index in range(start, stop):
        first, second = -1, -1
        if 0 < index <= q:
            first = index-1
        elif index > q:
            offset, first = index-q-1, 0
            while offset >= depth-first-1:
                offset -= depth-first-1
                first += 1
            second = first+1+offset
        for col in range(len(base)):
            bit = base[col]
            if first >= 0:
                bit ^= directions[first, col]
                counters[0] += 1
            if second >= 0:
                bit ^= directions[second, col]
                counters[0] += 1
            values[index-start, col] = bit
            counters[1] += 1
            if bit:
                scores[index-start] += 1.0 if uniform else bit_weights[col]
                counters[2] += 1
    return values, scores


@njit(cache=True)
def _check_candidates(packed_h, row_ptr, columns, values, syndrome, use_sparse, counters):
    for i in range(len(values)):
        for row in range(len(syndrome)):
            parity = 0
            if use_sparse:
                for edge in range(row_ptr[row], row_ptr[row+1]):
                    col = columns[edge]
                    parity ^= int((values[i, col//64] >> np.uint64(col % 64)) & np.uint64(1))
                counters[15] += row_ptr[row+1]-row_ptr[row]
            else:
                for w in range(packed_h.shape[1]):
                    parity ^= _popcount(packed_h[row, w] & values[i, w]) & 1
                counters[14] += packed_h.shape[1]
            if parity != syndrome[row]:
                return False
    return True


class AffineBasisCache:
    """Thread-safe bounded LRU, exact matrix bytes AND exact stable column order.

    Budget counts retained ndarray payloads plus key bytes; Python/container
    overhead is bounded by max_entries and measured separately by benchmarks.
    """

    def __init__(self, *, max_bytes=16*1024*1024, max_entries=8):
        if type(max_bytes) is not int or max_bytes < 0 or type(max_entries) is not int or max_entries < 0:
            raise ValueError('cache bounds must be nonnegative integers')
        self.max_bytes, self.max_entries = max_bytes, max_entries
        self.bytes = self.hits = self.misses = self.evictions = 0
        self._entries, self._lock = OrderedDict(), RLock()

    def get(self, key):
        with self._lock:
            value = self._entries.get(key)
            if value is None:
                self.misses += 1
                return None
            self.hits += 1
            self._entries.move_to_end(key)
            return value[0]

    def put(self, key, basis):
        size = sum(len(k) for k in key)+sum(v.nbytes for v in basis)
        with self._lock:
            if size > self.max_bytes or self.max_entries == 0:
                return False
            owned = tuple(immutable_snapshot(v) for v in basis)
            old = self._entries.pop(key, None)
            if old is not None:
                self.bytes -= old[1]
            while self._entries and (self.bytes+size > self.max_bytes or len(self._entries) >= self.max_entries):
                _, (_, removed) = self._entries.popitem(last=False)
                self.bytes -= removed
                self.evictions += 1
            self._entries[key] = (owned, size)
            self.bytes += size
            return True

    def info(self):
        with self._lock:
            return dict(entries=len(self._entries), bytes=self.bytes, hits=self.hits,
                        misses=self.misses, evictions=self.evictions,
                        max_bytes=self.max_bytes, max_entries=self.max_entries)


@dataclass(frozen=True)
class OsdResult:
    candidate: np.ndarray
    candidates_packed: np.ndarray | None
    candidate_weights: np.ndarray
    ordering: np.ndarray
    pivot_columns: np.ndarray
    free_columns: np.ndarray
    selected_index: int
    method: str
    order: int
    work: dict
    timings_ns: dict
    candidate_set_sha256: str
    ledger: dict

    def candidates(self):
        if self.candidates_packed is None:
            raise ValueError('candidates were streamed; replay with materialize_candidates=True')
        raw = np.ascontiguousarray(self.candidates_packed, dtype='<u8').view(np.uint8)
        return np.unpackbits(raw.reshape(len(raw), -1), axis=1, bitorder='little')[:, :len(self.candidate)]


class Osd:
    """Fixed-matrix OSD with cached per-bit priors, explicit scoring/evidence.

    The uniform positive-channel fast path retains integer Hamming scores and
    the v1 candidate-byte-then-int64-weight digest exactly. Nonuniform scores
    use float64; source and Bernoulli-ML conventions are separately identified.
    """

    def __init__(self, check_matrix, *, method, order, channel_probabilities,
                 score=SCORE_SOURCE, matrix_storage='auto', cache=None,
                 affine_reuse=True, response_method='set_bits', packed_scoring=True,
                 block_size=512, candidate_representation='packed'):
        started = perf_counter_ns()
        if method not in ('OSD_0', 'OSD_CS') or type(order) is not int or order < 0:
            raise ValueError('explicit OSD_0/OSD_CS method and integer order required')
        if (method == 'OSD_0' and order != 0) or (method == 'OSD_CS' and order < 1):
            raise ValueError('OSD_0 requires order0; OSD_CS requires positive depth')
        if matrix_storage not in ('auto', 'sparse', 'packed') or response_method not in ('set_bits', 'scan'):
            raise ValueError('invalid storage/response method')
        if type(block_size) is not int or block_size < 1:
            raise ValueError('positive integer block_size required')
        if type(affine_reuse) is not bool or type(packed_scoring) is not bool:
            raise ValueError('ablation switches must be bool')
        if candidate_representation not in ('packed', 'bytes'):
            raise ValueError('unknown candidate representation')
        if candidate_representation == 'bytes' and (not affine_reuse or packed_scoring):
            raise ValueError('byte ablation requires affine reuse and bitwise scoring')
        if cache is not None and not isinstance(cache, AffineBasisCache):
            raise ValueError('cache must be an AffineBasisCache')
        if score not in (SCORE_SOURCE, SCORE_ML):
            raise ValueError('unknown channel score convention')
        if sparse.issparse(check_matrix):
            csr = check_matrix.tocsr(copy=True)
            # Duplicates must describe a binary matrix after canonicalization;
            # silently interpreting nonbinary multiplicities mod2 is unsafe.
            csr.sum_duplicates()
            csr.eliminate_zeros()
            csr.sort_indices()
            if not (np.issubdtype(csr.dtype, np.integer) or csr.dtype == np.bool_) or np.any(csr.data != 1):
                raise ValueError('sparse check matrix must be binary with no nonbinary duplicate sums')
            m, n = csr.shape
            ptr, cols = csr.indptr, csr.indices
        else:
            h = _binary(check_matrix, ndim=2, name='check matrix')
            m, n = h.shape
            rows, cols = np.nonzero(h)
            ptr = np.r_[0, np.cumsum(np.bincount(rows, minlength=m))]
        if m == 0 or n == 0 or order > n:
            raise ValueError('nonempty matrix and depth <= column count required')
        self.n, self.m = int(n), int(m)
        ptr = np.asarray(ptr, dtype=np.int64)
        cols = np.asarray(cols, dtype=np.int64)
        self.matrix_key = (np.array([m, n], dtype='<i8').tobytes()+ptr.astype('<i8').tobytes()+cols.astype('<i8').tobytes())
        self.matrix_sha256 = sha256(self.matrix_key).hexdigest()
        self.nnz, self.width = len(cols), (n+63)//64
        csr_bytes, packed_bytes = ptr.nbytes+cols.nbytes, m*self.width*8
        self.matrix_storage = ('sparse' if csr_bytes < packed_bytes else 'packed') if matrix_storage == 'auto' else matrix_storage
        # The exact-key byte string owns CSR structure for replay/cache identity;
        # ndarray views share those bytes. No second dense H or duplicate CSR.
        self.row_ptr = np.frombuffer(self.matrix_key, dtype='<i8', count=m+1, offset=16)
        self.columns = np.frombuffer(self.matrix_key, dtype='<i8', count=len(cols), offset=16+8*(m+1))
        self.packed_matrix = immutable_snapshot(_pack_csr(ptr, cols, n)) if self.matrix_storage == 'packed' else None
        probabilities = np.asarray(channel_probabilities)
        if probabilities.dtype == np.bool_ or not np.issubdtype(probabilities.dtype, np.number) or np.iscomplexobj(probabilities):
            raise ValueError('finite per-bit probabilities required')
        probabilities = np.asarray(probabilities, dtype=np.float64)
        if probabilities.ndim == 0:
            probabilities = np.full(n, float(probabilities))
        if probabilities.shape != (n,) or not np.all(np.isfinite(probabilities)) or np.any((probabilities <= 0) | (probabilities >= 1)):
            raise ValueError('original channel probabilities must lie in (0,1) with one per bit')
        self.probabilities = immutable_snapshot(probabilities)
        # Scalar math calls match independent/native log operations; no exp/log
        # recomputation in the decode hot path. Source evaluates log(1/p).
        import math
        weights = np.array([math.log(1/float(p)) if score == SCORE_SOURCE else math.log1p(-float(p))-math.log(float(p)) for p in probabilities])
        if not np.all(np.isfinite(weights)):
            raise ValueError('channel score overflows float64 under the selected convention')
        self.bit_weights = immutable_snapshot(weights)
        self.uniform = bool(np.all(probabilities == probabilities[0]) and weights[0] > 0)
        self.score = score
        self.channel_sha256 = _digest(probabilities, '<f8')
        self.method, self.order, self.cache = method, order, cache
        self.affine_reuse, self.response_method = affine_reuse, response_method
        self.packed_scoring, self.block_size = packed_scoring, block_size
        self.candidate_representation = candidate_representation
        self.constructor_ns = perf_counter_ns()-started

    @property
    def retained_matrix_bytes(self):
        return len(self.matrix_key)+(0 if self.packed_matrix is None else self.packed_matrix.nbytes)

    def decode(self, syndrome, posterior_llr, *, evidence_mode='fast', materialize_candidates=False):
        started = perf_counter_ns()
        if evidence_mode not in ('fast', 'full') or type(materialize_candidates) is not bool:
            raise ValueError('explicit fast/full evidence mode and boolean materialization required')
        s = _binary(syndrome, ndim=1, name='syndrome')
        if np.iscomplexobj(posterior_llr):
            raise ValueError('posterior must be real signed LLRs')
        llr = np.asarray(posterior_llr, dtype=np.float64)
        if s.shape != (self.m,) or llr.shape != (self.n,) or not np.all(np.isfinite(llr)):
            raise ValueError('syndrome/finite signed posterior shape mismatch')
        timing = {'inputs': perf_counter_ns()-started}
        tick = perf_counter_ns()
        ordering = np.argsort(llr, kind='stable').astype(np.int64)
        timing['sort'] = perf_counter_ns()-tick
        counters = np.zeros(len(COUNTERS), dtype=np.int64)
        cs = self.method == 'OSD_CS'
        affine = cs and self.affine_reuse
        tick = perf_counter_ns()
        key = (self.matrix_key, ordering.astype('<i8', copy=False).tobytes()) if affine and self.cache is not None else None
        cached = self.cache.get(key) if key is not None else None
        timing['cache_lookup'] = perf_counter_ns()-tick
        tick = perf_counter_ns()
        packed_h = self.packed_matrix
        if packed_h is None and cached is None:
            packed_h = _pack_csr(self.row_ptr, self.columns, self.n)
        timing['pack_matrix'] = perf_counter_ns()-tick
        tick = perf_counter_ns()
        if cached is None:
            a, b, pivots, free, transform = _factor(packed_h, s, ordering, self.n, cs, affine, key is not None, counters)
        else:
            a, transform, pivots, free, directions = cached
            b = _transform_syndrome(transform, s, counters)
        timing['factor_or_transform'] = perf_counter_ns()-tick
        if np.any(b[len(pivots):]):
            raise ValueError('inconsistent syndrome')
        if cs and self.order > len(free):
            raise ValueError('OSD search depth exceeds non-pivot count')
        tick = perf_counter_ns()
        if cached is None:
            directions = _responses(a, pivots, free, self.n, self.response_method == 'scan', counters) if affine else np.empty((0, self.width), dtype=np.uint64)
        cache_stored = False
        if key is not None and cached is None:
            cache_stored = self.cache.put(key, (a, transform, pivots, free, directions))
        timing['responses_and_cache_store'] = perf_counter_ns()-tick
        tick = perf_counter_ns()
        base = _base(a, b, pivots, not affine, counters)
        byte_counters = np.zeros(3, dtype=np.int64)
        if self.candidate_representation == 'bytes':
            byte_base = np.unpackbits(np.ascontiguousarray(base, dtype='<u8').view(np.uint8), bitorder='little')[:self.n]
            byte_directions = np.unpackbits(np.ascontiguousarray(directions, dtype='<u8').view(np.uint8).reshape(len(directions), self.width*8), axis=1, bitorder='little')[:, :self.n]
        timing['base_solution'] = perf_counter_ns()-tick
        count = 1+(len(free)+self.order*(self.order-1)//2 if cs else 0)
        weights = np.empty(count, dtype=np.int64 if self.uniform else np.float64)
        materialized = np.empty((count, self.width), dtype=np.uint64) if materialize_candidates else None
        candidate_digest, selected, best = sha256(), base.copy(), -1
        timing.update(enumerate_score=0, candidate_validation=0, candidate_hash=0)
        checks, block_peak = 0, 0
        for start in range(0, count, self.block_size):
            stop = min(count, start+self.block_size)
            tick = perf_counter_ns()
            extra_bytes = 0
            if self.candidate_representation == 'bytes':
                byte_block, scores = _byte_block(start, stop, byte_base, byte_directions,
                                                len(free), self.order, self.uniform, self.bit_weights, byte_counters)
                packed_bytes = np.packbits(byte_block, axis=1, bitorder='little')
                padded = np.zeros((stop-start, self.width*8), dtype=np.uint8)
                padded[:, :packed_bytes.shape[1]] = packed_bytes
                block = padded.view('<u8')
                extra_bytes = byte_block.nbytes+packed_bytes.nbytes
            else:
                block, scores = _block(start, stop, base, directions, a, b, pivots, free, self.order,
                                       affine or not cs, self.uniform, self.bit_weights, self.n, self.packed_scoring, counters)
            weights[start:stop] = scores
            local = int(np.argmin(scores))
            if best < 0 or scores[local] < weights[best]:
                best = start+local
                selected[:] = block[local]
            if materialized is not None:
                materialized[start:stop] = block
            block_peak = max(block_peak, block.nbytes+scores.nbytes+extra_bytes)
            timing['enumerate_score'] += perf_counter_ns()-tick
            tick = perf_counter_ns()
            if evidence_mode == 'full':
                if not _check_candidates(packed_h if packed_h is not None else a, self.row_ptr, self.columns, block, s,
                                         self.matrix_storage == 'sparse', counters):
                    raise RuntimeError('OSD candidate fails original syndrome validation')
                checks += len(block)
            timing['candidate_validation'] += perf_counter_ns()-tick
            tick = perf_counter_ns()
            candidate_digest.update(np.ascontiguousarray(block, dtype='<u8').view(np.uint8))
            timing['candidate_hash'] += perf_counter_ns()-tick
        tick = perf_counter_ns()
        if evidence_mode == 'fast':
            if not _check_candidates(packed_h if packed_h is not None else a,
                                     self.row_ptr, self.columns, selected.reshape(1, -1), s,
                                     self.matrix_storage == 'sparse', counters):
                raise RuntimeError('OSD output fails original syndrome validation')
            checks += 1
        timing['candidate_validation'] += perf_counter_ns()-tick
        tick = perf_counter_ns()
        encoded_weights = np.ascontiguousarray(weights, dtype='<i8' if self.uniform else '<f8').view(np.uint8)
        weights_digest = sha256(encoded_weights).hexdigest()
        candidate_digest.update(encoded_weights)
        digest = candidate_digest.hexdigest()
        timing['weight_hash'] = perf_counter_ns()-tick
        tick = perf_counter_ns()
        output = np.unpackbits(np.ascontiguousarray(selected, dtype='<u8').view(np.uint8), bitorder='little')[:self.n]
        work = {name: int(counters[i]) for i, name in enumerate(COUNTERS)}
        work.update(schema=WORK_VERSION, sort_items=self.n, pivots=len(pivots),
                    matrix_words_copied=self.m*self.width if cached is None else 0,
                    matrix_pack_edges=self.nnz if self.packed_matrix is None and packed_h is not None else 0,
                    candidate_evaluations=count, original_syndrome_checks=checks,
                    candidate_hash_bytes=count*self.width*8, weight_hash_bytes=weights.nbytes,
                    candidate_materialized_bytes=0 if materialized is None else materialized.nbytes,
                    candidate_block_peak_bytes=block_peak, retained_weights_bytes=weights.nbytes,
                    cache_lookup=int(key is not None), cache_hit=int(cached is not None), cache_stored=int(cache_stored),
                    retained_matrix_bytes=self.retained_matrix_bytes,
                    cache_retained_bytes=0 if self.cache is None else self.cache.info()['bytes'])
        work.update(candidate_xor_bytes=int(byte_counters[0]), byte_score_bit_tests=int(byte_counters[1]),
                    byte_score_additions=int(byte_counters[2]))
        semantic = dict(version=VERSION, evidence_version=EVIDENCE_VERSION,
                        method=self.method, order=self.order, n=self.n, m=self.m,
                        matrix_sha256=self.matrix_sha256, channel_sha256=self.channel_sha256,
                        syndrome_sha256=_digest(s, 'u1'), posterior_sha256=_digest(llr, '<f8'),
                        ordering_sha256=_digest(ordering, '<i8'),
                        pivots_sha256=_digest(pivots, '<i8'), free_sha256=_digest(free, '<i8'),
                        score=self.score, weight_encoding='int64-hamming' if self.uniform else 'float64-weighted',
                        digest_encoding='candidate-major-original-column-le-u64-then-all-le-weights-v1',
                        count=count, selected_index=best, selected_sha256=_digest(output, 'u1'),
                        weights_sha256=weights_digest, candidate_set_sha256=digest)
        ledger = dict(semantic=semantic, semantic_sha256=_json_digest(semantic),
                      evidence_mode=evidence_mode, validation_scope='all' if evidence_mode == 'full' else 'winner',
                      materialized=materialize_candidates, work=work,
                      execution=dict(matrix_storage=self.matrix_storage, affine_reuse=self.affine_reuse,
                                     response_method=self.response_method, packed_scoring=self.packed_scoring,
                                     block_size=self.block_size, candidate_representation=self.candidate_representation))
        ledger['ledger_sha256'] = _json_digest(ledger)
        result = OsdResult(immutable_snapshot(output), None if materialized is None else immutable_snapshot(materialized),
                           immutable_snapshot(weights), immutable_snapshot(ordering), immutable_snapshot(pivots),
                           immutable_snapshot(free), best, self.method, self.order, work, timing, digest, ledger)
        timing['ledger_and_snapshots'] = perf_counter_ns()-tick
        timing['total'] = perf_counter_ns()-started
        return result

    def replay(self, syndrome, posterior_llr, ledger, *, materialize_candidates=False):
        """Recompute full semantic evidence; operational cache/timing may differ."""
        if not isinstance(ledger, dict) or 'ledger_sha256' not in ledger:
            raise ValueError('missing versioned OSD ledger')
        unsigned = {k: v for k, v in ledger.items() if k != 'ledger_sha256'}
        if ledger['ledger_sha256'] != _json_digest(unsigned):
            raise ValueError('OSD ledger digest mismatch')
        result = self.decode(syndrome, posterior_llr, evidence_mode=ledger['evidence_mode'],
                             materialize_candidates=materialize_candidates)
        if result.ledger['semantic'] != ledger['semantic'] or result.ledger['semantic_sha256'] != ledger['semantic_sha256']:
            raise ValueError('OSD semantic replay mismatch')
        return result
