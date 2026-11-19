"""Damping-first selection with disjoint screened rounds and shared policy RNG."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import multiprocessing as mp
import os
from pathlib import Path

import numpy as np

import run
import screen

STATE = {}


@lru_cache(maxsize=4)
def cohort(path, digest):
    if run.sha(path) != digest:
        raise ValueError("training cohort bytes changed")
    return screen.read_arrays(path)


def init(job, root):
    run.ROOT = Path(root)
    STATE.clear()
    STATE["job"] = job
    for b in run.BASES:
        circuit, model = run.case_model(job, b)
        STATE[b] = model, run.source_masks(circuit.detector_error_model())


def measure(task):
    folder, basis, start, stop, controls, data_path, digest, plan_digest, seed = task
    job = STATE["job"]
    model, masks = STATE[basis]
    policy = run.spec_for(job)
    decoder = run.AdvancedMinSum(model, job["method"], policy, controls, seed)
    path = Path(folder) / f"{basis}-{start:06d}.npz"
    marker = path.with_suffix(".json")
    identity = {"basis": basis, "start": start, "stop": stop, "controls": controls,
                "sample_sha256": digest, "plan_sha256": plan_digest, "policy_seed": seed}
    raw = cohort(data_path, digest)
    det, obs = raw["detectors"][start:stop], raw["observables"][start:stop]
    previous = run.read_json(marker) if marker.exists() else None
    if previous:
        if any(previous[k] != v for k, v in identity.items()) or previous["sha256"] != run.sha(path):
            raise ValueError("sealed training evidence changed")
        data = screen.read_arrays(path)
    else:
        data = screen.events(decoder, model, det, raw["indices"][start:stop])
    summary = run.chunk_summary(data, det, obs, model, *masks, job["method"], policy)
    if previous:
        if previous["summary"] != summary:
            raise ValueError("recomputed training totals changed")
    else:
        run.write_npz(path, data)
        run.write_json(marker, {**identity, "summary": summary, "sha256": run.sha(path)})
    return controls, basis, summary, str(marker), run.sha(marker)


def rank(row):
    return row["errors"], row["edges"], run.identity(row["controls"])


def dedup(controls):
    return list({run.identity(c): c for c in controls}.values())


def choose(rows):
    low = min(r["errors"] for r in rows)
    return min((r for r in rows if r["errors"] <= low+1),
               key=lambda r: (r["edges"], r["errors"], run.identity(r["controls"])))


def tune(plan, index, workers):
    job = plan["jobs"][index]
    folder = run.selection_path(job).parent
    folder.mkdir(parents=True, exist_ok=True)
    origin = run.ROOT / "results" / "screen" / job["group"]
    screen_path = origin / "screen.json"
    screen_receipt = run.read_json(screen_path)
    plan_digest = run.sha(run.ROOT / "plan.json")
    if screen_receipt["plan_sha256"] != plan_digest or screen_receipt["group"] != job["group"]:
        raise ValueError("screening receipt does not match point")
    t = plan["tuning"]
    candidates = [{**run.NEUTRAL, "damping": d} for d in t["damping"]]
    rounds, offset = [], 0
    block = 2 if job["mode"] == "xyz" else 8
    with run.lock(folder / "training.lock", True):
        _, model = run.case_model(job, "x")
        run.prepared(plan, {**job, "controls": run.NEUTRAL}, "x", model).decode(
            np.zeros(model.table.check_count, np.uint8), shot=0)
        with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn"), initializer=init,
                                 initargs=(job, str(run.ROOT))) as pool:
            for stage, n in enumerate(screen_receipt["shots_per_stage"]):
                rows = {}
                tasks = []
                for c in candidates:
                    key = run.identity(c)
                    d = folder / f"round-{stage}" / key
                    d.mkdir(parents=True, exist_ok=True)
                    rows[key] = {"controls": c, "bases": {b: run.empty_summary() for b in run.BASES}, "markers": {}}
                    for b in run.BASES:
                        seed = int(run.identity([t["policy_seed"], job["id"], stage, b])[:15], 16)
                        data = origin / f"{b}-cohort.npz"
                        digest = screen_receipt["bases"][b]["sha256"]
                        for start in range(offset, offset+n, block):
                            tasks.append((str(d), b, start, min(start+block, offset+n), c,
                                          str(data), digest, plan_digest, seed))
                seen = 0
                for c, b, totals, marker, sha in pool.map(measure, tasks, chunksize=1):
                    row = rows[run.identity(c)]
                    run.add(row["bases"][b], totals)
                    row["markers"][str(Path(marker).relative_to(folder))] = sha
                    seen += 1
                    if seen % 32 == 0 or seen == len(tasks):
                        print(job["id"], "round", stage+1, seen, "/", len(tasks), flush=True)
                for row in rows.values():
                    assert all(b["shots"] == n for b in row["bases"].values())
                    row["errors"] = sum(b["errors"] for b in row["bases"].values())
                    row["edges"] = sum(b["directed_edge_updates"] for b in row["bases"].values())
                ranked = sorted(rows.values(), key=rank)
                rounds.append({"round": stage+1, "shots_per_basis": n, "ranked": ranked})
                if stage == 0:
                    candidates = dedup([{"damping": r["controls"]["damping"], "alpha": a, "beta": b}
                                        for r in ranked[:2] for a in t["scaling"] for b in t["offset"]]+[run.NEUTRAL])
                elif stage == 1:
                    candidates = dedup([r["controls"] for r in ranked[:2]]+[run.NEUTRAL])
                offset += n
                run.write_json(folder / "progress.json",
                               {"point": job["id"], "rounds_completed": stage+1,
                                "front_runner": ranked[0]["controls"], "errors": ranked[0]["errors"]})
        selected = choose(ranked)
        selection = {"point": job["id"], "p": job["p"], "plan_sha256": plan_digest,
                     "screen_sha256": run.sha(screen_path), "controls": selected["controls"], "rounds": rounds}
        path = run.selection_path(job)
        if path.exists() and run.read_json(path) != selection:
            raise ValueError("deterministic selection changed")
        if not path.exists():
            run.write_json(path, selection)
        print("Selected", job["id"], selection["controls"], "training errors", selected["errors"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int)
    args = parser.parse_args()
    plan = run.load()
    if int(os.environ["SLURM_CPUS_PER_TASK"]) != plan["workers"]:
        raise ValueError("tuning worker allocation differs from plan")
    tune(plan, args.index, plan["workers"])
