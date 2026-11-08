"""Matched warmed CPU timing against a read-only pre-fix source snapshot.

BP_BENCH_SOURCE selects package source; BP_BENCH_LABEL selects output directory.
Cold calls are recorded separately. No fastmath or algorithm changes in harness.
"""
from pathlib import Path
import os, sys
ROOT = Path.cwd()
SOURCE = Path(os.environ.get('BP_BENCH_SOURCE', ROOT / 'src')).resolve()
sys.path.insert(0, str(SOURCE))
from dataclasses import replace
from hashlib import sha256
import gzip, json, platform, time
import numpy as np
import numba
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.problems import compile_css_artifact
from bp_registry.resolution import STABLE_SPA_F64

HERE = Path(__file__).resolve().parent
OUT = HERE / os.environ['BP_BENCH_LABEL']
OUT.mkdir(exist_ok=True)
INPUTS = HERE.parent / '026-stable-spa-qualification/benchmark-inputs.npz'


def main():
    inputs = np.load(INPUTS)
    limit, repeats = 20, 9
    report = dict(source_sha256={str(p.relative_to(SOURCE)): sha256(p.read_bytes()).hexdigest()
        for p in sorted((SOURCE / 'bp_registry').rglob('*.py'))},
        inputs_sha256=sha256(INPUTS.read_bytes()).hexdigest(), max_iterations=limit,
        repeats=repeats, host=platform.node(), affinity=sorted(os.sched_getaffinity(0)),
        numpy=np.__version__, numba=numba.__version__,
        timing_scope='decode only; warm timings exclude first compilation, construction and ledger I/O',
        assessment_status='not_assessed', cases={})
    report['cpu_topology'] = {str(cpu): {
        key: (Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')/key).read_text().strip()
        for key in ('physical_package_id','core_id','thread_siblings_list')}
        for cpu in sorted(os.sched_getaffinity(0))}
    h = np.array(json.loads(Path('data/artifacts/bb72-css.json').read_text())['hz'], dtype=np.uint8)
    code = compile_css_artifact(parse_pinned_gb46_css(Path('data/artifacts/gb46-h44.alist').read_bytes()), source_artifact_identity='gb46-h44-pinned-alist')
    policy = replace(STABLE_SPA_F64, zero_syndrome_shortcut=False)
    cases = [('binary_bb72', CompiledBinaryFlooding.from_check_matrix(h, policy=policy), inputs['binary_syndromes'], {'error_rate': .08}),
        ('pauli_gb46', CompiledBp4Graph.from_code(code, np.tile([.92,.08/3,.08/3,.08/3], (code.n,1)), policy=policy), inputs['pauli_syndromes'], {})]
    for name, graph, syndromes, kwargs in cases:
        runner = graph.bind_error_rate(.08).run if kwargs else graph.run
        start = time.perf_counter()
        expected = [runner(s, max_iterations=limit) for s in syndromes]
        row = dict(first_single_seconds=time.perf_counter()-start, numerics=graph.effective_numerics, timings={})
        for workers in (1, 2, 4):
            start = time.perf_counter()
            result = graph.run_batch(syndromes, max_iterations=limit, workers=workers, **kwargs)
            first = time.perf_counter()-start
            np.testing.assert_array_equal(result.candidates, [r.candidate for r in expected])
            np.testing.assert_array_equal(result.iterations, [r.iterations for r in expected])
            np.testing.assert_array_equal(result.converged, [r.converged for r in expected])
            times = {'single': [], 'batch': []}
            for rep in range(repeats):
                for variant in (('single','batch') if rep % 2 else ('batch','single')):
                    start = time.perf_counter()
                    if variant == 'single':
                        [runner(s, max_iterations=limit) for s in syndromes]
                    else:
                        graph.run_batch(syndromes, max_iterations=limit, workers=workers, **kwargs)
                    times[variant].append(time.perf_counter()-start)
            row['timings'][str(workers)] = dict(**times, first_batch_seconds=first,
                median_speedup=float(np.median(times['single'])/np.median(times['batch'])),
                shots_per_second=float(len(syndromes)/np.median(times['batch'])))
            path = OUT / f'{name}-{workers}-events.jsonl'
            result.write_ledger(path)
            path.with_suffix('.jsonl.gz').write_bytes(gzip.compress(path.read_bytes(), mtime=0))
            path.unlink()
        row['candidate_sha256'] = sha256(result.candidates.tobytes()).hexdigest()
        row['iterations_sha256'] = sha256(result.iterations.tobytes()).hexdigest()
        row['converged_sha256'] = sha256(result.converged.tobytes()).hexdigest()
        row['total_iterations'] = int(result.iterations.sum())
        row['shots'] = len(syndromes)
        report['cases'][name] = row
        print(name, {w: round(t['median_speedup'], 3) for w,t in row['timings'].items()}, flush=True)
    from contextlib import redirect_stdout
    from bp_registry.cpu_batch import _binary_batch, _pauli_batch
    with (OUT / 'parallel-diagnostics.txt').open('w') as handle, redirect_stdout(handle):
        _binary_batch.parallel_diagnostics(level=1)
        _pauli_batch.parallel_diagnostics(level=1)
    report['threading_layer'] = numba.threading_layer()
    (OUT / 'benchmark.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
