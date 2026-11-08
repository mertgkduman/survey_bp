"""Verify evidence integrity without relabeling confirmed kernel defects as passes."""
from pathlib import Path
from hashlib import sha256,sha1
from collections import Counter
import gzip,json,subprocess,re
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path.cwd();HERE=ROOT/'.planning/spikes'
FOLDERS=['034-completeness-mathematics','035-completeness-upstream','036-completeness-policies','037-completeness-execution']

def main():
    results=[json.loads((HERE/f/'results.json').read_text()) for f in FOLDERS]
    results.append(json.loads((HERE/FOLDERS[2]/'grid/results.json').read_text()))
    assert [(r['checks'],r['passed'],r['failed']) for r in results]==[(3,3,0),(1,1,0),(14,4,10),(13,4,9),(1,1,0)]
    findings=Counter(e['name'].split('_')[0] for r in results for e in r['events'] if not e['passed'])
    assert findings==dict(D01=8,D02=2,D03=5,D04=3,D05=1),findings
    import ldpc
    binary=next(Path(ldpc.__file__).parent.glob('bp_decoder/_bp_decoder*.so'))
    assert sha256(binary.read_bytes()).hexdigest()==results[1]['events'][0]['details']['native_binary_sha256']
    for r in results:
        for name,digest in r['source_hashes'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    assert not subprocess.check_output(['git','diff','4cce08e','--','src','tests'])
    historical=0
    for entry in subprocess.check_output(['git','ls-tree','-r','-z','4cce08e','.planning/spikes']).split(b'\0'):
        if not entry:continue
        info,path=entry.split(b'\t',1);name=path.decode();part=Path(name).parts[2]
        if not(part[:3].isdigit() and 8<=int(part[:3])<=33):continue
        data=(ROOT/name).read_bytes()
        assert sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==info.split()[2].decode(),name
        historical+=1
    xml=ET.parse(HERE/FOLDERS[3]/'full-regression.xml').getroot()
    counts={key:sum(int(s.get(key,0)) for s in xml.iter('testsuite')) for key in ('tests','failures','errors','skipped')}
    assert counts==dict(tests=2110,failures=0,errors=0,skipped=1),counts
    log=(HERE/FOLDERS[3]/'full-regression.log').read_text()
    assert '2109 passed, 1 skipped, 25 warnings' in log
    collection=[line for line in (HERE/FOLDERS[3]/'test-collection.log').read_text().splitlines() if line.startswith('tests/') and '::' in line]
    assert len(collection)==counts['tests']
    skips=[dict(classname=c.get('classname'),name=c.get('name'),reason=c.find('skipped').get('message')) for c in xml.iter('testcase') if c.find('skipped') is not None]
    matrix=json.loads((HERE/FOLDERS[2]/'grid/matrix.json').read_text());assert len(matrix)==432 and all(row['passed'] for row in matrix)
    from bp_registry.resolution import BpFloodingPolicy
    expected=Counter({(row['family'],row['policy_identity']):6 for row in matrix});actual=Counter();h=np.array([[1,1,0],[0,1,1]],dtype=np.uint8)
    with gzip.open(HERE/FOLDERS[2]/'grid/events.jsonl.gz','rt') as handle:
        rows=[json.loads(line) for line in handle]
    for row in rows:
        assert row['assessment_status']=='not_assessed'
        spec={k:row['numerics'][k] for k in ('check_rule','resolution','damping','alpha','beta','hard_decision','zero_syndrome_shortcut','version','check_stabilization','product_epsilon')}
        p=BpFloodingPolicy.from_spec(spec);family='binary' if row['family']=='binary' else 'pauli'
        actual[(family,p.semantic_identity)]+=1
        candidate=np.array(row['candidate']);bits=candidate if family=='binary' else np.isin(candidate,[2,3]).astype(np.uint8)
        valid=np.array_equal(h@bits%2,row['syndrome']);assert valid==row['candidate_valid']
        assert row['iterations']==row['work']['bp_calls']
    assert actual==expected and len(rows)==2592
    with gzip.open(HERE/FOLDERS[1]/'events.jsonl.gz','rt') as handle:
        native_rows=[json.loads(line) for line in handle]
    assert len(native_rows)==216
    for row in native_rows:
        assert row['native_candidate']==row['canonical_candidate']
        assert row['native_iterations']==row['canonical_iterations']
        assert row['native_converged']==row['canonical_converged']
        assert row['assessment_status']=='not_assessed'
    mutated=json.loads((HERE/FOLDERS[3]/'mutated-batch-event.json').read_text())
    assert mutated['candidate_valid'] and mutated['candidate'][0]!=mutated['syndrome'][0]
    report=dict(evidence_verified=True,kernel_freeze_ready=False,baseline='4cce08e',production_and_tests_unchanged=True,
        groups=32,passing_groups=13,failed_invariants=19,findings=dict(findings),
        full_suite=counts,warnings=25,warning_scope="fork from multithreaded campaign test process; no observed deadlock",native_comparison_rows=216,skips=skips,historical_files_unchanged=historical,
        source_files=len(results[0]['source_hashes']),policy_configurations=432,verified_grid_ledger_rows=len(rows),
        command='NUMBA_NUM_THREADS=4 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests --junitxml=.planning/spikes/037-completeness-execution/full-regression.xml',
        artifact_sha256={str(p.relative_to(HERE)):sha256(p.read_bytes()).hexdigest() for f in FOLDERS for p in sorted((HERE/f).rglob('*')) if p.is_file() and p.suffix!='.pyc'})
    for name in ('CANONICAL-KERNEL-COMPLETENESS-AUDIT.md','verify_completeness_audit.py'):
        report['artifact_sha256'][name]=sha256((HERE/name).read_bytes()).hexdigest()
    (HERE/'COMPLETENESS-AUDIT-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('artifact_sha256','skips')},indent=2))

if __name__=='__main__':main()
