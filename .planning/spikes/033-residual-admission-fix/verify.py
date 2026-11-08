"""Verify post-fix source identity, regressions, retained history and CPU evidence."""
from pathlib import Path
from hashlib import sha256, sha1
import gzip, json, subprocess, tarfile
from io import BytesIO
import xml.etree.ElementTree as ET

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent


def main():
    result = json.loads((HERE/'results.json').read_text())
    assert (result['checks'], result['passed'], result['failed']) == (18,18,0)
    for name, digest in result['source_hashes'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    suites = ET.parse(HERE/'regression.xml').getroot()
    totals = {key: sum(int(s.get(key, 0)) for s in suites.iter('testsuite')) for key in ('tests','failures','errors','skipped')}
    assert totals == dict(tests=1413, failures=0, errors=0, skipped=1), totals
    classes = [case.get('classname') for case in suites.iter('testcase')]
    for suffix, count in [('test_freeze_fixes',28), ('test_bp4_failure_contract',8), ('test_residual_admission',8)]:
        assert sum(c.endswith(suffix) for c in classes) == count
    history = subprocess.check_output(['git','ls-tree','-r','-z','729157f','.planning/spikes'])
    preserved = 0
    for entry in history.split(b'\0'):
        if not entry:
            continue
        info, path = entry.split(b'\t',1)
        name = path.decode()
        component = Path(name).parts[2]
        if not (component[:3].isdigit() and 8 <= int(component[:3]) <= 30):
            continue
        data = (ROOT/name).read_bytes()
        actual = sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert actual == info.split()[2].decode(), name
        preserved += 1
    before = json.loads((HERE/'baseline/benchmark.json').read_text())
    after = json.loads((HERE/'current/benchmark.json').read_text())
    archive = subprocess.check_output(['git','archive','729157f','src'])
    with tarfile.open(fileobj=BytesIO(archive)) as tree:
        baseline_hashes = {member.name.removeprefix('src/'):sha256(tree.extractfile(member).read()).hexdigest()
            for member in tree if member.isfile() and member.name.endswith('.py') and member.name.startswith('src/bp_registry/')}
    assert before['source_sha256'] == baseline_hashes
    for name, digest in after['source_sha256'].items():
        assert sha256((ROOT/'src'/name).read_bytes()).hexdigest() == digest, name
    assert before['inputs_sha256'] == after['inputs_sha256'] == sha256((HERE.parent/'026-stable-spa-qualification/benchmark-inputs.npz').read_bytes()).hexdigest()
    assert before['repeats'] == after['repeats'] == 15
    assert before['timing_methodology'] == after['timing_methodology']
    for report in (before,after):
        for case in report['cases'].values():
            for timings in case['timings'].values():
                assert len(timings['single']) == len(timings['batch']) == 15
    diagnostics = (HERE/'current/parallel-diagnostics.txt').read_text()
    assert diagnostics.count('Parallel structure is already optimal.') == 2
    assert diagnostics.count('for shot in prange(count):') == 2
    ledger_rows = 0
    for case in ('binary_bb72','pauli_gb46'):
        for key in ('candidate_sha256','iterations_sha256','converged_sha256','total_iterations','shots','numerics'):
            assert before['cases'][case][key] == after['cases'][case][key]
        for worker in (1,2,4):
            name = f'{case}-{worker}-events.jsonl.gz'
            a = gzip.decompress((HERE/'baseline'/name).read_bytes())
            b = gzip.decompress((HERE/'current'/name).read_bytes())
            assert a == b, name
            rows = [json.loads(line) for line in b.splitlines()]
            assert len(rows) == 512
            for index, row in enumerate(rows):
                assert row['shot_index'] == index and row['workers'] == worker
                assert row['assessment_status'] == 'not_assessed'
                assert row['work']['bp_calls'] == row['iterations']
                assert all(type(value) is int and value >= 0 for value in row['work'].values())
            ledger_rows += len(rows)*2
    report = dict(status='PASS', qualified_source_commit=result['git_head'],
        grouped_probes=18, regression_passed=totals['tests']-totals['skipped'], existing_skips=1,
        new_regressions=44, historical_files_unchanged=preserved, matched_cpu_ledger_rows=ledger_rows,
        source_files=len(result['source_hashes']),
        artifact_sha256={str(p.relative_to(HERE)):sha256(p.read_bytes()).hexdigest()
            for p in sorted(HERE.rglob('*')) if p.is_file() and p.suffix not in ('.pyc',) and p.name != 'verification.json'})
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='artifact_sha256'},indent=2))


if __name__ == '__main__':
    main()
