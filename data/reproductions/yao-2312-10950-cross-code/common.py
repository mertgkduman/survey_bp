"""Shared source receipts and policies for the missing plain-decoder cells."""
from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2, REFERENCE_CPU_F64
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE_ROOT = ROOT.with_name('yao-2312-10950-non-osd')
VANILLA_ROOT = ROOT.with_name('yao-2312-10950-vanilla')
sys.path.insert(0, str(SOURCE_ROOT))
from ledger_io import open_event_ledger
from compress_completed import compress


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


source = load_module('cross_source', SOURCE_ROOT / 'run_point.py')
vanilla = load_module('cross_vanilla', VANILLA_ROOT / 'run.py')
ARMS = ('qbp_v2', 'binary_v2', 'binary_paper')
FIELDS = ('type_i', 'type_ii', 'exact_success', 'stabilizer_success')


def policies():
    data = json.loads((ROOT / 'decoders.json').read_text())
    expected = {'schema': 'cross-code-plain-bp-policies-v1', 'max_iterations': 100,
                'resolution': 'float64', 'damping_old': 0.0, 'check_rule': 'sum_product',
                'schedule': 'flooding', 'check_product_epsilon': 1e-10,
                'qbp_check_cap': None, 'binary_v2_check_cap': None,
                'binary_paper_v2c_cap': 25.0,
                'bit_flip_prior': ["1-p", "p", 0, 0],
                'excluded_support_guard': '1024+abs(log((1-p)/p))+128*maximum_joint_degree'}
    if data != expected:
        raise ValueError('unsupported decoder policy file')
    return data


def bit_flip_graphs(code, p):
    policies()
    # Every finite tanh-product C2V is <64 in magnitude, including the
    # nearest representable product below one. M guarantees that excluded
    # Y/Z weights are >1024 log units below both I and X at every sweep.
    # exp(-1024) is zero in float64. Active scalar projections therefore
    # have exactly the I/X support of (1-p,p,0,0), without inf-inf arithmetic.
    degree = np.sum(code.hx, axis=0) + np.sum(code.hz, axis=0)
    prior = math.log((1-p)/p)
    guard = 1024 + abs(prior) + 128 * int(max(degree))
    llrs = np.full((code.n, 3), guard, dtype=np.float64)
    llrs[:, 0] = prior
    llrs.setflags(write=False)
    qbp = replace(CompiledBp4Graph.from_css(code, p), prior_llrs=llrs,
                  profile=replace(QBP4_F64_V2, v2c_damping=0.0,
                                  profile_id='cross-code-qbp-v2-x-only-undamped'))
    binary = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=replace(
        BINARY_SPA_F64_V2, v2c_damping=0.0, profile_id='cross-code-binary-v2-undamped'))
    paper = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=REFERENCE_CPU_F64)
    return {'qbp_v2': qbp, 'binary_v2': binary, 'binary_paper': paper}, guard


def sample(seed, code, p, shot):
    return source._sample(seed, round(p*100000), shot, code.n, depolarizing=False)


def one_arm(arm, graph, code, p, syndrome):
    if arm == 'qbp_v2':
        r = graph.run(syndrome, max_iterations=100)
    elif arm == 'binary_v2':
        r = graph.run(syndrome[code.hx.shape[0]:], error_rate=p, max_iterations=100)
    else:
        r = graph.run_paper_bp(syndrome[code.hx.shape[0]:], error_rate=p, max_iterations=100)
    return r


def source_hashes():
    paths = [ROOT/'common.py', ROOT/'run.py', ROOT/'decoders.json',
             SOURCE_ROOT/'run_point.py', SOURCE_ROOT/'codes.json',
             REPO/'src/bp_registry/code_constructions.py',
             REPO/'src/bp_registry/canonical/compiled.py',
             REPO/'src/bp_registry/canonical/numerics.py',
             REPO/'src/bp_registry/quaternary/compiled.py',
             REPO/'src/bp_registry/quaternary/numerics.py']
    return {str(p.relative_to(REPO)): sha256(p.read_bytes()).hexdigest() for p in paths}
