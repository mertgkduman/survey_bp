"""Deterministic compiled CPU batches for explicitly qualified flooding contracts.

Only shots are parallelized. Within a shot, arithmetic and stopping use the same
compiled functions as single-shot execution (no fastmath or reordered reductions).
This decoder API receives observations, never hidden simulation truth.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
from numba import njit, prange, get_num_threads, set_num_threads, config
from .canonical.compiled import _decode_v2 as binary_decode, _decode_policy as binary_policy
from .quaternary.compiled import _decode_v2 as pauli_decode, _decode_policy as pauli_policy
from .canonical.numerics import BinaryNumericalProfileV3
from .quaternary.numerics import QuaternaryNumericalProfileV3


@njit(cache=True, parallel=True)
def _binary_batch(row_ptr, variables, n, syndromes, prior, limit, cap, epsilon,
                  damping, use_policy, fmt, scale, all_state, rule, old, fresh,
                  alpha, beta, shortcut, band):
    count = len(syndromes)
    candidates = np.empty((count, n), dtype=np.uint8)
    iterations = np.empty(count, dtype=np.int64)
    converged = np.empty(count, dtype=np.bool_)
    for shot in prange(count):
        if use_policy:
            c, ok, it = binary_policy(row_ptr, variables, n, syndromes[shot], prior, limit,
                fmt, scale, all_state, rule, old, fresh, alpha, beta, shortcut, band, epsilon, True)
        else:
            c, ok, it = binary_decode(row_ptr, variables, n, syndromes[shot], prior, limit,
                                     cap, epsilon, damping, True)
        candidates[shot] = c
        iterations[shot], converged[shot] = it, ok
    return candidates, iterations, converged


@njit(cache=True, parallel=True)
def _pauli_batch(row_ptr, variable_ptr, variable_edges, variables, labels, priors,
                 syndromes, limit, cap, epsilon, damping, stop, use_policy,
                 fmt, scale, scope, rule, old, fresh, alpha, beta, decision, shortcut, band):
    count = len(syndromes)
    candidates = np.empty((count, len(priors)), dtype=np.uint8)
    iterations = np.empty(count, dtype=np.int64)
    converged = np.empty(count, dtype=np.bool_)
    for shot in prange(count):
        if use_policy:
            c, it, ok = pauli_policy(row_ptr, variable_ptr, variable_edges, variables, labels,
                priors, syndromes[shot], limit, fmt, scale, scope, rule, old, fresh,
                alpha, beta, decision, shortcut, stop, band, epsilon, True)
        else:
            c, it, ok = pauli_decode(row_ptr, variable_ptr, variable_edges, variables, labels,
                priors, syndromes[shot], limit, cap, epsilon, damping, stop, True)
        candidates[shot] = c
        iterations[shot], converged[shot] = it, ok
    return candidates, iterations, converged


@dataclass(frozen=True)
class CpuBatchResult:
    candidates: np.ndarray
    iterations: np.ndarray
    converged: np.ndarray
    syndromes: np.ndarray
    evidence_json: str

    def write_ledger(self, path: str | Path) -> None:
        """Write one input/output/work record per shot; no outcome is inferred."""
        from .canonical.budgets import WorkVector
        evidence = json.loads(self.evidence_json)
        unit = WorkVector.from_flooding_counts(edge_count=evidence['edge_count'],
                                               variable_count=self.candidates.shape[1]) + WorkVector(bp_calls=1)
        with Path(path).open('w', encoding='utf-8') as handle:
            for shot, (candidate, iterations, valid) in enumerate(zip(self.candidates, self.iterations, self.converged, strict=True)):
                work = {key: int(value) * int(iterations) for key, value in unit.as_evidence(structural_event_version=4).items()}
                shortcut = evidence['numerics'].get('zero_syndrome_shortcut', False) and evidence['stop_on_convergence']
                initial_stop = shortcut and int(iterations) == 0 and bool(valid)
                sweep_stop = evidence['stop_on_convergence'] and int(iterations) > 0 and bool(valid)
                work['candidate_constructions'] += 1
                work['candidate_checks'] += self.candidates.shape[1]
                work['convergence_checks'] = (int(iterations) if evidence['stop_on_convergence'] else 0) + int(shortcut) + int(not initial_stop and not sweep_stop)
                empty_binary = evidence['family'] == 'binary' and evidence['edge_count'] == 0 and evidence['numerics'].get('version') is None
                terminal = 'empty_graph' if empty_binary else 'initial_convergence' if initial_stop else 'converged' if sweep_stop else 'max_iterations'
                row = {'event': 'cpu_batch_decode', 'termination': terminal, 'shot_index': shot, 'syndrome': self.syndromes[shot].tolist(),
                       'candidate': candidate.tolist(), 'iterations': int(iterations),
                       'candidate_valid': bool(valid), 'work': work, **evidence}
                handle.write(json.dumps(row, sort_keys=True) + '\n')


def _request(graph, syndromes, limit, workers):
    if type(limit) is not int or limit < 0:
        raise ValueError('max_iterations must be a nonnegative integer')
    if type(workers) is not int or not 1 <= workers <= config.NUMBA_NUM_THREADS:
        raise ValueError('workers must be between 1 and NUMBA_NUM_THREADS')
    s = np.asarray(syndromes)
    if (s.ndim != 2 or s.shape[1] != len(graph.row_ptr)-1 or not np.issubdtype(s.dtype,np.integer)
            or np.any((s != 0) & (s != 1))):
        raise ValueError('syndromes must be a binary integer matrix with one row per shot')
    if graph.policy is not None and graph.policy.version != 'bp-flooding-policy-v2':
        raise ValueError('CPU batches require an explicit v2 flooding policy')
    s = np.array(s, dtype=np.uint8, order='C', copy=True)
    return s


def _policy_args(policy):
    if policy is None:
        return (0, 1., 0, 0, 0., 1., 1., 0., 2, False, False, 1e-10)
    r = policy.resolution
    band, epsilon = policy.stabilization_args
    return (r.format_code, r.fixed_scale, {'scalar_edges':0,'all_messages':1,'all_state':2}[r.scope],
            int(policy.check_rule == 'min_sum'), *policy.coefficients, policy.decision_code,
            policy.zero_syndrome_shortcut, band, epsilon)


def _execute(function, args, graph, s, workers, limit, stop, prior):
    previous = get_num_threads()
    try:
        set_num_threads(workers)
        arrays = function(*args)
    finally:
        set_num_threads(previous)
    for array in (*arrays, s):
        array.setflags(write=False)
    identity = sha256(str(arrays[0].shape[1]).encode())
    for value in (graph.row_ptr, graph.variables, getattr(graph,'labels',np.empty(0,dtype=np.uint8)), np.asarray(prior,dtype=np.float64)):
        identity.update(str((value.shape, value.dtype.str)).encode())
        identity.update(value.tobytes())
    evidence = {'backend':'numba-cpu-batch-v1', 'family':'quaternary' if hasattr(graph,'labels') else 'binary', 'numerics':graph.effective_numerics,
                'graph_prior_sha256':identity.hexdigest(), 'syndromes_sha256':sha256(s.tobytes()).hexdigest(),
                'workers':workers, 'max_iterations':limit, 'stop_on_convergence':stop,
                'edge_count':len(graph.variables), 'work_accounting_version':'compiled-flooding-v1',
                'work_scope':'sweeps plus initial decision and actual convergence checks; excludes graph/prior binding',
                'assessment_status':'not_assessed', 'parallel_unit':'independent_shot', 'fastmath':False}
    return CpuBatchResult(*arrays, s, json.dumps(evidence,sort_keys=True))


def binary_batch(graph, syndromes, *, error_rate, max_iterations, workers=1):
    s = _request(graph, syndromes, max_iterations, workers)
    if graph.policy is None and not isinstance(graph.profile, BinaryNumericalProfileV3):
        raise ValueError('CPU batches require corrected binary v3 or explicit policy v2')
    _, prior = graph._inputs(np.zeros(len(graph.row_ptr)-1,dtype=np.uint8), error_rate)
    fmt,scale,scope,rule,old,fresh,alpha,beta,decision,shortcut,band,eps = _policy_args(graph.policy)
    p=graph.profile
    epsilon=eps if graph.policy else p.product_epsilon
    cap=np.inf if graph.policy or p.check_cap is None else p.check_cap
    damping=0. if graph.policy else p.v2c_damping
    args=(graph.row_ptr,graph.variables,graph.table.variable_count,s,prior,max_iterations,cap,epsilon,
          damping,graph.policy is not None,fmt,scale,scope==2,rule,old,fresh,alpha,beta,shortcut,band)
    return _execute(_binary_batch,args,graph,s,workers,max_iterations,True,prior)


def pauli_batch(graph, syndromes, *, max_iterations, workers=1, stop_on_convergence=True):
    s = _request(graph, syndromes, max_iterations, workers)
    if type(stop_on_convergence) is not bool:
        raise ValueError('stop_on_convergence must be boolean')
    if graph.policy is None and not isinstance(graph.profile, QuaternaryNumericalProfileV3):
        raise ValueError('CPU batches require corrected BP4 v3 or explicit policy v2')
    fmt,scale,scope,rule,old,fresh,alpha,beta,decision,shortcut,band,eps = _policy_args(graph.policy)
    p=graph.profile
    epsilon=eps if graph.policy else p.product_epsilon
    cap=np.inf if graph.policy or p.check_cap is None else p.check_cap
    damping=0. if graph.policy else p.v2c_damping
    args=(graph.row_ptr,graph.variable_ptr,graph.variable_edges,graph.variables,graph.labels,graph.prior_llrs,
          s,max_iterations,cap,epsilon,damping,stop_on_convergence,graph.policy is not None,
          fmt,scale,scope,rule,old,fresh,alpha,beta,decision,shortcut,band)
    return _execute(_pauli_batch,args,graph,s,workers,max_iterations,stop_on_convergence,graph.prior_llrs)
