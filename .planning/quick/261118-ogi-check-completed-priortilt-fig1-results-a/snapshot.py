"""Status-only extraction from completed full-worker audit receipts; no raw-ledger rehash."""
import csv
from dataclasses import asdict
import io
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
STUDY=ROOT/'data/reproductions/priortilt-2611-13373'
sys.path.insert(0,str(STUDY));import run,parallel
plan=run.load();parallel.load_amendment()
source={(r['code'],float(r['p']),r['method']):r for r in csv.DictReader((STUDY/'source-figure1.csv').open())}
names={'priortilt':'PriorTilt_3phase','relay':'RelayBP','beam':'BeamSearch32'}
rows=[];bindings=[]
for j in plan['jobs']:
    root=STUDY/'results'/j['id'];path=root/'audit.json'
    if not path.exists():continue
    a=json.loads(path.read_text());assert a==json.loads((root/'complete.json').read_text())
    assert a['plan_sha256']==run.sha(STUDY/'plan.json') and a['job']==j
    assert a['manifest_sha256']==run.sha(root/'manifest.json')
    assert a['resolved_policy']==json.loads(json.dumps(asdict(run.spec_for(j))))
    for s in a['bases'].values():
        assert s==run.terminal({k:v for k,v in s.items() if k not in ('rate','ci975','stop_reason')},plan)
    x,z=a['bases']['x'],a['bases']['z'];cycle=j['cycles'];p=source[j['code'],j['p'],names[j['method']]]
    rate=(x['rate']+z['rate'])/cycle;lo=(x['ci975'][0]+z['ci975'][0])/cycle;hi=(x['ci975'][1]+z['ci975'][1])/cycle
    row={'point':j['id'],'code':j['code'],'p':j['p'],'method':j['method'],'cycles':cycle,
         'ler_per_cycle':rate,'ci95_low':lo,'ci95_high':hi,'paper_ler_per_cycle':float(p['ler_per_cycle']),
         'paper_1sigma':float(p['published_1sigma']),'local_over_paper':rate/float(p['ler_per_cycle']),
         'paper_inside_local95':lo<=float(p['ler_per_cycle'])<=hi,'audit_sha256':run.sha(path)}
    for basis,s in (('x',x),('z',z)):
        row.update({basis+'_'+k:s[k] for k in ('shots','errors','nonconvergence','stop_reason')})
        row[basis+'_observable_rate']=s['rate'];row[basis+'_ci975_low'],row[basis+'_ci975_high']=s['ci975']
        for k in ('iterations','directed_edge_updates','random_draws','biased_node_updates'):row[basis+'_mean_'+k]=s[k]/s['shots']
        row[basis+'_mean_decode_ms']=s['decode_ns']/s['shots']/1e6
    rows.append(row);bindings.append({'point':j['id'],'audit_sha256':run.sha(path),'manifest_sha256':run.sha(root/'manifest.json')})
stream=io.StringIO();writer=csv.DictWriter(stream,list(rows[0]));writer.writeheader();writer.writerows(rows)
(HERE/'comparison-snapshot.csv').write_text(stream.getvalue())
run.write_json(HERE/'receipt-bindings.json',{'scope':'Matching final full-worker audit/complete receipts and manifests/resolved policies; frozen identities and terminal summaries checked. Raw event ledgers and shared samples NOT freshly rehashed for this status snapshot. Canonical publication remains unchanged pending scheduled final collector.',
    'plan_sha256':run.sha(STUDY/'plan.json'),'resource_amendment_sha256':run.sha(STUDY/'resource-amendment.json'),'frozen_file_count':len(plan['implementation_sha256']),'points':bindings})
print('Status snapshot:',len(rows),'fully audited points; main publication unchanged')
