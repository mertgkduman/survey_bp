"""Deterministic compiled CPU batches for explicitly qualified flooding contracts.

Only shots are parallelized. Within a shot, arithmetic and stopping use the same
compiled functions as single-shot execution (no fastmath or reordered reductions).
This decoder API receives observations, never hidden simulation truth.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
import numpy as np
from numba import njit, prange, get_num_threads, set_num_threads, config
from .canonical.compiled import _decode_v2 as binary_decode, _decode_policy as binary_policy
from .quaternary.compiled import _decode_v2 as pauli_decode, _decode_policy as pauli_policy
from .canonical.numerics import BinaryNumericalProfileV3
from .quaternary.numerics import QuaternaryNumericalProfileV3
from .compiled_contracts import immutable_snapshot


_EVIDENCE_KEYS = frozenset(('backend', 'family', 'numerics', 'graph_prior_sha256',
    'syndromes_sha256', 'workers', 'max_iterations', 'stop_on_convergence', 'edge_count',
    'work_accounting_version', 'work_scope', 'assessment_status', 'parallel_unit', 'fastmath'))
_V2_KEYS = frozenset(('batch_size', 'variable_count', 'check_count', 'result_binding_sha256'))


def _evidence(text, *, legacy=False):
    if type(text) is not str:
        raise ValueError('CPU batch evidence must be immutable JSON text')
    try:
        value = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise ValueError('invalid CPU batch evidence JSON') from exc
    if not isinstance(value, dict):
        raise ValueError('CPU batch evidence must be an object')
    v1 = legacy and value.get('backend') == 'numba-cpu-batch-v1'
    if set(value) != (_EVIDENCE_KEYS if v1 else _EVIDENCE_KEYS | _V2_KEYS):
        raise ValueError('CPU batch evidence fields do not match its version')
    if value['backend'] != ('numba-cpu-batch-v1' if v1 else 'numba-cpu-batch-v2'):
        raise ValueError('unsupported CPU batch evidence version')
    if value['family'] not in ('binary', 'quaternary') or not isinstance(value['numerics'], dict):
        raise ValueError('invalid CPU batch family or numerics')
    for name in ('workers', 'max_iterations', 'edge_count') + (() if v1 else ('batch_size', 'variable_count', 'check_count')):
        if type(value[name]) is not int or not (int(name == 'workers') <= value[name] <= np.iinfo(np.int64).max):
            raise ValueError(f'invalid CPU batch {name}')
    for name in ('graph_prior_sha256', 'syndromes_sha256') + (() if v1 else ('result_binding_sha256',)):
        if type(value[name]) is not str or re.fullmatch('[0-9a-f]{64}', value[name]) is None:
            raise ValueError(f'invalid CPU batch {name}')
    if type(value['stop_on_convergence']) is not bool or value['fastmath'] is not False:
        raise ValueError('invalid CPU batch execution flags')
    if value['family'] == 'binary' and not value['stop_on_convergence']:
        raise ValueError('binary batch execution requires convergence stopping')
    if (value['parallel_unit'] != 'independent_shot' or value['assessment_status'] != 'not_assessed'
            or value['work_accounting_version'] != 'compiled-flooding-v1'
            or value['work_scope'] != 'sweeps plus initial decision and actual convergence checks; excludes graph/prior binding'):
        raise ValueError('invalid CPU batch execution contract')
    return value


def _result_binding(arrays, evidence):
    identity = sha256(b'cpu-batch-result-v2')
    metadata = {key: value for key, value in evidence.items() if key != 'result_binding_sha256'}
    identity.update(json.dumps(metadata, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
    for value in arrays:
        identity.update(str((value.shape, value.dtype.str)).encode())
        identity.update(value.tobytes())
    return identity.hexdigest()


def _graph_prior_identity(graph, prior, variable_count):
    identity = sha256(str(variable_count).encode())
    for value in (graph.row_ptr, graph.variables, getattr(graph, 'labels', np.empty(0, dtype=np.uint8)), np.asarray(prior, dtype=np.float64)):
        identity.update(str((value.shape, value.dtype.str)).encode())
        identity.update(value.tobytes())
    return identity.hexdigest()


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


@njit(cache=True, inline="never")
def _pauli_shot(row_ptr, variable_ptr, variable_edges, variables, labels, priors,
                 syndrome, limit, cap, epsilon, damping, stop, use_policy,
                 fmt, scale, scope, rule, old, fresh, alpha, beta, decision, shortcut, band):
    # Keep exception exits outside prange so independent shots remain parallel.
    try:
        if use_policy:
            c, it, ok = pauli_policy(row_ptr, variable_ptr, variable_edges, variables, labels,
                priors, syndrome, limit, fmt, scale, scope, rule, old, fresh,
                alpha, beta, decision, shortcut, stop, band, epsilon, True)
        else:
            c, it, ok = pauli_decode(row_ptr, variable_ptr, variable_edges, variables, labels,
                priors, syndrome, limit, cap, epsilon, damping, stop, True)
        return c, it, ok, False
    except Exception:
        # Numba cannot carry exception instances out of a parallel worker.
        return np.zeros(len(priors), dtype=np.uint8), 0, False, True


@njit(cache=True, parallel=True)
def _pauli_batch(row_ptr, variable_ptr, variable_edges, variables, labels, priors,
                 syndromes, limit, cap, epsilon, damping, stop, use_policy,
                 fmt, scale, scope, rule, old, fresh, alpha, beta, decision, shortcut, band):
    count = len(syndromes)
    candidates = np.empty((count, len(priors)), dtype=np.uint8)
    iterations = np.empty(count, dtype=np.int64)
    converged = np.empty(count, dtype=np.bool_)
    failures = np.empty(count, dtype=np.bool_)
    for shot in prange(count):
        c, it, ok, failed = _pauli_shot(
            row_ptr, variable_ptr, variable_edges, variables, labels, priors,
            syndromes[shot], limit, cap, epsilon, damping, stop, use_policy,
            fmt, scale, scope, rule, old, fresh, alpha, beta, decision, shortcut, band)
        candidates[shot] = c
        iterations[shot], converged[shot], failures[shot] = it, ok, failed
    return candidates, iterations, converged, failures


@dataclass(frozen=True)
class CpuBatchResult:
    candidates: np.ndarray
    iterations: np.ndarray
    converged: np.ndarray
    syndromes: np.ndarray
    evidence_json: str

    def __post_init__(self):
        evidence = _evidence(self.evidence_json)
        count, n, m = (evidence[key] for key in ('batch_size', 'variable_count', 'check_count'))
        specifications = (
            ('candidates', (count, n), np.uint8, 3 if evidence['family'] == 'quaternary' else 1),
            ('iterations', (count,), np.int64, evidence['max_iterations']),
            ('converged', (count,), np.bool_, 1),
            ('syndromes', (count, m), np.uint8, 1),
        )
        arrays = []
        for name, shape, dtype, maximum in specifications:
            value = np.asarray(getattr(self, name))
            valid_dtype = value.dtype == np.dtype(bool) if name == 'converged' else np.issubdtype(value.dtype, np.integer)
            if value.shape != shape or not valid_dtype or np.any(value < 0) or np.any(value > maximum):
                raise ValueError(f'invalid CPU batch {name}')
            arrays.append(immutable_snapshot(value, dtype=dtype))
        if sha256(arrays[3].tobytes()).hexdigest() != evidence['syndromes_sha256']:
            raise ValueError('CPU batch syndrome identity mismatch')
        if _result_binding(arrays, evidence) != evidence['result_binding_sha256']:
            raise ValueError('CPU batch result binding mismatch')
        for (name, *_), value in zip(specifications, arrays, strict=True):
            object.__setattr__(self, name, value)

    def write_ledger(self, path: str | Path) -> None:
        """Write one input/output/work record per shot; no outcome is inferred."""
        from .canonical.budgets import WorkVector
        evidence = _evidence(self.evidence_json)
        if _result_binding((self.candidates, self.iterations, self.converged, self.syndromes), evidence) != evidence['result_binding_sha256']:
            raise ValueError('CPU batch result binding mismatch')
        unit = WorkVector.from_flooding_counts(edge_count=evidence['edge_count'],
                                               variable_count=self.candidates.shape[1]) + WorkVector(bp_calls=1)
        destination = Path(path)
        temporary = None
        try:
            with NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent, prefix=f'.{destination.name}.', delete=False) as handle:
                temporary = Path(handle.name)
                self._write_rows(handle, evidence, unit)
            os.replace(temporary, destination)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _write_rows(self, handle, evidence, unit):
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
    if type(limit) is not int or not 0 <= limit <= np.iinfo(np.int64).max:
        raise ValueError('max_iterations must be a bounded nonnegative integer')
    if type(workers) is not int or not 1 <= workers <= config.NUMBA_NUM_THREADS:
        raise ValueError('workers must be between 1 and NUMBA_NUM_THREADS')
    s = np.asarray(syndromes)
    if (s.ndim != 2 or s.shape[1] != len(graph.row_ptr)-1 or not np.issubdtype(s.dtype,np.integer)
            or np.any((s != 0) & (s != 1))):
        raise ValueError('syndromes must be a binary integer matrix with one row per shot')
    if graph.policy is not None and graph.policy.version not in {'bp-flooding-policy-v2', 'bp-flooding-policy-v3'}:
        raise ValueError('CPU batches require an explicit v2/v3 flooding policy')
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
    if len(arrays) == 4:
        failures = np.flatnonzero(arrays[3])
        if len(failures):
            raise ValueError(f"compiled BP4 execution failed for shot indices {failures.tolist()}; no batch result")
        arrays = arrays[:3]
    evidence = {'backend':'numba-cpu-batch-v2', 'family':'quaternary' if hasattr(graph,'labels') else 'binary', 'numerics':graph.effective_numerics,
                'graph_prior_sha256':_graph_prior_identity(graph, prior, arrays[0].shape[1]), 'syndromes_sha256':sha256(s.tobytes()).hexdigest(),
                'workers':workers, 'max_iterations':limit, 'stop_on_convergence':stop,
                'edge_count':len(graph.variables), 'work_accounting_version':'compiled-flooding-v1',
                'work_scope':'sweeps plus initial decision and actual convergence checks; excludes graph/prior binding',
                'assessment_status':'not_assessed', 'parallel_unit':'independent_shot', 'fastmath':False}
    evidence.update(batch_size=len(s), variable_count=arrays[0].shape[1], check_count=s.shape[1])
    evidence['result_binding_sha256'] = _result_binding((*arrays, s), evidence)
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


def verify_cpu_batch_ledger(path, graph, *, error_rate=None):
    """Replay a stored batch against a caller-supplied graph and prior.

    Verify numerical outputs by single-shot replay, candidate validity by an
    independent parity calculation, and work by explicit traversal counts.
    V1 historical ledgers remain readable; V2 additionally binds all results.
    An empty JSONL file contains no shots or graph claim to verify.
    """
    from dataclasses import fields
    from .canonical.budgets import WorkVector

    try:
        rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    except (TypeError, ValueError) as exc:
        raise ValueError('invalid CPU batch ledger JSON') from exc
    if not rows:
        return {'shots': 0, 'graph_verified': False}
    row_keys = {'event', 'termination', 'shot_index', 'syndrome', 'candidate', 'iterations', 'candidate_valid', 'work'}
    if not isinstance(rows[0], dict):
        raise ValueError('CPU batch ledger rows must be objects')
    evidence = _evidence(json.dumps({k: v for k, v in rows[0].items() if k not in row_keys}), legacy=True)
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(evidence) | row_keys:
            raise ValueError('CPU batch ledger row fields mismatch')
        if any(row[key] != value for key, value in evidence.items()):
            raise ValueError('CPU batch ledger metadata differs between shots')
        if type(row['shot_index']) is not int or row['shot_index'] != index or row['event'] != 'cpu_batch_decode':
            raise ValueError('CPU batch shot order mismatch')
        if type(row['iterations']) is not int or type(row['candidate_valid']) is not bool:
            raise ValueError('invalid CPU batch result scalar types')
        for name in ('candidate', 'syndrome'):
            if not isinstance(row[name], list) or any(type(x) is not int for x in row[name]):
                raise ValueError(f'invalid CPU batch {name} labels')
        if not isinstance(row['work'], dict) or any(type(x) is not int or x < 0 for x in row['work'].values()):
            raise ValueError('invalid CPU batch work counters')
    pauli = hasattr(graph, 'labels')
    family = 'quaternary' if pauli else 'binary'
    n = len(graph.prior_llrs) if pauli else graph.table.variable_count
    m = len(graph.row_ptr) - 1
    try:
        arrays = (np.asarray([r['candidate'] for r in rows], dtype=np.int64),
                  np.asarray([r['iterations'] for r in rows], dtype=np.int64),
                  np.asarray([r['candidate_valid'] for r in rows], dtype=np.bool_),
                  np.asarray([r['syndrome'] for r in rows], dtype=np.int64))
    except (ValueError, OverflowError) as exc:
        raise ValueError('invalid CPU batch array representation') from exc
    if evidence['backend'] == 'numba-cpu-batch-v1':
        # Validate legacy storage without modifying or relabeling its file.
        bound = {**evidence, 'backend': 'numba-cpu-batch-v2', 'batch_size': len(rows), 'variable_count': n, 'check_count': m}
        normalized = tuple(a.astype(dtype) for a, dtype in zip(arrays, (np.uint8, np.int64, np.bool_, np.uint8), strict=True))
        bound['result_binding_sha256'] = _result_binding(normalized, bound)
    else:
        bound = evidence
    result = CpuBatchResult(*arrays, json.dumps(bound))
    if result.candidates.shape[1] != n or result.syndromes.shape[1] != m:
        raise ValueError('CPU batch graph dimensions mismatch')
    prior = graph.prior_llrs if pauli else graph._inputs(np.zeros(m, dtype=np.uint8), error_rate)[1]
    if (evidence['family'] != family or evidence['edge_count'] != len(graph.variables)
            or evidence['graph_prior_sha256'] != _graph_prior_identity(graph, prior, n)
            or json.dumps(evidence['numerics'], sort_keys=True) != json.dumps(graph.effective_numerics, sort_keys=True)):
        raise ValueError('CPU batch graph/prior/numerics identity mismatch')
    stop = evidence['stop_on_convergence']
    shortcut = bool(evidence['numerics'].get('zero_syndrome_shortcut', False)) and stop
    for row, candidate, syndrome in zip(rows, result.candidates, result.syndromes, strict=True):
        replay = graph.run(syndrome, max_iterations=evidence['max_iterations'], **({'stop_on_convergence': stop} if pauli else {'error_rate': error_rate}))
        if (not np.array_equal(candidate, replay.candidate) or row['iterations'] != replay.iterations
                or row['candidate_valid'] != replay.converged):
            raise ValueError('CPU batch numerical replay mismatch')
        parity = np.zeros(m, dtype=np.uint8)
        for check in range(m):
            for edge in range(int(graph.row_ptr[check]), int(graph.row_ptr[check + 1])):
                value = int(candidate[graph.variables[edge]])
                parity[check] ^= int(value != 0 and value != int(graph.labels[edge])) if pauli else value
        if bool(np.array_equal(parity, syndrome)) != row['candidate_valid']:
            raise ValueError('CPU batch candidate validity mismatch')
        iterations = row['iterations']
        initial_stop = shortcut and iterations == 0 and row['candidate_valid']
        sweep_stop = stop and iterations > 0 and row['candidate_valid']
        expected = {field.name: 0 for field in fields(WorkVector)}
        expected.update(check_to_variable_updates=iterations * len(graph.variables),
                        variable_to_check_updates=iterations * len(graph.variables),
                        belief_assemblies=iterations * n, bp_calls=iterations,
                        candidate_constructions=iterations + 1, candidate_checks=(iterations + 1) * n,
                        convergence_checks=(iterations if stop else 0) + int(shortcut) + int(not initial_stop and not sweep_stop))
        empty_binary = family == 'binary' and len(graph.variables) == 0 and evidence['numerics'].get('version') is None
        terminal = 'empty_graph' if empty_binary else 'initial_convergence' if initial_stop else 'converged' if sweep_stop else 'max_iterations'
        if row['work'] != expected or row['termination'] != terminal:
            raise ValueError('CPU batch work or termination mismatch')
    return {'shots': len(rows), 'graph_verified': True, 'backend': evidence['backend']}
