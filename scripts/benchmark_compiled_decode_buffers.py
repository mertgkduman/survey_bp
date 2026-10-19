"""Warmed, matched decode-only timing for the optional compiled BP kernels."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import time

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import compile_css_artifact


ROOT = Path(__file__).resolve().parents[1]


def measure(run, syndromes, batches: int) -> list[dict[str, object]]:
    rows = []
    for _ in range(5):
        start = time.perf_counter_ns()
        results = [run(s) for _ in range(batches) for s in syndromes]
        elapsed = time.perf_counter_ns() - start
        first = results[:len(syndromes)]
        rows.append({
            "ns_per_shot": elapsed / len(results),
            "candidate_sha256": sha256(b"".join(r.candidate.tobytes() for r in first)).hexdigest(),
            "iterations": [int(r.iterations) for r in first],
            "converged": [bool(r.converged) for r in first],
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = json.loads((ROOT / "data/artifacts/bb72-css.json").read_text())
    h = np.asarray(artifact["hz"], dtype=np.uint8)
    rng = np.random.default_rng(11019)
    errors = (rng.random((24, h.shape[1])) < .08).astype(np.uint8)
    binary_syndromes = np.asarray((errors @ h.T) % 2, dtype=np.uint8)
    raw = (ROOT / "data/artifacts/gb46-h44.alist").read_bytes()
    code = compile_css_artifact(parse_pinned_gb46_css(raw), source_artifact_identity="gb46-h44-pinned-alist")
    pauli_errors = np.zeros((8, code.n), dtype=np.uint8)
    for row in pauli_errors:
        selected = rng.random(code.n) < .08
        row[selected] = rng.choice(np.asarray([1, 2, 3], dtype=np.uint8), size=int(selected.sum()))
    bp4_syndromes = [code.syndrome(row) for row in pauli_errors]
    priors = np.tile([.92, .08 / 3, .08 / 3, .08 / 3], (code.n, 1))
    report = {
        "schema": "compiled-decode-buffers-benchmark-v1",
        "host": platform.node(),
        "affinity": sorted(os.sched_getaffinity(0)),
        "python": platform.python_version(),
        "numba": __import__("numba").__version__,
        "bb72_syndrome_sha256": sha256(binary_syndromes.tobytes()).hexdigest(),
        "gb46_syndrome_sha256": sha256(b"".join(s.tobytes() for s in bp4_syndromes)).hexdigest(),
        "cases": {},
    }
    for rule in ("spa", "min_sum"):
        bound = CompiledBinaryFlooding.from_check_matrix(h, rule=rule).bind_error_rate(.08)
        run = lambda syndrome: bound.run(syndrome, max_iterations=10)
        run(binary_syndromes[0])
        report["cases"]["bb72_" + rule] = measure(run, binary_syndromes, 100)
    graph = CompiledBp4Graph.from_code(code, priors)
    for stop, label in ((True, "early"), (False, "fixed8")):
        run = lambda syndrome: graph.run(syndrome, max_iterations=8, stop_on_convergence=stop)
        run(bp4_syndromes[0])
        report["cases"]["gb46_" + label] = measure(run, bp4_syndromes, 100)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
