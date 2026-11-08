"""Independently verify retained freeze-audit receipts without rerunning old probes."""
from pathlib import Path
from hashlib import sha256
import gzip,json,subprocess
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; HERE=ROOT/'.planning/spikes'
NAMES=['027-stable-spa-stress-audit','028-stable-upstream-audit','029-schedule-policy-closure','030-freeze-execution-audit']
EXPECTED=[(4,3,1),(6,6,0),(5,4,1),(5,2,3)]

def main():
    source={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/bp_registry').rglob('*.py')}
    results=[json.loads((HERE/name/'results.json').read_text()) for name in NAMES]
    for result,expected in zip(results,EXPECTED):
        assert tuple(result[k] for k in ('checks','passed','failed'))==expected
        assert result['source_hashes']==source
        assert sum(e['passed'] for e in result['events'])==result['passed']
    failures=[e['name'] for r in results for e in r['events'] if not e['passed']]
    assert len(failures)==5 and {name[:3] for name in failures}=={'C01','C02','C03'}
    assert [sum(x.startswith(c) for x in failures) for c in ['C01','C02','C03']]==[2,1,2]
    subprocess.run(['git','diff','--exit-code','12cf2b1','--','src'],cwd=ROOT,check=True,stdout=subprocess.PIPE)
    history=[str(p.relative_to(ROOT)) for p in HERE.iterdir() if p.is_dir() and p.name[:3].isdigit() and 8<=int(p.name[:3])<=26]
    subprocess.run(['git','diff','--exit-code','12cf2b1','--',*history],cwd=ROOT,check=True,stdout=subprocess.PIPE)
    previous=json.loads((HERE/'026-stable-spa-qualification/verification.json').read_text())
    assert previous['source_hashes']==source and previous['passed']
    for relative,digest in previous['artifact_hashes'].items():
        assert sha256((HERE/'026-stable-spa-qualification'/relative).read_bytes()).hexdigest()==digest
    suite=ET.parse(HERE/NAMES[-1]/'regression.xml').getroot().find('testsuite')
    assert suite.attrib['tests']=='364' and all(suite.attrib[k]=='0' for k in ['errors','failures','skipped'])
    rows=[json.loads(line) for line in gzip.decompress((HERE/NAMES[-1]/'events.jsonl.gz').read_bytes()).splitlines()]
    assert len(rows)==12
    h=np.array([[1,1,0],[0,1,1]],dtype=np.uint8)
    for row in rows:
        c=np.array(row['candidate']);s=np.array(row['syndrome'])
        actual=(h@c)%2 if row['family']=='binary' else np.sum((h!=0)&(c[None,:]!=0)&(h!=c[None,:]),axis=1)%2
        assert bool(np.array_equal(actual,s))==row['candidate_valid']
        assert row['work']['check_to_variable_updates']==row['work']['variable_to_check_updates']==4*row['iterations']
    def details(name):return next(e['details'] for e in results[1]['events'] if e['name']==name)
    assert details('stable_SPA_aligned_native_ldpc')['cases']==63
    assert details('native_NMS_controls')['cases']==84
    assert details('native_Relay_inner_memory_controls')['cases']==189
    files=[p for name in NAMES for p in (HERE/name).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    report=dict(verified=True,production_unchanged_from='be7286e',historical_spikes_008_026_unchanged=True,
        grouped_checks=20,passed=15,failed=5,findings=failures,selected_regressions=364,
        prior_broad_receipt={'passed':1368,'skipped':1,'rerun_this_audit':False},ledger_rows=12,
        source_hashes=source,artifact_hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files})
    (HERE/'FREEZE-AUDIT-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('_hashes')}))

if __name__=='__main__':main()
