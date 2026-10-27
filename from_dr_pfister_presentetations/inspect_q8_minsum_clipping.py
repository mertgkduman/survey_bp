"""Matched diagnostic of clipping sites in experimental Q8 BP4 min-sum.

This isolates the exact implementation in policy_kernel.py. It does not define
a new canonical decoder or claim fidelity to an unspecified source Q8 kernel.
Every attempted arm and shot is retained in the JSONL event ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
from pathlib import Path

import numpy as np
from numba import njit

from bp_registry.code_constructions import build_b1_ghp
from policy_kernel import decode_bp4
import policy_kernel
from run_reproduction import (
    bp4_graph_from_css, css_syndrome, double_gross, logical_failure, sample_error,
)


@njit
def _logaddexp(a: float, b: float) -> float:
    return max(a, b) + math.log1p(math.exp(-abs(a - b)))


@njit
def _exact_projection(values: np.ndarray, label: int, unused_bound: float) -> float:
    """Form the log-sum-exp difference before the caller quantizes it."""
    x, y, z = values[0], values[1], values[2]
    if label == 1:
        return _logaddexp(0.0, -x) - _logaddexp(-y, -z)
    if label == 2:
        return _logaddexp(0.0, -y) - _logaddexp(-x, -z)
    return _logaddexp(0.0, -z) - _logaddexp(-x, -y)


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"experimental clone no longer matches policy_kernel.py: {old}")
    return source.replace(old, new)


def _variants() -> dict[str, object]:
    # Clone the existing Numba function to change only the named clipping sites.
    # Exact-text guards make future upstream changes fail closed.
    source = inspect.getsource(decode_bp4.py_func).split("\n", 1)[1]
    no_v2c_clip = _replace_once(
        source,
        "v2c[edge, state] = _q(prior_llrs[variables[edge], state], scale)",
        "v2c[edge, state] = prior_llrs[variables[edge], state]",
    )
    no_v2c_clip = _replace_once(
        no_v2c_clip, "proposal = _q(proposal, scale)", "proposal = proposal",
    )
    no_v2c_clip = _replace_once(
        no_v2c_clip,
        "next_v2c[edge, state - 1] = _q(damping * v2c[edge, state - 1] + (1.0 - damping) * proposal, scale)",
        "next_v2c[edge, state - 1] = damping * v2c[edge, state - 1] + (1.0 - damping) * proposal",
    )
    result: dict[str, object] = {"q8_original": decode_bp4}
    for name, body, projection in (
        ("exact_projection_only", source, _exact_projection),
        ("unbounded_v2c_only", no_v2c_clip, policy_kernel._commutation_llr),
        ("both_changes", no_v2c_clip, _exact_projection),
    ):
        namespace = policy_kernel.__dict__.copy()
        namespace["_commutation_llr"] = projection
        exec(body, namespace)
        result[name] = njit(namespace["decode_bp4"])
    return result


def _first_sweep_clip_count(graph: object, syndrome: np.ndarray, scale: int) -> tuple[int, int]:
    """Count original Q8 V2C proposals outside range on the first sweep."""
    bound = 127.0 / scale
    q = lambda value: np.clip(np.rint(value * scale) / scale, -bound, bound)
    initial = np.full(3, q(graph.prior_llrs[0, 0]), dtype=np.float64)
    comm = q(policy_kernel._commutation_llr(initial, 1, bound))
    edge_checks = np.repeat(np.arange(len(graph.row_ptr) - 1), np.diff(graph.row_ptr))
    c2v = (1 - 2 * syndrome[edge_checks].astype(np.int16)) * comm
    beliefs = graph.prior_llrs.copy()
    for state in range(1, 4):
        affected = graph.labels != state
        np.add.at(beliefs[:, state - 1], graph.variables[affected], c2v[affected])
    proposals = beliefs[graph.variables].copy()
    for state in range(1, 4):
        affected = graph.labels != state
        proposals[affected, state - 1] -= c2v[affected]
    return int(np.count_nonzero(np.abs(proposals) > bound)), int(proposals.size)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", choices=("b1", "double_gross"), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-iterations", type=int, default=1000)
    args = parser.parse_args()
    if not (0 < args.p < 0.75 and args.shots > 0 and args.max_iterations > 0):
        parser.error("require 0<p<0.75, shots>0, max-iterations>0")
    if args.output.exists():
        parser.error("output must not exist")

    code = build_b1_ghp() if args.code == "b1" else double_gross()
    graph = bp4_graph_from_css(code, args.p)
    variants = _variants()
    zero = np.zeros(len(graph.row_ptr) - 1, dtype=np.uint8)
    for run in variants.values():
        run(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
            graph.variables, graph.labels, graph.prior_llrs, zero,
            1, 16, 0.0, True)

    args.output.mkdir(parents=True)
    counts = {name: {"shots": 0, "type_i": 0, "type_ii": 0,
                     "exact_success": 0, "stabilizer_success": 0,
                     "total_iterations": 0} for name in variants}
    first_clip = first_total = 0
    digest = hashlib.sha256()
    rng = np.random.default_rng(args.seed)
    with (args.output / "events.jsonl").open("x", encoding="utf-8") as ledger:
        for shot in range(args.shots):
            truth = sample_error(rng, code.n, args.p)
            syndrome = css_syndrome(code, truth)
            nclip, nproposal = _first_sweep_clip_count(graph, syndrome, 16)
            first_clip += nclip
            first_total += nproposal
            truth_hash = hashlib.sha256(truth.tobytes()).hexdigest()
            for name, run in variants.items():
                candidate, iterations, valid = run(
                    graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                    graph.variables, graph.labels, graph.prior_llrs, syndrome,
                    args.max_iterations, 16, 0.0, True,
                )
                type_i = not bool(valid)
                type_ii = bool(valid and logical_failure(code, truth, candidate))
                exact = bool(valid and not type_ii and np.array_equal(candidate, truth))
                stabilizer = bool(valid and not type_ii and not exact)
                record = {"shot": shot, "arm": name, "error_sha256": truth_hash,
                          "iterations": int(iterations), "type_i": type_i,
                          "type_ii": type_ii, "exact_success": exact,
                          "stabilizer_success": stabilizer}
                encoded = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
                ledger.write(encoded.decode("utf-8"))
                digest.update(encoded)
                count = counts[name]
                count["shots"] += 1
                count["type_i"] += int(type_i)
                count["type_ii"] += int(type_ii)
                count["exact_success"] += int(exact)
                count["stabilizer_success"] += int(stabilizer)
                count["total_iterations"] += int(iterations)
            if (shot + 1) % 25 == 0:
                print(args.code, shot + 1, "/", args.shots, flush=True)

    summary = {
        "schema": "experimental-bp4-q8-ms-clipping-ablation-v1",
        "code": args.code, "physical_p": args.p, "decoder_p0": args.p,
        "shots": args.shots, "seed": args.seed,
        "sampler": "numpy.PCG64; shared errors for all arms",
        "pauli_order": "I,X,Y,Z", "check_rule": "unscaled_unoffset_min_sum",
        "q8_scale": 16, "damping": 0.0, "max_iterations": args.max_iterations,
        "arms": counts,
        "first_sweep_original_v2c_proposals_outside_q8_range": first_clip,
        "first_sweep_original_v2c_proposals_total": first_total,
        "event_ledger_sha256": digest.hexdigest(),
    }
    with (args.output / "summary.json").open("x", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
