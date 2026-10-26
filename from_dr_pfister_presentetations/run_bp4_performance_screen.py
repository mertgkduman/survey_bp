"""Matched-shot diagnostic of BP4 policy sensitivity on presentation codes.

This is exploratory screening/validation, not a source-faithful paper reproduction.
Every decoder attempt is retained in an event ledger.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.stats import binomtest

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.code_constructions import build_b1_ghp, derive_css_logicals
from bp_registry.css import CssCode
from bp_registry.quaternary.compiled import _decode

from policy_kernel import binary_prior, decode_binary_oms, decode_bp4, decode_bp4_variable_serial
from run_reproduction import LABELS, bp4_graph_from_css, css_syndrome, double_gross, logical_failure, sample_error


def miao_toric_d4() -> CssCode:
    """Read the original rank-30 toric PCM from Miao et al.'s pinned repository."""
    path = Path(__file__).resolve().parent / "external/miao_2025/toric_32_2_H_30.alist"
    lines = [line.split() for line in path.read_text(encoding="utf-8").splitlines()]
    n, m = map(int, lines[0])
    if (n, m) != (32, 30):
        raise ValueError("unexpected Miao toric matrix shape")
    check_rows = np.zeros((m, n), dtype=np.uint8)
    for row in range(m):
        cols = [int(value) - 1 for value in lines[4 + n + row] if value != "0"]
        labels = [int(value) for value in lines[4 + n + m + row] if value != "0"]
        if len(cols) != len(labels):
            raise ValueError("alist row/label cardinalities disagree")
        for col, label in zip(cols, labels, strict=True):
            check_rows[row, col] = label
    if not np.all(np.isin(check_rows, (0, 1, 2))):
        raise ValueError("Miao C++ alist labels must use I=0,X=1,Z=2")
    hx = (check_rows[np.any(check_rows == 1, axis=1)] == 1).astype(np.uint8)
    hz = (check_rows[np.any(check_rows == 2, axis=1)] == 2).astype(np.uint8)
    lx, lz = derive_css_logicals(hx, hz)
    code = CssCode(hx=hx, hz=hz, lx=lx, lz=lz).validate()
    if code.n != 32 or code.k != 2 or hx.shape[0] != 15 or hz.shape[0] != 15:
        raise ValueError("Miao toric matrix did not yield [[32,2]] CSS code")
    return code


def independent_checks(code: CssCode) -> CssCode:
    """Keep the first independent rows of each CSS check matrix over GF(2)."""
    def select(matrix: np.ndarray) -> np.ndarray:
        pivots: dict[int, np.ndarray] = {}
        selected = []
        for index, row in enumerate(matrix):
            work = row.copy()
            while np.any(work):
                pivot = int(np.flatnonzero(work)[0])
                if pivot not in pivots:
                    pivots[pivot] = work
                    selected.append(index)
                    break
                work ^= pivots[pivot]
        return matrix[selected].copy()

    return CssCode(hx=select(code.hx), hz=select(code.hz), lx=code.lx, lz=code.lz).validate()


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", choices=("b1", "double_gross", "miao_toric_d4"), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-iterations", type=int, default=1000)
    parser.add_argument("--independent-checks", action="store_true")
    parser.add_argument("--configs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 0 < args.p < 0.75 or args.shots < 1 or args.max_iterations < 1:
        parser.error("require 0<p<0.75, shots>=1, and max-iterations>=1")
    if args.output.exists():
        raise FileExistsError(args.output)
    configs = json.loads(args.configs.read_text(encoding="utf-8"))
    if not isinstance(configs, list) or not configs:
        raise ValueError("configs must be a nonempty list")
    ids = [item["id"] for item in configs]
    if len(ids) != len(set(ids)):
        raise ValueError("config IDs must be unique")

    code = (build_b1_ghp() if args.code == "b1" else
            double_gross() if args.code == "double_gross" else miao_toric_d4())
    source_check_shape = [list(code.hx.shape), list(code.hz.shape)]
    if args.independent_checks:
        code = independent_checks(code)
    graphs = {}
    for item in configs:
        if item["kernel"] not in ("q8_flood", "q8_variable_serial", "f64_flood", "f64_limit60", "binary_oms"):
            raise ValueError(f"unsupported kernel {item['kernel']}")
        if "min_sum" in item and (item["kernel"] != "q8_flood" or type(item["min_sum"]) is not bool):
            raise ValueError("min_sum is a boolean option of q8_flood only")
        if item["kernel"] != "binary_oms":
            initial_p = float(item.get("initial_p", args.p))
            if not 0 < initial_p < 0.75:
                raise ValueError("initial_p must lie in (0,0.75)")
            graphs[item["id"]] = bp4_graph_from_css(code, initial_p)
    x_graph = CompiledBinaryFlooding.from_check_matrix(code.hz)
    z_graph = CompiledBinaryFlooding.from_check_matrix(code.hx)
    edge_checks = {name: np.repeat(np.arange(len(graph.row_ptr) - 1, dtype=np.int64),
                                   np.diff(graph.row_ptr)) for name, graph in graphs.items()}
    zero = np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8)
    for item in configs:
        if item["kernel"] == "q8_flood":
            graph = graphs[item["id"]]
            decode_bp4(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                       graph.variables, graph.labels, graph.prior_llrs, zero, 1,
                       int(item["scale"]), float(item["damping"]), item.get("min_sum", False))
        elif item["kernel"] == "q8_variable_serial":
            graph = graphs[item["id"]]
            decode_bp4_variable_serial(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                                       edge_checks[item["id"]], graph.variables, graph.labels,
                                       graph.prior_llrs, zero, 1, int(item["scale"]), float(item["damping"]))
        elif item["kernel"] in ("f64_flood", "f64_limit60"):
            graph = graphs[item["id"]]
            _decode(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                    graph.variables, graph.labels, graph.prior_llrs, zero,
                    60.0 if item["kernel"] == "f64_limit60" else 25.0, 1, True)
        else:
            decode_binary_oms(x_graph.row_ptr, x_graph.variables, code.n,
                              np.zeros(code.hz.shape[0], dtype=np.uint8), binary_prior(args.p),
                              1, 4, 0.1, 1.0, 0.25)

    rng = np.random.Generator(np.random.PCG64(args.seed))
    samples = []
    for _ in range(args.shots):
        truth = sample_error(rng, code.n, args.p)
        syndrome = css_syndrome(code, truth)
        # The joint graph orders X stabilizers, then Z stabilizers. Binary X
        # correction uses the latter syndrome block and vice versa.
        sz = syndrome[:code.hx.shape[0]].copy()
        sx = syndrome[code.hx.shape[0]:].copy()
        samples.append((truth, syndrome, sx, sz, hashlib.sha256(truth.tobytes()).hexdigest()))
    args.output.mkdir(parents=True)
    event_path = args.output / "events.jsonl"
    digest = hashlib.sha256()
    counts = defaultdict(lambda: {"failures": 0, "invalid_syndrome": 0,
                                  "logical_failures_with_valid_syndrome": 0,
                                  "iterations": 0, "elapsed_seconds": 0.0})
    with event_path.open("w", encoding="utf-8") as handle:
        for item in configs:
            graph = graphs.get(item["id"])
            for shot, (truth, syndrome, sx, sz, error_hash) in enumerate(samples):
                start = time.perf_counter()
                if item["kernel"] == "binary_oms":
                    xhat, ix, cx = decode_binary_oms(x_graph.row_ptr, x_graph.variables, code.n,
                                                       sx, binary_prior(args.p), args.max_iterations,
                                                       4, 0.1, 1.0, 0.25)
                    zhat, iz, cz = decode_binary_oms(z_graph.row_ptr, z_graph.variables, code.n,
                                                       sz, binary_prior(args.p), args.max_iterations,
                                                       4, 0.1, 1.0, 0.25)
                    candidate = LABELS[xhat, zhat]
                    iterations = (int(ix) + int(iz)) / 2
                    converged = bool(cx and cz)
                elif item["kernel"] == "f64_flood":
                    result = graph.run(syndrome, max_iterations=args.max_iterations)
                    candidate, iterations, converged = result.candidate, result.iterations, result.converged
                elif item["kernel"] == "f64_limit60":
                    candidate, iterations, converged = _decode(
                        graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                        graph.variables, graph.labels, graph.prior_llrs, syndrome,
                        60.0, args.max_iterations, True)
                elif item["kernel"] == "q8_variable_serial":
                    candidate, iterations, converged = decode_bp4_variable_serial(
                        graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                        edge_checks[item["id"]], graph.variables, graph.labels, graph.prior_llrs,
                        syndrome, args.max_iterations, int(item["scale"]), float(item["damping"]))
                else:
                    candidate, iterations, converged = decode_bp4(
                        graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                        graph.variables, graph.labels, graph.prior_llrs, syndrome,
                        args.max_iterations, int(item["scale"]), float(item["damping"]),
                        item.get("min_sum", False))
                elapsed = time.perf_counter() - start
                valid = bool(np.array_equal(css_syndrome(code, candidate), syndrome))
                logical = bool(valid and logical_failure(code, truth, candidate))
                failed = not valid or logical
                count = counts[item["id"]]
                count["failures"] += int(failed)
                count["invalid_syndrome"] += int(not valid)
                count["logical_failures_with_valid_syndrome"] += int(logical)
                count["iterations"] += float(iterations)
                count["elapsed_seconds"] += elapsed
                record = {"arm": item["id"], "shot": shot, "error_sha256": error_hash,
                          "failed": failed, "valid_syndrome": valid, "logical_failure": logical,
                          "converged": bool(converged), "iterations": float(iterations),
                          "elapsed_seconds": elapsed}
                line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                handle.write(line)
                digest.update(line.encode())
                if (shot + 1) % 100 == 0:
                    handle.flush()
            nfail = count["failures"]
            interval = binomtest(nfail, args.shots).proportion_ci(method="exact")
            print(f"{item['id']}: {nfail}/{args.shots}, invalid {count['invalid_syndrome']}, "
                  f"logical {count['logical_failures_with_valid_syndrome']}, "
                  f"95% CI [{interval.low:.4g}, {interval.high:.4g}]")
    summary = {"status": "exploratory_policy_screen", "code": args.code, "physical_p": args.p,
               "shots": args.shots, "seed": args.seed, "max_iterations": args.max_iterations,
               "check_selection": "independent" if args.independent_checks else "all",
               "source_check_shape": source_check_shape,
               "executed_check_shape": [list(code.hx.shape), list(code.hz.shape)],
               "configs": configs, "counts": counts, "event_ledger": event_path.name,
               "event_ledger_sha256": digest.hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
