"""Qualify current CPU throughput against pre-fix 729157f, with owned temp state."""
from pathlib import Path
from tempfile import TemporaryDirectory
from io import BytesIO
import json, os, subprocess, sys, tarfile
import numpy as np

HERE = Path(__file__).resolve().parent
BASELINE = '729157f'


def main():
    with TemporaryDirectory(prefix='bp-freeze-cpu-') as temp:
        root = Path(temp)
        archive = subprocess.check_output(['git', 'archive', BASELINE, 'src'])
        with tarfile.open(fileobj=BytesIO(archive)) as tree:
            tree.extractall(root, filter='data')
        for label, source in [('baseline', root/'src'), ('current', Path.cwd()/'src')]:
            env = {**os.environ, 'NUMBA_NUM_THREADS': '4', 'OMP_NUM_THREADS': '1',
                'NUMBA_CACHE_DIR': str(root/f'cache-{label}'),
                'BP_BENCH_LABEL': label, 'BP_BENCH_SOURCE': str(source)}
            subprocess.run([sys.executable, str(HERE/'benchmark.py')], env=env, check=True)
    before = json.loads((HERE/'baseline/benchmark.json').read_text())
    after = json.loads((HERE/'current/benchmark.json').read_text())
    assert before['inputs_sha256'] == after['inputs_sha256']
    assert before['affinity'] == after['affinity']
    summary = dict(baseline=BASELINE, current=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        affinity=after['affinity'], methodology='same input replay, sequential baseline/current processes, fresh compile caches; nine warm repetitions, medians; shared host timing is descriptive, not a statistical performance guarantee', cases={})
    for name, a in after['cases'].items():
        b = before['cases'][name]
        for key in ('candidate_sha256','iterations_sha256','converged_sha256','total_iterations','numerics','shots'):
            assert a[key] == b[key], (name, key)
        rows = {}
        for workers in ('1','2','4'):
            prior, current = b['timings'][workers], a['timings'][workers]
            rows[workers] = dict(baseline_batch_seconds=float(np.median(prior['batch'])),
                current_batch_seconds=float(np.median(current['batch'])),
                throughput_ratio=float(np.median(prior['batch'])/np.median(current['batch'])),
                current_speedup_vs_single=current['median_speedup'], shots_per_second=current['shots_per_second'])
        summary['cases'][name] = dict(exact_results_preserved=True, workers=rows)
    (HERE/'cpu-comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
