"""Check saved source/test evidence and independently validate CPU ledger outputs."""
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.problems import compile_css_artifact

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'.planning/debug'
BENCH=BASE/'kernel-cpu-benchmark-qualified'


def main():
    report=json.loads((BENCH/'report.json').read_text())
    for path,digest in report['source_sha256'].items():
        assert sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    tests={}
    for name,count,skipped in [('regression',985,1),('final',276,0),('legacy-guards',87,0)]:
        suites=ET.parse(BASE/f'kernel-stabilization-{name}.xml').getroot().findall('testsuite')
        assert sum(int(s.attrib['tests']) for s in suites)==count
        assert sum(int(s.attrib['skipped']) for s in suites)==skipped
        assert all(int(s.attrib[key])==0 for s in suites for key in ('failures','errors'))
        tests[name]={'passed':count-skipped,'skipped':skipped}
    h=np.asarray(json.loads((ROOT/'data/artifacts/bb72-css.json').read_text())['hz'],dtype=np.int64)
    code=compile_css_artifact(parse_pinned_gb46_css((ROOT/'data/artifacts/gb46-h44.alist').read_bytes()),source_artifact_identity='gb46-h44-pinned-alist')
    inputs=np.load(BENCH/'inputs.npz')
    checked=0
    for case,entry in report['cases'].items():
        binary=case.startswith('bb72')
        checks=h if binary else code.checks
        syndromes=inputs['binary_syndromes' if binary else 'pauli_syndromes']
        previous=None
        for workers in ('1','4'):
            rows=[json.loads(line) for line in (BENCH/f'{case}-{workers}-events.jsonl').read_text().splitlines()]
            assert len(rows)==report['shots']==len(syndromes)
            candidates=[];summary=[]
            for shot,row in enumerate(rows):
                assert row['shot_index']==shot and row['workers']==int(workers)
                np.testing.assert_array_equal(row['syndrome'],syndromes[shot])
                assert row['syndromes_sha256']==sha256(syndromes.tobytes()).hexdigest()
                assert row['numerics']==entry['profile']
                candidate=np.array(row['candidate'],dtype=np.uint8)
                measured=(h@candidate%2 if binary else np.sum((checks!=0)&(candidate!=0)&(checks!=candidate),axis=1)%2)
                valid=bool(np.array_equal(measured,syndromes[shot]))
                assert row['candidate_valid']==valid
                n=checks.shape[1];edges=int(np.count_nonzero(checks));iterations=row['iterations'];work=row['work']
                assert work['bp_calls']==iterations
                assert work['check_to_variable_updates']==work['variable_to_check_updates']==edges*iterations
                assert work['belief_assemblies']==n*iterations
                assert work['candidate_constructions']==iterations+1
                assert work['candidate_checks']==n*(iterations+1)
                shortcut=row['numerics'].get('zero_syndrome_shortcut',False) and row['stop_on_convergence']
                initial=shortcut and iterations==0 and valid
                early=row['stop_on_convergence'] and iterations>0 and valid
                assert work['convergence_checks']==(iterations if row['stop_on_convergence'] else 0)+int(shortcut)+int(not initial and not early)
                assert row['work_accounting_version']=='compiled-flooding-v1'
                candidates.append(candidate);summary.append((row['candidate'],iterations,valid))
                checked+=1
            assert sha256(np.array(candidates,dtype=np.uint8).tobytes()).hexdigest()==entry['candidate_sha256']
            if previous is not None: assert summary==previous
            previous=summary
    print(json.dumps({'source_revision':report['git_head'],'source_hashes':'verified','tests':tests,
                      'independently_checked_cpu_ledger_rows':checked,
                      'note':'test sets overlap; timing and scientific decoding performance are separate'},sort_keys=True))


if __name__=='__main__':main()
