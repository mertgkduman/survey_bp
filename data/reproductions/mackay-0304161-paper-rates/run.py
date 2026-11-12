"""Run the published MacKay rate grid with certified, counted branch pruning."""

from __future__ import annotations

import argparse
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import fcntl
import importlib.util
from itertools import islice
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ORIGINAL = ROOT.with_name("mackay-0304161-unicycle")
PLAN = ROOT / "plan.json"
RESULTS = ROOT / "results"
RATES = (1000, 1300, 2000, 3000, 4000)  # exact p*100000 coordinates
CHUNK_SIZE = 1024
spec = importlib.util.spec_from_file_location("_paper_rate_original", ORIGINAL / "run.py")
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
sha, write_json = original.sha, original.write_json
original_event = original.event
original_split = original.split_decode


def code_plan() -> dict:
    plan = deepcopy(original.code_plan())
    plan["schema"] = "mackay-paper-rates-plan-v1"
    plan["parent_plan_sha256"] = sha(ORIGINAL / "plan.json")
    plan["source_plot"] = json.loads((ROOT / "source_points.json").read_text())
    plan["matched_rates"] = [{"x_only": rate / 100000, "depolarizing": 3 * rate / 200000} for rate in RATES]
    plan["arms"]["unicycle_sp"]["controller"].update({
        "certified_pruning": "skip_second_if_first_valid_and_twice_weight_below_distance_bound",
        "distance_bound": "q_plus_2_for_extended_projective_plane_incidence_code",
        "minimum_distance_bounds": {"unicycle74": 10, "unicycle274": 18},
        "hypothesis_order": "syndrome_majority_then_other; independent_branch_states",
        "work_accounting": "executed_branch_sweeps_only; skipped_branch_zero",
    })
    plan["claim_limit"] = (
        "Paper error-rate grid; length-274 unicycle SP is the direct source comparison. "
        "Other arms are controlled comparisons. Classical source block errors and quantum "
        "stabilizer equivalence are recorded separately. Numerical conventions and the 88,200 "
        "total-sweep ceiling remain controlled settings. Certified pruning preserves the selected "
        "candidate and changes executed work; work is not pooled with the original unpruned arm.")
    for path in (Path(__file__), ROOT / "source_points.json"):
        plan["implementation_sha256"][str(path.relative_to(REPO))] = sha(path)
    return plan


def load_plan() -> dict:
    plan = json.loads(PLAN.read_text())
    if plan != code_plan():
        raise ValueError("frozen paper-rate plan, software or implementation has changed")
    return plan


def jobs(plan: dict) -> list[dict]:
    result = []
    for job in original.jobs(plan):
        p = job["matched_x_rate"]
        workers = (16 if job["code"] == "unicycle274" and job["arm"] == "unicycle_sp" and p <= .02
                   else 4 if p <= .02 else 1)
        # p=.0195 must not be rounded to a different experiment identity.
        result.append({**job, "workers": workers,
                       "id": f"{job['code']}-{job['arm']}-p{round(job['physical_p'] * 100000):05d}"})
    return result


def certified_split(graph, syndrome: np.ndarray, *, p: float, limit: int):
    n = graph.table.variable_count + 1
    bound = {74: 10, 274: 18}.get(n)
    if bound is None or not 0 < p < .5:
        raise ValueError("certified pruning requires a qualified Construction U graph and p<1/2")
    first = int(2 * np.count_nonzero(syndrome) > len(syndrome))
    candidates, iterations = [], [0, 0]
    for extra in (first, 1 - first):
        decoded = graph.run(syndrome ^ extra, error_rate=p, max_iterations=limit)
        candidate = np.append(decoded.candidate, np.uint8(extra)).astype(np.uint8)
        iterations[extra] = decoded.iterations
        weight = int(candidate.sum())
        candidates.append((not decoded.converged, weight, extra, candidate))
        if decoded.converged and 2 * weight < bound:
            return candidate, True, iterations
    # For matched Bernoulli p<1/2, full-pattern likelihood is strictly
    # decreasing in weight. Comparing integer weights preserves exact ties.
    selected = min(candidates, key=lambda row: row[:3])
    return selected[3], not selected[0], iterations


original.split_decode = certified_split
decoder_state = original.decoder_state


def event(state: tuple, shot: int) -> dict:
    row = original_event(state, shot)
    row["certified_branch_pruned"] = state[0]["arm"] == "unicycle_sp" and 0 in row["branch_iterations"]
    return row


class Ledger(original.Ledger):
    def __init__(self, directory: Path, job: dict):
        self.pruned = 0
        super().__init__(directory, job)

    def add(self, row: dict, line: bytes) -> None:
        skipped = self.job["arm"] == "unicycle_sp" and 0 in row["branch_iterations"]
        if (type(row.get("certified_branch_pruned")) is not bool or row["certified_branch_pruned"] != skipped
                or skipped and row["outcome"] == "type_i"):
            raise ValueError("invalid certified branch counter")
        super().add(row, line)
        self.pruned += skipped

    def summary(self) -> dict:
        summary = super().summary()
        n = summary["shots"]
        classical = summary["failures"] + summary["counts"]["stabilizer_success"]
        return {**summary, "certified_branches_pruned": self.pruned,
                "classical_block_errors": classical, "classical_block_error_rate": classical / n}


def manifest_for(job: dict) -> dict:
    return {"schema": "mackay-paper-rates-run-v1", "plan_sha256": sha(PLAN), "job": job}


def set_worker(state):
    global WORKER_STATE
    WORKER_STATE = state


def batch(state, offset):
    job = state[0]
    rows, failures = [], 0
    for shot in range(offset, min(offset + CHUNK_SIZE, job["max_shots"])):
        row = event(state, shot)
        rows.append(row)
        failures += row["outcome"] in original.base.FAILURES
        if failures == job["target_block_failures"]:
            break
    return rows


def worker_batch(offset):
    return batch(WORKER_STATE, offset)


def batches(job, start):
    state = decoder_state(job)
    offsets = iter(range(start, job["max_shots"], CHUNK_SIZE))
    if job["workers"] == 1:
        for offset in offsets:
            yield batch(state, offset)
        return
    # Warm the qualified kernels before independent shot workers are forked.
    event(state, start)
    with ProcessPoolExecutor(max_workers=job["workers"], initializer=set_worker, initargs=(state,)) as pool:
        pending = deque(pool.submit(worker_batch, offset) for offset in islice(offsets, job["workers"]))
        while pending:
            yield pending.popleft().result()
            offset = next(offsets, None)
            if offset is not None:
                pending.append(pool.submit(worker_batch, offset))


def run(job: dict, results: Path) -> dict:
    directory = results / job["id"]
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = directory / "manifest.json"
        expected = manifest_for(job)
        if not path.exists():
            write_json(path, expected)
        elif json.loads(path.read_text()) != expected:
            raise ValueError(f"checkpoint manifest mismatch: {directory}")
        ledger = Ledger(directory, job)
        stream = batches(job, ledger.shots) if not ledger.complete else iter(())
        try:
            for rows in stream:
                ledger.commit(rows)
                print(job["id"], ledger.shots, ledger.failures, flush=True)
                if ledger.complete:
                    break
        finally:
            stream.close() if hasattr(stream, "close") else None
        summary = {**ledger.summary(), "manifest_sha256": sha(path)}
        target = directory / "summary.json"
        if target.exists() and json.loads(target.read_text()) != summary:
            raise ValueError(f"terminal summary mismatch: {directory}")
        write_json(target, summary)
        return summary


def collect(plan: dict, results: Path) -> dict:
    verified = []
    for job in jobs(plan):
        directory = results / job["id"]
        path = directory / "summary.json"
        if not path.exists():
            continue
        ledger = Ledger(directory, job)
        manifest = directory / "manifest.json"
        summary = json.loads(path.read_text())
        if (json.loads(manifest.read_text()) != manifest_for(job)
                or summary != {**ledger.summary(), "manifest_sha256": sha(manifest)}):
            raise ValueError(f"terminal evidence mismatch: {directory}")
        state = decoder_state(job)
        for stored in (ledger.first, ledger.last):
            replay = event(state, stored["shot"])
            if {k: v for k, v in replay.items() if k != "decode_ns"} != {k: v for k, v in stored.items() if k != "decode_ns"}:
                raise ValueError(f"shot replay mismatch: {directory}, {stored['shot']}")
        source = plan["source_plot"]["points"].get(f"{job['matched_x_rate']:.3f}")
        verified.append({"id": job["id"], "code": job["code"], "arm": job["arm"],
                         "physical_p": job["physical_p"], "matched_x_rate": job["matched_x_rate"],
                         "source_target": source if job["code"] == "unicycle274" and job["arm"] == "unicycle_sp" else None,
                         "summary_sha256": sha(path), **summary})
    payload = {"schema": "mackay-paper-rates-verification-v1", "plan_sha256": sha(PLAN),
               "planned_points": len(jobs(plan)), "points": verified}
    results.mkdir(exist_ok=True, parents=True)
    write_json(results / "verified.json", payload)
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--index", type=int)
    group.add_argument("--collect", action="store_true")
    group.add_argument("--list", action="store_true")
    parser.add_argument("--results", type=Path, default=RESULTS)
    args = parser.parse_args()
    if args.freeze:
        frozen = code_plan()
        with PLAN.open("x") as stream:
            json.dump(frozen, stream, indent=2, sort_keys=True)
            stream.write("\n")
        return
    plan = load_plan()
    points = jobs(plan)
    if args.list:
        for i, job in enumerate(points):
            print(i, job["id"], job["workers"])
    elif args.collect:
        receipt = collect(plan, args.results)
        print(f"{len(receipt['points'])}/{receipt['planned_points']} terminal points verified")
    elif not 0 <= args.index < len(points):
        parser.error("index is outside the frozen rate grid")
    else:
        print(json.dumps(run(points[args.index], args.results)), flush=True)


if __name__ == "__main__":
    main()
