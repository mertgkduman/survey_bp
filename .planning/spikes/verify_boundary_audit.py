"""Verify boundary audit integrity without treating known failures as passes."""
from pathlib import Path
from hashlib import sha256
import gzip,json,subprocess
import xml.etree.ElementTree as ET
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EXPECTED={19:{'known_default_approximation_not_global_exact_SPA'},20:set(),
          21:{'B01_alternate_graph_construction_preserves_admission','B01_schedule_profile_agrees_with_kernel_profile',
              'B02_low_level_serial_honors_or_rejects_v3_damping'},
          22:{'B03_compiled_BP4_honors_accepted_v1_saturation'}}


def main():
    checks=passed=0
    for number,failures in EXPECTED.items():
        directory=next(BASE.glob(f'{number:03d}-*'))
        data=json.loads((directory/'results.json').read_text())
        for path,digest in data['source_hashes'].items():
            assert sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
        assert {e['name'] for e in data['events'] if not e['passed']}==failures
        assert data['checks']==len(data['events'])
        assert data['passed']==sum(e['passed'] for e in data['events'])
        checks+=data['checks'];passed+=data['passed']
    directory=BASE/'022-cpu-graph-integrity'
    ledger=directory/'events.jsonl.gz';count=0
    with gzip.open(ledger,'rt') as stream:
        for line in stream:
            row=json.loads(line);h=np.array(row['checks']);c=np.array(row['candidate']);s=np.array(row['syndrome'])
            measured=(h@c)%2 if row['family']=='binary' else np.sum((h!=0)&(c[None,:]!=0)&(h!=c[None,:]),axis=1)%2
            assert row['candidate_valid']==bool(np.array_equal(measured,s))
            assert row['work']['bp_calls']==row['iterations']
            count+=1
    assert count==840
    suites=ET.parse(directory/'regression.xml').getroot().findall('testsuite')
    assert sum(int(s.attrib['tests']) for s in suites)==183
    assert all(int(s.attrib[k])==0 for s in suites for k in ('failures','errors','skipped'))
    subprocess.run(['git','diff','--exit-code','e7a0387','--','src'],cwd=ROOT,check=True,capture_output=True)
    old_dirs=[str(p.relative_to(ROOT)) for number in range(8,19) for p in BASE.glob(f'{number:03d}-*') if p.is_dir()]
    subprocess.run(['git','diff','--exit-code','e7a0387','--',*old_dirs],cwd=ROOT,check=True,capture_output=True)
    report=dict(production_unchanged=True,prior_spikes_unchanged=True,grouped_checks=checks,passed=passed,
                retained_failed_assertions=checks-passed,independently_rechecked_ledger_rows=count,
                ledger_sha256=sha256(ledger.read_bytes()).hexdigest(),selected_regressions_passed=183)
    (BASE/'BOUNDARY-AUDIT-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
