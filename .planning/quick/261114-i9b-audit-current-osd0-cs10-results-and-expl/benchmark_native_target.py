"""Fresh source-matched CS10 timing with C++ host CPU optimization enabled."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

import numpy as np

from bp_registry.postprocessing.osd import UniformOsd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPIKE = REPO / '.planning/spikes/056-efficient-osd'
spec = importlib.util.spec_from_file_location('_native_cpu_target_probe', SPIKE / 'native.py')
native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
native.LIBRARY = REPO / '.git/osd-reference-host-target.so'
command = ['g++', '-std=c++17', '-O3', '-march=native', '-shared', '-fPIC',
           '-I'+str(native.SOURCE / 'src_cpp'), str(SPIKE / 'reference.cpp'), '-o', str(native.LIBRARY)]
assert subprocess.check_output(['git', '-C', str(native.SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == native.COMMIT
assert not subprocess.check_output(['git', '-C', str(native.SOURCE), 'status', '--porcelain'], text=True).strip()
subprocess.run(command, check=True)


def main():
    import sys
    sys.path.insert(0, str(REPO / 'data/reproductions'))
    import bp_study_runtime as rt
    plan = rt.load(REPO / 'data/reproductions/roffe-2005-07016-bp')
    cases = json.loads((SPIKE / 'terminal-fixtures.json').read_text())
    affinity = sorted(os.sched_getaffinity(0)); os.sched_setaffinity(0, {affinity[0]})
    rows = []
    try:
        for code in sorted(plan['codes'], key=lambda c: plan['codes'][c]['n']):
            h = rt.load_artifact(REPO, plan['codes'][code]['artifact']).code.hz
            processor, ref = UniformOsd(h, method='OSD_CS', order=10), native.Native(h, 10, p=.04)
            fixtures = []
            for case in cases:
                if case['code'] != code:
                    continue
                llr = np.array(case['terminal_llr']); ordering = np.argsort(llr, kind='stable')
                ranks = np.empty(len(llr)); ranks[ordering] = np.arange(len(llr))
                syndrome = np.array(case['syndrome'], dtype=np.uint8)
                expected, _ = ref.decode(syndrome, ranks, trace=False, control_ties=False)
                actual = processor.decode(syndrome, ranks, error_rate=.04)
                assert np.array_equal(expected, actual.candidate)
                fixtures.append((syndrome, ranks))
            trials = {'native': [], 'optimized': []}
            for repeat in range(12):
                for name in (('native', 'optimized') if repeat % 2 == 0 else ('optimized', 'native')):
                    start = time.perf_counter_ns()
                    for syndrome, ranks in fixtures:
                        if name == 'native':
                            ref.decode(syndrome, ranks, trace=False, control_ties=False)
                        else:
                            processor.decode(syndrome, ranks, error_rate=.04)
                    trials[name].append((time.perf_counter_ns()-start)/len(fixtures))
            med = {k: statistics.median(v) for k, v in trials.items()}
            rows.append({'code': code, 'n': h.shape[1], 'fixtures': len(fixtures), 'median_ns': med,
                         'speed_ratio': med['native']/med['optimized'], 'trials': trials})
            ref.close(); print(rows[-1]['code'], rows[-1]['speed_ratio'], flush=True)
    finally:
        os.sched_setaffinity(0, affinity)
    result = {'status': 'passed', 'command': command, 'source_commit': native.COMMIT,
              'library_sha256': sha256(native.LIBRARY.read_bytes()).hexdigest(),
              'implementation_sha256': sha256((REPO / 'src/bp_registry/postprocessing/osd.py').read_bytes()).hexdigest(),
              'host': platform.node(), 'affinity': [affinity[0]], 'benchmarks': rows,
              'scope': 'CS10 vs CS10 on64 warm source-derived fixtures; twelve alternating rounds; native final-only with original syndrome check vs optimized full candidates/digest/work/check; BP/constructor/JIT excluded; host-target C++ -O3 -march=native; original qualification preserved; no exclusive physical core claim'}
    rt.write_json(HERE / 'native-target-benchmark.json', result)


if __name__ == '__main__':
    main()
