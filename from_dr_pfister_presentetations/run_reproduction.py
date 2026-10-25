"""Run a bounded same-error pilot for the four presentation policy variants."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.code_constructions import build_b1_ghp, derive_css_logicals
from bp_registry.css import CssCode
from bp_registry.quaternary.compiled import CompiledBp4Graph

from policy_kernel import binary_prior, decode_binary_oms, decode_bp4


ROOT = Path(__file__).resolve().parent
BITS = np.asarray(((0, 0), (1, 0), (1, 1), (0, 1)), dtype=np.uint8)
LABELS = np.asarray(((0, 3), (1, 2)), dtype=np.uint8)
ARMS = ("bp4_vanilla_sp", "bp4_vanilla_ms", "binary_tuned_oms", "bp4_tuned_sp")


def double_gross() -> CssCode:
    """Bravyi et al. BB (12,12): A=x^3+y^7+y^2, B=x^2+x+y^3."""
    eye = np.eye(12, dtype=np.uint8)
    shift = lambda power: np.roll(eye, power, axis=1)
    x = lambda power: np.kron(shift(power), eye)
    y = lambda power: np.kron(eye, shift(power))
    a = x(3) ^ y(7) ^ y(2)
    b = x(2) ^ x(1) ^ y(3)
    hx, hz = np.hstack((a, b)), np.hstack((b.T, a.T))
    lx, lz = derive_css_logicals(hx, hz)
    code = CssCode(hx=hx, hz=hz, lx=lx, lz=lz).validate()
    if code.n != 288 or code.k != 12:
        raise RuntimeError(f"double-Gross structural check failed: n={code.n}, k={code.k}")
    return code


def sample_error(rng: np.random.Generator, n: int, p: float) -> np.ndarray:
    draw = rng.random(n)
    return np.where(draw < 1.0 - p, 0,
                    np.where(draw < 1.0 - 2.0 * p / 3.0, 1,
                             np.where(draw < 1.0 - p / 3.0, 2, 3))).astype(np.uint8)


def css_syndrome(code: CssCode, labels: np.ndarray) -> np.ndarray:
    bits = BITS[labels]
    sx = (code.hx.astype(np.int64) @ bits[:, 1].astype(np.int64) % 2).astype(np.uint8)
    sz = (code.hz.astype(np.int64) @ bits[:, 0].astype(np.int64) % 2).astype(np.uint8)
    return np.concatenate((sx, sz))


def bp4_graph_from_css(code: CssCode, p: float) -> CompiledBp4Graph:
    """Index CSS rows directly; PauliCode's dense pairwise proof exceeds B1 RAM."""
    checks = np.vstack((np.where(code.hx, 1, 0), np.where(code.hz, 3, 0))).astype(np.uint8)
    rows, cols = np.nonzero(checks)
    labels = checks[rows, cols]
    variables = np.asarray(cols, dtype=np.int64)
    row_ptr = np.bincount(rows, minlength=checks.shape[0]).astype(np.int64)
    row_ptr = np.concatenate((np.asarray((0,), dtype=np.int64), np.cumsum(row_ptr)))
    variable_ptr = np.bincount(variables, minlength=code.n).astype(np.int64)
    variable_ptr = np.concatenate((np.asarray((0,), dtype=np.int64), np.cumsum(variable_ptr)))
    variable_edges = np.empty(len(labels), dtype=np.int64)
    offsets = variable_ptr[:-1].copy()
    for edge, variable in enumerate(variables):
        variable_edges[offsets[variable]] = edge
        offsets[variable] += 1
    prior_llrs = np.tile(np.log((1.0 - p) / (p / 3.0)), (code.n, 3))
    for value in (row_ptr, variable_ptr, variable_edges, variables, labels, prior_llrs):
        value.setflags(write=False)
    return CompiledBp4Graph(row_ptr, variable_ptr, variable_edges, variables, labels, prior_llrs)


def logical_failure(code: CssCode, truth: np.ndarray, candidate: np.ndarray) -> bool:
    residual = BITS[truth] ^ BITS[candidate]
    if code.lx is None or code.lz is None:
        raise RuntimeError("logical basis required")
    return bool(np.any((code.lz.astype(np.int64) @ residual[:, 0].astype(np.int64)) % 2)
                or np.any((code.lx.astype(np.int64) @ residual[:, 1].astype(np.int64)) % 2))


def _percentile(values: list[float], p: float) -> float:
    return float(np.percentile(values, p))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", choices=("b1", "double_gross"), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--shots", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--max-iterations", type=int, default=1000)
    args = parser.parse_args()
    if not (0.0 < args.p < 0.75) or args.shots < 1 or args.max_iterations < 1:
        parser.error("require 0<p<0.75, shots>=1, and max-iterations>=1")
    code = build_b1_ghp() if args.code == "b1" else double_gross()
    code_id = "B1_882_24" if args.code == "b1" else "double_Gross_288_12_18"
    bp4 = bp4_graph_from_css(code, args.p)
    x_graph = CompiledBinaryFlooding.from_check_matrix(code.hz)
    z_graph = CompiledBinaryFlooding.from_check_matrix(code.hx)
    # Compile every Numba signature before the first timed decode.
    zero4 = np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8)
    zero_x = np.zeros(code.hz.shape[0], dtype=np.uint8)
    decode_bp4(bp4.row_ptr, bp4.variable_ptr, bp4.variable_edges, bp4.variables, bp4.labels,
               bp4.prior_llrs, zero4, 1, 16, 0.0, False)
    decode_bp4(bp4.row_ptr, bp4.variable_ptr, bp4.variable_edges, bp4.variables, bp4.labels,
               bp4.prior_llrs, zero4, 1, 16, 0.0, True)
    decode_binary_oms(x_graph.row_ptr, x_graph.variables, code.n, zero_x,
                      binary_prior(args.p), 1, 4, 0.1, 1.0, 0.25)
    run_stem = f"pilot_{args.code}_p{args.p:.3f}_n{args.shots}_seed{args.seed}_t{args.max_iterations}"
    result_path = ROOT / "results" / f"{run_stem}.json"
    events_path = ROOT / "results" / f"{run_stem}.events.jsonl"
    if result_path.exists() or events_path.exists():
        raise FileExistsError("pilot output already exists; use a fresh seed or remove only your own exploratory output")
    rng = np.random.Generator(np.random.PCG64(args.seed))
    failures = defaultdict(int)
    invalid = defaultdict(int)
    work = defaultdict(list)
    elapsed = defaultdict(list)
    discordance = defaultdict(lambda: {"rescue": 0, "loss": 0})
    event_digest = hashlib.sha256()
    start = time.time()
    with events_path.open("w", encoding="utf-8") as handle:
        for shot in range(args.shots):
            truth = sample_error(rng, code.n, args.p)
            syndrome = css_syndrome(code, truth)
            x_syndrome = (code.hz.astype(np.int64) @ BITS[truth, 0].astype(np.int64) % 2).astype(np.uint8)
            z_syndrome = (code.hx.astype(np.int64) @ BITS[truth, 1].astype(np.int64) % 2).astype(np.uint8)
            record = {"category": "paired_shot", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                      "shot": shot, "error_sha256": hashlib.sha256(truth.tobytes()).hexdigest(), "arms": {}}
            for arm in ARMS:
                tick = time.perf_counter_ns()
                if arm == "binary_tuned_oms":
                    prior = binary_prior(args.p)
                    xhat, ix, cx = decode_binary_oms(x_graph.row_ptr, x_graph.variables, code.n, x_syndrome,
                                                       prior, args.max_iterations, 4, 0.1, 1.0, 0.25)
                    zhat, iz, cz = decode_binary_oms(z_graph.row_ptr, z_graph.variables, code.n, z_syndrome,
                                                       prior, args.max_iterations, 4, 0.1, 1.0, 0.25)
                    candidate = LABELS[xhat, zhat]
                    iterations = [int(ix), int(iz)]
                    equivalent_work = (ix + iz) / 2.0
                    converged = bool(cx and cz)
                else:
                    scale = 4 if arm == "bp4_tuned_sp" else 16
                    damping = 0.1 if arm == "bp4_tuned_sp" else 0.0
                    min_sum = arm == "bp4_vanilla_ms"
                    candidate, iterations, converged = decode_bp4(
                        bp4.row_ptr, bp4.variable_ptr, bp4.variable_edges, bp4.variables, bp4.labels,
                        bp4.prior_llrs, syndrome, args.max_iterations, scale, damping, min_sum)
                    iterations = int(iterations)
                    equivalent_work = float(iterations)
                duration = (time.perf_counter_ns() - tick) / 1e9
                valid = bool(np.array_equal(css_syndrome(code, candidate), syndrome))
                failed = not valid or logical_failure(code, truth, candidate)
                failures[arm] += int(failed)
                invalid[arm] += int(not valid)
                work[arm].append(equivalent_work)
                elapsed[arm].append(duration)
                record["arms"][arm] = {"failed": bool(failed), "valid_syndrome": valid,
                                        "converged": converged, "iterations": iterations,
                                        "bp4_equivalent_work": equivalent_work, "elapsed_seconds": duration}
            old = record["arms"]["bp4_vanilla_sp"]["failed"]
            new = record["arms"]["bp4_tuned_sp"]["failed"]
            discordance["bp4_tuned_sp_vs_bp4_vanilla_sp"]["rescue"] += int(old and not new)
            discordance["bp4_tuned_sp_vs_bp4_vanilla_sp"]["loss"] += int(new and not old)
            line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            handle.write(line)
            event_digest.update(line.encode())
            if (shot + 1) % 100 == 0:
                print(f"{shot + 1}/{args.shots} shots", file=sys.stderr, flush=True)
    result = {
        "schema": "presentation-paired-pilot-v1", "status": "exploratory_adaptation", "code": code_id,
        "code_matrix_sha256": {"hx": hashlib.sha256(code.hx.tobytes()).hexdigest(), "hz": hashlib.sha256(code.hz.tobytes()).hexdigest()},
        "p": args.p, "shots": args.shots, "seed": args.seed, "max_iterations": args.max_iterations,
        "event_ledger": events_path.name, "event_ledger_sha256": event_digest.hexdigest(),
        "wall_seconds": time.time() - start, "arms": {}, "paired": dict(discordance),
        "limitations": ["Q8 stage and rounding assumed", "V2C damping target assumed", "flooding assumed",
                        "binary marginal channel assumed", "timing includes Python call overhead and is not a controlled latency comparison"],
    }
    for arm in ARMS:
        result["arms"][arm] = {"failures": failures[arm], "invalid_syndrome": invalid[arm],
                               "ler": failures[arm] / args.shots,
                               "mean_bp4_equivalent_work": float(np.mean(work[arm])),
                               "p99_bp4_equivalent_work": _percentile(work[arm], 99),
                               "p99_9_bp4_equivalent_work": _percentile(work[arm], 99.9),
                               "mean_elapsed_seconds": float(np.mean(elapsed[arm]))}
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result_path)


if __name__ == "__main__":
    main()
