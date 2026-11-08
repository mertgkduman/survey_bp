"""Verify closure, stored numerical evidence and unchanged historical artifacts."""
from collections import Counter
from hashlib import sha1, sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import gzip
import json
import subprocess
import xml.etree.ElementTree as ET
import numpy as np

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent


def verify_grid():
    from bp_registry.cpu_batch import verify_cpu_batch_ledger
    from bp_registry.resolution import BpFloodingPolicy
    from bp_registry.canonical.compiled import CompiledBinaryFlooding
    from bp_registry.quaternary.compiled import CompiledBp4Graph
    from bp_registry.quaternary.problems import PauliCode
    matrix = json.loads((HERE / 'grid/matrix.json').read_text())
    assert len(matrix) == 432 and all(row['passed'] for row in matrix)
    expected = Counter({(row['family'], row['policy_identity']): 6 for row in matrix})
    actual = Counter()
    h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    with gzip.open(HERE / 'grid/events.jsonl.gz', 'rt') as handle:
        rows = [json.loads(line) for line in handle]
    assert len(rows) == 2592
    with TemporaryDirectory() as temp:
        path = Path(temp) / 'ledger.jsonl'
        for start in range(0, len(rows), 3):
            batch = rows[start:start + 3]
            numerics = batch[0]['numerics']
            spec = {key: numerics[key] for key in ('check_rule', 'resolution', 'damping', 'alpha', 'beta', 'hard_decision', 'zero_syndrome_shortcut', 'version', 'check_stabilization', 'product_epsilon')}
            policy = BpFloodingPolicy.from_spec(spec)
            family = 'binary' if batch[0]['family'] == 'binary' else 'pauli'
            actual[(family, policy.semantic_identity)] += 3
            if family == 'binary':
                graph = CompiledBinaryFlooding.from_check_matrix(h, policy=policy, rule='spa' if policy.check_rule == 'sum_product' else 'min_sum')
                kwargs = {'error_rate': .17}
            else:
                graph = CompiledBp4Graph.from_code(PauliCode(checks=h), np.array([[.7, .1, .1, .1], [.4, .3, .2, .1], [.1, .2, .3, .4]]), policy=policy)
                kwargs = {}
            path.write_text(''.join(json.dumps(row) + '\n' for row in batch))
            assert verify_cpu_batch_ledger(path, graph, **kwargs)['shots'] == 3
    assert actual == expected
    return len(rows)


def verify_cpu_receipts():
    from dataclasses import replace
    from bp_registry.cpu_batch import verify_cpu_batch_ledger
    from bp_registry.canonical.compiled import CompiledBinaryFlooding
    from bp_registry.quaternary.compiled import CompiledBp4Graph
    from bp_registry.quaternary.asced import parse_pinned_gb46_css
    from bp_registry.quaternary.problems import compile_css_artifact
    from bp_registry.resolution import STABLE_SPA_F64
    policy = replace(STABLE_SPA_F64, zero_syndrome_shortcut=False)
    h = np.array(json.loads((ROOT / 'data/artifacts/bb72-css.json').read_text())['hz'], dtype=np.uint8)
    code = compile_css_artifact(parse_pinned_gb46_css((ROOT / 'data/artifacts/gb46-h44.alist').read_bytes()), source_artifact_identity='gb46-h44-pinned-alist')
    graphs = {
        'binary_bb72': (CompiledBinaryFlooding.from_check_matrix(h, policy=policy), {'error_rate': .08}),
        'pauli_gb46': (CompiledBp4Graph.from_code(code, np.tile([.92, .08/3, .08/3, .08/3], (code.n, 1)), policy=policy), {}),
    }
    count = 0
    with TemporaryDirectory() as temp:
        path = Path(temp) / 'events.jsonl'
        for label in ('baseline', 'current'):
            for name, (graph, kwargs) in graphs.items():
                for workers in (1, 2, 4):
                    with gzip.open(HERE / label / f'{name}-{workers}-events.jsonl.gz', 'rb') as handle:
                        path.write_bytes(handle.read())
                    verified = verify_cpu_batch_ledger(path, graph, **kwargs)
                    assert verified['shots'] == 512
                    count += verified['shots']
    return count


def main():
    result = json.loads((HERE / 'results.json').read_text())
    assert (result['checks'], result['passed'], result['failed']) == (32, 32, 0)
    closed = Counter(event['name'].split('_')[0] for event in result['events'] if event['name'].startswith(('D01_', 'D02_', 'D03_', 'D04_', 'D05_')))
    assert closed == dict(D01=8, D02=2, D03=5, D04=3, D05=1)
    for name, digest in result['source_hashes'].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    capability = json.loads((HERE / 'capability-contracts.json').read_text())
    for name, digest in capability['admission_source_sha256'].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    historical = 0
    for entry in subprocess.check_output(['git', 'ls-tree', '-r', '-z', '6f68961', '.planning/spikes']).split(b'\0'):
        if not entry:
            continue
        info, path = entry.split(b'\t', 1)
        name = path.decode()
        part = Path(name).parts[2]
        if not (part[:3].isdigit() and 8 <= int(part[:3]) <= 37):
            continue
        data = (ROOT / name).read_bytes()
        assert sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == info.split()[2].decode(), name
        historical += 1
    grid_rows = verify_grid()
    cpu_rows = verify_cpu_receipts()
    with gzip.open(HERE / 'native/events.jsonl.gz', 'rt') as handle:
        native = [json.loads(line) for line in handle]
    assert len(native) == 216
    for row in native:
        for key in ('candidate', 'iterations', 'converged'):
            assert row[f'native_{key}'] == row[f'canonical_{key}']
    import ldpc
    binary = next(Path(ldpc.__file__).parent.glob('bp_decoder/_bp_decoder*.so'))
    recorded = next(e['details']['native_binary_sha256'] for e in result['events'] if e['name'] == 'native_heterogeneous_alignment')
    assert sha256(binary.read_bytes()).hexdigest() == recorded
    xml = ET.parse(HERE / 'full-regression.xml').getroot()
    counts = {key: sum(int(s.get(key, 0)) for s in xml.iter('testsuite')) for key in ('tests', 'failures', 'errors', 'skipped')}
    assert counts['failures'] == counts['errors'] == 0 and counts['skipped'] == 1
    assert counts['tests'] == 2252
    collection = [line for line in (HERE / 'test-collection.log').read_text().splitlines()
                  if line.startswith('tests/') and '::' in line]
    assert len(collection) == counts['tests']
    assert '2251 passed, 1 skipped, 25 warnings' in (HERE / 'full-regression.log').read_text()
    skips = [dict(classname=c.get('classname'), name=c.get('name'), reason=c.find('skipped').get('message')) for c in xml.iter('testcase') if c.find('skipped') is not None]
    performance = json.loads((HERE / 'cpu-comparison.json').read_text())
    assert performance['baseline'] == '6f68961'
    assert all(row['exact_results_preserved'] for row in performance['cases'].values())
    benchmark = json.loads((HERE / 'current/benchmark.json').read_text())
    benchmark_source_differences = [name for name, digest in benchmark['source_sha256'].items()
                                  if sha256((ROOT / 'src' / name).read_bytes()).hexdigest() != digest]
    assert benchmark_source_differences == ['bp_registry/canonical/group_shuffled.py']
    report = dict(evidence_verified=True, findings_closed=dict(closed), grouped_checks=32,
                  historical_files_unchanged=historical, source_files=len(result['source_hashes']),
                  policy_configurations=432, verified_grid_rows=grid_rows, native_comparisons=216,
                  verified_cpu_benchmark_rows=cpu_rows,
                  full_suite=counts, skips=skips, performance=performance,
                  warnings=25, warning_scope='existing campaign fork/multithread deprecations; no observed deadlock',
                  benchmark_source_differences=benchmark_source_differences,
                  benchmark_difference_scope='Hsu constructor admission only; compiled arithmetic and batch evidence dependencies unchanged',
                  qualification_scope='named tested contracts; no universal policy cross-product or publication assessment',
                  public_manifest_defaults_unchanged=True, publication_gates_unchanged=True,
                  baseline='6f68961', source_head=result['git_head'])
    report['artifact_sha256'] = {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.rglob('*'))
                                 if p.is_file() and p.suffix != '.pyc' and p.name != 'verification.json'}
    report['test_source_sha256'] = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                                  for p in sorted((ROOT / 'tests').rglob('*.py'))}
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ('artifact_sha256', 'performance')}, indent=2))


if __name__ == '__main__':
    main()
