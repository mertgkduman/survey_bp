"""Observable uniform-channel OSD-0/CS, informed by quantumgizmos/ldpc.

Source: d3429964cd4ffe1abfc041c6ec8b8425cb174f40/src_cpp/osd.hpp.
See UPSTREAM-LICENSE.txt for the public source license. This is a new,
independently qualified implementation; it does not admit the historical
failed Phase7 standalone-worker receipt. Posterior log(P0/P1) is sorted in
ascending signed order, with original column ID breaking equalities.
"""
from dataclasses import dataclass
from hashlib import sha256
import math

from numba import njit
import numpy as np

from bp_registry.compiled_contracts import immutable_snapshot

VERSION = 'uniform-osd-packed-v1'
UPSTREAM_COMMIT = 'd3429964cd4ffe1abfc041c6ec8b8425cb174f40'


@njit(cache=True)
def _popcount(value):
    value -= (value >> np.uint64(1)) & np.uint64(0x5555555555555555)
    value = (value & np.uint64(0x3333333333333333)) + ((value >> np.uint64(2)) & np.uint64(0x3333333333333333))
    value = (value + (value >> np.uint64(4))) & np.uint64(0x0F0F0F0F0F0F0F0F)
    return int((value*np.uint64(0x0101010101010101)) >> np.uint64(56))


@njit(cache=True)
def _weight(words):
    total = 0
    for word in words:
        total += _popcount(word)
    return total


@njit(cache=True)
def _original_check(matrix, candidate, syndrome):
    for row in range(matrix.shape[0]):
        parity = 0
        for word in range(matrix.shape[1]):
            parity ^= _popcount(matrix[row, word] & candidate[word]) & 1
        if parity != syndrome[row]:
            return False
    return True


@njit(cache=True)
def _solve(matrix, syndrome, ordering, n, depth, cs):
    m, width = matrix.shape
    a, b = matrix.copy(), syndrome.copy()
    pivots = np.empty(min(m, n), dtype=np.int64)
    pivot_flags = np.zeros(n, dtype=np.uint8)
    rank, probes, xor_words, row_swaps = 0, 0, 0, 0
    remaining = int(np.sum(b))
    # OSD0 may stop once the transformed syndrome lies in the pivot span.
    for column in ordering:
        if rank == min(m, n) or (not cs and remaining == 0):
            break
        word, bit = column//64, np.uint64(1) << np.uint64(column % 64)
        pivot = -1
        for row in range(rank, m):
            probes += 1
            if a[row, word] & bit:
                pivot = row
                break
        if pivot < 0:
            continue
        if pivot != rank:
            for w in range(width):
                a[pivot, w], a[rank, w] = a[rank, w], a[pivot, w]
            b[pivot], b[rank] = b[rank], b[pivot]
            row_swaps += 1
        pivots[rank] = column
        pivot_flags[column] = 1
        for row in range(rank+1, m):
            probes += 1
            if a[row, word] & bit:
                for w in range(width):
                    a[row, w] ^= a[rank, w]
                b[row] ^= b[rank]
                xor_words += width
        rank += 1
        remaining = int(np.sum(b[rank:]))
    if np.any(b[rank:]):
        return (np.zeros((0, width), dtype=np.uint64), np.zeros(0, dtype=np.int64),
                pivots[:rank], np.zeros(0, dtype=np.int64), probes, xor_words, row_swaps, -1)
    # Reduce only pivot rows above the diagonal, reusing one elimination for
    # the OSD0 solution and every affine nullspace direction.
    if cs:
        for i in range(rank-1, -1, -1):
            column = pivots[i]
            word, bit = column//64, np.uint64(1) << np.uint64(column % 64)
            for row in range(i):
                probes += 1
                if a[row, word] & bit:
                    for w in range(width):
                        a[row, w] ^= a[i, w]
                    b[row] ^= b[i]
                    xor_words += width
    free = np.empty(n-rank, dtype=np.int64)
    q = 0
    for column in ordering:
        if not pivot_flags[column]:
            free[q] = column
            q += 1
    if cs and depth > q:
        return (np.zeros((0, width), dtype=np.uint64), np.zeros(0, dtype=np.int64),
                pivots[:rank], free, probes, xor_words, row_swaps, -2)
    count = 1 + (q + depth*(depth-1)//2 if cs else 0)
    candidates = np.zeros((count, width), dtype=np.uint64)
    for row in range(rank-1, -1, -1):
        value = int(b[row])
        if not cs:
            # OSD0 needs only one triangular solve, not a complete RREF.
            for w in range(width):
                value ^= _popcount(a[row, w] & candidates[0, w]) & 1
        if value:
            column = pivots[row]
            candidates[0, column//64] |= np.uint64(1) << np.uint64(column % 64)
    if cs:
        for j in range(q):
            column = free[j]
            word, bit = column//64, np.uint64(1) << np.uint64(column % 64)
            candidates[j+1] = candidates[0]
            candidates[j+1, word] ^= bit
            for row in range(rank):
                if a[row, word] & bit:
                    pivot = pivots[row]
                    candidates[j+1, pivot//64] ^= np.uint64(1) << np.uint64(pivot % 64)
        index = 1+q
        for i in range(depth):
            for j in range(i+1, depth):
                # x0 XOR dir_i XOR dir_j = x0 XOR single_i XOR single_j.
                for w in range(width):
                    candidates[index, w] = candidates[0, w] ^ candidates[1+i, w] ^ candidates[1+j, w]
                index += 1
    weights = np.empty(count, dtype=np.int64)
    best = 0
    for i in range(count):
        weights[i] = _weight(candidates[i])
        if weights[i] < weights[best]:
            best = i
    return candidates, weights, pivots[:rank], free, probes, xor_words, row_swaps, best


def _binary(value, *, ndim, name):
    a = np.asarray(value)
    if a.ndim != ndim or not np.issubdtype(a.dtype, np.integer) or np.any((a != 0) & (a != 1)):
        raise ValueError(f'{name} must be an integer binary array with dimension {ndim}')
    return np.asarray(a, dtype=np.uint8)


@dataclass(frozen=True)
class OsdResult:
    candidate: np.ndarray
    candidates_packed: np.ndarray
    candidate_weights: np.ndarray
    ordering: np.ndarray
    pivot_columns: np.ndarray
    free_columns: np.ndarray
    selected_index: int
    method: str
    order: int
    work: dict
    candidate_set_sha256: str

    def candidates(self):
        """Expose every original-coordinate candidate, including OSD0 first."""
        n = len(self.candidate)
        raw = np.ascontiguousarray(self.candidates_packed, dtype='<u8').view(np.uint8)
        return np.unpackbits(raw.reshape(len(raw), -1), axis=1, bitorder='little')[:, :n]


class UniformOsd:
    """Deterministic OSD for a fixed binary matrix and uniform bit-flip prior.

    Minimal Hamming weight is equivalent to both the public source's uniform
    channel score and full original-channel negative log likelihood. Equal
    weights retain OSD0, then the first enumerated single/pair candidate.
    """

    def __init__(self, check_matrix, *, method: str, order: int):
        h = _binary(check_matrix, ndim=2, name='check matrix')
        if not h.shape[0] or not h.shape[1]:
            raise ValueError('check matrix must have nonempty dimensions')
        if method not in ('OSD_0', 'OSD_CS') or type(order) is not int or order < 0:
            raise ValueError('explicit OSD_0/OSD_CS method and nonnegative integer order required')
        if method == 'OSD_0' and order != 0 or method == 'OSD_CS' and order < 1:
            raise ValueError('OSD_0 requires order0; OSD_CS requires positive search depth')
        if order > h.shape[1]:
            raise ValueError('OSD search depth exceeds original column count')
        self.check_matrix = immutable_snapshot(h, dtype=np.uint8)
        self.method, self.order = method, order
        self.n = h.shape[1]
        padded = np.zeros((h.shape[0], ((self.n+63)//64)*8), dtype=np.uint8)
        packed_bytes = np.packbits(h, axis=1, bitorder='little')
        padded[:, :packed_bytes.shape[1]] = packed_bytes
        self.packed_matrix = immutable_snapshot(padded.view('<u8'), dtype=np.uint64)

    def decode(self, syndrome, posterior_llr, *, error_rate: float):
        if isinstance(error_rate, (bool, np.bool_)) or not isinstance(error_rate, (float, int)) or not math.isfinite(error_rate) or not 0 < error_rate < .5:
            raise ValueError('uniform original error_rate must lie in (0,.5)')
        s = _binary(syndrome, ndim=1, name='syndrome')
        llr = np.asarray(posterior_llr, dtype=np.float64)
        if s.shape != (self.check_matrix.shape[0],) or llr.shape != (self.n,) or not np.all(np.isfinite(llr)):
            raise ValueError('syndrome/finite signed posterior shape mismatch')
        ordering = np.argsort(llr, kind='stable').astype(np.int64)
        values, weights, pivots, free, probes, xor_words, swaps, best = _solve(
            self.packed_matrix, s, ordering, self.n, self.order, self.method == 'OSD_CS')
        if best < 0:
            raise ValueError('inconsistent syndrome' if best == -1 else 'OSD search depth exceeds non-pivot count')
        selected = np.unpackbits(np.ascontiguousarray(values[best], dtype='<u8').view(np.uint8), bitorder='little')[:self.n]
        if not _original_check(self.packed_matrix, values[best], s):
            raise RuntimeError('OSD output fails independent original-syndrome validation')
        work = {'sort_items': self.n, 'pivot_probes': probes, 'row_xor_words': xor_words,
                'row_swaps': swaps, 'pivots': len(pivots), 'candidate_evaluations': len(weights),
                'candidate_score_words': len(weights)*self.packed_matrix.shape[1], 'original_syndrome_checks': 1,
                'matrix_words_copied': self.packed_matrix.size,
                'back_substitution_words': len(pivots)*self.packed_matrix.shape[1] if self.method == 'OSD_0' else 0,
                'affine_single_pivot_probes': len(pivots)*len(free) if self.method == 'OSD_CS' else 0,
                'affine_pair_xor_words': (self.order*(self.order-1)//2)*self.packed_matrix.shape[1] if self.method == 'OSD_CS' else 0,
                'original_check_words': self.packed_matrix.size}
        encoded = np.ascontiguousarray(values, dtype='<u8').tobytes() + np.ascontiguousarray(weights, dtype='<i8').tobytes()
        return OsdResult(immutable_snapshot(selected, dtype=np.uint8), immutable_snapshot(values),
                         immutable_snapshot(weights), immutable_snapshot(ordering), immutable_snapshot(pivots),
                         immutable_snapshot(free), int(best), self.method, self.order, work, sha256(encoded).hexdigest())
