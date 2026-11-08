"""Explicit accepted-policy grid: single/batch identity, not a mathematical oracle."""
from pathlib import Path
from itertools import product
from dataclasses import replace
from tempfile import TemporaryDirectory
import sys,gzip,json
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from audit_support import Audit
from bp_registry.resolution import STABLE_SPA_F64,ResolutionPolicy,BpFloodingPolicy
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
HERE=Path(__file__).parent/'grid';HERE.mkdir(exist_ok=True)

def grid():
    h=np.array([[1,1,0],[0,1,1]],dtype=np.uint8);s=np.array([[0,0],[1,0],[1,1]],dtype=np.uint8)
    rows=[];cases=0
    with TemporaryDirectory() as temp,gzip.open(HERE/'events.jsonl.gz','wt') as handle:
        for rule,fmt,scope,coeff,damping in product(('stable_spa','nms','oms'),('float16','float32','float64','int8','int16','int32'),('scalar_edges','all_messages','all_state'),('float64','same'),(0.,.6)):
            resolution=ResolutionPolicy(fmt,8 if fmt.startswith('int') else None,scope,coeff)
            policy=replace(STABLE_SPA_F64,resolution=resolution,damping=damping) if rule=='stable_spa' else BpFloodingPolicy(check_rule='min_sum',resolution=resolution,damping=damping,alpha=.75 if rule=='nms' else 1.,beta=.25 if rule=='oms' else 0.,hard_decision='map_pauli',version='bp-flooding-policy-v2',check_stabilization='exact_unity',product_epsilon=1e-10)
            for family in ('binary','pauli'):
                graph=CompiledBinaryFlooding.from_check_matrix(h,policy=policy,rule="spa" if rule=="stable_spa" else "min_sum") if family=='binary' else CompiledBp4Graph.from_code(PauliCode(checks=h),np.array([[.7,.1,.1,.1],[.4,.3,.2,.1],[.1,.2,.3,.4]]),policy=policy)
                kwargs={'error_rate':.17} if family=='binary' else {}
                expected=[graph.run(x,max_iterations=3,**kwargs) for x in s]
                for workers in (1,2):
                    result=graph.run_batch(s,max_iterations=3,workers=workers,**kwargs)
                    np.testing.assert_array_equal(result.candidates,[r.candidate for r in expected])
                    np.testing.assert_array_equal(result.iterations,[r.iterations for r in expected])
                    np.testing.assert_array_equal(result.converged,[r.converged for r in expected])
                    p=Path(temp)/'events.jsonl';result.write_ledger(p);handle.write(p.read_text())
                rows.append(dict(family=family,rule=rule,format=fmt,scope=scope,coefficients=coeff,damping=damping,policy_identity=policy.semantic_identity,passed=True))
                cases+=1
    (HERE/'matrix.json').write_text(json.dumps(rows,indent=2)+'\n')
    return dict(configurations=cases,workers=[1,2],shots_per_configuration=3,ledger_rows=cases*6,claim='admitted dispatch and single/batch parity; not all combinations of controllers/schedules or an independent equation proof')

if __name__=='__main__':
    a=Audit(HERE);a.probe('compiled_policy_grid',grid);a.finish()
