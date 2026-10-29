"""Paired development study: frozen tuned BP4 inside four-state Q-BPGD.

Run with ``PYTHONPATH=src .venv/bin/python .../run.py --code a5 --shots 1000``.
Every arm receives the same PCG64 physical errors; the decoder receives only
the syndrome. Original CSS logical outcomes are evaluated independently.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import time

import numpy as np

from bp_registry.css import semantic_sha256
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
VANILLA_PATH = ROOT.parent / "yao-2312-10950-vanilla" / "run.py"
TUNING = ROOT.parent / "yao-2312-10950-bp4-tuning-p006" / "decoders"
spec = importlib.util.spec_from_file_location("yao_vanilla_for_tuned_qbpgd", VANILLA_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load the pinned CSS evaluator")
vanilla = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vanilla)


def _policy(code_name: str) -> tuple[dict, dict, str]:
    selected_path = TUNING / f"{code_name}_tuned.json"
    selected_bytes = selected_path.read_bytes()
    selected = json.loads(selected_bytes)
    local = json.loads((ROOT / "decoders" / f"{code_name}.json").read_text())
    candidate = selected["candidates"][0]
    if (local["schema"] != "yao-bp4-tuned-qbpgd-policy-v1"
            or local["selected_bp4_sha256"] != sha256(selected_bytes).hexdigest()
            or local["selected_candidate_id"] != selected["selected_candidate_id"]
            or selected["code"] != code_name or selected["physical_p"] != .06
            or candidate["kernel"] != "profile_v2"
            or candidate["check_cap"] is not None or candidate["product_epsilon"] != 1e-10
            or local["qbpgd"] != {"iterations_per_round": 10, "epsilon": 1e-10, "round_limit": "n"}):
        raise ValueError("Q-BPGD policy is not bound to the selected BP4 file")
    return local, candidate, sha256(selected_bytes).hexdigest()


def _outcome(candidate: np.ndarray, truth: np.ndarray, syndrome: np.ndarray,
             evaluator, truth_signature: int, masks) -> dict[str, bool]:
    valid = bool(np.array_equal(vanilla._original_syndrome(evaluator, candidate), syndrome))
    logical = valid and vanilla._logical_signature(candidate, masks) != truth_signature
    exact = valid and not logical and bool(np.array_equal(candidate, truth))
    return {"type_i": not valid, "type_ii": bool(logical), "exact_success": bool(exact),
            "stabilizer_success": bool(valid and not logical and not exact)}


def run(code_name: str, shots: int, seed: int, output: Path) -> dict:
    if code_name not in ("a5", "b2") or type(shots) is not int or shots < 1 or type(seed) is not int or seed < 0:
        raise ValueError("invalid study request")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {output}")
    local, tuned, selected_sha = _policy(code_name)
    code = vanilla._load_code(code_name)
    if semantic_sha256(code) != local["code_semantic_sha256"]:
        raise ValueError("pinned CSS artifact changed")
    base_profile = replace(QBP4_F64_V2, profile_id=f"{code_name}-qbpgd-control-f64-v2", v2c_damping=0.0)
    tuned_profile = replace(QBP4_F64_V2, profile_id=f"{code_name}-qbpgd-tuned-f64-v2",
                            v2c_damping=float(tuned["damping"]), check_cap=tuned["check_cap"],
                            product_epsilon=float(tuned["product_epsilon"]))
    base = replace(CompiledBp4Graph.from_css(code, .06), profile=base_profile)
    tuned_graph = replace(CompiledBp4Graph.from_css(code, float(tuned["p0"])), profile=tuned_profile)
    zero = np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8)
    for graph in (base, tuned_graph):
        graph.run_qbpgd(zero, iterations_per_round=1, round_limit=1)
    masks = vanilla._logical_masks(code)
    evaluator = vanilla._syndrome_evaluator(code)
    files = (Path(__file__), VANILLA_PATH, selected_path_for(code_name),
             REPO / "src/bp_registry/quaternary/compiled.py",
             REPO / "src/bp_registry/quaternary/numerics.py")
    manifest = {
        "schema": "yao-bp4-tuned-qbpgd-manifest-v1", "code": code_name,
        "code_semantic_sha256": semantic_sha256(code), "physical_p": .06,
        "shots": shots, "seed": seed, "sampler": "numpy.PCG64; I/X/Y/Z=(1-p,p/3,p/3,p/3)",
        "arms": {"control": {"decoder_p0": .06, "numerics": base.effective_numerics},
                 "tuned": {"decoder_p0": tuned["p0"], "numerics": tuned_graph.effective_numerics,
                            "selected_bp4_sha256": selected_sha,
                            "selected_candidate_id": tuned["id"]}},
        "qbpgd": local["qbpgd"],
        "interpretation": "persistent V2C, four-state max-marginal fixation, I/X/Y/Z ties, normalizing raw (1-epsilon,epsilon,epsilon,epsilon)",
        "fidelity": "canonical_adaptation; compiled development backend",
        "stop_rule": "fixed_shots; up to n Q-BPGD rounds per shot; syndrome check after each 10-sweep block",
        "source_files_sha256": {str(path.relative_to(REPO)): sha256(path.read_bytes()).hexdigest() for path in files},
    }
    output.mkdir(parents=True)
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    counts = {arm: {key: 0 for key in ("type_i", "type_ii", "exact_success", "stabilizer_success",
                                            "iterations", "rounds", "fixations", "elapsed_ns")}
              for arm in ("control", "tuned")}
    pairs = {"rescues": 0, "losses": 0, "both_fail": 0, "both_succeed": 0}
    digest = sha256()
    rng = np.random.Generator(np.random.PCG64(seed))
    started = time.monotonic()
    with (output / "events.jsonl").open("x") as ledger:
        for shot in range(shots):
            truth = vanilla._sample(rng, code.n, .06)
            syndrome = vanilla._original_syndrome(evaluator, truth)
            signature = vanilla._logical_signature(truth, masks)
            records = {}
            for arm, graph in (("control", base), ("tuned", tuned_graph)):
                start_ns = time.perf_counter_ns()
                decoded = graph.run_qbpgd(syndrome, iterations_per_round=10, epsilon=1e-10)
                elapsed_ns = time.perf_counter_ns() - start_ns
                outcome = _outcome(decoded.candidate, truth, syndrome, evaluator, signature, masks)
                record = {**outcome, "iterations": decoded.iterations, "rounds": decoded.rounds,
                          "fixations": decoded.fixations, "elapsed_ns": elapsed_ns,
                          "candidate_sha256": sha256(decoded.candidate.tobytes()).hexdigest(),
                          "claimed_convergence": decoded.converged}
                records[arm] = record
                for key in counts[arm]:
                    counts[arm][key] += int(record[key])
            control_fail = records["control"]["type_i"] or records["control"]["type_ii"]
            tuned_fail = records["tuned"]["type_i"] or records["tuned"]["type_ii"]
            pair_key = "rescues" if control_fail and not tuned_fail else "losses" if tuned_fail and not control_fail else "both_fail" if tuned_fail else "both_succeed"
            pairs[pair_key] += 1
            event = {"schema": "yao-bp4-tuned-qbpgd-shot-v1", "shot": shot,
                     "error_sha256": sha256(truth.tobytes()).hexdigest(), "syndrome_sha256": sha256(syndrome.tobytes()).hexdigest(),
                     "arms": records, "pair": pair_key}
            row = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            ledger.write(row)
            digest.update(row.encode())
            if (shot + 1) % 1000 == 0:
                ledger.flush()
                print(code_name, shot + 1, {arm: counts[arm]["type_i"] + counts[arm]["type_ii"] for arm in counts}, flush=True)
    summary = {"schema": "yao-bp4-tuned-qbpgd-summary-v1", "code": code_name, "shots": shots,
               "seed": seed, "counts": counts, "pairs": pairs,
               "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
               "events_sha256": digest.hexdigest(), "wall_seconds": time.monotonic() - started}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def selected_path_for(code_name: str) -> Path:
    return TUNING / f"{code_name}_tuned.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=("a5", "b2"), required=True)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--seed", type=int, default=20261029)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.code, args.shots, args.seed, args.output), sort_keys=True))
