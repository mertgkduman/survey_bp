"""Paired depolarizing controls; message equations remain canonical and frozen."""
import importlib.util
import sys
import time
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import numpy as np
from bp_registry.artifacts import load_artifact
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_mackay_isolation_rt', HERE/'bp_study_runtime.py')
rt = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = rt
spec.loader.exec_module(rt)
original_state, original_event = rt.state, rt.event


def state(job):
    if job['arm'] != 'binary_separate':
        return original_state(job)
    code = load_artifact(rt.REPO, job['code_artifact'],
                         expected_semantic_sha256=job['code_semantic_sha256']).code
    profile = replace(BINARY_SPA_F64_V2, v2c_damping=0., check_cap=None)
    graphs = [CompiledBinaryFlooding.from_check_matrix(h, profile=profile) for h in (code.hz, code.hx)]
    packed = tuple(np.packbits(h, axis=1, bitorder='little') for h in (code.hx, code.hz, code.lx, code.lz))
    return job, code.n, packed, graphs


def paulis(x, z):
    lookup = np.empty((2, 2), dtype=np.uint8)
    for label, (xb, zb) in enumerate(rt.parent.base.PAULI_BITS):
        lookup[xb, zb] = label
    return lookup[x, z]


def event(value, shot):
    job, n, packed, graphs = value
    if job['arm'] != 'binary_separate':
        return original_event(value, shot)
    truth = rt.parent.base._sample(job['seed'], round(job['physical_p']*100000), shot, n, depolarizing=True)
    bits = rt.parent.base.PAULI_BITS[truth]
    sx = rt.parent.base._syndrome(packed[0], bits[:, 1])
    sz = rt.parent.base._syndrome(packed[1], bits[:, 0])
    syndrome = np.concatenate((sx, sz))
    p0 = 2*job['physical_p']/3
    start = time.perf_counter_ns()
    results = [g.run(s, error_rate=p0, max_iterations=job['decoder']['max_iterations'])
               for g, s in zip(graphs, (sz, sx), strict=True)]
    elapsed = time.perf_counter_ns()-start
    candidate = paulis(results[0].candidate, results[1].candidate)
    label, _ = rt.parent.outcome(*packed, truth, candidate, joint=True)
    if all(r.converged for r in results) != (label != 'type_i'):
        raise ValueError('separate-X/Z convergence disagrees with original-code evaluation')
    components = [r.iterations for r in results]
    rounds = max(components)
    return {'shot': shot, 'outcome': label, 'iterations': rounds, 'branch_iterations': [rounds],
            'component_iterations': components, 'component_converged': [bool(r.converged) for r in results],
            'directed_edge_updates': 2*job['component_graph_edges']*sum(components), 'decode_ns': elapsed,
            'error_sha256': sha256(truth.tobytes()).hexdigest(),
            'syndrome_sha256': sha256(syndrome.tobytes()).hexdigest(),
            'candidate_sha256': sha256(candidate.tobytes()).hexdigest()}


class Ledger(rt.parent.base.Ledger):
    def __init__(self, directory, job):
        self.edge_updates = self.component_sweeps = 0
        super().__init__(directory, job)

    def add(self, row, line):
        cap = self.job['decoder']['max_iterations']
        if type(row['iterations']) is not int or row['branch_iterations'] != [row['iterations']]:
            raise ValueError('invalid full-graph rounds')
        if self.job['arm'] == 'binary_separate':
            parts = row.get('component_iterations', [])
            flags = row.get('component_converged', [])
            if (len(parts) != 2 or any(type(x) is not int or not 0 <= x <= cap for x in parts)
                    or max(parts) != row['iterations'] or len(flags) != 2
                    or any(type(x) is not bool for x in flags) or all(flags) != (row['outcome'] != 'type_i')):
                raise ValueError('invalid separate component work or convergence')
            expected = 2*self.job['component_graph_edges']*sum(parts)
            component_sweeps = sum(parts)
        else:
            expected = 2*self.job['graph_edges']*row['iterations']
            component_sweeps = 0
        if type(row['directed_edge_updates']) is not int or row['directed_edge_updates'] != expected:
            raise ValueError('invalid directed edge work')
        super().add(row, line)
        self.edge_updates += expected
        self.component_sweeps += component_sweeps

    def summary(self):
        s = super().summary()
        classical = s['failures']+s['counts']['stabilizer_success']
        return {**s, 'directed_edge_updates': self.edge_updates,
                'component_iterations': self.component_sweeps,
                'classical_block_errors': classical, 'classical_block_error_rate': classical/s['shots']}


rt.state, rt.event, rt.Ledger = state, event, Ledger
