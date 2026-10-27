"""Run one paired presentation-curve point with promoted canonical v2 kernels.

Each process owns one (code, p) point. Its gzip ledger contains every attempted
arm/shot, including syndrome-inconsistent outcomes. The source Q8 rules are
explicit controls; they are never mislabeled as canonical float64 v2.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from dataclasses import replace
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.stats import binomtest

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
from bp_registry.code_constructions import build_b1_ghp
from bp_registry.quaternary.numerics import QBP4_F64_V2

from policy_kernel import binary_prior, decode_binary_oms, decode_bp4
from run_reproduction import (
    LABELS, bp4_graph_from_css, css_syndrome, double_gross,
    logical_failure, sample_error,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results/source_curves.csv"
CODE_IDS = {"b1": "B1_882_24", "double_gross": "double_Gross_288_12_18"}


def source_rows(code: str, p: float) -> dict[str, dict]:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle)
                if row["code"] == CODE_IDS[code] and abs(float(row["p"]) - p) < 1e-12]
    if not rows:
        raise ValueError(f"no source points at {code}, p={p}")
    return {row["decoder"]: row for row in rows}


def shot_target(row: dict, p: float, *, target_failures: int, max_shots: int) -> int:
    if row["point_type"] == "upper_95_one_sided":
        return min(max_shots, max(100_000, target_failures * int(row["reported_trials"]) // 3))
    rate = float(row["reported_ler"])
    floor = 20_000 if p >= .12 else 50_000
    return min(max_shots, max(floor, math.ceil(target_failures / rate)))


def intervals(failures: int, shots: int) -> dict[str, float]:
    ci = binomtest(failures, shots).proportion_ci(confidence_level=.95, method="exact")
    return {"lower_95_two_sided": float(ci.low), "upper_95_two_sided": float(ci.high),
            "upper_95_one_sided_if_zero": float(1 - .05 ** (1 / shots)) if failures == 0 else None}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", choices=tuple(CODE_IDS), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-iterations", type=int, default=1000)
    parser.add_argument("--target-failures", type=int, default=30)
    parser.add_argument("--max-shots", type=int, default=10_000_000)
    args = parser.parse_args()
    if args.output.exists() or args.max_iterations < 1 or args.target_failures < 1 or args.max_shots < 1:
        parser.error("output must not exist; iteration, target, and shot caps must be positive")
    source = source_rows(args.code, args.p)
    code = build_b1_ghp() if args.code == "b1" else double_gross()
    max_n = max(shot_target(row, args.p, target_failures=args.target_failures,
                            max_shots=args.max_shots) for row in source.values())
    arms = {}
    for name, row in source.items():
        count = shot_target(row, args.p, target_failures=args.target_failures,
                            max_shots=args.max_shots)
        if name == "bp4_vanilla_sp":
            arms["bp4_vanilla_sp_v2"] = (name, count)
        elif name == "bp4_vanilla_ms":
            arms["bp4_vanilla_ms_q8"] = (name, count)
        elif name == "bp4_tuned_sp":
            arms["bp4_tuned_sp_v2"] = (name, count)
        elif name == "binary_tuned_oms":
            arms["binary_tuned_oms_q8"] = (name, count)
            arms["binary_tuned_spa_v2"] = (name, count)
        else:
            raise ValueError(name)
    base = bp4_graph_from_css(code, args.p)
    bp4 = {
        0.0: replace(base, profile=replace(QBP4_F64_V2, v2c_damping=0.0)),
        0.1: replace(base, profile=QBP4_F64_V2),
    }
    xgraph = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=BINARY_SPA_F64_V2)
    zgraph = CompiledBinaryFlooding.from_check_matrix(code.hx, profile=BINARY_SPA_F64_V2)
    xb, zb = xgraph.bind_error_rate(2 * args.p / 3), zgraph.bind_error_rate(2 * args.p / 3)
    q8_prior = binary_prior(args.p)
    split = code.hx.shape[0]
    zero = np.zeros(split + code.hz.shape[0], dtype=np.uint8)
    # Warm every Numba specialization before the ledger starts.
    if "bp4_vanilla_sp_v2" in arms:
        bp4[0.0].run(zero, max_iterations=1)
    if "bp4_tuned_sp_v2" in arms:
        bp4[0.1].run(zero, max_iterations=1)
    if "bp4_vanilla_ms_q8" in arms:
        decode_bp4(base.row_ptr, base.variable_ptr, base.variable_edges,
                   base.variables, base.labels, base.prior_llrs, zero, 1, 16, 0.0, True)
    if "binary_tuned_spa_v2" in arms:
        xb.run(zero[split:], max_iterations=1)
        zb.run(zero[:split], max_iterations=1)
    if "binary_tuned_oms_q8" in arms:
        decode_binary_oms(xgraph.row_ptr, xgraph.variables, code.n, zero[split:],
                          q8_prior, 1, 4, .1, 1., .25)
        decode_binary_oms(zgraph.row_ptr, zgraph.variables, code.n, zero[:split],
                          q8_prior, 1, 4, .1, 1., .25)
    args.output.mkdir(parents=True)
    counts = defaultdict(lambda: {"shots": 0, "failures": 0, "type_i": 0,
                                  "type_ii": 0, "exact_success": 0,
                                  "stabilizer_success": 0, "total_work": 0.0,
                                  "total_elapsed_seconds": 0.0})
    paired = defaultdict(lambda: {"overlap": 0, "rescues": 0, "losses": 0,
                                  "both_fail": 0, "both_succeed": 0})
    rng = np.random.Generator(np.random.PCG64(args.seed))
    digest = hashlib.sha256()
    start_all = time.perf_counter()
    with gzip.open(args.output / "events.jsonl.gz", "wt", encoding="utf-8", compresslevel=1) as handle:
        for shot in range(max_n):
            truth = sample_error(rng, code.n, args.p)
            syndrome = css_syndrome(code, truth)
            error_hash = hashlib.sha256(truth.tobytes()).hexdigest()
            outcomes = {}
            for arm, (source_name, target) in arms.items():
                if shot >= target:
                    continue
                tick = time.perf_counter()
                if arm == "bp4_vanilla_sp_v2" or arm == "bp4_tuned_sp_v2":
                    result = bp4[0.0 if arm == "bp4_vanilla_sp_v2" else 0.1].run(
                        syndrome, max_iterations=args.max_iterations)
                    candidate, iterations = result.candidate, int(result.iterations)
                    work = float(iterations)
                elif arm == "bp4_vanilla_ms_q8":
                    candidate, iterations, _ = decode_bp4(
                        base.row_ptr, base.variable_ptr, base.variable_edges,
                        base.variables, base.labels, base.prior_llrs, syndrome,
                        args.max_iterations, 16, 0.0, True)
                    work = float(iterations)
                else:
                    sx, sz = syndrome[split:], syndrome[:split]
                    if arm == "binary_tuned_spa_v2":
                        xr = xb.run(sx, max_iterations=args.max_iterations)
                        zr = zb.run(sz, max_iterations=args.max_iterations)
                        xhat, zhat = xr.candidate, zr.candidate
                        iterations = [int(xr.iterations), int(zr.iterations)]
                    else:
                        xhat, ix, _ = decode_binary_oms(
                            xgraph.row_ptr, xgraph.variables, code.n, sx, q8_prior,
                            args.max_iterations, 4, .1, 1., .25)
                        zhat, iz, _ = decode_binary_oms(
                            zgraph.row_ptr, zgraph.variables, code.n, sz, q8_prior,
                            args.max_iterations, 4, .1, 1., .25)
                        iterations = [int(ix), int(iz)]
                    candidate = LABELS[xhat, zhat]
                    work = sum(iterations) / 2
                elapsed = time.perf_counter() - tick
                valid = bool(np.array_equal(css_syndrome(code, candidate), syndrome))
                type_ii = bool(valid and logical_failure(code, truth, candidate))
                failed = not valid or type_ii
                exact = bool(valid and not type_ii and np.array_equal(candidate, truth))
                counter = counts[arm]
                counter["shots"] += 1
                counter["failures"] += int(failed)
                counter["type_i"] += int(not valid)
                counter["type_ii"] += int(type_ii)
                counter["exact_success"] += int(exact)
                counter["stabilizer_success"] += int(valid and not type_ii and not exact)
                counter["total_work"] += work
                counter["total_elapsed_seconds"] += elapsed
                record = {"arm": arm, "source_decoder": source_name, "shot": shot,
                          "error_sha256": error_hash, "failed": failed,
                          "type_i": not valid, "type_ii": type_ii,
                          "exact_success": exact,
                          "stabilizer_success": bool(valid and not type_ii and not exact),
                          "iterations": iterations, "bp4_equivalent_work": work,
                          "elapsed_seconds": elapsed}
                line = json.dumps(record, separators=(",", ":")) + "\n"
                handle.write(line)
                digest.update(line.encode())
                outcomes[arm] = failed
            for first, second in (("bp4_tuned_sp_v2", "binary_tuned_spa_v2"),
                                  ("bp4_tuned_sp_v2", "binary_tuned_oms_q8"),
                                  ("binary_tuned_spa_v2", "binary_tuned_oms_q8"),
                                  ("bp4_vanilla_sp_v2", "bp4_tuned_sp_v2")):
                if first in outcomes and second in outcomes:
                    item = paired[f"{first}__vs__{second}"]
                    item["overlap"] += 1
                    a, b = outcomes[first], outcomes[second]
                    item["rescues"] += int(a and not b)
                    item["losses"] += int(not a and b)
                    item["both_fail"] += int(a and b)
                    item["both_succeed"] += int(not a and not b)
            if (shot + 1) % 100_000 == 0 or shot + 1 == max_n:
                progress = {arm: f"{c['failures']}/{c['shots']}" for arm, c in counts.items()}
                print(f"{args.code} p={args.p} {shot + 1}/{max_n}: {progress}", flush=True)
    arm_summaries = {}
    for arm, (source_name, target) in arms.items():
        c = dict(counts[arm])
        assert c["shots"] == target
        row = source[source_name]
        arm_summaries[arm] = {"source_decoder": source_name,
                              "source_rate_or_bound": float(row["reported_ler"]),
                              "source_point_type": row["point_type"],
                              "source_trials": int(row["reported_trials"]) if row["reported_trials"] else None,
                              **c, "ler": c["failures"] / target,
                              "mean_work": c["total_work"] / target,
                              **intervals(c["failures"], target)}
    summary = {"schema": "full-v2-curve-point-v1", "code": args.code,
               "physical_p": args.p, "decoder_p0": args.p,
               "binary_marginal_prior": 2 * args.p / 3,
               "seed": args.seed, "sampler": "numpy.PCG64; shared prefix per (code,p)",
               "max_iterations": args.max_iterations,
               "pauli_order": "I,X,Y,Z", "shot_target_rule": {
                   "target_failures": args.target_failures, "max_shots": args.max_shots,
                   "highest_p_floor": 20_000, "other_floor": 50_000},
               "profile_ids": {"bp4_v2": QBP4_F64_V2.profile_id,
                               "binary_spa_v2": BINARY_SPA_F64_V2.profile_id},
               "arms": arm_summaries, "paired": dict(paired),
               "elapsed_seconds": time.perf_counter() - start_all,
               "event_ledger": "events.jsonl.gz",
               "uncompressed_event_ledger_sha256": digest.hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({arm: (v["failures"], v["shots"]) for arm, v in arm_summaries.items()}), flush=True)


if __name__ == "__main__":
    main()
