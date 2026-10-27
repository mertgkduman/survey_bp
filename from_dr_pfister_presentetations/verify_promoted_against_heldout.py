"""Replay a held-out arm through the promoted compiled canonical profile."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
from bp_registry.code_constructions import build_b1_ghp
from bp_registry.quaternary.numerics import QBP4_F64_V2

from run_bp4_performance_screen import miao_toric_d4
from run_reproduction import LABELS, bp4_graph_from_css, css_syndrome, double_gross, logical_failure, sample_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--arm", required=True)
    args = parser.parse_args()
    summary = json.loads((args.run / "summary.json").read_text())
    item = next((x for x in summary["configs"] if x["id"] == args.arm), None)
    if item is None or args.arm not in {"product_e10_d01", "binary_product_e10_d01"}:
        parser.error("arm must be a selected v2 product-check candidate")
    payload = (args.run / summary["event_ledger"]).read_bytes()
    if hashlib.sha256(payload).hexdigest() != summary["event_ledger_sha256"]:
        raise ValueError("event ledger digest mismatch")
    expected = [json.loads(line) for line in payload.splitlines() if json.loads(line)["arm"] == args.arm]
    if len(expected) != summary["shots"]:
        raise ValueError("selected arm is incomplete")
    code = (build_b1_ghp() if summary["code"] == "b1" else
            double_gross() if summary["code"] == "double_gross" else miao_toric_d4())
    p = summary["physical_p"]
    p0 = float(item.get("initial_p", p))
    if args.arm == "product_e10_d01":
        graph = replace(bp4_graph_from_css(code, p0), profile=QBP4_F64_V2)
    else:
        xgraph = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=BINARY_SPA_F64_V2)
        zgraph = CompiledBinaryFlooding.from_check_matrix(code.hx, profile=BINARY_SPA_F64_V2)
    rng = np.random.Generator(np.random.PCG64(summary["seed"]))
    matched = 0
    for shot, record in enumerate(expected):
        truth = sample_error(rng, code.n, p)
        syndrome = css_syndrome(code, truth)
        if hashlib.sha256(truth.tobytes()).hexdigest() != record["error_sha256"]:
            raise ValueError(f"sample mismatch at shot {shot}")
        if args.arm == "product_e10_d01":
            result = graph.run(syndrome, max_iterations=summary["max_iterations"])
            candidate = result.candidate
            iterations = result.iterations
            converged = result.converged
        else:
            split = code.hx.shape[0]
            xr = xgraph.run(syndrome[split:], error_rate=2*p0/3,
                            max_iterations=summary["max_iterations"])
            zr = zgraph.run(syndrome[:split], error_rate=2*p0/3,
                            max_iterations=summary["max_iterations"])
            candidate = LABELS[xr.candidate, zr.candidate]
            iterations = [xr.iterations, zr.iterations]
            converged = bool(xr.converged and zr.converged)
        valid = bool(np.array_equal(css_syndrome(code, candidate), syndrome))
        type_ii = bool(valid and logical_failure(code, truth, candidate))
        actual = {
            "iterations": iterations, "converged": converged, "failed": not valid or type_ii,
            "type_i": not valid, "type_ii": type_ii,
            "exact_success": bool(valid and not type_ii and np.array_equal(candidate, truth)),
            "stabilizer_success": bool(valid and not type_ii and not np.array_equal(candidate, truth)),
        }
        if any(record[key] != value for key, value in actual.items()):
            raise AssertionError(f"promoted kernel diverged at shot {shot}: {actual} vs {record}")
        matched += 1
    print(f"{args.run.name}: promoted {args.arm} matched {matched} ledgered shots")


if __name__ == "__main__":
    main()
