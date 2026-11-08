"""Bounded, matched stable-SPA CPU measurements; run after correctness tests."""
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import gzip, json, os, platform, subprocess, time
import numpy as np
import numba
from numba import njit
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.problems import compile_css_artifact
from bp_registry.resolution import STABLE_SPA_F64
from bp_registry.check_numerics import stable_boxplus, stable_check_extrinsics

HERE=Path(__file__).parent
ROOT=Path.cwd()

@njit(cache=True)
def reference_checks(values,ptr,syndrome,epsilon,out):
    unary=np.log1p(1-epsilon)-np.log(epsilon)
    for row in range(len(ptr)-1):
        for edge in range(ptr[row],ptr[row+1]):
            value=np.inf
            for other in range(ptr[row],ptr[row+1]):
                if edge!=other:value=stable_boxplus(value,values[other])
            if ptr[row+1]-ptr[row]==1:value=unary
            out[edge]=-value if syndrome[row] else value

@njit(cache=True)
def repeat_checks(values,ptr,syndrome,out,repeats,linear):
    for _ in range(repeats):
        if linear:stable_check_extrinsics(values,ptr,syndrome,1e-10,out)
        else:reference_checks(values,ptr,syndrome,1e-10,out)


def main():
    rng=np.random.default_rng(1126); shots=512; repeats=7;limit=20
    report=dict(seed=1126,shots=shots,repeats=repeats,max_iterations=limit,
        host=platform.node(),affinity=sorted(os.sched_getaffinity(0)),numpy=np.__version__,numba=numba.__version__,
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in Path('src/bp_registry').rglob('*.py')},
        timing_scope='decode only; graph construction and ledger I/O excluded; first invocation separately measured; empty NUMBA_CACHE_DIR recommended',
        assessment_status='not_assessed',cases={},checks={})
    h=np.array(json.loads(Path('data/artifacts/bb72-css.json').read_text())['hz'],dtype=np.uint8)
    code=compile_css_artifact(parse_pinned_gb46_css(Path('data/artifacts/gb46-h44.alist').read_bytes()),source_artifact_identity='gb46-h44-pinned-alist')
    binary_s=((rng.random((shots,h.shape[1]))<.08).astype(np.uint8)@h.T%2).astype(np.uint8)
    errors=rng.choice(np.arange(4,dtype=np.uint8),size=(shots,code.n),p=[.92,.08/3,.08/3,.08/3])
    pauli_s=np.array([code.syndrome(row) for row in errors])
    np.savez_compressed(HERE/'benchmark-inputs.npz',binary_syndromes=binary_s,pauli_syndromes=pauli_s)
    policy=replace(STABLE_SPA_F64,zero_syndrome_shortcut=False)
    cases=[('binary_bb72',CompiledBinaryFlooding.from_check_matrix(h,policy=policy),binary_s,{'error_rate':.08}),
        ('pauli_gb46',CompiledBp4Graph.from_code(code,np.tile([.92,.08/3,.08/3,.08/3],(code.n,1)),policy=policy),pauli_s,{})]
    for name,graph,syndromes,kwargs in cases:
        runner=graph.bind_error_rate(.08).run if kwargs else graph.run
        start=time.perf_counter(); expected=[runner(s,max_iterations=limit) for s in syndromes]; first=time.perf_counter()-start
        row=dict(numerics=graph.effective_numerics,single_first_seconds=first,timings={})
        for workers in (1,4):
            start=time.perf_counter();batch=graph.run_batch(syndromes,max_iterations=limit,workers=workers,**kwargs);first=time.perf_counter()-start
            np.testing.assert_array_equal(batch.candidates,[r.candidate for r in expected])
            np.testing.assert_array_equal(batch.iterations,[r.iterations for r in expected])
            np.testing.assert_array_equal(batch.converged,[r.converged for r in expected])
            times={'single':[],'batch':[]}
            for rep in range(repeats):
                for variant in (('single','batch') if rep%2 else ('batch','single')):
                    start=time.perf_counter()
                    if variant=='single': [runner(s,max_iterations=limit) for s in syndromes]
                    else:graph.run_batch(syndromes,max_iterations=limit,workers=workers,**kwargs)
                    times[variant].append(time.perf_counter()-start)
            row['timings'][str(workers)]={**times,'first_batch_seconds':first,'median_speedup':float(np.median(times['single'])/np.median(times['batch'])), 'shots_per_second':float(shots/np.median(times['batch']))}
            ledger=HERE/f'{name}-{workers}-events.jsonl'
            batch.write_ledger(ledger)
            ledger.with_suffix('.jsonl.gz').write_bytes(gzip.compress(ledger.read_bytes(),mtime=0))
            ledger.unlink()
        row['total_iterations']=int(batch.iterations.sum());row['candidate_sha256']=sha256(batch.candidates.tobytes()).hexdigest()
        report['cases'][name]=row
        print(name,{w:round(t['median_speedup'],2) for w,t in row['timings'].items()},flush=True)
    for degree in (4,16,64,256):
        values=rng.normal(0,20,degree*16);ptr=np.arange(17,dtype=np.int64)*degree;syndrome=rng.integers(0,2,16,dtype=np.uint8)
        a=np.empty_like(values);b=np.empty_like(values)
        repeat_checks(values,ptr,syndrome,a,1,False);repeat_checks(values,ptr,syndrome,b,1,True)
        np.testing.assert_allclose(a,b,rtol=0,atol=2e-11)
        times={'quadratic':[],'linear':[]}
        for rep in range(7):
            for label in (('quadratic','linear') if rep%2 else ('linear','quadratic')):
                start=time.perf_counter();repeat_checks(values,ptr,syndrome,b,100,label=='linear');times[label].append(time.perf_counter()-start)
        report['checks'][str(degree)]={**times,'speedup':float(np.median(times['quadratic'])/np.median(times['linear']))}
    report['threading_layer']=numba.threading_layer()
    (HERE/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
