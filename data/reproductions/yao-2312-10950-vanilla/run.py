"""Paired vanilla BP campaign for Yao et al. arXiv:2312.10950v2.

Run from the repository root with ``PYTHONPATH=src python .../run.py``.
Every physical error is decoded by all four frozen policies. The decoder
receives only syndrome and its declared prior; the evaluator sees truth.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
import math
from pathlib import Path
import time
from typing import NamedTuple

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2, REFERENCE_CPU_F64
from bp_registry.code_constructions import build_b2_ghp
from bp_registry.css import CssCode, semantic_sha256
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V1, QBP4_F64_V2
from bp_registry.quaternary.problems import build_qbpgd_a5_css_artifact


ROOT = Path(__file__).resolve().parent
ARMS = ("bp4_v1", "bp4_v2", "binary_v1", "binary_v2")
PAULI_BITS = np.asarray(((0, 0), (1, 0), (1, 1), (0, 1)), dtype=np.uint8)
BITS_TO_PAULI = np.asarray(((0, 3), (1, 2)), dtype=np.uint8)


def _load_code(name: str) -> CssCode:
    if name == "a5":
        code, _ = build_qbpgd_a5_css_artifact()
    elif name == "b2":
        code = build_b2_ghp()
    else:
        raise ValueError(f"unknown study code {name}")
    receipt = json.loads((ROOT / "codes" / f"{name}.json").read_text())
    if (semantic_sha256(code) != receipt["css_semantic_sha256"]
            or sha256(code.hx.tobytes()).hexdigest() != receipt["hx_sha256"]
            or sha256(code.hz.tobytes()).hexdigest() != receipt["hz_sha256"]
            or code.n != receipt["parameters"]["n"] or code.k != receipt["parameters"]["k"]):
        raise ValueError("constructed CSS code differs from pinned source receipt")
    return code


def _decoder_specs() -> dict[str, dict[str, object]]:
    specs = {name: json.loads((ROOT / "decoders" / f"{name}.json").read_text()) for name in ARMS}
    expected_profiles = {
        "bp4_v1": QBP4_F64_V1.profile_id,
        "bp4_v2": "quaternary-bp4-f64-v2-undamped",
        "binary_v1": REFERENCE_CPU_F64.profile_id,
        "binary_v2": "binary-spa-flooding-f64-v2-undamped",
    }
    for name, spec in specs.items():
        if (spec.get("schema") != "vanilla-bp-decoder-v1" or spec.get("id") != name
                or spec.get("check_rule") != "sum_product"
                or spec.get("numerical_profile") != expected_profiles[name]
                or spec.get("message_resolution") != "float64"
                or spec.get("max_iterations") != 100 or spec.get("damping_old") != 0.0):
            raise ValueError(f"invalid or unsupported decoder policy file {name}")
        if name.endswith("v2") and (spec.get("check_cap", "missing") is not None
                                    or spec.get("product_epsilon") != 1e-10):
            raise ValueError(f"unsupported v2 numerical details in {name}")
    return specs


def _graphs(code: CssCode, p: float):
    bp4_base = CompiledBp4Graph.from_css(code, p)
    bp4_v1 = replace(bp4_base, profile=QBP4_F64_V1)
    bp4_v2 = replace(bp4_base, profile=replace(
        QBP4_F64_V2, profile_id="quaternary-bp4-f64-v2-undamped", v2c_damping=0.0,
    ))
    q = 2.0 * p / 3.0
    binary_v1_x = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=REFERENCE_CPU_F64).bind_error_rate(q)
    binary_v1_z = CompiledBinaryFlooding.from_check_matrix(code.hx, profile=REFERENCE_CPU_F64).bind_error_rate(q)
    binary_v2_profile = replace(BINARY_SPA_F64_V2, profile_id="binary-spa-flooding-f64-v2-undamped", v2c_damping=0.0)
    binary_v2_x = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=binary_v2_profile).bind_error_rate(q)
    binary_v2_z = CompiledBinaryFlooding.from_check_matrix(code.hx, profile=binary_v2_profile).bind_error_rate(q)
    return {"bp4_v1": bp4_v1, "bp4_v2": bp4_v2,
            "binary_v1": (binary_v1_x, binary_v1_z),
            "binary_v2": (binary_v2_x, binary_v2_z)}


def _logical_masks(code: CssCode) -> tuple[np.ndarray, np.ndarray]:
    if code.lx is None or code.lz is None or code.k > 63:
        raise ValueError("paired logical basis with at most 63 logical qubits required")
    weights = np.left_shift(np.uint64(1), np.arange(code.k, dtype=np.uint64))
    x_masks = (code.lz.astype(np.uint64) * weights[:, None]).sum(axis=0, dtype=np.uint64)
    z_masks = (code.lx.astype(np.uint64) * weights[:, None]).sum(axis=0, dtype=np.uint64)
    return x_masks, z_masks


def _logical_signature(paulis: np.ndarray, masks: tuple[np.ndarray, np.ndarray]) -> int:
    bits = PAULI_BITS[paulis]
    x, z = masks
    value = np.uint64(0)
    if np.any(bits[:, 0]):
        value ^= np.bitwise_xor.reduce(x[bits[:, 0] != 0])
    if np.any(bits[:, 1]):
        value ^= np.bitwise_xor.reduce(z[bits[:, 1] != 0])
    return int(value)


class _SyndromeEvaluator(NamedTuple):
    hx_packed: np.ndarray
    hz_packed: np.ndarray


def _syndrome_evaluator(code: CssCode) -> _SyndromeEvaluator:
    return _SyndromeEvaluator(np.packbits(code.hx, axis=1, bitorder="little"),
                              np.packbits(code.hz, axis=1, bitorder="little"))


def _original_syndrome(evaluator: _SyndromeEvaluator, paulis: np.ndarray) -> np.ndarray:
    bits = PAULI_BITS[paulis]
    x = np.packbits(bits[:, 0], bitorder="little")
    z = np.packbits(bits[:, 1], bitorder="little")
    sx = (np.bitwise_count(np.bitwise_and(evaluator.hx_packed, z)).sum(axis=1) & 1).astype(np.uint8)
    sz = (np.bitwise_count(np.bitwise_and(evaluator.hz_packed, x)).sum(axis=1) & 1).astype(np.uint8)
    return np.concatenate((sx, sz))


def _sample(rng: np.random.Generator, n: int, p: float) -> np.ndarray:
    draw = rng.random(n)
    return np.where(draw < 1-p, 0, np.where(draw < 1-2*p/3, 1,
                    np.where(draw < 1-p/3, 2, 3))).astype(np.uint8)


def _one_arm(name, graph, syndrome, code, evaluator, truth, truth_signature, masks, max_iterations):
    start = time.perf_counter_ns()
    if name.startswith("bp4"):
        result = graph.run(syndrome, max_iterations=max_iterations)
        candidate = result.candidate
        iterations = (result.iterations,)
        claimed_convergence = result.converged
    else:
        x_graph, z_graph = graph
        sx = syndrome[code.hx.shape[0]:]
        sz = syndrome[:code.hx.shape[0]]
        x_result = x_graph.run(sx, max_iterations=max_iterations)
        z_result = z_graph.run(sz, max_iterations=max_iterations)
        candidate = BITS_TO_PAULI[x_result.candidate, z_result.candidate]
        iterations = (x_result.iterations, z_result.iterations)
        claimed_convergence = x_result.converged and z_result.converged
    elapsed_ns = time.perf_counter_ns() - start
    syndrome_valid = np.array_equal(_original_syndrome(evaluator, candidate), syndrome)
    if bool(claimed_convergence) != bool(syndrome_valid):
        raise RuntimeError(f"decoder and independent syndrome disagree for {name}")
    type_i = not syndrome_valid
    type_ii = bool(syndrome_valid and _logical_signature(candidate, masks) != truth_signature)
    exact = bool(syndrome_valid and not type_ii and np.array_equal(candidate, truth))
    record = {
        "candidate_digest": sha256(candidate.tobytes()).hexdigest()[:20],
        "iterations": list(iterations),
        "elapsed_ns": elapsed_ns,
        "syndrome_valid": syndrome_valid,
        "type_i": type_i,
        "type_ii": type_ii,
        "exact_success": exact,
        "stabilizer_success": bool(syndrome_valid and not type_ii and not exact),
    }
    return record


def run_point(code_name: str, p: float, *, target_failures: int, max_shots: int,
              seed: int, output: Path, start_shot: int = 0,
              fixed_shots: int | None = None,
              campaign_sha256: str | None = None) -> None:
    source = json.loads((ROOT / "source_points.json").read_text())
    key = f"{p:.2f}"
    if key not in source["curves"][code_name]["p_to_qbp_rate"]:
        raise ValueError("requested p is not a plotted source point")
    specs = _decoder_specs()
    code = _load_code(code_name)
    graphs = _graphs(code, p)
    masks = _logical_masks(code)
    evaluator = _syndrome_evaluator(code)
    # The first call compiles every Numba signature before timed shots.
    zero = np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8)
    for name, graph in graphs.items():
        if name.startswith("bp4"):
            graph.run(zero, max_iterations=1)
        else:
            graph[0].run(zero[code.hx.shape[0]:], max_iterations=1)
            graph[1].run(zero[:code.hx.shape[0]], max_iterations=1)
    output.mkdir(parents=True, exist_ok=False)
    if start_shot < 0 or (start_shot and fixed_shots is None):
        raise ValueError("nonzero start_shot requires a fixed shard length")
    if fixed_shots is not None and fixed_shots < 1:
        raise ValueError("fixed_shots must be positive")
    requested = max_shots if fixed_shots is None else fixed_shots
    manifest = {
        "schema": "yao-vanilla-point-manifest-v1", "code": code_name,
        "code_semantic_sha256": semantic_sha256(code), "physical_p": p,
        "decoder_p0": p, "binary_marginal_q": 2*p/3,
        "source_qbp_rate": source["curves"][code_name]["p_to_qbp_rate"][key],
        "source_figure": source["curves"][code_name]["figure"],
        "seed": seed, "rng": "numpy.PCG64", "target_failures_each_arm": None if fixed_shots is not None else target_failures,
        "max_shots": requested, "start_shot": start_shot,
        "campaign_sha256": campaign_sha256,
        "stop_rule": "fixed_shard" if fixed_shots is not None else "all_arms_target_or_max_shots",
        "decoder_specs": specs,
        "profile_evidence": {
            "bp4_v1": graphs["bp4_v1"].profile.as_evidence(),
            "bp4_v2": graphs["bp4_v2"].profile.as_evidence(),
            "binary_v1": graphs["binary_v1"][0].graph.profile.as_evidence(),
            "binary_v2": graphs["binary_v2"][0].graph.profile.as_evidence(),
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    manifest_hash = sha256((output / "manifest.json").read_bytes()).hexdigest()
    counts = {name: {"type_i": 0, "type_ii": 0, "exact_success": 0,
                     "stabilizer_success": 0, "iteration_sum": 0, "elapsed_ns_sum": 0}
              for name in ARMS}
    ledger_digest = sha256()
    rng = np.random.Generator(np.random.PCG64(seed))
    if start_shot:
        # _sample consumes exactly n float64 draws from this PCG64 stream.
        rng.bit_generator.advance(start_shot * code.n)
    start = time.monotonic()
    with (output / "events.jsonl").open("x", encoding="utf-8") as handle:
        for offset in range(requested):
            shot = start_shot + offset
            truth = _sample(rng, code.n, p)
            syndrome = _original_syndrome(evaluator, truth)
            truth_signature = _logical_signature(truth, masks)
            arm_records = {
                name: _one_arm(name, graphs[name], syndrome, code, evaluator, truth,
                               truth_signature, masks, specs[name]["max_iterations"])
                for name in ARMS
            }
            event = {"schema": "yao-vanilla-shot-v1", "shot": shot,
                     "error_sha256": sha256(truth.tobytes()).hexdigest(),
                     "zero_syndrome": bool(not np.any(syndrome)), "arms": arm_records}
            encoded = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
            handle.write(encoded.decode())
            ledger_digest.update(encoded)
            for name, arm in arm_records.items():
                count = counts[name]
                for field in ("type_i", "type_ii", "exact_success", "stabilizer_success"):
                    count[field] += int(arm[field])
                count["iteration_sum"] += sum(arm["iterations"])
                count["elapsed_ns_sum"] += arm["elapsed_ns"]
            n = offset + 1
            if n % 10000 == 0:
                print(code_name, key, n, {arm: counts[arm]["type_i"] + counts[arm]["type_ii"] for arm in ARMS}, flush=True)
                handle.flush()
            if fixed_shots is None and n >= 100 and all(
                counts[name]["type_i"] + counts[name]["type_ii"] >= target_failures for name in ARMS
            ):
                reason = "all_arms_reached_target_failures"
                break
        else:
            n = requested
            reason = "fixed_shard_complete" if fixed_shots is not None else "max_shots"
    summary = {
        "schema": "yao-vanilla-point-summary-v1", "manifest_sha256": manifest_hash,
        "events_sha256": ledger_digest.hexdigest(), "shots": n,
        "start_shot": start_shot, "end_shot_exclusive": start_shot + n,
        "stop_reason": reason, "wall_seconds": time.monotonic() - start,
        "code": code_name, "physical_p": p,
        "source_qbp_rate": manifest["source_qbp_rate"], "counts": counts,
    }
    (output / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"code": code_name, "p": p, "shots": n, "stop_reason": reason,
                      "counts": {name: counts[name]["type_i"] + counts[name]["type_ii"] for name in ARMS}}, sort_keys=True), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=("a5", "b2"), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--target-failures", type=int, default=100)
    parser.add_argument("--max-shots", type=int, default=1_000_000)
    parser.add_argument("--shots", type=int, help="fixed shard size; disables adaptive failure stopping")
    parser.add_argument("--start-shot", type=int, default=0)
    parser.add_argument("--seed", type=int, default=231210950)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (not math.isfinite(args.p) or args.target_failures < 1
            or args.max_shots < 100 or args.seed < 0
            or args.start_shot < 0 or (args.shots is not None and args.shots < 1)):
        parser.error("invalid p, stopping, or seed")
    run_point(args.code, args.p, target_failures=args.target_failures,
              max_shots=args.max_shots, seed=args.seed, output=args.output,
              start_shot=args.start_shot, fixed_shots=args.shots)


if __name__ == "__main__":
    main()
