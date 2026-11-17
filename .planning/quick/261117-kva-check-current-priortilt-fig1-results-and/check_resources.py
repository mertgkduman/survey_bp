"""Independently reconcile canonical-prefix and speculative accounting."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'data/reproductions/priortilt-2611-13373'
sys.path.insert(0,str(STUDY));import run,parallel
plan=run.load();parallel.load_amendment();checks=[]
keys=('shots','errors','iterations','directed_edge_updates','decode_ns','nonconvergence','random_draws','biased_node_updates')
for path in sorted((STUDY/'results').glob('*/parallel-work.json')):
    root=path.parent
    if not (root/'audit.json').exists():continue
    audit=json.loads((root/'audit.json').read_text());work=json.loads(path.read_text());inherited=json.loads((root/'inherited-prefix.json').read_text())
    computed={k:0 for k in keys};retained={k:0 for k in keys};oldmarkers=0
    for name,digest in work['stages'].items():
        marker=root/'parallel-stages'/parallel.VERSION/name
        assert run.sha(marker)==digest
        stage=json.loads(marker.read_text());assert run.sha(marker.with_suffix('.npz'))==stage['sha256']
        for k in keys:computed[k]+=stage['summary'][k]
    for basis,s in audit['bases'].items():
        for name,digest in inherited['bases'][basis]['chunks'].items():
            assert run.sha(root/basis/name)==digest;oldmarkers+=1
        for name,digest in s['chunks'].items():
            marker=root/basis/name;assert run.sha(marker)==digest;m=json.loads(marker.read_text())
            if 'parallel_execution' in m:
                assert m['parallel_execution']['controller']==parallel.VERSION
                assert m['parallel_execution']['resource_amendment_sha256']==run.sha(STUDY/'resource-amendment.json')
                for k in keys:retained[k]+=m['summary'][k]
    assert computed==work['computed'] and retained==work['retained']
    assert {k:computed[k]-retained[k] for k in keys}==work['speculative']
    for k in keys:
        assert sum(s[k] for s in audit['bases'].values())==sum(s[k] for s in inherited['bases'].values())+retained[k]
    checks.append({'point':root.name,'inherited_markers_unchanged':oldmarkers,'stages':len(work['stages']),
                   'computed':computed,'retained':retained,'speculative':work['speculative'],'work_sha256':run.sha(path)})
out={'parent_plan_sha256':run.sha(STUDY/'plan.json'),'resource_amendment_sha256':run.sha(STUDY/'resource-amendment.json'),
     'checks':checks,'scope':'worker final full candidate/work/replay audits retained; rehash sealed stages, inherited markers and recompute cohort/work separation; no simulations rerun'}
run.write_json(Path(__file__).parent/'resource-check.json',out)
print('Checked resource work and inherited prefixes:',len(checks),'audited parallel points',flush=True)
