"""Seal independent anchor samples and retain the first difficult syndromes."""
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import multiprocessing as mp
import os
from pathlib import Path
from time import perf_counter_ns

import numpy as np

import run
from bp_registry.circuit.tuned_minsum import MinSumSpec, TunableMinSum

STATE = {}


def init(point, iterations, root):
    run.ROOT = Path(root)
    STATE.clear()
    for basis in run.BASES:
        c, model = run.case_model(point, basis)
        STATE[basis] = (c, model, run.source_masks(c.detector_error_model()),
                        TunableMinSum(model, MinSumSpec(iterations=iterations)))


def events(decoder, model, det, shot_ids):
    size = len(det)
    candidate = np.empty((size, (model.table.variable_count + 7)//8), np.uint8)
    prediction = np.empty((size, (model.observable_matrix.shape[0]+7)//8), np.uint8)
    stats = np.empty((size, 6), np.uint64)
    elapsed = np.empty(size, np.uint64)
    trace, offsets = [], [0]
    for i, syn in enumerate(np.unpackbits(det, axis=1, bitorder="little", count=model.table.check_count)):
        start = perf_counter_ns()
        result = decoder.decode(syn, shot=int(shot_ids[i]))
        elapsed[i] = perf_counter_ns()-start
        candidate[i] = np.packbits(result.candidate, bitorder="little")
        observable = (model.observable_matrix @ result.candidate) % 2 ^ model.observable_bias
        prediction[i] = np.packbits(observable, bitorder="little")
        stats[i] = [result.iterations, result.directed_edge_updates, result.converged,
                    result.random_draws, result.biased_node_updates, result.lineage]
        trace.append(result.trace)
        offsets.append(offsets[-1]+len(result.trace))
    return {"candidate": candidate, "prediction": prediction, "stats": stats, "decode_ns": elapsed,
            "trace_ptr": np.array(offsets, np.int64),
            "trace": np.concatenate(trace) if offsets[-1] else np.empty((0, 8), np.int64)}


def read_arrays(path):
    with np.load(path, allow_pickle=False) as f:
        return {k: f[k] for k in f.files}


def block(args):
    basis, index, size, seed, prefix, plan_digest = args
    circuit, model, masks, decoder = STATE[basis]
    path = Path(prefix) / basis / f"{index:06d}.npz"
    marker = path.with_suffix(".json")
    expected = {"seed": seed, "basis": basis, "index": index, "size": size, "plan_sha256": plan_digest}
    if marker.exists():
        record = run.read_json(marker)
        if any(record[k] != v for k, v in expected.items()) or record["sha256"] != run.sha(path):
            raise ValueError("screened block identity changed")
        data = read_arrays(path)
    else:
        det, obs = circuit.compile_detector_sampler(seed=seed).sample(size, separate_observables=True, bit_packed=True)
        data = {**events(decoder, model, det, np.arange(size) + index*size), "detectors": det, "observables": obs}
    summary = run.bp.chunk_summary(data, data["detectors"], data["observables"], model, *masks, "bp", decoder.spec)
    sealed = {**expected, "summary": summary, "sha256": run.sha(path) if marker.exists() else None}
    if marker.exists():
        if sealed != record:
            raise ValueError("screened block totals changed")
    else:
        run.write_npz(path, data)
        sealed["sha256"] = run.sha(path)
        run.write_json(marker, sealed)
    hard = data["stats"][:, 2] == 0
    return basis, index, data["detectors"][hard], data["observables"][hard], np.flatnonzero(hard), run.sha(marker)


def prepare(plan, group, workers):
    point = plan["groups"][group]
    t = plan["tuning"]
    quotas = t["shots_per_stage"][point["mode"]]
    needed = sum(quotas)
    size = t["screen_block"][point["mode"]]
    folder = run.ROOT / "results" / "screen" / group
    folder.mkdir(parents=True, exist_ok=True)
    for b in run.BASES:
        (folder / b).mkdir(exist_ok=True)
    receipt = folder / "screen.json"
    digest = run.sha(run.ROOT / "plan.json")
    with run.lock(folder / "screen.lock", True):
        if receipt.exists():
            saved = run.read_json(receipt)
            assert saved["plan_sha256"] == digest and saved["group"] == group
            for b, info in saved["bases"].items():
                assert run.sha(folder / f"{b}-cohort.npz") == info["sha256"]
            return
        rows = {b: [] for b in run.BASES}
        markers = {b: {} for b in run.BASES}
        received = dict.fromkeys(run.BASES, 0)
        cursor = dict.fromkeys(run.BASES, 0)
        _, model = run.case_model(point, "x")
        TunableMinSum(model, MinSumSpec(iterations=t["screen_iterations"])).decode(
            np.zeros(model.table.check_count, np.uint8), shot=0)
        with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn"), initializer=init,
                                 initargs=(point, t["screen_iterations"], str(run.ROOT))) as pool:
            while True:
                active = [b for b in run.BASES if received[b] < needed and cursor[b] * size < t["screen_limit"]]
                if not active:
                    break
                tasks = []
                for i in range(workers):
                    b = active[i % len(active)]
                    ix = cursor[b]
                    if ix * size >= t["screen_limit"]:
                        continue
                    cursor[b] += 1
                    seed = int(run.identity([t["screen_seed"], group, b, ix])[:15], 16)
                    tasks.append((b, ix, size, seed, str(folder), digest))
                for b, ix, det, obs, indices, marker in pool.map(block, tasks, chunksize=1):
                    markers[b][str(ix)] = marker
                    take = needed-received[b]
                    if len(det) and take:
                        rows[b].append((det[:take], obs[:take], indices[:take]+ix*size))
                        received[b] += min(take, len(det))
                print(group, "hard syndromes", received, "sampled blocks", cursor, flush=True)
        count = min(received.values())
        if count < 3:
            raise ValueError("screening cap yielded fewer than three difficult syndromes in a memory basis")
        # Deterministic reduced quotas if a memory hits the screening cap.
        n0 = min(quotas[0], max(1, count*quotas[0]//needed))
        n1 = min(quotas[1], max(1, count*quotas[1]//needed))
        actual = [n0, n1, min(quotas[2], count-n0-n1)]
        bases = {}
        for b in run.BASES:
            det, obs, ids = (np.concatenate([row[i] for row in rows[b]])[:sum(actual)] for i in range(3))
            path = folder / f"{b}-cohort.npz"
            run.write_npz(path, {"detectors": det, "observables": obs, "indices": ids})
            bases[b] = {"sha256": run.sha(path), "screen_markers": markers[b], "sampled": cursor[b]*size}
        run.write_json(receipt, {"group": group, "p": point["p"], "plan_sha256": digest,
                                 "shots_per_stage": actual, "bases": bases,
                                 "conditioning": "nonconvergence after 40 ordinary min-sum sweeps"})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("group")
    args = parser.parse_args()
    plan = run.load()
    if int(os.environ["SLURM_CPUS_PER_TASK"]) != plan["workers"]:
        raise ValueError("screening worker allocation differs from plan")
    prepare(plan, args.group, plan["workers"])
