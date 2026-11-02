"""Frozen execution semantics for matched B1/C2 depolarizing baselines."""
from hashlib import sha256
from pathlib import Path
import json
import sys
import time

import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from common import REPO,source,vanilla,compress,open_event_ledger,source_hashes

ARMS=('binary_v2','qbp_v2')
FIELDS=('type_i','type_ii','exact_success','stabilizer_success')


def policies():
    data=json.loads((ROOT/'decoders.json').read_text())
    expected={'schema':'paired-depolarizing-plain-bp-v1','arms':list(ARMS),
              'check_rule':'sum_product','schedule':'flooding','resolution':'float64',
              'max_iterations':100,'damping_old':0.0,'check_cap':None,
              'check_product_epsilon':1e-10,'binary_prior':'q_X=q_Z=2p/3',
              'qbp_prior':['1-p','p/3','p/3','p/3'],'pauli_order':'I,X,Y,Z',
              'candidate':'first_syndrome_matching_completed_iteration_per_component',
              'logical_evaluator':'separate_X_and_Z_signatures'}
    if data!=expected:raise ValueError('unsupported policy file')
    return data


def implementation_hashes():
    files=[ROOT/'study.py',ROOT/'run.py',ROOT/'decoders.json',
           ROOT.parent.with_name('yao-2312-10950-vanilla')/'run.py']
    return {**source_hashes(),**{str(p.relative_to(REPO)):sha256(p.read_bytes()).hexdigest() for p in files}}


def graphs(code,p):
    policies()
    old=vanilla._graphs(code,p)
    return {'binary_v2':old['binary_v2'],'qbp_v2':old['bp4_v2']}


def signature(code,pauli):
    bits=vanilla.PAULI_BITS[pauli]
    return ((code.lz@bits[:,0])%2).tobytes(),((code.lx@bits[:,1])%2).tobytes()


def decode(arm,graph,code,syndrome):
    if arm=='qbp_v2':
        r=graph.run(syndrome,max_iterations=100)
        return r.candidate,[r.iterations],r.converged
    xr=graph[0].run(syndrome[code.hx.shape[0]:],max_iterations=100)
    zr=graph[1].run(syndrome[:code.hx.shape[0]],max_iterations=100)
    return vanilla.BITS_TO_PAULI[xr.candidate,zr.candidate],[xr.iterations,zr.iterations],xr.converged and zr.converged


def outcome(code,evaluator,truth,syndrome,candidate):
    valid=bool(np.array_equal(vanilla._original_syndrome(evaluator,candidate),syndrome))
    logical=bool(valid and signature(code,truth)!=signature(code,candidate))
    exact=bool(valid and not logical and np.array_equal(truth,candidate))
    return {'type_i':not valid,'type_ii':logical,'exact_success':exact,
            'stabilizer_success':bool(valid and not logical and not exact)}


def record(arm,graph,code,evaluator,truth,syndrome):
    start=time.perf_counter_ns()
    candidate,iterations,converged=decode(arm,graph,code,syndrome)
    elapsed=time.perf_counter_ns()-start
    flags=outcome(code,evaluator,truth,syndrome,candidate)
    if flags['type_i']==converged:raise ValueError('independent syndrome evaluator disagrees')
    return {**flags,'iterations':iterations,'elapsed_ns':elapsed,
            'candidate_sha256':sha256(candidate.tobytes()).hexdigest()}
