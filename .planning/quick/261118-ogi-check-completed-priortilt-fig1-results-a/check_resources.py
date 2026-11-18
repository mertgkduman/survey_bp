"""Rehash sealed evidence and reconcile all parallel work with bounded I/O concurrency."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'data/reproductions/priortilt-2611-13373'
sys.path.insert(0,str(STUDY));import run,parallel
plan=run.load();parallel.load_amendment();checks=[]
keys=('shots','errors','iterations','directed_edge_updates','decode_ns','nonconvergence','random_draws','biased_node_updates')


def marker(path,digest):
    data=path.read_bytes();assert sha256(data).hexdigest()==digest
    return json.loads(data)


with ThreadPoolExecutor(max_workers=8) as pool:
    for path in sorted((STUDY/'results').glob('*/parallel-work.json')):
        root=path.parent
        if not (root/'audit.json').exists():continue
        audit=json.loads((root/'audit.json').read_text());work=json.loads(path.read_text());inherited=json.loads((root/'inherited-prefix.json').read_text())
        computed={k:0 for k in keys};retained={k:0 for k in keys};oldmarkers=0
        def stage_summary(item):
            name,digest=item;p=root/'parallel-stages'/parallel.VERSION/name
            stage=marker(p,digest);assert run.sha(p.with_suffix('.npz'))==stage['sha256']
            return stage['summary']
        for summary in pool.map(stage_summary,work['stages'].items()):
            for k in keys:computed[k]+=summary[k]
        for basis,s in audit['bases'].items():
            def inherited_marker(item):
                name,digest=item;assert run.sha(root/basis/name)==digest
                return 1
            oldmarkers+=sum(pool.map(inherited_marker,inherited['bases'][basis]['chunks'].items()))
            def retained_summary(item):
                name,digest=item;m=marker(root/basis/name,digest)
                if 'parallel_execution' not in m:return None
                assert m['parallel_execution']['controller']==parallel.VERSION
                assert m['parallel_execution']['resource_amendment_sha256']==run.sha(STUDY/'resource-amendment.json')
                return m['summary']
            for summary in pool.map(retained_summary,s['chunks'].items()):
                if summary is not None:
                    for k in keys:retained[k]+=summary[k]
        assert computed==work['computed'] and retained==work['retained']
        assert {k:computed[k]-retained[k] for k in keys}==work['speculative']
        for k in keys:
            assert sum(s[k] for s in audit['bases'].values())==sum(s[k] for s in inherited['bases'].values())+retained[k]
        checks.append({'point':root.name,'inherited_markers_unchanged':oldmarkers,'stages':len(work['stages']),
                       'computed':computed,'retained':retained,'speculative':work['speculative'],'work_sha256':run.sha(path)})
        print('PASS',root.name,'stages',len(work['stages']),'computed/retained/speculative shots',computed['shots'],retained['shots'],work['speculative']['shots'],flush=True)
out={'parent_plan_sha256':run.sha(STUDY/'plan.json'),'resource_amendment_sha256':run.sha(STUDY/'resource-amendment.json'),
     'checks':checks,'scope':'worker final full candidate/work/replay audits retained; rehash all sealed stage JSON/NPZ and inherited/canonical markers, recompute cohort/work separation; eight bounded I/O threads, deterministic ordered aggregation; no simulations rerun'}
run.write_json(Path(__file__).parent/'resource-check.json',out)
print('Checked resource work and inherited prefixes:',len(checks),'audited parallel points',flush=True)
