"""Matched-shot cross-check of canonical public and compiled BP4 executions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.problems import PauliCode, QuaternaryOriginalProblem

from run_bp4_performance_screen import miao_toric_d4
from run_reproduction import bp4_graph_from_css, css_syndrome, logical_failure, sample_error


def main() -> None:
    root = Path(__file__).resolve().parent / "results/performance_investigation"
    output = root / "public_compiled_toric_p0075_n100_seed20261103"
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    code = miao_toric_d4()
    checks = np.vstack((np.where(code.hx, 1, 0), np.where(code.hz, 3, 0))).astype(np.uint8)
    pauli_code = PauliCode(checks=checks)
    graph = bp4_graph_from_css(code, 0.1)
    priors = np.tile(np.asarray((0.9, 0.1 / 3, 0.1 / 3, 0.1 / 3)), (code.n, 1))
    rng = np.random.Generator(np.random.PCG64(20261103))
    digest = hashlib.sha256()
    disagreements = 0
    outcome_disagreements = 0
    with (output / "events.jsonl").open("w", encoding="utf-8") as handle:
        for shot in range(100):
            truth = sample_error(rng, code.n, 0.075)
            observed = css_syndrome(code, truth)
            problem = QuaternaryOriginalProblem(
                lineage_id=f"original-miao-toric-{shot}", code=pauli_code, syndrome=observed)
            public = ScalarLlrBp4Kernel().new_session(problem, priors).run(max_iterations=25)
            compiled = graph.run(observed, max_iterations=25)
            public_candidate = np.asarray(public.candidate, dtype=np.uint8)
            public_failed = (not public.converged or logical_failure(code, truth, public_candidate))
            compiled_failed = (not compiled.converged or logical_failure(code, truth, compiled.candidate))
            disagreements += int(not np.array_equal(public_candidate, compiled.candidate))
            outcome_disagreements += int(public_failed != compiled_failed)
            event = {"shot": shot, "error_sha256": hashlib.sha256(truth.tobytes()).hexdigest(),
                     "public_failed": bool(public_failed), "compiled_failed": bool(compiled_failed),
                     "public_converged": bool(public.converged), "compiled_converged": bool(compiled.converged),
                     "same_candidate": bool(np.array_equal(public_candidate, compiled.candidate)),
                     "public_iterations": public.iteration, "compiled_iterations": compiled.iterations}
            line = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            handle.write(line)
            digest.update(line.encode())
    summary = {"code": "miao_toric_d4", "physical_p": 0.075, "initial_p": 0.1,
               "shots": 100, "seed": 20261103, "max_iterations": 25,
               "candidate_disagreements": disagreements,
               "outcome_disagreements": outcome_disagreements,
               "event_ledger": "events.jsonl", "event_ledger_sha256": digest.hexdigest()}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
