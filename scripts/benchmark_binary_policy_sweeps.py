"""Exact trace and warmed sweep timing for canonical binary flooding policies."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import time

import numpy as np

from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64, boxplus_pair
from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule
from bp_registry.canonical.updates import MinSumUpdate, NormalizedMinSumUpdate, OffsetMinSumUpdate, ParameterAssignment


ROOT = Path(__file__).resolve().parents[1]


def trace(sweep) -> dict[str, object]:
    return {
        "old_v2c": sha256(sweep.old_v2c.tobytes()).hexdigest(),
        "c2v": sha256(sweep.check_to_variable.tobytes()).hexdigest(),
        "beliefs": sha256(sweep.beliefs.tobytes()).hexdigest(),
        "new_v2c": sha256(sweep.new_v2c.tobytes()).hexdigest(),
        "candidate": sha256(sweep.candidate.tobytes()).hexdigest(),
        "work": sweep.proposed_work.as_evidence(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = (ROOT / "data/artifacts/bb72-css.json").read_bytes()
    h = np.asarray(json.loads(raw)["hz"], dtype=np.uint8)
    table = EdgeTable.from_check_matrix(h)
    rng = np.random.default_rng(11019)
    error = (rng.random(h.shape[1]) < .08).astype(np.uint8)
    syndrome = np.asarray((h @ error) % 2, dtype=np.uint8)
    pairs = np.vstack((rng.uniform(-40, 40, size=(512, 2)), np.asarray([
        [-0.0, 0.0], [25.0, -25.0], [1e-300, -1e-300], [40.0, 40.0], [-40.0, -40.0],
    ])))
    pair_results = np.asarray([boxplus_pair(float(left), float(right)) for left, right in pairs], dtype=np.float64)
    report = {
        "schema": "binary-policy-sweeps-v1",
        "host": platform.node(), "affinity": sorted(os.sched_getaffinity(0)),
        "python": platform.python_version(), "numpy": np.__version__,
        "artifact_sha256": sha256(raw).hexdigest(),
        "syndrome_sha256": sha256(syndrome.tobytes()).hexdigest(),
        "pair_inputs_sha256": sha256(pairs.tobytes()).hexdigest(),
        "pair_output_sha256": sha256(pair_results.tobytes()).hexdigest(),
        "pair_output_bits": pair_results.view(np.uint64).tolist(),
        "shape": list(h.shape), "edges": table.edge_count, "cases": {},
    }
    assignment = lambda value: ParameterAssignment(shape="scalar", value=value)
    rules = {
        "spa": BinarySpaKernel(),
        "min_sum": BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate()),
        "normalized_min_sum": BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=NormalizedMinSumUpdate(alpha=assignment(.8))),
        "offset_min_sum": BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=OffsetMinSumUpdate(beta=assignment(.2))),
    }
    for name, kernel in rules.items():
        schedule = FloodingSchedule(table, kernel=kernel, profile=kernel.profile)
        rows = []
        for _ in range(3):
            old = schedule.initialize(.08)
            start = time.perf_counter_ns()
            sweeps = []
            for iteration in range(3):
                result = schedule.sweep(old, syndrome, error_rate=.08, source_iteration=iteration)
                sweeps.append(result)
                old = result.new_v2c
            elapsed = time.perf_counter_ns() - start
            rows.append({"ns_per_sweep": elapsed / 3, "traces": [trace(s) for s in sweeps]})
        report["cases"][name] = rows
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
