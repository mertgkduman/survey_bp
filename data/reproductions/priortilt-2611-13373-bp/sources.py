"""Resolve the frozen evaluation grid and qualify training-only rate rescaling."""
import json
import math
from decimal import Decimal
from pathlib import Path

import stim

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PARENTS = {
    "xz": ROOT.parent / "priortilt-2611-13373",
    "xyz": ROOT.parent / "priortilt-2611-13373-xyz",
}
TRAIN_P = 0.003
NOISE = {"DEPOLARIZE1", "DEPOLARIZE2", "M", "MX", "MY", "MR", "MRX", "MRY",
         "X_ERROR", "Y_ERROR", "Z_ERROR"}


def parent_plans():
    return {mode: json.loads((directory / "plan.json").read_text())
            for mode, directory in PARENTS.items()}


def evaluation_points():
    points = {}
    for mode, plan in parent_plans().items():
        for job in plan["jobs"]:
            key = (mode, job["code"], job["p"])
            bases = {b: {"path": str((PARENTS[mode] / "circuits" / c["file"]).relative_to(REPO)),
                         "sha256": c["sha256"]} for b, c in job["bases"].items()}
            value = {"mode": mode, "code": job["code"], "p": job["p"],
                     "cycles": job["cycles"], "bases": bases,
                     "group": f'{mode}-{job["code"].lower()}'}
            if points.setdefault(key, value) != value:
                raise ValueError(f"parent arms disagree on {key}")
    return list(points.values())


def circuit(case):
    from run import sha
    path = REPO / case["path"]
    if sha(path) != case["sha256"]:
        raise ValueError(f"circuit digest mismatch: {path}")
    return stim.Circuit.from_file(str(path))


def rescale(source, original_rate, new_rate):
    """Keep repeat blocks and targets, changing only known noise arguments."""
    out = stim.Circuit()
    for instruction in source:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            out.append(stim.CircuitRepeatBlock(instruction.repeat_count,
                                               rescale(instruction.body_copy(), original_rate, new_rate)))
            continue
        args = instruction.gate_args_copy()
        if instruction.name in NOISE and args:
            if len(args) != 1:
                raise ValueError(f"unexpected channel arguments: {instruction.name}")
            args = [float(Decimal(str(args[0])) * Decimal(str(new_rate)) / Decimal(str(original_rate)))]
        elif args and instruction.name not in {"DETECTOR", "OBSERVABLE_INCLUDE", "QUBIT_COORDS", "SHIFT_COORDS"}:
            raise ValueError(f"unclassified gate argument: {instruction.name}")
        out.append(instruction.name, instruction.targets_copy(), args, tag=instruction.tag)
    return out


def verify_scaling(highest, reference, rate, basis):
    scaled = rescale(circuit(highest["bases"][basis]), highest["p"], rate)
    a, b = list(scaled.flattened()), list(reference.flattened())
    if len(a) != len(b):
        raise ValueError(f"released circuit instruction count changed at {rate}")
    for left, right in zip(a, b):
        args, expected = left.gate_args_copy(), right.gate_args_copy()
        if (left.name != right.name or left.tag != right.tag or left.targets_copy() != right.targets_copy()
                or len(args) != len(expected)
                or any(not math.isclose(x, y, rel_tol=1e-13, abs_tol=1e-16) for x, y in zip(args, expected))):
            raise ValueError(f"scaling does not recover released instruction: {left} != {right}")


def training_points(write=False):
    from run import sha
    points = evaluation_points()
    groups = {}
    for point in points:
        groups.setdefault(point["group"], []).append(point)
    out = {}
    for group, rows in groups.items():
        exact = next((p for p in rows if p["p"] == TRAIN_P), None)
        if exact:
            out[group] = exact
            continue
        high = max(rows, key=lambda p: p["p"])
        point = {**high, "p": TRAIN_P, "bases": {}, "training_only": True,
                 "checked_against_released_rates": [p["p"] for p in rows]}
        for basis in ("x", "z"):
            if write:
                for released in rows:
                    verify_scaling(high, circuit(released["bases"][basis]), released["p"], basis)
            path = ROOT / "training-circuits" / f"{group}-{basis}-p003.stim"
            if write:
                path.parent.mkdir(exist_ok=True)
                rescale(circuit(high["bases"][basis]), high["p"], TRAIN_P).to_file(str(path))
            point["bases"][basis] = {"path": str(path.relative_to(REPO)), "sha256": sha(path)}
        out[group] = point
    return out
