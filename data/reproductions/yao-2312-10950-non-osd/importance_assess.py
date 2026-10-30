"""Independently verify and aggregate fixed-shot rare-event ledgers."""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULTS = ROOT / "results"
CODE_N = {key: value["n"] for key, value in json.loads((ROOT / "codes.json").read_text())["codes"].items()}


def _sample_error(manifest: dict, shot: int) -> tuple[np.ndarray, str]:
    p = manifest["physical_target_p"]
    q = manifest["proposal_p"]
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence((
        manifest["seed"], round(p*100000), round(q*100000), shot))))
    target = bool(rng.random() < manifest["defensive_fraction"])
    physical_p = p if target else q
    draw = rng.random(CODE_N[manifest["code"]])
    if manifest["noise"] == "depolarizing":
        error = np.where(draw < 1-physical_p, 0, np.where(draw < 1-2*physical_p/3, 1,
                         np.where(draw < 1-physical_p/3, 2, 3))).astype(np.uint8)
    else:
        error = (draw < physical_p).astype(np.uint8)
    return error, "target" if target else "shifted"


def _weight(n: int, k: int, p: float, q: float, d: float) -> float:
    lp = k*math.log(p) + (n-k)*math.log1p(-p)
    lq = k*math.log(q) + (n-k)*math.log1p(-q)
    return math.exp(lp - float(np.logaddexp(math.log(d)+lp, math.log1p(-d)+lq)))


def verified_importance_runs() -> dict[tuple[str, str, str], dict]:
    grouped = defaultdict(list)
    runner_name = str((ROOT / "run_importance.py").relative_to(REPO))
    expected_runner_sha = sha256((ROOT / "run_importance.py").read_bytes()).hexdigest()
    intervals = defaultdict(list)
    for path in sorted(RESULTS.glob("completion-importance-*/summary.json")):
        summary = json.loads(path.read_text())
        if summary.get("schema") != "yao-importance-summary-v1":
            continue
        manifest_path = path.with_name("manifest.json")
        ledger_path = path.with_name("events.jsonl")
        if sha256(manifest_path.read_bytes()).hexdigest() != summary["manifest_sha256"]:
            raise ValueError(f"importance manifest mismatch: {path}")
        manifest = json.loads(manifest_path.read_text())
        if manifest["source_files_sha256"][runner_name] != expected_runner_sha:
            raise ValueError(f"importance runner drift: {path}")
        if sha256(ledger_path.read_bytes()).hexdigest() != summary["events_sha256"]:
            raise ValueError(f"importance ledger mismatch: {path}")
        code, method, p = summary["code"], summary["method"], summary["physical_target_p"]
        key = (code, method, f"{p:.5f}")
        first, stop = summary["start_shot"], summary["start_shot"]+summary["shots"]
        seed_proposal = (summary["seed"], summary["proposal_p"])
        for old_seed_proposal, old_first, old_stop in intervals[key]:
            if old_seed_proposal == seed_proposal and first < old_stop and old_first < stop:
                raise ValueError(f"overlapping importance shards: {path}")
        intervals[key].append((seed_proposal, first, stop))
        totals = {field: 0 for field in summary["counts"]}
        sums = {field: 0.0 for field in summary["weighted_sums"]}
        seen = 0
        with ledger_path.open() as ledger:
            for line in ledger:
                event = json.loads(line)
                if event["shot"] != first + seen or event["schema"] != "yao-importance-shot-v1":
                    raise ValueError(f"importance shot order/schema mismatch: {path}")
                truth, branch = _sample_error(manifest, event["shot"])
                if (sha256(truth.tobytes()).hexdigest() != event["error_sha256"]
                        or int(np.count_nonzero(truth)) != event["error_weight"]
                        or branch != event["proposal_branch"]):
                    raise ValueError(f"importance sample mismatch: {path}, shot {event['shot']}")
                weight = _weight(CODE_N[code], event["error_weight"], p,
                                 manifest["proposal_p"], manifest["defensive_fraction"])
                if not math.isclose(weight, event["importance_weight"], rel_tol=2e-14, abs_tol=1e-15):
                    raise ValueError(f"importance weight mismatch: {path}, shot {event['shot']}")
                outcome = event["outcome"]
                if sum(int(outcome[field]) for field in ("type_i", "type_ii", "exact_success", "stabilizer_success")) != 1:
                    raise ValueError(f"outcome partition mismatch: {path}, shot {event['shot']}")
                for field in totals:
                    totals[field] += int(outcome[field])
                fail = int(outcome["type_i"] or outcome["type_ii"])
                sums["failure"] += weight*fail
                sums["failure_sq"] += weight*weight*fail
                sums["type_i"] += weight*int(outcome["type_i"])
                sums["type_ii"] += weight*int(outcome["type_ii"])
                sums["weight"] += weight
                sums["weight_sq"] += weight*weight
                seen += 1
        if seen != summary["shots"] or totals != summary["counts"]:
            raise ValueError(f"importance count mismatch: {path}")
        for field, reported in summary["weighted_sums"].items():
            if not math.isclose(sums[field], reported, rel_tol=1e-11, abs_tol=1e-12):
                raise ValueError(f"importance weighted sum mismatch: {path}, {field}")
        evidence_path = path.relative_to(REPO) if path.is_relative_to(REPO) else path
        grouped[key].append({**summary, "evidence_path": str(evidence_path)})
    result = {}
    for key, shards in grouped.items():
        shots = sum(item["shots"] for item in shards)
        weighted_failure = sum(item["weighted_sums"]["failure"] for item in shards)
        squared_failure = sum(item["weighted_sums"]["failure_sq"] for item in shards)
        variance_total = sum(
            item["shots"] / (item["shots"]-1) *
            max(0.0, item["weighted_sums"]["failure_sq"] -
                item["weighted_sums"]["failure"]**2/item["shots"])
            for item in shards)
        se = math.sqrt(variance_total) / shots
        rate = weighted_failure / shots
        result[key] = {
            "shots": shots,
            "raw_failures": sum(item["counts"]["type_i"]+item["counts"]["type_ii"] for item in shards),
            "raw_type_i": sum(item["counts"]["type_i"] for item in shards),
            "raw_type_ii": sum(item["counts"]["type_ii"] for item in shards),
            "mean_iterations": sum(item["counts"]["iterations"] for item in shards)/shots,
            "mean_fixations": sum(item["counts"]["fixations"] for item in shards)/shots,
            "mean_decode_ms": sum(item["counts"]["elapsed_ns"] for item in shards)/shots/1e6,
            "rate": rate, "se": se,
            "ci95_low": max(0.0, rate-1.96*se),
            "ci95_high": min(1.0, rate+1.96*se),
            "failure_ess": (weighted_failure**2/squared_failure if squared_failure else 0.0),
            "weighted_type_i": sum(item["weighted_sums"]["type_i"] for item in shards)/shots,
            "weighted_type_ii": sum(item["weighted_sums"]["type_ii"] for item in shards)/shots,
            "mean_weight": sum(item["weighted_sums"]["weight"] for item in shards)/shots,
            "evidence_paths": [item["evidence_path"] for item in shards],
            "proposals": sorted(set(item["proposal_p"] for item in shards)),
            "shards": len(shards),
        }
    return result
