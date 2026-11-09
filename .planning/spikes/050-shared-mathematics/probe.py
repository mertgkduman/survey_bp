"""Independent factor sums/minima and boundary quantization for shared BP."""
from pathlib import Path
from itertools import product
from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
import math
import sys
import numpy as np
from scipy.special import logsumexp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from audit_support import Audit
from bp_registry.canonical.policy_decoder import BinaryPolicy, BinaryPolicyDecoder
from bp_registry.canonical.updates import ParameterAssignment
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy

H = np.array([[1, 1, 1, 0, 0], [0, 0, 1, 1, 1]], np.uint8)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ordinary_factors():
    oracle = load('previous_independent_factors', HERE.parent / '043-circuit-cuda-mathematics/probe.py').reference
    rng = np.random.default_rng(5001)
    records, worst = [], 0.
    for sample in range(12):
        prior = rng.uniform(-4, 4, H.shape[1])
        for rule, parameter in [('spa', 1.), ('min_sum', 1.), ('normalized_min_sum', .7), ('offset_min_sum', .3)]:
            for cap, syndrome in product([0, 1, 5], product([0, 1], repeat=2)):
                s = np.asarray(syndrome, np.uint8)
                expected = oracle(prior, s, rule, parameter, cap)
                for backend in ['scalar', 'compiled']:
                    decoder = BinaryPolicyDecoder(H, BinaryPolicy(rule=rule, backend=backend,
                        parameter=ParameterAssignment(shape='scalar', value=parameter), max_iterations=cap))
                    result = decoder.decode(s, prior_llrs=prior)
                    posterior = np.asarray(result.ledger['execution']['posterior'])
                    error = float(np.max(abs(posterior-expected[1])))
                    worst = max(worst, error)
                    np.testing.assert_allclose(posterior, expected[1], atol=2e-12, rtol=2e-12)
                    np.testing.assert_array_equal(result.candidate, expected[0])
                    assert (result.iterations, result.converged) == expected[2:]
                    records.append(dict(sample=sample, prior=prior.tolist(), syndrome=s.tolist(), rule=rule,
                        parameter=parameter, cap=cap, backend=backend, candidate=result.candidate.tolist(),
                        iterations=result.iterations, converged=result.converged, posterior_error=error))
    (HERE/'ordinary-cases.json').write_text(json.dumps(records, indent=2)+'\n')
    return dict(cases=len(records), max_error=worst, seed=5001, tolerance=2e-12)


def quantize(value, resolution):
    if resolution.format.startswith('int'):
        bits = int(resolution.format[3:])
        bound = (2**(bits-1)-1)/resolution.scale
        return float(np.clip(np.rint(value*resolution.scale)/resolution.scale, -bound, bound))
    dtype = getattr(np, resolution.format)
    return float(dtype(np.clip(value, -np.finfo(dtype).max, np.finfo(dtype).max)))


def precision_reference(prior, syndrome, policy, cap):
    edges = list(zip(*np.nonzero(H)))
    q = lambda x: quantize(x, policy.resolution)
    co = q if policy.resolution.coefficients == 'same' else float
    old_weight, fresh_weight, alpha, beta = map(co, [policy.damping, 1-policy.damping, policy.alpha, policy.beta])
    posterior = np.array([q(x) if policy.resolution.scope == 'all_state' else x for x in prior])
    candidate = (posterior < 0).astype(np.uint8)
    valid = lambda: np.array_equal(H@candidate % 2, syndrome)
    if policy.zero_syndrome_shortcut and valid():
        return candidate, posterior, 0, True
    old = np.array([q(prior[v]) for _, v in edges])
    for iteration in range(1, cap+1):
        messages = []
        for e, (check, _) in enumerate(edges):
            incoming = [old[j] for j,(c,_) in enumerate(edges) if c == check and j != e]
            buckets = [[], []]
            for assignment in product([0,1], repeat=len(incoming)):
                cost = float(np.dot(assignment, incoming))
                buckets[(int(syndrome[check])-sum(assignment)) % 2].append(cost)
            if policy.check_rule == 'sum_product':
                message = logsumexp(-np.asarray(buckets[0])) - logsumexp(-np.asarray(buckets[1]))
            else:
                message = min(buckets[1])-min(buckets[0])
                message = math.copysign(alpha*max(0., abs(message)-beta), message)
            messages.append(q(message))
        posterior = prior.copy()
        for e,(_,v) in enumerate(edges):
            posterior[v] += messages[e]
        if policy.resolution.scope == 'all_state':
            posterior = np.array([q(x) for x in posterior])
        candidate = (posterior < 0).astype(np.uint8)
        old = np.array([q(old_weight*old[e] + fresh_weight*q(posterior[v]-messages[e])) for e,(_,v) in enumerate(edges)])
        if valid():
            return candidate, posterior, iteration, True
    return candidate, posterior, cap, bool(valid())


def precision_factors():
    rng = np.random.default_rng(5002)
    priors = [rng.uniform(-4,4,H.shape[1]) for _ in range(4)]
    records, worst = [], 0.
    for fmt, scope, rule in product(['float16','float32','float64','int8','int16','int32'],
                                  ['scalar_edges','all_messages','all_state'], ['sum_product','min_sum']):
        fp = BpFloodingPolicy(check_rule=rule, resolution=ResolutionPolicy(fmt,8 if fmt.startswith('int') else None,scope,'same'),
            damping=.25, alpha=.75 if rule=='min_sum' else 1., beta=.125 if rule=='min_sum' else 0.,
            version='bp-flooding-policy-v3' if rule=='sum_product' else 'bp-flooding-policy-v2',
            check_stabilization='log_domain' if rule=='sum_product' else 'exact_unity',product_epsilon=1e-10)
        for sample, cap, bits in product(range(4), [0,1,4], product([0,1],repeat=2)):
            prior, syndrome = priors[sample], np.array(bits,np.uint8)
            decoder = BinaryPolicyDecoder(H, BinaryPolicy(flooding_policy=fp, max_iterations=cap))
            result = decoder.decode(syndrome,prior_llrs=prior)
            expected = precision_reference(prior,syndrome,fp,cap)
            posterior = np.array(result.ledger['execution']['posterior'])
            error = float(np.max(abs(posterior-expected[1])))
            worst = max(worst,error)
            np.testing.assert_allclose(posterior,expected[1],atol=2e-12,rtol=2e-12)
            np.testing.assert_array_equal(result.candidate,expected[0])
            assert (result.iterations,result.converged)==expected[2:]
            records.append(dict(format=fmt,scope=scope,rule=rule,sample=sample,prior=prior.tolist(),
                syndrome=list(bits),cap=cap,posterior_error=error,candidate=result.candidate.tolist(),iterations=result.iterations))
    (HERE/'precision-cases.json').write_text(json.dumps(records,indent=2)+'\n')
    return dict(cases=len(records),max_error=worst,seed=5002,tolerance=2e-12)


def carried_mathematics():
    path = HERE.parent/'043-circuit-cuda-mathematics/results.json'
    record = json.loads(path.read_text())
    names=['quaternary/kernel.py','quaternary/compiled.py','quaternary/numerics.py','quaternary/mbp4.py',
           'quaternary/qbpgd.py','quaternary/asced.py','canonical/compiled.py','check_numerics.py','resolution.py','gpu.py']
    checked = []
    for name in names:
        relative='src/bp_registry/'+name
        if relative not in record['source_hashes']:
            continue
        assert sha256((ROOT/relative).read_bytes()).hexdigest()==record['source_hashes'][relative],relative
        checked.append(relative)
    return dict(source_files=checked,receipt_sha256=sha256(path.read_bytes()).hexdigest(),
        carried_cases='192 exact Pauli trees,100 covariance cases,8 CUDA simulator trees; prior source-qualified named policies remain separately scoped')


if __name__=='__main__':
    audit=Audit(HERE)
    audit.probe('independent_ordinary_factors',ordinary_factors)
    audit.probe('independent_precision_factors',precision_factors)
    audit.probe('unchanged_family_math',carried_mathematics)
    audit.finish()
