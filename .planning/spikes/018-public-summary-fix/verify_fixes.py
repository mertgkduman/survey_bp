"""Validate current qualification and preserve historical evidence identities."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASELINE = '422da15'


def historical(path):
    return subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT)


def main():
    qualification = json.loads((HERE / 'results.json').read_text())
    for path, digest in qualification['source_hashes'].items():
        assert sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    assert qualification['checks'] == qualification['passed'] == 18
    assert qualification['failed'] == 0
    suites = {}
    for name, path in [('admission', HERE.parent / '016-scalar-admission-fix/green.xml'),
                       ('profiles', HERE.parent / '017-profile-evidence-fix/green.xml'),
                       ('profile_compatibility', HERE.parent / '017-profile-evidence-fix/alias-regression.xml'),
                       ('summaries', HERE / 'green.xml'), ('regression', HERE / 'regression.xml')]:
        items = ET.parse(path).getroot().findall('testsuite')
        counts = {key: sum(int(item.attrib[key]) for item in items)
                  for key in ('tests', 'failures', 'errors', 'skipped')}
        assert counts['tests'] > 0 and counts['failures'] == counts['errors'] == 0
        suites[name] = counts
    assert [suites[key]['tests'] for key in ('admission', 'profiles', 'summaries')] == [76, 247, 125]
    assert suites['profile_compatibility']['tests'] == 159
    assert suites['regression']['tests'] >= 1000
    old_directories = [str(path.relative_to(ROOT)) for number in range(8, 16)
                       for path in HERE.parent.glob(f'{number:03d}-*') if path.is_dir()]
    subprocess.run(['git', 'diff', '--exit-code', BASELINE, '--', *old_directories], cwd=ROOT, check=True, capture_output=True)
    # Exact bodies of compiled arithmetic/decoding functions are unchanged.
    functions = lambda source: {node.name: ast.dump(node, include_attributes=False)
                               for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    for path in ('src/bp_registry/canonical/compiled.py', 'src/bp_registry/canonical/numerics.py',
                 'src/bp_registry/quaternary/numerics.py'):
        assert functions(historical(path)) == functions((ROOT / path).read_bytes()), path
    unchanged = ['src/bp_registry/quaternary/compiled.py', 'src/bp_registry/cpu_batch.py',
                 'src/bp_registry/check_numerics.py', 'src/bp_registry/resolution.py']
    for path in unchanged:
        assert historical(path) == (ROOT / path).read_bytes(), path
    report = dict(production_source_hashes='verified', historical_spikes='008-015 unchanged',
                  qualification_revision=qualification['git_head'], grouped_checks_passed=18,
                  suites=suites, test_sets_overlap=True, compiled_hot_functions='unchanged',
                  unchanged_execution_modules=unchanged, new_performance_claim=False)
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
