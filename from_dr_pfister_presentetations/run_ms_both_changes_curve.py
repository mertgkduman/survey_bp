"""Run the jointly corrected diagnostic BP4 min-sum arm at one curve point.

The arm has float64 three-coordinate V2C and an exact log-sum-exp difference,
but still Q8 scalar projected and check messages. It is a diagnostic hybrid,
not a claim about the presentation's unspecified 8-bit implementation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.stats import binomtest

from bp_registry.code_constructions import build_b1_ghp
from inspect_q8_minsum_clipping import _variants
from run_full_v2_curve import source_rows
from run_reproduction import (
    bp4_graph_from_css, css_syndrome, double_gross, logical_failure, sample_error,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", choices=("b1", "double_gross"), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--shots", type=int, default=10_000)
    parser.add_argument("--start-shot", type=int, default=0)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (0 < args.p < 0.75 and args.shots > 0 and args.start_shot >= 0) or args.output.exists():
        parser.error("require 0<p<0.75, shots>0, start-shot>=0, and a new output directory")
    source = source_rows(args.code, args.p).get("bp4_vanilla_ms")
    if source is None:
        parser.error("no vanilla BP4 MS source point at this code and p")

    code = build_b1_ghp() if args.code == "b1" else double_gross()
    graph = bp4_graph_from_css(code, args.p)
    decode = _variants()["both_changes"]
    zero = np.zeros(len(graph.row_ptr) - 1, dtype=np.uint8)
    decode(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
           graph.variables, graph.labels, graph.prior_llrs, zero,
           1, 16, 0.0, True)

    args.output.mkdir(parents=True)
    counts = {"shots": 0, "type_i": 0, "type_ii": 0,
              "exact_success": 0, "stabilizer_success": 0,
              "total_iterations": 0}
    rng = np.random.default_rng(args.seed)
    for _ in range(args.start_shot):
        rng.random(code.n)
    digest = hashlib.sha256()
    start = time.perf_counter()
    ledger_path = args.output / "events.jsonl.gz"
    with gzip.open(ledger_path, "wt", encoding="utf-8", compresslevel=1) as ledger:
        for shot in range(args.shots):
            truth = sample_error(rng, code.n, args.p)
            target = css_syndrome(code, truth)
            candidate, iterations, valid = decode(
                graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                graph.variables, graph.labels, graph.prior_llrs, target,
                1000, 16, 0.0, True,
            )
            type_i = not bool(valid)
            type_ii = bool(valid and logical_failure(code, truth, candidate))
            exact = bool(valid and not type_ii and np.array_equal(candidate, truth))
            stabilizer = bool(valid and not type_ii and not exact)
            record = {"shot": args.start_shot + shot,
                      "error_sha256": hashlib.sha256(truth.tobytes()).hexdigest(),
                      "iterations": int(iterations), "type_i": type_i,
                      "type_ii": type_ii, "exact_success": exact,
                      "stabilizer_success": stabilizer}
            encoded = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
            ledger.write(encoded.decode("utf-8"))
            digest.update(encoded)
            counts["shots"] += 1
            counts["type_i"] += int(type_i)
            counts["type_ii"] += int(type_ii)
            counts["exact_success"] += int(exact)
            counts["stabilizer_success"] += int(stabilizer)
            counts["total_iterations"] += int(iterations)
            if (shot + 1) % 1000 == 0:
                print(args.code, args.p, shot + 1, "/", args.shots,
                      "failures", counts["type_i"] + counts["type_ii"],
                      "elapsed_s", round(time.perf_counter() - start, 1), flush=True)

    failures = counts["type_i"] + counts["type_ii"]
    ci = binomtest(failures, args.shots).proportion_ci(.95, method="exact")
    summary = {
        "schema": "experimental-bp4-ms-both-changes-curve-v1",
        "code": args.code, "physical_p": args.p, "decoder_p0": args.p,
        "seed": args.seed, "sampler": "numpy.PCG64; existing full-v2 point seed",
        "start_shot": args.start_shot,
        "end_shot_exclusive": args.start_shot + args.shots,
        "max_iterations": 1000, "q8_scalar_scale": 16,
        "v2c_format": "float64_unbounded_three_identity_llrs",
        "projection": "exact_logsumexp_difference_then_q8_scalar",
        "check_rule": "unscaled_unoffset_min_sum", "damping": 0.0,
        "source_ler": float(source["reported_ler"]),
        "source_point_type": source["point_type"],
        "counts": counts, "failures": failures, "ler": failures / args.shots,
        "lower_95": float(ci.low), "upper_95": float(ci.high),
        "upper_95_one_sided_if_zero": (float(1 - .05 ** (1 / args.shots))
                                       if failures == 0 else None),
        "mean_iterations": counts["total_iterations"] / args.shots,
        "elapsed_seconds": time.perf_counter() - start,
        "event_ledger": ledger_path.name,
        "event_ledger_uncompressed_sha256": digest.hexdigest(),
    }
    with (args.output / "summary.json").open("x", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
