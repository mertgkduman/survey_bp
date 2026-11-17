"""Fresh-process replay of every published OSD equivalence/pipeline event."""
import argparse
from collections import Counter
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import time

import numpy as np

from bp_registry.postprocessing.osd_v2 import Osd, _digest, _json_digest
from bp_registry.postprocessing.bp_osd_v2 import CanonicalBpOsd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'data/benchmarks/osd-v2/qualified'


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def verify(out):
    started = time.time()
    affinity = sorted(os.sched_getaffinity(0)); os.sched_setaffinity(0, {affinity[0]})
    spec = importlib.util.spec_from_file_location('_osdv2_replay_benchmark', ROOT/'scripts/benchmark_osd_v2.py')
    bench = importlib.util.module_from_spec(spec); spec.loader.exec_module(bench)
    bench.verify(out)
    analysis = json.loads((out/'analysis-manifest.json').read_text())
    assert sha(out/'manifest.json') == analysis['benchmark_manifest_sha256']
    assert sha(ROOT/'scripts/report_osd_v2.py') == analysis['script_sha256']
    for name, digest in analysis['files'].items():
        assert sha(out/name) == digest
    metadata = json.loads((out/'fixtures.json').read_text())
    groups = {g['id']: g for g in metadata['groups']}
    data = {name: bench.load_group(out, group) for name, group in groups.items()}
    inputs, counts = {}, Counter()
    with np.load(out/'fixtures.npz') as sealed:
        for name, group in groups.items():
            h, probabilities, fixtures, mixed = data[name]
            processor = Osd(h, method='OSD_0', order=0, channel_probabilities=probabilities)
            pipe = CanonicalBpOsd(processor, max_iterations=group['cap'], alpha=group['alpha'])
            for index, (s, _, posterior) in enumerate(fixtures):
                candidate, fresh, converged, iterations = pipe.bp(s)
                assert not converged and iterations == group['cap']
                assert np.array_equal(fresh, posterior)
                assert np.array_equal(candidate, sealed[name+'_bp_candidate'][index])
                inputs[name, _digest(s, 'u1'), _digest(posterior, '<f8')] = (s, posterior)
                counts['sealed_actual_bp_failure_terminal_states'] += 1
    processors = {}
    for line in (out/'equivalence-ledgers.jsonl').read_text().splitlines():
        row = json.loads(line); name, depth, score = row['group'], row['depth'], row['score']
        ledger = row['ledger']; semantic = ledger['semantic']
        s, posterior = inputs[name, semantic['syndrome_sha256'], semantic['posterior_sha256']]
        key = (name, depth, score)
        if key not in processors:
            h, p, _, _ = data[name]
            processors[key] = Osd(h, method='OSD_CS' if depth else 'OSD_0', order=depth, channel_probabilities=p, score=score)
        result = processors[key].replay(s, posterior, ledger, materialize_candidates=True)
        assert result.selected_index == semantic['selected_index']
        counts['full_osd_equivalence_ledgers_replayed'] += 1
    pipeline_cache, lookup = {}, {}
    for name, (_, _, fixtures, mixed) in data.items():
        for s in [f[0] for f in fixtures]+list(mixed):
            lookup[name, _digest(s, 'u1')] = s
    for line in (out/'pipeline-ledgers.jsonl').read_text().splitlines():
        row = json.loads(line); ledger = row['ledger']
        unsigned = {k: v for k, v in ledger.items() if k != 'ledger_sha256'}
        assert _json_digest(unsigned) == ledger['ledger_sha256']
        name, depth = row['group'], row['depth']
        syn_hash = ledger['syndrome_sha256']; key = (name, depth, syn_hash)
        if key not in pipeline_cache:
            h, p, _, _ = data[name]; group = groups[name]
            processor = Osd(h, method='OSD_CS' if depth else 'OSD_0', order=depth, channel_probabilities=p)
            pipe = CanonicalBpOsd(processor, max_iterations=group['cap'], alpha=group['alpha'])
            pipeline_cache[key] = pipe.decode(lookup[name, syn_hash])
            counts['unique_whole_pipeline_shots_recomputed'] += 1
        actual = pipeline_cache[key].ledger
        for field in ('matrix_sha256', 'channel_sha256', 'syndrome_sha256', 'bp_iterations',
                      'bp_converged', 'bp_directed_edge_updates', 'posterior_sha256', 'selected_sha256'):
            assert actual[field] == ledger[field], (name, depth, row['variant'], field)
        if ledger['osd'] is None:
            assert actual['osd'] is None
        elif row['variant'] == 'v1_full':
            assert ledger['osd']['candidate_set_sha256'] == actual['osd']['semantic']['candidate_set_sha256']
        else:
            assert ledger['osd']['semantic'] == actual['osd']['semantic']
            assert _json_digest({k: v for k, v in ledger['osd'].items() if k != 'ledger_sha256'}) == ledger['osd']['ledger_sha256']
        counts['published_pipeline_event_ledgers_verified'] += 1
    receipt = dict(schema='osd-v2-fresh-replay-v1', status='passed', counts=dict(counts),
                   benchmark_manifest_sha256=sha(out/'manifest.json'), analysis_manifest_sha256=sha(out/'analysis-manifest.json'),
                   verifier_sha256=sha(Path(__file__)), affinity=[affinity[0]],
                   slurm_job_id=os.environ.get('SLURM_JOB_ID'), slurm_cpus_per_task=os.environ.get('SLURM_CPUS_PER_TASK'),
                   elapsed_seconds=time.time()-started)
    (out/'replay-verification.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, default=DEFAULT)
    verify(parser.parse_args().output)
