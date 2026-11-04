"""Evidence declarations are mandatory even when an editor rewrites file hashes."""
import json
from hashlib import sha256
from pathlib import Path

import pytest

from bp_registry.research.results import normalize_result_directory
from bp_registry.research.runner import run_experiment

ROOT = Path(__file__).resolve().parents[2]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


@pytest.mark.parametrize('mutation', ['missing_provenance', 'timing_scope'])
def test_rehashed_evidence_declarations_cannot_be_dropped_or_relabelled(tmp_path, mutation):
    spec = json.loads((ROOT/'research/examples/code-capacity.json').read_text())
    spec['rate_points'] = spec['rate_points'][:1]
    spec['sampling']['shots'] = spec['budgets']['max_shots'] = 1
    result = tmp_path/'result'
    run_experiment(spec, output=result, repository=ROOT)
    if mutation == 'timing_scope':
        path = result/'summary.json'
        payload = json.loads(path.read_text())
        payload['timing_boundaries']['decode_seconds'] = 'fabricated runtime scope'
        path.write_bytes(canonical(payload))
        pattern = 'timing boundaries'
    else:
        run = json.loads((result/'run-manifest.json').read_text())
        identity = sha256(canonical({'configuration_sha256':run['configuration_sha256'], 'implementation_sha256':'0'*64})).hexdigest()
        for name in ['run-manifest.json','status.json','summary.json','result-manifest.json']:
            path = result/name
            payload = json.loads(path.read_text())
            payload['experiment_id'] = identity
            if 'provenance' in payload:
                payload['provenance'] = {'implementation_sha256':'0'*64}
            path.write_bytes(canonical(payload))
        path = result/'effective-spec.json'
        payload = json.loads(path.read_text());payload['implementation_sha256'] = '0'*64
        path.write_bytes(canonical(payload));pattern = 'requires source hashes'
    path = result/'result-manifest.json'
    manifest = json.loads(path.read_text())
    manifest['files'] = {name:sha256((result/name).read_bytes()).hexdigest() for name in manifest['files']}
    path.write_bytes(canonical(manifest))
    with pytest.raises(ValueError, match=pattern):
        normalize_result_directory(result)
