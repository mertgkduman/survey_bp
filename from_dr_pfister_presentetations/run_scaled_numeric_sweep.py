"""Paired, ledgered BP4 and binary numerical-policy campaign on CSS codes."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.stats import binomtest

from bp_registry.canonical.compiled import CompiledBinaryFlooding, _decode as legacy_binary_decode
from bp_registry.code_constructions import build_b1_ghp
from bp_registry.quaternary.compiled import _decode as legacy_bp4_decode

from numeric_sweep_kernel import decode_binary_numeric, decode_bp4_numeric
from policy_kernel import decode_binary_oms, decode_bp4, binary_prior
from run_bp4_performance_screen import miao_toric_d4
from run_reproduction import LABELS, bp4_graph_from_css, css_syndrome, double_gross, logical_failure, sample_error


def _options(item: dict) -> tuple[int, float, float, float]:
    method = item.get("check", "product")
    if method not in ("product", "boxplus"):
        raise ValueError("check must be product or boxplus")
    cap = math.inf if item.get("check_cap") is None else float(item["check_cap"])
    epsilon = float(item.get("product_epsilon", 1e-10))
    damping = float(item.get("damping", 0.0))
    if not cap > 0 or not 0 < epsilon < .5 or not 0 <= damping < 1:
        raise ValueError("invalid numerical policy")
    return (0 if method == "product" else 1), cap, epsilon, damping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", choices=("b1", "double_gross", "miao_toric_d4"), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-iterations", type=int, default=1000)
    parser.add_argument("--configs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--status", choices=("screen", "heldout", "control"), default="screen")
    args = parser.parse_args()
    if not 0 < args.p < .75 or args.shots < 1 or args.max_iterations < 1:
        parser.error("require 0<p<.75, shots>=1, and max-iterations>=1")
    if args.output.exists():
        raise FileExistsError(args.output)
    items = json.loads(args.configs.read_text(encoding="utf-8"))
    if not isinstance(items, list) or not items or len({x["id"] for x in items}) != len(items):
        raise ValueError("configs must have unique IDs")
    valid_families = {"bp4_numeric", "binary_numeric", "bp4_legacy", "binary_legacy_spa", "binary_oms", "bp4_q8"}
    for item in items:
        if item["family"] not in valid_families:
            raise ValueError(f"unknown family {item['family']}")
        if item["family"].endswith("numeric"):
            _options(item)
    code = (build_b1_ghp() if args.code == "b1" else
            double_gross() if args.code == "double_gross" else miao_toric_d4())
    p0 = {item["id"]: float(item.get("initial_p", args.p)) for item in items}
    graphs = {item["id"]: bp4_graph_from_css(code, p0[item["id"]]) for item in items
              if item["family"].startswith("bp4")}
    x_graph = CompiledBinaryFlooding.from_check_matrix(code.hz)
    z_graph = CompiledBinaryFlooding.from_check_matrix(code.hx)
    binary_llr = {item["id"]: binary_prior(p0[item["id"]]) for item in items}
    zero = np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8)
    zero_x = np.zeros(code.hz.shape[0], dtype=np.uint8)
    zero_z = np.zeros(code.hx.shape[0], dtype=np.uint8)
    # Compile every Numba specialization outside timed attempts.
    for item in items:
        family = item["family"]
        if family == "bp4_numeric":
            graph = graphs[item["id"]]
            decode_bp4_numeric(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                               graph.variables, graph.labels, graph.prior_llrs, zero, 1, *_options(item))
        elif family == "binary_numeric":
            decode_binary_numeric(x_graph.row_ptr, x_graph.variables, code.n, binary_llr[item["id"]],
                                  zero_x, 1, *_options(item))
        elif family == "bp4_legacy":
            graph = graphs[item["id"]]
            legacy_bp4_decode(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                              graph.variables, graph.labels, graph.prior_llrs, zero, 25., 1, True)
        elif family == "binary_legacy_spa":
            legacy_binary_decode(x_graph.row_ptr, x_graph.variables, code.n, zero_x,
                                 binary_llr[item["id"]], 25., 0, 1)
        elif family == "binary_oms":
            decode_binary_oms(x_graph.row_ptr, x_graph.variables, code.n, zero_x,
                              binary_llr[item["id"]], 1, 4, .1, 1., .25)
        else:
            graph = graphs[item["id"]]
            decode_bp4(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                       graph.variables, graph.labels, graph.prior_llrs, zero, 1,
                       int(item.get("scale", 4)), float(item.get("damping", .1)), False)
    rng = np.random.Generator(np.random.PCG64(args.seed))
    samples = []
    for _ in range(args.shots):
        truth = sample_error(rng, code.n, args.p)
        syndrome = css_syndrome(code, truth)
        samples.append((truth, syndrome, hashlib.sha256(truth.tobytes()).hexdigest()))
    args.output.mkdir(parents=True)
    counts = defaultdict(lambda: {"failures": 0, "type_i": 0, "type_ii": 0,
                                  "exact_success": 0, "stabilizer_success": 0,
                                  "total_work_iterations": 0.0, "total_elapsed_seconds": 0.0})
    digest = hashlib.sha256()
    with (args.output / "events.jsonl").open("w", encoding="utf-8") as handle:
        for item in items:
            family, arm = item["family"], item["id"]
            graph = graphs.get(arm)
            for shot, (truth, syndrome, error_hash) in enumerate(samples):
                start = time.perf_counter()
                if family == "bp4_numeric":
                    candidate, iterations, converged = decode_bp4_numeric(
                        graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                        graph.variables, graph.labels, graph.prior_llrs,
                        syndrome, args.max_iterations, *_options(item))
                    work = float(iterations)
                elif family == "bp4_legacy":
                    candidate, iterations, converged = legacy_bp4_decode(
                        graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                        graph.variables, graph.labels, graph.prior_llrs,
                        syndrome, 25., args.max_iterations, True)
                    work = float(iterations)
                elif family == "bp4_q8":
                    candidate, iterations, converged = decode_bp4(
                        graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                        graph.variables, graph.labels, graph.prior_llrs, syndrome,
                        args.max_iterations, int(item.get("scale", 4)), float(item.get("damping", .1)), False)
                    work = float(iterations)
                else:
                    sx, sz = syndrome[code.hx.shape[0]:], syndrome[:code.hx.shape[0]]
                    if family == "binary_numeric":
                        xhat, ix, cx = decode_binary_numeric(x_graph.row_ptr, x_graph.variables,
                                                              code.n, binary_llr[arm], sx,
                                                              args.max_iterations, *_options(item))
                        zhat, iz, cz = decode_binary_numeric(z_graph.row_ptr, z_graph.variables,
                                                              code.n, binary_llr[arm], sz,
                                                              args.max_iterations, *_options(item))
                    elif family == "binary_legacy_spa":
                        xhat, cx, ix = legacy_binary_decode(x_graph.row_ptr, x_graph.variables,
                                                             code.n, sx, binary_llr[arm], 25., 0,
                                                             args.max_iterations)
                        zhat, cz, iz = legacy_binary_decode(z_graph.row_ptr, z_graph.variables,
                                                             code.n, sz, binary_llr[arm], 25., 0,
                                                             args.max_iterations)
                    else:
                        xhat, ix, cx = decode_binary_oms(x_graph.row_ptr, x_graph.variables,
                                                         code.n, sx, binary_llr[arm], args.max_iterations,
                                                         4, .1, 1., .25)
                        zhat, iz, cz = decode_binary_oms(z_graph.row_ptr, z_graph.variables,
                                                         code.n, sz, binary_llr[arm], args.max_iterations,
                                                         4, .1, 1., .25)
                    candidate = LABELS[xhat, zhat]
                    iterations = (int(ix), int(iz))
                    work = (int(ix) + int(iz)) / 2.0
                    converged = bool(cx and cz)
                elapsed = time.perf_counter() - start
                valid = bool(np.array_equal(css_syndrome(code, candidate), syndrome))
                type_ii = bool(valid and logical_failure(code, truth, candidate))
                exact = bool(valid and not type_ii and np.array_equal(candidate, truth))
                stabilizer = bool(valid and not type_ii and not exact)
                failed = not valid or type_ii
                entry = counts[arm]
                entry["failures"] += int(failed)
                entry["type_i"] += int(not valid)
                entry["type_ii"] += int(type_ii)
                entry["exact_success"] += int(exact)
                entry["stabilizer_success"] += int(stabilizer)
                entry["total_work_iterations"] += work
                entry["total_elapsed_seconds"] += elapsed
                record = {"arm": arm, "shot": shot, "error_sha256": error_hash,
                          "failed": failed, "type_i": not valid, "type_ii": type_ii,
                          "exact_success": exact, "stabilizer_success": stabilizer,
                          "converged": bool(converged), "iterations": iterations,
                          "bp4_equivalent_work": work, "elapsed_seconds": elapsed}
                line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                handle.write(line)
                digest.update(line.encode())
            handle.flush()
            print(f"{arm}: {entry['failures']}/{args.shots} failures", flush=True)
    summary = {"status": args.status, "code": args.code,
               "physical_p": args.p, "shots": args.shots, "seed": args.seed,
               "max_iterations": args.max_iterations,
               "check_shape": [list(code.hx.shape), list(code.hz.shape)],
               "pauli_order": "I,X,Y,Z", "binary_marginal_prior_by_arm": {
                   arm: 2 * prior / 3 for arm, prior in p0.items()},
               "configs": items, "counts": counts,
               "event_ledger": "events.jsonl", "event_ledger_sha256": digest.hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for item in items:
        count = counts[item["id"]]["failures"]
        ci = binomtest(count, args.shots).proportion_ci(method="exact")
        print(f"{item['id']} 95% CI [{ci.low:.5g}, {ci.high:.5g}]")


if __name__ == "__main__":
    main()
