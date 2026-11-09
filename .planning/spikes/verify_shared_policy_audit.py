"""Verify evidence integrity; expected diagnostic findings remain failures."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
SPIKES=ROOT/'.planning/spikes'
expected={
    '050-shared-mathematics':(3,3,0),
    '051-shared-upstream':(2,2,0),
    '052-shared-policy-closure':(4,3,1),
    '053-shared-evidence':(3,2,1),
}
receipts={}
for name,counts in expected.items():
    path=SPIKES/name/'results.json'
    result=json.loads(path.read_text())
    assert tuple(result[k] for k in ['checks','passed','failed'])==counts,name
    for relative,digest in result['source_hashes'].items():
        assert sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
    receipts[name]=dict(checks=counts[0],passed=counts[1],failed=counts[2],
        source_hashes_verified=len(result['source_hashes']),sha256=sha256(path.read_bytes()).hexdigest())
assert not subprocess.check_output(['git','diff','d031436','--','src','tests','pyproject.toml'],cwd=ROOT)
for folder,file,count in [
    ('050-shared-mathematics','ordinary-cases.json',1152),
    ('050-shared-mathematics','precision-cases.json',1728),
    ('051-shared-upstream','ldpc-cases.json',972),
    ('051-shared-upstream','relay-cases.json',216),
    ('052-shared-policy-closure','matrix.json',432),
    ('052-shared-policy-closure','controllers.json',216),
]:
    assert len(json.loads((SPIKES/folder/file).read_text()))==count,(folder,file)
f01=json.loads((SPIKES/'052-shared-policy-closure/fixed-prior-counterexample.json').read_text())
assert len(f01)==3 and all(row['fresh_changed'] and row['all_outputs_identical'] for row in f01)
f02=json.loads((SPIKES/'053-shared-evidence/chunking-counterexample.json').read_text())
for row in f02['records']:
    assert all(row['full_valid'])
    assert bool(row['different_shots'])==(row['scope'] in ['attempt','sweep'])
regression=SPIKES/'053-shared-evidence/regression.log'
assert '290 passed' in regression.read_text().splitlines()[-1]
evidence={}
for name in expected:
    for path in sorted((SPIKES/name).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            evidence[str(path.relative_to(SPIKES))]=sha256(path.read_bytes()).hexdigest()
out=dict(schema='shared-policy-audit-verification-v1',production_baseline='d031436',
    source_unchanged=True,receipts=receipts,evidence_sha256=evidence,
    fresh_regression_passed=290,open_findings=['F01','F02'],
    overall='PARTIAL: audit completed; two material contract findings remain open',
    distinction='Verification success validates evidence integrity, not the failed production invariants.')
(SPIKES/'SHARED-POLICY-AUDIT-VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['source_unchanged','fresh_regression_passed','open_findings','overall']}))
