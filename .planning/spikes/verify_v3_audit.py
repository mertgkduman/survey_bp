"""Verify saved audit integrity while retaining expected unresolved findings."""
from pathlib import Path
from hashlib import sha256
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).parent
expected={12:set(),13:set(),14:{'V3-A01_scalar_profile_admission_matches_declared_min_sum','V3-A02_accepted_profile_metadata_describes_execution'},15:{'V3-A03_public_verification_rejects_false_summary_fields'}}
checks=passed=0
for number,failures in expected.items():
    directory=next(BASE.glob(f'{number:03d}-*'))
    result=json.loads((directory/'results.json').read_text())
    for path,digest in result['source_hashes'].items():
        assert sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    assert {e['name'] for e in result['events'] if not e['passed']}==failures
    assert result['checks']==len(result['events'])
    assert result['passed']==sum(e['passed'] for e in result['events'])
    assert result['failed']==len(failures)
    checks+=result['checks'];passed+=result['passed']
    if number in (14,15):
        suites=ET.parse(directory/'regression.xml').getroot().findall('testsuite')
        assert sum(int(s.attrib['tests']) for s in suites)==(49 if number==14 else 114)
        assert all(int(s.attrib[k])==0 for s in suites for k in ('errors','failures','skipped'))
print(json.dumps(dict(source_hashes='verified',grouped_checks=checks,passed=passed,unresolved_findings=checks-passed,regression_tests_passed=163)))
