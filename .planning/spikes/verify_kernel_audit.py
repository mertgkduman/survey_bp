"""Verify retained audit integrity without rerunning decoders or changing evidence.

Run: .venv/bin/python .planning/spikes/verify_kernel_audit.py
This verifies report/evidence consistency, not absence of kernel defects.
"""
from hashlib import sha256
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'.planning/spikes'
EXPECTED={'008-mathematical-correctness':(16,11,5),
          '009-open-source-cross-check':(3,3,0),
          '010-policy-extensibility':(14,11,3),
          '011-execution-consistency':(18,6,12)}

def main():
    totals=[0,0,0]
    for directory,counts in EXPECTED.items():
        result=json.loads((BASE/directory/'results.json').read_text())
        actual=(len(result['events']),sum(e['passed'] for e in result['events']),sum(not e['passed'] for e in result['events']))
        assert actual==counts==tuple(result[k] for k in ('checks','passed','failed')),(directory,actual)
        for source,digest in result['source_hashes'].items():
            assert sha256((ROOT/source).read_bytes()).hexdigest()==digest,source
        totals=[x+y for x,y in zip(totals,actual)]
    regression=0
    for directory,count in [('010-policy-extensibility',238),('011-execution-consistency',160)]:
        suites=ET.parse(BASE/directory/'regression.xml').getroot().findall('testsuite')
        assert sum(int(s.attrib['tests']) for s in suites)==count
        assert all(int(s.attrib[key])==0 for s in suites for key in ('errors','failures','skipped'))
        regression+=count
    rows=[line for line in (BASE/'MANIFEST.md').read_text().splitlines() if '| canonical-kernel-audit |' in line]
    assert len(rows)==4 and all('| PARTIAL |' in row for row in rows)
    for schema in ('quaternary_experiment_v2','quaternary_experiment_v3'):
        directory=BASE/'011-execution-consistency'/f'{schema}-budget-counterexample'
        events=[json.loads(row) for row in (directory/'events.jsonl').read_text().splitlines()]
        work=next(e['data']['work'] for e in events if e['kind']=='scalar_schedule')
        assert work['bp_calls']==0 # Retained defect, deliberately not a correctness assertion.
        assert json.loads((directory/'input.json').read_text())['max_work']==1
        assert json.loads((directory/'result.json').read_text())['termination']=='work_budget_exhausted'
    print(json.dumps(dict(artifact_integrity='verified',production_source_hashes='unchanged',
                          diagnostics=dict(zip(('checks','passed','finding_bearing'),totals)),
                          passing_regression_tests=regression,freeze_readiness='not_ready')))

if __name__=='__main__': main()
