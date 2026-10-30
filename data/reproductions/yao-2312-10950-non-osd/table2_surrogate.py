"""Bounded surrogate for the paper's unpublished fixed weight-73 Table 2 error."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import time

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import REFERENCE_CPU_F64

import run_point as common

ROOT = Path(__file__).resolve().parent


def run(seed: int, trials: int, output: Path, *, require_bp_failure: bool = False) -> None:
    if output.exists() or seed < 0 or not 1 <= trials <= 1000:
        raise ValueError("new output and 1–1000 trials required")
    code = common._code("b1")
    rng = np.random.Generator(np.random.PCG64(seed))
    packed_hx = np.packbits(code.hx, axis=1, bitorder="little")
    packed_hz = np.packbits(code.hz, axis=1, bitorder="little")
    masks = common._binary_masks(code)
    graph = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=REFERENCE_CPU_F64)
    graph.run_paper_bp(np.zeros(code.hz.shape[0], dtype=np.uint8), error_rate=.08, max_iterations=1)
    for attempt in range(1, 1001):
        truth = np.zeros(code.n, dtype=np.uint8)
        truth[rng.choice(code.n, 73, replace=False)] = 1
        syndrome = common._syndrome(packed_hz, truth)
        baseline = graph.run_paper_bp(syndrome, error_rate=.08, max_iterations=100)
        if not require_bp_failure or not baseline.converged:
            break
    else:
        raise RuntimeError("no BP-nonconvergent weight-73 sample in 1000 attempts")
    manifest = {"schema": "yao-table2-surrogate-v1", "source_error_bytes": "unpublished",
                "classification": "new seeded fixed error, not paper's error",
                "seed": seed, "trials": trials, "error_weight": 73, "physical_p": .08,
                "error_selection": "first_BP_nonconvergent_weight73" if require_bp_failure else "first_weight73",
                "selection_attempts": attempt, "plain_bp_converged": baseline.converged,
                "decoder_p0": .08, "algorithm": "paper-style binary BPGD, T=10, top-gap random",
                "gap": 1.0, "round_limit": code.n,
                "code_semantic_sha256": common.semantic_sha256(code),
                "error_sha256": sha256(truth.tobytes()).hexdigest(),
                "syndrome_sha256": sha256(syndrome.tobytes()).hexdigest(),
                "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    output.mkdir(parents=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    counts = {"converged": 0, "type_i": 0, "type_ii": 0}
    distinct = set()
    started = time.monotonic()
    with (output / "events.jsonl").open("x") as handle:
        for trial in range(trials):
            draws = np.random.Generator(np.random.PCG64(np.random.SeedSequence((seed, trial, 777)))).random(code.n)
            result = graph.run_paper_bpgd(syndrome, error_rate=.08, sweeps_per_round=10,
                                          order="top_gap_random", gap=1.0, random_draws=draws)
            outcome = common._outcome(result.candidate, truth, syndrome, packed_hx, packed_hz,
                                      code, masks, None)
            candidate_hash = sha256(result.candidate.tobytes()).hexdigest()
            if result.converged:
                distinct.add(candidate_hash)
            counts["converged"] += int(result.converged)
            counts["type_i"] += int(outcome["type_i"])
            counts["type_ii"] += int(outcome["type_ii"])
            handle.write(json.dumps({"trial": trial, "candidate_sha256": candidate_hash,
                                     "converged": result.converged, "fixations": result.fixations,
                                     "iterations": result.iterations, **outcome}, sort_keys=True) + "\n")
            print(trial + 1, counts, flush=True)
    summary = {"schema": "yao-table2-surrogate-summary-v1", "trials": trials,
               "counts": counts, "distinct_converged_corrections": len(distinct),
               "wall_seconds": time.monotonic() - started,
               "manifest_sha256": sha256((output / "manifest.json").read_bytes()).hexdigest(),
               "events_sha256": sha256((output / "events.jsonl").read_bytes()).hexdigest()}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--require-bp-failure", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.seed, args.trials, args.output, require_bp_failure=args.require_bp_failure)
