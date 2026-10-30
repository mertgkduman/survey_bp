"""One bounded, source-linked Yao non-OSD curve point with a shot ledger.

The compiled kernels are development interpretations. This script never
receives hidden truth inside a decoder and never treats a source point as an
expected bit-for-bit result.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
import math
from pathlib import Path
import time

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import REFERENCE_CPU_F64
from bp_registry.code_constructions import build_b1_ghp, build_b2_ghp, build_c2_hp
from bp_registry.css import semantic_sha256
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2
from bp_registry.quaternary.problems import build_qbpgd_a5_css_artifact

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PAULI_BITS = np.asarray(((0, 0), (1, 0), (1, 1), (0, 1)), dtype=np.uint8)
SOURCE = json.loads((ROOT / "source_points.json").read_text())
RECEIPTS = json.loads((ROOT / "codes.json").read_text())
BINARY_METHODS = {
    "bp": (100, None, "most_reliable"),
    "bpgd_t1": (1, None, "most_reliable"),
    "bpgd_t10": (10, None, "most_reliable"),
    "bpgd_t70": (70, None, "most_reliable"),
    "bpgd_t100": (100, None, "most_reliable"),
    "bpgd_random_t100": (100, None, "uniform_random"),
    "bpgd_t100_r2": (100, 2, "most_reliable"),
    "bpgd_t100_r5": (100, 5, "most_reliable"),
    "bpgd_t100_r10": (100, 10, "most_reliable"),
    "bpgd_t100_r50": (100, 50, "most_reliable"),
    "bpgd_t100_r882": (100, 882, "most_reliable"),
}
QUATERNARY_METHODS = {"bpgd_t10", "bpgd_t10_tuned"}


def _code(name: str):
    builders = {
        "b1": build_b1_ghp,
        "c2": build_c2_hp,
        "a5": lambda: build_qbpgd_a5_css_artifact()[0],
        "b2": build_b2_ghp,
    }
    code = builders[name]()
    if semantic_sha256(code) != RECEIPTS["codes"][name]["semantic_sha256"]:
        raise ValueError("source code construction differs from its pinned receipt")
    return code


def _point_targets(code_name: str, p: float, method: str) -> list[dict]:
    key = f"{p:.5f}"
    targets = []
    source_key = "bpgd_t100_r882" if method == "bpgd_t100" else method
    for figure, body in SOURCE["figures"].items():
        if body["code"] != code_name:
            continue
        for curve in dict.fromkeys((method, source_key)):
            if key in body["curves"].get(curve, {}):
                targets.append({"figure": int(figure), "curve": curve,
                                "physical_p": p, "published_rate": body["curves"][curve][key]})
    return targets


def _binary_masks(code) -> np.ndarray:
    if code.lz is None or code.k > 63:
        raise ValueError("binary outcomes need a complete <=63-logical CSS basis")
    weights = np.left_shift(np.uint64(1), np.arange(code.k, dtype=np.uint64))
    return (code.lz.astype(np.uint64) * weights[:, None]).sum(axis=0, dtype=np.uint64)


def _signature(bits: np.ndarray, masks: np.ndarray) -> int:
    return int(np.bitwise_xor.reduce(masks[bits != 0])) if np.any(bits) else 0


def _syndrome(packed_checks: np.ndarray, bits: np.ndarray) -> np.ndarray:
    packed = np.packbits(bits, bitorder="little")
    return (np.bitwise_count(np.bitwise_and(packed_checks, packed)).sum(axis=1) & 1).astype(np.uint8)


def _pauli_signature(paulis: np.ndarray, masks_x: np.ndarray, masks_z: np.ndarray) -> int:
    bits = PAULI_BITS[paulis]
    return _signature(bits[:, 0], masks_x) ^ _signature(bits[:, 1], masks_z)


def _sample(seed: int, p_index: int, shot: int, n: int, *, depolarizing: bool) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence((seed, p_index, shot))))
    draw = rng.random(n)
    if not depolarizing:
        return (draw < p_index / 100000.0).astype(np.uint8)
    p = p_index / 100000.0
    return np.where(draw < 1-p, 0, np.where(draw < 1-2*p/3, 1,
                    np.where(draw < 1-p/3, 2, 3))).astype(np.uint8)


def _outcome(candidate: np.ndarray, truth: np.ndarray, syndrome: np.ndarray,
             packed_hx: np.ndarray, packed_hz: np.ndarray, code,
             masks_x: np.ndarray, masks_z: np.ndarray | None) -> dict[str, bool]:
    if masks_z is None:
        valid = bool(np.array_equal(_syndrome(packed_hz, candidate), syndrome))
        logical = valid and _signature(candidate, masks_x) != _signature(truth, masks_x)
    else:
        candidate_bits = PAULI_BITS[candidate]
        candidate_syndrome = np.concatenate((_syndrome(packed_hx, candidate_bits[:, 1]),
                                              _syndrome(packed_hz, candidate_bits[:, 0])))
        valid = bool(np.array_equal(candidate_syndrome, syndrome))
        logical = valid and _pauli_signature(candidate, masks_x, masks_z) != _pauli_signature(truth, masks_x, masks_z)
    exact = valid and not logical and bool(np.array_equal(candidate, truth))
    return {"type_i": not valid, "type_ii": bool(logical), "exact_success": bool(exact),
            "stabilizer_success": bool(valid and not logical and not exact)}


def _quaternary_graph(code, method: str, p: float) -> tuple[CompiledBp4Graph, dict]:
    if method == "bpgd_t10":
        selected = {"p0": p, "damping": 0.0, "check_cap": None, "product_epsilon": 1e-10,
                    "profile_id": "yao-source-qbpgd-undamped-v2"}
    else:
        path = REPO / "data/reproductions/yao-2312-10950-bp4-tuning-p006/decoders" / f"{'a5' if code.n == 180 else 'b2'}_tuned.json"
        payload = json.loads(path.read_text())
        candidate = payload["candidates"][0]
        selected = {**candidate, "profile_id": "yao-controlled-qbpgd-selected-bp4-v2",
                    "selected_file": str(path.relative_to(REPO)),
                    "selected_file_sha256": sha256(path.read_bytes()).hexdigest()}
    graph = CompiledBp4Graph.from_css(code, float(selected["p0"]))
    profile = replace(QBP4_F64_V2, profile_id=selected["profile_id"],
                      v2c_damping=float(selected["damping"]), check_cap=selected["check_cap"],
                      product_epsilon=float(selected["product_epsilon"]))
    return replace(graph, profile=profile), selected


def run(*, code_name: str, method: str, p: float, seed: int, start_shot: int,
        max_shots: int, target_failures: int | None, output: Path) -> dict:
    if code_name not in RECEIPTS["codes"] or not math.isfinite(p) or not 0 < p < 1:
        raise ValueError("invalid code or physical probability")
    if (type(seed) is not int or seed < 0 or type(start_shot) is not int or start_shot < 0
            or type(max_shots) is not int or max_shots < 1
            or target_failures is not None and (type(target_failures) is not int or target_failures < 1)):
        raise ValueError("invalid shot request")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {output}")
    depolarizing = code_name in {"a5", "b2"}
    if method not in (QUATERNARY_METHODS if depolarizing else BINARY_METHODS):
        raise ValueError("unsupported method/code combination")
    p_index = round(p * 100000)
    if abs(p_index / 100000 - p) > 1e-12:
        raise ValueError("physical p must have at most five decimal places")
    code = _code(code_name)
    packed_hx = np.packbits(code.hx, axis=1, bitorder="little")
    packed_hz = np.packbits(code.hz, axis=1, bitorder="little")
    if depolarizing:
        graph, decoder = _quaternary_graph(code, method, p)
        weights = np.left_shift(np.uint64(1), np.arange(code.k, dtype=np.uint64))
        masks_x = (code.lz.astype(np.uint64) * weights[:, None]).sum(axis=0, dtype=np.uint64)
        masks_z = (code.lx.astype(np.uint64) * weights[:, None]).sum(axis=0, dtype=np.uint64)
        graph.run_qbpgd(np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8),
                        iterations_per_round=1, round_limit=1)
    else:
        graph = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=REFERENCE_CPU_F64)
        decoder = {"profile": "yao-binary-spa-v2c-cap25", "prior_p0": p, "damping": 0.0,
                   "check_product_epsilon": 1e-10, "v2c_cap": 25.0,
                   "ordinary_bp_max_iterations": 100,
                   "bpgd_iterations_per_round": BINARY_METHODS[method][0],
                   "bpgd_round_limit": BINARY_METHODS[method][1] or code.n,
                   "decimation_order": BINARY_METHODS[method][2]}
        masks_x, masks_z = _binary_masks(code), None
        graph.run_paper_bp(np.zeros(code.hz.shape[0], dtype=np.uint8), error_rate=p, max_iterations=1)
    source_targets = _point_targets(code_name, p, method)
    if not source_targets and not method.endswith("_tuned"):
        raise ValueError("method and physical p have no source point")
    source_files = [Path(__file__), REPO / "src/bp_registry/code_constructions.py",
                    REPO / "src/bp_registry/canonical/compiled.py",
                    REPO / "src/bp_registry/quaternary/compiled.py",
                    ROOT / "source_points.json", ROOT / "codes.json"]
    manifest = {
        "schema": "yao-non-osd-run-v1", "code": code_name, "method": method, "noise": "depolarizing" if depolarizing else "bit_flip",
        "physical_p": p, "seed": seed, "start_shot": start_shot, "max_shots": max_shots,
        "target_failures": target_failures, "stop_rule": "target_failures_or_max_shots" if target_failures else "fixed_shots",
        "sampler": "PCG64 SeedSequence(seed,p*100000,global_shot); separate random-order stream",
        "code_semantic_sha256": semantic_sha256(code), "decoder": decoder,
        "source_targets": source_targets, "source_archive_sha256": SOURCE["archive_sha256"],
        "source_files_sha256": {str(path.relative_to(REPO)): sha256(path.read_bytes()).hexdigest() for path in source_files},
        "fidelity": "canonical_adaptation_compiled_development",
        "outcome": "independent original-code Type I + Type II block failure; stabilizer-equivalent success",
    }
    output.mkdir(parents=True)
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    counts = {key: 0 for key in ("type_i", "type_ii", "exact_success", "stabilizer_success",
                                 "iterations", "rounds", "fixations", "elapsed_ns")}
    digest = sha256()
    started = time.monotonic()
    with (output / "events.jsonl").open("x", buffering=1) as ledger:
        for offset in range(max_shots):
            shot = start_shot + offset
            truth = _sample(seed, p_index, shot, code.n, depolarizing=depolarizing)
            if depolarizing:
                truth_bits = PAULI_BITS[truth]
                syndrome = np.concatenate((_syndrome(packed_hx, truth_bits[:, 1]),
                                           _syndrome(packed_hz, truth_bits[:, 0])))
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
            event = {"schema": "yao-non-osd-shot-v1", "shot": shot,
                     "error_sha256": sha256(truth.tobytes()).hexdigest(),
                     "syndrome_sha256": sha256(syndrome.tobytes()).hexdigest(),
                     "outcome": record}
            row = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            ledger.write(row)
            digest.update(row.encode())
            for key in counts:
                counts[key] += int(record[key])
            n = offset + 1
            failures = counts["type_i"] + counts["type_ii"]
            if n % 100 == 0:
                ledger.flush()
                print(code_name, method, p, n, failures, flush=True)
            if target_failures is not None and failures >= target_failures:
                reason = "target_failures"
                break
        else:
            reason = "fixed_shots" if target_failures is None else "max_shots"
    summary = {"schema": "yao-non-osd-summary-v1", "code": code_name, "method": method,
               "physical_p": p, "seed": seed, "start_shot": start_shot,
               "shots": n, "failures": failures, "stop_reason": reason,
               "counts": counts, "source_targets": source_targets,
               "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
               "events_sha256": digest.hexdigest(), "wall_seconds": time.monotonic() - started}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=tuple(RECEIPTS["codes"]), required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--start-shot", type=int, default=0)
    parser.add_argument("--max-shots", type=int, required=True)
    parser.add_argument("--target-failures", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(code_name=args.code, method=args.method, p=args.p, seed=args.seed,
                 start_shot=args.start_shot, max_shots=args.max_shots,
                 target_failures=args.target_failures, output=args.output)
    print(json.dumps({key: result[key] for key in ("code", "method", "physical_p", "shots", "failures", "stop_reason")}, sort_keys=True))
