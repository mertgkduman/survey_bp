"""Alternate warmed, persistent baseline/current processes to reduce host drift.

Both compiled versions remain isolated in their own Python processes. Only one
process measures at a time; the other blocks on stdin. Initialization is untimed.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from io import BytesIO
import json, os, subprocess, sys, tarfile
import numpy as np
HERE = Path(__file__).resolve().parent


def worker():
    import benchmark as b
    inputs = b.np.load(b.INPUTS)
    h = b.np.array(json.loads(Path('data/artifacts/bb72-css.json').read_text())['hz'], dtype=b.np.uint8)
    code = b.compile_css_artifact(b.parse_pinned_gb46_css(Path('data/artifacts/gb46-h44.alist').read_bytes()), source_artifact_identity='gb46-h44-pinned-alist')
    policy = b.replace(b.STABLE_SPA_F64, zero_syndrome_shortcut=False)
    cases = {
        'binary_bb72': (b.CompiledBinaryFlooding.from_check_matrix(h, policy=policy), inputs['binary_syndromes'], {'error_rate':.08}),
        'pauli_gb46': (b.CompiledBp4Graph.from_code(code,b.np.tile([.92,.08/3,.08/3,.08/3],(code.n,1)),policy=policy),inputs['pauli_syndromes'],{})}
    reference = {}
    for name,(graph,s,kwargs) in cases.items():
        run = graph.bind_error_rate(.08).run if kwargs else graph.run
        run(s[0],max_iterations=20)
        result = graph.run_batch(s,max_iterations=20,workers=1,**kwargs)
        reference[name] = {key:b.sha256(getattr(result,key).tobytes()).hexdigest() for key in ('candidates','iterations','converged')}
    print(json.dumps(reference),flush=True)
    for line in sys.stdin:
        name,workers,order = json.loads(line)
        graph,s,kwargs = cases[name]
        run = graph.bind_error_rate(.08).run if kwargs else graph.run
        times = {}
        for variant in order:
            start = b.time.perf_counter()
            if variant == 'single':
                [run(syndrome,max_iterations=20) for syndrome in s]
            else:
                graph.run_batch(s,max_iterations=20,workers=workers,**kwargs)
            times[variant] = b.time.perf_counter()-start
        print(json.dumps(times),flush=True)


def main():
    records = {label:json.loads((HERE/label/'benchmark.json').read_text()) for label in ('baseline','current')}
    children = {}
    with TemporaryDirectory(prefix='bp-paired-cpu-') as temp:
        root=Path(temp)
        with tarfile.open(fileobj=BytesIO(subprocess.check_output(['git','archive','6f68961','src']))) as tree:
            tree.extractall(root,filter='data')
        try:
            for label,source in [('baseline',root/'src'),('current',Path.cwd()/'src')]:
                env={**os.environ,'NUMBA_NUM_THREADS':'4','OMP_NUM_THREADS':'1','BP_BENCH_LABEL':label,
                     'BP_BENCH_SOURCE':str(source),'NUMBA_CACHE_DIR':str(root/f'cache-{label}')}
                children[label]=subprocess.Popen([sys.executable,__file__,'worker'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
            identities={label:json.loads(child.stdout.readline()) for label,child in children.items()}
            assert identities['baseline']==identities['current']
            for label in records:
                for name in records[label]['cases']:
                    row=records[label]['cases'][name]
                    for key,field in [('candidates','candidate_sha256'),('iterations','iterations_sha256'),('converged','converged_sha256')]:
                        assert identities[label][name][key]==row[field]
                    for workers in ('1','2','4'):
                        row['timings'][workers]['single']=[]
                        row['timings'][workers]['batch']=[]
            for name in ('binary_bb72','pauli_gb46'):
                for workers in (1,2,4):
                    for rep in range(15):
                        for label in (('baseline','current') if rep%2 else ('current','baseline')):
                            child=children[label]
                            order=('single','batch') if rep%2 else ('batch','single')
                            child.stdin.write(json.dumps([name,workers,order])+'\n');child.stdin.flush()
                            times=json.loads(child.stdout.readline())
                            for key,value in times.items():
                                records[label]['cases'][name]['timings'][str(workers)][key].append(value)
                    print(name,workers,'paired timings complete',flush=True)
        finally:
            for child in children.values():
                child.stdin.close()
            for child in children.values():
                assert child.wait()==0
    summary=dict(baseline='6f68961',current=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        affinity=records['current']['affinity'],
        methodology='15 paired warm repetitions; persistent isolated processes alternate measurement order; one measuring process at a time; cold measurements/ledgers/diagnostics retained from initial matching source runs',cases={})
    for label,report in records.items():
        report['repeats']=15
        report['timing_methodology']=summary['methodology']
        for row in report['cases'].values():
            for times in row['timings'].values():
                times['median_speedup']=float(np.median(times['single'])/np.median(times['batch']))
                times['shots_per_second']=float(512/np.median(times['batch']))
        (HERE/label/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
    for name in records['current']['cases']:
        rows={}
        for workers in ('1','2','4'):
            a=records['baseline']['cases'][name]['timings'][workers]
            b=records['current']['cases'][name]['timings'][workers]
            rows[workers]=dict(baseline_batch_seconds=float(np.median(a['batch'])),current_batch_seconds=float(np.median(b['batch'])),
                throughput_ratio=float(np.median(a['batch'])/np.median(b['batch'])),
                paired_throughput_ratio_median=float(np.median(np.array(a['batch'])/np.array(b['batch']))),
                current_speedup_vs_single=b['median_speedup'],shots_per_second=b['shots_per_second'])
        summary['cases'][name]=dict(exact_results_preserved=True,workers=rows)
    (HERE/'cpu-comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    worker() if len(sys.argv)>1 else main()
