"""Independently reconcile a fixed audited Fig1 CSV and recorded OSD timing claim."""
import csv
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import sys
from scipy.stats import beta

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'data/reproductions/priortilt-2611-13373'
sys.path.insert(0,str(STUDY));import run
plan=run.load()
rows=list(csv.DictReader((STUDY/'comparison.csv').open()))
source={(r['code'],r['p'],r['method']):r for r in csv.DictReader((STUDY/'source-figure1.csv').open())}
names={'priortilt':'PriorTilt_3phase','beam':'BeamSearch32','relay':'RelayBP'}
checks=[];shots=errors=0
for row in rows:
    root=STUDY/'results'/row['point'];a=json.loads((root/'audit.json').read_text())
    assert a==json.loads((root/'complete.json').read_text())
    assert sha256((root/'audit.json').read_bytes()).hexdigest()==row['audit_sha256']
    j=next(j for j in plan['jobs'] if j['id']==row['point']);assert a['job']==j
    total=lo=hi=0.
    for basis in ('x','z'):
        s=a['bases'][basis];n,k=s['shots'],s['errors'];shots+=n;errors+=k
        assert n==int(row[basis+'_shots']) and k==int(row[basis+'_errors'])
        assert (k==20 or n==100000000) and 0<=k<=20 and 0<n<=100000000
        assert n==sum(s['joint_counts']) and k==s['joint_counts'][1]+s['joint_counts'][3]
        assert s['nonconvergence']==s['joint_counts'][2]+s['joint_counts'][3]
        total+=k/n;lo+=0. if not k else beta.ppf(.0125,k,n-k+1)
        hi+=1. if k==n else beta.ppf(.9875,k if k==20 else k+1,n-k)
        for col in ('iterations','directed_edge_updates','random_draws','biased_node_updates'):
            assert math.isclose(s[col]/n,float(row[basis+'_mean_'+col]),rel_tol=1e-12)
        assert math.isclose(s['decode_ns']/n/1e6,float(row[basis+'_mean_decode_ms']),rel_tol=1e-12)
    cycle=j['cycles'];total/=cycle;lo/=cycle;hi/=cycle
    assert math.isclose(total,float(row['ler_per_cycle']),rel_tol=1e-12)
    assert math.isclose(lo,float(row['ci95_low']),rel_tol=1e-12) and math.isclose(hi,float(row['ci95_high']),rel_tol=1e-12)
    p=source[(j['code'],str(j['p']),names[j['method']])]
    original=(int(p['x_errors'])/int(p['x_shots'])+int(p['z_errors'])/int(p['z_shots']))/cycle
    assert math.isclose(original,float(row['paper_ler_per_cycle']),rel_tol=1e-12)
    assert (lo<=original<=hi)==(row['paper_inside_local95']=='True')
    checks.append({'point':j['id'],'local':total,'paper':original,'local_ci95':[lo,hi],'local_over_paper':total/original,'paper_inside':bool(lo<=original<=hi)})
bench=ROOT/'.planning/quick/261114-i9b-audit-current-osd0-cs10-results-and-expl/native-target-benchmark.json'
b=json.loads(bench.read_text());impl=ROOT/'src/bp_registry/postprocessing/osd.py'
assert b['implementation_sha256']==sha256(impl.read_bytes()).hexdigest()
assert b['status']=='passed' and '-O3' in b['command'] and '-march=native' in b['command']
for r in b['benchmarks']:
    assert math.isclose(r['median_ns']['native']/r['median_ns']['optimized'],r['speed_ratio'],rel_tol=1e-12)
result={'snapshot_points':len(checks),'complete_pair_shots':shots,'complete_pair_errors':errors,'checks':checks,
        'scope':'worker full-ledger audits retained; collector rehashes all bound chunks/shared samples; this independent check recomputes aggregate source/count/interval/work arithmetic, without rerunning simulations',
        'frozen_plan_sha256':run.sha(STUDY/'plan.json'),'csv_sha256':run.sha(STUDY/'comparison.csv'),
        'osd_benchmark_sha256':run.sha(bench),'osd_implementation_sha256':b['implementation_sha256'],
        'osd_cs10_speed_range':[min(r['speed_ratio'] for r in b['benchmarks']),max(r['speed_ratio'] for r in b['benchmarks'])],
        'osd_scope':b['scope']}
(Path(__file__).parent/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
print(f"Checked {len(checks)}/39 audited pairs, {shots:,} shots/{errors} errors; {sum(c['paper_inside'] for c in checks)} paper values inside pointwise intervals; OSD benchmark/implementation hash valid")
