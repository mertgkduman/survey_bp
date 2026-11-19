"""Independently reconcile the refreshed audited Fig1 snapshot, preserving earlier rows."""
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
prior=json.loads((ROOT/'.planning/quick/261118-ogi-check-completed-priortilt-fig1-results-a/assessment.json').read_text())
previous={r['point']:r for r in prior['checks']};current={r['point']:r for r in checks}
assert all(current[k]==v for k,v in previous.items())
progress=[json.loads(p.read_text()) for p in (STUDY/'results').glob('*/progress.json')]
result={'snapshot_points':len(checks),'complete_pair_shots':shots,'complete_pair_errors':errors,'checks':checks,
        'preserved_previous_points':len(previous),'frozen_file_count':len(plan['implementation_sha256']),
        'scope':'completed frozen collector full-ledger/sample rehash retained; independent final receipt/source/count/stopping/CI/work and prior38-point reconciliation; no new raw full-ledger rehash or simulations for this check',
        'frozen_plan_sha256':run.sha(STUDY/'plan.json'),'csv_sha256':run.sha(STUDY/'comparison.csv'),
        'progress_committed_shots':sum(s['shots'] for p in progress for s in p['bases'].values()),
        'progress_committed_errors':sum(s['errors'] for p in progress for s in p['bases'].values())}
output=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent/'assessment.json'
output.write_text(json.dumps(result,indent=2)+'\n')
print(f"Checked {len(checks)}/39 audited pairs, {shots:,} shots/{errors} errors; {sum(c['paper_inside'] for c in checks)} paper values inside pointwise intervals; {len(previous)} previous points unchanged")
