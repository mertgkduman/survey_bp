"""Matched-shot diagnostic of BP4 hard decisions and reference numerics.

This is an exploratory ablation, not a publication decoder or source replay.
It retains per-shot outcomes and never exposes sampled truth to the decoder.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from numba import njit

from bp_registry.code_constructions import build_b1_ghp
from bp_registry.quaternary.compiled import (
    _boxplus_pair as _compiled_boxplus_pair, _candidate_matches, _clip,
    _commutation_llr, _logaddexp, _sweep_into,
)

from policy_kernel import _q, _boxplus_pair
from run_reproduction import bp4_graph_from_css, css_syndrome, double_gross, logical_failure, sample_error


@njit(cache=True)
def _reference_candidate(beliefs: np.ndarray, output: np.ndarray) -> int:
    """Reference's strict I/X/Z/Y ladder in this project's I/X/Y/Z encoding."""
    differing = 0
    for variable in range(len(output)):
        x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
        if x > 0.0 and y > 0.0 and z > 0.0:
            output[variable] = 0
        elif x < y and x < z:
            output[variable] = 1
        elif z < x and z < y:
            output[variable] = 3
        else:
            output[variable] = 2
        if (x > 0.0 and y > 0.0 and z > 0.0):
            original = 0
        elif x <= y and x <= z:
            original = 1
        elif y <= z:
            original = 2
        else:
            original = 3
        differing += int(output[variable] != original)
    return differing


@njit(cache=True)
def _decode_float_ties(row_ptr, variable_ptr, variable_edges, variables, labels,
                       prior_llrs, syndrome, limit, max_iterations):
    n, edge_count = prior_llrs.shape[0], len(labels)
    old = prior_llrs[variables].copy()
    new = np.empty_like(old)
    quantized = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    ordinary = np.zeros(n, dtype=np.uint8)
    reference = np.zeros(n, dtype=np.uint8)
    first_ordinary = -1
    first_reference = -1
    ordinary_final = ordinary.copy()
    reference_final = reference.copy()
    tie_sites = 0
    tie_iterations = 0
    if _candidate_matches(row_ptr, variables, labels, ordinary, syndrome):
        return ordinary_final, reference_final, 0, 0, 0, 0
    for iteration in range(1, max_iterations + 1):
        _sweep_into(row_ptr, variable_ptr, variable_edges, variables, labels, old,
                    prior_llrs, syndrome, limit, quantized, c2v, beliefs, new, ordinary)
        count = _reference_candidate(beliefs, reference)
        tie_sites += count
        tie_iterations += int(count > 0)
        if first_ordinary < 0:
            ordinary_final[:] = ordinary
            if _candidate_matches(row_ptr, variables, labels, ordinary, syndrome):
                first_ordinary = iteration
        if first_reference < 0:
            reference_final[:] = reference
            if _candidate_matches(row_ptr, variables, labels, reference, syndrome):
                first_reference = iteration
        if first_ordinary >= 0 and first_reference >= 0:
            break
        old, new = new, old
    return ordinary_final, reference_final, first_ordinary, first_reference, tie_sites, tie_iterations


@njit(cache=True)
def _decode_q8_ties(row_ptr, variable_ptr, variable_edges, variables, labels,
                    prior_llrs, syndrome, max_iterations, scale, damping):
    n, edge_count = prior_llrs.shape[0], len(labels)
    old = np.empty((edge_count, 3), dtype=np.float64)
    new = np.empty_like(old)
    comm = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    ordinary = np.zeros(n, dtype=np.uint8)
    reference = np.zeros(n, dtype=np.uint8)
    ordinary_final = ordinary.copy()
    reference_final = reference.copy()
    first_ordinary = -1
    first_reference = -1
    tie_sites = 0
    tie_iterations = 0
    bound = 127.0 / scale
    if _candidate_matches(row_ptr, variables, labels, ordinary, syndrome):
        return ordinary_final, reference_final, 0, 0, 0, 0
    for edge in range(edge_count):
        for state in range(3):
            old[edge, state] = _q(prior_llrs[variables[edge], state], scale)
    for iteration in range(1, max_iterations + 1):
        for edge in range(edge_count):
            comm[edge] = _q(_commutation_llr(old[edge], labels[edge], bound), scale)
        for check in range(len(row_ptr) - 1):
            start, stop = row_ptr[check], row_ptr[check + 1]
            for edge in range(start, stop):
                first = True
                message = bound
                for other in range(start, stop):
                    if other == edge:
                        continue
                    if first:
                        message = comm[other]
                        first = False
                    else:
                        message = _boxplus_pair(message, comm[other], bound)
                if syndrome[check]:
                    message = -message
                c2v[edge] = _q(message, scale)
        for variable in range(n):
            for state in range(1, 4):
                value = prior_llrs[variable, state - 1]
                for position in range(variable_ptr[variable], variable_ptr[variable + 1]):
                    edge = variable_edges[position]
                    if labels[edge] != state:
                        value += c2v[edge]
                beliefs[variable, state - 1] = value
            x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
            if x > 0.0 and y > 0.0 and z > 0.0:
                ordinary[variable] = 0
            elif x <= y and x <= z:
                ordinary[variable] = 1
            elif y <= z:
                ordinary[variable] = 2
            else:
                ordinary[variable] = 3
        count = _reference_candidate(beliefs, reference)
        tie_sites += count
        tie_iterations += int(count > 0)
        if first_ordinary < 0:
            ordinary_final[:] = ordinary
            if _candidate_matches(row_ptr, variables, labels, ordinary, syndrome):
                first_ordinary = iteration
        if first_reference < 0:
            reference_final[:] = reference
            if _candidate_matches(row_ptr, variables, labels, reference, syndrome):
                first_reference = iteration
        if first_ordinary >= 0 and first_reference >= 0:
            break
        for edge in range(edge_count):
            variable, label = variables[edge], labels[edge]
            for state in range(1, 4):
                proposal = beliefs[variable, state - 1]
                if label != state:
                    proposal -= c2v[edge]
                proposal = _q(proposal, scale)
                new[edge, state - 1] = _q(damping * old[edge, state - 1] + (1.0 - damping) * proposal, scale)
        old, new = new, old
    return ordinary_final, reference_final, first_ordinary, first_reference, tie_sites, tie_iterations


@njit(cache=True)
def _reference_projection(values, label):
    x, y, z = values[0], values[1], values[2]
    if label == 1:
        return _logaddexp(0.0, -x) - _logaddexp(-y, -z)
    if label == 2:
        return _logaddexp(0.0, -y) - _logaddexp(-x, -z)
    return _logaddexp(0.0, -z) - _logaddexp(-x, -y)


@njit(cache=True)
def _reference_tanh_half(value):
    if value > 40.0:
        return 1.0
    if value < -40.0:
        return -1.0
    return math.tanh(value / 2.0)


@njit(cache=True)
def _decode_reference_float(row_ptr, variable_ptr, variable_edges, variables,
                            labels, prior_llrs, syndrome, max_iterations,
                            numerical_mode):
    """Reference SPA and two controlled clipping/check-reduction hybrids.

    Modes: 0 reference; 1 reference check product plus global ±25 clip;
    2 no global clipping plus left-fold boxplus check reduction;
    3 clipped projection only; 4 clipped posterior/V2C only.
    """
    n, edge_count = prior_llrs.shape[0], len(labels)
    old = prior_llrs[variables].copy()
    new = np.empty_like(old)
    comm = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    candidate = np.zeros(n, dtype=np.uint8)
    tie_sites = 0
    saturated_products = 0
    last_iteration = 0
    # Reference always completes at least one iteration, including s=0.
    for iteration in range(1, max_iterations + 1):
        last_iteration = iteration
        for edge in range(edge_count):
            if numerical_mode == 1 or numerical_mode == 3:
                comm[edge] = _commutation_llr(old[edge], labels[edge], 25.0)
            else:
                comm[edge] = _reference_projection(old[edge], labels[edge])
        for check in range(len(row_ptr) - 1):
            start, stop = row_ptr[check], row_ptr[check + 1]
            for edge in range(start, stop):
                if numerical_mode == 2:
                    first = True
                    message = 1e6
                    for other in range(start, stop):
                        if other == edge:
                            continue
                        if first:
                            message = comm[other]
                            first = False
                        else:
                            message = _compiled_boxplus_pair(message, comm[other], 1e6)
                    c2v[edge] = -message if syndrome[check] else message
                else:
                    product = -1.0 if syndrome[check] else 1.0
                    for other in range(start, stop):
                        if other != edge:
                            product *= _reference_tanh_half(comm[other])
                    if product >= 1.0:
                        product = 1.0 - 1e-10
                        saturated_products += 1
                    elif product <= -1.0:
                        product = -1.0 + 1e-10
                        saturated_products += 1
                    c2v[edge] = math.log1p(product) - math.log1p(-product)
        for variable in range(n):
            for state in range(1, 4):
                value = prior_llrs[variable, state - 1]
                for position in range(variable_ptr[variable], variable_ptr[variable + 1]):
                    edge = variable_edges[position]
                    if labels[edge] != state:
                        value += c2v[edge]
                beliefs[variable, state - 1] = _clip(value, 25.0) if numerical_mode == 1 or numerical_mode == 4 else value
        tie_sites += _reference_candidate(beliefs, candidate)
        if _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
            break
        for edge in range(edge_count):
            variable, label = variables[edge], labels[edge]
            for state in range(1, 4):
                value = beliefs[variable, state - 1]
                if label != state:
                    value -= c2v[edge]
                new[edge, state - 1] = _clip(value, 25.0) if numerical_mode == 1 or numerical_mode == 4 else value
        old, new = new, old
    return candidate, last_iteration, tie_sites, saturated_products


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", choices=("b1", "double_gross"), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--kernel", choices=("float", "q8", "reference_float",
                                             "reference_check_clipped", "boxplus_unclipped",
                                             "projection_clipped", "posterior_v2c_clipped"), required=True)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--damping", type=float, default=0.1)
    parser.add_argument("--limit", type=float, default=25.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    code = build_b1_ghp() if args.code == "b1" else double_gross()
    graph = bp4_graph_from_css(code, args.p)
    zero = np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8)
    decoder = (_decode_float_ties if args.kernel == "float" else
               _decode_q8_ties if args.kernel == "q8" else _decode_reference_float)
    if args.kernel == "float":
        decoder(graph.row_ptr, graph.variable_ptr, graph.variable_edges, graph.variables,
                graph.labels, graph.prior_llrs, zero, args.limit, 1)
    elif args.kernel == "q8":
        decoder(graph.row_ptr, graph.variable_ptr, graph.variable_edges, graph.variables,
                graph.labels, graph.prior_llrs, zero, 1, args.scale, args.damping)
    else:
        decoder(graph.row_ptr, graph.variable_ptr, graph.variable_edges, graph.variables,
                graph.labels, graph.prior_llrs, zero, 1,
                1 if args.kernel == "reference_check_clipped" else
                2 if args.kernel == "boxplus_unclipped" else
                3 if args.kernel == "projection_clipped" else
                4 if args.kernel == "posterior_v2c_clipped" else 0)
    rng = np.random.Generator(np.random.PCG64(args.seed))
    args.output.mkdir(parents=True)
    digest = hashlib.sha256()
    counters = Counter()
    with (args.output / "events.jsonl").open("w", encoding="utf-8") as handle:
        for shot in range(args.shots):
            truth = sample_error(rng, code.n, args.p)
            syndrome = css_syndrome(code, truth)
            if args.kernel == "float":
                result = decoder(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                                 graph.variables, graph.labels, graph.prior_llrs, syndrome,
                                 args.limit, 1000)
            elif args.kernel == "q8":
                result = decoder(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                                 graph.variables, graph.labels, graph.prior_llrs, syndrome,
                                 1000, args.scale, args.damping)
            else:
                candidate, completed, tie_sites, saturated = decoder(
                    graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                    graph.variables, graph.labels, graph.prior_llrs, syndrome, 1000,
                    1 if args.kernel == "reference_check_clipped" else
                    2 if args.kernel == "boxplus_unclipped" else
                    3 if args.kernel == "projection_clipped" else
                    4 if args.kernel == "posterior_v2c_clipped" else 0)
                valid = bool(np.array_equal(css_syndrome(code, candidate), syndrome))
                logical = bool(valid and logical_failure(code, truth, candidate))
                exact = bool(np.array_equal(candidate, truth))
                arm_name = "reference_float" if args.kernel == "reference_float" else "variant"
                counters[f"{arm_name}_failed"] += int(not valid or logical)
                counters[f"{arm_name}_invalid"] += int(not valid)
                counters[f"{arm_name}_type_ii"] += int(logical)
                counters[f"{arm_name}_exact"] += int(exact)
                counters[f"{arm_name}_degenerate_success"] += int(valid and not logical and not exact)
                counters["tie_sites"] += int(tie_sites)
                counters["saturated_check_products"] += int(saturated)
                record = {"shot": shot, "error_sha256": hashlib.sha256(truth.tobytes()).hexdigest(),
                          arm_name: {"valid_syndrome": valid, "logical_failure": logical,
                                     "failed": not valid or logical, "iterations": int(completed),
                                     "exact_correction": exact},
                          "tie_sites": int(tie_sites), "saturated_check_products": int(saturated)}
                line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                handle.write(line)
                digest.update(line.encode())
                continue
            ordinary, reference, ordinary_iteration, reference_iteration, sites, iterations = result
            values = {}
            for name, candidate, first in (("ordinary", ordinary, ordinary_iteration),
                                           ("reference_tie", reference, reference_iteration)):
                valid = bool(np.array_equal(css_syndrome(code, candidate), syndrome))
                logical = bool(valid and logical_failure(code, truth, candidate))
                values[name] = {"valid_syndrome": valid, "logical_failure": logical,
                                "failed": not valid or logical, "first_valid_iteration": int(first),
                                "exact_correction": bool(np.array_equal(candidate, truth))}
                counters[f"{name}_failed"] += int(values[name]["failed"])
                counters[f"{name}_invalid"] += int(not valid)
                counters[f"{name}_type_ii"] += int(logical)
                counters[f"{name}_exact"] += int(values[name]["exact_correction"])
                counters[f"{name}_degenerate_success"] += int(valid and not logical and not values[name]["exact_correction"])
            counters["tie_sites"] += int(sites)
            counters["tie_iterations"] += int(iterations)
            counters["shots_with_tie_difference"] += int(sites > 0)
            counters["different_first_valid_iteration"] += int(ordinary_iteration != reference_iteration)
            counters["different_outcome"] += int(values["ordinary"]["failed"] != values["reference_tie"]["failed"])
            counters["reference_rescues"] += int(values["ordinary"]["failed"] and not values["reference_tie"]["failed"])
            counters["reference_losses"] += int(not values["ordinary"]["failed"] and values["reference_tie"]["failed"])
            record = {"shot": shot, "error_sha256": hashlib.sha256(truth.tobytes()).hexdigest(),
                      "tie_sites": int(sites), "tie_iterations": int(iterations), **values}
            line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            handle.write(line)
            digest.update(line.encode())
    numerical_variant = args.kernel not in ("float", "q8")
    summary = {"status": "exploratory_numerical_ablation" if numerical_variant else "exploratory_tie_policy_ablation", "code": args.code,
               "physical_p": args.p, "prior_p0": args.p, "shots": args.shots, "seed": args.seed,
               "kernel": args.kernel, "scale": args.scale if args.kernel == "q8" else None,
               "damping": args.damping if args.kernel == "q8" else None,
               "posterior_v2c_limit": args.limit if args.kernel == "float" else
               25.0 if args.kernel in ("reference_check_clipped", "posterior_v2c_clipped") else None,
               "projection_limit": args.limit if args.kernel == "float" else
               25.0 if args.kernel in ("reference_check_clipped", "projection_clipped") else None,
               "check_rule": "boxplus_left_fold" if args.kernel in ("float", "boxplus_unclipped") else "tanh_product" if numerical_variant else "q8_boxplus_left_fold",
               "max_iterations": 1000, "counts": counters,
               "event_ledger": "events.jsonl", "event_ledger_sha256": digest.hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run()
