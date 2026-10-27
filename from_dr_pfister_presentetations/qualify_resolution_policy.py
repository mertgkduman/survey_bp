"""Record paired-shot equivalence of promoted compiled policies and diagnostics.

This is implementation qualification, not a source-curve campaign. It writes
one event per error with both decoder outputs and independent logical outcome.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.code_constructions import build_b1_ghp
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy
from inspect_q8_minsum_clipping import _variants
from policy_kernel import binary_prior, decode_binary_oms
from run_reproduction import (
    BITS, LABELS, bp4_graph_from_css, css_syndrome, double_gross,
    logical_failure, sample_error,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results" / "ms_resolution_policy_qualification"
SEED = 26027
SHOTS = 200
T = 1000


def _result(code, truth, candidate, iterations, converged):
    return {
        "candidate_sha256": sha256(candidate.tobytes()).hexdigest(),
        "iterations": int(iterations),
        "converged": bool(converged),
        "type_i": not bool(converged),
        "type_ii": bool(converged and logical_failure(code, truth, candidate)),
    }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"qualification output already exists: {OUTPUT}")
    OUTPUT.mkdir(parents=True)
    reference_ms = _variants()["both_changes"]
    binary_policy = BpFloodingPolicy(
        check_rule="min_sum",
        resolution=ResolutionPolicy("int8", 4, "all_messages"),
        damping=.1, alpha=1.0, beta=.25,
    )
    digest = sha256()
    counts: dict[str, dict[str, object]] = {}
    with (OUTPUT / "events.jsonl").open("x", encoding="utf-8") as ledger:
        for name, code, p in (
            ("b1", build_b1_ghp(), .10),
            ("double_gross", double_gross(), .08),
        ):
            old_graph = bp4_graph_from_css(code, p)
            new_graph = CompiledBp4Graph.from_css(code, p, rule="min_sum")
            x_graph = CompiledBinaryFlooding.from_check_matrix(
                code.hz, rule="min_sum", policy=binary_policy,
            ).bind_error_rate(2 * p / 3)
            z_graph = CompiledBinaryFlooding.from_check_matrix(
                code.hx, rule="min_sum", policy=binary_policy,
            ).bind_error_rate(2 * p / 3)
            rng = np.random.default_rng(SEED)
            count = {"shots": 0, "bp4_exact_matches": 0, "binary_exact_matches": 0,
                     "bp4_type_i": 0, "bp4_type_ii": 0,
                     "binary_type_i": 0, "binary_type_ii": 0}
            for shot in range(SHOTS):
                truth = sample_error(rng, code.n, p)
                syndrome = css_syndrome(code, truth)
                old_bp4 = reference_ms(
                    old_graph.row_ptr, old_graph.variable_ptr, old_graph.variable_edges,
                    old_graph.variables, old_graph.labels, old_graph.prior_llrs,
                    syndrome, T, 16, 0.0, True,
                )
                new_bp4 = new_graph.run(syndrome, max_iterations=T)
                old_bp4_outcome = _result(code, truth, *old_bp4)
                new_bp4_outcome = _result(
                    code, truth, new_bp4.candidate, new_bp4.iterations, new_bp4.converged,
                )
                bits = BITS[truth]
                sx = (code.hz.astype(np.int64) @ bits[:, 0].astype(np.int64) % 2).astype(np.uint8)
                sz = (code.hx.astype(np.int64) @ bits[:, 1].astype(np.int64) % 2).astype(np.uint8)
                old_x = decode_binary_oms(x_graph.graph.row_ptr, x_graph.graph.variables, code.n,
                                          sx, binary_prior(p), T, 4, .1, 1.0, .25)
                old_z = decode_binary_oms(z_graph.graph.row_ptr, z_graph.graph.variables, code.n,
                                          sz, binary_prior(p), T, 4, .1, 1.0, .25)
                new_x, new_z = x_graph.run(sx, max_iterations=T), z_graph.run(sz, max_iterations=T)
                old_candidate = LABELS[old_x[0], old_z[0]]
                new_candidate = LABELS[new_x.candidate, new_z.candidate]
                old_binary_outcome = _result(code, truth, old_candidate,
                                             max(old_x[1], old_z[1]), old_x[2] and old_z[2])
                new_binary_outcome = _result(code, truth, new_candidate,
                                             max(new_x.iterations, new_z.iterations),
                                             new_x.converged and new_z.converged)
                bp4_match = old_bp4_outcome == new_bp4_outcome
                binary_match = (old_binary_outcome == new_binary_outcome
                                and old_x[1:] == (new_x.iterations, new_x.converged)
                                and old_z[1:] == (new_z.iterations, new_z.converged))
                event = {
                    "schema": "paired-policy-qualification-v1", "code": name,
                    "physical_p": p, "decoder_p0": p, "seed": SEED, "shot": shot,
                    "error_sha256": sha256(truth.tobytes()).hexdigest(),
                    "bp4_ms_diagnostic": old_bp4_outcome,
                    "bp4_ms_default": new_bp4_outcome,
                    "binary_oms_experimental": old_binary_outcome,
                    "binary_oms_policy": new_binary_outcome,
                    "bp4_exact_match": bp4_match, "binary_exact_match": binary_match,
                }
                encoded = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
                ledger.write(encoded.decode())
                digest.update(encoded)
                count["shots"] += 1
                count["bp4_exact_matches"] += int(bp4_match)
                count["binary_exact_matches"] += int(binary_match)
                count["bp4_type_i"] += int(new_bp4_outcome["type_i"])
                count["bp4_type_ii"] += int(new_bp4_outcome["type_ii"])
                count["binary_type_i"] += int(new_binary_outcome["type_i"])
                count["binary_type_ii"] += int(new_binary_outcome["type_ii"])
            counts[name] = count
    summary = {
        "schema": "paired-policy-qualification-summary-v1",
        "seed": SEED, "shots_per_code": SHOTS, "max_iterations": T,
        "codes": counts,
        "bp4_policy": new_graph.policy.as_evidence(),
        "bp4_policy_semantic_identity": new_graph.policy.semantic_identity,
        "binary_policy": binary_policy.as_evidence(),
        "binary_policy_semantic_identity": binary_policy.semantic_identity,
        "events_sha256": digest.hexdigest(),
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
