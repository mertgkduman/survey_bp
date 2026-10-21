"""Pinned-workload timings and exact trace hashes for policy-bearing BP4 sweeps."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import time

import numpy as np

from bp_registry.quaternary.asced import parse_pinned_gb46_css
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.mbp4 import FixedAlphaMbp4Kernel, Mbp4Spec
from bp_registry.quaternary.problems import QuaternaryOriginalProblem, compile_css_artifact
from bp_registry.quaternary.schedules import QbpFloodingSchedule, QbpVariableSerialSchedule, QuaternaryCheckTransform


ROOT = Path(__file__).resolve().parents[1]


def trace(sweep) -> dict[str, object]:
    return {
        "iteration": sweep.iteration,
        "terminal": sweep.terminal,
        "converged": sweep.converged,
        "candidate": sha256(sweep.candidate.tobytes()).hexdigest(),
        "c2v": sha256(sweep.c2v.tobytes()).hexdigest(),
        "v2c": sha256(sweep.v2c.tobytes()).hexdigest(),
        "beliefs": sha256(sweep.beliefs.tobytes()).hexdigest(),
        "marginals": sha256(sweep.marginals.tobytes()).hexdigest(),
        "work": sweep.work.as_evidence(structural_event_version=4),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = (ROOT / "data/artifacts/gb46-h44.alist").read_bytes()
    code = compile_css_artifact(parse_pinned_gb46_css(raw), source_artifact_identity="gb46-h44-pinned-alist")
    rng = np.random.default_rng(11019)
    rng.random((24, 72))
    error = np.zeros(code.n, dtype=np.uint8)
    selected = rng.random(code.n) < .08
    error[selected] = rng.choice(np.asarray([1, 2, 3], dtype=np.uint8), size=int(selected.sum()))
    problem = QuaternaryOriginalProblem("original-policy-benchmark-gb46", code, code.syndrome(error))
    priors = np.tile([.92, .08 / 3, .08 / 3, .08 / 3], (code.n, 1))
    transforms = (QuaternaryCheckTransform.normalization(1.5), QuaternaryCheckTransform.offset(.1))
    report = {
        "schema": "quaternary-policy-sweeps-v1",
        "host": platform.node(), "affinity": sorted(os.sched_getaffinity(0)),
        "python": platform.python_version(),
        "artifact_sha256": sha256(raw).hexdigest(),
        "syndrome_sha256": sha256(problem.syndrome.tobytes()).hexdigest(),
        "code_shape": list(code.checks.shape),
        "edges": int(np.count_nonzero(code.checks)),
        "cases": {},
    }
    for mode in ("transformed_flooding", "transformed_serial", "mbp4_flooding", "mbp4_serial"):
        rows = []
        for _ in range(3):
            if mode in ("transformed_flooding", "transformed_serial"):
                session = ScalarLlrBp4Kernel().new_session(problem, priors)
                policy = (QbpFloodingSchedule(session, transforms=transforms) if mode == "transformed_flooding"
                          else QbpVariableSerialSchedule(session, transforms=transforms))
                sweep = lambda: policy.sweep().result
            else:
                schedule = "qbp_flooding" if mode == "mbp4_flooding" else "qbp_variable_serial"
                session = FixedAlphaMbp4Kernel(Mbp4Spec(alpha=1.5, schedule=schedule, max_iterations=2)).new_session(problem, priors)
                sweep = session.sweep
            start = time.perf_counter_ns()
            snapshots = [sweep() for _ in range(2)]
            elapsed = time.perf_counter_ns() - start
            rows.append({"ns_per_sweep": elapsed / 2, "traces": [trace(s) for s in snapshots],
                         "final_state_digest": session.state_digest})
        report["cases"][mode] = rows
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
