"""Frozen paired full-graph QBP and binary controls on X-only errors."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import time

import numpy as np
from bp_registry.css import semantic_sha256
from common import (ROOT, REPO, ARMS, FIELDS, source, vanilla, policies,
                    bit_flip_graphs, sample, one_arm, source_hashes, compress)


def run(index, *, smoke=False):
    plan_path = ROOT / 'campaign.json'
    plan = json.loads(plan_path.read_text())
    if plan['implementation_sha256'] != source_hashes():
        raise ValueError('implementation changed after plan freeze')
    job = plan['jobs'][index]
    output = REPO / job['output']
    if smoke:
        job = {**job, 'shots': 20}
        output = ROOT / 'results' / f"smoke-{job['code']}-p{job['p']:.2f}"
    if output.exists():
        raise FileExistsError(output)
    code = source._code(job['code'])
    graphs, guard = bit_flip_graphs(code, job['p'])
    evaluator = vanilla._syndrome_evaluator(code)
    masks = vanilla._logical_masks(code)
    zero = np.zeros(code.hx.shape[0]+code.hz.shape[0], dtype=np.uint8)
    for arm in ARMS:
        one_arm(arm, graphs[arm], code, job['p'], zero)
    manifest = {'schema': 'yao-cross-code-paired-v1', **job,
                'code_semantic_sha256': semantic_sha256(code),
                'campaign_sha256': sha256(plan_path.read_bytes()).hexdigest(),
                'policies': policies(), 'excluded_state_guard': guard,
                'physical_noise': 'bit_flip_X_only', 'decoder_prior': [1-job['p'], job['p'], 0, 0],
                'pauli_order': 'I,X,Y,Z', 'implementation_sha256': source_hashes(),
                'host': platform.node(), 'platform': platform.platform(),
                'arm_timing_order': 'rotate qbp_v2,binary_v2,binary_paper by shot modulo 3',
                'stop_rule': 'fixed_shots', 'fidelity': 'controlled_missing_baseline',
                'sampler': 'PCG64 SeedSequence(seed,p*100000,global_shot)'}
    output.mkdir(parents=True)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    totals = {a: {f: 0 for f in (*FIELDS, 'iterations', 'elapsed_ns')} for a in ARMS}
    digest = sha256()
    with (output/'events.jsonl').open('x', buffering=1) as stream:
        for shot in range(job['shots']):
            truth = sample(job['seed'], code, job['p'], shot)
            syndrome = vanilla._original_syndrome(evaluator, truth)
            truth_signature = vanilla._logical_signature(truth, masks)
            records = {}
            order = ARMS[shot%3:] + ARMS[:shot%3]
            for arm in order:
                begin = time.perf_counter_ns()
                r = one_arm(arm, graphs[arm], code, job['p'], syndrome)
                elapsed = time.perf_counter_ns()-begin
                candidate = r.candidate
                if np.any(candidate > 1):
                    raise ValueError('excluded Y/Z state selected in X-only decoding')
                valid = bool(np.array_equal(vanilla._original_syndrome(evaluator, candidate), syndrome))
                if valid != r.converged:
                    raise ValueError('independent syndrome check disagrees')
                logical = valid and vanilla._logical_signature(candidate, masks) != truth_signature
                exact = valid and not logical and np.array_equal(candidate, truth)
                rec = {'type_i': not valid, 'type_ii': bool(logical), 'exact_success': bool(exact),
                       'stabilizer_success': bool(valid and not logical and not exact),
                       'iterations': r.iterations, 'elapsed_ns': elapsed,
                       'candidate_sha256': sha256(candidate.tobytes()).hexdigest()}
                records[arm] = rec
                for f in totals[arm]:
                    totals[arm][f] += int(rec[f])
            event = {'schema': 'yao-cross-code-shot-v1', 'shot': shot,
                     'error_sha256': sha256(truth.tobytes()).hexdigest(),
                     'syndrome_sha256': sha256(syndrome.tobytes()).hexdigest(), 'arms': records}
            line = json.dumps(event, sort_keys=True, separators=(',', ':'))+'\n'
            stream.write(line)
            digest.update(line.encode())
            if (shot+1)%1000 == 0:
                print(job['code'], job['p'], shot+1, {a:totals[a]['type_i']+totals[a]['type_ii'] for a in ARMS}, flush=True)
    summary = {'schema': 'yao-cross-code-summary-v1', 'shots': job['shots'], 'counts': totals,
               'manifest_sha256': sha256((output/'manifest.json').read_bytes()).hexdigest(),
               'events_sha256': digest.hexdigest(), 'stop_reason': 'fixed_shots_complete'}
    (output/'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
    compress(output)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', required=True, type=int)
    ap.add_argument('--smoke', action='store_true')
    args = ap.parse_args()
    run(args.index, smoke=args.smoke)
