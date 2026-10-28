"""Supersede a provisional decoder file while preserving its exact bytes."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json

from bp_registry.css import semantic_sha256

from runner import ROOT, load_registry, vanilla


def main(code: str, stage: str, candidate_id: str) -> None:
    if code not in {"a5", "b2"} or not stage.startswith(code + "_"):
        raise ValueError("stage must belong to the selected code")
    registry_path = ROOT / "decoders" / f"{stage}_candidates.json"
    _, items, _ = load_registry(registry_path)
    if candidate_id not in items:
        raise ValueError("candidate absent from stage registry")
    result_path = ROOT / "results" / f"{stage}_results.json"
    result_raw = result_path.read_bytes()
    result = json.loads(result_raw)
    plan_raw = (ROOT / f"{stage}_plan.json").read_bytes()
    if (not result["complete"] or result["stage"] != stage
            or result["plan_sha256"] != sha256(plan_raw).hexdigest()
            or not any(row["code"] == code and row["candidate_id"] == candidate_id
                       for row in result["rows"])):
        raise ValueError("candidate lacks complete audited stage evidence")
    output = ROOT / "decoders" / f"{code}_tuned.json"
    old_raw = output.read_bytes()
    old, _, _ = load_registry(output)
    if old["code"] != code or old["code_semantic_sha256"] != semantic_sha256(vanilla._load_code(code)):
        raise ValueError("provisional decoder code identity differs")
    old_sha = sha256(old_raw).hexdigest()
    archive = ROOT / "decoders/selection_history" / f"{code}_prior_{old_sha[:12]}.json"
    archive.parent.mkdir(exist_ok=True)
    if archive.exists():
        raise FileExistsError("provisional selection already archived")
    archive.write_bytes(old_raw)
    selected = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "code": code, "code_semantic_sha256": old["code_semantic_sha256"],
                "baseline_id": candidate_id, "selected_candidate_id": candidate_id,
                "selection_stage": stage,
                "selection_stage_plan_sha256": sha256(plan_raw).hexdigest(),
                "selection_stage_results_sha256": sha256(result_raw).hexdigest(),
                "selection_status": "finite_neighborhood_90pct_interval_and_work",
                "supersedes_selection_sha256": old_sha,
                "candidates": [items[candidate_id]]}
    output.write_text(json.dumps(selected, sort_keys=True, indent=2) + "\n")
    load_registry(output)
    print(f"archived {archive}; selected {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=("a5", "b2"), required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    main(args.code, args.stage, args.candidate)
