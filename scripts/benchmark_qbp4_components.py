"""Pinned GB46 BP4 setup/sweep timing and call profile for local development."""

from __future__ import annotations

import argparse
import cProfile
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import platform
import pstats
import statistics
import time

import numpy as np

from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.problems import QuaternaryOriginalProblem, compile_css_artifact


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = (ROOT / 'data/artifacts/gb46-h44.alist').read_bytes()
    code = compile_css_artifact(parse_pinned_gb46_css(raw), source_artifact_identity='gb46-h44-pinned-alist')
    rng = np.random.default_rng(11019)
    errors = np.zeros((4, code.n), dtype=np.uint8)
    for row in errors:
        selected = rng.random(code.n) < .08
        row[selected] = rng.choice(np.array([1, 2, 3], dtype=np.uint8), size=int(selected.sum()))
    syndromes = [code.syndrome(row) for row in errors]
    problems = [QuaternaryOriginalProblem(f'original-profile-{i}', code, syndrome)
                for i, syndrome in enumerate(syndromes)]
    priors = np.tile([.92, .08/3, .08/3, .08/3], (code.n, 1))
    kernel = ScalarLlrBp4Kernel()
    kernel.new_session(problems[0], priors).sweep(stop_on_convergence=False)
    samples = []
    for repeat in range(5):
        for problem in problems:
            start = time.perf_counter_ns()
            session = kernel.new_session(problem, priors)
            setup = time.perf_counter_ns() - start
            start = time.perf_counter_ns()
            sweep = session.sweep(stop_on_convergence=False)
            elapsed = time.perf_counter_ns() - start
            samples.append({'repeat': repeat, 'problem': problem.lineage_id, 'setup_ns': setup,
                            'sweep_ns': elapsed, 'candidate': sweep.candidate.tolist(),
                            'c2v_sha256': sha256(sweep.c2v.tobytes()).hexdigest(),
                            'v2c_sha256': sha256(sweep.v2c.tobytes()).hexdigest(),
                            'beliefs_sha256': sha256(sweep.beliefs.tobytes()).hexdigest()})
    session = kernel.new_session(problems[0], priors)
    profiler = cProfile.Profile()
    profiler.enable()
    session.sweep(stop_on_convergence=False)
    profiler.disable()
    output = io.StringIO()
    pstats.Stats(profiler, stream=output).sort_stats('cumtime').print_stats(24)
    result = {'schema': 'qbp4-component-profile-v1', 'host': platform.node(),
              'affinity': sorted(os.sched_getaffinity(0)), 'python': platform.python_version(),
              'alist_sha256': sha256(raw).hexdigest(), 'shape': list(code.checks.shape),
              'edges': int(np.count_nonzero(code.checks)), 'p': .08, 'samples': samples,
              'median_setup_ms': statistics.median(row['setup_ns'] for row in samples) / 1e6,
              'median_sweep_ms': statistics.median(row['sweep_ns'] for row in samples) / 1e6,
              'cprofile': output.getvalue()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"setup {result['median_setup_ms']:.3f} ms; sweep {result['median_sweep_ms']:.3f} ms")


if __name__ == '__main__':
    main()
