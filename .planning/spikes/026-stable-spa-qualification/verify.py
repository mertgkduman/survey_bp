"""Verify current-source qualification, immutable historical evidence and ledgers."""
from pathlib import Path
from hashlib import sha256
import gzip,json,subprocess
import xml.etree.ElementTree as ET
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def main():
    current={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/bp_registry').rglob('*.py')}
    qualification=json.loads((HERE/'results.json').read_text())
    assert qualification['failed']==0 and qualification['checks']==14
    assert qualification['source_hashes']==current
    benchmark=json.loads((HERE/'benchmark.json').read_text())
    assert benchmark['source_sha256']==current
    suite=ET.parse(HERE/'regression.xml').getroot().find('testsuite')
    assert int(suite.attrib['tests'])>=1369
    assert suite.attrib['failures']==suite.attrib['errors']=='0'
    assert suite.attrib['skipped']=='1'
    old_dirs=[str(p.relative_to(ROOT)) for p in HERE.parent.iterdir() if p.is_dir() and p.name[:3].isdigit() and 8<=int(p.name[:3])<=22]
    subprocess.run(['git','diff','--exit-code','02d165e','--',*old_dirs],cwd=ROOT,check=True,stdout=subprocess.PIPE)
    boundary_counts={}
    for path in (HERE/'events.jsonl.gz',HERE/'stable-controls/events.jsonl.gz'):
        rows=[json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
        assert len(rows)==840
        for row in rows:
            h=np.array(row['checks']); c=np.array(row['candidate']); s=np.array(row['syndrome'])
            actual=(h@c)%2 if row['family']=='binary' else np.sum((h!=0)&(c[None,:]!=0)&(h!=c[None,:]),axis=1)%2
            assert row['candidate_valid']==bool(np.array_equal(actual,s))
            assert row['work']['check_to_variable_updates']==int(np.count_nonzero(h))*row['iterations']
        boundary_counts[str(path.relative_to(HERE))]=len(rows)
    inputs=np.load(HERE/'benchmark-inputs.npz')
    from bp_registry.quaternary.asced import parse_pinned_gb46_css
    from bp_registry.quaternary.problems import compile_css_artifact
    h=np.array(json.loads((ROOT/'data/artifacts/bb72-css.json').read_text())['hz'])
    code=compile_css_artifact(parse_pinned_gb46_css((ROOT/'data/artifacts/gb46-h44.alist').read_bytes()),source_artifact_identity='gb46-h44-pinned-alist')
    ledger_count=0
    for case in ('binary_bb72','pauli_gb46'):
        previous=None
        for workers in (1,4):
            rows=[json.loads(line) for line in gzip.decompress((HERE/f'{case}-{workers}-events.jsonl.gz').read_bytes()).splitlines()]
            assert len(rows)==benchmark['shots']
            syndromes=inputs['binary_syndromes' if case=='binary_bb72' else 'pauli_syndromes']
            for i,row in enumerate(rows):
                np.testing.assert_array_equal(row['syndrome'],syndromes[i])
                candidate=np.array(row['candidate'],dtype=np.uint8)
                actual=(h@candidate)%2 if case=='binary_bb72' else code.syndrome(candidate)
                assert row['candidate_valid']==bool(np.array_equal(actual,syndromes[i]))
                assert row['numerics']==benchmark['cases'][case]['numerics']
                work=row['work'];it=row['iterations'];n=len(candidate)
                assert work['candidate_constructions']==it+1
                assert work['candidate_checks']==n*(it+1)
                assert work['belief_assemblies']==n*it
                assert work['check_to_variable_updates']==work['variable_to_check_updates']==row['edge_count']*it
                assert work['convergence_checks']==it+int(not(it>0 and row['candidate_valid']))
            outcomes=[(r['candidate'],r['iterations'],r['candidate_valid'],r['work']) for r in rows]
            if previous is not None: assert previous==outcomes
            previous=outcomes;ledger_count+=len(rows)
    artifacts={str(p.relative_to(HERE)):sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name!='verification.json' and '__pycache__' not in str(p)}
    result=dict(passed=True,regression_tests=int(suite.attrib['tests']),regression_skipped=1,
        independent_probes=14,boundary_ledgers=boundary_counts,benchmark_ledger_rows=ledger_count,
        historical_spikes_008_022_unchanged=True,source_hashes=current,artifact_hashes=artifacts)
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('hashes')}))

if __name__=='__main__':main()
