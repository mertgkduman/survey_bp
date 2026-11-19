"""Adapter from the frozen ordered campaign runner to the BP follow-up."""
from dataclasses import asdict
from functools import lru_cache
import importlib.util
import json
from pathlib import Path

import numpy as np

from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.tuned_minsum import MinSumSpec, TunableMinSum
from sources import ROOT, REPO, PARENTS, circuit, evaluation_points, parent_plans, training_points

BASES = ("x", "z")
WORKERS = 20
VERSION = "circuit-bp-ordered-v1"


def import_parent(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Read and extend the existing immutable shared-noise stores under their own locks.
PARENT_RUN = {mode: import_parent(path / "run.py", f"parent_{mode}")
              for mode, path in PARENTS.items()}
shared = PARENT_RUN["xyz"]
sha, write_json, write_npz, lock = shared.sha, shared.write_json, shared.write_npz, shared.lock
identity = shared.identity
software, empty_summary, add = shared.software, shared.empty_summary, shared.add
finished, terminal = shared.finished, shared.terminal
source_masks, audit_candidates = shared.source_masks, shared.audit_candidates


def read_json(path):
    return json.loads(Path(path).read_text())


def design(write_training=False):
    jobs = []
    for point in evaluation_points():
        for method in ("bp", "tuned-bp"):
            jobs.append({**point, "method": method,
                         "id": f'{point["group"]}-p{round(point["p"]*1e6):06d}-{method}'})
    coarse = [{"damping": d, "alpha": a, "beta": b}
              for d in (0.0, 0.25, 0.5, 0.75)
              for a in (0.65, 0.8, 1.0)
              for b in (0.0, 0.5)]
    return {"schema": VERSION, "software": software(), "jobs": jobs, "workers": WORKERS,
            "training_points": training_points(write=write_training),
            "protocol": {"target_errors": 20, "max_shots": 100_000_000,
                         "minimum_free_bytes": 20 * 1024**3, "iterations": 18080,
                         "evaluation_batch": {"xz": 512, "xyz": 32}},
            "tuning": {"seed": 20261119071, "candidates": coarse,
                       "shots_per_basis": [128, 512, 2048], "advance": [6, 3],
                       "final_error_tie": 1,
                       "rank": "minimum total observable errors over equal X/Z shots; within one error of final minimum prefer fewer mean sweeps"},
            "parent_plans": {mode: sha(directory / "plan.json") for mode, directory in PARENTS.items()}}


def freeze():
    plan = design(write_training=True)
    files = list(ROOT.glob("*.py")) + list(ROOT.glob("*.sh")) + list((ROOT / "training-circuits").glob("*.stim"))
    files += [REPO / "src/bp_registry/circuit/tuned_minsum.py",
              REPO / "src/bp_registry/canonical/compiled.py", PARENTS["xyz"] / "parallel.py"]
    pins = {}
    for mode, parent in parent_plans().items():
        for path, digest in parent["implementation_sha256"].items():
            if pins.setdefault(path, digest) != digest:
                raise ValueError(f"parents pin different bytes for {path}")
        pins[str((PARENTS[mode] / "plan.json").relative_to(REPO))] = plan["parent_plans"][mode]
    pins.update({str(path.relative_to(REPO)): sha(path) for path in files})
    plan["implementation_sha256"] = pins
    path = ROOT / "plan.json"
    if path.exists():
        if read_json(path) != plan:
            raise ValueError("refusing to overwrite frozen BP plan")
    else:
        write_json(path, plan)
    load()
    return plan


def load():
    plan = read_json(ROOT / "plan.json")
    if plan["schema"] != VERSION or plan["software"] != software():
        raise ValueError("frozen BP plan/software changed")
    for name, digest in plan["implementation_sha256"].items():
        if sha(REPO / name) != digest:
            raise ValueError(f"frozen dependency changed: {name}")
    return plan


def effective_plan(plan, job):
    protocol = plan["protocol"]
    return {**plan, "protocol": {**protocol, "batch": protocol["evaluation_batch"][job["mode"]]}}


def case_model(job, basis):
    c = circuit(job["bases"][basis])
    return c, DemBinaryModel.from_dem(c.detector_error_model())


def spec_for(job):
    return MinSumSpec(**job["spec"])


def prepared(plan, job, basis, model):
    return TunableMinSum(model, spec_for(job))


def selection_path(group):
    return ROOT / "results" / "training" / group / "selection.json"


def resolve_job(plan, index):
    job = plan["jobs"][index]
    spec = MinSumSpec(plan["protocol"]["iterations"])
    binding = None
    if job["method"] == "tuned-bp":
        path = selection_path(job["group"])
        selection = read_json(path)
        if (selection["plan_sha256"] != sha(ROOT / "plan.json") or selection["group"] != job["group"]
                or selection["iteration_limit"] != spec.iterations
                or selection["p"] != plan["training_points"][job["group"]]["p"]
                or selection["controls"] not in plan["tuning"]["candidates"]):
            raise ValueError("tuning selection is bound to a different study")
        spec = MinSumSpec(spec.iterations, **selection["controls"])
        binding = sha(path)
    return {**job, "spec": asdict(spec), "selection_sha256": binding}


@lru_cache(maxsize=2)
def frozen_parent_plan(mode):
    return read_json(PARENTS[mode] / "plan.json")


def slice_parent(plan, job, basis, index):
    parent = PARENT_RUN[job["mode"]]
    source = frozen_parent_plan(job["mode"])
    length = plan["protocol"]["batch"]
    start = index * length
    parent_index, parent_offset = divmod(start, source["protocol"]["batch"])
    if source["protocol"]["batch"] % length:
        raise ValueError("local batch crosses parent source chunks")
    directory = f'{job["code"]}-p{round(job["p"]*1e6):06d}-{basis}'
    path = parent.ROOT / "results" / "noise" / directory / f"{parent_index:08d}.npz"
    local = ROOT / "results" / "noise" / job["mode"] / directory / f"{index:08d}.npz"
    return parent, source, parent_index, parent_offset, length, path, local


def noise(plan, job, basis, index, circuit):
    parent, source, parent_index, offset, length, source_path, path = slice_parent(plan, job, basis, index)
    # The parent helper locks and verifies already sealed bytes and atomically extends
    # the same stream if the new BP prefix needs samples beyond the parent runs.
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = path.with_suffix(".json")
    with lock(path.with_suffix(".lock")):
        if not marker.exists():
            original, meta, raw = parent.noise(source, job, basis, parent_index, circuit)
            if original != source_path:
                raise ValueError("unexpected parent noise path")
            data = {k: v[offset:offset + length] for k, v in raw.items()}
            write_npz(path, data)
            write_json(marker, {"sha256": sha(path), "parent_noise_sha256": meta["sha256"],
                                "parent_path": str(original.relative_to(REPO)), "parent_offset": offset})
        meta = read_json(marker)
        verify_noise_binding(plan, job, basis, index * length,
                             {"noise_path": str(path.relative_to(ROOT)), "noise_offset": 0,
                              "noise_sha256": meta["sha256"]})
        with np.load(path, allow_pickle=False) as f:
            return path, meta, {k: f[k] for k in f.files}


def verify_noise_binding(plan, job, basis, start, value):
    size = plan["protocol"]["batch"]
    parent, source, index, offset, _, source_path, path = slice_parent(plan, job, basis, start // size)
    meta = read_json(path.with_suffix(".json"))
    if (value["noise_path"] != str(path.relative_to(ROOT)) or value["noise_offset"] != start % size
            or meta["sha256"] != value["noise_sha256"] or meta["sha256"] != sha(path)
            or meta["parent_path"] != str(source_path.relative_to(REPO)) or meta["parent_offset"] != offset):
        raise ValueError("BP sample slice binding changed")
    original = read_json(source_path.with_suffix(".json"))
    expected = {"circuit_sha256": job["bases"][basis]["sha256"], "seed": parent.seed(source, job, basis, "noise", index),
                "start": index * source["protocol"]["batch"], "max_shots": source["protocol"]["max_shots"],
                "software": source["software"]}
    if original["sampling"] != expected or original["sha256"] != meta["parent_noise_sha256"]:
        raise ValueError("parent sample identity changed")
    return path


def chunk_summary(data, det, obs, model, dmasks, omasks, method, spec):
    n, stats = len(det), data["stats"]
    candidate, prediction = data["candidate"], data["prediction"]
    if (not n or stats.shape != (n, 6) or stats.dtype != np.uint64
            or det.dtype != np.uint8 or det.shape != (n, dmasks.shape[1])
            or obs.dtype != np.uint8 or obs.shape != (n, omasks.shape[1])
            or candidate.dtype != np.uint8 or candidate.shape != (n, (len(dmasks) + 7) // 8)
            or prediction.dtype != np.uint8 or prediction.shape != obs.shape
            or data["decode_ns"].shape != (n,) or data["decode_ns"].dtype != np.uint64
            or data["trace"].shape != (0, 8) or data["trace_ptr"].shape != (n + 1,) or np.any(data["trace_ptr"])):
        raise ValueError("invalid single-attempt BP ledger")
    iters, edges, converged = stats[:, 0], stats[:, 1], stats[:, 2]
    if (np.any(iters < 1) or np.any(iters > spec.iterations) or np.any(converged > 1)
            or np.any((converged == 0) & (iters != spec.iterations))
            or np.any(edges != iters * (2 * model.table.edge_count)) or np.any(stats[:, 3:])):
        raise ValueError("invalid single-attempt BP stopping or work")
    counts = audit_candidates(candidate, det, obs, prediction, stats, dmasks, omasks)
    return {"shots": n, "errors": int(counts[1]), "iterations": int(iters.sum()),
            "directed_edge_updates": int(edges.sum()), "decode_ns": int(data["decode_ns"].sum()),
            "nonconvergence": int(n - converged.sum()), "joint_counts": counts[2:].tolist(),
            "random_draws": 0, "biased_node_updates": 0}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true", required=True)
    parser.parse_args()
    print("Frozen", len(freeze()["jobs"]), "BP points")
