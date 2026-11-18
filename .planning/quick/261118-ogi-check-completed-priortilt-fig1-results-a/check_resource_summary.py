"""Receipt-level resource reconciliation and explicitly sampled on-disk binding checks."""
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
STUDY=ROOT/'data/reproductions/priortilt-2611-13373'
sys.path.insert(0,str(STUDY));import run,parallel
run.load();parallel.load_amendment()
keys=('shots','errors','iterations','directed_edge_updates','decode_ns','nonconvergence','random_draws','biased_node_updates')
plan_sha=run.sha(STUDY/'plan.json');resource_sha=run.sha(STUDY/'resource-amendment.json')
checks=[]

def sample(names):
    names=sorted(names)
    return [names[i] for i in sorted({0,len(names)//2,len(names)-1})] if names else []

for binding in json.loads((HERE/'receipt-bindings.json').read_text())['points']:
    root=STUDY/'results'/binding['point'];path=root/'parallel-work.json'
    if not path.exists():continue
    audit=json.loads((root/'audit.json').read_text());work=json.loads(path.read_text());old=json.loads((root/'inherited-prefix.json').read_text())
    assert run.sha(root/'audit.json')==binding['audit_sha256']
    assert old['plan_sha256']==plan_sha and old['resource_amendment_sha256']==resource_sha
    assert {k:work['computed'][k]-work['retained'][k] for k in keys}==work['speculative']
    for k in keys:assert sum(s[k] for s in audit['bases'].values())==sum(s[k] for s in old['bases'].values())+work['retained'][k]
    inherited_bound=inherited_sampled=canonical_sampled=stage_sampled=0
    for basis,s in audit['bases'].items():
        inherited=old['bases'][basis]['chunks']
        assert all(s['chunks'][name]==digest for name,digest in inherited.items())
        inherited_bound+=len(inherited)
        for name in sample(inherited):
            assert run.sha(root/basis/name)==inherited[name];inherited_sampled+=1
        for name in sample(s['chunks']):
            marker=root/basis/name;assert run.sha(marker)==s['chunks'][name]
            m=json.loads(marker.read_text());assert run.sha(marker.with_suffix('.npz'))==m['sha256']
            j=audit['job'];run.verify_noise_binding(run.load(),j,basis,m['start'],m)
            canonical_sampled+=1
            if 'parallel_execution' in m:
                assert m['parallel_execution']['controller']==parallel.VERSION
                assert m['parallel_execution']['resource_amendment_sha256']==resource_sha
    for basis in ('x','z'):
        for name in sample([n for n in work['stages'] if n.startswith(basis+'-')]):
            marker=root/'parallel-stages'/parallel.VERSION/name
            assert run.sha(marker)==work['stages'][name];m=json.loads(marker.read_text())
            assert run.sha(marker.with_suffix('.npz'))==m['sha256']
            assert m['controller']==parallel.VERSION and m['plan_sha256']==plan_sha
            run.verify_noise_binding(run.load(),audit['job'],basis,m['start'],m);stage_sampled+=1
    checks.append({'point':root.name,'stages':len(work['stages']),
                   'inherited_marker_digests_preserved_in_full_audit':inherited_bound,
                   'inherited_markers_sampled':inherited_sampled,'canonical_markers_npz_noise_sampled':canonical_sampled,
                   'stage_markers_npz_noise_sampled':stage_sampled,
                   'computed':work['computed'],'retained':work['retained'],'speculative':work['speculative'],
                   'work_sha256':run.sha(path)})
out={'parent_plan_sha256':plan_sha,'resource_amendment_sha256':resource_sha,'checks':checks,
     'scope':'Retain completed full-worker audits; reconcile all additive receipt totals and all inherited marker digest maps. Fresh on-disk checks are deterministic first/middle/last per basis for inherited, canonical and stage evidence. This is not a fresh full-stage/ledger rehash.'}
run.write_json(HERE/'resource-check.json',out)
print('PASS',len(checks),'resource receipt reconciliations; sampled stages',sum(c['stage_markers_npz_noise_sampled'] for c in checks),flush=True)
