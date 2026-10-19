"""Profile one bounded CSS SPA decode and one GB46 four-state sweep."""

from __future__ import annotations

import cProfile
import io
import json
from pathlib import Path
import pstats

import numpy as np

from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.problems import QuaternaryOriginalProblem, compile_css_artifact


ROOT = Path(__file__).resolve().parents[1]


def profile(label, fn):
    profiler = cProfile.Profile()
    profiler.enable()
    fn()
    profiler.disable()
    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).sort_stats('cumtime').print_stats(18)
    print(f'=== {label} ===\n{stream.getvalue()}')


def main():
    h = np.asarray(json.loads((ROOT / 'data/artifacts/bb72-css.json').read_text())['hz'], dtype=np.uint8)
    profile('BB72 canonical SPA, one syndrome, max 3 iterations',
            lambda: BinarySpaKernel().run(h, h[:, 0].copy(), error_rate=.08, max_iterations=3))
    css = parse_pinned_gb46_css((ROOT / 'data/artifacts/gb46-h44.alist').read_bytes())
    code = compile_css_artifact(css, source_artifact_identity='gb46-h44-pinned-alist')
    error = np.zeros(code.n, dtype=np.uint8)
    error[0] = 1
    problem = QuaternaryOriginalProblem('original-profile', code, code.syndrome(error))
    priors = np.tile([1-.08, .08/3, .08/3, .08/3], (code.n, 1))
    session = ScalarLlrBp4Kernel().new_session(problem, priors)
    profile('GB46 canonical BP4, one flooding sweep', lambda: session.sweep(stop_on_convergence=False))


if __name__ == '__main__':
    main()
