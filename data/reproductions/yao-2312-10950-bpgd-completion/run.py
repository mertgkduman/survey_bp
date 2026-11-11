"""Run and verify the B1/C2 direct BPGD and matched-marginal Q-BP campaign."""

from __future__ import annotations

import argparse
from collections import Counter, deque
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
import fcntl
import gzip
from hashlib import sha256
from itertools import islice
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
from scipy.stats import beta

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import REFERENCE_CPU_F64
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE_ROOT = ROOT.with_name("yao-2312-10950-non-osd")
sys.path.insert(0, str(SOURCE_ROOT))
from run_point import PAULI_BITS, RECEIPTS, SOURCE, _binary_masks, _code, _sample, _signature, _syndrome

PLAN = ROOT / "plan.json"
RESULTS = ROOT / "results"
OUTCOMES = ("type_i", "type_ii", "exact_success", "stabilizer_success")
FAILURES = frozenset(OUTCOMES[:2])
CHUNK_SIZE = 4096
SEED = 2026111077


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def code_plan() -> dict:
    source_files = [Path(__file__), SOURCE_ROOT / "run_point.py",
                    SOURCE_ROOT / "source_points.json", SOURCE_ROOT / "codes.json"]
    source_files.extend(REPO / "src/bp_registry" / file for file in (
        "code_constructions.py", "canonical/compiled.py", "canonical/numerics.py",
        "quaternary/compiled.py", "quaternary/numerics.py"))
    return {
        "schema": "yao-bpgd-completion-plan-v1",
        "paper": "https://arxiv.org/html/2312.10950v2",
        "implementation_sha256": {str(p.relative_to(REPO)): sha(p) for p in source_files},
        "seed": SEED,
        "sampler": "PCG64 SeedSequence(seed, physical_p * 100000, shot); shared across BPGD arms at each rate",
        "stop": {"target_block_failures": 20, "max_shots": 100_000_000,
                 "failure_events": list(OUTCOMES[:2])},
        "codes": {name: RECEIPTS["codes"][name]["semantic_sha256"] for name in ("b1", "c2")},
        "arms": {
            **{f"b1:bpgd_t{t}_r{r}": binary(t, r, figures)
               for t, r, figures in [(100, r, [6]) for r in (2, 5, 10, 50)]
               + [(t, 882, [3]) for t in (1, 10, 70)] + [(100, 882, [3, 6])]},
            "c2:bpgd_t10_r1922": binary(10, 1922, [5]),
            **{f"{name}:qbp": qbp(limit) for name, limit in (("b1", 88200), ("c2", 19220))},
        },
        "matched_rates": [{"x_only": p / 100, "depolarizing": 3 * p / 200} for p in range(4, 11)],
    }


def binary(t: int, r: int, figures: list[int]) -> dict:
    return {
        "family": "bpgd", "check_rule": "sum_product", "message_resolution": "float64",
        "numerical_profile": "yao-binary-spa-v2c-cap25", "noise_model": "x_only",
        "damping_old": 0.0, "binary_paper_v2c_cap": 25.0, "product_epsilon": 1e-10,
        "prior": "p", "max_iterations": t * r, "source_figures": figures,
        "controller": {"iterations_per_round": t, "round_limit": r, "order": "most_reliable"},
    }


def qbp(limit: int) -> dict:
    return {
        "family": "bp4", "check_rule": "sum_product", "message_resolution": "float64",
        "numerical_profile": "quaternary-bp4-f64-v2", "noise_model": "depolarizing",
        "v2c_damping": 0.1, "check_cap": None, "product_epsilon": 1e-10,
        "prior": "p", "max_iterations": limit, "source_figures": [],
    }


def jobs(plan: dict) -> list[dict]:
    points = []
    for key, settings in sorted(plan["arms"].items()):
        code, arm = key.split(":")
        channel = settings["noise_model"]
        for pair in plan["matched_rates"]:
            p = pair[channel]
            worker_count = 1
            if settings["family"] == "bpgd" and pair["x_only"] <= 0.05:
                worker_count = 16 if p == 0.04 and settings["controller"]["round_limit"] == 882 else 4
            points.append({
                "code": code, "arm": arm, "decoder": settings, "physical_p": p,
                "matched_x_rate": pair["x_only"], "seed": plan["seed"], "workers": worker_count,
                "code_semantic_sha256": plan["codes"][code], **plan["stop"],
                "id": f"{code}-{arm}-p{round(p * 1000):03d}",
            })
    return points


def load_plan() -> dict:
    plan = json.loads(PLAN.read_text())
    if plan != code_plan():
        raise ValueError("frozen plan or implementation has changed")
    return plan


def decoder_state(job: dict) -> tuple:
    code = _code(job["code"])
    settings = job["decoder"]
    p = job["physical_p"]
    hx = np.packbits(code.hx, axis=1, bitorder="little")
    hz = np.packbits(code.hz, axis=1, bitorder="little")
    masks_x = _binary_masks(code)
    if settings["family"] == "bp4":
        graph = CompiledBp4Graph.from_css(code, p)
        profile = replace(QBP4_F64_V2, v2c_damping=settings["v2c_damping"],
                          check_cap=settings["check_cap"], product_epsilon=settings["product_epsilon"])
        weights = np.left_shift(np.uint64(1), np.arange(code.k, dtype=np.uint64))
        masks_z = (code.lx.astype(np.uint64) * weights[:, None]).sum(axis=0, dtype=np.uint64)
        return job, code.n, hx, hz, masks_x, masks_z, replace(graph, profile=profile)
    graph = CompiledBinaryFlooding.from_check_matrix(code.hz, profile=REFERENCE_CPU_F64)
    return job, code.n, hx, hz, masks_x, None, graph


def event(state: tuple, shot: int) -> dict:
    job, n, hx, hz, masks_x, masks_z, graph = state
    settings = job["decoder"]
    p = job["physical_p"]
    joint = masks_z is not None
    truth = _sample(job["seed"], round(p * 100000), shot, n, depolarizing=joint)
    truth_bits = PAULI_BITS[truth] if joint else truth
    syndrome = (np.concatenate((_syndrome(hx, truth_bits[:, 1]), _syndrome(hz, truth_bits[:, 0])))
                if joint else _syndrome(hz, truth))
    start = time.perf_counter_ns()
    if joint:
        decoded = graph.run(syndrome, max_iterations=settings["max_iterations"])
    else:
        controller = settings["controller"]
        decoded = graph.run_paper_bpgd(syndrome, error_rate=p,
                                       sweeps_per_round=controller["iterations_per_round"],
                                       round_limit=controller["round_limit"], order=controller["order"])
    elapsed = time.perf_counter_ns() - start
    candidate = decoded.candidate
    if joint:
        candidate_bits = PAULI_BITS[candidate]
        candidate_syndrome = np.concatenate((_syndrome(hx, candidate_bits[:, 1]),
                                             _syndrome(hz, candidate_bits[:, 0])))
        # Compare two signatures independently. XOR between them would miss
        # errors whose X and Z signatures are equal and nonzero.
        logical = (_signature(candidate_bits[:, 0] ^ truth_bits[:, 0], masks_x) != 0
                   or _signature(candidate_bits[:, 1] ^ truth_bits[:, 1], masks_z) != 0)
    else:
        candidate_syndrome = _syndrome(hz, candidate)
        logical = _signature(candidate ^ truth, masks_x) != 0
    valid = np.array_equal(candidate_syndrome, syndrome)
    if valid != decoded.converged:
        raise ValueError(f"syndrome evaluation disagrees at shot {shot}")
    outcome = ("type_i" if not valid else "type_ii" if logical else
               "exact_success" if np.array_equal(candidate, truth) else "stabilizer_success")
    return {"shot": shot, "outcome": outcome, "iterations": decoded.iterations,
            "rounds": getattr(decoded, "rounds", 0), "fixations": getattr(decoded, "fixations", 0),
            "decode_ns": elapsed, "error_sha256": sha256(truth.tobytes()).hexdigest(),
            "syndrome_sha256": sha256(syndrome.tobytes()).hexdigest(),
            "candidate_sha256": sha256(candidate.tobytes()).hexdigest()}


def batches(job: dict, start: int):
    """Keep worker batches in shot order with at most one batch per worker queued."""
    workers = job["workers"]
    starts = iter(range(start, job["max_shots"], CHUNK_SIZE))
    state = decoder_state(job)
    if workers == 1:
        for offset in starts:
            yield batch(state, offset)
        return
    # Warm the already existing JIT kernel before starting independent workers.
    graph = state[-1]
    graph.run_paper_bpgd(np.zeros(state[3].shape[0], dtype=np.uint8),
                         error_rate=job["physical_p"], sweeps_per_round=1, round_limit=1)
    with ProcessPoolExecutor(max_workers=workers, initializer=set_worker, initargs=(state,)) as pool:
        pending = deque(pool.submit(worker_batch, offset) for offset in islice(starts, workers))
        while pending:
            yield pending.popleft().result()
            offset = next(starts, None)
            if offset is not None:
                pending.append(pool.submit(worker_batch, offset))
        # Executor shutdown also waits for already running batches when the
        # caller reaches the terminal prefix. Those rows are never retained.


def set_worker(state: tuple) -> None:
    global WORKER_STATE
    WORKER_STATE = state


def worker_batch(offset: int) -> list[dict]:
    return batch(WORKER_STATE, offset)


def batch(state: tuple, offset: int) -> list[dict]:
    job = state[0]
    failures = 0
    events = []
    for shot in range(offset, min(offset + CHUNK_SIZE, job["max_shots"])):
        row = event(state, shot)
        events.append(row)
        failures += row["outcome"] in FAILURES
        if failures == job["target_block_failures"]:
            break
    return events


class Ledger:
    """Audit checkpoint chunks and maintain the contiguous terminal prefix."""

    def __init__(self, directory: Path, job: dict):
        self.directory = directory
        self.job = job
        self.shots = 0
        self.counts = Counter({key: 0 for key in OUTCOMES})
        self.iterations = self.decode_ns = 0
        self.digest = sha256()
        self.first = self.last = None
        for path in sorted(directory.glob("shots-*.jsonl.gz")):
            if path.name != self.path().name:
                raise ValueError(f"unexpected chunk boundary: {path}")
            with gzip.open(path, "rb") as stream:
                for line in stream:
                    self.add(json.loads(line), line)

    @property
    def failures(self) -> int:
        return self.counts["type_i"] + self.counts["type_ii"]

    @property
    def complete(self) -> bool:
        return self.failures == self.job["target_block_failures"] or self.shots == self.job["max_shots"]

    def path(self) -> Path:
        return self.directory / f"shots-{self.shots:09d}.jsonl.gz"

    def add(self, row: dict, line: bytes) -> None:
        if (self.complete or row["shot"] != self.shots or row["outcome"] not in OUTCOMES
                or not 0 <= row["iterations"] <= self.job["decoder"]["max_iterations"]
                or row["decode_ns"] < 0):
            raise ValueError(f"invalid ledger row for {self.job['id']} at shot {self.shots}")
        if self.shots == 0:
            self.first = row
        self.last = row
        self.shots += 1
        self.counts[row["outcome"]] += 1
        self.iterations += row["iterations"]
        self.decode_ns += row["decode_ns"]
        self.digest.update(line)

    def commit(self, rows: list[dict]) -> None:
        destination = self.path()
        temporary = destination.with_suffix(".tmp")
        with gzip.open(temporary, "wb", compresslevel=3) as stream:
            for row in rows:
                line = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                self.add(row, line)
                stream.write(line)
                if self.complete:
                    break
        os.replace(temporary, destination)

    def summary(self) -> dict:
        if not self.complete:
            raise ValueError("partial ledger cannot produce a terminal summary")
        n, k = self.shots, self.failures
        target = k == self.job["target_block_failures"]
        # Invert the first-passage time when the event target is reached.
        # Otherwise invert the terminal binomial count at the fixed cap.
        low = 0.0 if k == 0 else float(beta.ppf(.025, k, n - k + 1))
        high = (1.0 if k == n else float(beta.ppf(.975, k if target else k + 1, n - k)))
        return {"shots": n, "failures": k, "counts": dict(self.counts),
                "stop_reason": "target_block_failures" if target else "max_shots",
                "rate": k / n, "ci95_low": low, "ci95_high": high,
                "iterations": self.iterations, "decode_ns": self.decode_ns,
                "ledger_sha256": self.digest.hexdigest()}


def manifest_for(job: dict) -> dict:
    return {"schema": "yao-bpgd-completion-run-v1", "plan_sha256": sha(PLAN),
            "numpy": np.__version__, "job": job}


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
            with_batches = batches(job, ledger.shots)
            try:
                for rows in with_batches:
                    ledger.commit(rows)
                    print(job["id"], ledger.shots, ledger.failures, flush=True)
                    if ledger.complete:
                        break
            finally:
                with_batches.close()
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
            replay.pop("decode_ns")
            if replay != {k: v for k, v in stored.items() if k != "decode_ns"}:
                raise ValueError(f"shot replay mismatch: {directory}, {stored['shot']}")
        references = []
        for number in job["decoder"]["source_figures"]:
            curve = job["arm"].split("_r")[0] if number != 6 else job["arm"]
            value = SOURCE["figures"][str(number)]["curves"][curve][f"{job['physical_p']:.5f}"]
            references.append({"figure": number, "block_failure_rate": value})
        verified.append({"id": job["id"], "code": job["code"], "arm": job["arm"],
                         "physical_p": job["physical_p"], "matched_x_rate": job["matched_x_rate"],
                         "source_targets": references, "summary_sha256": sha(summary_path),
                         **summary})
    payload = {"schema": "yao-bpgd-completion-verification-v1", "plan_sha256": sha(PLAN),
               "planned_points": len(jobs(plan)), "points": verified}
    write_json(results / "verified.json", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--index", type=int)
    group.add_argument("--collect", action="store_true")
    group.add_argument("--list", action="store_true")
    parser.add_argument("--results", type=Path, default=RESULTS)
    args = parser.parse_args()
    if args.freeze:
        with PLAN.open("x") as handle:
            json.dump(code_plan(), handle, indent=2, sort_keys=True)
            handle.write("\n")
        return
    plan = load_plan()
    if args.list:
        for index, job in enumerate(jobs(plan)):
            print(index, job["id"], job["workers"])
    elif args.collect:
        result = collect(plan, args.results)
        print(f"{len(result['points'])}/{result['planned_points']} verified terminal points", flush=True)
    else:
        points = jobs(plan)
        if not 0 <= args.index < len(points):
            parser.error("index is outside the frozen point grid")
        print(json.dumps(run(points[args.index], args.results)), flush=True)


if __name__ == "__main__":
    main()
