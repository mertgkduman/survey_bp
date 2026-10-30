"""Fixed-shot mixture importance sampling for rare Yao BP/BPGD points.

Each error is drawn from d*P_p + (1-d)*P_q, decoded using the source p,
and weighted by P_p(error)/mixture(error). The estimator targets the
ordinary iid code-capacity block error rate at p. It is a separate,
explicitly labelled statistical protocol, not a source-faithful shot run.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import time

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import REFERENCE_CPU_F64
from run_point import (BINARY_METHODS, PAULI_BITS, RECEIPTS, REPO, ROOT, SOURCE,
                       _binary_masks, _code, _outcome, _point_targets,
                       _quaternary_graph, _syndrome)


def _error_draw(seed: int, p_index: int, q_index: int, shot: int, n: int,
                defensive_fraction: float, depolarizing: bool) -> tuple[np.ndarray, int, str]:
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence((seed, p_index, q_index, shot))))
    target_branch = bool(rng.random() < defensive_fraction)
    sampling_p = (p_index if target_branch else q_index) / 100000.0
    draw = rng.random(n)
    if depolarizing:
        error = np.where(draw < 1-sampling_p, 0, np.where(draw < 1-2*sampling_p/3, 1,
                         np.where(draw < 1-sampling_p/3, 2, 3))).astype(np.uint8)
    else:
        error = (draw < sampling_p).astype(np.uint8)
    return error, int(np.count_nonzero(error)), "target" if target_branch else "shifted"


def _likelihood_weight(n: int, weight: int, p: float, q: float, defensive_fraction: float) -> float:
    log_target = weight * math.log(p) + (n-weight) * math.log1p(-p)
    log_shifted = weight * math.log(q) + (n-weight) * math.log1p(-q)
    log_mix = float(np.logaddexp(math.log(defensive_fraction) + log_target,
                                math.log1p(-defensive_fraction) + log_shifted))
    return math.exp(log_target - log_mix)


def run(*, code_name: str, method: str, p: float, proposal_p: float, defensive_fraction: float,
        seed: int, start_shot: int, shots: int, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {output}")
    if code_name not in RECEIPTS["codes"] or not 0 < p < proposal_p < 1:
        raise ValueError("require source p < proposal p < 1")
    if not 0 < defensive_fraction < 1 or seed < 0 or start_shot < 0 or shots < 2:
        raise ValueError("invalid mixture or shot request")
    p_index, q_index = round(p*100000), round(proposal_p*100000)
    if abs(p_index/100000-p) > 1e-12 or abs(q_index/100000-proposal_p) > 1e-12:
        raise ValueError("probabilities must have at most five decimal places")
    depolarizing = code_name in {"a5", "b2"}
    if method not in ({"bpgd_t10"} if depolarizing else BINARY_METHODS):
        raise ValueError("unsupported method/code combination")
    code = _code(code_name)
    packed_hx = np.packbits(code.hx, axis=1, bitorder="little")
    packed_hz = np.packbits(code.hz, axis=1, bitorder="little")
    if depolarizing:
        graph, decoder = _quaternary_graph(code, method, p)
        powers = np.left_shift(np.uint64(1), np.arange(code.k, dtype=np.uint64))
        masks_x = (code.lz.astype(np.uint64) * powers[:, None]).sum(axis=0, dtype=np.uint64)
        masks_z = (code.lx.astype(np.uint64) * powers[:, None]).sum(axis=0, dtype=np.uint64)
        graph.run_qbpgd(np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8),
                        iterations_per_round=1, round_limit=1)
    else:
        graph = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=REFERENCE_CPU_F64)
        decoder = {"profile": "yao-binary-spa-v2c-cap25", "prior_p0": p, "v2c_cap": 25.0,
                   "check_product_epsilon": 1e-10, "method": method,
                   "bpgd_policy": BINARY_METHODS[method]}
        masks_x, masks_z = _binary_masks(code), None
        graph.run_paper_bp(np.zeros(code.hz.shape[0], dtype=np.uint8), error_rate=p, max_iterations=1)
    source_targets = _point_targets(code_name, p, method)
    if not source_targets:
        raise ValueError("method and target p have no source point")
    files = [Path(__file__), ROOT / "run_point.py", REPO / "src/bp_registry/code_constructions.py",
             REPO / "src/bp_registry/canonical/compiled.py", REPO / "src/bp_registry/quaternary/compiled.py",
             ROOT / "source_points.json", ROOT / "codes.json"]
    manifest = {
        "schema": "yao-importance-run-v1", "code": code_name, "method": method,
        "physical_target_p": p, "proposal_p": proposal_p, "defensive_fraction": defensive_fraction,
        "seed": seed, "start_shot": start_shot, "shots": shots,
        "sampler": "PCG64 SeedSequence(seed,target_p*100000,proposal_p*100000,global_shot); iid mixture target/shifted",
        "estimator": "mean of P_target(error)/Q_mixture(error) times independent block-failure indicator",
        "noise": "depolarizing" if depolarizing else "bit_flip",
        "code_semantic_sha256": RECEIPTS["codes"][code_name]["semantic_sha256"],
        "decoder": decoder, "source_targets": source_targets,
        "source_archive_sha256": SOURCE["archive_sha256"],
        "source_files_sha256": {str(path.relative_to(REPO)): sha256(path.read_bytes()).hexdigest() for path in files},
        "fidelity": "canonical_adaptation_importance_sampling_development",
        "outcome": "independent original-code Type I + Type II block failure; stabilizer-equivalent success",
    }
    output.mkdir(parents=True)
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    counts = {key: 0 for key in ("type_i", "type_ii", "exact_success", "stabilizer_success",
                                 "iterations", "rounds", "fixations", "elapsed_ns")}
    weighted = {"failure": 0.0, "failure_sq": 0.0, "type_i": 0.0, "type_ii": 0.0,
                "weight": 0.0, "weight_sq": 0.0}
    digest = sha256()
    started = time.monotonic()
    with (output / "events.jsonl").open("x", buffering=1) as ledger:
        for offset in range(shots):
            shot = start_shot + offset
            truth, error_weight, branch = _error_draw(seed, p_index, q_index, shot,
                                                       code.n, defensive_fraction, depolarizing)
            weight = _likelihood_weight(code.n, error_weight, p, proposal_p, defensive_fraction)
            if depolarizing:
                bits = PAULI_BITS[truth]
                syndrome = np.concatenate((_syndrome(packed_hx, bits[:, 1]),
                                           _syndrome(packed_hz, bits[:, 0])))
            else:
                syndrome = _syndrome(packed_hz, truth)
            start_ns = time.perf_counter_ns()
            if depolarizing:
                decoded = graph.run_qbpgd(syndrome, iterations_per_round=10, epsilon=1e-10)
            elif method == "bp":
                decoded = graph.run_paper_bp(syndrome, error_rate=p, max_iterations=100)
            else:
                sweeps, rounds, order = BINARY_METHODS[method]
                if order == "uniform_random":
                    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence((seed, p_index, shot, 777))))
                    draws = rng.random(rounds or code.n)
                else:
                    draws = None
                decoded = graph.run_paper_bpgd(syndrome, error_rate=p, sweeps_per_round=sweeps,
                                               round_limit=rounds, order=order, random_draws=draws)
            elapsed_ns = time.perf_counter_ns() - start_ns
            outcome = _outcome(decoded.candidate, truth, syndrome, packed_hx, packed_hz,
                               code, masks_x, masks_z)
            record = {**outcome, "iterations": decoded.iterations,
                      "rounds": getattr(decoded, "rounds", 0),
                      "fixations": getattr(decoded, "fixations", 0),
                      "elapsed_ns": elapsed_ns, "claimed_convergence": decoded.converged,
                      "candidate_sha256": sha256(decoded.candidate.tobytes()).hexdigest()}
            event = {"schema": "yao-importance-shot-v1", "shot": shot,
                     "error_sha256": sha256(truth.tobytes()).hexdigest(),
                     "syndrome_sha256": sha256(syndrome.tobytes()).hexdigest(),
                     "error_weight": error_weight, "proposal_branch": branch,
                     "importance_weight": weight, "outcome": record}
            row = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            ledger.write(row)
            digest.update(row.encode())
            for key in counts:
                counts[key] += int(record[key])
            failure = int(record["type_i"] or record["type_ii"])
            weighted["failure"] += weight * failure
            weighted["failure_sq"] += weight * weight * failure
            weighted["type_i"] += weight * int(record["type_i"])
            weighted["type_ii"] += weight * int(record["type_ii"])
            weighted["weight"] += weight
            weighted["weight_sq"] += weight * weight
            if (offset + 1) % 1000 == 0:
                ledger.flush()
                print(code_name, method, p, proposal_p, offset + 1,
                      counts["type_i"] + counts["type_ii"], flush=True)
    summary = {"schema": "yao-importance-summary-v1", "code": code_name, "method": method,
               "physical_target_p": p, "proposal_p": proposal_p,
               "seed": seed, "start_shot": start_shot, "shots": shots,
               "counts": counts, "weighted_sums": weighted, "source_targets": source_targets,
               "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
               "events_sha256": digest.hexdigest(), "wall_seconds": time.monotonic() - started}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=tuple(RECEIPTS["codes"]), required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--proposal-p", type=float, required=True)
    parser.add_argument("--defensive-fraction", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=20261033)
    parser.add_argument("--start-shot", type=int, default=0)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(code_name=args.code, method=args.method, p=args.p,
                 proposal_p=args.proposal_p, defensive_fraction=args.defensive_fraction,
                 seed=args.seed, start_shot=args.start_shot, shots=args.shots,
                 output=args.output)
    print(json.dumps({key: result[key] for key in ("code", "method", "physical_target_p",
                                                    "proposal_p", "shots", "weighted_sums")}, sort_keys=True))
