"""Write the two selected, directly runnable decoder registries with receipts."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json

from bp_registry.css import semantic_sha256

from runner import ROOT, load_registry, vanilla


STAGES = {"a5": "tail_a5", "b2": "sweet_b2"}


def write_selected(code: str, candidate_id: str) -> None:
    stage = STAGES[code]
    registry_path = ROOT / "decoders" / f"{stage}_candidates.json"
    _, items, _ = load_registry(registry_path)
    if candidate_id not in items:
        raise ValueError(f"{candidate_id} is not in audited {stage} candidates")
    result_path = ROOT / "results" / f"{stage}_results.json"
    result_raw = result_path.read_bytes()
    result = json.loads(result_raw)
    plan_raw = (ROOT / f"{stage}_plan.json").read_bytes()
    if (not result["complete"] or result["stage"] != stage
            or result["plan_sha256"] != sha256(plan_raw).hexdigest()
            or not any(row["code"] == code and row["candidate_id"] == candidate_id
                       for row in result["rows"])):
        raise ValueError("candidate lacks a complete audited stage result")
    output = ROOT / "decoders" / f"{code}_tuned.json"
    if output.exists():
        raise FileExistsError(f"selected decoder already exists: {output}")
    selected = {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
                "code": code, "code_semantic_sha256": semantic_sha256(vanilla._load_code(code)),
                "baseline_id": candidate_id, "selected_candidate_id": candidate_id,
                "selection_stage": stage,
                "selection_stage_plan_sha256": sha256(plan_raw).hexdigest(),
                "selection_stage_results_sha256": sha256(result_raw).hexdigest(),
                "selection_status": "finite_neighborhood_90pct_interval_and_work",
                "candidates": [items[candidate_id]]}
    output.write_text(json.dumps(selected, sort_keys=True, indent=2) + "\n")
    loaded, _, _ = load_registry(output)
    if loaded != selected:
        raise AssertionError("selected decoder failed round-trip validation")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a5", required=True, help="candidate ID from audited tail_a5")
    parser.add_argument("--b2", required=True, help="candidate ID from audited sweet_b2")
    args = parser.parse_args()
    write_selected("a5", args.a5)
    write_selected("b2", args.b2)
