"""Opt-in canonical min-sum BP + OSD v2 with mandatory per-call evidence.

Only traversal, channel binding and provenance live here. Every BP message is
computed by the existing canonical _policy_sweep_into, with no kernel edits.
"""
from dataclasses import dataclass
import math
from time import perf_counter_ns

import numpy as np
from numba import njit

from bp_registry.canonical.compiled import _policy_sweep_into, _candidate_matches
from bp_registry.compiled_contracts import immutable_snapshot
from bp_registry.postprocessing.osd import _binary
from bp_registry.postprocessing.osd_v2 import Osd, _digest, _json_digest

VERSION = 'canonical-minsum-osd-pipeline-v2'


@njit(cache=True)
def _run(row_ptr, columns, n, syndrome, initial, prior, cap, alpha, roffe_schedule):
    old = initial[columns].copy()
    new, c2v = np.empty_like(old), np.empty_like(old)
    beliefs, candidate = np.empty(n, dtype=np.float64), np.empty(n, dtype=np.uint8)
    for iteration in range(1, cap+1):
        coefficient = 1.-2.**(-iteration) if roffe_schedule else alpha
        _policy_sweep_into(row_ptr, columns, n, old, syndrome, prior,
                           2, 1., False, 1, 0., 1., coefficient, 0.,
                           c2v, beliefs, candidate, new, True, 1e-10)
        if _candidate_matches(row_ptr, columns, candidate, syndrome):
            return candidate, beliefs, True, iteration
        old, new = new, old
    return candidate, beliefs, False, cap


@dataclass(frozen=True)
class BpOsdResult:
    candidate: np.ndarray
    bp_candidate: np.ndarray
    posterior_llr: np.ndarray
    converged: bool
    iterations: int
    osd: object
    ledger: dict
    timings_ns: dict


class CanonicalBpOsd:
    """Fixed original channel, float64 min-sum, OSD only on nonconvergence.

    alpha='roffe' means alpha_t=1-2^-t; a numeric alpha is constant scaling.
    initial messages use log((1-p)/p), update priors use log1p(-p)-log(p),
    preserving the qualified Roffe controller's historical distinction.
    """

    def __init__(self, processor, *, max_iterations, alpha='roffe'):
        if not isinstance(processor, Osd) or type(max_iterations) is not int or max_iterations < 1:
            raise ValueError('OSD v2 processor and positive integer BP budget required')
        roffe = isinstance(alpha, str) and alpha == 'roffe'
        if not roffe and (isinstance(alpha, (bool, str)) or not isinstance(alpha, (float, int)) or not math.isfinite(alpha) or alpha <= 0):
            raise ValueError('positive finite alpha or roffe schedule required')
        self.processor, self.cap = processor, max_iterations
        self.alpha, self.roffe_schedule = 1. if roffe else float(alpha), roffe
        p = processor.probabilities
        self.initial = immutable_snapshot(np.array([math.log((1-float(v))/float(v)) for v in p]))
        self.prior = immutable_snapshot(np.array([math.log1p(-float(v))-math.log(float(v)) for v in p]))
        if not np.all(np.isfinite(self.initial)) or not np.all(np.isfinite(self.prior)):
            raise ValueError('initial canonical BP messages must be finite float64')

    def bp(self, syndrome):
        p = self.processor
        s = _binary(syndrome, ndim=1, name='syndrome')
        if s.shape != (p.m,):
            raise ValueError('original syndrome shape mismatch')
        return _run(p.row_ptr, p.columns, p.n, s, self.initial, self.prior,
                    self.cap, self.alpha, self.roffe_schedule)

    def decode(self, syndrome, *, evidence_mode='fast', materialize_candidates=False):
        if evidence_mode not in ('fast', 'full') or type(materialize_candidates) is not bool:
            raise ValueError('explicit fast/full evidence mode and boolean materialization required')
        started = perf_counter_ns()
        candidate, posterior, converged, iterations = self.bp(syndrome)
        bp_ns = perf_counter_ns()-started
        tick = perf_counter_ns()
        osd = None if converged else self.processor.decode(syndrome, posterior, evidence_mode=evidence_mode,
                                                          materialize_candidates=materialize_candidates)
        osd_ns = perf_counter_ns()-tick
        selected = candidate if osd is None else osd.candidate
        ledger = dict(version=VERSION, matrix_sha256=self.processor.matrix_sha256,
                      channel_sha256=self.processor.channel_sha256,
                      syndrome_sha256=_digest(syndrome, 'u1'), max_iterations=self.cap,
                      alpha='roffe' if self.roffe_schedule else self.alpha,
                      bp_converged=bool(converged), bp_iterations=int(iterations),
                      bp_directed_edge_updates=2*int(iterations)*self.processor.nnz,
                      bp_candidate_sha256=_digest(candidate, 'u1'), posterior_sha256=_digest(posterior, '<f8'),
                      selected_sha256=_digest(selected, 'u1'), osd=None if osd is None else osd.ledger)
        ledger['ledger_sha256'] = _json_digest(ledger)
        return BpOsdResult(immutable_snapshot(selected), immutable_snapshot(candidate), immutable_snapshot(posterior),
                           bool(converged), int(iterations), osd, ledger,
                           dict(bp=bp_ns, osd=osd_ns, total=perf_counter_ns()-started))
