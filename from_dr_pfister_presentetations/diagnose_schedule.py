"""Probe whether variable-serial BP4 freshness explains the slide gap."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from policy_kernel import decode_bp4, decode_bp4_variable_serial
from run_reproduction import bp4_graph_from_css, css_syndrome, double_gross, logical_failure, sample_error
from bp_registry.code_constructions import build_b1_ghp


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", choices=("b1", "double_gross"), required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--shots", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20261025)
    args = parser.parse_args()
    code = build_b1_ghp() if args.code == "b1" else double_gross()
    graph = bp4_graph_from_css(code, args.p)
    edge_checks = np.repeat(np.arange(len(graph.row_ptr) - 1, dtype=np.int64), np.diff(graph.row_ptr))
    zero = np.zeros(len(graph.row_ptr) - 1, dtype=np.uint8)
    decode_bp4_variable_serial(graph.row_ptr, graph.variable_ptr, graph.variable_edges,
                               edge_checks, graph.variables, graph.labels, graph.prior_llrs, zero, 1, 16, 0.0)
    rng = np.random.Generator(np.random.PCG64(args.seed))
    stem = f"schedule_{args.code}_p{args.p:.3f}_n{args.shots}_seed{args.seed}"
    events_path = ROOT / "results" / f"{stem}.events.jsonl"
    summary_path = ROOT / "results" / f"{stem}.json"
    if events_path.exists() or summary_path.exists():
        raise FileExistsError("schedule diagnostic already exists")
    arms = {"serial_vanilla_sp": (16, 0.0), "serial_tuned_sp": (4, 0.1)}
    totals = {arm: {"failures": 0, "work": 0} for arm in arms}
    digest = hashlib.sha256()
    with events_path.open("w", encoding="utf-8") as handle:
        for shot in range(args.shots):
            error = sample_error(rng, code.n, args.p)
            syndrome = css_syndrome(code, error)
            record = {"category": "schedule_diagnostic_shot", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                      "shot": shot, "error_sha256": hashlib.sha256(error.tobytes()).hexdigest(), "arms": {}}
            for arm, (scale, damping) in arms.items():
                candidate, iterations, converged = decode_bp4_variable_serial(
                    graph.row_ptr, graph.variable_ptr, graph.variable_edges, edge_checks,
                    graph.variables, graph.labels, graph.prior_llrs, syndrome, 1000, scale, damping)
                failed = not converged or logical_failure(code, error, candidate)
                totals[arm]["failures"] += int(failed)
                totals[arm]["work"] += int(iterations)
                record["arms"][arm] = {"failed": bool(failed), "iterations": int(iterations)}
            line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            handle.write(line)
            digest.update(line.encode())
    summary = {"status": "schedule_diagnostic_adaptation", "code": args.code, "p": args.p,
               "shots": args.shots, "seed": args.seed, "event_ledger": events_path.name,
               "event_ledger_sha256": digest.hexdigest(),
               "arms": {arm: {"failures": value["failures"], "mean_iterations": value["work"] / args.shots}
                        for arm, value in totals.items()}}
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary_path)


if __name__ == "__main__":
    main()
