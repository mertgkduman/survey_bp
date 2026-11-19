"""Select one damping/scale/offset setting per code and detector mode at p=.003."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import multiprocessing as mp
import os
from pathlib import Path
from time import perf_counter_ns

import numpy as np

import run
from bp_registry.circuit.tuned_minsum import MinSumSpec, TunableMinSum

STATE = {}
BLOCK = 16
NEUTRAL = {"damping": 0.0, "alpha": 1.0, "beta": 0.0}


@lru_cache(maxsize=8)
def arrays(path):
    with np.load(path, allow_pickle=False) as data:
        return {k: data[k] for k in data.files}


def initialize(point, cap):
    STATE.clear()
    for basis in run.BASES:
        circuit, model = run.case_model(point, basis)
        STATE[basis] = model, run.source_masks(circuit.detector_error_model())
    STATE["cap"] = cap


def stage_noise(plan, point, folder, stage, basis, n):
    path = folder / f"round-{stage}-{basis}.npz"
    marker = path.with_suffix(".json")
    case = point["bases"][basis]
    seed = int(run.identity([plan["tuning"]["seed"], point["group"], stage, basis])[:15], 16)
    expected = {"seed": seed, "shots": n, "circuit_sha256": case["sha256"], "software": plan["software"]}
    if marker.exists():
        meta = run.read_json(marker)
        if meta != {**expected, "sha256": run.sha(path)}:
            raise ValueError("sealed tuning samples changed")
    else:
        det, obs = run.circuit(case).compile_detector_sampler(seed=seed).sample(
            n, separate_observables=True, bit_packed=True)
        run.write_npz(path, {"detectors": det, "observables": obs})
        sort_meta = {**expected, "sha256": run.sha(path)}
        run.write_json(marker, sort_meta)
    return str(path), run.sha(path)


def measure(task):
    folder, basis, start, stop, controls, noise_path, noise_digest, plan_digest = task
    model, masks = STATE[basis]
    spec = MinSumSpec(STATE["cap"], **controls)
    folder = Path(folder)
    path = folder / f"{basis}-{start:06d}.npz"
    marker = path.with_suffix(".json")
    identity = {"basis": basis, "start": start, "stop": stop, "controls": controls,
                "noise_sha256": noise_digest, "plan_sha256": plan_digest}
    if run.sha(noise_path) != noise_digest:
        raise ValueError("training sample digest changed")
    noise = arrays(noise_path)
    det, obs = noise["detectors"][start:stop], noise["observables"][start:stop]
    n = len(det)
    if marker.exists():
        existing = run.read_json(marker)
        if any(existing[k] != v for k, v in identity.items()) or existing["ledger_sha256"] != run.sha(path):
            raise ValueError("training ledger binding changed")
        data = arrays(str(path))
    else:
        decoder = TunableMinSum(model, spec)
        candidate = np.empty((n, (model.table.variable_count + 7) // 8), np.uint8)
        prediction = np.empty_like(obs)
        stats = np.zeros((n, 6), np.uint64)
        latency = np.empty(n, np.uint64)
        for i, syndrome in enumerate(np.unpackbits(det, axis=1, bitorder="little", count=model.table.check_count)):
            begin = perf_counter_ns()
            result = decoder.decode(syndrome, shot=start + i)
            latency[i] = perf_counter_ns() - begin
            candidate[i] = np.packbits(result.candidate, bitorder="little")
            prediction[i] = np.packbits((model.observable_matrix @ result.candidate) % 2 ^ model.observable_bias, bitorder="little")
            stats[i, :3] = result.iterations, result.directed_edge_updates, result.converged
        data = {"candidate": candidate, "prediction": prediction, "stats": stats,
                "decode_ns": latency, "trace": np.empty((0, 8), np.int64),
                "trace_ptr": np.zeros(n + 1, np.int64)}
    summary = run.chunk_summary(data, det, obs, model, *masks, "tuned-bp", spec)
    if marker.exists():
        if existing["summary"] != summary:
            raise ValueError("training ledger failed audit")
    else:
        run.write_npz(path, data)
        run.write_json(marker, {**identity, "ledger_sha256": run.sha(path), "summary": summary})
    return controls, basis, summary, str(marker), run.sha(marker)


def rank(row):
    return row["errors"], row["iterations"], run.identity(row["controls"])


def choose(rows, tolerance):
    minimum = min(row["errors"] for row in rows)
    return min((row for row in rows if row["errors"] <= minimum + tolerance),
               key=lambda r: (r["iterations"], r["errors"], run.identity(r["controls"])))


def tune(plan, group, workers):
    point = plan["training_points"][group]
    folder = run.selection_path(group).parent
    folder.mkdir(parents=True, exist_ok=True)
    with run.lock(folder / "tune.lock", True):
        _tune(plan, point, folder, workers)


def _tune(plan, point, folder, workers):
    protocol = plan["tuning"]
    plan_digest = run.sha(run.ROOT / "plan.json")
    cap = plan["protocol"]["iterations"]
    candidates, rounds = protocol["candidates"], []
    # Compile once before spawned workers import the shared cache.
    _, model = run.case_model(point, "x")
    TunableMinSum(model, MinSumSpec(cap)).decode(np.zeros(model.table.check_count, np.uint8), shot=0)
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn"),
                             initializer=initialize, initargs=(point, cap)) as pool:
        for stage, n in enumerate(protocol["shots_per_basis"]):
            shared = {b: stage_noise(plan, point, folder, stage, b, n) for b in run.BASES}
            rows = {run.identity(c): {"controls": c, "bases": {b: run.empty_summary() for b in run.BASES},
                                      "chunks": {}}
                    for c in candidates}
            tasks = []
            for key, row in rows.items():
                arm = folder / f"round-{stage}" / key
                arm.mkdir(parents=True, exist_ok=True)
                for b, (path, digest) in shared.items():
                    for start in range(0, n, BLOCK):
                        tasks.append((str(arm), b, start, min(start + BLOCK, n),
                                      row["controls"], path, digest, plan_digest))
            completed = 0
            for controls, basis, summary, marker, digest in pool.map(measure, tasks, chunksize=1):
                row = rows[run.identity(controls)]
                run.add(row["bases"][basis], summary)
                row["chunks"][str(Path(marker).relative_to(folder))] = digest
                completed += 1
                if completed % 64 == 0 or completed == len(tasks):
                    print(point["group"], "round", stage, completed, "/", len(tasks), flush=True)
            for row in rows.values():
                if any(v["shots"] != n for v in row["bases"].values()):
                    raise ValueError("tuning denominators disagree")
                for field in ("errors", "iterations"):
                    row[field] = sum(v[field] for v in row["bases"].values())
            scored = sorted(rows.values(), key=rank)
            rounds.append({"stage": stage, "shots_per_basis": n, "ranked": scored})
            if stage < len(protocol["advance"]):
                keep = protocol["advance"][stage]
                candidates = [row["controls"] for row in scored[:keep]]
                if NEUTRAL not in candidates:
                    candidates[-1] = NEUTRAL
        winner = choose(scored, protocol["final_error_tie"])
    result = {"plan_sha256": plan_digest, "group": point["group"], "p": point["p"],
              "iteration_limit": cap, "controls": winner["controls"], "rounds": rounds}
    path = run.selection_path(point["group"])
    if path.exists() and run.read_json(path) != result:
        raise ValueError("sealed training selection changed")
    if not path.exists():
        run.write_json(path, result)
    print("Selected", point["group"], winner["controls"], "errors", winner["errors"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("group")
    args = parser.parse_args()
    plan = run.load()
    if int(os.environ.get("SLURM_CPUS_PER_TASK", 0)) != plan["workers"] or len(os.sched_getaffinity(0)) < plan["workers"]:
        raise ValueError("training needs the plan's Slurm CPU allocation")
    tune(plan, args.group, plan["workers"])
