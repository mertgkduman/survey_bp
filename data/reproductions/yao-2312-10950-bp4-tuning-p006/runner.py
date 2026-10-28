"""Run one pinned BP4 candidate on a deterministic paired error stream.

All candidates for a code/stage use the same PCG64 seed and shot prefix.
The decoder sees only the syndrome; original-code recovery is classified
independently. The event ledger is mandatory even for short screens.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import time

import numpy as np

from bp_registry.css import semantic_sha256
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V2
from bp_registry.resolution import BpFloodingPolicy


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
VANILLA_RUN = ROOT.parent / "yao-2312-10950-vanilla" / "run.py"
_spec = importlib.util.spec_from_file_location("yao_2312_vanilla_run", VANILLA_RUN)
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot import the pinned vanilla study evaluator")
vanilla = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vanilla)

SOURCE_FILES = (
    "data/reproductions/yao-2312-10950-bp4-tuning-p006/runner.py",
    "data/reproductions/yao-2312-10950-vanilla/run.py",
    "data/reproductions/yao-2312-10950-vanilla/codes/a5.json",
    "data/reproductions/yao-2312-10950-vanilla/codes/b2.json",
    "src/bp_registry/code_constructions.py",
    "src/bp_registry/css.py",
    "src/bp_registry/quaternary/compiled.py",
    "src/bp_registry/quaternary/numerics.py",
    "src/bp_registry/resolution.py",
)


def source_hashes() -> dict[str, str]:
    return {name: sha256((REPO / name).read_bytes()).hexdigest() for name in SOURCE_FILES}


def load_registry(path: Path) -> tuple[dict[str, object], dict[str, dict[str, object]], str]:
    raw = path.read_bytes()
    registry = json.loads(raw)
    if (registry.get("schema") != "yao-bp4-tuning-candidates-v1"
            or registry.get("physical_p") != .06
            or not isinstance(registry.get("candidates"), list)):
        raise ValueError("unsupported BP4 tuning registry")
    items = {}
    for item in registry["candidates"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or item["id"] in items:
            raise ValueError("invalid or duplicate decoder candidate")
        if item.get("kernel") not in {"profile_v2", "policy_flooding"}:
            raise ValueError("unknown BP4 tuning kernel")
        if not (isinstance(item.get("p0"), (int, float)) and 0 < item["p0"] < 1
                and type(item.get("max_iterations")) is int and item["max_iterations"] > 0):
            raise ValueError("invalid BP4 decoder prior or iteration cap")
        if item["kernel"] == "policy_flooding":
            if set(item) != {"id", "kernel", "p0", "max_iterations", "policy"}:
                raise ValueError("unexpected policy candidate fields")
            BpFloodingPolicy.from_spec(item["policy"])
        else:
            if set(item) != {"id", "kernel", "p0", "damping", "check_cap", "product_epsilon", "max_iterations"}:
                raise ValueError("unexpected v2 profile candidate fields")
            replace(QBP4_F64_V2, v2c_damping=item["damping"], check_cap=item["check_cap"],
                    product_epsilon=item["product_epsilon"])
        items[item["id"]] = item
    if registry.get("baseline_id") not in items:
        raise ValueError("baseline candidate missing")
    return registry, items, sha256(raw).hexdigest()


def bind_candidate(code, item: dict[str, object]) -> CompiledBp4Graph:
    p0 = float(item["p0"])
    if item["kernel"] == "profile_v2":
        profile = replace(QBP4_F64_V2, profile_id=f"tuning-{item['id']}",
                          v2c_damping=float(item["damping"]),
                          check_cap=item["check_cap"],
                          product_epsilon=float(item["product_epsilon"]))
        return replace(CompiledBp4Graph.from_css(code, p0), profile=profile)
    policy = BpFloodingPolicy.from_spec(item["policy"])
    return CompiledBp4Graph.from_css(code, p0, rule=policy.check_rule, policy=policy)


def run_one(*, code_name: str, candidate_id: str, registry_path: Path,
            seed: int, max_shots: int, target_failures: int | None,
            output: Path, plan_sha256: str | None = None) -> dict[str, object]:
    registry, items, registry_sha256 = load_registry(registry_path)
    if candidate_id not in items or code_name not in {"a5", "b2"}:
        raise ValueError("unknown code or candidate")
    if type(seed) is not int or seed < 0 or type(max_shots) is not int or max_shots < 1:
        raise ValueError("invalid seed or shot limit")
    if target_failures is not None and (type(target_failures) is not int or target_failures < 1):
        raise ValueError("target_failures must be a positive integer")
    code = vanilla._load_code(code_name)
    graph = bind_candidate(code, items[candidate_id])
    masks = vanilla._logical_masks(code)
    evaluator = vanilla._syndrome_evaluator(code)
    graph.run(np.zeros(code.hx.shape[0] + code.hz.shape[0], dtype=np.uint8), max_iterations=1)
    if output.exists():
        raise FileExistsError(f"refusing to replace existing evidence: {output}")
    output.mkdir(parents=True)
    manifest = {
        "schema": "yao-bp4-tuning-run-v1", "code": code_name,
        "code_semantic_sha256": semantic_sha256(code),
        "physical_p": registry["physical_p"], "seed": seed,
        "candidate_id": candidate_id, "candidate": items[candidate_id],
        "candidate_registry": str(registry_path.resolve().relative_to(REPO)),
        "candidate_registry_sha256": registry_sha256,
        "effective_numerics": graph.effective_numerics,
        "planned_max_shots": max_shots, "target_failures": target_failures,
        "stop_rule": "fixed_shots" if target_failures is None else "target_block_failures_or_max_shots",
        "plan_sha256": plan_sha256, "source_files_sha256": source_hashes(),
        "sampler": "numpy.PCG64; I/X/Y/Z = 1-p,p/3,p/3,p/3",
        "outcome": "independent original-code Type I + Type II block failure",
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    digest = sha256()
    counts = {key: 0 for key in ("type_i", "type_ii", "exact_success",
                                 "stabilizer_success", "iterations", "elapsed_ns")}
    rng = np.random.Generator(np.random.PCG64(seed))
    start = time.monotonic()
    with (output / "events.jsonl").open("x", encoding="utf-8") as handle:
        for shot in range(max_shots):
            truth = vanilla._sample(rng, code.n, .06)
            syndrome = vanilla._original_syndrome(evaluator, truth)
            truth_signature = vanilla._logical_signature(truth, masks)
            record = vanilla._one_arm("bp4_candidate", graph, syndrome, code, evaluator,
                                      truth, truth_signature, masks,
                                      items[candidate_id]["max_iterations"])
            event = {"schema": "yao-bp4-tuning-shot-v1", "shot": shot,
                     "error_sha256": sha256(truth.tobytes()).hexdigest(),
                     "outcome": record}
            encoded = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
            handle.write(encoded.decode())
            digest.update(encoded)
            for key in ("type_i", "type_ii", "exact_success", "stabilizer_success"):
                counts[key] += int(record[key])
            counts["iterations"] += record["iterations"][0]
            counts["elapsed_ns"] += record["elapsed_ns"]
            n = shot + 1
            if n % 1000 == 0:
                print(code_name, candidate_id, n, counts["type_i"] + counts["type_ii"], flush=True)
                handle.flush()
            if target_failures is not None and counts["type_i"] + counts["type_ii"] >= target_failures:
                reason = "target_block_failures"
                break
        else:
            n = max_shots
            reason = "fixed_shots" if target_failures is None else "max_shots"
    summary = {
        "schema": "yao-bp4-tuning-summary-v1", "code": code_name,
        "candidate_id": candidate_id, "seed": seed,
        "shots": n, "max_shots": max_shots, "target_failures": target_failures,
        "stop_reason": reason, "counts": counts,
        "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
        "events_sha256": digest.hexdigest(), "wall_seconds": time.monotonic() - start,
    }
    (output / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"code": code_name, "candidate": candidate_id, "shots": n,
                      "failures": counts["type_i"] + counts["type_ii"],
                      "stop": reason}, sort_keys=True), flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=("a5", "b2"), required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--registry", type=Path, default=ROOT / "decoders/screen_candidates.json")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--target-failures", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_one(code_name=args.code, candidate_id=args.candidate, registry_path=args.registry,
            seed=args.seed, max_shots=args.shots,
            target_failures=args.target_failures, output=args.output)


if __name__ == "__main__":
    main()
