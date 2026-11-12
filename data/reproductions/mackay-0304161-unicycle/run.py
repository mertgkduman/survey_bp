"""Frozen MacKay Construction U BP campaign with resumable audited ledgers."""

from __future__ import annotations

import argparse
from dataclasses import replace
import fcntl
from hashlib import sha256
import importlib.util
import json
import platform
from pathlib import Path
import sys
import time

import numba
import numpy as np
import scipy

from bp_registry.artifacts import load_artifact
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PLAN = ROOT / "plan.json"
RESULTS = ROOT / "results"
SEED = 2026111203
TOTAL_ITERATIONS = 88200
HELPER = ROOT.with_name("yao-2312-10950-bpgd-completion") / "run.py"
helper_spec = importlib.util.spec_from_file_location("_unicycle_ledger_helpers", HELPER)
base = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(base)
sha, write_json = base.sha, base.write_json


def code_plan() -> dict:
    files = [Path(__file__), ROOT / "source.json", ROOT / "codes.json", HELPER,
             base.SOURCE_ROOT / "run_point.py", base.SOURCE_ROOT / "codes.json",
             base.SOURCE_ROOT / "source_points.json"]
    files.extend(REPO / "src/bp_registry" / name for name in (
        "unicycle.py", "css.py", "artifacts.py", "code_constructions.py", "check_numerics.py",
        "compiled_contracts.py", "profile_contracts.py", "resolution.py", "canonical/compiled.py", "canonical/numerics.py",
        "canonical/kernel.py", "canonical/schedules.py", "canonical/update_context.py",
        "quaternary/algebra.py", "quaternary/kernel.py", "quaternary/problems.py",
        "quaternary/compiled.py", "quaternary/numerics.py"))
    receipts = json.loads((ROOT / "codes.json").read_text())
    files.extend(ROOT / row["artifact"] for row in receipts.values())
    common = {"check_rule": "sum_product", "schedule": "flooding", "message_resolution": "float64",
              "prior": "p", "check_cap": None, "product_epsilon": 1e-10,
              "max_iterations": TOTAL_ITERATIONS}
    return {
        "schema": "mackay-unicycle-plan-v1", "paper": "https://arxiv.org/abs/quant-ph/0304161v3",
        "evidence_status": "source_informed_canonical_adaptation", "seed": SEED,
        "implementation_sha256": {str(p.relative_to(REPO)): sha(p) for p in files},
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scipy": scipy.__version__, "numba": numba.__version__},
        "sampler": "PCG64 SeedSequence(seed, physical_p * 100000, shot); shared X-only stream across binary arms",
        "stop": {"target_block_failures": 20, "max_shots": 100_000_000,
                 "failure_events": ["type_i", "type_ii"]},
        "codes": receipts,
        "arms": {
            "binary_sp": {**common, "family": "binary_css", "noise_model": "x_only", "v2c_damping": 0.0,
                          "numerical_profile": "binary-spa-flooding-f64-v2", "branch_count": 1,
                          "iterations_per_branch": TOTAL_ITERATIONS, "mechanism": "ordinary_binary_bp"},
            "unicycle_sp": {**common, "family": "binary_css", "noise_model": "x_only", "v2c_damping": 0.0,
                            "numerical_profile": "binary-spa-flooding-f64-v2", "branch_count": 2,
                            "iterations_per_branch": TOTAL_ITERATIONS // 2,
                            "controller": {"kind": "unicycle_extra_bit_hypotheses", "branch_count": 2,
                                           "iterations_per_branch": TOTAL_ITERATIONS // 2,
                                           "selection": "valid_maximum_likelihood", "tie_break": "extra_bit_zero"},
                            "mechanism": "condition_extra_bit_on_zero_and_one_then_select_valid_maximum_likelihood",
                            "tie_break": "extra_bit_zero"},
            "qbp": {**common, "family": "bp4", "noise_model": "depolarizing", "v2c_damping": 0.1,
                    "numerical_profile": "quaternary-bp4-f64-v2", "branch_count": 1,
                    "iterations_per_branch": TOTAL_ITERATIONS, "mechanism": "joint_pauli_bp"},
        },
        "matched_rates": [{"x_only": p / 100, "depolarizing": 3 * p / 200} for p in range(4, 11)],
        "claim_limit": "Controlled X-only and matched-marginal depolarizing experiment; no source-curve agreement claim. "
                       "Source independent-X/Z and classical block-error plots have different semantics. "
                       "Equal total iteration ceilings do not equalize directed-edge work. "
                       "The source does not specify this iteration ceiling or floating-point conventions.",
    }


def load_plan() -> dict:
    plan = json.loads(PLAN.read_text())
    if plan != code_plan():
        raise ValueError("frozen plan, software or implementation has changed")
    return plan


def jobs(plan: dict) -> list[dict]:
    result = []
    for code_id, receipt in sorted(plan["codes"].items()):
        for arm, decoder in sorted(plan["arms"].items()):
            for rates in plan["matched_rates"]:
                p = rates[decoder["noise_model"]]
                result.append({"code": code_id, "arm": arm, "decoder": decoder,
                               "physical_p": p, "matched_x_rate": rates["x_only"],
                               "code_semantic_sha256": receipt["semantic_sha256"],
                               "code_artifact": receipt["artifact"], "seed": plan["seed"],
                               "workers": 1, **plan["stop"],
                               "id": f"{code_id}-{arm}-p{round(p * 1000):03d}",
                               "graph_edges": receipt["edges_per_component"] * (2 if arm == "qbp" else 1)
                                              - (receipt["n"] - 1 if arm == "unicycle_sp" else 0)})
    return result


def decoder_state(job: dict) -> tuple:
    code = load_artifact(ROOT, job["code_artifact"],
                         expected_semantic_sha256=job["code_semantic_sha256"]).code
    if job["arm"] == "qbp":
        graph = replace(CompiledBp4Graph.from_css(code, job["physical_p"]),
                        profile=replace(QBP4_F64_V2, v2c_damping=.1, check_cap=None))
    else:
        check = code.hz[:, :-1] if job["arm"] == "unicycle_sp" else code.hz
        graph = CompiledBinaryFlooding.from_check_matrix(
            check, profile=replace(BINARY_SPA_F64_V2, v2c_damping=0.0, check_cap=None))
    packed = tuple(np.packbits(matrix, axis=1, bitorder="little")
                   for matrix in (code.hx, code.hz, code.lx, code.lz))
    return job, code.n, packed, graph


def split_decode(graph, syndrome: np.ndarray, *, p: float, limit: int) -> tuple[np.ndarray, bool, list[int]]:
    """Condition only on observed syndrome and decoder prior, never truth."""
    candidates = []
    iterations = []
    for extra in (0, 1):
        decoded = graph.run(syndrome ^ extra, error_rate=p, max_iterations=limit)
        candidate = np.append(decoded.candidate, np.uint8(extra)).astype(np.uint8)
        # Negative log probability includes the extra bit, too.
        weight = int(candidate.sum())
        score = -weight * np.log(p) - (len(candidate) - weight) * np.log1p(-p)
        candidates.append((not decoded.converged, float(score), extra, candidate))
        iterations.append(decoded.iterations)
    selected = min(candidates, key=lambda row: row[:3])
    return selected[3], not selected[0], iterations


def outcome(hx, hz, lx, lz, truth: np.ndarray, candidate: np.ndarray, *, joint: bool) -> tuple[str, np.ndarray]:
    """Evaluate both logical signatures separately, with no uint64 limit."""
    syndrome = base._syndrome
    if joint:
        actual, guessed = base.PAULI_BITS[truth], base.PAULI_BITS[candidate]
        target = np.concatenate((syndrome(hx, actual[:, 1]), syndrome(hz, actual[:, 0])))
        observed = np.concatenate((syndrome(hx, guessed[:, 1]), syndrome(hz, guessed[:, 0])))
        logical = (np.any(syndrome(lz, actual[:, 0] ^ guessed[:, 0]))
                   or np.any(syndrome(lx, actual[:, 1] ^ guessed[:, 1])))
    else:
        target, observed = syndrome(hz, truth), syndrome(hz, candidate)
        logical = np.any(syndrome(lz, truth ^ candidate))
    label = ("type_i" if not np.array_equal(target, observed) else "type_ii" if logical else
             "exact_success" if np.array_equal(truth, candidate) else "stabilizer_success")
    return label, target


def event(state: tuple, shot: int) -> dict:
    job, n, packed, graph = state
    joint = job["arm"] == "qbp"
    p = job["physical_p"]
    truth = base._sample(job["seed"], round(p * 100000), shot, n, depolarizing=joint)
    hx, hz, lx, lz = packed
    bits = base.PAULI_BITS[truth] if joint else truth
    syndrome = (np.concatenate((base._syndrome(hx, bits[:, 1]), base._syndrome(hz, bits[:, 0])))
                if joint else base._syndrome(hz, truth))
    started = time.perf_counter_ns()
    if job["arm"] == "unicycle_sp":
        candidate, converged, branches = split_decode(graph, syndrome, p=p,
                                                      limit=job["decoder"]["iterations_per_branch"])
    else:
        kwargs = {} if joint else {"error_rate": p}
        decoded = graph.run(syndrome, max_iterations=job["decoder"]["iterations_per_branch"], **kwargs)
        candidate, converged, branches = decoded.candidate, decoded.converged, [decoded.iterations]
    elapsed = time.perf_counter_ns() - started
    label, _ = outcome(*packed, truth, candidate, joint=joint)
    if converged != (label != "type_i"):
        raise ValueError(f"independent syndrome evaluation disagrees at shot {shot}")
    iterations = sum(branches)
    return {"shot": shot, "outcome": label, "iterations": iterations,
            "branch_iterations": branches, "directed_edge_updates": 2 * job["graph_edges"] * iterations,
            "decode_ns": elapsed, "error_sha256": sha256(truth.tobytes()).hexdigest(),
            "syndrome_sha256": sha256(syndrome.tobytes()).hexdigest(),
            "candidate_sha256": sha256(candidate.tobytes()).hexdigest()}


class Ledger(base.Ledger):
    def add(self, row: dict, line: bytes) -> None:
        settings = self.job["decoder"]
        branches = row["branch_iterations"]
        if (len(branches) != settings["branch_count"]
                or any(type(value) is not int or not 0 <= value <= settings["iterations_per_branch"] for value in branches)
                or sum(branches) != row["iterations"]
                or row["directed_edge_updates"] != 2 * self.job["graph_edges"] * row["iterations"]):
            raise ValueError("invalid branch work counters")
        super().add(row, line)

    def summary(self) -> dict:
        return {**super().summary(), "directed_edge_updates": 2 * self.job["graph_edges"] * self.iterations}


def manifest_for(job: dict) -> dict:
    return {"schema": "mackay-unicycle-run-v1", "plan_sha256": sha(PLAN), "job": job}


def run(job: dict, results: Path) -> dict:
    directory = results / job["id"]
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest = directory / "manifest.json"
        expected = manifest_for(job)
        if not manifest.exists():
            write_json(manifest, expected)
        elif json.loads(manifest.read_text()) != expected:
            raise ValueError(f"checkpoint manifest mismatch: {directory}")
        ledger = Ledger(directory, job)
        if not ledger.complete:
            state = decoder_state(job)
            while not ledger.complete:
                rows = []
                failures = ledger.failures
                # Commit small durable chunks, including progress on rare points.
                for shot in range(ledger.shots, min(ledger.shots + 128, job["max_shots"])):
                    row = event(state, shot)
                    rows.append(row)
                    failures += row["outcome"] in base.FAILURES
                    if failures == job["target_block_failures"]:
                        break
                ledger.commit(rows)
                print(job["id"], ledger.shots, ledger.failures, flush=True)
        summary = {**ledger.summary(), "manifest_sha256": sha(manifest)}
        path = directory / "summary.json"
        if path.exists() and json.loads(path.read_text()) != summary:
            raise ValueError(f"terminal summary mismatch: {directory}")
        write_json(path, summary)
        return summary


def collect(plan: dict, results: Path) -> dict:
    verified = []
    for job in jobs(plan):
        directory = results / job["id"]
        summary_path = directory / "summary.json"
        if not summary_path.exists():
            continue
        manifest = directory / "manifest.json"
        ledger = Ledger(directory, job)
        summary = json.loads(summary_path.read_text())
        if (json.loads(manifest.read_text()) != manifest_for(job)
                or summary != {**ledger.summary(), "manifest_sha256": sha(manifest)}):
            raise ValueError(f"terminal evidence mismatch: {directory}")
        state = decoder_state(job)
        for stored in (ledger.first, ledger.last):
            replay = event(state, stored["shot"])
            if {k: v for k, v in replay.items() if k != "decode_ns"} != {k: v for k, v in stored.items() if k != "decode_ns"}:
                raise ValueError(f"shot replay mismatch: {directory}, {stored['shot']}")
        verified.append({"id": job["id"], "code": job["code"], "arm": job["arm"],
                         "physical_p": job["physical_p"], "matched_x_rate": job["matched_x_rate"],
                         "summary_sha256": sha(summary_path), **summary})
    payload = {"schema": "mackay-unicycle-verification-v1", "plan_sha256": sha(PLAN),
               "planned_points": len(jobs(plan)), "points": verified}
    write_json(results / "verified.json", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--freeze", action="store_true")
    actions.add_argument("--index", type=int)
    actions.add_argument("--collect", action="store_true")
    actions.add_argument("--list", action="store_true")
    parser.add_argument("--results", type=Path, default=RESULTS)
    args = parser.parse_args()
    if args.freeze:
        frozen = code_plan()
        with PLAN.open("x") as handle:
            json.dump(frozen, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return
    plan = load_plan()
    if args.list:
        for index, job in enumerate(jobs(plan)):
            print(index, job["id"])
    elif args.collect:
        args.results.mkdir(exist_ok=True, parents=True)
        payload = collect(plan, args.results)
        print(f"{len(payload['points'])}/{payload['planned_points']} terminal points verified")
    elif not 0 <= args.index < len(jobs(plan)):
        parser.error("point index is outside the frozen grid")
    else:
        print(json.dumps(run(jobs(plan)[args.index], args.results)), flush=True)


if __name__ == "__main__":
    main()
