"""Matched CPU throughput with frozen inputs, warm timings, and decode ledgers."""
from __future__ import annotations
import argparse
import importlib.util
import sys
import tempfile
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import numpy as np
import numba
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import compile_css_artifact
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--shots',type=int,default=256)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--legacy-revision',default='3aacb2c',help='pinned pre-stabilization compiled implementation')
    args=parser.parse_args()
    if min(args.shots,args.workers,args.repeats)<1: parser.error('positive sizes required')
    args.output.mkdir(parents=True,exist_ok=False)
    rng=np.random.default_rng(11027)
    h=np.asarray(json.loads((ROOT/'data/artifacts/bb72-css.json').read_text())['hz'],dtype=np.uint8)
    errors=(rng.random((args.shots,h.shape[1]))<.08).astype(np.uint8)
    binary_syndromes=(errors@h.T%2).astype(np.uint8)
    code=compile_css_artifact(parse_pinned_gb46_css((ROOT/'data/artifacts/gb46-h44.alist').read_bytes()),source_artifact_identity='gb46-h44-pinned-alist')
    errors=rng.choice(np.arange(4,dtype=np.uint8),size=(args.shots,code.n),p=[.92,.08/3,.08/3,.08/3])
    pauli_syndromes=np.array([code.syndrome(row) for row in errors])
    priors=np.tile([.92,.08/3,.08/3,.08/3],(code.n,1))
    np.savez(args.output/'inputs.npz',binary_syndromes=binary_syndromes,pauli_syndromes=pauli_syndromes)
    policy=BpFloodingPolicy(resolution=ResolutionPolicy('int8',16,'all_messages'),
        damping=.1,alpha=.8,beta=.1,hard_decision='map_pauli',zero_syndrome_shortcut=False,
        version='bp-flooding-policy-v2',check_stabilization='exact_unity',product_epsilon=1e-10)
    report={'schema':'kernel-cpu-benchmark-v1','assessment_status':'not_assessed',
        'host':platform.node(),'affinity':sorted(os.sched_getaffinity(0)), 'python':platform.python_version(),
        'numba':numba.__version__,'numpy':np.__version__,'seed':11027,'shots':args.shots,'repeats':args.repeats,
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'source_sha256':{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/bp_registry').rglob('*.py')},
        'timing_scope':'decode only; graph construction and ledger serialization excluded; JIT first calls separate',
        'cases':{}}
    cases=[('bb72_spa',CompiledBinaryFlooding.from_check_matrix(h),binary_syndromes,{'error_rate':.08}),
           ('bb72_q8_nms_oms',CompiledBinaryFlooding.from_check_matrix(h,rule='min_sum',policy=policy),binary_syndromes,{'error_rate':.08}),
           ('gb46_spa',CompiledBp4Graph.from_code(code,priors),pauli_syndromes,{}),
           ('gb46_q8_nms_oms',CompiledBp4Graph.from_code(code,priors,policy=policy),pauli_syndromes,{})]
    for name,graph,syndromes,kwargs in cases:
        # Compare against the existing bound-prior binary API where available.
        single = graph.bind_error_rate(kwargs['error_rate']).run if kwargs else graph.run
        start=time.perf_counter();reference=[single(s,max_iterations=20) for s in syndromes];single_first=time.perf_counter()-start
        baseline=lambda:[single(s,max_iterations=20) for s in syndromes]
        row={'single_first_seconds':single_first,'profile':graph.effective_numerics,'timings':{}}
        for workers in (1,args.workers):
            start=time.perf_counter();batch=graph.run_batch(syndromes,max_iterations=20,workers=workers,**kwargs);first=time.perf_counter()-start
            np.testing.assert_array_equal(batch.candidates,[r.candidate for r in reference])
            np.testing.assert_array_equal(batch.iterations,[r.iterations for r in reference])
            np.testing.assert_array_equal(batch.converged,[r.converged for r in reference])
            single_times=[];batch_times=[]
            for repeat in range(args.repeats):
                # Alternate ordering to reduce systematic thermal/load bias.
                for label in (('single','batch') if repeat%2==0 else ('batch','single')):
                    start=time.perf_counter()
                    if label=='single': baseline()
                    else: graph.run_batch(syndromes,max_iterations=20,workers=workers,**kwargs)
                    (single_times if label=='single' else batch_times).append(time.perf_counter()-start)
            row['timings'][str(workers)]={'batch_first_seconds':first,'single_seconds':single_times,'batch_seconds':batch_times,
                'median_speedup':float(np.median(single_times)/np.median(batch_times)),
                'batch_shots_per_second':float(args.shots/np.median(batch_times))}
            batch.write_ledger(args.output/(name+f'-{workers}-events.jsonl'))
        row['candidate_sha256']=sha256(batch.candidates.tobytes()).hexdigest()
        row['total_iterations']=int(batch.iterations.sum())
        report['cases'][name]=row
        print(name,{w:round(t['median_speedup'],2) for w,t in row['timings'].items()},flush=True)
    from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
    from bp_registry.quaternary.numerics import QBP4_F64_V2
    report['compiled_optimization'] = {}
    with tempfile.TemporaryDirectory(prefix='bp-cpu-baseline-') as temporary:
        for family,syndromes in [('canonical',binary_syndromes),('quaternary',pauli_syndromes)]:
            source = subprocess.check_output(['git','show',f'{args.legacy_revision}:src/bp_registry/{family}/compiled.py'],cwd=ROOT)
            file = Path(temporary)/(family+'_baseline.py');file.write_bytes(source)
            module_name=f'bp_registry.{family}._cpu_benchmark_baseline'
            spec=importlib.util.spec_from_file_location(module_name,file)
            module=importlib.util.module_from_spec(spec);sys.modules[module_name]=module;spec.loader.exec_module(module)
            if family=='canonical':
                legacy=module.CompiledBinaryFlooding.from_check_matrix(h,profile=BINARY_SPA_F64_V2).bind_error_rate(.08)
                current=CompiledBinaryFlooding.from_check_matrix(h,profile=BINARY_SPA_F64_V2).bind_error_rate(.08)
            else:
                legacy=module.CompiledBp4Graph.from_code(code,priors,profile=QBP4_F64_V2)
                current=CompiledBp4Graph.from_code(code,priors,profile=QBP4_F64_V2)
            legacy_graph=legacy.graph if family=='canonical' else legacy
            current_graph=current.graph if family=='canonical' else current
            for syndrome in syndromes[:4]:
                values=rng.normal(0,10,len(legacy_graph.variables) if family=='canonical' else (len(legacy_graph.labels),3))
                kw={'error_rate':.08} if family=='canonical' else {}
                left=legacy_graph.sweep(values,syndrome,**kw);right=current_graph.sweep(values,syndrome,**kw)
                fields=('check_to_variable','new_v2c','beliefs','candidate') if family=='canonical' else ('c2v','v2c','beliefs','candidate')
                for field in fields: np.testing.assert_array_equal(getattr(left,field),getattr(right,field))
            old=[legacy.run(s,max_iterations=20) for s in syndromes]
            new=[current.run(s,max_iterations=20) for s in syndromes]
            for a,b in zip(old,new,strict=True):
                np.testing.assert_array_equal(a.candidate,b.candidate)
                assert (a.iterations,a.converged)==(b.iterations,b.converged)
            timings={'legacy':[],'optimized':[]}
            for repeat in range(args.repeats):
                for label in (('legacy','optimized') if repeat%2==0 else ('optimized','legacy')):
                    runner=legacy if label=='legacy' else current
                    start=time.perf_counter()
                    for syndrome in syndromes: runner.run(syndrome,max_iterations=20)
                    timings[label].append(time.perf_counter()-start)
            report['compiled_optimization'][family]={'revision':args.legacy_revision,'source_sha256':sha256(source).hexdigest(),
                'profile':'frozen-v2 for both backends','seconds':timings,
                'median_speedup':float(np.median(timings['legacy'])/np.median(timings['optimized'])),
                'candidate_sha256':sha256(np.array([r.candidate for r in new]).tobytes()).hexdigest(),
                'iterations':[r.iterations for r in new],'converged':[r.converged for r in new]}
            print(family+' compiled optimization',report['compiled_optimization'][family]['median_speedup'],flush=True)
    report['threading_layer']=numba.threading_layer()
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
