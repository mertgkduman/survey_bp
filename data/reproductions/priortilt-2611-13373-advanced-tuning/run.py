"""Frozen inputs and ledger adapter for tuning the advanced circuit decoders."""
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

from bp_registry.canonical.prior_tilt import PriorTiltSpec
from bp_registry.circuit.advanced_minsum import AdvancedMinSum
from bp_registry.circuit.paper_decoders import PaperDecoderSpec
from bp_registry.circuit.relay_list import RelayListSpec

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BP = ROOT.parent / "priortilt-2611-13373-bp"
sys.path.append(str(BP))
loader = importlib.util.spec_from_file_location("bp_shared", BP / "run.py")
bp = importlib.util.module_from_spec(loader)
loader.loader.exec_module(bp)

PARENTS, PARENT_RUN = bp.PARENTS, bp.PARENT_RUN
shared = PARENT_RUN["xyz"]
identity, sha = bp.identity, bp.sha
read_json, write_json, write_npz, lock = bp.read_json, bp.write_json, bp.write_npz, bp.lock
case_model, circuit, source_masks = bp.case_model, bp.circuit, bp.source_masks
finished, terminal = shared.finished, shared.terminal
BASES = ("x", "z")
VERSION = "advanced-kernel-tuning-v1"
NEUTRAL = {"damping": 0., "alpha": 1., "beta": 0.}
RATES = {"BB144": .003, "BB70": .001, "GB102": .001}
POLICY_TYPES = {"priortilt": PriorTiltSpec, "relay": PaperDecoderSpec, "beam": PaperDecoderSpec,
                "relay5": RelayListSpec}


def design():
    inputs = {(p["mode"], p["code"], p["p"]): p for p in bp.evaluation_points()}
    jobs = []
    groups = {}
    for mode, parent in PARENT_RUN.items():
        for source in bp.frozen_parent_plan(mode)["jobs"]:
            if source["p"] != RATES[source["code"]]:
                continue
            point = inputs[mode, source["code"], source["p"]]
            method = source["method"]
            policy = json.loads(json.dumps(asdict(parent.spec_for(source))))
            manifest = parent.ROOT / "results" / source["id"] / "manifest.json"
            if manifest.exists() and read_json(manifest)["resolved_policy"] != policy:
                raise ValueError("frozen paper settings disagree with the existing run")
            jobs.append({**point, "id": f'{point["group"]}-{method}-tuned',
                         "parent_id": source["id"], "method": method, "policy": policy,
                         "seed_by_basis": {b: parent.seed(bp.frozen_parent_plan(mode), source, b, "policy") for b in BASES}})
            groups[point["group"]] = point
    if len(jobs) != 11 or len(groups) != 4:
        raise ValueError("unexpected anchor/controller inventory")
    return {"schema": VERSION, "software": bp.software(), "jobs": jobs, "groups": groups, "workers": 20,
            "protocol": {"target_errors": 20, "max_shots": 100_000_000, "minimum_free_bytes": 20 * 1024**3,
                         "evaluation_batch": {"xz": 256, "xyz": 32}},
            "tuning": {"screen_seed": 20261119081, "policy_seed": 20261119082, "screen_limit": 2_097_152,
                       "screen_block": {"xz": 2048, "xyz": 128}, "screen_iterations": 40,
                       "shots_per_stage": {"xz": [64, 128, 256], "xyz": [16, 32, 64]},
                       "damping": [0., .05, .10, .15, .20, .25, .35, .50, .70],
                       "scaling": [.75, .9, 1.], "offset": [0., .5],
                       "rank": "observable errors; among final rows within one error choose fewer directed edge updates"}}


def freeze():
    plan = design()
    pins = {}
    for mode, directory in PARENTS.items():
        parent = bp.frozen_parent_plan(mode)
        for rel, digest in parent["implementation_sha256"].items():
            if pins.setdefault(rel, digest) != digest:
                raise ValueError(f"inconsistent parent dependency {rel}")
        path = directory / "plan.json"
        pins[str(path.relative_to(REPO))] = sha(path)
    paths = [*ROOT.glob("*.py"), *ROOT.glob("*.sh"),
             BP / "run.py", BP / "sources.py",
             REPO / "src/bp_registry/circuit/advanced_minsum.py",
             REPO / "src/bp_registry/circuit/tuned_minsum.py", PARENTS["xyz"] / "parallel.py"]
    pins.update({str(p.relative_to(REPO)): sha(p) for p in paths})
    plan["implementation_sha256"] = pins
    path = ROOT / "plan.json"
    if path.exists() and read_json(path) != plan:
        raise ValueError("advanced tuning plan changed")
    if not path.exists():
        write_json(path, plan)
    return load()


def load():
    plan = read_json(ROOT / "plan.json")
    if plan["schema"] != VERSION or plan["software"] != bp.software():
        raise ValueError("advanced tuning schema or software changed")
    for rel, digest in plan["implementation_sha256"].items():
        if sha(REPO / rel) != digest:
            raise ValueError(f"frozen dependency changed: {rel}")
    return plan


def effective_plan(plan, job):
    return bp.effective_plan(plan, job)


def selection_path(job):
    return ROOT / "results" / "training" / job["id"] / "selection.json"


def resolve_job(plan, index):
    job = plan["jobs"][index]
    path = selection_path(job)
    selected = read_json(path)
    screen = ROOT / "results" / "screen" / job["group"] / "screen.json"
    if (selected["plan_sha256"] != sha(ROOT / "plan.json") or selected["point"] != job["id"]
            or selected["p"] != job["p"] or selected["screen_sha256"] != sha(screen)):
        raise ValueError("selection identifies a different job or screening cohort")
    from tune import choose
    if selected["controls"] != choose(selected["rounds"][-1]["ranked"])["controls"]:
        raise ValueError("sealed selection differs from the declared objective")
    return {**job, "controls": selected["controls"], "selection_sha256": sha(path)}


def spec_for(job):
    return POLICY_TYPES[job["method"]](**job["policy"])


def prepared(plan, job, basis, model):
    return AdvancedMinSum(model, job["method"], spec_for(job), job["controls"], job["seed_by_basis"][basis])


def noise(plan, job, basis, index, circuit):
    bp.ROOT = ROOT
    return bp.noise(plan, job, basis, index, circuit)


def verify_noise_binding(plan, job, basis, start, meta):
    bp.ROOT = ROOT
    return bp.verify_noise_binding(plan, job, basis, start, meta)


def empty_summary():
    return {**shared.empty_summary(), "guarded_shots": 0, "guarded_messages": 0}


def add(summary, row):
    shared.add(summary, row)
    for key in ("guarded_shots", "guarded_messages"):
        summary[key] += row[key]


def chunk_summary(data, det, obs, model, dmasks, omasks, method, spec):
    trace, ptr = data["trace"], data["trace_ptr"]
    trailer = trace[:, 0] == -2
    count = int(np.count_nonzero(trailer))
    if count:
        ends = ptr[1:][np.diff(ptr) > 0] - 1
        if not np.isin(np.flatnonzero(trailer), ends).all():
            raise ValueError("range guard counter must end the shot trace")
        evidence = trace[trailer]
        if np.any(evidence[:, 1] <= 0) or np.any(evidence[:, 2:]):
            raise ValueError("invalid range guard counter")
        prefix = np.concatenate(([0], np.cumsum(trailer)))
        stripped = {**data, "trace": trace[~trailer], "trace_ptr": ptr - prefix[ptr]}
    else:
        stripped = data
    row = shared.chunk_summary(stripped, det, obs, model, dmasks, omasks, method, spec)
    return {**row, "guarded_shots": count, "guarded_messages": int(trace[trailer, 1].sum())}


if __name__ == "__main__":
    print("Frozen", len(freeze()["jobs"]), "advanced tuning points")
